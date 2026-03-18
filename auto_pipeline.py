import sqlite3
import requests
import os
import time
import subprocess
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# 🔥 INIT DB (FIXED WITH views COLUMN)
def init_db():
    conn = sqlite3.connect("shorts.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT,
        views INTEGER DEFAULT 0,
        score REAL DEFAULT 0,
        used INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


# 🔥 SCORING SYSTEM
def score_topic(text):
    score = 0
    text = text.lower()

    triggers = ["why", "how", "what", "secret", "hidden", "truth"]
    for t in triggers:
        if t in text:
            score += 2

    power_words = ["never", "instant", "forever", "inside", "real"]
    for w in power_words:
        if w in text:
            score += 2

    weak = ["explained", "revealed", "study"]
    for w in weak:
        if w in text:
            score -= 1

    return score


# 🔥 GENERATE VARIATIONS
def generate_variations(topic):
    prompt = f"""
Generate 5 viral YouTube Shorts topics based on this:

{topic}

Rules:
- curiosity driven
- 6-12 words
- science/biology style
- no hashtags
- no names
- highly clickable

Return as a list.
"""

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }

    for _ in range(3):
        try:
            res = requests.post(url, headers=headers, json=data)
            response = res.json()

            if "choices" in response:
                text = response["choices"][0]["message"]["content"]

                lines = text.split("\n")
                clean = [
                    l.strip("-•1234567890. ").strip()
                    for l in lines if len(l.strip()) > 5
                ]

                return clean[:5]

            if "error" in response:
                print("Rate limited... waiting")
                time.sleep(2)

        except Exception as e:
            print("Error:", e)
            time.sleep(2)

    return []


# 🔥 PICK BEST TOPIC
def get_best_topic():
    conn = sqlite3.connect("shorts.db")
    cur = conn.cursor()

    row = cur.execute("""
        SELECT topic FROM topics
        ORDER BY views DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    if not row:
        return None

    original = row[0]

    variations = generate_variations(original)

    if not variations:
        return original

    scored = [(v, score_topic(v)) for v in variations]
    scored.sort(key=lambda x: x[1], reverse=True)

    best = scored[0][0]

    print("\nORIGINAL:", original)
    print("🔥 BEST SELECTED:", best)

    return best


# 🔥 RUN PIPELINE
def run_pipeline(topic):
    print("\n🚀 Sending to pipeline...\n")

    subprocess.run([
        "python",
        "pipeline.py",
        topic
    ])


def main():
    print("🚀 Starting pipeline...")

    # 🔥 FORCE DB INIT FIRST
    init_db()
    print("✅ DB initialized")

    # 🔥 DEBUG: check table exists
    conn = sqlite3.connect("shorts.db")
    cur = conn.cursor()

    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='topics';")
        table = cur.fetchone()
        print("📊 Table exists:", table)
    except Exception as e:
        print("DB ERROR:", e)

    conn.close()

    # 🔥 NOW populate DB
    from trend_miner import mine_trends
    mine_trends()
    print("✅ Trends mined")

    # 🔥 NOW fetch topic
    topic = get_best_topic()

    if not topic:
        print("❌ No topic found")
        return

    run_pipeline(topic)

if __name__ == "__main__":
    main()
