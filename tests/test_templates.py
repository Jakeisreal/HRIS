import os
import tempfile
import unittest

from backend.app import create_app


class TemplateApiTest(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(fd)
        os.unlink(self.db_path)
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        self.hr_token = self._login("E24017")
        self.viewer_token = self._login("E90001")

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_default_templates_are_visible_to_viewer(self):
        response = self.client.get("/api/templates", headers=auth_header(self.viewer_token))

        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.json["items"]}
        self.assertIn("expat-basic", ids)
        self.assertIn("leader-basic", ids)

    def test_hr_can_create_private_template_and_share_it(self):
        created = self.client.post(
            "/api/templates",
            json={
                "name": "품질 주재원 후보",
                "purpose": "주재원",
                "scope": "나만 보기",
                "filter_state": {"purpose": "주재원", "minLanguage": 820, "overseasOnly": True},
                "count": 12,
            },
            headers=auth_header(self.hr_token),
        )
        self.assertEqual(created.status_code, 201)
        template_id = created.json["item"]["id"]

        viewer_before = self.client.get("/api/templates", headers=auth_header(self.viewer_token))
        self.assertNotIn(template_id, {item["id"] for item in viewer_before.json["items"]})

        shared = self.client.post(
            f"/api/templates/{template_id}/share",
            headers=auth_header(self.hr_token),
        )
        self.assertEqual(shared.status_code, 200)
        self.assertEqual(shared.json["item"]["scope"], "인사팀 공유")

        viewer_after = self.client.get("/api/templates", headers=auth_header(self.viewer_token))
        self.assertIn(template_id, {item["id"] for item in viewer_after.json["items"]})

    def test_viewer_cannot_create_template(self):
        response = self.client.post(
            "/api/templates",
            json={"name": "viewer template"},
            headers=auth_header(self.viewer_token),
        )
        self.assertEqual(response.status_code, 403)

    def test_hr_can_unshare_and_delete_template(self):
        created = self.client.post(
            "/api/templates",
            json={
                "name": "삭제 테스트 템플릿",
                "purpose": "검증",
                "scope": "나만 보기",
                "filter_state": {"purpose": "검증", "minLanguage": 700},
                "count": 5,
            },
            headers=auth_header(self.hr_token),
        )
        self.assertEqual(created.status_code, 201)
        template_id = created.json["item"]["id"]

        share = self.client.post(
            f"/api/templates/{template_id}/share",
            headers=auth_header(self.hr_token),
        )
        self.assertEqual(share.status_code, 200)
        self.assertEqual(share.json["item"]["scope"], "인사팀 공유")

        unshare = self.client.post(
            f"/api/templates/{template_id}/unshare",
            headers=auth_header(self.hr_token),
        )
        self.assertEqual(unshare.status_code, 200)
        self.assertEqual(unshare.json["item"]["scope"], "나만 보기")

        delete = self.client.delete(
            f"/api/templates/{template_id}",
            headers=auth_header(self.hr_token),
        )
        self.assertEqual(delete.status_code, 200)
        self.assertTrue(delete.json["ok"])

        remaining = self.client.get("/api/templates", headers=auth_header(self.hr_token))
        self.assertNotIn(template_id, {item["id"] for item in remaining.json["items"]})

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
