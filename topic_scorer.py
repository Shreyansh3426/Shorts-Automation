import sqlite3


def score_topics():

    conn = sqlite3.connect("shorts.db")
    cur = conn.cursor()

    rows = cur.execute("""
    SELECT id, views, likes FROM topics
    WHERE used = 0
    """).fetchall()

    for row in rows:

        topic_id, views, likes = row

        if views == 0:
            continue

        like_ratio = likes / views

        score = (views * 0.7) + (like_ratio * 1000)

        cur.execute("""
        UPDATE topics
        SET score = ?
        WHERE id = ?
        """, (score, topic_id))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    score_topics()

