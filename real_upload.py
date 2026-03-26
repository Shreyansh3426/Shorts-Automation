#!/usr/bin/env python3
"""Actual YouTube upload for the March 27 video"""
import sqlite3
import os
import sys
from upload_youtube import upload_video

def main():
    job_id = "job_20260327_023051_6c2e5a"
    video_path = f"media/{job_id}/final_A.mp4"

    # Get job details
    conn = sqlite3.connect('shorts.db')
    cursor = conn.execute(
        "SELECT topic, script, keywords, clips_json FROM jobs WHERE id=?",
        (job_id,)
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        print(f"❌ Job not found: {job_id}")
        return False

    topic, script, keywords, clips_json = result

    print(f"\n📤 REAL YOUTUBE UPLOAD")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Job ID:     {job_id}")
    print(f"Video File: {video_path}")
    print(f"Topic:      {topic}")
    print(f"Size:       {os.path.getsize(video_path)/1024/1024:.1f} MB")

    # Check if video exists
    if not os.path.exists(video_path):
        print(f"\n❌ Video file not found: {video_path}")
        return False

    # Try to upload
    try:
        print(f"\n⏳ Uploading to YouTube...")
        result_json = upload_video(
            video_path,
            title=f"UNBELIEVABLE {topic}",
            job_id=job_id,
            topic=topic,
            clips_json=clips_json,
            script=script,
            keywords=keywords
        )
        print(f"\n✅ Upload successful!")
        
        # Update database with real YouTube ID
        import json
        result_data = json.loads(result_json)
        video_id = result_data.get('video_id')
        
        conn = sqlite3.connect('shorts.db')
        conn.execute(
            "UPDATE jobs SET youtube_id=? WHERE id=?",
            (video_id, job_id)
        )
        conn.commit()
        conn.close()
        
        print(f"   Video ID: {video_id}")
        print(f"   URL: https://youtube.com/shorts/{video_id}")
        return True
        
    except Exception as e:
        print(f"\n❌ Upload failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
