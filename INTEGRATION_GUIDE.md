# Autonomous Quality Assurance Integration Guide

This guide explains how to integrate the new QA modules into the pipeline for autonomous operation.

## New Modules Overview

### 1. **diagnostics.py** - System Health Monitoring
Tracks every aspect of pipeline execution:
- System resources (CPU, memory, disk)
- Stage performance (duration per stage)
- API call success/failure rates
- File validation (exists, size checks)

**Key Class:** `DiagnosticsCollector`
```python
diagnostics = DiagnosticsCollector(job_folder)
diagnostics.stage_start("script_generation")
# ... run stage ...
diagnostics.stage_complete("script_generation")
diagnostics.log_api_call("groq", status=200, duration=2.5)
report = diagnostics.generate_report()
```

### 2. **auto_repair.py** - Autonomous Error Recovery
Classifies errors and applies recovery strategies:
- Exponential backoff retry (1s → 2s → 4s)
- Quota-aware waiting (1 hour for 403 errors)
- Missing file fallback handling
- Batch size reduction for memory issues

**Key Class:** `AutoRepair`
```python
from auto_repair import AutoRepair, retry_with_backoff, quota_aware_retry

# Wrap risky calls:
@retry_with_backoff(max_retries=3)
def fetch_videos():
    return api.get_trending_videos()

# Or use directly:
auto_repair = AutoRepair()
error = "429 Rate limit exceeded"
suggestion = auto_repair.get_recovery_suggestion(error)
```

### 3. **anomaly_detector.py** - Pattern Analysis & Alerting
Detects unusual behavior patterns:
- Performance degradation (50%+ slower than baseline)
- Elevated error rates (2x above baseline)
- Stage timeouts (2.5x historical average)
- Resource constraints (disk >85%, memory >80%)
- API quota exhaustion (403 errors)

**Key Class:** `AnomalyDetector`
```python
anomaly_detector = AnomalyDetector(job_folder)
anomaly_detector.add_run(current_run_data)
anomalies = anomaly_detector.detect_anomalies(new_run)
report = format_anomaly_report(anomalies)
recommendations = get_recommendations(anomalies)
```

### 4. **run_validator.py** - Output Completeness Validation
Ensures all expected artifacts are generated:
- Required directories (visuals, voice, videos)
- Script files (valid JSON with correct variant count)
- Audio/video files (proper codecs and formats)
- Metadata and upload status
- File integrity checks

**Key Class:** `RunValidator`
```python
validator = RunValidator(job_folder)
validation = validator.validate_run(topic="AI", variant_count=3)
report = format_validation_report(validation)
if validation["status"] == "invalid":
    # Handle missing/corrupt files
```

### 5. **quality_dashboard.py** - Comprehensive Metrics
Aggregates all metrics for system-wide health:
- Pipeline health (success rate, average duration)
- Content metrics (views, engagement rate)
- Performance trends
- System resource usage trends
- Overall health score (0-100)

**Key Class:** `QualityDashboard`
```python
dashboard = QualityDashboard(workspace_root)
dashboard.update_from_diagnostics(diagnostics_report)
dashboard.update_from_analytics(youtube_stats)
health_scores = dashboard.get_health_score()
trends = dashboard.get_trend_analysis()
alerts = get_alerts_from_dashboard(dashboard)
```

## Integration Pattern

Here's the recommended integration flow in `pipeline.py`:

```python
from diagnostics import DiagnosticsCollector, format_diagnostic_summary
from auto_repair import AutoRepair, retry_with_backoff
from anomaly_detector import AnomalyDetector
from run_validator import RunValidator, format_validation_report
from quality_dashboard import QualityDashboard, format_dashboard

def run_pipeline(topic: str):
    # Initialize all QA components
    diagnostics = DiagnosticsCollector(job_folder)
    auto_repair = AutoRepair()
    validator = RunValidator(job_folder)
    dashboard = QualityDashboard(workspace_root)
    
    try:
        # Stage 1: Trend Mining
        diagnostics.stage_start("trend_mining")
        trending_topics = trend_miner.get_trending()
        diagnostics.stage_complete("trend_mining")
        
        # Stage 2: Script Generation (with auto-repair)
        diagnostics.stage_start("script_generation")
        @retry_with_backoff(max_retries=3)
        def generate_with_retry():
            return generate_script.create_script(topic)
        
        scripts = generate_with_retry()
        diagnostics.stage_complete("script_generation")
        diagnostics.log_api_call("groq", status=200, duration=2.5)
        
        # ... rest of stages ...
        
        # Final validation
        validation = validator.validate_run(topic, variant_count=3)
        diagnostics.set_validation_result(validation)
        
        # Generate diagnostic report
        report = diagnostics.generate_report()
        diagnostics.save_report(os.path.join(job_folder, 'diagnostics.json'))
        print(format_diagnostic_summary(report))
        
        # Check for anomalies
        anomaly_detector = AnomalyDetector(job_folder)
        anomaly_detector.add_run(report)
        anomalies = anomaly_detector.detect_anomalies(report)
        if anomalies:
            print(format_anomaly_report(anomalies))
            recommendations = get_recommendations(anomalies)
            for rec in recommendations:
                print(f"  💡 {rec}")
        
        # Update dashboard
        dashboard.update_from_diagnostics(report)
        if validation["status"] == "valid":
            print(format_dashboard(dashboard))
        
        return True
        
    except Exception as e:
        error_type = auto_repair.classify_error(str(e))
        suggestion = auto_repair.get_recovery_suggestion(str(e))
        diagnostics.log_error(str(e), error_type)
        
        print(f"❌ Pipeline failed: {error_type}")
        print(f"💡 Suggestion: {suggestion}")
        
        # Save diagnostic report even on failure
        report = diagnostics.generate_report()
        diagnostics.save_report(os.path.join(job_folder, 'diagnostics.json'))
        
        return False
```

