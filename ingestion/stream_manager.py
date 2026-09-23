"""
National Weather Big Data Analytics Platform (NWBDAP)
Streaming Queue Manager & Worker Pipeline
Asynchronously processes heterogeneous weather data streams through the AI/ML layer.
"""

import queue
import threading
import time
import uuid
from datetime import datetime, timezone
import config
from database.repository import insert_report, increment_source_ingested
from ml.categorizer import categorizer
from ml.source_verifier import source_verifier
from ml.fake_detector import fake_detector
from ml.deduplicator import deduplicator

class StreamPipelineManager:
    """Threaded Event Streaming Pipeline."""

    def __init__(self, num_workers=config.INGESTION_WORKERS):
        self.queue = queue.Queue(maxsize=config.QUEUE_MAXSIZE)
        self.num_workers = num_workers
        self.workers = []
        self.running = False

        # Telemetry metrics
        self.total_received = 0
        self.total_processed = 0
        self.total_errors = 0
        self.recent_latencies = []
        self.start_time = datetime.now(timezone.utc)
        self.lock = threading.Lock()

    def start(self):
        """Starts background streaming worker threads."""
        if self.running:
            return

        self.running = True
        for i in range(self.num_workers):
            t = threading.Thread(target=self._worker_loop, name=f"StreamWorker-{i+1}", daemon=True)
            t.start()
            self.workers.append(t)
        print(f"[STREAM] Pipeline started with {self.num_workers} background processing workers.")

    def stop(self):
        """Stops the pipeline gracefully."""
        self.running = False

    def push_raw_report(self, report_dict):
        """
        Pushes an incoming raw report from any connector into the ingestion queue.
        """
        with self.lock:
            self.total_received += 1

        if not report_dict.get("report_uuid"):
            report_dict["report_uuid"] = f"RPT-{uuid.uuid4().hex[:10].upper()}"

        report_dict["_queued_at"] = time.time()

        try:
            self.queue.put(report_dict, block=False)
            return True
        except queue.Full:
            print("[STREAM WARN] Ingestion queue full! Dropping item or applying backpressure.")
            with self.lock:
                self.total_errors += 1
            return False

    def _worker_loop(self):
        """Worker thread loop executing end-to-end ML enrichment and database insertion."""
        while self.running:
            try:
                raw_report = self.queue.get(timeout=1.0)
            except queue.Empty:
                continue

            t_start = time.time()
            try:
                # 1. Source Credibility Verification
                author = raw_report.get("author_handle", "anonymous")
                source_type = raw_report.get("source_type", "social_media")
                has_contact = bool(raw_report.get("citizen_contact"))

                src_meta = source_verifier.verify_source(
                    author, source_type=source_type, has_verified_contact=has_contact
                )
                raw_report["author_credibility_tier"] = src_meta["tier"]
                raw_report["source_credibility_score"] = src_meta["score"]

                # 2. AI Auto-Categorization (or preserve verified ground-truth sensor category)
                if not raw_report.get("detected_category") or source_type != "open_meteo":
                    text = raw_report.get("raw_text", "")
                    cat_result = categorizer.predict(text)
                    raw_report["detected_category"] = cat_result["category"]
                    raw_report["category_confidence"] = cat_result["confidence"]
                elif not raw_report.get("category_confidence"):
                    raw_report["category_confidence"] = 0.98

                # 3. AI Fake / Misleading Report Detection
                fake_result = fake_detector.evaluate(raw_report, src_meta["score"])
                raw_report["authenticity_score"] = fake_result["authenticity_score"]
                raw_report["is_fake"] = fake_result["is_fake"]
                raw_report["fake_reasons"] = fake_result["reasons"]

                # 4. Determine Initial Verification Status
                if raw_report["is_fake"]:
                    raw_report["verification_status"] = "flagged_fake"
                elif src_meta["is_official"]:
                    raw_report["verification_status"] = "verified"
                elif source_type == "open_meteo":
                    raw_report["verification_status"] = "verified"
                else:
                    raw_report["verification_status"] = "unverified"

                # 5. Commit Enriched Report to Database
                report_id = insert_report(raw_report)

                # 6. Spatio-Temporal Deduplication & Incident Clustering
                # Only cluster non-fake reports to prevent polluting real-world ground truth
                if not raw_report["is_fake"] and report_id:
                    dedup_res = deduplicator.process_report(report_id, raw_report)
                    raw_report["cluster_id"] = dedup_res.get("cluster_id")

                # Track source volume
                source_id = raw_report.get("source_id", "social_stream")
                increment_source_ingested(source_id, 1)

                # Latency calculation
                latency_ms = (time.time() - raw_report.get("_queued_at", t_start)) * 1000.0
                with self.lock:
                    self.total_processed += 1
                    self.recent_latencies.append(latency_ms)
                    if len(self.recent_latencies) > 200:
                        self.recent_latencies.pop(0)

            except Exception as e:
                print(f"[STREAM ERROR] Error processing report: {e}")
                with self.lock:
                    self.total_errors += 1
            finally:
                self.queue.task_done()

    def process_report_now(self, raw_report):
        """Processes a single report synchronously through the ML enrichment pipeline."""
        author = raw_report.get("author_handle", "anonymous")
        source_type = raw_report.get("source_type", "social_media")
        has_contact = bool(raw_report.get("citizen_contact"))

        src_meta = source_verifier.verify_source(
            author, source_type=source_type, has_verified_contact=has_contact
        )
        raw_report["author_credibility_tier"] = src_meta["tier"]
        raw_report["source_credibility_score"] = src_meta["score"]

        # 2. AI Auto-Categorization (or preserve verified ground-truth sensor category)
        if not raw_report.get("detected_category") or source_type != "open_meteo":
            text = raw_report.get("raw_text", "")
            cat_result = categorizer.predict(text)
            raw_report["detected_category"] = cat_result["category"]
            raw_report["category_confidence"] = cat_result["confidence"]
        elif not raw_report.get("category_confidence"):
            raw_report["category_confidence"] = 0.98

        fake_result = fake_detector.evaluate(raw_report, src_meta["score"])
        raw_report["authenticity_score"] = fake_result["authenticity_score"]
        raw_report["is_fake"] = fake_result["is_fake"]
        raw_report["fake_reasons"] = fake_result["reasons"]

        if raw_report["is_fake"]:
            raw_report["verification_status"] = "flagged_fake"
        elif src_meta["is_official"] or source_type == "open_meteo":
            raw_report["verification_status"] = "verified"
        else:
            raw_report["verification_status"] = "unverified"

        report_id = insert_report(raw_report)
        raw_report["id"] = report_id

        if not raw_report["is_fake"] and report_id:
            dedup_res = deduplicator.process_report(report_id, raw_report)
            raw_report["cluster_id"] = dedup_res.get("cluster_id")

        source_id = raw_report.get("source_id", "social_stream")
        increment_source_ingested(source_id, 1)

        with self.lock:
            self.total_processed += 1

        return raw_report

    def get_telemetry(self):
        """Returns real-time pipeline performance metrics."""
        with self.lock:
            avg_lat = sum(self.recent_latencies) / len(self.recent_latencies) if self.recent_latencies else 12.5
            uptime_seconds = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            throughput_per_min = (self.total_processed / (uptime_seconds / 60.0)) if uptime_seconds > 0 else 0.0

            return {
                "total_received": self.total_received,
                "total_processed": self.total_processed,
                "total_errors": self.total_errors,
                "queue_depth": self.queue.qsize(),
                "average_latency_ms": round(avg_lat, 2),
                "throughput_per_min": round(throughput_per_min, 1),
                "active_workers": len(self.workers),
                "pipeline_status": "ONLINE" if self.running else "STOPPED"
            }

stream_pipeline = StreamPipelineManager()
