import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'shorts.db')

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            script TEXT,
            keywords TEXT,
            voice_path TEXT,
            clips_json TEXT,
            video_path TEXT,
            youtube_id TEXT,
            error TEXT,
            attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            source TEXT DEFAULT 'manual',
            score REAL DEFAULT 0,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS clip_cache (
            keyword TEXT PRIMARY KEY,
            clip_path TEXT,
            downloaded_at TIMESTAMP,
            file_size INTEGER
        );
    ''')
    conn.commit()
    conn.close()
    print('Database initialized')

def create_job(topic):
    import uuid
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    conn = get_conn()
    conn.execute(
        'INSERT INTO jobs (id, topic, status) VALUES (?, ?, ?)',
        (job_id, topic, 'pending')
    )
    conn.commit()
    conn.close()
    return job_id

def update_job(job_id, **kwargs):
    kwargs['updated_at'] = datetime.now().isoformat()
    fields = ', '.join(f'{k} = ?' for k in kwargs)
    values = list(kwargs.values()) + [job_id]
    conn = get_conn()
    conn.execute(f'UPDATE jobs SET {fields} WHERE id = ?', values)
    conn.commit()
    conn.close()

def get_job(job_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_pending_jobs():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM jobs WHERE status = 'pending' ORDER BY created_at ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_topic(title, source='manual'):
    conn = get_conn()
    try:
        conn.execute(
            'INSERT INTO topics (title, source) VALUES (?, ?)',
            (title, source)
        )
        conn.commit()
        print(f'Topic added: {title}')
    except sqlite3.IntegrityError:
        print(f'Topic already exists: {title}')
    conn.close()

if __name__ == '__main__':
    init_db()
