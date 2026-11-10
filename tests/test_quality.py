
import unittest

from src.data.quality import assess_data_quality, audit_incidents


def make_incident(**overrides):
    incident = {
        "incident_id": "DIS-TEST001",
        "disaster_type": "Flood",
        "location": "Multan, Pakistan",
        "affected_people": 120,
        "damaged_houses": 30,
        "latitude": 30.1575,
        "longitude": 71.5249,
        "active": True,
        "verified": True,
        "severity": "high",
        "reported_at": "2026-11-09T10:00:00+00:00",
    }

    incident.update(overrides)
    return incident


class TestDataQuality(unittest.TestCase):

    def test_valid_incident_has_good_quality(self):
        result = assess_data_quality(make_incident())

        self.assertEqual(result["quality_score"], 100)
        self.assertEqual(result["status"], "Good quality")
        self.assertFalse(result["needs_review"])

    def test_missing_location_is_flagged(self):
        result = assess_data_quality(make_incident(location=""))

        codes = [issue["code"] for issue in result["issues"]]

        self.assertIn("missing_location", codes)
        self.assertEqual(result["status"], "Invalid data")

    def test_missing_coordinates_are_flagged(self):
        result = assess_data_quality(
            make_incident(latitude=None, longitude=None)
        )

        codes = [issue["code"] for issue in result["issues"]]

        self.assertIn("missing_coordinates", codes)
        self.assertEqual(result["status"], "Needs review")

    def test_incomplete_coordinates_are_flagged(self):
        result = assess_data_quality(
            make_incident(latitude=30.1, longitude=None)
        )

        codes = [issue["code"] for issue in result["issues"]]

        self.assertIn("incomplete_coordinates", codes)

    def test_invalid_coordinates_are_flagged(self):
        result = assess_data_quality(
            make_incident(latitude=150, longitude=71.5)
        )

        codes = [issue["code"] for issue in result["issues"]]

        self.assertIn("invalid_coordinates", codes)

    def test_negative_affected_people_are_rejected(self):
        result = assess_data_quality(
            make_incident(affected_people=-5)
        )

        codes = [issue["code"] for issue in result["issues"]]

        self.assertIn("invalid_affected_people", codes)

    def test_unverified_report_needs_review(self):
        result = assess_data_quality(
            make_incident(verified=False)
        )

        codes = [issue["code"] for issue in result["issues"]]

        self.assertIn("unverified_report", codes)
        self.assertTrue(result["needs_review"])

    def test_unassessed_severity_needs_review(self):
        result = assess_data_quality(
            make_incident(severity="unassessed")
        )

        codes = [issue["code"] for issue in result["issues"]]

        self.assertIn("unassessed_severity", codes)

    def test_invalid_timestamp_is_flagged(self):
        result = assess_data_quality(
            make_incident(reported_at="not-a-date")
        )

        codes = [issue["code"] for issue in result["issues"]]

        self.assertIn("invalid_timestamp", codes)

    def test_duplicate_incident_ids_are_detected(self):
        first = make_incident()
        second = make_incident(location="Bahawalpur, Pakistan")

        result = audit_incidents([first, second])

        self.assertEqual(result["total_incidents"], 2)
        self.assertEqual(result["invalid_data"], 2)

        for report in result["reports"]:
            codes = [issue["code"] for issue in report["issues"]]
            self.assertIn("duplicate_incident_id", codes)

    def test_empty_dataset(self):
        result = audit_incidents([])

        self.assertEqual(result["total_incidents"], 0)
        self.assertEqual(result["average_quality_score"], 0)


if __name__ == "__main__":
    unittest.main()
