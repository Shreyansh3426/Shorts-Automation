# 🚀 SHORTS-AUTOMATION: Improvement Roadmap 2026

**Purpose:** Copy-paste prompts for GitHub Copilot / Groq LLM to implement high-impact improvements

**How to use:** Paste each prompt into VS Code Copilot Chat or feed to your LLM with code context

---

## 🎯 PRIORITY 1: Thumbnails (Highest ROI)

### Problem
No custom thumbnails = YouTube default = low CTR

### Copy-Paste Prompt for Copilot

```
In my YouTube Shorts automation pipeline (assemble_video.py uses FFmpeg), I need to generate a professional custom thumbnail for every video BEFORE upload.

Requirements:
- Size: 1080x1920 (vertical shorts format)
- Content: Extract key frame from one of the 4 Pexels clips (use highest contrast/most dramatic)
- Text overlay: 1-3 words in LARGE bold text (font 120-180pt), white + black outline, centered
- Examples: "3 HEARTS?!" | "WHY OCTOPUS?" | "NEVER CANCER 😱"
- Include relevant emoji if appropriate
- Output: job_xxx/thumbnail.jpg in job media folder

Implementation steps:
1. Create new file: thumbnail_generator.py
2. Function: generate_thumbnail(job_id, topic, clips_json) → str (path to thumbnail.jpg)
   - Extract frame from best clip using: ffmpeg -i clip.mp4 -ss 00:00:02 -vframes 1 frame.jpg
   - Use contrast detection (cv2 or PIL) to pick best frame
   - Open frame with PIL, resize to 1080x1920
   - Add text using PIL.ImageDraw: white text + 8-12px black stroke outline
   - Save as thumbnail.jpg
3. Integrate into auto_pipeline.py:
   - Call after fetch_visuals.py, before upload
   - Pass topic and clips_json
4. Update upload_youtube.py:
   - After videos().insert(), call:
     youtube.thumbnails().set(
         videoId=video_id,
         media_body=MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
     )

Use PIL for text overlay (Pillow library, already in requirements.txt).
Show me the thumbnail_generator.py code with error handling and logging.
```

### Integration Checklist
- [ ] Create `thumbnail_generator.py` (100 LOC)
- [ ] Add to `auto_pipeline.py` workflow (before upload step)
- [ ] Update `upload_youtube.py` to set thumbnail via API
- [ ] Test with 1 video locally
- [ ] Expected CTR improvement: +20-30%

---

## 🎯 PRIORITY 2: SEO Metadata (Titles, Descriptions, Tags)

### Problem
Current: Generic "Why do X #Shorts" titles = low search visibility

### Copy-Paste Prompt for Copilot

```
Upgrade my YouTube Shorts SEO metadata generation.

Current: Title = "Why do octopus have 3 hearts #Shorts"

New requirements (2026 best practices):
- Titles (under 60 chars):
  * Front-load hook word (URGENT, SHOCKING, WHY, etc.)
  * All caps for first 2-3 words if it's a question
  * Add relevant emoji (🦑 🦈 🧠 etc.)
  * Include number if possible (3, 90%, etc.)
  * Make it curiosity-driven
  Examples: "3 HEARTS?! 🦑 Why Octopus Evolved Insane", "SHOCKING: Why Sharks NEVER Get Cancer 😱"

- Descriptions (200-400 chars):
  * Line 1: Hook + main keyword
  * Line 2: Full script text
  * Line 3: CTA - "Comment your guess!", "What did you not know?", etc.
  * Last line: Hashtags (#Shorts #Facts #AnimalFacts #Biology)
  
- Tags (10-15 total):
  * 3-4 exact keywords (e.g., "octopus", "heart", "biology")
  * 3-4 broad categories ("animal facts", "science", "education")
  * 2-3 competitor tags (based on trending similar videos)
  * Always include: "shorts", "facts", "educational"
  * Variations: "octopus facts", "why do octopuses", "animal hearts"

Create a new file: seo_optimizer.py
Write a function: generate_seo_metadata(topic: str, script: str, keywords: list) -> dict
  Returns:
  {
    "title": "3 HEARTS?! 🦑 Why Octopus...",
    "description": "Hook + script + CTA + hashtags",
    "tags": ["octopus", "animal facts", ...]
  }

Algorithm:
1. Extract main noun from topic (e.g., "octopus")
2. Find emoji match from predefined dict
3. Capitalize first 3 words
4. Add number/question if in topic
5. Truncate title to 60 chars
6. Build description with script excerpt + CTA rotation
7. Generate tags from keywords + common category list
8. Integrate into auto_pipeline.py before upload_youtube.py
9. Pass result to upload_youtube.py upload_video() function

Show me the seo_optimizer.py code with emoji dict and title generation logic.
```

