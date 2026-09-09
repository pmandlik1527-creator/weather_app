"""
National Weather Big Data Analytics Platform (NWBDAP)
Source Verification & Credibility Scoring Engine
"""

import re
import config

OFFICIAL_HANDLES = {
    "@indiametdept", "@imdweather", "@ndrfhq", "@pib_india",
    "@moesgoi", "@ddnewslive", "@mybmc", "@bengalurupolice",
    "@delhipolice", "@sdmaindia"
}

VERIFIED_MET_HANDLES = {
    "@mumbaiweather", "@chennairains", "@delhiweather",
    "@keralaweather", "@skymetweather", "@weatherofindia",
    "@pradeepjohn_weatherman"
}

class SourceVerifier:
    """Evaluates author and channel reliability."""

    def __init__(self):
        self.tier_map = config.SOURCE_CREDIBILITY_MAP

    def verify_source(self, author_handle, source_type="social_media", has_verified_contact=False):
        """
        Determines the credibility tier and numerical score of an author.
        Returns:
            dict: {
                'tier': str,
                'score': float,
                'is_official': bool
            }
        """
        if not author_handle:
            author_handle = "anonymous"

        handle_lower = author_handle.lower().strip()

        # 1. Official Government & Meteorological Agencies
        if handle_lower in OFFICIAL_HANDLES or any(h in handle_lower for h in ["indiametdept", "ndrfhq", "moesgoi"]):
            return {
                "tier": "official_imd",
                "score": self.tier_map["official_imd"],
                "is_official": True,
                "label": "Official MoES / IMD Agency"
            }

        # 2. Verified Meteorological Analysts & Media
        if handle_lower in VERIFIED_MET_HANDLES or handle_lower.startswith("@toi") or handle_lower.startswith("@ani"):
            return {
                "tier": "verified_media",
                "score": self.tier_map["verified_media"],
                "is_official": False,
                "label": "Verified Weather Analyst / Media"
            }

        # 3. Citizen Portal with Phone/Email Validation
        if source_type == "citizen" and has_verified_contact:
            return {
                "tier": "citizen_verified",
                "score": self.tier_map["citizen_verified"],
                "is_official": False,
                "label": "Verified Citizen Contributor"
            }

        # 4. Bot & Automated Spam Heuristic
        # e.g., handles like user8237469281, bot_weather_391, random alphanumeric spammers
        if re.search(r"bot_\d{4,}|\w+\d{6,}$", handle_lower):
            return {
                "tier": "bot_flagged",
                "score": self.tier_map["bot_flagged"],
                "is_official": False,
                "label": "Flagged Bot / Automated Account"
            }

        # 5. Anonymous / Blank
        if handle_lower in ["anonymous", "guest", "unknown", ""]:
            return {
                "tier": "anonymous",
                "score": self.tier_map["anonymous"],
                "is_official": False,
                "label": "Anonymous Source"
            }

        # 6. Standard Social Public Contributor
        return {
            "tier": "social_public",
            "score": self.tier_map["social_public"],
            "is_official": False,
            "label": "Public Social Media User"
        }

source_verifier = SourceVerifier()
