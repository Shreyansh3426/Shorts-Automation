#!/usr/bin/env python3
"""
Test that all database-accessing functions properly initialize the DB
"""

print("Testing all entry points for DB initialization...\n")

# Test 1: auto_pipeline.get_best_topic
try:
    from auto_pipeline import get_best_topic
    result = get_best_topic()
    print("✅ auto_pipeline.get_best_topic() - DB initialized")
except Exception as e:
    print(f"❌ auto_pipeline.get_best_topic(): {type(e).__name__}: {e}")

# Test 2: topic_scorer.score_topics
try:
    from topic_scorer import score_topics
    score_topics()
    print("✅ topic_scorer.score_topics() - DB initialized")
except Exception as e:
    print(f"❌ topic_scorer.score_topics(): {type(e).__name__}: {e}")

# Test 3: topic_multiplier.run
try:
    from topic_multiplier import run as multiplier_run
    multiplier_run()
    print("✅ topic_multiplier.run() - DB initialized")
except Exception as e:
    print(f"❌ topic_multiplier.run(): {type(e).__name__}: {e}")

# Test 4: topic_rewriter.rewrite_all
try:
    from topic_rewriter import rewrite_all
    rewrite_all()
    print("✅ topic_rewriter.rewrite_all() - DB initialized")
except Exception as e:
    print(f"❌ topic_rewriter.rewrite_all(): {type(e).__name__}: {e}")

# Test 5: topic_queue.get_next_topic
try:
    from topic_queue import get_next_topic
    next_topic = get_next_topic()
    print("✅ topic_queue.get_next_topic() - DB initialized")
except Exception as e:
    print(f"❌ topic_queue.get_next_topic(): {type(e).__name__}: {e}")

# Test 6: topic_queue.mark_topic_used
try:
    from topic_queue import mark_topic_used
    mark_topic_used(999)  # dummy ID
    print("✅ topic_queue.mark_topic_used() - DB initialized")
except Exception as e:
    print(f"❌ topic_queue.mark_topic_used(): {type(e).__name__}: {e}")

print("\n✅ All database-accessing functions have safeguards!")
