
"""Data quality checks for disaster incident records.

This module flags data-quality issues. It never modifies incident records.
"""

from datetime import datetime


VALID_SEVERITIES = {
    "unassessed",
    "low",
    "moderate",
    "high",
    "critical",
}


def _to_record(incident):
    """Convert an Incident object or dictionary into a dictionary."""
    if isinstance(incident, dict):
        return incident

    if hasattr(incident, "to_dict"):
        return incident.to_dict()

    raise TypeError("Each incident must be a dictionary or an Incident object.")


def _add_issue(issues, code, severity, message):
    issues.append({
        "code": code,
        "severity": severity,
        "message": message,
    })


def assess_data_quality(incident):
    """Assess one incident and return a quality report."""
    record = _to_record(incident)
    issues = []

    # Required text fields
    for field in ("incident_id", "disaster_type", "location"):
        value = record.get(field)

        if not isinstance(value, str) or not value.strip():
            _add_issue(
                issues,
                f"missing_{field}",
                "error",
                f"The {field.replace('_', ' ')} is missing or invalid.",
            )

    # Affected people and damaged houses
    for field in ("affected_people", "damaged_houses"):
        value = record.get(field)

        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            _add_issue(
                issues,
                f"invalid_{field}",
                "error",
                f"{field.replace('_', ' ').capitalize()} must be a non-negative integer.",
            )

    # Geographic coordinates
    latitude = record.get("latitude")
    longitude = record.get("longitude")

    if latitude is None and longitude is None:
        _add_issue(
            issues,
            "missing_coordinates",
            "warning",
            "No geographic coordinates are available for this incident.",
        )
    elif latitude is None or longitude is None:
        _add_issue(
            issues,
            "incomplete_coordinates",
            "warning",
            "Both latitude and longitude are required for map placement.",
        )
    else:
        try:
            lat = float(latitude)
            lon = float(longitude)

            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError

        except (TypeError, ValueError):
            _add_issue(
                issues,
                "invalid_coordinates",
                "error",
                "Latitude or longitude is invalid or outside its permitted range.",
            )

    # Verification status
    verified = record.get("verified")

    if not isinstance(verified, bool):
        _add_issue(
            issues,
            "invalid_verification_status",
            "error",
            "Verification status must be True or False.",
        )
    elif not verified:
        _add_issue(
            issues,
            "unverified_report",
            "warning",
            "This incident has not been verified.",
        )

    # Severity
    severity = record.get("severity")

    if not isinstance(severity, str) or severity.lower() not in VALID_SEVERITIES:
        _add_issue(
            issues,
            "invalid_severity",
            "error",
            "The incident severity is missing or not recognized.",
        )
    elif severity.lower() == "unassessed":
        _add_issue(
            issues,
            "unassessed_severity",
            "warning",
            "Incident severity has not yet been assessed.",
        )

    # Active status
    if not isinstance(record.get("active"), bool):
        _add_issue(
            issues,
            "invalid_active_status",
            "error",
            "Active status must be True or False.",
        )

    # Report timestamp
    timestamp = record.get("reported_at")

    try:
        if isinstance(timestamp, datetime):
            parsed_timestamp = timestamp
        elif isinstance(timestamp, str) and timestamp.strip():
            parsed_timestamp = datetime.fromisoformat(
                timestamp.strip().replace("Z", "+00:00")
            )
        else:
            raise ValueError

        if parsed_timestamp.tzinfo is None:
            _add_issue(
                issues,
                "timezone_missing",
                "warning",
                "The report timestamp does not include a timezone.",
            )

    except (TypeError, ValueError):
        _add_issue(
            issues,
            "invalid_timestamp",
            "error",
            "The report timestamp is missing or invalid.",
        )

    # Calculate a transparent quality score.
    penalties = {
        "error": 25,
        "warning": 10,
        "info": 3,
    }

    deductions = sum(
        penalties[issue["severity"]]
        for issue in issues
    )

    quality_score = max(0, 100 - deductions)

    if any(issue["severity"] == "error" for issue in issues):
        status = "Invalid data"
    elif issues:
        status = "Needs review"
    else:
        status = "Good quality"

    return {
        "incident_id": record.get("incident_id"),
        "quality_score": quality_score,
        "status": status,
        "needs_review": bool(issues),
        "issue_count": len(issues),
        "issues": issues,
    }


def audit_incidents(incidents):
    """Audit a collection of incidents and detect duplicate IDs."""
    records = [_to_record(item) for item in incidents]

    reports = [
        assess_data_quality(record)
        for record in records
    ]

    # Find duplicate non-empty incident IDs.
    id_positions = {}

    for index, record in enumerate(records):
        incident_id = record.get("incident_id")

        if isinstance(incident_id, str) and incident_id.strip():
            id_positions.setdefault(incident_id, []).append(index)

    for incident_id, positions in id_positions.items():
        if len(positions) > 1:
            for index in positions:
                _add_issue(
                    reports[index]["issues"],
                    "duplicate_incident_id",
                    "error",
                    f"Incident ID {incident_id} appears more than once.",
                )

                reports[index]["issue_count"] += 1
                reports[index]["quality_score"] = max(
                    0,
                    reports[index]["quality_score"] - 25,
                )
                reports[index]["status"] = "Invalid data"
                reports[index]["needs_review"] = True

    total = len(reports)
    good = sum(report["status"] == "Good quality" for report in reports)
    review = sum(report["status"] == "Needs review" for report in reports)
    invalid = sum(report["status"] == "Invalid data" for report in reports)

    average_score = (
        round(sum(report["quality_score"] for report in reports) / total, 2)
        if total
        else 0
    )

    return {
        "total_incidents": total,
        "good_quality": good,
        "needs_review": review,
        "invalid_data": invalid,
        "average_quality_score": average_score,
        "reports": reports,
    }


if __name__ == "__main__":
    sample = {
        "incident_id": "DIS-DEMO001",
        "disaster_type": "Flood",
        "location": "Multan, Pakistan",
        "affected_people": 120,
        "damaged_houses": 30,
        "latitude": 30.1575,
        "longitude": 71.5249,
        "active": True,
        "verified": False,
        "severity": "unassessed",
        "reported_at": "2026-11-09T10:00:00+00:00",
    }

    print(assess_data_quality(sample))
