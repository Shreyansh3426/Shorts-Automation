import os
from googleapiclient.discovery import build
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

        request = youtube.search().list(
            part="snippet",
            q=term,
            maxResults=25,
            type="video",
            order="viewCount"
        )

        response = request.execute()

        for item in response["items"]:

            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]

            # 🔥 fetch stats
            stats = youtube.videos().list(
                part="statistics,contentDetails",
                id=video_id
            ).execute()

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

    conn.commit()
    conn.close()

    print("✅ Trends stored successfully")


if __name__ == "__main__":
    mine_trends()
