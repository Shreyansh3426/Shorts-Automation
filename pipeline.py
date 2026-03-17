import sys
import os
import json
import time
import subprocess
from db import init_db, create_job, update_job, get_job

MEDIA_DIR = os.path.join(os.path.dirname(__file__), 'media')
SCRIPTS_DIR = os.path.dirname(__file__)
PYTHON = sys.executable

def run_with_retry(fn, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            wait = 2 ** attempt
            print(f'  Attempt {attempt+1} failed: {e}. Retrying in {wait}s...')
            time.sleep(wait)

def run_script(script_name, args):
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    result = subprocess.run(
        [PYTHON, script_path] + args,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise Exception(f'{script_name} failed:\n{result.stderr}')
    last_line = [l for l in result.stdout.strip().split('\n') if l.strip()][-1]
    return json.loads(last_line)

def run_pipeline(topic):
    init_db()
    job_id = create_job(topic)
    media_path = os.path.join(MEDIA_DIR, job_id)
    os.makedirs(media_path, exist_ok=True)

    print(f'\n[JOB] {job_id}')
    print(f'[TOPIC] {topic}')

    # Stage 1 - Script
    print('\n[1/4] Generating script...')
    try:
        def do_script():
            return run_script('generate_script.py', [topic])
        result = run_with_retry(do_script)
        script = result['script']
        keywords = result['keywords']
        update_job(job_id, status='scripted', script=script, keywords=json.dumps(keywords))
        print(f'  Script: {script[:60]}...')
        print(f'  Keywords: {keywords}')
    except Exception as e:
        update_job(job_id, status='failed', error=str(e))
        print(f'  FAILED: {e}')
        return None

    # Stage 2 - Voice
    print('\n[2/4] Generating voice...')
    voice_path = os.path.join(media_path, 'voice.mp3')
    try:
        def do_voice():
            return run_script('generate_voice.py', [script, voice_path])
        result = run_with_retry(do_voice)
        update_job(job_id, status='voiced', voice_path=voice_path)
        print(f'  Voice saved: {voice_path}')
    except Exception as e:
        update_job(job_id, status='failed', error=str(e))
        print(f'  FAILED: {e}')
        return None

    # Stage 3 - Visuals
    print('\n[3/4] Fetching visuals...')
    try:
        def do_visuals():
            return run_script('fetch_visuals.py', [json.dumps(keywords), job_id, media_path])
        result = run_with_retry(do_visuals)
        clips = result['clips']
        if not clips:
            raise Exception('No clips returned from Pexels')
        update_job(job_id, status='fetched', clips_json=json.dumps(clips))
        print(f'  Downloaded {len(clips)} clips')
    except Exception as e:
        update_job(job_id, status='failed', error=str(e))
        print(f'  FAILED: {e}')
        return None

    # Stage 4 - Assemble
    print('\n[4/4] Assembling video...')
    output_path = os.path.join(media_path, 'final.mp4')
    try:
        def do_assemble():
            return run_script('assemble_video.py', [
                job_id, json.dumps(clips), voice_path, output_path
            ])
        result = run_with_retry(do_assemble)
        update_job(job_id, status='done', video_path=output_path)
        print(f'  Video saved: {output_path}')
        print(f'  Duration: {result["duration"]}s')
    except Exception as e:
        update_job(job_id, status='failed', error=str(e))
        print(f'  FAILED: {e}')
        return None

    # Stage 5 - Upload
    print('\n[5/5] Uploading to YouTube...')
    try:
        from upload_youtube import upload_video
        title = topic[:90] + ' #Shorts'
        def do_upload():
            result = json.loads(upload_video(output_path, title, script, keywords))
            return result
        result = run_with_retry(do_upload)
        update_job(job_id, status='uploaded', youtube_id=result['video_id'])
        print(f'  YouTube: {result["url"]}')
    except Exception as e:
        update_job(job_id, status='failed_upload', error=str(e))
        print(f'  Upload FAILED: {e}')
        return None

    # Stage 5 - DISABLED FOR TESTING
    return job_id
    print('\n[5/5] Uploading to YouTube...')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        from topic_queue import get_next_topic, mark_topic_used
        topic_row = get_next_topic()
        if not topic_row:
            print('No topics in queue. Run: python3 topic_queue.py')
            sys.exit(1)
        topic = topic_row['title']
        topic_id = topic_row['id']
        print(f'Auto-picked topic from queue: {topic}')
        result = run_pipeline(topic)
        if result:
            mark_topic_used(topic_id)
    else:
        topic = ' '.join(sys.argv[1:])
        run_pipeline(topic)
