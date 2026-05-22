from io import BytesIO
import os
import tempfile
import unittest

from openpyxl import Workbook

from backend.app import create_app


class CandidateUploadChangeTest(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(fd)
        os.unlink(self.db_path)
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        self.token = login(self.client, "E24017", "password")

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_upload_reports_new_changed_and_unchanged_rows(self):
        first = workbook_bytes(
            ["사번", "이름", "부서", "직군", "직위", "2026 평가", "어학종류", "어학점수숫자"],
            [
                ["E1", "김도현", "품질관리팀", "품질", "과장", "A", "TOEIC", 890],
                ["E2", "박준호", "영업팀", "영업", "차장", "A", "TOEIC", 930],
            ],
        )
        response = self.client.post(
            "/api/candidates/upload",
            data={"file": (first, "first.xlsx")},
            content_type="multipart/form-data",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["newRows"], 2)
        self.assertEqual(response.json["changedRows"], 0)
        self.assertEqual(response.json["dup"], 0)

        second = workbook_bytes(
            ["사번", "이름", "부서", "직군", "직위", "2026 평가", "어학종류", "어학점수숫자"],
            [
                ["E1", "김도현", "품질관리팀", "품질", "과장", "A", "TOEIC", 890],
                ["E2", "박준호", "해외영업팀", "영업", "차장", "A", "TOEIC", 930],
                ["E3", "정하늘", "인사팀", "인사", "과장", "B+", "OPIc", 880],
            ],
        )
        response = self.client.post(
            "/api/candidates/upload",
            data={"file": (second, "second.xlsx")},
            content_type="multipart/form-data",
            headers={"Authorization": f"Bearer {self.token}"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["newRows"], 1)
        self.assertEqual(response.json["changedRows"], 1)
        self.assertEqual(response.json["dup"], 1)
        changed = [item for item in response.json["change_details"] if item["change_type"] == "changed"]
        self.assertEqual(changed[0]["employee_id"], "E2")
        self.assertEqual(changed[0]["fields"][0]["field_name"], "dept")

        candidates = self.client.get("/api/candidates", headers={"Authorization": f"Bearer {self.token}"}).json["items"]
        e2 = next(candidate for candidate in candidates if candidate["employee_id"] == "E2")
        self.assertEqual(e2["dept"], "해외영업팀")
        self.assertEqual(e2["job_family"], "영업")
        self.assertEqual(e2["language_type"], "TOEIC")


def workbook_bytes(headers, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def login(client, employee_id, password):
    response = client.post(
        "/api/auth/login",
        json={"employee_id": employee_id, "password": password},
    )
    assert response.status_code == 200
    return response.json["token"]


if __name__ == "__main__":
    unittest.main()
