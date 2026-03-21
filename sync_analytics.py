"""
ML Analytics Feedback Loop - Syncs YouTube video stats and applies ML score adjustments.
Designed to run daily on GitHub Actions to continuously improve topic selection.
"""

import os
import math
import re
from datetime import datetime
from dotenv import load_dotenv
from db import init_db, get_conn
from upload_youtube import get_youtube_client
from alerts import send_failure_alert

load_dotenv()

print("=" * 70)
print("🤖 YOUTUBE SHORTS - ML ANALYTICS FEEDBACK LOOP")
print(f"⏰ Started: {datetime.now().isoformat()}")
print("=" * 70)


def fetch_youtube_stats(youtube_ids):
    """
    Fetch video statistics from YouTube API in batches.
    Respects API limits by chunking into batches of 50.
    """
    print(f"\n📊 Fetching stats for {len(youtube_ids)} videos...")
    
    try:
        youtube = get_youtube_client()
    except Exception as e:
        print(f"❌ YouTube authentication failed: {e}")
        return {}
    
    stats = {}
    batch_size = 50
    
    for i in range(0, len(youtube_ids), batch_size):
        batch = youtube_ids[i:i + batch_size]
        batch_str = ','.join(batch)
        
        print(f"   📥 Batch {i//batch_size + 1}: Querying {len(batch)} videos...")
        
        try:
            request = youtube.videos().list(
                part="statistics",
                id=batch_str
            )
            response = request.execute()
            
            for item in response.get('items', []):
                video_id = item['id']
                stat = item['statistics']
                
                stats[video_id] = {
                    'views': int(stat.get('viewCount', 0)),
                    'likes': int(stat.get('likeCount', 0)),
                    'comments': int(stat.get('commentCount', 0))
                }
                
                print(f"      ✅ {video_id}: {stats[video_id]['views']} views, "
                      f"{stats[video_id]['likes']} likes, "
                      f"{stats[video_id]['comments']} comments")
        
        except Exception as e:
            print(f"      ⚠️  Error fetching batch: {e}")
            continue
    
    print(f"✅ Fetched stats for {len(stats)} videos")
    return stats


def upsert_video_stats(youtube_id, topic, views, likes, comments):
    """
    Insert or update video stats in the video_stats table.
    """
    conn = get_conn()
    try:
        conn.execute('''
            INSERT INTO video_stats (youtube_id, topic, views, likes, comments, last_checked)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(youtube_id) DO UPDATE SET
                views = excluded.views,
                likes = excluded.likes,
                comments = excluded.comments,
                last_checked = datetime('now')
        ''', (youtube_id, topic, views, likes, comments))
        conn.commit()
    except Exception as e:
        print(f"❌ Error upserting stats for {youtube_id}: {e}")
    finally:
        conn.close()


def extract_keywords(topic):
    """
    Extract words longer than 4 characters from topic for keyword matching.
    Used for ML feedback: viral topics boost similar non-used topics.
    """
    # Remove special characters, keep alphanumeric only
    clean_topic = re.sub(r'[^a-zA-Z0-9\s]', '', topic.lower())
    
    # Split and filter: keep words > 4 characters
    words = [w for w in clean_topic.split() if len(w) > 4]
    
    if words:
        print(f"   🔑 Keywords extracted from '{topic}': {words}")
    
    return words