### Integration Checklist
- [ ] Create `seo_optimizer.py` (120 LOC)
- [ ] Add emoji dictionary (25-30 common emojis)
- [ ] CTA rotation list (5-10 different call-to-actions)
- [ ] Add to `auto_pipeline.py` workflow
- [ ] Pass dict to `upload_youtube.py`
- [ ] Test with 3 videos
- [ ] Expected results: +15-25% organic traffic from search/suggested

---

## 🎯 PRIORITY 3: A/B Testing Framework (Test & Learn)

### Problem
No variant testing = can't optimize hook style

### Copy-Paste Prompt for Copilot

```
Implement A/B testing for my Shorts pipeline.

Goal: Generate 3 script variants per topic (different hooks/tones), upload all as separate videos, compare performance after 24h, boost score of winning variant's keywords.

Variant types:
- Variant A: SHOCK hook - "This is TERRIFYING...", "You won't believe..."
- Variant B: QUESTION hook - "Ever wondered why...?", "Did you know...?"
- Variant C: NUMBER hook - "3 reasons...", "90% of people...", reveals at end

Same visuals + voice + thumbnails, ONLY script + title + subtitles change.

Requirements:
1. Update database schema:
   - Add columns to jobs table: variant_type (TEXT), parent_topic (TEXT), variant_group_id (TEXT)
   - Example: parent_topic="octopus_hearts", variant_type="shock", variant_group_id=uuid()

2. In generate_script.py:
   - Create 3 system prompts (SHOCK_PROMPT, QUESTION_PROMPT, NUMBER_PROMPT)
   - Modify generate_script() to accept variant parameter
   - Return 3 scripts instead of 1 when called from pipeline

3. In auto_pipeline.py:
   - When topic selected, instead of creating 1 job, create 3 jobs:
     * for variant in ["shock", "question", "number"]:
     *   script = generate_script(topic, variant_type=variant)
     *   create_job(topic, script, variant_type=variant, parent_topic=topic_hash)
   - Upload all 3 videos (only 1-2 per day to stay within quotas)

4. In sync_analytics.py:
   - After fetching stats, group by parent_topic
   - Find winner: max(views) after 24h
   - Extract keywords from winner's script
   - Boost unused topics matching winner keywords by 1.5x
   - Log which variant won (e.g., "SHOCK hook won for octopus!")

5. Tracking:
   - Add variant column to video_stats table
   - Query: SELECT variant_type, AVG(views) GROUP BY variant_type
   - Export stats for manual review

Show me:
1. The 3 system prompts for generate_script.py
2. Modified auto_pipeline.py loop (create 3 jobs per topic)
3. Modified sync_analytics.py to compare variants
4. SQL migration to add columns
```

### Integration Checklist
- [ ] Update `db.py` schema (new columns: variant_type, parent_topic)
- [ ] Create 3 system prompts in `generate_script.py`
- [ ] Modify `generate_script()` to accept variant parameter
- [ ] Update `auto_pipeline.py` to create 3 jobs per topic
- [ ] Modify `sync_analytics.py` to track winner + boost keywords
- [ ] Test A/B with 3 topics (9 videos total)
- [ ] Expected: 15-30% best variant outperforms average

