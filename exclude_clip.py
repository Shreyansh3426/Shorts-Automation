"""Utility to exclude specific clips from being used again"""
import sys
import sqlite3
import json

def exclude_clip(clip_url):
    """Exclude a clip URL from being used in future videos"""
    db_path = 'shorts.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if clip exists
        cursor.execute('SELECT excluded FROM clip_usage WHERE clip_url = ?', (clip_url,))
        row = cursor.fetchone()
        
        if row:
            # Update existing entry
            cursor.execute(
                'UPDATE clip_usage SET excluded = 1 WHERE clip_url = ?',
                (clip_url,)
            )
            print(f'✅ Clip marked as excluded: {clip_url}')
        else:
            # Create new entry with excluded=1
            cursor.execute(
                'INSERT INTO clip_usage (clip_url, job_ids, excluded) VALUES (?, ?, 1)',
                (clip_url, json.dumps([]))
            )
            print(f'✅ New clip added to exclusion list: {clip_url}')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f'❌ Error: {e}')
        conn.close()
        return False

def list_clips():
    """List all tracked clips and their usage"""
    db_path = 'shorts.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT clip_url, job_ids, excluded, last_used FROM clip_usage ORDER BY last_used DESC')
        rows = cursor.fetchall()
        
        if not rows:
            print('No clips tracked yet')
            return
        
        print(f'\n{"URL":<80} {"Used In":<20} {"Excluded":<10}')
        print('=' * 110)
        
        for url, job_ids_json, excluded, last_used in rows:
            job_ids = json.loads(job_ids_json) if job_ids_json else []
            num_uses = len(job_ids)
            excluded_str = '🚫 YES' if excluded else 'No'
            
            # Truncate URL for display
            display_url = url[:75] + '...' if len(url) > 75 else url
            print(f'{display_url:<80} {num_uses:<20} {excluded_str:<10}')
        
        conn.close()
    except Exception as e:
        print(f'❌ Error: {e}')
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage:')
        print('  python3 exclude_clip.py <clip_url>  - Exclude a specific clip')
        print('  python3 exclude_clip.py list        - List all tracked clips')
        sys.exit(1)
    
    if sys.argv[1] == 'list':
        list_clips()
    else:
        clip_url = sys.argv[1]
        exclude_clip(clip_url)
