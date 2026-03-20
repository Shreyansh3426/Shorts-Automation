import os
import sys
import json
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from thumbnail_generator import generate_thumbnail
from seo_optimizer import generate_seo_metadata

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'youtube_token.json')

def get_youtube_client():
    # Check if we have a pre-authorized token (for GitHub Actions)
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if creds and creds.valid:
            return build('youtube', 'v3', credentials=creds)
    
    # Check if credentials file exists for new OAuth flow (local only)
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(
            f'YouTube credentials not found at {CREDENTIALS_FILE}. '
            'This file is required for uploads (not available in CI/CD). '
            'Videos will be created but cannot be uploaded from GitHub Actions.'
        )
    
    # Only run browser flow in local environment (has display)
    if os.environ.get('CI') or not os.environ.get('DISPLAY'):
        raise RuntimeError(
            'Running in headless environment. YouTube token (youtube_token.json) required. '
            'Run locally with credentials.json to generate token, then add to GitHub Secrets.'
        )
    
    # Local browser-based flow
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=8080)
    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)

def upload_video(video_path, title, description='', tags=None, job_id=None, topic=None, clips_json=None, script='', keywords=None):
    if not os.path.exists(video_path):
        raise Exception(f'Video file not found: {video_path}')
    
    youtube = get_youtube_client()
    
    if tags is None:
        tags = ['shorts', 'facts', 'psychology']
    if isinstance(tags, list):
        tags = tags + ['shorts', 'facts']
    
    if job_id and topic and clips_json and script:
        seo = generate_seo_metadata(topic, script, keywords)
        title = seo['title']
        description = seo['description']
        tags = seo['tags']
    
    body = {
        'snippet': {
            'title': title[:100],
            'description': description if description and '#Shorts' in description else description + '\n\n#Shorts',
            'tags': tags[:15],
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(
        video_path,
        mimetype='video/mp4',
        resumable=True,
        chunksize=1024*1024
    )

    print(f'Uploading: {title}')
    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f'  Progress: {int(status.progress() * 100)}%')

    video_id = response['id']
    video_url = f'https://youtube.com/shorts/{video_id}'
    print(f'  Uploaded: {video_url}')
    
    if job_id and topic and clips_json:
        try:
            thumbnail_path = generate_thumbnail(job_id, topic, clips_json)
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
            ).execute()
            print(f'  Thumbnail set: {thumbnail_path}')
        except Exception as e:
            print(f'  ⚠️  Thumbnail upload failed: {e}')

    return json.dumps({'video_id': video_id, 'url': video_url, 'status': 'ok'})

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python3 upload_youtube.py <video_path> <title>')
        sys.exit(1)
    video_path = sys.argv[1]
    title = sys.argv[2]
    print(upload_video(video_path, title))
