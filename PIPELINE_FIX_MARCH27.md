# Pipeline Failures Investigation & Fixes - March 27, 2026

## Problem Summary
**Pipeline stopped working on March 25-27**: No videos uploaded for 2 days despite correct scheduled runs.

### Root Causes Found & Fixed

#### 1. **FFmpeg Hanging (No Timeout Protection)** ✅ FIXED
**Issue**: `assemble_video.py` had `subprocess.run()` calls without timeouts
- FFmpeg processes could hang indefinitely
- Complex `zoompan` filter was unstable
- Result: Jobs got stuck at "fetched" status forever

**Fix Applied**:
```python
# Before: subprocess.run([ffmpeg_cmd], check=True)
# After:  subprocess.run([ffmpeg_cmd], check=True, timeout=120)
```
- Added 120s timeout for clip processing
- Added 180s timeout for concat operation
- Added 300s timeout for final assembly
- Removed unstable `zoompan` filter
- Simplified to basic scale/crop/fps filters

#### 2. **Broken Audio Filter Chain** ✅ FIXED
**Issue**: FFmpeg sidechain compression filter had incorrect syntax
```
Error: [AVFilterGraph] More input link labels specified for filter 'acompressor' than it has inputs: 2 > 1
```

**Fix Applied**:
```python
# Removed complex sidechain ducking
# Changed to simple volume mixing:
'[2:a]volume=0.4[music];'
'[1:a]volume=1.0[voice];'
'[voice][music]amix=inputs=2:duration=first[aout]'
```
- Voice at 100% volume
- Background music at 40% volume
- Simple, reliable audio mixing

#### 3. **Python 3.9 Type Hint Incompatibilities** ✅ FIXED
**Files Fixed**:
- `thumbnail_generator.py` - line 9
- `seo_optimizer.py` - line 1

**Changes**:
```python
# Was:  list[str] | None → Now: Optional[List[str]]
# Was:  dict → Now: Dict
```

## Files Modified
1. `assemble_video.py` - FFmpeg timeouts + audio filter fixes
2. `thumbnail_generator.py` - Python 3.9 type hints
3. `seo_optimizer.py` - Python 3.9 type hints

## Testing Status
- ✅ March 27: New job created (20260327_023051_6c2e5a)
- ✅ Visuals downloaded successfully (4 clips)
- ✅ Voice variants generated (A, B, C)
- ⏳ Assembly stage: Testing in progress

## Next Steps
1. Verify assembly completes with new timeout/filter fixes
2. Monitor YouTube for successful uploads
3. Check that jobs complete all stages (script → voice → visuals → assembly → upload)
4. Ensure GitHub Actions triggers properly every 6 hours

## Commits
- `8e51834` - Add FFmpeg timeouts & simplify video filter
- `a202848` - Fix Python 3.9 type hints in thumbnail_generator and seo_optimizer
- `720fa72` - Add Smart Strategy Engine for analytics
- `4806fe3` - Critical fix: Python 3.9 compatibility for QA modules

## Prevention Going Forward
- ✅ All FFmpeg calls now have timeouts (prevent infinite hangs)
- ✅ Audio filters simplified (remove complex filters that fail)
- ✅ Type hints validated for Python 3.9 (deployed environment)
- ✅ Error handling improved (timeouts caught and logged)
