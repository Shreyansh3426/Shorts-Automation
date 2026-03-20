#!/usr/bin/env python3
"""
Auto-Recovery Script for Shorts Automation Pipeline
Detects and fixes common errors without manual intervention
"""

import os
import sqlite3
import sys
from pathlib import Path

def fix_sqlite_issues():
    """Fix SQLite database issues"""
    print("🔧 Checking SQLite database...")
    
    db_path = os.path.join(os.path.dirname(__file__), "shorts.db")
    
    try:
        # Try to connect
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA integrity_check")
        
        # Check topics table
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='topics'")
        
        if not cur.fetchone():
            print("⚠️  Topics table missing - recreating...")
            from db import init_db
            init_db()
            print("✅ Topics table recreated")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("🔄 Attempting to reinitialize database...")
        
        try:
            # Delete corrupted DB
            if os.path.exists(db_path):
                os.remove(db_path)
            
            # Reinitialize
            from db import init_db
            init_db()
            print("✅ Database reinitialized successfully")
            return True
            
        except Exception as e2:
            print(f"❌ Failed to recover database: {e2}")
            return False

def check_dependencies():
    """Verify all required packages are installed"""
    print("📦 Checking dependencies...")
    
    required = [
        'requests',
        'dotenv',
        'googleapiclient',
        'youtube_dl',
        'ffmpeg',
        'pydub'
    ]
    
    try:
        import pkg_resources
        installed = {pkg.key for pkg in pkg_resources.working_set}
        
        missing = [pkg for pkg in required if pkg not in installed]
        
        if missing:
            print(f"⚠️  Missing packages: {missing}")
            print("Installing...")
            os.system(f"pip install {' '.join(missing)}")
            print("✅ Dependencies installed")
        else:
            print("✅ All dependencies present")
            
        return True
        
    except Exception as e:
        print(f"⚠️  Dependency check failed: {e}")
        return False

def check_env_vars():
    """Verify required environment variables"""
    print("🔐 Checking environment variables...")
    
    required_vars = ['GROQ_API_KEY', 'YOUTUBE_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing env vars: {missing}")
        return False
    
    print("✅ All required env vars set")
    return True

def clean_cache():
    """Clean up temporary files"""
    print("🧹 Cleaning cache...")
    
    cache_dirs = [
        '__pycache__',
        '.pytest_cache',
        '*.pyc'
    ]
    
    try:
        for pattern in cache_dirs:
            if pattern == '*.pyc':
                os.system("find . -name '*.pyc' -delete")
            else:
                os.system(f"rm -rf {pattern}")
        
        print("✅ Cache cleaned")
        return True
        
    except Exception as e:
        print(f"⚠️  Cache cleanup failed: {e}")
        return False

def main():
    """Run all recovery checks"""
    print("\n" + "="*50)
    print("🏥 SHORTS AUTOMATION - ERROR RECOVERY")
    print("="*50 + "\n")
    
    results = {
        "SQLite": fix_sqlite_issues(),
        "Dependencies": check_dependencies(),
        "Environment": check_env_vars(),
        "Cache": clean_cache(),
    }
    
    print("\n" + "="*50)
    print("📋 Recovery Summary:")
    print("="*50)
    
    for check, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    if all(results.values()):
        print("\n✅ All checks passed! System ready to run.")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please review above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
