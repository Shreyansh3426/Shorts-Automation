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
    # Clean up any stale connections and WAL files
    import glob
    db_dir = os.path.dirname(DB_PATH)
    
    # Try to remove WAL files if they exist (can cause migration issues)
    for wal_file in glob.glob(os.path.join(db_dir, 'shorts.db-*')):
        try:
            os.remove(wal_file)
        except:
            pass
    
    conn = get_conn()
    conn.execute('PRAGMA journal_mode=DELETE;')  # Use DELETE mode for safer migration
    
    # Check if topics table exists and validate schema
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='topics'")
    table_exists = cur.fetchone() is not None
    
    # If table exists, check if it has the correct schema
    needs_migration = False
    if table_exists:
        cur.execute("PRAGMA table_info(topics)")
        columns = {row[1] for row in cur.fetchall()}
        required_columns = {'id', 'topic', 'views', 'likes', 'score', 'used', 'created_at'}
        
        if not required_columns.issubset(columns):
            print(f"⚠️  Schema mismatch detected. Current: {columns}, Required: {required_columns}")
            needs_migration = True
    
    # Close connection before migration
    conn.close()
    
    # If migration needed, drop and recreate with fresh connection
    if needs_migration:
        print("🔄 Migrating topics table...")
        conn = get_conn()
        conn.execute('PRAGMA journal_mode=DELETE;')
        try:
            conn.execute("DROP TABLE IF EXISTS topics")
            conn.commit()
            print("✅ Old topics table dropped")
        except Exception as e:
            print(f"❌ Error dropping table: {e}")
            conn.close()
            raise
        conn.close()
    
    # Create tables with fresh connection
    conn = get_conn()
    conn.execute('PRAGMA journal_mode=DELETE;')
    
    try:
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
                topic TEXT UNIQUE,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
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
        print('✅ Database initialized successfully')
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        conn.close()
        raise
    finally:
        conn.close()

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

def add_topic(topic, views=0, likes=0, source='manual'):
    conn = get_conn()
    try:
        conn.execute(
            'INSERT INTO topics (topic, views, likes) VALUES (?, ?, ?)',
            (topic, views, likes)
        )
        conn.commit()
        print(f'✅ Topic added: {topic}')
    except sqlite3.IntegrityError:
        print(f'ℹ️  Topic already exists: {topic}')
    except Exception as e:
        print(f'❌ Error adding topic: {e}')
    conn.close()

if __name__ == '__main__':
    init_db()