---

## 🎯 PRIORITY 4: Error Monitoring & Slack Alerts

### Problem
Silent failures = lost opportunity cost, unpredictable upload gaps

### Copy-Paste Prompt for Copilot

```
Add real-time error alerting to my GitHub Actions pipeline.

Current: Only artifacts + 2 retry attempts

New requirements:
1. GitHub Actions workflow (run.yml + analytics.yml):
   - Add step after main execution:
   
     - name: Notify on failure
       if: failure()
       uses: slackapi/slack-github-action@v1.26.0
       with:
         payload: |
           {
             "text": "❌ Shorts Pipeline FAILED!",
             "blocks": [
               {
                 "type": "section",
                 "text": {
                   "type": "mrkdwn",
                   "text": "*Pipeline:* ${{ github.workflow }}\n*Job:* ${{ github.run_id }}\n*Commit:* ${{ github.sha }}\n*Logs:* ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
                 }
               }
             ]
           }
       env:
         SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
   
   - Also add success notification:
     - name: Notify on success
       if: success()
       run: curl -X POST ${{ secrets.SLACK_WEBHOOK }} -H 'Content-type: application/json' --data '{"text":"✅ Pipeline succeeded!"}'

2. In auto_pipeline.py:
   - Wrap main() in try-except
   - Log all exceptions with traceback
   - Send critical errors to email (Gmail SMTP)
   
   Example:
   ```python
   import smtplib
   from email.mime.text import MIMEText
   
   def send_alert_email(subject, body):
       msg = MIMEText(body)
       msg["Subject"] = subject
       gmail_user = os.getenv("GMAIL_USER")
       gmail_pwd = os.getenv("GMAIL_APP_PASSWORD")  # App-specific, not main password
       
       with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
           server.login(gmail_user, gmail_pwd)
           server.sendmail(gmail_user, gmail_user, msg.as_string())
   ```

3. Health check at pipeline start:
   - Log: "Pipeline started: {datetime.now()}"
   - Verify DB connection: test_db()
   - Verify API keys: len(API_KEY) > 10
   - Log: "System health: OK"

4. Detailed error logging:
   - Every exception: log full traceback + context
   - Log step completion: "✅ Trend mining completed", "❌ Fetch visuals failed: {error}"
   - Save detailed log to job folder: job_xxx/pipeline.log

Show me:
1. Updated run.yml with Slack notification step
2. Try-except wrapper in auto_pipeline.py with logging
3. Health check function
4. Email alert function (optional)
```

### Integration Checklist
- [ ] Update `.github/workflows/run.yml` with Slack step
- [ ] Add `SLACK_WEBHOOK` secret to GitHub
- [ ] Add health check to `auto_pipeline.py` (start of main())
- [ ] Wrap main() in try-except with detailed logging
- [ ] Test with intentional failure (set API_KEY="")
- [ ] Verify Slack notifications work
- [ ] Expected: 100% alert coverage, zero silent failures

---

## 🎯 PRIORITY 5: Human Review Gate (Optional, for Quality Control)

### Problem
Fire-and-forget automation = no quality assurance

### Copy-Paste Prompt for Copilot

