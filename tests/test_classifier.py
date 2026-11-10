
import unittest

from src.intelligence.classifier import classify_incident


class TestDisasterClassifier(unittest.TestCase):

    def test_flood_classification(self):
        result = classify_incident(
            "Heavy rainfall caused river overflow and flooding."
        )
        self.assertEqual(result["category"], "Flood")
        self.assertGreater(result["match_score"], 0)

    def test_earthquake_classification(self):
        result = classify_incident(
            "An earthquake caused tremors and aftershocks."
        )
        self.assertEqual(result["category"], "Earthquake")

    def test_fire_classification(self):
        result = classify_incident(
            "A wildfire spread through the forest with strong flames."
        )
        self.assertEqual(result["category"], "Fire")

    def test_storm_classification(self):
        result = classify_incident(
            "A cyclone brought strong winds and a thunderstorm."
        )
        self.assertEqual(result["category"], "Storm")

    def test_landslide_classification(self):
        result = classify_incident(
            "A landslide and mudslide blocked the mountain road."
        )
        self.assertEqual(result["category"], "Landslide")

    def test_unknown_description(self):
        result = classify_incident(
            "Several people are waiting near the town hall."
        )
        self.assertEqual(result["category"], "Other")
        self.assertTrue(result["needs_review"])

    def test_empty_description_rejected(self):
        with self.assertRaises(ValueError):
            classify_incident("   ")

    def test_non_string_description_rejected(self):
        with self.assertRaises(TypeError):
            classify_incident(123)


if __name__ == "__main__":
    unittest.main()
