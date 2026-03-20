def generate_ab_variants(topic: str, base_script: str, keywords: list[str]) -> list[dict]:
    """
    Returns list of 3 variant dicts for A/B testing.
    Each variant has different hook + ending question.
    """
    
    # Extract core facts from base script (skip first sentence, keep middle-end)
    sentences = [s.strip() for s in base_script.split('.') if s.strip()]
    core_facts = '. '.join(sentences[1:]) if len(sentences) > 1 else base_script
    
    # Get main topic word
    topic_word = topic.split()[0].capitalize() if topic else "This"
    
    # Variant A: Shock hook
    hook_a = f"Your {topic_word.lower()} does something TERRIFYING."
    question_a = "Have you ever noticed this?"
    script_a = f"{hook_a} {core_facts} {question_a}"[:180].strip()
    
    # Variant B: Curiosity hook
    hook_b = f"Ever wondered why {topic_word.lower()}s are so weird?"
    question_b = "Tell me in the comments below!"
    script_b = f"{hook_b} {core_facts} {question_b}"[:180].strip()
    
    # Variant C: Number hook
    hook_c = f"3 shocking facts about {topic_word.lower()}s revealed."
    question_c = "Which one shocked you most?"
    script_c = f"{hook_c} {core_facts} {question_c}"[:180].strip()
    
    return [
        {
            "variant": "A",
            "script": script_a,
            "title_hook": "TERRIFYING"
        },
        {
            "variant": "B",
            "script": script_b,
            "title_hook": "SHOCKING"
        },
        {
            "variant": "C",
            "script": script_c,
            "title_hook": "3 FACTS"
        }
    ]
