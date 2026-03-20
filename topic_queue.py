import os
import sys
import json
import requests
from dotenv import load_dotenv
from db import init_db, add_topic, get_conn

load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

def generate_topics(niche='dark psychology and human behavior', count=20):
    prompt = f"""Generate {count} viral YouTube Shorts video topics about: {niche}

Requirements:
- Each topic must be a question or shocking statement
- Must work with stock footage (no face needed)
- Must be curiosity-triggering in first 3 words
- Must appeal to all ages and countries
- No duplicate ideas

Return ONLY a JSON array like this:
["topic 1", "topic 2", "topic 3"]"""

    response = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {GROQ_API_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'llama-3.3-70b-versatile',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 1000,
            'temperature': 0.9
        },
        timeout=30
    )

    if response.status_code != 200:
        raise Exception(f'Groq error: {response.status_code}')

    content = response.json()['choices'][0]['message']['content']

    # Parse JSON array
    import re
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if not match:
        raise Exception(f'Could not parse topics: {content[:200]}')

    topics = json.loads(match.group())
    return topics

def queue_topics(niche='dark psychology and human behavior', count=20):
    init_db()
    print(f'Generating {count} topics for niche: {niche}')
    topics = generate_topics(niche, count)
    added = 0
    skipped = 0
    for topic in topics:
        conn = get_conn()
        try:
            conn.execute(
                'INSERT INTO topics (title, source, score) VALUES (?, ?, ?)',
                (topic, 'ai_generated', 8.0)
            )
            conn.commit()
            print(f'  + {topic}')
            added += 1
        except Exception:
            print(f'  ~ skipped (duplicate): {topic}')
            skipped += 1
        finally:
            conn.close()
    print(f'\nDone: {added} added, {skipped} skipped')

def get_next_topic():
    init_db()
    conn = get_conn()
    row = conn.execute(
        "SELECT id, title FROM topics WHERE used = 0 ORDER BY score DESC, created_at ASC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def mark_topic_used(topic_id):
    init_db()
    conn = get_conn()
    conn.execute('UPDATE topics SET used = 1 WHERE id = ?', (topic_id,))
    conn.commit()
    conn.close()
if __name__ == '__main__':
    if len(sys.argv) > 1:
        niche = ' '.join(sys.argv[1:])
    else:
        niche = 'dark psychology and human behavior'
    queue_topics(niche)
