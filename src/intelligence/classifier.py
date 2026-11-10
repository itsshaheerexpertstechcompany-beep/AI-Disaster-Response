
"""Transparent baseline classifier for disaster incident descriptions.

This is a keyword-based decision-support tool, not an official
emergency classification system or a trained predictive model.
"""

import re
from typing import Dict, List, Any


DISASTER_KEYWORDS = {
    "Flood": {
        "flood", "flooding", "overflow", "overflowing", "waterlogged",
        "inundation", "river overflow", "flash flood", "heavy rainfall",
        "water entered", "submerged"
    },
    "Earthquake": {
        "earthquake", "quake", "tremor", "aftershock", "seismic",
        "ground shaking", "building collapsed", "collapsed building"
    },
    "Fire": {
        "fire", "wildfire", "forest fire", "flames", "burning",
        "blaze", "smoke", "house caught fire", "building caught fire"
    },
    "Storm": {
        "storm", "thunderstorm", "cyclone", "hurricane", "tornado",
        "strong winds", "high winds", "windstorm", "hailstorm",
        "heavy wind"
    },
    "Landslide": {
        "landslide", "mudslide", "rockslide", "slope failure",
        "soil movement", "rocks fell", "mud flow"
    },
}

# Longer phrases are checked before shorter phrases.
SORTED_KEYWORDS = {
    category: sorted(words, key=len, reverse=True)
    for category, words in DISASTER_KEYWORDS.items()
}


def normalize_text(text: str) -> str:
    """Normalize text for consistent keyword matching."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text)


def classify_incident(description: str) -> Dict[str, Any]:
    """Classify an incident description using transparent keyword matching.

    Returns:
        category: Suggested disaster category, or "Other".
        match_score: Rule-based score from 0 to 100.
        matched_keywords: Keywords that matched the description.
        explanation: Human-readable explanation.
        needs_review: Whether manual review is recommended.
    """
    if not isinstance(description, str):
        raise TypeError("Incident description must be a string.")

    if not description.strip():
        raise ValueError("Incident description cannot be empty.")

    normalized = normalize_text(description)

    if not normalized:
        raise ValueError("Incident description must contain readable text.")

    scores: Dict[str, int] = {}
    matched: Dict[str, List[str]] = {}

    for category, keywords in SORTED_KEYWORDS.items():
        category_matches = []

        for keyword in keywords:
            # Match complete phrases/words, not partial words.
            pattern = r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])"

            if re.search(pattern, normalized):
                category_matches.append(keyword)

        matched[category] = category_matches
        scores[category] = len(category_matches)

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    if best_score == 0:
        return {
            "category": "Other",
            "match_score": 0,
            "matched_keywords": [],
            "explanation": (
                "No supported disaster keywords were found. "
                "Manual review is recommended."
            ),
            "needs_review": True,
        }

    # If two or more categories have the same highest score,
    # do not make an automatic category suggestion.
    top_categories = [
        category for category, score in scores.items()
        if score == best_score
    ]

    if len(top_categories) > 1:
        all_matches = {
            category: matched[category]
            for category in top_categories
        }

        return {
            "category": "Needs Review",
            "match_score": 0,
            "matched_keywords": all_matches,
            "explanation": (
                "The description matches multiple disaster categories "
                f"equally: {', '.join(top_categories)}. "
                "Please review the incident manually."
            ),
            "needs_review": True,
        }

    # This is a rule-based match score, not a probability.
    # Multiple matching keywords increase the score, up to 100.
    match_score = min(100, best_score * 30)

    # A single keyword match is deliberately flagged for review.
    needs_review = best_score < 2

    keywords_found = matched[best_category]

    explanation = (
        f"Suggested category: {best_category}. "
        f"Matching keywords: {', '.join(keywords_found)}."
    )

    if needs_review:
        explanation += " Only one keyword matched; manual review is recommended."

    return {
        "category": best_category,
        "match_score": match_score,
        "matched_keywords": keywords_found,
        "explanation": explanation,
        "needs_review": needs_review,
    }


if __name__ == "__main__":
    sample = (
        "Heavy rainfall caused river overflow and flooding in nearby homes."
    )

    result = classify_incident(sample)

    print("Incident description:", sample)
    print("Classification:", result["category"])
    print("Match score:", f'{result["match_score"]}%')
    print("Matched keywords:", result["matched_keywords"])
    print("Explanation:", result["explanation"])
    print("Needs manual review:", result["needs_review"])
