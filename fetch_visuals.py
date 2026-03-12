import sys
import json
import requests
import os
from dotenv import load_dotenv
load_dotenv()
PEXELS_KEY = os.getenv('PEXELS_API_KEY')
OUTPUT_DIR = '/tmp/shorts_visuals'

def fetch_visuals(keywords, topic_id):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    clips = []

    for i, keyword in enumerate(keywords):
        print(f'Searching for: {keyword}', flush=True)

        resp = requests.get(
            'https://api.pexels.com/videos/search',
            headers={'Authorization': PEXELS_KEY},
            params={'query': keyword, 'orientation': 'portrait', 'per_page': 5}
        )

        videos = resp.json().get('videos', [])
        downloaded = False

        for video in videos:
            if video.get('duration', 0) >= 4:
                files = sorted(video.get('video_files', []),
                             key=lambda f: f.get('height', 0), reverse=True)
                hd = next((f for f in files if f.get('height', 0) <= 1920), None)

                if hd:
                    path = f'{OUTPUT_DIR}/{topic_id}_clip{i}.mp4'
                    r = requests.get(hd['link'], stream=True, timeout=60)
                    with open(path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    clips.append({'path': path, 'keyword': keyword})
                    print(f'  Downloaded: {path}', flush=True)
                    downloaded = True
                    break

        if not downloaded:
            print(f'  No video found for: {keyword}', flush=True)

    print(json.dumps({'clips': clips}))

if __name__ == '__main__':
    keywords = json.loads(sys.argv[1])
    topic_id = sys.argv[2]
    fetch_visuals(keywords, topic_id)
