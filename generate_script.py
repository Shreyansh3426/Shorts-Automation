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
Create a SHOCKING YouTube Shorts script (15-16 seconds) about:

{topic}

RULES - FOR 15-16 SECOND VIDEO (HIGH ENGAGEMENT):
- 3-4 sentences ONLY (50-60 words total for perfect pacing)
- Starts with shocking hook: "Did you know...", "This is why...", "A GROUP OF...", "This is terrifying..."
- Each sentence MORE shocking than previous
- Build tension and intrigue throughout  
- CRITICAL: End with COMMENT BAIT question (e.g., "Have you ever seen this?", "Did this surprise you?", "Would you touch it?")
- Use simple words - max 15 words per sentence
- Keep language conversational and direct

TONE & STYLE:
- Science/nature facts (like IFL Science)
- Shocking revelations - make viewers go "WAIT WHAT?!"
- Urgent, gripping, personal
- Make them THINK, FEEL wonder, WANT TO COMMENT

PERFECT EXAMPLES (15-16 sec format with comment bait):
"A group of butterflies taste with their feet.
They know if food is poison before eating it.
Your tongue can NEVER do that.
Have you ever noticed something this weird in nature?"

"Your body has trillions of cells.
But MOST aren't actually you.
Bacteria control your health in ways you don't know.
Are you creeped out yet? Comment below."

"Plants hide weapons in their leaves.
One drop causes extreme fire-like pain.
It's growing in forests RIGHT NOW.
Would you ever touch it? Tell me in comments."

ENGAGEMENT MULTIPLIER:
- Questions that make viewers WANT to comment
- Reference personal experience ("Have you?", "Did you?")
- Create conversation starters
- Invite opinion or experience sharing

NEVER:
- Generic facts ("brains are complex")
- Sentences over 15 words
- Boring educational tone
- Vague vocabulary
- Forget the SHOCK + COMMENT HOOK combo
"""

    url = 'https://api.groq.com/openai/v1/chat/completions'

    headers = {
        'Authorization': f'Bearer {GROQ_API_KEY}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'llama-3.3-70b-versatile',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 250,
        'temperature': 0.85
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
                text = enforce_script_length(topic, text)

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

    # ❌ fallback with shocking tone
    fallback = f"This is shocking about {topic}. Most people don't know it. But it's happening right now. And you need to see this."
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


def enforce_script_length(topic, text):
    words = [w for w in text.split() if w.strip()]
    if len(words) >= 45:
        return text

    expand_prompt = f"""
Rewrite this YouTube Shorts script to be 45-65 words in 3-4 short sentences.
Keep same topic and shocking tone. Simple words only.

Topic: {topic}
Current script: {text}
"""

    url = 'https://api.groq.com/openai/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {GROQ_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'llama-3.3-70b-versatile',
        'messages': [{'role': 'user', 'content': expand_prompt}],
        'max_tokens': 250,
        'temperature': 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        res = response.json()
        if 'choices' in res:
            expanded = clean_text(res['choices'][0]['message']['content'].strip())
            expanded_words = [w for w in expanded.split() if w.strip()]
            if len(expanded_words) >= 45:
                return expanded
    except Exception:
        pass

    fillers = [
        "Most people discover this far too late.",
        "Your body reacts before your brain even understands what happened.",
        "Scientists still debate how this works in real life.",
        "And this is happening around you right now."
    ]

    rebuilt = text.strip()
    idx = 0
    while len([w for w in rebuilt.split() if w.strip()]) < 45 and idx < len(fillers):
        rebuilt = f"{rebuilt} {fillers[idx]}"
        idx += 1

    final_words = rebuilt.split()
    if len(final_words) > 65:
        rebuilt = " ".join(final_words[:65]).rstrip(".,!?") + "."

    return rebuilt


# 🧠 keyword extractor (for tags / visuals later)
def extract_keywords(text):
    words = text.lower().split()

    ignore = {
        "your", "this", "that", "with", "from",
        "have", "will", "been", "they", "them",
        "about", "there", "their", "and", "but",
        "why", "you", "are", "the", "is", "it"
    }

    keywords = [
        w for w in words
        if len(w) > 4 and w not in ignore
    ]

    return list(dict.fromkeys(keywords))[:4]  # unique + limit 4


if __name__ == '__main__':
    topic = sys.argv[1] if len(sys.argv) > 1 else "The human brain"
    generate_script(topic)
