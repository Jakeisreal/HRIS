from io import BytesIO
import unittest

from openpyxl import Workbook

from backend.parsing import parse_candidate_workbook


class CandidateWorkbookParsingTest(unittest.TestCase):
    def test_parse_valid_candidate_rows(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["사번", "이름", "부서", "직위", "주재원 적합도"])
        sheet.append(["E24017", "김도현", "품질관리팀", "과장", 92])
        sheet.append(["E21884", "박준호", "영업팀", "차장", 95])

        result = parse_candidate_workbook(_to_bytes(workbook))

        self.assertEqual(len(result.candidates), 2)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.candidates[0].data["employee_id"], "E24017")
        self.assertEqual(result.candidates[0].data["expat_fit"], 92)

    def test_missing_required_values_are_reported(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["사번", "이름"])
        sheet.append(["E24017", None])

        result = parse_candidate_workbook(_to_bytes(workbook))

        self.assertEqual(result.candidates, [])
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].row_number, 2)


def _to_bytes(workbook):
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


if __name__ == "__main__":
    unittest.main()
