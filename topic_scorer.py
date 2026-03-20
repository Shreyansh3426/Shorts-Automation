from db import init_db, get_conn


def score_topics():
    # Ensure DB is initialized before querying
    init_db()
    
    conn = get_conn()
    cur = conn.cursor()

    rows = cur.execute("""
    SELECT id, topic, views, likes FROM topics
    WHERE used = 0
    """).fetchall()

    # High-performing niche keywords (from analytics: 597-view winner is animal/nature content)
    niche_keywords = ['animal', 'biology', 'space', 'nature', 'shark', 'octopus', 'bear', 'snake', 'fish', 'planet', 'star', 'galaxy', 'insect', 'creature']
    niche_multiplier = 1.5  # 50% score boost for verified high-performers

    for row in rows:
        topic_id, topic, views, likes = row

        if views == 0:
            continue

        like_ratio = likes / views
        score = (views * 0.7) + (like_ratio * 1000)

        # Apply niche multiplier for high-performing topics
        topic_lower = topic.lower() if topic else ""
        if any(keyword in topic_lower for keyword in niche_keywords):
            score *= niche_multiplier
            print(f"🎯 Niche boost applied to '{topic}': {score:.0f} (multiplier: {niche_multiplier}x)")

        cur.execute("""
        UPDATE topics
        SET score = ?
        WHERE id = ?
        """, (score, topic_id))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    score_topics()

