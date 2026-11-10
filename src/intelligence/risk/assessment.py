
"""Transparent, rule-based disaster incident risk assessment.

This is a prototype decision-support tool, not a real-world prediction model.
The scoring weights are configurable and require validation before operational use.
"""

from collections.abc import Mapping


SEVERITY_POINTS = {
    "unassessed": 0,
    "low": 5,
    "moderate": 12,
    "high": 20,
    "critical": 25,
}

# Small, configurable context adjustments.
# These are prototype assumptions, not measured hazard probabilities.
DISASTER_CONTEXT_POINTS = {
    "flood": 5,
    "earthquake": 5,
    "fire": 4,
    "wildfire": 4,
    "storm": 4,
    "landslide": 5,
    "drought": 3,
    "other": 0,
}

RISK_THRESHOLDS = (
    (25, "Low"),
    (50, "Moderate"),
    (75, "High"),
    (101, "Critical"),
)


def _get_value(incident, field):
    """Read a field from either a dictionary or an incident object."""
    if isinstance(incident, Mapping):
        return incident.get(field)

    return getattr(incident, field, None)


def _validate_count(value, field):
    """Validate a non-negative whole-number incident count."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be a non-negative integer.")

    if value < 0:
        raise ValueError(f"{field} cannot be negative.")

    return value


def _people_points(count):
    """Return points based on the number of affected people (maximum 30)."""
    if count == 0:
        return 0
    if count < 10:
        return 3
    if count < 50:
        return 7
    if count < 200:
        return 12
    if count < 500:
        return 20
    return 30


def _housing_points(count):
    """Return points based on damaged houses (maximum 20)."""
    if count == 0:
        return 0
    if count < 5:
        return 2
    if count < 20:
        return 5
    if count < 50:
        return 10
    if count < 100:
        return 15
    return 20


def _risk_level(score):
    """Convert a numeric score into a risk category."""
    for threshold, level in RISK_THRESHOLDS:
        if score < threshold:
            return level

    return "Critical"


def assess_risk(incident):
    """Assess an incident and return its transparent risk breakdown.

    Accepted input:
      - An Incident object with the expected attributes.
      - A dictionary containing the expected fields.

    Returns:
      risk_score, risk_level, factors, explanation, needs_review
    """
    if not isinstance(incident, Mapping) and incident is None:
        raise ValueError("An incident object or dictionary is required.")

    affected_people = _validate_count(
        _get_value(incident, "affected_people"),
        "affected_people",
    )
    damaged_houses = _validate_count(
        _get_value(incident, "damaged_houses"),
        "damaged_houses",
    )

    severity = _get_value(incident, "severity")
    if not isinstance(severity, str):
        raise ValueError("severity must be a string.")

    severity = severity.strip().lower()
    if severity not in SEVERITY_POINTS:
        raise ValueError(
            f"Unsupported severity: {severity}. "
            f"Expected one of: {', '.join(SEVERITY_POINTS)}."
        )

    disaster_type = _get_value(incident, "disaster_type")
    if not isinstance(disaster_type, str) or not disaster_type.strip():
        raise ValueError("disaster_type must be a non-empty string.")

    disaster_type = disaster_type.strip()
    disaster_key = disaster_type.lower()

    active = _get_value(incident, "active")
    if not isinstance(active, bool):
        raise ValueError("active must be a boolean.")

    people_score = _people_points(affected_people)
    housing_score = _housing_points(damaged_houses)
    severity_score = SEVERITY_POINTS[severity]
    active_score = 10 if active else 0
    context_score = DISASTER_CONTEXT_POINTS.get(disaster_key, 0)

    raw_score = (
        people_score
        + housing_score
        + severity_score
        + active_score
        + context_score
    )
    score = min(100, raw_score)

    factors = {
        "affected_people": {
            "value": affected_people,
            "points": people_score,
            "maximum": 30,
        },
        "damaged_houses": {
            "value": damaged_houses,
            "points": housing_score,
            "maximum": 20,
        },
        "reported_severity": {
            "value": severity,
            "points": severity_score,
            "maximum": 25,
        },
        "active_status": {
            "value": active,
            "points": active_score,
            "maximum": 10,
        },
        "disaster_context": {
            "value": disaster_type,
            "points": context_score,
            "maximum": 5,
        },
    }

    explanation = [
        f"{affected_people} people affected: +{people_score} points.",
        f"{damaged_houses} damaged houses: +{housing_score} points.",
        f"Reported severity '{severity}': +{severity_score} points.",
        f"Incident {'is active' if active else 'is inactive'}: "
        f"+{active_score} points.",
        f"{disaster_type} context adjustment: +{context_score} points.",
    ]

    needs_review = severity == "unassessed"

    if disaster_key not in DISASTER_CONTEXT_POINTS:
        needs_review = True
        explanation.append(
            "Unknown disaster type: manual review is recommended."
        )

    if needs_review:
        explanation.append(
            "Manual review is recommended before using this assessment."
        )

    return {
        "risk_score": score,
        "risk_level": _risk_level(score),
        "factors": factors,
        "explanation": explanation,
        "needs_review": needs_review,
    }


if __name__ == "__main__":
    sample_incident = {
        "disaster_type": "Flood",
        "affected_people": 500,
        "damaged_houses": 120,
        "severity": "high",
        "active": True,
    }

    result = assess_risk(sample_incident)

    print("Risk Assessment")
    print("----------------")
    print(f"Risk Score: {result['risk_score']}/100")
    print(f"Risk Level: {result['risk_level']}")

    print("\nContributing Factors:")
    for explanation in result["explanation"]:
        print(f"- {explanation}")

    print(f"\nManual Review Required: {result['needs_review']}")
