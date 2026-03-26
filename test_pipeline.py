#!/usr/bin/env python3
"""Test the updated pipeline with subtitle and deduplication fixes"""
import sys
sys.path.insert(0, '.')

from db import create_job
from fetch_visuals import fetch_visuals
from generate_script import generate_script  
from generate_voice import generate_voice
from assemble_video import assemble_video
import json
import os
import sqlite3

# Create test job
job_id = create_job('AI Secrets Scientists Dont Want You to Know')
print(f'✅ Created job: {job_id}')

# Generate script
script, keywords = generate_script('AI Secrets Scientists Dont Want You to Know')
print(f'✅ Generated script with {len(keywords)} keywords: {keywords}')

# Fetch clips
output_dir = f'media/{job_id}'
os.makedirs(output_dir, exist_ok=True)

print(f'\n📝 Fetching clips for keywords...')
fetch_visuals(keywords, job_id, output_dir)

# Generate voice
voice_path = f'{output_dir}/voice_test.mp3'
print(f'\n🔊 Generating voice...')
generate_voice(script, voice_path)
print(f'✅ Generated voice: {voice_path}')

# Get clips that were downloaded
clips_data = []
for i in range(10):
    clip_path = f'{output_dir}/clip{i}.mp4'
    if os.path.exists(clip_path):
        clips_data.append({'path': clip_path, 'keyword': keywords[i] if i < len(keywords) else 'unknown'})

print(f'\n🎬 Found {len(clips_data)} clips for assembly')

# Assemble video
if clips_data:
    video_out = f'{output_dir}/final_A.mp4'
    print(f'\n🎨 Assembling video with subtitles...')
    assemble_video(job_id, json.dumps(clips_data), voice_path, video_out)
    
    if os.path.exists(video_out):
        size = os.path.getsize(video_out)
        print(f'✅ Video created successfully: {video_out} ({size} bytes)')
    else:
        print(f'❌ Video assembly failed')
else:
    print(f'❌ No clips fetched - unable to assemble')

# Check clip usage tracking
print(f'\n📊 Checking clip usage tracking in database...')
conn = sqlite3.connect('shorts.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM clip_usage')
count = cursor.fetchone()[0]
print(f'✅ {count} clips tracked in database')

cursor.execute('SELECT clip_url, job_ids FROM clip_usage LIMIT 3')
rows = cursor.fetchall()
for url, job_ids_json in rows:
    job_ids = json.loads(job_ids_json) if job_ids_json else []
    print(f'   - {url[:60]}... used in {len(job_ids)} video(s)')

conn.close()

print(f'\n✨ Pipeline test complete!')
