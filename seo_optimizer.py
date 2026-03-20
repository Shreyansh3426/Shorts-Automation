def generate_seo_metadata(topic: str, script: str, keywords: list[str] | None = None) -> dict:
    """
    Returns dict with title, description, tags optimized for 2026 YouTube Shorts.
    Extremely high-CTR, keyword-rich, curiosity-driven.
    """
    # Extract main topic word
    topic_words = [w for w in topic.lower().split() if len(w) > 3]
    main_topic = topic_words[0].capitalize() if topic_words else topic[:20]
    
    # Shock word rotation based on topic hash
    shock_words = ["SHOCKING", "INSANE", "WILD", "MIND-BLOWING", "RARE", "INCREDIBLE", "UNBELIEVABLE", "STUNNING"]
    shock = shock_words[hash(topic) % len(shock_words)]
    
    # Title: shock word + topic + emoji (max 60 chars)
    if len(topic) > 40:
        title = f"{shock} {topic[:30]} 😱"
    else:
        title = f"{shock} {topic} 😱"
    
    title = title[:60]
    
    # Description: hook + summary + CTA + hashtags
    hook = f"Did you know? {main_topic} has secrets that will blow your mind..."
    summary = script[:100].strip() + "..." if len(script) > 100 else script.strip()
    
    hashtags = [
        "#Shorts",
        "#Facts",
        "#MindBlowing",
        f"#{main_topic}Facts",
        "#Education",
        "#Learning",
        "#Viral",
        "#Interesting"
    ]
    
    description = f"{hook}\n\n{summary}\n\n🤖 AI Generated • Comment your guess below! 👇 #Shorts\n\n{' '.join(hashtags)}"
    
    # Tags: base + keyword variations (12-15 max)
    base_tags = [
        "shorts",
        "facts",
        f"{main_topic.lower()} facts",
        "mind blowing facts",
        "education",
        "learning",
        "viral",
        "interesting"
    ]
    
    if keywords:
        for kw in keywords[:3]:
            if len(kw) > 2:
                base_tags.append(f"{kw} facts")
    
    # Remove duplicates while preserving order, limit to 15
    tags = list(dict.fromkeys(base_tags))[:15]
    
    return {
        "title": title,
        "description": description,
        "tags": tags
    }
