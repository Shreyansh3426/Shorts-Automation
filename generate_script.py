import sys
import json
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')


def generate_script(topic):
    prompt = f"""
Create a HIGHLY ADDICTIVE YouTube Shorts script about:

{topic}

RULES:
- MAX 2 sentences ONLY
- 15–25 words total
- Sentence 1 = shocking hook
- Sentence 2 = fast explanation + LOOP ending
- Ending must feel incomplete and connect back to the hook
- Make viewer feel like something is still unresolved

STYLE:
- urgent
- curiosity driven
- slightly unsettling
- simple words

GOOD EXAMPLES:
"Your brain deletes memories every day.
And you never notice what you just forgot."

"Your body is slowly collapsing when you sit.
And it’s happening right now."

BAD:
"Did you know the brain has many functions?"
"""

    url = 'https://api.groq.com/openai/v1/chat/completions'

    headers = {
        'Authorization': f'Bearer {GROQ_API_KEY}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'llama-3.3-70b-versatile',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 200,
        'temperature': 0.9
    }

    # 🔁 retry system (handles rate limits)
    for attempt in range(5):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            res = response.json()

            # ✅ success
            if "choices" in res:
                text = res["choices"][0]["message"]["content"].strip()
                text = clean_text(text)

                result = {
                    'script': text,
                    'keywords': extract_keywords(text)
                }

                print(json.dumps(result))
                return

            # ⚠️ rate limit
            if "error" in res:
                print("Rate limited... waiting 2 sec")
                time.sleep(2)

        except Exception as e:
            print("Error:", e)
            time.sleep(2)

    # ❌ fallback
    fallback = f"{topic} is more dangerous than you think. And it might already be affecting you."
    result = {
        'script': fallback,
        'keywords': extract_keywords(fallback)
    }

    print(json.dumps(result))


# 🧹 clean weird formatting
def clean_text(text):
    text = text.replace('"', '').replace("'", "")
    text = text.replace("\n", " ")
    return text.strip()


# 🧠 keyword extractor (for tags / visuals later)
def extract_keywords(text):
    words = text.lower().split()

    ignore = {
        "your", "this", "that", "with", "from",
        "have", "will", "been", "they", "them",
        "about", "there", "their"
    }

    keywords = [
        w for w in words
        if len(w) > 4 and w not in ignore
    ]

    return list(dict.fromkeys(keywords))[:4]  # unique + limit 4


if __name__ == '__main__':
    topic = sys.argv[1] if len(sys.argv) > 1 else "The human brain"
    generate_script(topic)
