
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.data.incident import Incident
from src.data import storage


class TestIncidentStorage(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = Path(self.temp_dir.name) / "incidents.json"

        self.storage_patch = patch.object(
            storage, "DATA_FILE", self.storage_file
        )
        self.storage_patch.start()

        self.incident = Incident(
            disaster_type="Flood",
            location="Multan, Pakistan",
            affected_people=500,
            damaged_houses=120,
            latitude=30.1575,
            longitude=71.5249,
        )

    def tearDown(self):
        self.storage_patch.stop()
        self.temp_dir.cleanup()

    def test_save_and_load_incident(self):
        storage.save_incident(self.incident)

        incidents = storage.load_incidents()

        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0].location, "Multan, Pakistan")

    def test_get_incident_by_id(self):
        storage.save_incident(self.incident)

        result = storage.get_incident(self.incident.incident_id)

        self.assertIsNotNone(result)
        self.assertEqual(result.incident_id, self.incident.incident_id)

    def test_missing_incident_returns_none(self):
        result = storage.get_incident("DIS-NOTFOUND")

        self.assertIsNone(result)

    def test_update_incident(self):
        storage.save_incident(self.incident)

        updated = storage.update_incident(
            self.incident.incident_id,
            affected_people=750,
            severity="high",
        )

        self.assertEqual(updated.affected_people, 750)
        self.assertEqual(updated.severity, "high")

        saved = storage.get_incident(self.incident.incident_id)

        self.assertEqual(saved.affected_people, 750)

    def test_deactivate_incident(self):
        storage.save_incident(self.incident)

        updated = storage.deactivate_incident(
            self.incident.incident_id
        )

        self.assertFalse(updated.active)

    def test_duplicate_incident_is_rejected(self):
        storage.save_incident(self.incident)

        with self.assertRaises(ValueError):
            storage.save_incident(self.incident)

    def test_invalid_update_field_is_rejected(self):
        storage.save_incident(self.incident)

        with self.assertRaises(ValueError):
            storage.update_incident(
                self.incident.incident_id,
                reported_at="2026-01-01",
            )


if __name__ == "__main__":
    unittest.main()
