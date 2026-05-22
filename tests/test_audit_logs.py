import os
import tempfile
import unittest

from backend.app import create_app


class AuditLogApiTest(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(fd)
        os.unlink(self.db_path)
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_login_and_candidate_list_events_are_recorded(self):
        token = self._login("E24017")
        self.client.get("/api/candidates", headers=auth_header(token))

        response = self.client.get("/api/audit-logs", headers=auth_header(token))
        response = self.client.get("/api/audit-logs", headers=auth_header(token))

        self.assertEqual(response.status_code, 200)
        actions = [item["action"] for item in response.json["items"]]
        self.assertIn("로그인", actions)
        self.assertIn("후보자 목록 조회", actions)
        self.assertIn("감사 로그 조회", actions)

    def test_viewer_cannot_read_audit_logs_and_block_is_recorded(self):
        viewer_token = self._login("E90001")
        blocked = self.client.get("/api/audit-logs", headers=auth_header(viewer_token))
        self.assertEqual(blocked.status_code, 403)

        hr_token = self._login("E24017")
        response = self.client.get("/api/audit-logs", headers=auth_header(hr_token))
        blocked_rows = [
            item for item in response.json["items"]
            if item["action"] == "감사 로그 조회" and item["result"] == "차단"
        ]
        self.assertTrue(blocked_rows)

    def _login(self, employee_id):
        response = self.client.post(
            "/api/auth/login",
            json={"employee_id": employee_id, "password": "password"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json["token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


if __name__ == "__main__":
    unittest.main()
