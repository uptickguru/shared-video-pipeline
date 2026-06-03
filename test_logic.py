import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import os

# Mock Redis before importing app
with patch('redis.from_url') as mock_redis:
    from main import app
    from database import init_db, SessionLocal, engine
    from models import Base, JobRecord

class TestPipelineLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use a temporary SQLite DB for testing
        if os.path.exists("test_pipeline.db"):
            os.remove("test_pipeline.db")
        init_db()
        cls.client = TestClient(app)

    def setUp(self):
        # Clear DB before each test
        db = SessionLocal()
        db.query(JobRecord).delete()
        db.commit()
        db.close()

    @patch('queue_manager.high_priority_queue')
    @patch('queue_manager.standard_queue')
    @patch('queue_manager.video_vast_queue')
    def test_job_submission_logic(self, mock_vast_q, mock_std_q, mock_high_q):
        # Test Case 1: Standard Video Job (should go to vast_video queue)
        payload = {
            "job_type": "video",
            "provider": "wan",
            "engine": "test-engine",
            "prompt": "test prompt",
            "priority": "normal",
            "emergency": False,
            "direct_to_vast": False
        }
        response = self.client.post("/jobs/", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "queued:held_in_vast_queue")
        self.assertTrue(mock_vast_q.enqueue.called)

        # Test Case 2: Emergency Video Job (should go to high priority queue)
        payload["emergency"] = True
        response = self.client.post("/jobs/", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "queued:enqueued_high")
        self.assertTrue(mock_high_q.enqueue.called)

        # Test Case 3: Direct-to-Vast Video Job (should go to standard queue)
        payload["emergency"] = False
        payload["direct_to_vast"] = True
        response = self.client.post("/jobs/", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "queued:enqueued_standard")
        self.assertTrue(mock_std_q.enqueue.called)

    def test_stats_endpoint(self):
        with patch('queue_manager.get_queue_stats') as mock_stats:
            mock_stats.return_value = {"high": 1, "standard": 2, "vast_video": 3}
            response = self.client.get("/stats")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"high": 1, "standard": 2, "vast_video": 3})

if __name__ == "__main__":
    unittest.main()
