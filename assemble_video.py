import sys
import json
import subprocess
import os
import tempfile

def assemble_video(topic_id, clips_json, voice_path, output_path):
    clips = json.loads(clips_json)
    tmpdir = tempfile.mkdtemp()

    # Get voice duration
    probe = subprocess.run([
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', voice_path
    ], capture_output=True, text=True)
    streams = json.loads(probe.stdout)['streams']
    voice_duration = float(next(s for s in streams if 'duration' in s)['duration'])
    seg_duration = voice_duration / len(clips)
    print(f'Voice duration: {voice_duration:.2f}s | Segment: {seg_duration:.2f}s')

    # Process each clip
    processed = []
    for i, clip in enumerate(clips):
        out = f'{tmpdir}/clip{i}.mp4'
        subprocess.run([
            'ffmpeg', '-y', '-i', clip['path'],
            '-t', str(seg_duration),
            '-vf', f'scale=1920:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,zoompan=z=\'min(zoom+0.0015,1.5)\':d=1:x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':s=1080x1920',
            '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', out
        ], capture_output=True, check=True)
        processed.append(out)
        print(f'Processed clip {i+1}/{len(clips)}')

    # Concatenate clips
    concat_file = f'{tmpdir}/concat.txt'
    with open(concat_file, 'w') as f:
        for p in processed:
            f.write(f"file '{p}'\n")

    bg_video = f'{tmpdir}/background.mp4'
    subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', concat_file, '-c', 'copy', bg_video
    ], capture_output=True, check=True)
    print('Clips concatenated')

    # Generate subtitles
    srt_path = f'{tmpdir}/subtitles.srt'
    from faster_whisper import WhisperModel
    model = WhisperModel('tiny', device='cpu', compute_type='int8')
    segments, _ = model.transcribe(voice_path, language='en', word_timestamps=True)
    def fmt(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t % 1) * 1000)
        return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

    srt_lines = []
    counter = 1
    for seg in segments:
        words = list(seg.words) if hasattr(seg, 'words') else []
        if words:
            # Use real word-level timestamps
            for word in words:
                text = word.word.strip()
                if not text:
                    continue
                srt_lines.append(f'{counter}\n{fmt(word.start)} --> {fmt(word.end)}\n{text}\n')
                counter += 1
        else:
            # Fallback to chunk method if no word timestamps
            chunk_size = 4
            word_list = seg.text.strip().split()
            chunks = [word_list[i:i+chunk_size] for i in range(0, len(word_list), chunk_size)]
            duration = (seg.end - seg.start) / max(len(chunks), 1)
            for j, chunk in enumerate(chunks):
                start = seg.start + j * duration
                end = start + duration
                srt_lines.append(f'{counter}\n{fmt(start)} --> {fmt(end)}\n{" ".join(chunk)}\n')
                counter += 1
    with open(srt_path, 'w') as f:
        f.write('\n'.join(srt_lines))
    print('Subtitles generated')

    # Final render
    subprocess.run([
        'ffmpeg', '-y',
        '-i', bg_video,
        '-i', voice_path,
        '-vf', 'subtitles=' + srt_path,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '192k',
        '-movflags', '+faststart',
        '-shortest', output_path
    ], check=True)

    print(json.dumps({'video_path': output_path, 'duration': voice_duration}))

if __name__ == '__main__':
    assemble_video(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
