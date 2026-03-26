import sys
import json
import requests
import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()
PEXELS_KEY = os.getenv('PEXELS_API_KEY')

def get_db_conn():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(__file__), 'shorts.db')
    conn = sqlite3.connect(db_path)
    return conn

def is_clip_used(clip_url):
    """Check if a clip URL has already been used"""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT excluded FROM clip_usage WHERE clip_url = ?', (clip_url,))
        row = cursor.fetchone()
        conn.close()
        return row is not None
    except:
        return False

def is_clip_excluded(clip_url):
    """Check if a clip is explicitly excluded from use"""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT excluded FROM clip_usage WHERE clip_url = ? AND excluded = 1', (clip_url,))
        row = cursor.fetchone()
        conn.close()
        return row is not None
    except:
        return False

def track_clip_usage(clip_url, job_id):
    """Track that a clip has been used in a job"""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Check if clip already tracked
        cursor.execute('SELECT job_ids FROM clip_usage WHERE clip_url = ?', (clip_url,))
        row = cursor.fetchone()
        
        if row:
            # Update existing entry
            job_ids = json.loads(row[0]) if row[0] else []
            if job_id not in job_ids:
                job_ids.append(job_id)
            cursor.execute(
                'UPDATE clip_usage SET job_ids = ?, last_used = CURRENT_TIMESTAMP WHERE clip_url = ?',
                (json.dumps(job_ids), clip_url)
            )
        else:
            # Create new entry
            cursor.execute(
                'INSERT INTO clip_usage (clip_url, job_ids) VALUES (?, ?)',
                (clip_url, json.dumps([job_id]))
            )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f'⚠️  Error tracking clip usage: {e}', flush=True)

def fetch_visuals(keywords, topic_id, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    clips = []
    for i, keyword in enumerate(keywords):
        print(f'Searching for: {keyword}', flush=True)
        resp = requests.get(
            'https://api.pexels.com/videos/search',
            headers={'Authorization': PEXELS_KEY},
            params={'query': keyword, 'orientation': 'portrait', 'per_page': 5},
            timeout=15
        )
        if resp.status_code != 200:
            print(f'  Pexels API error {resp.status_code} for: {keyword}', flush=True)
            continue
        videos = resp.json().get('videos', [])
        downloaded = False
        for video in videos:
            if video.get('duration', 0) >= 4:
                files = sorted(video.get('video_files', []),
                             key=lambda f: f.get('height', 0), reverse=True)
                hd = next((f for f in files if f.get('height', 0) <= 1920), None)
                if hd:
                    clip_url = hd['link']
                    
                    # Skip if already used or excluded
                    if is_clip_used(clip_url):
                        print(f'  ⏭️ Skipping already-used clip: {clip_url}', flush=True)
                        continue
                    
                    if is_clip_excluded(clip_url):
                        print(f'  🚫 Skipping excluded clip: {clip_url}', flush=True)
                        continue
                    
                    path = os.path.join(output_dir, f'clip{i}.mp4')
                    r = requests.get(clip_url, stream=True, timeout=60)
                    with open(path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Track this clip usage
                    track_clip_usage(clip_url, topic_id)
                    
                    clips.append({'path': path, 'keyword': keyword})
                    print(f'  ✅ Downloaded: {path}', flush=True)
                    downloaded = True
                    break
        if not downloaded:
            print(f'  No video found for: {keyword}', flush=True)
    print(json.dumps({'clips': clips}))

if __name__ == '__main__':
    keywords = json.loads(sys.argv[1])
    topic_id = sys.argv[2]
    output_dir = sys.argv[3]
    fetch_visuals(keywords, topic_id, output_dir)
