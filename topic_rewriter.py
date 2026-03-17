import sqlite3
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# 🔥 FINAL CLEAN + VIRAL OPTIMIZER
def clean_final_output(text):
    text = text.replace('"', '')
    text = text.strip()

    # fix duplicates / typos
    text = text.replace("bodyr body", "body")
    text = text.replace("inside you", "in your body")

    # normalize casing
    text = text[0].upper() + text[1:] if text else text

    # ❌ remove weak/abstract topics
    banned_words = ["ionic", "bonds", "spark"]
    if any(word in text.lower() for word in banned_words):
        return None

    # 🔥 enforce curiosity hook
    if not any(word in text.lower().startswith(w) for w in ["why", "how", "what"]):
        text = "Why " + text.lower()

    return text


# 🔥 REWRITE FUNCTION (with retry + rate handling)
def rewrite_topic(topic):
    prompt = f"""
Rewrite this into a viral YouTube Shorts topic:

{topic}

Rules:
- Make it curiosity-driven
- 6-12 words max
- science/biology focused
- no names, no hashtags
- clean grammar
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
            response_json = res.json()

            # ✅ SUCCESS
            if "choices" in response_json:
                output = response_json["choices"][0]["message"]["content"].strip()

                cleaned = clean_final_output(output)

                if cleaned:
                    return cleaned
                else:
                    return topic

            # ⚠️ RATE LIMIT
            if "error" in response_json:
                print("Rate limited... waiting 2 sec")
                time.sleep(2)

        except Exception as e:
            print("Request error:", e)
            time.sleep(2)

    return topic  # fallback


# 🔥 MAIN LOOP
def rewrite_all():
    conn = sqlite3.connect("shorts.db")
    cur = conn.cursor()

    rows = cur.execute("SELECT id, topic FROM topics").fetchall()

    for row in rows:
        topic_id, topic = row

        try:
            new_topic = rewrite_topic(topic)

            cur.execute(
                "UPDATE topics SET topic = ? WHERE id = ?",
                (new_topic, topic_id)
            )

            print(f"Updated: {topic} → {new_topic}")

            # ⛔ avoid rate limit
            time.sleep(1.2)

        except Exception as e:
            print("Error:", e)

    conn.commit()
    conn.close()


# 🚀 ENTRY POINT
if __name__ == "_main__":
    rewrite_all()
