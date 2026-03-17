import sqlite3
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# 🔥 SCORING SYSTEM (picks best hook)
def score_topic(text):
    score = 0
    text = text.lower()

    # curiosity triggers
    triggers = ["why", "how", "what", "secret", "hidden", "truth"]
    for t in triggers:
        if t in text:
            score += 2

    # strong words
    power_words = ["never", "instant", "forever", "inside", "real"]
    for w in power_words:
        if w in text:
            score += 2

    # penalize boring
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
- make them highly clickable

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

    for attempt in range(3):
        try:
            res = requests.post(url, headers=headers, json=data)
            response = res.json()

            if "choices" in response:
                text = response["choices"][0]["message"]["content"]

                lines = text.split("\n")
                clean = [
                    l.strip("-•1234567890. ").strip()
                    for l in lines
                    if len(l.strip()) > 5
                ]

                return clean[:5]

            if "error" in response:
                print("Rate limited... waiting")
                time.sleep(2)

        except Exception as e:
            print("Request error:", e)
            time.sleep(2)

    return []


# 🔥 MAIN
def run():
    conn = sqlite3.connect("shorts.db")
    cur = conn.cursor()

    rows = cur.execute("SELECT topic FROM topics LIMIT 20").fetchall()

    for row in rows:
        topic = row[0]

        variations = generate_variations(topic)

        if not variations:
            continue

        # score all variations
        scored = [(v, score_topic(v)) for v in variations]
        scored.sort(key=lambda x: x[1], reverse=True)

        best = scored[0][0]

        print("\n==============================")
        print("ORIGINAL:", topic)
        print("🔥 BEST:", best)
        print("------------------------------")

        for v, s in scored:
            print(f"{s} → {v}")

        # avoid rate limit
        time.sleep(2)


if __name__ == "__main__":
    run()
