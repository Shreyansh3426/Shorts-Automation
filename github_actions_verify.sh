#!/bin/bash
# GitHub Actions Setup Checklist
# Run this to verify everything is configured correctly

echo "════════════════════════════════════════════"
echo "✅ SHORTS AUTOMATION - GITHUB ACTIONS SETUP"
echo "════════════════════════════════════════════"
echo ""

# Check 1: .github/workflows/run.yml exists
echo "1️⃣  Checking workflow file..."
if [ -f ".github/workflows/run.yml" ]; then
    echo "   ✅ Workflow file exists"
else
    echo "   ❌ Workflow file missing!"
    exit 1
fi

# Check 2: error_recovery.py exists
echo "2️⃣  Checking error recovery script..."
if [ -f "error_recovery.py" ]; then
    echo "   ✅ Error recovery script exists"
else
    echo "   ❌ Error recovery script missing!"
    exit 1
fi

# Check 3: requirements.txt exists
echo "3️⃣  Checking requirements..."
if [ -f "requirements.txt" ]; then
    echo "   ✅ Requirements file exists"
else
    echo "   ❌ Requirements file missing!"
    exit 1
fi

# Check 4: db.py exists
echo "4️⃣  Checking database module..."
if [ -f "db.py" ]; then
    echo "   ✅ Database module exists"
else
    echo "   ❌ Database module missing!"
    exit 1
fi

# Check 5: auto_pipeline.py exists
echo "5️⃣  Checking main pipeline..."
if [ -f "auto_pipeline.py" ]; then
    echo "   ✅ Pipeline script exists"
else
    echo "   ❌ Pipeline script missing!"
    exit 1
fi

# Check 6: credentials.json exists
echo "6️⃣  Checking credentials..."
if [ -f "credentials.json" ]; then
    echo "   ✅ Credentials file exists (YouTube OAuth)"
else
    echo "   ⚠️  Credentials file missing (may be needed)"
fi

echo ""
echo "════════════════════════════════════════════"
echo "📋 NEXT STEPS:"
echo "════════════════════════════════════════════"
echo ""
echo "1. Push to GitHub:"
echo "   git add ."
echo "   git commit -m 'Add GitHub Actions automation'"
echo "   git push"
echo ""
echo "2. Add GitHub Secrets:"
echo "   Go to: GitHub.com → Your Repo → Settings → Secrets"
echo "   Add:"
echo "     - GROQ_API_KEY"
echo "     - YOUTUBE_API_KEY"
echo ""
echo "3. Test manually:"
echo "   Go to: GitHub.com → Actions tab"
echo "   Click: '🚀 Shorts Automation - Auto-Run & Self-Heal'"
echo "   Click: 'Run workflow' button"
echo ""
echo "4. Monitor:"
echo "   Check the workflow run in real-time"
echo "   Download logs if failed"
echo ""
echo "5. Automate:"
echo "   Every 6 hours it will run automatically! 🎉"
echo ""
echo "════════════════════════════════════════════"
