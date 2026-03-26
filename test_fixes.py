#!/usr/bin/env python3
"""Test the video generation with subtitle and deduplication fixes"""
import sys
sys.path.insert(0, '.')

import json
import os
import sqlite3
from db import create_job

# Create test job
job_id = create_job('Test Video with Subtitles')
print(f'✅ Created test job: {job_id}')

# Use a hardcoded topic and script for testing
topic = 'Test Video with Subtitles'
script = "Did you know your body does this. Scientists discovered it last year. Its happening right now. Have you seen this before."
keywords = ["body", "scientists", "discovered", "happening"]

# Create output directory
output_dir = f'media/{job_id}'
os.makedirs(output_dir, exist_ok=True)

# Generate test voice using existing function
from generate_voice import generate_voice
voice_path = f'{output_dir}/voice_test.mp3'
print(f'\n🔊 Generating voice...')
generate_voice(script, voice_path)

# Manually fetch a few clips for testing
print(f'\n🎬 Fetching test clips...')
from fetch_visuals import fetch_visuals
fetch_visuals(keywords, job_id, output_dir)

# Get clips that were downloaded
clips_data = []
for i in range(10):
    clip_path = f'{output_dir}/clip{i}.mp4'
    if os.path.exists(clip_path):
        clips_data.append({'path': clip_path, 'keyword': keywords[i] if i < len(keywords) else f'keyword{i}'})

print(f'✅ Found {len(clips_data)} clips')

# Assemble video with subtitles
if clips_data:
    from assemble_video import assemble_video
    video_out = f'{output_dir}/final_test.mp4'
    print(f'\n🎨 Assembling video with subtitles...')
    assemble_video(job_id, json.dumps(clips_data), voice_path, video_out)
    
    if os.path.exists(video_out):
        size = os.path.getsize(video_out)
        print(f'\n✅ Video created: {video_out}')
        print(f'✅ File size: {size:,} bytes')
        
        # Verify video has proper encoding for subtitles
        import subprocess
        probe_result = subprocess.run([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name,width,height,duration',
            '-of', 'json', video_out
        ], capture_output=True, text=True)
        
        if probe_result.returncode == 0:
            info = json.loads(probe_result.stdout)
            if info.get('streams'):
                stream = info['streams'][0]
                print(f'✅ Video codec: {stream.get("codec_name")}')
                print(f'✅ Resolution: {stream.get("width")}x{stream.get("height")}')
                print(f'✅ Duration: {stream.get("duration")} seconds')
    else:
        print(f'❌ Video assembly failed')
else:
    print(f'⚠️ No clips fetched')

# Check clip tracking
print(f'\n📊 Checking clip usage tracking...')
conn = sqlite3.connect('shorts.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM clip_usage')
count = cursor.fetchone()[0]
print(f'✅ {count} clips tracked in database')

if count > 0:
    cursor.execute('SELECT clip_url, job_ids FROM clip_usage ORDER BY last_used DESC LIMIT 2')
    rows = cursor.fetchall()
    for url, job_ids_json in rows:
        job_ids = json.loads(job_ids_json) if job_ids_json else []
        display_url = url[:60] + '...' if len(url) > 60 else url
        print(f'   ✓ {display_url}')
        print(f'     Used in {len(job_ids)} video(s): {job_ids}')

conn.close()

print(f'\n✨ Test complete! Check the video at: {output_dir}/final_test.mp4')
print(f'💡 Try uploading it to YouTube to verify subtitles appear.')
