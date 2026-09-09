"""
Integration and API endpoint tests for NWBDAP
"""

import unittest
import json
from app import app
from database.db import init_db

class TestAPI(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        init_db()

    def test_pages_render(self):
        """Verify public web pages return HTTP 200 OK."""
        pages = ["/", "/report", "/analytics", "/login"]
        for p in pages:
            res = self.app.get(p)
            self.assertEqual(res.status_code, 200, f"Page {p} failed to render.")

    def test_admin_redirects_unauthenticated(self):
        """Verify /admin redirects to /login when unauthenticated."""
        res = self.app.get("/admin", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers.get("Location", ""))

    def test_login_flow(self):
        """Verify user login, session access, and logout."""
        # Test valid login with seeded admin credentials
        login_res = self.app.post("/login", data={
            "username": "admin",
            "password": "Admin@123"
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)

        # Verify /api/auth/me returns authenticated admin
        me_res = self.app.get("/api/auth/me")
        self.assertEqual(me_res.status_code, 200)
        me_data = json.loads(me_res.data)
        self.assertTrue(me_data.get("authenticated"))
        self.assertEqual(me_data.get("user", {}).get("username"), "admin")

        # Verify admin can now access /admin
        admin_res = self.app.get("/admin")
        self.assertEqual(admin_res.status_code, 200)

        # Test logout
        logout_res = self.app.get("/logout", follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)

        # Verify no longer authenticated
        me_after_logout = self.app.get("/api/auth/me")
        me_after_data = json.loads(me_after_logout.data)
        self.assertFalse(me_after_data.get("authenticated"))

    def test_officer_and_citizen_login(self):
        """Verify seeded meteorologist officer and citizen accounts can authenticate."""
        # Test officer login
        off_res = self.app.post("/login", data={
            "username": "officer",
            "password": "Officer@123"
        }, follow_redirects=True)
        self.assertEqual(off_res.status_code, 200)

        me_res = self.app.get("/api/auth/me")
        me_data = json.loads(me_res.data)
        self.assertTrue(me_data.get("authenticated"))
        self.assertEqual(me_data.get("user", {}).get("role"), "meteorologist")
        self.app.get("/logout")

        # Test citizen login
        cit_res = self.app.post("/login", data={
            "username": "citizen",
            "password": "Citizen@123"
        }, follow_redirects=True)
        self.assertEqual(cit_res.status_code, 200)

        me_res = self.app.get("/api/auth/me")
        me_data = json.loads(me_res.data)
        self.assertTrue(me_data.get("authenticated"))
        self.assertEqual(me_data.get("user", {}).get("role"), "citizen")
        self.app.get("/logout")

    def test_api_auth_login(self):
        """Verify /api/auth/login endpoint for JSON/AJAX clients."""
        res = self.app.post("/api/auth/login", json={
            "username": "admin",
            "password": "Admin@123"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("user", {}).get("username"), "admin")
        self.app.get("/logout")

    def test_citizen_registration(self):
        """Verify citizen registration and auto-login."""
        import uuid
        uid = uuid.uuid4().hex[:6]
        reg_res = self.app.post("/register", data={
            "username": f"user_{uid}",
            "email": f"citizen_{uid}@imd.gov.in",
            "full_name": "Citizen Reporter",
            "password": "SecurePassword123",
            "confirm_password": "SecurePassword123"
        }, follow_redirects=True)
        self.assertEqual(reg_res.status_code, 200)

        me_res = self.app.get("/api/auth/me")
        me_data = json.loads(me_res.data)
        self.assertTrue(me_data.get("authenticated"))
        self.assertEqual(me_data.get("user", {}).get("role"), "citizen")

    def test_api_reports(self):
        """Verify /api/reports endpoint returns valid JSON array."""
        res = self.app.get("/api/reports?limit=10")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("reports", data)
        self.assertIn("count", data)

    def test_api_clusters(self):
        """Verify /api/clusters returns active deduplicated clusters."""
        res = self.app.get("/api/clusters")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("clusters", data)

    def test_api_analytics(self):
        """Verify /api/analytics returns aggregated statistics."""
        res = self.app.get("/api/analytics?days=7")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("totals", data)
        self.assertIn("categories", data)
        self.assertIn("state_hotspots", data)

    def test_citizen_submission(self):
        """Verify citizen intake endpoint enqueues submissions."""
        payload = {
            "description": "Continuous heavy downpour in Bandra West, water logging observed on Linking Road.",
            "latitude": "19.0596",
            "longitude": "72.8295",
            "city": "Mumbai",
            "state": "Maharashtra",
            "severity": "moderate",
            "citizen_name": "Test Citizen",
            "citizen_contact": "+91 9999988888"
        }
        res = self.app.post(
            "/api/report/submit",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        self.assertIn("report_uuid", data)

    def test_csv_export(self):
        """Verify CSV export endpoint returns valid CSV format."""
        res = self.app.get("/api/export/csv")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "text/csv")
        self.assertIn(b"Report ID", res.data)

    def test_api_weather_states(self):
        """Verify /api/weather/states returns all 36 Indian states/UTs."""
        res = self.app.get("/api/weather/states")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        self.assertIn("states", data)
        self.assertIn("districts_by_state", data)
        self.assertIn("Maharashtra", data["states"])
        self.assertIn("Delhi", data["states"])
        self.assertIn("Tamil Nadu", data["states"])
        self.assertIn("Pune", data["districts_by_state"]["Maharashtra"])

    def test_api_live_weather_district(self):
        """Verify /api/weather/live returns live telemetry and 12-hour micro-forecast."""
        res = self.app.get("/api/weather/live?state=Maharashtra&district=Pune")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        weather = data.get("data", {})
        self.assertEqual(weather.get("city"), "Pune")
        self.assertEqual(weather.get("state"), "Maharashtra")
        self.assertIn("temperature", weather)
        self.assertIn("humidity", weather)
        self.assertIn("hourly", weather)
        self.assertGreaterEqual(len(weather["hourly"]), 12)

    def test_api_weather_state_summary(self):
        """Verify /api/weather/state-summary returns all districts in state."""
        res = self.app.get("/api/weather/state-summary?state=Goa")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("state"), "Goa")
        districts = data.get("districts", [])
        self.assertGreaterEqual(len(districts), 3)

    def test_api_sync_live_imd(self):
        """Verify /api/social/sync-live-imd ingests real-world #IMD reports."""
        res = self.app.post("/api/social/sync-live-imd?limit=3")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        self.assertIn("count", data)
        self.assertIn("posts", data)

    def test_api_ingest_custom_social_post(self):
        """Verify /api/social/ingest enriches custom weather tweet with AI pipeline."""
        payload = {
            "text": "Intense thunderstorm and waterlogging in Lucknow Charbagh area, roads inundated. #IMD #WeatherAlert",
            "author_handle": "@lucknow_spotter",
            "platform": "twitter"
        }
        res = self.app.post(
            "/api/social/ingest",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        report = data.get("report", {})
        self.assertEqual(report.get("state"), "Uttar Pradesh")
        self.assertEqual(report.get("city"), "Lucknow")
        self.assertIn("detected_category", report)
        self.assertIn("authenticity_score", report)
        self.assertIn("id", report)

if __name__ == "__main__":
    unittest.main()
