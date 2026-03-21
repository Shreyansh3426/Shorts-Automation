#!/usr/bin/env python3
"""Test workflow components"""
import subprocess
import sys
import os

print("🧪 Testing pipeline components...\n")

# Test 1: Database initialization
print("1️⃣  Testing database initialization...")
try:
    from db import init_db
    init_db()
    print("✅ Database initialization passed\n")
except Exception as e:
    print(f"❌ Database initialization failed: {e}\n")
    sys.exit(1)

# Test 2: Error recovery
print("2️⃣  Testing error recovery script...")
result = subprocess.run([sys.executable, "error_recovery.py"], capture_output=True, text=True, timeout=10)
print(f"Error recovery output (first 300 chars):\n{result.stdout[:300]}\n")

# Test 3: Check environment
print("3️⃣  Checking environment...")
groq_ok = "GROQ_API_KEY" in os.environ
youtube_ok = "YOUTUBE_API_KEY" in os.environ
print(f"GROQ_API_KEY: {'✅ Set' if groq_ok else '⚠️  Not set'}")
print(f"YOUTUBE_API_KEY: {'✅ Set' if youtube_ok else '⚠️  Not set'}")

print("\n✅ All component tests complete!")
print("Ready to run: python auto_pipeline.py")
