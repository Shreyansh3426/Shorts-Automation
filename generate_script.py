import sys
import json
import requests
import os
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

def generate_script(topic):
    prompt = f"""You are a YouTube Shorts scriptwriter.
Write a 30-second narration script about: {topic}

RULES:
1. First sentence: shocking or surprising fact. No 'Did you know' openings.
2. Body: 4 short sentences, max 10 words each.
3. End with a cliffhanger or mind-blowing final fact.
4. Total: 60-80 words only.
5. Write ONLY the spoken words. No labels or directions.

After the script add this line:
KEYWORDS: keyword1, keyword2, keyword3, keyword4"""

    response = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {GROQ_API_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'llama-3.3-70b-versatile',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 400,
            'temperature': 0.8
        }
    )

    full_text = response.json()['choices'][0]['message']['content']

    if 'KEYWORDS:' in full_text:
        parts = full_text.split('KEYWORDS:')
        script = parts[0].strip()
        keywords = [k.strip() for k in parts[1].strip().split(',')]
    else:
        script = full_text.strip()
        keywords = ['nature', 'science', 'space', 'people']

    result = {'script': script, 'keywords': keywords}
    print(json.dumps(result))

if __name__ == '__main__':
    topic = sys.argv[1] if len(sys.argv) > 1 else 'The human brain'
    generate_script(topic)
