# 🚀 Shorts Automation System — FULL ENGINEERING CONTEXT

## 👤 Owner

Shreyansh — building a fully automated YouTube Shorts system.

---

# 🎯 OBJECTIVE

Build a **zero-touch, fully automated pipeline** that:

1. Finds viral topics
2. Optimizes them for clicks
3. Generates scripts (AI)
4. Generates voiceover (TTS)
5. Fetches visuals
6. Generates subtitles (viral style)
7. Assembles video (ffmpeg)
8. Uploads to YouTube
9. Runs automatically (GitHub Actions)

---

# 🧠 SYSTEM ARCHITECTURE

## 🔁 End-to-End Flow

trend_miner.py
→ auto_pipeline.py
→ generate_script.py
→ generate_voice.py
→ fetch_visuals.py
→ assemble_video.py
→ upload_youtube.py

---

# ⚙️ TECH STACK

* Python (core)
* SQLite (shorts.db)
* ffmpeg (video)
* faster-whisper (subtitles)
* Groq API (LLM)
* YouTube Data API
* GitHub Actions (automation)

---

# 📂 FILE RESPONSIBILITIES

## trend_miner.py

* Fetch trending videos using YouTube API
* Extract clean topics
* Store in DB

## auto_pipeline.py

* Central orchestrator
* Picks best topic
* Sends to pipeline

## generate_script.py

* Uses Groq API
* Outputs:

  * script
  * keywords

## generate_voice.py

* Converts script → audio

## fetch_visuals.py

* Downloads relevant clips

## assemble_video.py

* Uses ffmpeg
* Creates vertical video
* Adds subtitles
* Adds background music

## upload_youtube.py

* Uploads final video

---

# 🧱 DATABASE DESIGN

## File: shorts.db

### Table: topics

Columns:

* id (primary key)
* topic (TEXT, UNIQUE)
* views (INTEGER)
* likes (INTEGER)
* score (REAL)
* used (INTEGER)
* created_at (TEXT)

---

# ⚠️ CRITICAL DESIGN RULE

DB must be consistent across ALL files.

Use:

```python
DB_PATH = os.path.join(os.path.dirname(__file__), "shorts.db")
```

NEVER use:

sqlite3.connect("shorts.db")

---

# ✅ WHAT WORKS

* GitHub Actions workflow runs
* API keys connected (Groq + YouTube)
* Trend mining logic works
* Topic cleaning + filtering works
* AI topic rewriting works
* Script generation works
* Subtitle generation works
* Video assembly pipeline exists
* Automation triggered every 6 hours

---

# ❌ MAJOR PROBLEMS FACED

## 1. SQLite Table Error

Error:
sqlite3.OperationalError: no such table: topics

### Root Causes:

* DB created in different directories
* Multiple DB schemas across files
* init_db not called early enough
* trend_miner + pipeline using different DBs

### Fix Strategy:

* Centralize DB in db.py
* Use absolute DB_PATH everywhere
* Call init_db() before any query
* Ensure trend_miner runs before topic selection

---

## 2. GitHub Actions Issues

Problems:

* Missing requirements.txt
* Wrong script executed
* Old workflow cache

Fix:

* Added requirements.txt
* Updated workflow YAML
* Forced manual runs

---

## 3. API Issues

* Groq rate limits
* YouTube quota limits

Fix:

* Retry logic
* Backoff delays

---

## 4. Code Instability

* indentation errors
* broken imports
* inconsistent logic

---

# ⚠️ CURRENT STATE (IMPORTANT)

System is VERY close to working.

Current blocking issue:
SQLite table inconsistency still appearing in GitHub Actions.

Likely reasons:

* DB path mismatch
* Schema mismatch
* init_db not properly enforced

---

# 🔥 SYSTEM WEAKNESSES

* No logging system (only prints)
* No retry system across pipeline
* No queue (everything sequential)
* No caching
* No monitoring
* No failure recovery
* No deduplication logic

---

# 🚀 NEXT LEVEL IMPROVEMENTS

## 🔧 Stability

* Add logging (structured logs)
* Add retry wrappers
* Add error recovery

## ⚡ Performance

* Parallel processing
* Batch API calls

## 📈 Growth

* Topic scoring model
* A/B testing titles
* Analytics tracking

## 🎬 Video Quality

* Viral subtitles (yellow/white style)
* Better pacing
* Hook optimization

## ☁️ Infrastructure

* Move from GitHub Actions → workers
* Add queue (Redis / RabbitMQ)

---

# 🤖 COPILOT ROLE

You are acting as:

→ Senior Backend Engineer
→ AI Systems Engineer
→ Automation Architect

---

# 🧠 WHAT YOU SHOULD DO

Help with:

* Debugging pipeline failures
* Fixing SQLite issues
* Improving architecture
* Making system production-ready
* Optimizing performance
* Improving video output quality

---

# 🚫 WHAT NOT TO DO

* Do NOT give generic advice
* Do NOT rewrite working code unnecessarily
* Do NOT overcomplicate

---

# 🎯 FOCUS

* Fix real bugs
* Improve reliability
* Maintain simplicity
* Enable full automation

---

# 🧨 FINAL GOAL

A system that:

* runs without human input
* produces viral content daily
* scales to 50–100 videos/day
* generates revenue automatically

---

# ⚡ NOTE

This is NOT a toy project.

This is an early-stage automated content system being prepared for scale.

Treat all suggestions as production-level decisions.







Goal

Fully automated YouTube Shorts pipeline:

mine topics

generate scripts (Groq API)

create voice

fetch visuals

assemble video (ffmpeg)

upload to YouTube

run via GitHub Actions

Current Problem

Error:
sqlite3.OperationalError: no such table: topics

Suspected Causes

DB not initialized before query

Different files using different DB paths

Schema mismatch across files

Current Setup

SQLite database: shorts.db

db.py handles DB creation

trend_miner.py inserts topics

auto_pipeline.py reads topics

Key Rule

All files must use:

DB_PATH = os.path.join(os.path.dirname(file), "shorts.db")

NOT:
sqlite3.connect("shorts.db")

What I Need Help With

Fix SQLite table issue

Ensure DB is created and used consistently

Debug pipeline execution order

Make system stable for automation