def apply_ml_feedback(youtube_id, topic, views, likes, comments):
    """
    Core ML Loop: Boost topic scores based on viral video performance.
    - Videos with >500 views trigger a "viral" event
    - Calculate score bump: log10(views) * 1.5 (capped at 5.0)
    - Extract keywords from the topic
    - Apply score bump to all unused topics containing those keywords
    """
    print(f"\n🤖 ML Feedback Loop - Video: {youtube_id}")
    print(f"   Performance: {views} views, {likes} likes, {comments} comments")
    
    # Check if video is viral (arbitrary threshold: 500 views)
    if views < 500:
        print(f"   ℹ️  Views ({views}) below viral threshold (500) - no score boost")
        return
    
    print(f"   🔥 VIRAL DETECTED! Calculating score boost...")
    
    # Calculate score bump with logarithmic scaling and cap at 5.0
    score_bump = min(math.log10(views) * 1.5, 5.0)
    print(f"   📈 Score bump formula: log10({views}) * 1.5 = {score_bump:.2f} (capped at 5.0)")
    
    # Extract keywords from the viral topic
    keywords = extract_keywords(topic)
    
    if not keywords:
        print(f"   ℹ️  No keywords extracted from topic - skipping score boost")
        return
    
    # Update unused topics that contain any of these keywords
    conn = get_conn()
    try:
        # Find all unused topics containing any keyword
        for keyword in keywords:
            # Use LIKE for case-insensitive substring matching
            rows = conn.execute('''
                SELECT id, topic, score FROM topics
                WHERE used = 0 AND topic LIKE ?
            ''', (f'%{keyword}%',)).fetchall()
            
            if rows:
                print(f"   🎯 Keyword '{keyword}' matches {len(rows)} unused topics:")
                
                for row in rows:
                    topic_id, matched_topic, current_score = row
                    new_score = current_score + score_bump
                    
                    conn.execute('''
                        UPDATE topics SET score = ? WHERE id = ?
                    ''', (new_score, topic_id))
                    
                    print(f"      ✅ '{matched_topic}': {current_score:.2f} → {new_score:.2f}")
            else:
                print(f"   ℹ️  Keyword '{keyword}' matched no unused topics")
        
        conn.commit()
        print(f"   ✅ ML feedback applied and committed to DB")
    
    except Exception as e:
        print(f"   ❌ Error applying ML feedback: {e}")
    finally:
        conn.close()