## Stage-by-Stage Integration

### Trend Mining Stage
```python
diagnostics.stage_start("trend_mining")
diagnostics.check_system_resources()  # Check before API call

try:
    @retry_with_backoff(max_retries=3)
    def fetch_trends():
        return trend_miner.get_trending()
    
    topics = fetch_trends()
    diagnostics.log_api_call("pexels", status=200, results=len(topics))

except Exception as e:
    diagnostics.log_api_call("pexels", status=500, error=str(e))
    raise

diagnostics.stage_complete("trend_mining")
```

### Script Generation Stage (with Groq)
```python
diagnostics.stage_start("script_generation")

@retry_with_backoff(max_retries=3)
def generate_scripts():
    scripts = []
    for variant in ["A", "B", "C"]:
        script = generate_script.create_script(topic, variant)
        scripts.append(script)
    return scripts

try:
    scripts = generate_scripts()
    diagnostics.log_api_call("groq", status=200, duration=2.5, tokens=1500)
except Exception as e:
    if "429" in str(e):  # Rate limit
        wait_time = quota_aware_retry(lambda: generate_scripts())
    raise

diagnostics.stage_complete("script_generation")
```

### Voice Generation Stage (with Edge-TTS + validation)
```python
diagnostics.stage_start("voice_generation")

for variant, script in zip(["A", "B", "C"], scripts):
    voice_file = generate_voice.create_voice(script, variant)
    
    # Validate audio file
    is_valid, msg = validator.validate_file_integrity(voice_file)
    if is_valid:
        diagnostics.check_file_exists(voice_file)
    else:
        diagnostics.log_warning(f"Invalid audio for variant {variant}: {msg}")

diagnostics.stage_complete("voice_generation")
```

### Visual Fetching Stage (with API retry)
```python
diagnostics.stage_start("visual_fetching")
diagnostics.log_api_call("pexels", status=200, calls=1)

@retry_with_backoff(max_retries=3)
def fetch_visuals():
    return fetch_visuals.get_clips_for_topic(topic, keywords)

try:
    visuals = fetch_visuals()
except Exception as e:
    diagnostics.log_api_call("pexels", status=429, error="Quota exceeded")
    raise

diagnostics.stage_complete("visual_fetching")
```

### Video Assembly Stage (with resource monitoring)
```python
diagnostics.stage_start("video_assembly")

for variant in ["A", "B", "C"]:
    video_file = assemble_video.create_video(
        script=scripts[variant],
        voice=voices[variant],
        clips=visuals
    )
    
    # Validate video
    is_valid, msg = validator.validate_file_integrity(video_file)
    if is_valid:
        diagnostics.check_file_size(video_file, min_bytes=1000000)

diagnostics.stage_complete("video_assembly")
```

### Upload Stage (with comprehensive validation)
```python
diagnostics.stage_start("upload")

for variant in ["A", "B", "C"]:
    try:
        @retry_with_backoff(max_retries=2)
        def upload_with_retry():
            return upload_youtube.upload_video(
                video_path=videos[variant],
                title=titles[variant],
                thumbnail=thumbnails[variant]
            )
        
        result = upload_with_retry()
        diagnostics.log_api_call("youtube", status=200, video_id=result["id"])
        
    except Exception as e:
        diagnostics.log_api_call("youtube", status=500, error=str(e))

diagnostics.stage_complete("upload")
```

## Integration Checklist

- [ ] **Import statements**: Add all QA module imports to `pipeline.py`
- [ ] **Initialization**: Create diagnostic collector at pipeline start
- [ ] **Stage wrapping**: Wrap each major stage with `diagnostics.stage_start/complete()`
- [ ] **API calls**: Log all API calls with `diagnostics.log_api_call()`
- [ ] **File validation**: Validate outputs with `validator.validate_file_integrity()`
- [ ] **Error handling**: Use `auto_repair.classify_error()` for proper categorization
- [ ] **Anomaly detection**: Add `AnomalyDetector` at end of run
- [ ] **Dashboard update**: Update `QualityDashboard` with final metrics
- [ ] **Report saving**: Save diagnostic report to job folder
- [ ] **GitHub Actions**: Update workflows to preserve diagnostic reports

