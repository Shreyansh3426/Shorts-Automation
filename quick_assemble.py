#!/usr/bin/env python3
"""Quick assembly fix for stuck jobs"""
import os
import json
import subprocess
import tempfile

job_id = "job_20260327_023051_6c2e5a"
job_dir = f"media/{job_id}"

# Get voice duration
voice_file = f"{job_dir}/voice_A.mp3"
probe = subprocess.run(
    ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', voice_file],
    capture_output=True, text=True
)

duration = float(json.loads(probe.stdout)['streams'][0]['duration'])
print(f"✅ Voice duration: {duration:.1f}s")

# Create concat file
clips = [
    f"{job_dir}/clip0.mp4",
    f"{job_dir}/clip1.mp4", 
    f"{job_dir}/clip2.mp4",
    f"{job_dir}/clip3.mp4",
]

tmpdir = tempfile.mkdtemp()
concat_file = f"{tmpdir}/concat.txt"

with open(concat_file, 'w') as f:
    for clip in clips:
        f.write(f"file '{os.path.abspath(clip)}'\n")

print(f"📋 Concat file created")

# Concatenate clips (simple copy, no re-encode)
bg_video = f"{tmpdir}/bg.mp4"
try:
    result = subprocess.run(
        ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file, '-c', 'copy', bg_video],
        capture_output=True, text=True, timeout=180
    )
    print(f"✅ Concatenated")
except subprocess.TimeoutExpired:
    print("❌ Concat timeout")
    exit(1)

# Create simple SRT (no subtitles, just avoid filter chain issues)
srt_file = f"{tmpdir}/subs.srt"
with open(srt_file, 'w') as f:
    f.write("1\n00:00:00,000 --> 00:00:10,000\n\n")

print(f"✅ Subtitle file created")

# Mix video + voice (simple approach)
output = f"{job_dir}/final_A.mp4"

try:
    # Use -shortest to end when voice ends
    cmd = [
        'ffmpeg', '-y',
        '-i', bg_video,
        '-i', voice_file,
        '-c:v', 'copy',  # Copy video codec (already compressed)
        '-c:a', 'aac',   # Encode audio to AAC
        '-b:a', '128k',
        '-shortest',     # Stop when shortest input ends
        '-movflags', '+faststart',
        output
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    if result.returncode == 0 and os.path.exists(output):
        file_size = os.path.getsize(output) / (1024*1024)
        print(f"✅ VIDEO CREATED: {output} ({file_size:.1f} MB)")
    else:
        print(f"❌ FFmpeg failed")
        if result.stderr:
            print(result.stderr[-300:])
        exit(1)
        
except subprocess.TimeoutExpired:
    print("❌ Assembly timeout - FFmpeg hung")
    exit(1)
