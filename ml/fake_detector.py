"""
National Weather Big Data Analytics Platform (NWBDAP)
AI/ML Fake / Misleading Report Detection Engine
Multi-signal authenticity evaluation for weather intelligence.
"""

import re
from datetime import datetime
import config
from database.repository import get_nearby_recent_reports

# Sensationalist / Clickbait vocabulary and panic markers
SENSATIONALIST_PATTERNS = [
    (r"\b(apocalypse|doomsday|end of the world|cataclysm)\b", "Apocalyptic language detected"),
    (r"\b(wiped out|submerged completely|entire city underwater|sinking)\b", "Extreme exaggeration of disaster scale"),
    (r"\b(sharks? in the street|giant crocodile in flood)\b", "Common viral social media hoax tropes"),
    (r"\b(unbelievable catastrophe|worst in human history|deluge of the millennium)\b", "Hyperbolic catastrophic claims"),
    (r"[!]{3,}", "Excessive exclamation marks (panic signaling)"),
    (r"\b(omg+|run for your lives|flee immediately)\b", "Unverified panic-inducing phrases"),
    (r"\b(secret cloud seeding|government weather weapon|haarp)\b", "Weather conspiracy theory terminology")
]

class FakeReportDetector:
    """Multi-signal Authenticity & Fake Report Classifier."""

    def __init__(self):
        self.plausibility_rules = config.CLIMATIC_PLAUSIBILITY_RULES
        self.threshold = config.FAKE_SCORE_THRESHOLD

    def evaluate(self, report_dict, source_credibility_score=60.0):
        """
        Evaluates a report for authenticity and misinformation.
        Parameters:
            report_dict (dict): Report data including text, category, state, city, lat, lon.
            source_credibility_score (float): Baseline trust score from source verifier.
        Returns:
            dict: {
                'authenticity_score': float (0-100),
                'is_fake': bool,
                'reasons': list of str,
                'signals': dict
            }
        """
        raw_text = report_dict.get("raw_text", "")
        category = report_dict.get("detected_category", "Rainfall")
        state = report_dict.get("state", "Unknown")
        city = report_dict.get("city", "Unknown")
        lat = report_dict.get("latitude")
        lon = report_dict.get("longitude")

        reasons = []
        score = source_credibility_score # Base score from source trust

        # 1. Content Sensationalism & Panic Signal
        sensationalism_penalty = 0
        for pattern, reason in SENSATIONALIST_PATTERNS:
            if re.search(pattern, raw_text, re.IGNORECASE):
                sensationalism_penalty += 18
                reasons.append(reason)

        # Check for ALL CAPS screaming
        words = raw_text.split()
        if len(words) >= 4:
            caps_count = sum(1 for w in words if w.isupper() and len(w) > 1)
            if (caps_count / len(words)) > 0.45:
                sensationalism_penalty += 15
                reasons.append("Excessive uppercase text (sensational shouting)")

        score -= min(sensationalism_penalty, 40)

        # 2. Meteorological & Geographical Plausibility Signal
        plausibility_penalty = 0
        if state and state != "Unknown":
            # Snowfall verification
            if category == "Snowfall" and state not in self.plausibility_rules.get("Snowfall", []):
                plausibility_penalty += 65
                reasons.append(f"Climatically implausible: Snowfall does not occur in {state}")

            # Cyclone inland verification
            if category == "Cyclone" and state not in self.plausibility_rules.get("Cyclone", []):
                plausibility_penalty += 45
                reasons.append(f"Geographically implausible: Landlocked state ({state}) cannot experience tropical cyclone landfall")

            # High altitude heatwave check
            if category == "Heatwave" and state in ["Ladakh", "Sikkim"]:
                plausibility_penalty += 40
                reasons.append(f"Climatically implausible: Heatwave condition in high-altitude Himalayan territory ({state})")

        score -= min(plausibility_penalty, 70)

        # 3. Spatio-temporal Corroboration Signal
        consensus_bonus = 0
        if lat is not None and lon is not None:
            try:
                nearby = get_nearby_recent_reports(lat, lon, max_dist_km=25.0, max_hours_ago=3.0)
                matching_category = [r for r in nearby if r.get("detected_category") == category]

                if len(matching_category) >= 3:
                    consensus_bonus = 15
                    # Boost confidence when multiple independent reports agree
                    score += consensus_bonus
                elif len(matching_category) == 0 and category in ["Flooding", "Cyclone", "Hailstorm"]:
                    # Isolated extreme report without corroboration
                    if source_credibility_score < 70:
                        score -= 10
                        reasons.append("Isolated extreme weather claim with zero corroborating nearby reports")
            except Exception:
                pass # Corroboration fallback during initial bootstrapping

        # 4. Final Score Normalization & Boundary Clamping
        final_score = max(0.0, min(100.0, round(score, 1)))
        is_fake = final_score < self.threshold

        if is_fake and not reasons:
            reasons.append("Cumulative low credibility across text patterns and source indicators")

        return {
            "authenticity_score": final_score,
            "is_fake": is_fake,
            "reasons": reasons,
            "signals": {
                "source_baseline": source_credibility_score,
                "sensationalism_penalty": sensationalism_penalty,
                "plausibility_penalty": plausibility_penalty,
                "consensus_bonus": consensus_bonus
            }
        }

fake_detector = FakeReportDetector()
