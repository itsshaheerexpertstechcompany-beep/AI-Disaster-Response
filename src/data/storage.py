
"""
Incident storage utilities.

Handles saving, loading, retrieving, updating, and deactivating
disaster incidents in a local JSON file.
"""

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from src.data.incident import Incident


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "data" / "processed" / "incidents.json"

UPDATABLE_FIELDS = {
    "disaster_type",
    "location",
    "affected_people",
    "damaged_houses",
    "latitude",
    "longitude",
    "active",
    "verified",
    "severity",
}


def _read_records():
    """Read stored incident records from disk."""

    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            records = json.load(file)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Incident storage contains invalid JSON: {DATA_FILE}"
        ) from error

    if not isinstance(records, list):
        raise RuntimeError("Incident storage must contain a JSON list.")

    return records


def _write_records(records):
    """Write records safely, replacing the file only after a complete write."""

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = None

    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=DATA_FILE.parent,
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            json.dump(records, temporary_file, indent=4, ensure_ascii=False)
            temporary_file.write("\n")
            temporary_path = Path(temporary_file.name)

        os.replace(temporary_path, DATA_FILE)

    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def _incident_from_record(record):
    """Convert a stored dictionary back into an Incident object."""

    if not isinstance(record, dict):
        raise RuntimeError("An incident record must be a JSON object.")

    values = dict(record)

    try:
        from datetime import datetime

        values["reported_at"] = datetime.fromisoformat(
            values["reported_at"]
        )

        return Incident(**values)

    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError(
            "A stored incident record could not be loaded."
        ) from error


def save_incident(incident):
    """Save a new incident and return its generated or existing ID."""

    if not isinstance(incident, Incident):
        raise TypeError("Expected an Incident object.")

    records = _read_records()

    if any(
        record.get("incident_id") == incident.incident_id
        for record in records
        if isinstance(record, dict)
    ):
        raise ValueError(
            f"Incident {incident.incident_id} already exists."
        )

    records.append(incident.to_dict())
    _write_records(records)

    return incident.incident_id


def load_incidents():
    """Return all stored incidents as Incident objects."""

    return [
        _incident_from_record(record)
        for record in _read_records()
    ]


def get_incident(incident_id):
    """Find one incident using its unique ID."""

    for record in _read_records():
        if (
            isinstance(record, dict)
            and record.get("incident_id") == incident_id
        ):
            return _incident_from_record(record)

    return None


def update_incident(incident_id, **changes):
    """Update permitted fields of an existing incident."""

    if not changes:
        raise ValueError("Provide at least one field to update.")

    invalid_fields = set(changes) - UPDATABLE_FIELDS

    if invalid_fields:
        names = ", ".join(sorted(invalid_fields))
        raise ValueError(f"These fields cannot be updated: {names}")

    records = _read_records()

    for index, record in enumerate(records):
        if (
            isinstance(record, dict)
            and record.get("incident_id") == incident_id
        ):
            incident = _incident_from_record(record)

            updated_values = {
                "disaster_type": incident.disaster_type,
                "location": incident.location,
                "affected_people": incident.affected_people,
                "damaged_houses": incident.damaged_houses,
                "latitude": incident.latitude,
                "longitude": incident.longitude,
                "active": incident.active,
                "verified": incident.verified,
                "severity": incident.severity,
                "incident_id": incident.incident_id,
                "reported_at": incident.reported_at,
            }

            updated_values.update(changes)
            updated_incident = Incident(**updated_values)

            records[index] = updated_incident.to_dict()
            _write_records(records)

            return updated_incident

    return None


def deactivate_incident(incident_id):
    """Mark an incident as inactive without deleting its history."""

    return update_incident(incident_id, active=False)