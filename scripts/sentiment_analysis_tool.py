# Placeholder for Sentiment Analysis Tool

import random
import re

def get_sentiment_score(text: str) -> dict:
    """
    Simulates sentiment analysis on a given text.

    In a real scenario, this would use a pre-trained model (like VADER, TextBlob, Hugging Face Transformers).
    For this project, it returns a simulated sentiment score.

    Args:
        text: The input text string.

    Returns:
        A dictionary containing 'label' (positive, negative, neutral) 
        and 'score' (a float, e.g., between -1 for very negative and 1 for very positive).
    """
    if not isinstance(text, str) or not text.strip():
        return {"label": "neutral", "score": 0.0, "error": "Input text was empty or invalid."}

    # Simple keyword-based simulation
    text_lower = text.lower()
    # Using regex to match whole words for better accuracy
    positive_keywords = [r"\bgood\b", r"\bgreat\b", r"\bsuccess(?:ful)?\b", r"\bsupport(?:s|ed|ing)?\b", r"\bapprove(?:d|s)?\b", r"\bbenefit(?:s|ed|ing)?\b", r"\badvance(?:d|s|ment)?\b", r"\bpositive\b", r"\bhopeful\b", r"\bpromising\b"]
    negative_keywords = [r"\bbad\b", r"\bterrible\b", r"\bfailure\b", r"\boppose(?:d|s|ition)?\b", r"\breject(?:s|ed|ion)?\b", r"\bharm(?:ful)?\b", r"\bdecline(?:d|s)?\b", r"\bnegative\b", r"\bconcern(?:s|ed)?\b", r"\bcrisis\b", r"\bproblem(?:atic)?\b"]

    score = 0.0
    
    for p_kw_pattern in positive_keywords:
        if re.search(p_kw_pattern, text_lower):
            score += 0.25 # Increment for each positive keyword match
    
    for n_kw_pattern in negative_keywords:
        if re.search(n_kw_pattern, text_lower):
            score -= 0.25 # Decrement for each negative keyword match

    # Add some randomness to make it seem more like a real model
    # This can be removed if deterministic behavior is preferred for the simulation
    # score += random.uniform(-0.05, 0.05) 
    
    # Normalize score to be within a typical range, e.g., -1 to 1
    # The score could exceed this if many keywords are present, so clamping is important.
    score = max(-1.0, min(1.0, score))

    label = "neutral"
    if score >= 0.15: # Adjusted threshold slightly
        label = "positive"
    elif score <= -0.15: # Adjusted threshold slightly
        label = "negative"

    return {"label": label, "score": round(score, 4)}

if __name__ == '__main__':
    # Example Usage
    sample_texts = [
        "This is a great development for the community, showing positive advancement.",
        "There are serious concerns about the new policy; it's problematic.",
        "The bill aims to support renewable energy projects, a promising step.",
        "The effects of this legislation are still unclear.",
        "Opponents reject the proposed changes, citing harmful outcomes.",
        "The new bill is good and offers support to many.",
        "This is bad, a total failure with negative consequences and much concern.",
        "", # Empty text
        "Despite initial support, the project now faces significant opposition due to concerns about its negative impact." # Mixed
    ]

    for text in sample_texts:
        sentiment = get_sentiment_score(text)
        print(f"Text: \"{text}\"\nSentiment: {sentiment}\n")
    
    complex_text = "While the initiative shows positive signs for economic support and is a promising advancement, some critics voice negative concerns and strong opposition regarding its long-term impact and potential harm to small businesses. This problem needs a solution."
    sentiment = get_sentiment_score(complex_text)
    print(f"Text: \"{complex_text}\"\nSentiment: {sentiment}\n")
