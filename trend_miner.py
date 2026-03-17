import os
import sqlite3
import re
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime
import isodate

# Load environment variables
load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
print("API KEY:", API_KEY)

# Initialize YouTube API
youtube = build("youtube", "v3", developerKey=API_KEY)

SEARCH_TERMS = [
    "science facts",
    "animal facts",
    "human body facts",
    "biology facts"
]


# 🔥 CLEAN FUNCTION
def extract_topic(title):
    title = title.lower()

    # remove emojis
    title = re.sub(r'[^\x00-\x7F]+', '', title)

    # remove hashtags
    title = re.sub(r'#\w+', '', title)

    # remove special characters
    title = re.sub(r'[^a-zA-Z0-9\s]', '', title)

    # remove extra spaces
    title = re.sub(r'\s+', ' ', title)

    # remove junk words
    junk_words = [
        "viral", "trending", "shorts", "explained",
        "animation", "official", "video", "2024",
        "america", "talent", "gift", "edit",
        "store", "using", "stopped", "cool"
    ]

    for word in junk_words:
        title = title.replace(word, "")

    title = title.strip()

    # too short = ignore
    if len(title.split()) < 3:
        return None

    # force hook style
    if not title.startswith(("why", "how")):
        title = "why " + title

    return title


# 🔥 MAIN FUNCTION
def mine_trends():

    conn = sqlite3.connect("shorts.db")
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

            # skip long videos
            if duration > 60:
                continue

            # clean topic
            topic = extract_topic(title)

            if not topic:
                continue

            # allow only science-related
            allowed_keywords = [
                "human", "body", "brain", "blood", "heart",
                "animal", "cells", "science", "biology",
                "why", "how"
            ]

            if not any(word in topic for word in allowed_keywords):
                continue

            # remove useless topics
            banned_words = [
                "magic", "trick", "talent", "gift",
                "store", "ice cream", "pins"
            ]

            if any(word in topic for word in banned_words):
                continue

            # avoid duplicates
            existing = cur.execute(
                "SELECT topic FROM topics WHERE topic = ?",
                (topic,)
            ).fetchone()

            if existing:
                continue

            # insert into DB
            cur.execute("""
            INSERT OR IGNORE INTO topics
            (topic, views, likes, created_at)
            VALUES (?, ?, ?, ?)
            """, (
                topic,
                views,
                likes,
                datetime.utcnow()
            ))

    conn.commit()
    conn.close()


# 🔥 RUN
if __name__ == "__main__":
    mine_trends()
