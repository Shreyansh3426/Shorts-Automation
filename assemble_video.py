import json
import subprocess
import os
import tempfile
import random
import sys

from faster_whisper import WhisperModel


def assemble_video(topic_id, clips_json, voice_path, output_path):
    clips = json.loads(clips_json)
    tmpdir = tempfile.mkdtemp()

    # 🎧 Voice duration
    probe = subprocess.run([
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', voice_path
    ], capture_output=True, text=True)

    streams = json.loads(probe.stdout)['streams']
    voice_duration = float(next(s for s in streams if 'duration' in s)['duration'])

    seg_duration = voice_duration / len(clips)
    print(f'Voice duration: {voice_duration:.2f}s | Segment: {seg_duration:.2f}s')

    # 🎬 Process clips (with timeout protection)
    processed = []
    for i, clip in enumerate(clips):
        out = f'{tmpdir}/clip{i}.mp4'

        try:
            subprocess.run([
                'ffmpeg', '-y', '-i', clip['path'],
                '-t', str(seg_duration),
                '-vf',
                "scale=1920:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,fps=30,"
                "eq=brightness=0.01:saturation=1.05",
                '-an',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                out
            ], check=True, timeout=120)
        except subprocess.TimeoutExpired:
            print(f'⚠️  Timeout on clip {i} - retrying with simpler filter')
            subprocess.run([
                'ffmpeg', '-y', '-i', clip['path'],
                '-t', str(seg_duration),
                '-vf',
                "scale=1080:1920:force_original_aspect_ratio=decrease,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30",
                '-an',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-crf', '25',
                out
            ], check=True, timeout=120)

        processed.append(out)

    # 🔗 Concatenate
    concat_file = f'{tmpdir}/concat.txt'
    with open(concat_file, 'w') as f:
        for p in processed:
            f.write(f"file '{p}'\n")

    bg_video = f'{tmpdir}/background.mp4'

    subprocess.run([
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0',
        '-i', concat_file,
        '-c', 'copy',
        bg_video
    ], check=True, timeout=180)

    # 🧠 Whisper model
    model = WhisperModel('tiny', device='cpu', compute_type='int8')
    segments, _ = model.transcribe(voice_path, language='en', word_timestamps=True)

    def fmt(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t % 1) * 1000)
        return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

    # 🎯 WINNING SUBTITLE STYLE (4 words per line - 597 view winner!)
    srt_path = f'{tmpdir}/subs.srt'

    srt_lines = []
    counter = 1

    for seg in segments:
        words = [w.word.strip() for w in seg.words if w.word.strip()]
        
        if not words:
            continue

        # 4 words per line with EVEN timing split
        chunk_size = 4
        chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
        
        # Divide segment duration evenly across chunks
        duration = (seg.end - seg.start) / len(chunks)

        for i, chunk in enumerate(chunks):
            start = seg.start + i * duration
            end = start + duration

            text = " ".join(chunk)

            # Simple SRT format - let FFmpeg handle styling
            srt_lines.append(
                f'{counter}\n{fmt(start)} --> {fmt(end)}\n{text}\n'
            )
            counter += 1

    with open(srt_path, 'w') as f:
        f.write('\n'.join(srt_lines))

    print("Subtitles generated (4-word formula)")

    # 🎵 Music (Optional - check if available)
    music_dir = os.path.join(os.path.dirname(__file__), 'assets', 'music')
    music_path = None
    
    # Ensure music directory exists
    if not os.path.exists(music_dir):
        os.makedirs(music_dir, exist_ok=True)
    
    music_files = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
    
    if music_files:
        music_path = os.path.join(music_dir, random.choice(music_files))
        print(f"🎵 Using background music: {os.path.basename(music_path)}")
    else:
        print("⚠️  No music files in assets/music/ - video will only have voice narration")

    # 🎬 FINAL RENDER
    if music_path:
        # Professional sidechain ducking: Music volume ducks when voice is speaking
        # Setup: Voice acts as sidechain input to compress background music
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', bg_video,
            '-i', voice_path,
            '-i', music_path,

            '-filter_complex',
            # Sidechain ducking: music ducks automatically when voice is loud
            '[2:a]aformat=sample_rates=44100[music];'
            '[1:a]aformat=sample_rates=44100[voice];'
            '[music][voice]acompressor=threshold=0.1:ratio=4:attack=50:release=200:makeup=3[music_compressed];'
            '[voice][music_compressed]amix=inputs=2:duration=first[aout]',

            '-map', '0:v',
            '-map', '[aout]',

            '-vf', f"subtitles={srt_path}:force_style='MarginV=180'",

            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',

            '-c:a', 'aac',
            '-b:a', '192k',

            '-movflags', '+faststart',
            '-shortest',

            output_path
        ]
    else:
        # Use only voice narration (no background music)
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', bg_video,
            '-i', voice_path,

            '-map', '0:v',
            '-map', '1:a',

            '-vf', f"subtitles={srt_path}:force_style='MarginV=180'",

            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',

            '-c:a', 'aac',
            '-b:a', '192k',

            '-movflags', '+faststart',
            '-shortest',

            output_path
        ]
    
    subprocess.run(ffmpeg_cmd, check=True, timeout=300)

    print(json.dumps({
        'video_path': output_path,
        'duration': voice_duration
    }))


if __name__ == '__main__':
    assemble_video(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