def main():
    """
    Main function: Orchestrates the entire analytics sync pipeline.
    Tracks A/B variant performance for winning variant selection.
    """
    # Initialize database (creates video_stats table if needed)
    init_db()
    
    variant_performance = {"A": [], "B": [], "C": []}  # Track variant metrics
    
    # Step 1: Fetch all uploaded jobs with youtube_id
    print("\n📋 Step 1: Fetching uploaded jobs from database...")
    conn = get_conn()
    try:
        rows = conn.execute('''
            SELECT youtube_id, topic FROM jobs
            WHERE status = 'uploaded' AND youtube_id IS NOT NULL
        ''').fetchall()
        
        jobs = [dict(r) for r in rows]
        print(f"✅ Found {len(jobs)} uploaded videos in database")
        
        if not jobs:
            print("⚠️  No uploaded videos found - nothing to sync")
            conn.close()
            return
    
    except Exception as e:
        print(f"❌ Error fetching jobs: {e}")
        conn.close()
        return
    finally:
        conn.close()
    
    # Step 2: Fetch YouTube stats
    print("\n📊 Step 2: Fetching YouTube video statistics...")
    youtube_ids = [j['youtube_id'] for j in jobs]
    youtube_map = {j['youtube_id']: j['topic'] for j in jobs}
    
    stats = fetch_youtube_stats(youtube_ids)
    
    if not stats:
        print("⚠️  No stats fetched - skipping upsert and ML feedback")
        return
    
    # Step 3: Upsert stats into video_stats table
    print("\n💾 Step 3: Upserting stats into database...")
    for youtube_id, stat in stats.items():
        topic = youtube_map.get(youtube_id, 'unknown')
        upsert_video_stats(youtube_id, topic, stat['views'], stat['likes'], stat['comments'])
    
    print(f"✅ Upserted {len(stats)} video stats")
    
    # Step 4: Apply ML feedback loop
    print("\n🤖 Step 4: Applying ML feedback loop (viral topic boost)...")
    feedback_count = 0
    
    for youtube_id, stat in stats.items():
        topic = youtube_map.get(youtube_id, 'unknown')
        
        # Extract variant marker: [A]/[B]/[C] OR hook name (TERRIFYING/SHOCKING/3 REASONS)
        variant = None
        
        # Check for [A], [B], [C] markers first
        variant_match = re.search(r'\[([ABC])\]', topic)
        if variant_match:
            variant = variant_match.group(1)
        # Check for new hook-based titles
        elif 'TERRIFYING' in topic.upper():
            variant = 'A'
        elif 'SHOCKING' in topic.upper():
            variant = 'B'
        elif '3 REASONS' in topic.upper() or '3 REASONS' in topic:
            variant = 'C'
        
        if variant:
            variant_performance[variant].append({
                'views': stat['views'],
                'likes': stat['likes'],
                'comments': stat['comments'],
                'youtube_id': youtube_id
            })
        
        apply_ml_feedback(
            youtube_id,
            topic,
            stat['views'],
            stat['likes'],
            stat['comments']
        )
        
        if stat['views'] >= 500:
            feedback_count += 1
    
    print(f"\n✅ ML feedback applied to {feedback_count} viral videos")
    
    # Step 5: Detailed variant performance analysis with winner detection
    print("\n🧪 A/B TEST RESULTS - VARIANT PERFORMANCE ANALYSIS:")
    print("=" * 70)
    
    variant_summary = {}
    for variant in ["A", "B", "C"]:
        if variant_performance[variant]:
            data = variant_performance[variant]
            views_list = [d['views'] for d in data]
            likes_list = [d['likes'] for d in data]
            comments_list = [d['comments'] for d in data]
            
            avg_views = sum(views_list) / len(views_list)
            avg_likes = sum(likes_list) / len(likes_list)
            avg_comments = sum(comments_list) / len(comments_list)
            total_views = sum(views_list)
            engagement_rate = (sum(likes_list) + sum(comments_list)) / total_views * 100 if total_views > 0 else 0
            
            variant_summary[variant] = {
                'count': len(data),
                'avg_views': avg_views,
                'avg_likes': avg_likes,
                'avg_comments': avg_comments,
                'total_views': total_views,
                'engagement_rate': engagement_rate,
                'max_views': max(views_list)
            }
            
            variant_names = {'A': 'Shock (TERRIFYING)', 'B': 'Curiosity (SHOCKING)', 'C': 'Number (3 REASONS)'}
            print(f"\n   Variant {variant} - {variant_names.get(variant, 'Unknown')}:")
            print(f"      Videos: {len(data)}")
            print(f"      Total Views: {total_views}")
            print(f"      Avg Views/Video: {avg_views:.0f}")
            print(f"      Avg Likes: {avg_likes:.0f}")
            print(f"      Avg Comments: {avg_comments:.0f}")
            print(f"      Engagement Rate: {engagement_rate:.1f}%")
            print(f"      Peak Views: {max(views_list)}")
        else:
            print(f"\n   Variant {variant}: No data yet")
            variant_summary[variant] = {}
    
    # Determine winner by engagement rate (likes + comments / views)
    if variant_summary:
        winner_variant = max(
            [(v, data['engagement_rate']) for v, data in variant_summary.items() if data],
            key=lambda x: x[1],
            default=(None, 0)
        )[0]
        
        if winner_variant and variant_summary[winner_variant]:
            print(f"\n🏆 WINNER: Variant {winner_variant} (Highest Engagement Rate: {variant_summary[winner_variant]['engagement_rate']:.1f}%)")
            print(f"   Boost recommendation: Increase score for this variant's keywords")
        else:
            print(f"\n⏳ Not enough data yet to determine winner. Check back in 24-48 hours.")
    
    # Step 6: Summary
    print("\n" + "=" * 70)
    print("✅ ANALYTICS SYNC COMPLETE")
    print(f"   📊 Videos processed: {len(stats)}")
    print(f"   🔥 Viral events (>500 views): {feedback_count}")
    print(f"   📈 Topics boosted: Based on keyword matching from viral videos")
    print(f"   🧪 A/B Tests: {sum(len(v) for v in variant_performance.values())} variant videos tracked")
    print(f"⏰ Completed: {datetime.now().isoformat()}")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        send_failure_alert("analytics_sync", str(e), "analytics_loop")
        import traceback
        traceback.print_exc()
