#!/usr/bin/env python3
"""
Quick reference - GitHub Actions Setup for Shorts Automation
Run this file to see all available commands and status
"""

import os
import json
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_files():
    print_header("✅ FILE CHECK")
    files = {
        ".github/workflows/run.yml": "GitHub Actions workflow",
        "error_recovery.py": "Auto-recovery script",
        "db.py": "Database module",
        "auto_pipeline.py": "Main pipeline",
        "requirements.txt": "Dependencies",
        "credentials.json": "YouTube OAuth (optional)",
        "youtube_token.json": "YouTube token (optional)"
    }
    
    for file, desc in files.items():
        exists = os.path.exists(file)
        status = "✅" if exists else "❌"
        print(f"{status} {file:40} ({desc})")

def show_next_steps():
    print_header("🚀 NEXT STEPS - DO THIS NOW")
    steps = [
        ("1", "Push to GitHub", [
            "git add .",
            "git commit -m 'Add GitHub Actions automation'",
            "git push origin main"
        ]),
        ("2", "Add GitHub Secrets", [
            "Go to: GitHub.com → Repo → Settings → Secrets",
            "Add: GROQ_API_KEY = your_key",
            "Add: YOUTUBE_API_KEY = your_key"
        ]),
        ("3", "Test (Optional)", [
            "Go to: GitHub.com → Actions",
            "Click: Run workflow button",
            "Monitor: Watch logs in real-time"
        ]),
        ("4", "Relax 🎉", [
            "Pipeline now runs every 6 hours automatically!",
            "Check GitHub Actions tab for status"
        ])
    ]
    
    for num, title, details in steps:
        print(f"{num}️⃣  {title}:")
        for detail in details:
            print(f"    • {detail}")
        print()

def show_commands():
    print_header("📝 USEFUL COMMANDS")
    commands = {
        "Test DB locally": "python -c \"from db import init_db; init_db()\"",
        "Run error recovery": "python error_recovery.py",
        "Run pipeline locally": "python auto_pipeline.py",
        "Check GitHub status": "gh run list",
        "View last workflow": "gh run view --web",
    }
    
    for desc, cmd in commands.items():
        print(f"\n{desc}:")
        print(f"  $ {cmd}")

def show_cron_examples():
    print_header("⏰ SCHEDULE EXAMPLES (Edit .github/workflows/run.yml)")
    examples = {
        "Every 6 hours": "0 */6 * * *",
        "Every 4 hours": "0 */4 * * *",
        "Every 2 hours": "0 */2 * * *",
        "Every hour": "0 * * * *",
        "Daily at 9 AM": "0 9 * * *",
        "Every 30 min": "*/30 * * * *",
    }
    
    for desc, cron in examples.items():
        print(f"{cron:20} → {desc}")
    print(f"\nMore: https://crontab.guru")

def show_secrets_required():
    print_header("🔐 REQUIRED GITHUB SECRETS")
    secrets = {
        "GROQ_API_KEY": "Your Groq API key (for LLM)",
        "YOUTUBE_API_KEY": "YouTube Data API key (for video lookup)",
    }
    
    print("These MUST be added to GitHub Settings → Secrets:\n")
    for key, desc in secrets.items():
        print(f"  Name: {key}")
        print(f"  Description: {desc}\n")

def show_troubleshooting():
    print_header("🆘 COMMON ISSUES & FIXES")
    issues = {
        "Workflow doesn't appear": [
            "Wait 5 minutes for GitHub to detect",
            "Refresh the page",
            "Check: Settings → Actions → Allow workflows"
        ],
        "Secrets error in logs": [
            "Add secrets to GitHub (see REQUIRED SECRETS above)",
            "Double-check names are EXACT"
        ],
        "Database error": [
            "Don't worry - auto-recovery script handles it",
            "Workflow retries automatically"
        ],
        "API key error": [
            "Verify keys in GitHub Secrets",
            "Check API quotas in Groq/YouTube dashboards"
        ],
        "No videos generated": [
            "Check logs for errors",
            "Verify trending videos exist (YouTube API)"
        ]
    }
    
    for issue, fixes in issues.items():
        print(f"❓ {issue}:")
        for fix in fixes:
            print(f"   → {fix}")
        print()

def show_monitoring():
    print_header("📊 HOW TO MONITOR")
    print("""
1. View all runs:
   GitHub → Actions tab → See all workflow runs

2. Check specific run:
   Click any run → See all steps + logs

3. Download logs:
   Click run → Artifacts → pipeline-logs

4. Check for failures:
   Look for ❌ red status (easy to spot)

5. Auto notifications:
   GitHub notifies on failure automatically
""")

def main():
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*18 + "🚀 SHORTS AUTOMATION 🚀" + " "*14 + "║")
    print("║" + " "*15 + "GitHub Actions Quick Reference" + " "*12 + "║")
    print("╚" + "="*58 + "╝")
    
    check_files()
    show_next_steps()
    show_secrets_required()
    show_commands()
    show_cron_examples()
    show_monitoring()
    show_troubleshooting()
    
    print_header("✅ YOU'RE ALL SET!")
    print("""
Your automated pipeline is ready! 🎉

Summary:
  ✅ Workflow auto-runs every 6 hours
  ✅ Self-healing error recovery
  ✅ Automatic retries on failure
  ✅ Comprehensive logging
  ✅ GitHub Actions integration complete

Next: Push code → Add secrets → Done! 🚀
""")

if __name__ == "__main__":
    main()
