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

    # 🎬 Process clips
    processed = []
    for i, clip in enumerate(clips):
        out = f'{tmpdir}/clip{i}.mp4'

        subprocess.run([
            'ffmpeg', '-y', '-i', clip['path'],
            '-t', str(seg_duration),
            '-vf',
            "scale=1920:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,fps=30,"
            "zoompan=z='min(zoom+0.0015,1.5)':d=1:"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920",
            '-an',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            out
        ], check=True)

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
    ], check=True)

    # 🧠 Whisper model
    model = WhisperModel('tiny', device='cpu', compute_type='int8')
    segments, _ = model.transcribe(voice_path, language='en', word_timestamps=True)

    def fmt(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t % 1) * 1000)
        return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

    # 🎯 VIRAL STYLE SUBTITLES
    srt_path = f'{tmpdir}/subs.srt'
    ass_path = f'{tmpdir}/subs.ass'

    srt_lines = []
    ass_lines = []

    # ASS HEADER - VIRAL SHORTS CAPTIONS (CLEAN & SMALL)
    ass_header = """
[Script Info]
ScriptType: v4.00+

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Arial Black,24,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,2,60,60,140,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

    ass_lines.append(ass_header)

    counter = 1

    for seg in segments:
        # Use actual Whisper word-level timestamps for PERFECT sync
        for word in seg.words:
            word_text = word.word.strip().upper()
            if not word_text:
                continue
            
            # Use actual word start/end times from Whisper
            start = word.start
            end = word.end

            # SRT (fallback)
            srt_lines.append(
                f'{counter}\n{fmt(start)} --> {fmt(end)}\n{word_text}\n'
            )

            # ASS (styled subtitles) - USE ACTUAL WORD TIMING
            ass_lines.append(
                f"Dialogue: 0,{fmt(start).replace(',', '.')},{fmt(end).replace(',', '.')},Default,,0,0,0,,{{{chr(92)}b1}}{word_text}{{{chr(92)}b0}}"
            )

            counter += 1

    with open(srt_path, 'w') as f:
        f.write('\n'.join(srt_lines))

    with open(ass_path, 'w') as f:
        f.write('\n'.join(ass_lines))

    print("Subtitles generated (viral style)")

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
        # Mix voice narration with background music
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', bg_video,
            '-i', voice_path,
            '-i', music_path,

            '-filter_complex',
            '[2:a]volume=-18dB[m];[1:a][m]amix=inputs=2:duration=first[aout]',

            '-map', '0:v',
            '-map', '[aout]',

            # 🔥 USE ASS (not SRT)
            '-vf', f"ass={ass_path}",

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

            # 🔥 USE ASS (not SRT)
            '-vf', f"ass={ass_path}",

            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',

            '-c:a', 'aac',
            '-b:a', '192k',

            '-movflags', '+faststart',
            '-shortest',

            output_path
        ]
    
    subprocess.run(ffmpeg_cmd, check=True)

    print(json.dumps({
        'video_path': output_path,
        'duration': voice_duration
    }))


if __name__ == '__main__':
    assemble_video(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
