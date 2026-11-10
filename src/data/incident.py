"""
Disaster Incident Management Module.

Defines the incident record used throughout the
AI-powered disaster response intelligence system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class Incident:
    """Represents a single reported disaster incident."""

    disaster_type: str
    location: str
    affected_people: int
    damaged_houses: int
    latitude: float
    longitude: float

    active: bool = True
    verified: bool = False
    severity: str = "unassessed"

    incident_id: str = field(
        default_factory=lambda: f"DIS-{uuid4().hex[:8].upper()}"
    )

    reported_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self):
        """Validate incident information before accepting it."""

        self.disaster_type = self._validate_text(
            self.disaster_type, "Disaster type"
        )

        self.location = self._validate_text(
            self.location, "Location"
        )

        self.severity = self._validate_text(
            self.severity, "Severity"
        ).lower()

        if (
            isinstance(self.affected_people, bool)
            or not isinstance(self.affected_people, int)
            or self.affected_people < 0
        ):
            raise ValueError(
                "Affected people must be a non-negative integer."
            )

        if (
            isinstance(self.damaged_houses, bool)
            or not isinstance(self.damaged_houses, int)
            or self.damaged_houses < 0
        ):
            raise ValueError(
                "Damaged houses must be a non-negative integer."
            )

        self.latitude = self._validate_coordinate(
            self.latitude, -90, 90, "Latitude"
        )

        self.longitude = self._validate_coordinate(
            self.longitude, -180, 180, "Longitude"
        )

        if not isinstance(self.active, bool):
            raise ValueError("Active must be True or False.")

        if not isinstance(self.verified, bool):
            raise ValueError("Verified must be True or False.")

    @staticmethod
    def _validate_text(value, field_name):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} cannot be empty.")

        return value.strip()

    @staticmethod
    def _validate_coordinate(value, minimum, maximum, field_name):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} must be a number.")

        if not minimum <= value <= maximum:
            raise ValueError(
                f"{field_name} must be between {minimum} and {maximum}."
            )

        return float(value)

    def to_dict(self):
        """Convert the incident into a database-friendly dictionary."""

        return {
            "incident_id": self.incident_id,
            "disaster_type": self.disaster_type,
            "location": self.location,
            "affected_people": self.affected_people,
            "damaged_houses": self.damaged_houses,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "active": self.active,
            "verified": self.verified,
            "severity": self.severity,
            "reported_at": self.reported_at.isoformat(),
        }

    def display(self):
        """Display a readable incident report."""

        print("\n" + "=" * 55)
        print("DISASTER INCIDENT REPORT")
        print("=" * 55)

        print(f"Incident ID: {self.incident_id}")
        print(f"Disaster Type: {self.disaster_type}")
        print(f"Location: {self.location}")
        print(f"Affected People: {self.affected_people}")
        print(f"Damaged Houses: {self.damaged_houses}")
        print(f"Latitude: {self.latitude}")
        print(f"Longitude: {self.longitude}")
        print(f"Severity: {self.severity}")
        print(f"Active: {self.active}")
        print(f"Verified: {self.verified}")
        print(f"Reported At: {self.reported_at.isoformat()}")

        print("=" * 55)


def main():
    """Create and display a sample disaster incident."""

    incident = Incident(
        disaster_type="Flood",
        location="Multan, Pakistan",
        affected_people=500,
        damaged_houses=120,
        latitude=30.1575,
        longitude=71.5249,
        active=True,
        verified=False,
    )

    incident.display()


if __name__ == "__main__":
    main()