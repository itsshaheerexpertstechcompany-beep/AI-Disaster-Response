
from collections import Counter
from datetime import date, datetime, timezone
from typing import Any

from src.intelligence.risk.assessment import assess_risk
from src.data.quality import audit_incidents


def _to_dict(incident: Any) -> dict:
    """Convert an Incident object or dictionary into a dictionary."""
    if isinstance(incident, dict):
        return incident.copy()

    if hasattr(incident, "to_dict"):
        return incident.to_dict()

    raise TypeError("Each incident must be a dictionary or Incident object.")


def _parse_reported_date(value: Any) -> date | None:
    """Extract a date from an incident timestamp."""
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).date()
        except ValueError:
            return None

    return None


def _safe_count(value: Any) -> int:
    """Return a valid non-negative integer, otherwise zero."""
    if isinstance(value, bool):
        return 0

    if isinstance(value, int) and value >= 0:
        return value

    return 0


def generate_analytics_report(
    incidents: list,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    """
    Generate a structured analytical report.

    Date filters are inclusive and use the date portion of reported_at.
    Invalid timestamps are excluded only when a date filter is active.
    """

    if not isinstance(incidents, (list, tuple)):
        raise TypeError("incidents must be a list or tuple.")

    if start_date is not None and not isinstance(start_date, date):
        raise TypeError("start_date must be a date or None.")

    if end_date is not None and not isinstance(end_date, date):
        raise TypeError("end_date must be a date or None.")

    if start_date and end_date and start_date > end_date:
        raise ValueError("start_date cannot be after end_date.")

    records = [_to_dict(item) for item in incidents]

    # Apply reporting-period filters.
    selected = []

    for record in records:
        if start_date is None and end_date is None:
            selected.append(record)
            continue

        reported_date = _parse_reported_date(record.get("reported_at"))

        if reported_date is None:
            continue

        if start_date and reported_date < start_date:
            continue

        if end_date and reported_date > end_date:
            continue

        selected.append(record)

    total = len(selected)

    active = sum(record.get("active") is True for record in selected)
    inactive = total - active

    verified = sum(record.get("verified") is True for record in selected)
    unverified = total - verified

    affected_people = sum(
        _safe_count(record.get("affected_people"))
        for record in selected
    )

    damaged_houses = sum(
        _safe_count(record.get("damaged_houses"))
        for record in selected
    )

    # Disaster type distribution.
    disaster_types = Counter(
        str(record.get("disaster_type") or "Unknown").strip().title()
        for record in selected
    )

    # Risk distribution.
    risk_distribution = Counter()
    risk_results = []

    for record in selected:
        try:
            result = assess_risk(record)
            risk_level = result["risk_level"]
            risk_distribution[risk_level] += 1

            risk_results.append({
                "incident_id": record.get("incident_id", "Unknown"),
                "risk_score": result["risk_score"],
                "risk_level": risk_level,
                "needs_review": result.get("needs_review", False),
            })

        except (TypeError, ValueError, KeyError):
            risk_distribution["Unavailable"] += 1

            risk_results.append({
                "incident_id": record.get("incident_id", "Unknown"),
                "risk_score": None,
                "risk_level": "Unavailable",
                "needs_review": True,
            })

    # Data quality audit.
    quality_report = audit_incidents(selected)

    # Daily reporting trend.
    daily_trend = Counter()

    for record in selected:
        reported_date = _parse_reported_date(record.get("reported_at"))

        if reported_date:
            daily_trend[reported_date.isoformat()] += 1

    # Synthetic data identification.
    synthetic_count = sum(
        "[DEMO]" in str(record.get("location", "")).upper()
        for record in selected
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reporting_period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
        "summary": {
            "total_incidents": total,
            "active_incidents": active,
            "inactive_incidents": inactive,
            "verified_incidents": verified,
            "unverified_incidents": unverified,
            "affected_people": affected_people,
            "damaged_houses": damaged_houses,
            "synthetic_incidents": synthetic_count,
        },
        "disaster_type_distribution": dict(disaster_types),
        "risk_distribution": dict(risk_distribution),
        "risk_results": risk_results,
        "quality_summary": quality_report,
        "daily_trend": dict(sorted(daily_trend.items())),
    }


def main():
    """Run a small demonstration report."""

    demo_incidents = [
        {
            "incident_id": "DIS-DEMO001",
            "disaster_type": "Flood",
            "location": "[DEMO] Multan, Pakistan",
            "affected_people": 500,
            "damaged_houses": 120,
            "severity": "high",
            "active": True,
            "verified": True,
            "reported_at": "2026-11-01T10:00:00+00:00",
        },
        {
            "incident_id": "DIS-DEMO002",
            "disaster_type": "Fire",
            "location": "[DEMO] Bahawalpur, Pakistan",
            "affected_people": 40,
            "damaged_houses": 8,
            "severity": "moderate",
            "active": True,
            "verified": False,
            "reported_at": "2026-11-02T12:00:00+00:00",
        },
    ]

    report = generate_analytics_report(demo_incidents)

    print("\nDISASTER ANALYTICS REPORT")
    print("=" * 35)

    for key, value in report["summary"].items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    print("\nDisaster Types:", report["disaster_type_distribution"])
    print("Risk Distribution:", report["risk_distribution"])
    print("Daily Trend:", report["daily_trend"])


if __name__ == "__main__":
    main()
