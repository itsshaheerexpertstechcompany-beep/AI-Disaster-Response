import unittest

from src.data.incident import Incident


class TestIncident(unittest.TestCase):

    def setUp(self):
        self.incident = Incident(
            disaster_type="Flood",
            location="Multan, Pakistan",
            affected_people=500,
            damaged_houses=120,
            latitude=30.1575,
            longitude=71.5249,
        )

    def test_incident_creation(self):
        self.assertEqual(self.incident.disaster_type, "Flood")
        self.assertEqual(self.incident.location, "Multan, Pakistan")

    def test_incident_id_is_generated(self):
        self.assertTrue(self.incident.incident_id.startswith("DIS-"))

    def test_negative_affected_people_is_rejected(self):
        with self.assertRaises(ValueError):
            Incident(
                disaster_type="Flood",
                location="Multan",
                affected_people=-10,
                damaged_houses=5,
                latitude=30.1575,
                longitude=71.5249,
            )

    def test_invalid_latitude_is_rejected(self):
        with self.assertRaises(ValueError):
            Incident(
                disaster_type="Flood",
                location="Multan",
                affected_people=100,
                damaged_houses=10,
                latitude=150,
                longitude=71.5249,
            )

    def test_incident_serialization(self):
        record = self.incident.to_dict()

        self.assertEqual(record["disaster_type"], "Flood")
        self.assertEqual(record["affected_people"], 500)
        self.assertIn("reported_at", record)


if __name__ == "__main__":
    unittest.main()