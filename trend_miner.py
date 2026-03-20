import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from datetime import datetime
import isodate
import re
from db import init_db, get_conn

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

youtube = build("youtube", "v3", developerKey=API_KEY)

SEARCH_TERMS = [
    "science facts",
    "animal facts",
    "human body facts",
    "biology facts"
]


# 🔥 CLEAN TOPIC EXTRACTION
def extract_topic(title):
    title = title.lower()

    # remove emojis
    title = re.sub(r'[^\x00-\x7F]+', '', title)

    # remove hashtags
    title = re.sub(r'#\w+', '', title)

    # remove special characters
    title = re.sub(r'[^a-zA-Z0-9\s]', '', title)

    # remove junk words
    junk = [
        "viral", "trending", "shorts", "explained",
        "animation", "official", "video", "2024",
        "edit"
    ]

    for j in junk:
        title = title.replace(j, "")

    title = title.strip()

    if len(title) < 10:
        return None

    return title


# 🔥 MAIN FUNCTION
def mine_trends():
    # Ensure DB is initialized
    init_db()
    
    conn = get_conn()
    cur = conn.cursor()

    for term in SEARCH_TERMS:
        try:
            request = youtube.search().list(
                part="snippet",
                q=term,
                maxResults=10,  # Reduced from 25 to save quota
                type="video",
                order="viewCount"
            )

            response = request.execute()

            for item in response["items"]:

                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]

                # 🔥 fetch stats
                try:
                    stats = youtube.videos().list(
                        part="statistics,contentDetails",
                        id=video_id
                    ).execute()
                except HttpError as e:
                    if e.resp.status == 403 and 'quotaExceeded' in str(e):
                        print(f"⚠️  Quota exceeded fetching stats. Using cached trends...")
                        raise  # Re-raise to be caught by outer handler
                    raise

                stats = stats["items"][0]

                views = int(stats["statistics"].get("viewCount", 0))
                likes = int(stats["statistics"].get("likeCount", 0))

                duration = isodate.parse_duration(
                    stats["contentDetails"]["duration"]
                ).total_seconds()

                # only shorts
                if duration > 60:
                    continue

                topic = extract_topic(title)

                if not topic:
                    continue

                # 🔥 insert safely
                try:
                    cur.execute("""
                    INSERT OR IGNORE INTO topics
                    (topic, views, likes, created_at)
                    VALUES (?, ?, ?, ?)
                    """, (
                        topic,
                        views,
                        likes,
                        datetime.utcnow().isoformat()
                    ))
                except Exception as e:
                    print("Insert error:", e)

        except HttpError as e:
            if e.resp.status == 403 and 'quotaExceeded' in str(e):
                print(f"❌ YouTube API QUOTA EXCEEDED for term: '{term}'")
                print(f"⏱️  Quota resets daily at midnight PT")
                print(f"📚 Using cached trending topics from database...")
                
                # Fall back to cached trends from database (sorted by views)
                try:
                    cached = cur.execute("""
                        SELECT topic, views, likes, created_at 
                        FROM topics 
                        ORDER BY views DESC 
                        LIMIT 5
                    """).fetchall()
                    
                    if cached:
                        print(f"✅ Found {len(cached)} cached trending topics")
                        for row in cached:
                            print(f"   - {row[0]} ({row[1]} views)")
                    else:
                        print(f"⚠️  No cached topics available")
                except Exception as db_err:
                    print(f"Error reading cached topics: {db_err}")
                
                continue  # Skip to next search term
            else:
                # Different HTTP error, re-raise
                raise
        except Exception as e:
            print(f"Unexpected error mining '{term}': {e}")
            continue

    conn.commit()
    conn.close()
    print("✅ Trend mining completed")

    print("✅ Trends stored successfully")


if __name__ == "__main__":
    mine_trends()