## Output Structure

After integration, each run will produce:

```
media/job_20260318_004253_bfee03/
├── script.json              # Generated scripts (validated)
├── voice/
│   ├── voice_A.mp3
│   ├── voice_B.mp3
│   └── voice_C.mp3
├── visuals/
│   ├── clips_A.json
│   ├── clips_B.json
│   └── clips_C.json
├── videos/
│   ├── video_A.mp4
│   ├── video_B.mp4
│   └── video_C.mp4
├── thumbnail_A.jpg
├── thumbnail_B.jpg
├── thumbnail_C.jpg
├── metadata.json
├── upload_status.json
├── diagnostics.json         # NEW: Comprehensive run report
└── quality_metrics.json (workspace root) # NEW: Aggregated metrics
```

## Monitoring & Alerts

### Diagnostic Report Example
```json
{
  "status": "success",
  "total_duration_sec": 480,
  "stages": {
    "script_generation": {"duration_sec": 8, "status": "success"},
    "voice_generation": {"duration_sec": 12, "status": "success"},
    "visual_fetching": {"duration_sec": 25, "status": "success"},
    "video_assembly": {"duration_sec": 420, "status": "success"},
    "upload": {"duration_sec": 15, "status": "success"}
  },
  "system": {
    "disk_usage_percent": 45,
    "memory_percent": 62,
    "cpu_percent": 35
  },
  "api_calls": {
    "groq": [{"status": 200, "duration": 2.5}],
    "pexels": [{"status": 200, "results": 40}],
    "youtube": [{"status": 200, "video_id": "abc123"}]
  },
  "errors": [],
  "warnings": []
}
```

### Anomaly Detection Example
```
⚠️  ANOMALIES DETECTED (2):

🟡 WARNING:
  • Pipeline took 720s (avg 480s) - 50% slower than normal
  • Memory usage: 85%

💡 Recommendations:
  • Check for background processes or system load increases
  • Reduce batch size or process fewer videos per run
```

### Quality Dashboard Example
```
🟢 QUALITY DASHBOARD

📊 HEALTH SCORES:
  Overall:        87.5/100
  Reliability:    95.0/100
  Content:        82.0/100
  Performance:    88.5/100
  System:         85.0/100

🔧 PIPELINE STATISTICS:
  Total Runs:     15
  Success Rate:   93.3%
  Avg Duration:   480s

📹 CONTENT STATISTICS:
  Total Videos:   45
  Total Views:    32,457
  Avg Per Video:  722
  Engagement:     0.87%

📈 TRENDS:
  • Pipeline Success: 95% (improving)
  • Content Views: 722 average (growing)
  • Engagement Rate: 0.87% (excellent)
  • Disk Usage: 45% (stable, healthy)
```

## Testing Integration

### 1. Local Test
```python
# test_qa_integration.py
from diagnostics import DiagnosticsCollector
from run_validator import RunValidator

job_folder = "test_job"
diagnostics = DiagnosticsCollector(job_folder)
diagnostics.stage_start("test_stage")
diagnostics.stage_complete("test_stage")
report = diagnostics.generate_report()
print(report)
```

### 2. Next Production Run
The integration will automatically:
1. Collect metrics from every stage
2. Validate all outputs
3. Generate diagnostic report
4. Detect any anomalies
5. Update quality dashboard
6. Alert on any issues

## Rollback Plan

If issues arise with integrated modules:

1. **Disable anomaly detection**: Comment out `AnomalyDetector` import
2. **Disable auto-repair**: Remove `@retry_with_backoff` decorators
3. **Keep diagnostics**: Continue collecting metrics (low risk)
4. **Revert changes**: Use git to revert `pipeline.py` changes

## Success Metrics

After integration, you should see:

✅ 95%+ pipeline success rate
✅ <600s average pipeline duration
✅ >0.8% engagement rate on winning variants
✅ <85% disk usage
✅ <80% memory usage during runs
✅ Zero unhandled errors (all classified and recovered)
✅ Anomalies detected within 1 run

## Next Steps

1. **Integrate diagnostics.py** into pipeline.py (wrap stages)
2. **Integrate auto_repair.py** into pipeline.py (wrap API calls)
3. **Add anomaly_detector.py** at end of run
4. **Add run_validator.py** validation before upload
5. **Update quality_dashboard.py** with final metrics
6. **Test with next pipeline run** (6 hours from now)
7. **Fix any integration issues** before production
8. **Monitor first 3 runs** for stability
9. **Deploy to GitHub Actions** with new modules
10. **Review diagnostic reports** daily for insights

## Support & Debugging

If integration breaks:

1. Check `diagnostics.json` in job folder
2. Review error classification in `auto_repair.py`
3. Check validation results in diagnostic report
4. Review anomalies in `anomaly_detector.py`
5. Check dashboard alerts for system issues

All modules are designed to fail gracefully—if a QA module has an error, the pipeline continues normally with diagnostics logged.
