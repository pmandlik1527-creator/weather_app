"""
Unit tests for AI/ML Processing Layer
- Auto-Categorizer
- Fake / Misleading Report Detector
- Source Verifier
- Deduplicator
"""

import unittest
from ml.categorizer import categorizer
from ml.fake_detector import fake_detector
from ml.source_verifier import source_verifier
from ml.deduplicator import deduplicator

class TestMLPipeline(unittest.TestCase):

    def test_auto_categorizer(self):
        """Verify categorization on representative weather phrases."""
        test_cases = [
            ("Continuous rain and waterlogging near Dadar station #MumbaiRains", "Flooding"),
            ("Intense cloudburst and rainfall flooding the underpass", "Flooding"),
            ("Loud thunder and lightning strikes across Gurugram", "Thunderstorm"),
            ("Extreme heatwave condition with temperature reaching 47°C in Churu", "Heatwave"),
            ("Dense smog and zero visibility on Yamuna Expressway", "Fog/Smog"),
            ("Heavy hailstones pounding Shimla apple orchards", "Hailstorm"),
            ("Cyclone making landfall on Odisha coast with 100 kmph winds", "Cyclone"),
            ("Fresh snowfall recorded in Gulmarg ski slopes", "Snowfall"),
            ("Sandstorm and dust gale blinding highway traffic in Jaipur", "Dust Storm")
        ]

        correct = 0
        for text, expected in test_cases:
            res = categorizer.predict(text)
            self.assertIn("category", res)
            self.assertGreater(res["confidence"], 0.2)
            if res["category"] == expected:
                correct += 1

        accuracy = correct / len(test_cases)
        print(f"\n[TEST ML] Categorizer Accuracy: {accuracy * 100:.1f}% ({correct}/{len(test_cases)})")
        self.assertGreaterEqual(accuracy, 0.85)

    def test_fake_detector(self):
        """Verify multi-signal fake detection on impossible or sensational claims."""
        # 1. Climatically implausible: Snowfall in Chennai
        fake_chennai_snow = {
            "raw_text": "Shocking snowfall falling at Marina Beach Chennai today morning!",
            "detected_category": "Snowfall",
            "state": "Tamil Nadu",
            "city": "Chennai",
            "latitude": 13.0827,
            "longitude": 80.2707
        }
        res1 = fake_detector.evaluate(fake_chennai_snow, source_credibility_score=50.0)
        self.assertTrue(res1["is_fake"])
        self.assertLess(res1["authenticity_score"], 50.0)
        self.assertTrue(any("Snowfall" in r for r in res1["reasons"]))

        # 2. Extreme sensationalist apocalypse
        fake_apocalypse = {
            "raw_text": "APOCALYPSE IN MUMBAI!!!! ENTIRE CITY SUBMERGED RUN FOR YOUR LIVES!!!! DOOMSDAY DELUGE!!!!",
            "detected_category": "Flooding",
            "state": "Maharashtra",
            "city": "Mumbai",
            "latitude": 19.0760,
            "longitude": 72.8777
        }
        res2 = fake_detector.evaluate(fake_apocalypse, source_credibility_score=40.0)
        self.assertTrue(res2["is_fake"])
        self.assertLess(res2["authenticity_score"], 50.0)

        # 3. Genuine authentic report: Heavy rain in Mumbai
        genuine_rain = {
            "raw_text": "Moderate rain showers observed across Dadar since 1 hour. Traffic moving normally.",
            "detected_category": "Rainfall",
            "state": "Maharashtra",
            "city": "Mumbai",
            "latitude": 19.0178,
            "longitude": 72.8478
        }
        res3 = fake_detector.evaluate(genuine_rain, source_credibility_score=80.0)
        self.assertFalse(res3["is_fake"])
        self.assertGreaterEqual(res3["authenticity_score"], 60.0)
        print("[TEST ML] Fake Detector validated across climatic and sensational tests.")

    def test_source_verifier(self):
        """Verify author trust scoring and tier categorization."""
        imd = source_verifier.verify_source("@Indiametdept")
        self.assertEqual(imd["tier"], "official_imd")
        self.assertEqual(imd["score"], 98.0)
        self.assertTrue(imd["is_official"])

        media = source_verifier.verify_source("@MumbaiWeather")
        self.assertEqual(media["tier"], "verified_media")

        bot = source_verifier.verify_source("bot_weather_982734")
        self.assertEqual(bot["tier"], "bot_flagged")
        self.assertLessEqual(bot["score"], 20.0)
        print("[TEST ML] Source Verifier tiering validated.")

if __name__ == "__main__":
    unittest.main()
