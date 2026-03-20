# 🚀 GitHub Actions Auto-Run Setup Guide

## ✅ What's Configured

Your Shorts Automation pipeline is now **fully automated** on GitHub Actions with:

### Auto-Execution
- ⏰ **Scheduled**: Runs every 6 hours automatically
- 🎮 **Manual**: "Run workflow" button on GitHub Actions tab
- 🔄 **Auto-Retry**: Fails → 5 second wait → Retries automatically
- 🛡️ **Error Recovery**: Auto-detects and fixes common issues

### Built-in Features
- ✅ Database auto-initialization
- ✅ Dependency verification
- ✅ API key validation
- ✅ Cache cleanup
- ✅ Log collection
- ✅ Failure notifications
- ✅ Artifact preservation (30 days)

---

## 📋 Prerequisites (One-time Setup)

### 1️⃣ Add GitHub Secrets
Go to: **GitHub Repo → Settings → Secrets and variables → Actions**

Add these secrets:
```
GROQ_API_KEY = your_groq_api_key
YOUTUBE_API_KEY = your_youtube_api_key
```

### 2️⃣ Verify credentials.json
Make sure `credentials.json` (for YouTube OAuth) is in your repo root.

### 3️⃣ Verify youtube_token.json
If using OAuth refresh tokens, keep `youtube_token.json` committed.

---

## 🎮 How to Use

### Automatic Runs
✅ Does it automatically:
- Every 6 hours on schedule
- No action needed from you

### Manual Trigger
1. Go to: **GitHub.com → Your Repo → Actions**
2. Click: **"🚀 Shorts Automation - Auto-Run & Self-Heal"**
3. Click: **"Run workflow"** → **"Run workflow"** again

### Monitor Execution
1. Go to: **Actions** tab
2. Click the running workflow
3. See real-time logs for each step
4. Download logs if it fails

---

## 🔍 Understanding the Workflow

### Step-by-Step Execution

```
1. 📦 Checkout repo
2. 🐍 Setup Python 3.10
3. 📥 Install dependencies (pip + ffmpeg)
4. 🗄️ Initialize database (creates tables if missing)
5. 🏥 Run error recovery (checks for common issues)
6. 🌐 Verify API keys (fail early if keys missing)
7. 🎬 Run pipeline (Attempt 1)
   ├─ If fails: Wait 5 seconds
   └─ If fails: Attempt 2 with reinstanced DB
8. 📊 Check for errors in logs
9. 💾 Upload logs to artifacts
10. 📧 Notify on failure (comment on PR)
11. ✅ Success notification
```

---

## 🛠️ Error Recovery (Automatic)

The pipeline automatically recovers from:

### Database Errors
- ✅ Missing `topics` table → Recreates it
- ✅ Corrupted database → Deletes & reinitializes
- ✅ Missing columns → Adds them

### Dependency Errors
- ✅ Missing packages → Installs automatically
- ✅ Wrong Python version → GitHub Actions has 3.10

### API Errors
- ✅ Rate limits → Retry with 5-second delay
- ✅ Network timeout → Retry attempt 2

### File Errors  
- ✅ Cache corruption → Clean & restart
- ✅ Missing media folder → Creates automatically

---

## 📊 Monitoring & Logs

### View Logs
1. **GitHub.com → Actions → Select workflow run**
2. Click any failed step to see full output
3. Look for 🔴 red X for error details

### Download Logs
1. Go to **Actions → Select run**
2. Scroll down to **Artifacts**
3. Download `pipeline-logs` file

### Check Status Badge
Add to your README:
```markdown
[![Build Status](https://github.com/YOUR-USERNAME/Shorts-Automation/workflows/Shorts%20Automation%20-%20Auto-Run%20%26%20Self-Heal/badge.svg)](https://github.com/YOUR-USERNAME/Shorts-Automation/actions)
```

---

## 🔧 Customization

### Change Schedule
Edit `.github/workflows/run.yml`:
```yaml
schedule:
  - cron: "0 */4 * * *"   # Every 4 hours
  - cron: "0 9 * * *"     # Every day at 9 AM
```

[Cron format reference](https://crontab.guru/)

### Add Slack/Discord Notifications
Add to workflow after `Run automation`:
```yaml
- name: 📢 Notify on Slack
  if: failure()
  run: |
    curl -X POST YOUR_SLACK_WEBHOOK -d '{"text":"Pipeline failed"}'
```

### Increase Timeout
Edit:
```yaml
timeout-minutes: 120  # Was 60, now 2 hours
```

---

## 🆘 Troubleshooting

### Pipeline never runs
- ✅ Check: **Settings → Actions → General**
- ✅ Enable: "Allow all actions and workflows"

### Secrets not working
- ✅ Go to **Secrets → Check names** (case-sensitive)
- ✅ Verify they're set correctly

### Database errors persist
- ✅ Manually run error recovery: `python error_recovery.py`
- ✅ Check media permissions: `chmod -R 755 media/`

### API timeouts
- ✅ Could be rate limiting - workflow has 60 min timeout
- ✅ Check API quotas in Google Cloud & Groq dashboards

### Logs show "file not found"
- ✅ Ensure `credentials.json` & `youtube_token.json` exist
- ✅ Commit them to GitHub (if not sensitive)

---

## 💡 Pro Tips

1. **Pin workflow results**: After success, they stay in History
2. **Test locally first**: Run `python run_system.py` locally before trusting automation
3. **Keep database small**: Archive/delete old media files occasionally
4. **Monitor API costs**: Check Groq & YouTube API dashboards monthly
5. **Git commits**: Each video upload should create a commit with logs

---

## 🎯 Next Steps

1. ✅ Add GitHub Secrets (GROQ_API_KEY, YOUTUBE_API_KEY)
2. ✅ Push to GitHub
3. ✅ Go to **Actions** and click **"Run workflow"** manually
4. ✅ Watch it execute - first run will take ~3-5 minutes
5. ✅ Check results & logs
6. ✅ Sit back - it runs automatically every 6 hours!

---

## 📞 Need Help?

If workflow fails:
1. Check **Actions → Last run → View all jobs**
2. Click the red ❌ step for error details
3. Share the error message, I'll help fix it

**Your automation is now 100% hands-off! 🎉**
