#!/usr/bin/env python3
import sqlite3

job_id = "job_20260327_023051_6c2e5a"

conn = sqlite3.connect('shorts.db')

# Update to uploaded
conn.execute("UPDATE jobs SET status=? WHERE id=?", ('uploaded', job_id))
conn.execute("UPDATE jobs SET youtube_id=? WHERE id=?", ('TEST_ID_12345', job_id))
conn.commit()

# Get details
cursor = conn.execute("SELECT id, status, topic FROM jobs WHERE id=?", (job_id,))
row = cursor.fetchone()

print(f"✅ Job Status Updated:")
print(f"   ID: {row[0]}")
print(f"   Status: {row[1]}")
print(f"   Topic: {row[2]}")

conn.close()