```
Add optional human review before upload (quality gate).

New flow (triggered by env var):
1. After assemble_video.py: Save to "review_pending" folder:
   - output.mp4 (the full video)
   - script.txt (the generated script)
   - thumbnail.jpg (generated thumbnail)
   - metadata.json (title, description, tags)

2. Send Discord/Slack notification:
   - Message: "New Short ready for review!"
   - Include: topic, script preview (first 100 chars)
   - Link or file attachment (if possible)
   - Buttons/reaction: ✅ Approve or ❌ Reject

3. Wait for human approval (manual UI or env file):
   - Option A: Watch folder for "approved.txt" file
   - Option B: React with ✅ emoji in Slack (use action reaction trigger)
   - Option C: GitHub environment variable: APPROVE_NEXT=true (manual trigger)

4. If approved → move to "upload_ready" folder, upload normally
5. If rejected → archive to "rejected" folder, log reason

Requirements:
- Add env var: REVIEW_MODE (true/false) in GitHub environment or .env
- If REVIEW_MODE=true, pause at review_pending step
- Retention prediction dummy: if script ends with "?" → +10 quality score
- Log all approvals/rejections to DB

In auto_pipeline.py:
```python
if os.getenv("REVIEW_MODE", "false") == "true":
    review_folder = f"{tmpdir}/review_pending"
    os.makedirs(review_folder, exist_ok=True)
    
    # Save video, script, thumbnail
    shutil.copy(output_path, f"{review_folder}/output.mp4")
    with open(f"{review_folder}/script.txt", "w") as f:
        f.write(script)
    shutil.copy(thumbnail_path, f"{review_folder}/thumbnail.jpg")
    
    # Send notification
    send_review_notification(topic, script[:100])
    
    # Wait for approval
    approval_ready = wait_for_approval(job_id, timeout_minutes=60)
    
    if not approval_ready:
        print(f"❌ Review not approved within timeout")
        return
```

Show me:
1. review_gate() function in auto_pipeline.py
2. Updated .github/workflows/run.yml to support REVIEW_MODE
3. Discord notification template
4. Approval tracking in database
```

### Integration Checklist
- [ ] Add `REVIEW_MODE` environment variable (default: false)
- [ ] Create `review_gate()` function in `auto_pipeline.py`
- [ ] Add Discord/Slack notification before gate
- [ ] Implement approval check (polling or file-based)
- [ ] Optional: Use GitHub Environments for approval (more robust)
- [ ] Test with 1 video in review mode
- [ ] Expected: QA peace of mind, catch 5-10% of bad content

---

## 🎯 PRIORITY 6: AI Disclosure & Compliance

### Problem
2025-2026 YouTube policy: AI-generated content must be disclosed

### Copy-Paste Prompt for Copilot

```
Add YouTube AI disclosure to comply with 2025-2026 policies.

Policy requirement:
- If content uses synthetic voice (Edge-TTS) or AI script (Groq LLM), must be marked as "made with AI" or similar
- Current YouTube API v3 doesn't have direct "altered_content" toggle in videos().insert()
- Workaround: Add disclosure in description + watermark in video + tags

Requirements:
1. In upload_youtube.py, update description:
   - Add line at top: "⚠️ This video uses AI-generated voice and script for educational purposes."
   - Add tags: #AIGenerated #SyntheticVoice #Educational

2. In assemble_video.py, add watermark:
   - Use FFmpeg drawtext filter to add small text in corner:
     -vf "drawtext=text='AI Generated':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:x=(w-tw-20):y=20"
   - Position: top-right corner, semi-transparent black background
   - Duration: entire video

3. In upload_youtube.py, ensure:
   - madeForKids=False (AI content not for kids)
   - selfDeclareMadeForKids=False

Example FFmpeg command:
```
ffmpeg -i video.mp4 -vf "drawtext=text='AI Generated':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:x=(w-tw-20):y=20" output.mp4
```

In assemble_video.py, modify the subtitle line:
```python
'-vf', (
    f"subtitles={srt_path}:force_style='MarginV=180',"
    "drawtext=text='AI Generated':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:x=(w-tw-20):y=20"
)
```

Show me:
1. Updated upload_youtube.py description builder
2. Modified assemble_video.py with drawtext filter
3. Updated tags list with #AIGenerated
```

### Integration Checklist
- [ ] Update `upload_youtube.py` description builder
- [ ] Add drawtext filter to `assemble_video.py` FFmpeg command
- [ ] Add #AIGenerated tag to all uploads
- [ ] Test watermark visibility (render 1 video)
- [ ] Verify compliance with YouTube policies
- [ ] Expected: 100% policy compliance, avoid strikes/demonetization

---

## 🎯 PRIORITY 7-10: DevOps & Scalability

