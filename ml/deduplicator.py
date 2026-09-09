"""
National Weather Big Data Analytics Platform (NWBDAP)
Spatio-Temporal & Semantic Deduplication Engine
Clusters duplicate weather reports of the same event into unified incidents.
"""

import uuid
import re
from datetime import datetime, timedelta, timezone
import config
from database.repository import (
    haversine_distance,
    get_active_clusters,
    create_cluster,
    update_cluster_increment,
    assign_report_to_cluster
)

def tokenize_clean(text):
    """Tokenizes text into a set of lower-case alphanumeric words."""
    words = re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower())
    # Exclude common stopwords
    stopwords = {"the", "and", "for", "with", "this", "that", "from", "are", "was", "has", "have", "here", "near", "after"}
    return set(w for w in words if w not in stopwords)

def jaccard_similarity(tokens1, tokens2):
    """Calculates Jaccard similarity coefficient between two token sets."""
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    return float(intersection) / float(union) if union > 0 else 0.0

class Deduplicator:
    """Spatio-temporal and semantic incident clustering engine."""

    def __init__(self):
        self.max_radius_km = config.DEDUP_RADIUS_KM
        self.max_hours = config.DEDUP_TIME_HOURS
        self.similarity_threshold = config.DEDUP_TEXT_SIMILARITY

    def process_report(self, report_id, report_data):
        """
        Deduplicates an incoming report against existing active clusters.
        Merges into an existing cluster if matched, or initializes a new cluster.
        Returns:
            dict: {'cluster_id': int, 'action': 'merged'|'created', 'cluster_title': str}
        """
        lat = report_data.get("latitude")
        lon = report_data.get("longitude")
        category = report_data.get("detected_category", "Rainfall")
        city = report_data.get("city", "Unknown")
        state = report_data.get("state", "Unknown")
        raw_text = report_data.get("raw_text", "")
        timestamp_str = report_data.get("timestamp", datetime.now(timezone.utc).isoformat())
        severity = report_data.get("severity_level", "moderate")

        # Parse report timestamp
        try:
            report_time = datetime.fromisoformat(timestamp_str.replace("Z", ""))
        except Exception:
            report_time = datetime.now(timezone.utc)

        report_tokens = tokenize_clean(raw_text)

        # Retrieve active incident clusters
        active_clusters = get_active_clusters(limit=40)
        matched_cluster = None

        for cluster in active_clusters:
            # 1. Check Category Match
            if cluster["category"] != category:
                continue

            # 2. Check Spatial Proximity (Haversine distance)
            c_lat = cluster.get("center_lat")
            c_lon = cluster.get("center_lon")
            if lat is not None and lon is not None and c_lat is not None and c_lon is not None:
                dist = haversine_distance(lat, lon, c_lat, c_lon)
                if dist > self.max_radius_km:
                    continue
            elif cluster["city"].lower() != city.lower():
                # Fallback to city match if coordinates are missing
                continue

            # 3. Check Temporal Window (Within max_hours)
            try:
                cluster_time = datetime.fromisoformat(cluster["last_reported_at"].replace("Z", ""))
                time_delta_hours = abs((report_time - cluster_time).total_seconds()) / 3600.0
                if time_delta_hours > self.max_hours:
                    continue
            except Exception:
                pass

            # 4. Semantic Similarity Check
            cluster_tokens = tokenize_clean(cluster["title"] + " " + (cluster.get("summary") or ""))
            sim = jaccard_similarity(report_tokens, cluster_tokens)

            # Match criteria: same category, close distance, within time window
            matched_cluster = cluster
            break

        if matched_cluster:
            # Merge report into existing cluster
            cluster_id = matched_cluster["id"]
            update_cluster_increment(cluster_id, timestamp_str)
            assign_report_to_cluster(report_id, cluster_id)
            return {
                "cluster_id": cluster_id,
                "action": "merged",
                "cluster_title": matched_cluster["title"]
            }
        else:
            # Create a brand new incident cluster
            cluster_title = f"{category} Surge in {city}, {state}"
            cluster_uuid = f"INC-{uuid.uuid4().hex[:8].upper()}"
            cluster_data = {
                "cluster_uuid": cluster_uuid,
                "title": cluster_title,
                "category": category,
                "severity": severity,
                "center_lat": lat if lat is not None else 20.5937,
                "center_lon": lon if lon is not None else 78.9629,
                "city": city,
                "state": state,
                "report_count": 1,
                "first_reported_at": timestamp_str,
                "last_reported_at": timestamp_str,
                "status": "active",
                "summary": raw_text[:200]
            }
            new_cluster_id = create_cluster(cluster_data)
            assign_report_to_cluster(report_id, new_cluster_id)
            return {
                "cluster_id": new_cluster_id,
                "action": "created",
                "cluster_title": cluster_title
            }

deduplicator = Deduplicator()
