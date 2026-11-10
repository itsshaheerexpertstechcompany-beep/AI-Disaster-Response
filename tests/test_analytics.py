
import unittest
from datetime import date

from src.reports.analytics import generate_analytics_report


class TestAnalyticsReport(unittest.TestCase):

    def setUp(self):
        self.incidents = [
            {
                "incident_id": "DIS-TEST001",
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
                "incident_id": "DIS-TEST002",
                "disaster_type": "Fire",
                "location": "[DEMO] Bahawalpur, Pakistan",
                "affected_people": 40,
                "damaged_houses": 8,
                "severity": "moderate",
                "active": False,
                "verified": False,
                "reported_at": "2026-11-02T12:00:00+00:00",
            },
            {
                "incident_id": "DIS-TEST003",
                "disaster_type": "Storm",
                "location": "Lahore, Pakistan",
                "affected_people": 10,
                "damaged_houses": 2,
                "severity": "low",
                "active": True,
                "verified": True,
                "reported_at": "2026-11-03T08:00:00+00:00",
            },
        ]

    def test_report_summary(self):
        report = generate_analytics_report(self.incidents)
        summary = report["summary"]

        self.assertEqual(summary["total_incidents"], 3)
        self.assertEqual(summary["active_incidents"], 2)
        self.assertEqual(summary["inactive_incidents"], 1)
        self.assertEqual(summary["verified_incidents"], 2)
        self.assertEqual(summary["unverified_incidents"], 1)
        self.assertEqual(summary["affected_people"], 550)
        self.assertEqual(summary["damaged_houses"], 130)
        self.assertEqual(summary["synthetic_incidents"], 2)

    def test_disaster_type_distribution(self):
        report = generate_analytics_report(self.incidents)

        distribution = report["disaster_type_distribution"]

        self.assertEqual(distribution["Flood"], 1)
        self.assertEqual(distribution["Fire"], 1)
        self.assertEqual(distribution["Storm"], 1)

    def test_risk_results_cover_all_incidents(self):
        report = generate_analytics_report(self.incidents)

        self.assertEqual(len(report["risk_results"]), 3)

        for result in report["risk_results"]:
            self.assertIn("incident_id", result)
            self.assertIn("risk_score", result)
            self.assertIn("risk_level", result)
            self.assertIn("needs_review", result)

    def test_risk_distribution_totals(self):
        report = generate_analytics_report(self.incidents)

        self.assertEqual(
            sum(report["risk_distribution"].values()),
            3,
        )

    def test_daily_trend(self):
        report = generate_analytics_report(self.incidents)

        self.assertEqual(
            report["daily_trend"],
            {
                "2026-11-01": 1,
                "2026-11-02": 1,
                "2026-11-03": 1,
            },
        )

    def test_date_filter_is_inclusive(self):
        report = generate_analytics_report(
            self.incidents,
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 2),
        )

        self.assertEqual(report["summary"]["total_incidents"], 2)
        self.assertEqual(
            report["reporting_period"]["start_date"],
            "2026-11-01",
        )
        self.assertEqual(
            report["reporting_period"]["end_date"],
            "2026-11-02",
        )

    def test_start_date_filter(self):
        report = generate_analytics_report(
            self.incidents,
            start_date=date(2026, 11, 2),
        )

        self.assertEqual(report["summary"]["total_incidents"], 2)

    def test_end_date_filter(self):
        report = generate_analytics_report(
            self.incidents,
            end_date=date(2026, 11, 2),
        )

        self.assertEqual(report["summary"]["total_incidents"], 2)

    def test_invalid_timestamp_excluded_when_filtering(self):
        incidents = [
            {
                **self.incidents[0],
                "reported_at": "not-a-valid-date",
            }
        ]

        report = generate_analytics_report(
            incidents,
            start_date=date(2026, 11, 1),
        )

        self.assertEqual(report["summary"]["total_incidents"], 0)

    def test_invalid_timestamp_included_without_date_filter(self):
        incidents = [
            {
                **self.incidents[0],
                "reported_at": "not-a-valid-date",
            }
        ]

        report = generate_analytics_report(incidents)

        self.assertEqual(report["summary"]["total_incidents"], 1)
        self.assertEqual(report["daily_trend"], {})

    def test_empty_incident_list(self):
        report = generate_analytics_report([])

        self.assertEqual(report["summary"]["total_incidents"], 0)
        self.assertEqual(report["summary"]["affected_people"], 0)
        self.assertEqual(report["summary"]["damaged_houses"], 0)
        self.assertEqual(report["disaster_type_distribution"], {})
        self.assertEqual(report["risk_distribution"], {})
        self.assertEqual(report["risk_results"], [])
        self.assertEqual(report["daily_trend"], {})

    def test_invalid_input_type(self):
        with self.assertRaises(TypeError):
            generate_analytics_report("not a list")

    def test_invalid_start_date_type(self):
        with self.assertRaises(TypeError):
            generate_analytics_report(
                self.incidents,
                start_date="2026-11-01",
            )

    def test_invalid_end_date_type(self):
        with self.assertRaises(TypeError):
            generate_analytics_report(
                self.incidents,
                end_date="2026-11-03",
            )

    def test_reversed_date_range(self):
        with self.assertRaises(ValueError):
            generate_analytics_report(
                self.incidents,
                start_date=date(2026, 11, 3),
                end_date=date(2026, 11, 1),
            )


if __name__ == "__main__":
    unittest.main()