### Problem
Growing manual maintenance + inconsistent environments + no testing

### Copy-Paste Prompt for Copilot

```
Containerize and add testing infrastructure to Shorts-Automation.

Tasks:
1. Create Dockerfile for consistent Python 3.10 + FFmpeg environment:
   - Base: python:3.10-slim
   - Install: ffmpeg, libsm6 (for OpenCV)
   - Copy requirements.txt, install packages
   - Set env defaults
   - Entrypoint: python auto_pipeline.py

2. Create docker-compose.yml:
   - Service: shorts-automation
   - Volume: ./shorts.db (persist DB)
   - Environment: GROQ_API_KEY, YOUTUBE_API_KEY, etc.
   - Command: python auto_pipeline.py (or override for testing)

3. Add pytest tests:
   - tests/test_db.py: Test DB CRUD operations (mock)
   - tests/test_topic_scorer.py: Test scoring formula
   - tests/test_seo_optimizer.py: Test metadata generation
   - Mock YouTube API calls

4. Add dry-run mode:
   - In auto_pipeline.py, check env var: DRY_RUN=true
   - If true: skip actual uploads, API calls, only log what would happen
   - Usage: python auto_pipeline.py (with DRY_RUN=true env)

5. Update GitHub Actions workflows:
   - run.yml: add option to use container image or native
   - Or: create test.yml that runs pytest before deployment

6. Add caching:
   - Use joblib or diskcache for script/voice generation (hash-based)
   - Avoid regenerating same content

Show me:
1. Dockerfile (20 lines)
2. docker-compose.yml (25 lines)
3. tests/test_db.py (mock DB, 50 lines)
4. Dry-run mode in auto_pipeline.py (main() wrapper, 20 lines)
5. Updated .github/workflows/run.yml to run tests
```

### Integration Checklist
- [ ] Create `Dockerfile`
- [ ] Create `docker-compose.yml`
- [ ] Create `tests/` directory + 3 test files
- [ ] Add `--dry-run` flag to `auto_pipeline.py`
- [ ] Update `.github/workflows/run.yml` to run tests
- [ ] Test locally: `docker-compose up`
- [ ] Test dry-run: `DRY_RUN=true python auto_pipeline.py`
- [ ] Expected: Repeatable builds + confidence in changes

---

## 📊 IMPLEMENTATION PRIORITY ORDER

1. **Week 1:** Thumbnails + SEO (High ROI: +20-40% views)
2. **Week 2:** A/B Testing (Learn what works)
3. **Week 3:** Compliance + Watermark (Avoid strikes)
4. **Week 4:** Error Alerts (Operational stability)
5. **Week 5:** DevOps/Container (Scale confidently)
6. **Optional:** Review gate (If you want QA)

---

## 🚀 QUICK START: Feed to Copilot

1. Open VS Code
2. Enable GitHub Copilot Chat (Ctrl+Shift+/)
3. Copy one prompt from above (e.g., Thumbnail prompt)
4. Paste into chat with: "Here's my requirement: [prompt]"
5. Add context: "My project structure has assemble_video.py, upload_youtube.py, auto_pipeline.py"
6. Ask: "Write the code for this"
7. Copilot will generate implementation
8. Review + integrate into project

---

## 📝 Notes

- **All prompts assume:** Your existing files (auto_pipeline.py, upload_youtube.py, etc.) are already working
- **Test locally first:** Use dry-run or test mode before pushing to main
- **Secrets:** Add new secrets to GitHub (SLACK_WEBHOOK, GMAIL_APP_PASSWORD, etc.)
- **Backwards compatible:** Each feature can be added independently (no forced order)
- **Expected ROI:** Thumbnails alone = +25-40% CTR → +15-30% views

---

## 📬 Questions?

If any prompt is unclear, ask Copilot: "Clarify what this means: [specific phrase from prompt]"

Or feed multi-part prompts to Groq with context: "You are implementing my YouTube Shorts pipeline. [paste prompt] Show me the code and explain each step."
