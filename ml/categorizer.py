"""
National Weather Big Data Analytics Platform (NWBDAP)
AI/ML Auto-Categorization Engine
Classifies weather reports into 10 IMD standard categories.
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import config

# Rich training corpus reflecting Indian weather terminology, social media posts, and citizen vocabulary
TRAINING_DATA = [
    # Rainfall
    ("Heavy rainfall observed across Dadar and Lower Parel since morning #MumbaiRains", "Rainfall"),
    ("Continuous drizzle and light showers in Connaught Place New Delhi", "Rainfall"),
    ("Torrential downpour lashed south Bengaluru, streets receiving heavy rain", "Rainfall"),
    ("Substantial precipitation recorded at Kolkata Alipore weather station today", "Rainfall"),
    ("Bahut tez baarish ho rahi hai yahan par, continuous rain for 3 hours", "Rainfall"),
    ("Moderate to heavy showers in Chennai Anna Nagar, skies overcast", "Rainfall"),
    ("Pitter patter rainfall starting in Pune, weather became cool", "Rainfall"),
    ("Monsoon showers arrive in Kerala, steady rainfall along the coast", "Rainfall"),
    ("Non-stop rain in Guwahati since midnight, umbrellas out", "Rainfall"),

    # Thunderstorm
    ("Massive lightning strike and loud thunder in Gurugram sector 56", "Thunderstorm"),
    ("Thunderstorm with intense cloud-to-ground lightning across Noida", "Thunderstorm"),
    ("Bijli kadak rahi hai aur tez badal garaj rahe hain, scary thunderstorm", "Thunderstorm"),
    ("Severe thunder activity and lightning strikes reported in North Kolkata", "Thunderstorm"),
    ("Thunderstorm approaching Hyderabad Banjara Hills, loud thunderclaps", "Thunderstorm"),
    ("Lightning struck a tree near airport, heavy thunder and gusty winds", "Thunderstorm"),
    ("Severe electric storm with continuous thunder flashes in Bhopal", "Thunderstorm"),

    # Flooding
    ("Milan subway flooded, waterlogging up to knee height, traffic halted", "Flooding"),
    ("Severe waterlogging on Outer Ring Road Bellandur, vehicles submerged in flood water", "Flooding"),
    ("Dadar Hindmata underwater, pumps deployed for flood drainage", "Flooding"),
    ("Pani bhar gaya poori sadak pe, residential colony flooded after reservoir overflow", "Flooding"),
    ("Urban flooding in Patna low-lying areas, houses inundated with water", "Flooding"),
    ("Yamuna river overflowing danger mark, flood alert issued for Delhi lowlands", "Flooding"),
    ("Heavy inundation and flash floods in Guwahati streets, boats deployed", "Flooding"),
    ("Underpass completely submerged in flood waters, avoid transit route", "Flooding"),

    # Heatwave
    ("Severe heatwave conditions with temperature crossing 47.8°C in Churu", "Heatwave"),
    ("Scorching heat in Delhi, loo winds blowing furiously in afternoon", "Heatwave"),
    ("Garmi se bura haal, extreme temperature of 45 degrees recorded in Nagpur", "Heatwave"),
    ("Red alert for heatwave issued by IMD for Western Rajasthan and Haryana", "Heatwave"),
    ("Deadly heat wave across Telangana, avoid going outdoors during peak afternoon", "Heatwave"),
    ("Sunstroke warnings as mercury surges to 46 degrees in Prayagraj", "Heatwave"),
    ("Unbearable sultry heat and blazing sun in Ahmedabad today", "Heatwave"),

    # Fog/Smog
    ("Zero visibility at IGI Airport Delhi due to dense fog, flight delays", "Fog/Smog"),
    ("Thick smog envelope over NCR, AQI hits hazardous 450 mark, vision impaired", "Fog/Smog"),
    ("Severe kohra on Yamuna Expressway, vehicles crawling at 10 kmph", "Fog/Smog"),
    ("Dense radiation fog reported across Punjab and Haryana plains", "Fog/Smog"),
    ("Morning smog creating eye irritation and low visibility in Anand Vihar", "Fog/Smog"),
    ("Winter fog blanket covers Lucknow, trains running behind schedule", "Fog/Smog"),
    ("Thick haze and morning mist reducing visibility below 50 meters", "Fog/Smog"),

    # Dust Storm
    ("Massive dust storm hits Jaipur, sky turned orange and dark at 4 PM", "Dust Storm"),
    ("Tez aandhi and dust storm blinding drivers on Bikaner highway", "Dust Storm"),
    ("Severe dust storm with high-velocity dust gale engulfs Delhi NCR", "Dust Storm"),
    ("Sandstorm approaching Jaisalmer, visibility drastically reduced by dust", "Dust Storm"),
    ("Aandhi toofan with thick dust clouds blowing over Rohtak", "Dust Storm"),
    ("Dust whirlwind and blinding sand squall sweeping across western Haryana", "Dust Storm"),

    # Strong Winds
    ("Gale force winds uprooting trees and electric poles on Marine Drive", "Strong Winds"),
    ("High wind gusts of 75 km/h blowing tin roofs away in coastal Alibaug", "Strong Winds"),
    ("Tez hawayen chal rahi hain, branches falling on parked cars", "Strong Winds"),
    ("Squall with sudden wind gusts recorded at Safdarjung observatory", "Strong Winds"),
    ("Violent gusty winds shaking windows and signboards in high rises", "Strong Winds"),
    ("Severe wind storm damaging billboards along the highway", "Strong Winds"),

    # Hailstorm
    ("Giant hailstones raining down in Shimla and Solan, windshields cracked", "Hailstorm"),
    ("Oley gir rahe hain yahan par, golf-ball sized hail damaging crops in Nashik", "Hailstorm"),
    ("Hailstorm lashes parts of Shillong, ground turns white with hailstones", "Hailstorm"),
    ("Severe hailstorm damages standing wheat crops in Punjab border belt", "Hailstorm"),
    ("Intense hail precipitation recorded with hailstones piling on roads", "Hailstorm"),
    ("Sudden hail shower pounding roofs and vehicles in Dehradun", "Hailstorm"),

    # Cyclone
    ("Cyclone Michaung making landfall near Bapatla with wind speeds of 110 kmph", "Cyclone"),
    ("Deep depression over Bay of Bengal intensifies into Severe Cyclonic Storm", "Cyclone"),
    ("Chakravati toofan coastal warning: fishermen advised not to venture into sea", "Cyclone"),
    ("Cyclone Biparjoy approaching Saurashtra coast, mass evacuation underway", "Cyclone"),
    ("Super cyclone alert issued for Odisha and West Bengal coastal districts", "Cyclone"),
    ("Cyclonic storm eye passing over Puri coast with heavy gale and surge", "Cyclone"),

    # Snowfall
    ("Fresh snowfall blankets Gulmarg and Pahalgam in pristine white", "Snowfall"),
    ("Heavy snow accumulation blocking Mughal road and Atal Tunnel Manali", "Snowfall"),
    ("Baraf pad rahi hai yahan Shimla Mall Road pe, tourists enjoying snowfall", "Snowfall"),
    ("Snow blizzard and sub-zero temperatures recorded across Ladakh and Spiti", "Snowfall"),
    ("Moderate snowfall underway at Badrinath and Kedarnath shrines", "Snowfall"),
    ("First seasonal snowfall recorded at Rohtang Pass, roads closed", "Snowfall")
]

# Rule-based meteorological keyword dictionaries for high-precision validation
KEYWORD_RULES = {
    "Flooding": [r"\bflood\b", r"\bflooded\b", r"\bflooding\b", r"\bwaterlogg\w*", r"\bunderpass\b", r"\bsubway\b", r"\bsubmerged\b", r"\binundat\w*", r"\bpani bhar\b", r"\bjala bharao\b", r"\bunderwater\b"],
    "Hailstorm": [r"\bhail\b", r"\bhailstorm\b", r"\bhailstone\w*", r"\boley?\b", r"\bola gir\b"],
    "Snowfall": [r"\bsnow\b", r"\bsnowfall\b", r"\bblizzard\b", r"\bbaraf\b", r"\bbarf\b", r"\bsnowing\b", r"\bavalanche\b"],
    "Cyclone": [r"\bcyclone\b", r"\bcyclonic\b", r"\blandfall\b", r"\bchakravat\b", r"\bdeep depression\b", r"\btyphoon\b", r"\bhurricane\b"],
    "Dust Storm": [r"\bdust storm\b", r"\bsandstorm\b", r"\baandhi\b", r"\bandhi\b", r"\bdust cloud\b"],
    "Fog/Smog": [r"\bfog\b", r"\bsmog\b", r"\bkohra\b", r"\bvisibility\b", r"\bhaze\b", r"\baqi\b", r"\bmist\b"],
    "Heatwave": [r"\bheatwave\b", r"\bheat wave\b", r"\bloo\b", r"\bscorching\b", r"\bgarmi\b", r"\bsunstroke\b", r"\b4[5-9]\s*°?c\b", r"\b5[0-2]\s*°?c\b"],
    "Thunderstorm": [r"\bthunder\b", r"\blightning\b", r"\bt-storm\b", r"\bbijli\b", r"\bthunderstorm\b", r"\bcloudburst\b", r"\bbadal phat\b"],
    "Strong Winds": [r"\bgale\b", r"\bsquall\b", r"\bgusts?\b", r"\bstrong winds?\b", r"\bhigh winds?\b", r"\btez hawa\b"],
    "Rainfall": [r"\brain\b", r"\brainfall\b", r"\bdownpour\b", r"\bshower\b", r"\bshowers\b", r"\bdrizzle\b", r"\bbaarish\b", r"\bprecipitation\b", r"\bmonsoon\b"]
}

class WeatherCategorizer:
    """Hybrid ML + Rule-based Auto-Categorizer."""

    def __init__(self):
        self.categories = config.WEATHER_CATEGORIES
        self.pipeline = None
        self._train_model()

    def _train_model(self):
        texts = [item[0] for item in TRAINING_DATA]
        labels = [item[1] for item in TRAINING_DATA]

        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), min_df=1, lowercase=True)),
            ('clf', MultinomialNB(alpha=0.1))
        ])
        self.pipeline.fit(texts, labels)

    def predict(self, text):
        """
        Classifies weather report text.
        Returns:
            dict: {
                'category': str,
                'confidence': float,
                'method': 'ml_hybrid',
                'scores': dict
            }
        """
        if not text or not text.strip():
            return {"category": "Rainfall", "confidence": 0.5, "method": "default", "scores": {}}

        clean_text = text.lower()

        # Step 1: Check high-priority rule patterns
        rule_matches = {}
        for cat, patterns in KEYWORD_RULES.items():
            for pat in patterns:
                if re.search(pat, clean_text, re.IGNORECASE):
                    rule_matches[cat] = rule_matches.get(cat, 0) + 1

        # Step 2: ML Pipeline Probabilities
        proba = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        ml_scores = {classes[i]: float(proba[i]) for i in range(len(classes))}

        # Step 3: Hybrid Blending
        hybrid_scores = {}
        for cat in self.categories:
            base_score = ml_scores.get(cat, 0.0)
            rule_bonus = rule_matches.get(cat, 0) * 0.45
            hybrid_scores[cat] = base_score + rule_bonus

        # Normalize scores to 0-1
        total = sum(hybrid_scores.values()) or 1.0
        normalized_scores = {k: round(v / total, 3) for k, v in hybrid_scores.items()}

        best_category = max(normalized_scores, key=normalized_scores.get)
        confidence = normalized_scores[best_category]

        return {
            "category": best_category,
            "confidence": min(round(confidence, 2), 0.99),
            "method": "hybrid_nlp_rules",
            "scores": normalized_scores
        }

# Global singleton
categorizer = WeatherCategorizer()
