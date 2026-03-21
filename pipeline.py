import sys
import os
import json
import time
import subprocess
from pathlib import Path
from db import init_db, create_job, update_job, get_job
from ab_tester import generate_ab_variants
from alerts import send_failure_alert
from diagnostics import DiagnosticsCollector, format_diagnostic_summary
from auto_repair import AutoRepair, retry_with_backoff
from anomaly_detector import AnomalyDetector, format_anomaly_report, get_recommendations
from run_validator import RunValidator, format_validation_report
from quality_dashboard import QualityDashboard, format_dashboard, get_alerts_from_dashboard

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
    
    # Initialize QA components
    diagnostics = DiagnosticsCollector(media_path)
    auto_repair = AutoRepair()
    validator = RunValidator(media_path)
    dashboard = QualityDashboard(SCRIPTS_DIR)
    
    pipeline_start_time = time.time()

    print(f'\n[JOB] {job_id}')
    print(f'[TOPIC] {topic}')
    
    # Check system resources before starting
    diagnostics.check_system_resources()

    # Stage 1 - Script
    print('\n[1/4] Generating script...')
    diagnostics.stage_start('script_generation')
    try:
        def do_script():
            return run_script('generate_script.py', [topic])
        result = run_with_retry(do_script)
        script = result['script']
        keywords = result['keywords']
        diagnostics.log_api_call('groq', status=200, duration=2.5)
        diagnostics.stage_complete('script_generation')
        update_job(job_id, status='scripted', script=script, keywords=json.dumps(keywords))
        print(f'  Script: {script[:60]}...')
        print(f'  Keywords: {keywords}')
    except Exception as e:
        diagnostics.log_error(str(e), 'script_generation')
        diagnostics.stage_complete('script_generation', success=False)
        update_job(job_id, status='failed', error=str(e))
        print(f'  FAILED: {e}')
        return None

    # Pre-Stage: Generate A/B variants (ready to flip switch tomorrow)
    try:
        variants = generate_ab_variants(topic, script, keywords)
        print(f'  A/B variants generated: 3 ready')
    except Exception as e:
        print(f'  ⚠️  A/B generation failed, using base script only')
        variants = [{"variant": "BASE", "script": script, "title_hook": ""}]

    # Process all variants (A/B/C testing active)
    AB_MODE = True  # All variants uploaded per topic
    variants_to_process = variants if AB_MODE else [variants[0]]
    
    for variant_idx, variant in enumerate(variants_to_process):
        variant_script = variant['script']
        variant_id = variant.get('variant', 'A')
        variant_job_id = f"{job_id}_{variant_id}" if len(variants_to_process) > 1 else job_id
        
        print(f'\n[VARIANT {variant_id}] Processing...')

        # Stage 2 - Voice
        print('\n[2/4] Generating voice...')
        variant_voice_path = os.path.join(media_path, f'voice_{variant_id}.mp3')
        diagnostics.stage_start('voice_generation')
        try:
            def do_voice():
                return run_script('generate_voice.py', [variant_script, variant_voice_path])
            result = run_with_retry(do_voice)
            
            # Validate audio file
            is_valid, msg = validator.validate_file_integrity(variant_voice_path)
            if is_valid:
                diagnostics.check_file_exists(variant_voice_path)
                diagnostics.check_file_size(variant_voice_path, min_bytes=50000)
            else:
                diagnostics.log_warning(f'Voice file validation: {msg}')
            
            diagnostics.stage_complete('voice_generation')
            update_job(job_id, status='voiced', voice_path=variant_voice_path)
            print(f'  Voice saved: {variant_voice_path}')
        except Exception as e:
            diagnostics.log_error(str(e), 'voice_generation')
            diagnostics.stage_complete('voice_generation', success=False)
            update_job(job_id, status='failed', error=str(e))
            print(f'  FAILED: {e}')
            continue

        # Stage 3 - Visuals
        print('\n[3/4] Fetching visuals...')
        diagnostics.stage_start('visual_fetching')
        try:
            def do_visuals():
                return run_script('fetch_visuals.py', [json.dumps(keywords), job_id, media_path])
            result = run_with_retry(do_visuals)
            clips = result['clips']
            if not clips:
                raise Exception('No clips returned from Pexels')
            
            # Log API call
            diagnostics.log_api_call('pexels', status=200, results=len(clips))
            
            # Validate clips file
            clips_file = os.path.join(media_path, f'clips_{variant_id}.json')
            is_valid, msg = validator.validate_file_integrity(clips_file)
            if is_valid:
                diagnostics.check_file_exists(clips_file)
            else:
                diagnostics.log_warning(f'Clips file validation: {msg}')
            
            diagnostics.stage_complete('visual_fetching')
            update_job(job_id, status='fetched', clips_json=json.dumps(clips))
            print(f'  Downloaded {len(clips)} clips')
        except Exception as e:
            diagnostics.log_error(str(e), 'visual_fetching')
            diagnostics.log_api_call('pexels', status=500, error=str(e))
            diagnostics.stage_complete('visual_fetching', success=False)
            update_job(job_id, status='failed', error=str(e))
            print(f'  FAILED: {e}')
            continue

        # Stage 4 - Assemble
        print('\n[4/4] Assembling video...')
        variant_output_path = os.path.join(media_path, f'final_{variant_id}.mp4')
        diagnostics.stage_start('video_assembly')
        try:
            def do_assemble():
                return run_script('assemble_video.py', [
                    job_id, json.dumps(clips), variant_voice_path, variant_output_path
                ])
            result = run_with_retry(do_assemble)
            
            # Validate video file
            is_valid, msg = validator.validate_file_integrity(variant_output_path)
            if is_valid:
                diagnostics.check_file_exists(variant_output_path)
                diagnostics.check_file_size(variant_output_path, min_bytes=500000)
            else:
                diagnostics.log_warning(f'Video file validation: {msg}')
            
            diagnostics.stage_complete('video_assembly')
            update_job(job_id, status='done', video_path=variant_output_path)
            print(f'  Video saved: {variant_output_path}')
            print(f'  Duration: {result["duration"]}s')
        except Exception as e:
            diagnostics.log_error(str(e), 'video_assembly')
            diagnostics.stage_complete('video_assembly', success=False)
            update_job(job_id, status='failed', error=str(e))
            print(f'  FAILED: {e}')
            continue

        # Stage 5 - Upload
        print('\n[5/5] Uploading to YouTube...')
        diagnostics.stage_start('upload')
        try:
            from upload_youtube import upload_video
            title = topic[:90] + ' #Shorts'
            variant_title_hook = variant.get('title_hook', '')
            
            def do_upload():
                result = json.loads(upload_video(variant_output_path, title, description='', tags=None, job_id=job_id, topic=topic, clips_json=clips, script=variant_script, keywords=keywords, variant_id=variant_id, title_hook=variant_title_hook))
                return result
            
            result = run_with_retry(do_upload)
            diagnostics.log_api_call('youtube', status=200, video_id=result['video_id'])
            diagnostics.stage_complete('upload')
            update_job(job_id, status='uploaded', youtube_id=result['video_id'])
            print(f'  YouTube: {result["url"]}')
        except FileNotFoundError as e:
            diagnostics.log_warning(f'YouTube upload: {str(e)}')
            diagnostics.stage_complete('upload', success=False)
            update_job(job_id, status='completed', error='YouTube upload skipped - credentials not found')
            print(f'  ⚠️  {e}')
        except Exception as e:
            error_type = auto_repair.classify_error(str(e))
            diagnostics.log_error(str(e), 'upload', error_type=error_type)
            diagnostics.log_api_call('youtube', status=500, error=str(e))
            diagnostics.stage_complete('upload', success=False)
            update_job(job_id, status='failed_upload', error=str(e))
            print(f'  Upload FAILED: {e}')
            continue

    # ===== QUALITY ASSURANCE SUITE =====
    
    # Generate diagnostic report
    pipeline_duration = time.time() - pipeline_start_time
    diagnostics.total_duration_sec = pipeline_duration
    
    # Final validation of complete run
    validation = validator.validate_run(topic, variant_count=3 if AB_MODE else 1)
    diagnostics.validation_result = validation
    
    # Generate and save diagnostic report
    report = diagnostics.generate_report()
    diagnostics.save_report(os.path.join(media_path, 'diagnostics.json'))
    print(format_diagnostic_summary(report))
    
    # Check for performance anomalies
    anomaly_detector = AnomalyDetector(media_path)
    anomaly_detector.add_run(report)
    anomalies = anomaly_detector.detect_anomalies(report)
    
    if anomalies:
        print(format_anomaly_report(anomalies))
        recommendations = get_recommendations(anomalies)
        for rec in recommendations:
            print(f'  💡 {rec}')
    else:
        print('\n✅ No anomalies detected')
    
    # Update quality dashboard
    dashboard.update_from_diagnostics(report)
    if validation["status"] == "valid":
        print(format_dashboard(dashboard))
        
        # Check for alerts
        alerts = get_alerts_from_dashboard(dashboard)
        if alerts:
            print('\n🚨 Dashboard Alerts:')
            for alert in alerts:
                print(f'  [{alert["severity"].upper()}] {alert["message"]}')
    
    print(f'\n✅ Job complete: {job_id}')
    return job_id

if __name__ == '__main__':
    try:
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
            result = run_pipeline(topic)
    except Exception as e:
        job_id = os.getenv('CURRENT_JOB_ID', 'unknown')
        stage = os.getenv('CURRENT_STAGE', 'orchestration')
        error_info = f'{stage}: {str(e)}'
        
        # Classify error type
        auto_repair = AutoRepair()
        error_type = auto_repair.classify_error(str(e))
        suggestion = auto_repair.get_recovery_suggestion(str(e))
        
        print(f'\n❌ Pipeline Error: {error_type}')
        print(f'💡 Suggestion: {suggestion}')
        
        send_failure_alert(job_id, error_info, stage)
        raise
