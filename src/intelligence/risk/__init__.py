
import unittest

from src.intelligence.risk.assessment import assess_risk


class TestRiskAssessment(unittest.TestCase):

    def setUp(self):
        self.incident = {
            "disaster_type": "Flood",
            "affected_people": 500,
            "damaged_houses": 120,
            "severity": "high",
            "active": True,
        }

    def test_high_impact_flood(self):
        result = assess_risk(self.incident)

        self.assertEqual(result["risk_score"], 90)
        self.assertEqual(result["risk_level"], "Critical")

    def test_zero_impact_incident(self):
        incident = {
            "disaster_type": "Other",
            "affected_people": 0,
            "damaged_houses": 0,
            "severity": "low",
            "active": False,
        }

        result = assess_risk(incident)

        self.assertEqual(result["risk_score"], 5)
        self.assertEqual(result["risk_level"], "Low")

    def test_active_incident_adds_points(self):
        active_result = assess_risk(self.incident)

        inactive = self.incident.copy()
        inactive["active"] = False
        inactive_result = assess_risk(inactive)

        self.assertEqual(
            active_result["risk_score"] - inactive_result["risk_score"],
            10,
        )

    def test_unknown_disaster_requires_review(self):
        incident = self.incident.copy()
        incident["disaster_type"] = "Volcanic Event"

        result = assess_risk(incident)

        self.assertTrue(result["needs_review"])

    def test_unassessed_severity_requires_review(self):
        incident = self.incident.copy()
        incident["severity"] = "unassessed"

        result = assess_risk(incident)

        self.assertTrue(result["needs_review"])

    def test_score_never_exceeds_100(self):
        incident = {
            "disaster_type": "Earthquake",
            "affected_people": 1000000,
            "damaged_houses": 1000000,
            "severity": "critical",
            "active": True,
        }

        result = assess_risk(incident)

        self.assertLessEqual(result["risk_score"], 100)

    def test_negative_people_count_rejected(self):
        incident = self.incident.copy()
        incident["affected_people"] = -5

        with self.assertRaises(ValueError):
            assess_risk(incident)

    def test_invalid_severity_rejected(self):
        incident = self.incident.copy()
        incident["severity"] = "extreme"

        with self.assertRaises(ValueError):
            assess_risk(incident)

    def test_dictionary_input_returns_all_fields(self):
        result = assess_risk(self.incident)

        self.assertIn("risk_score", result)
        self.assertIn("risk_level", result)
        self.assertIn("factors", result)
        self.assertIn("explanation", result)
        self.assertIn("needs_review", result)


if __name__ == "__main__":
    unittest.main()
