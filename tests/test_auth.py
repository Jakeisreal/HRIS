import os
import tempfile
import unittest

from openpyxl import Workbook
from io import BytesIO

from backend.app import create_app


class AuthApiTest(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(fd)
        os.unlink(self.db_path)
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_login_returns_token_and_user_role(self):
        response = self.client.post(
            "/api/auth/login",
            json={"employee_id": "E24017", "password": "password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["token"])
        self.assertEqual(response.json["user"]["role"], "hr")

    def test_me_requires_valid_token(self):
        unauthenticated = self.client.get("/api/auth/me")
        self.assertEqual(unauthenticated.status_code, 401)

        token = self._login("E24017")
        authenticated = self.client.get("/api/auth/me", headers=auth_header(token))
        self.assertEqual(authenticated.status_code, 200)
        self.assertEqual(authenticated.json["user"]["employee_id"], "E24017")

    def test_upload_requires_hr_role(self):
        no_token = self.client.post(
            "/api/candidates/upload",
            data={"file": (workbook_bytes(), "candidate.xlsx")},
            content_type="multipart/form-data",
        )
        self.assertEqual(no_token.status_code, 401)

        viewer_token = self._login("E90001")
        viewer = self.client.post(
            "/api/candidates/upload",
            data={"file": (workbook_bytes(), "candidate.xlsx")},
            content_type="multipart/form-data",
            headers=auth_header(viewer_token),
        )
        self.assertEqual(viewer.status_code, 403)

    def _login(self, employee_id):
        response = self.client.post(
            "/api/auth/login",
            json={"employee_id": employee_id, "password": "password"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json["token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def workbook_bytes():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["사번", "이름"])
    sheet.append(["E1", "김도현"])
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


if __name__ == "__main__":
    unittest.main()
