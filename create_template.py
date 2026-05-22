#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Excel 템플릿 생성 스크립트"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Create workbook
wb = Workbook()

# Sheet 1: 데이터 입력 용
ws_data = wb.active
ws_data.title = "후보자 데이터"

# Headers
headers = [
    "사번",           # A - Required
    "이름",           # B - Required
    "부서",           # C
    "직군",           # D
    "직위",           # E
    "등급",           # F
    "입사일",         # G
    "근무지",         # H
    "이메일",         # I
    "근속년수",       # J (tenure)
    "평가",           # K (performance)
    "2024 평가",      # L
    "2025 평가",      # M
    "2026 평가",      # N
    "리더십",         # O
    "어학",           # P
    "어학점수",       # Q
    "어학종류",       # R
    "해외경험",       # S
    "해외국가",       # T
    "해외개월수",     # U
    "해외유형",       # V
    "자격증",         # W
    "주재원적합도",   # X (1~100)
    "팀장적합도",     # Y (1~100)
    "후보목적",       # Z
    "사진URL",        # AA
    "발령내역",       # AB date|dept|position|note; ...
]

ws_data.append(headers)

# Style header
header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
header_font = Font(bold=True, color="FFFFFF", size=11)
header_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

for cell in ws_data[1]:
    cell.fill = header_fill
    cell.font = header_font
    cell.border = header_border
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

# Add sample data
sample_data = [
    ["E24017", "김도현", "품질관리팀", "생산/품질", "과장", "5", "2011-03-15", "본사", "kim.dohyun@company.com", 12.4, "A", "A", "A", "A", "A", "TOEIC", 890, "TOEIC", "중국 주재", "중국", 24, "장기 주재", "품질경영기사", 92, 87, "주재원;차기팀장", "", "2011-03|생산기술팀|사원|입사;2017-01|품질관리팀|대리|전보;2022-01|품질관리팀|과장|승진"],
    ["E21884", "박준호", "영업팀", "영업/마케팅", "차장", "5", "2009-06-10", "본사", "park.junho@company.com", 15.1, "A", "A", "A", "A", "A", "TOEIC", 930, "TOEIC", "인도 파견", "인도", 18, "해외 파견", "무역영어", 95, 91, "주재원;차기팀장", "", "2009-06|국내영업팀|사원|입사;2016-03|해외영업팀|과장|전보;2021-01|영업팀|차장|승진"],
    ["E22615", "윤지훈", "설계팀", "기술/설계", "과장", "4", "2014-07-20", "본사", "yoon.jihun@company.com", 9.4, "B+", "B+", "A", "A", "A", "TOEIC", 840, "TOEIC", "미국 주재", "미국", 30, "장기 주재", "기계설계기사", 86, 84, "주재원;차기팀장", "", "2014-07|설계팀|사원|입사;2019-01|선행설계팀|대리|전보;2023-01|설계팀|과장|승진"],
]

for row_data in sample_data:
    ws_data.append(row_data)

# Set column widths
column_widths = [12, 10, 12, 12, 10, 6, 12, 10, 24, 10, 6, 10, 10, 10, 6, 10, 8, 10, 12, 8, 10, 10, 12, 10, 10, 15, 26, 58]
for i, width in enumerate(column_widths, 1):
    ws_data.column_dimensions[get_column_letter(i)].width = width

# Sheet 2: 작성 지침
ws_guide = wb.create_sheet("작성 지침")

guide_content = [
    ["필수 입력 항목"],
    ["사번", "회사 직원 고유 번호 (예: E24017)"],
    ["이름", "직원 이름 (예: 김도현)"],
    ["", ""],
    ["주요 입력 항목"],
    ["부서", "팀/부서명 (예: 품질관리팀)"],
    ["직군", "직군명 (예: 생산/품질, 영업/마케팅, 기술/설계)"],
    ["직위", "직급 (예: 대리, 과장, 차장, 부장)"],
    ["등급", "임원등급 (예: 1~6급)"],
    ["입사일", "입사 날짜 (YYYY-MM-DD 형식, 예: 2011-03-15)"],
    ["근무지", "근무 지역 (예: 본사, 서울, 부산, 중국 법인)"],
    ["이메일", "회사 이메일 (예: kim.dohyun@company.com)"],
    ["", ""],
    ["경력 평가 항목"],
    ["근속년수", "입사 후 경과 년수 (소수점 1자리, 예: 12.4)"],
    ["평가", "최근 평가 등급 (A, B+, B, C, D)"],
    ["2024 평가", "2024년 평가 등급 (A, B+, B, C, D)"],
    ["2025 평가", "2025년 평가 등급 (A, B+, B, C, D)"],
    ["2026 평가", "2026년 평가 등급 (A, B+, B, C, D)"],
    ["리더십", "리더십 평가 (A, B+, B, C, D)"],
    ["", ""],
    ["어학 정보"],
    ["어학", "어학 시험 종류 (TOEIC, OPIc, IELTS, TEPS, 기타)"],
    ["어학점수", "어학 점수 (숫자만, 예: 890)"],
    ["어학종류", "어학 이름 (예: TOEIC, OPIc IH, IELTS 7.0)"],
    ["", ""],
    ["해외 경험"],
    ["해외경험", "해외 경험 유형 (예: 중국 주재, 인도 파견, 미국 출장)"],
    ["해외국가", "국가명 (예: 중국, 인도, 미국)"],
    ["해외개월수", "해외 경험 개월 수 (숫자만, 예: 24)"],
    ["해외유형", "해외 유형 (장기 주재, 해외 파견, 출장, 단기 파견)"],
    ["", ""],
    ["기타 정보"],
    ["자격증", "보유 자격증 (예: 품질경영기사, 무역영어)"],
    ["주재원적합도", "주재원 적합도 점수 (1~100, 예: 92)"],
    ["팀장적합도", "차기 팀장 적합도 점수 (1~100, 예: 87)"],
    ["후보목적", "후보 목적 (주재원, 차기팀장, 또는 둘 다 쌍반점으로 분리, 예: 주재원;차기팀장)"],
    ["사진URL", "후보자 사진 URL (선택, 예: https://example.com/photo.jpg)"],
    ["발령내역", "세미콜론으로 여러 건 입력. 각 건은 날짜|부서|직위|비고 형식 (예: 2022-01|품질관리팀|과장|승진)"],
]

for row in guide_content:
    ws_guide.append(row)

# Style guide sheet
for row in ws_guide.iter_rows():
    for cell in row:
        cell.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)

# Style section headers
for row in ws_guide.iter_rows(min_row=1, max_row=ws_guide.max_row):
    if row[0].value and row[1].value is None:
        row[0].font = Font(bold=True, size=12, color="FFFFFF")
        row[0].fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

ws_guide.column_dimensions['A'].width = 15
ws_guide.column_dimensions['B'].width = 60

# Save
wb.save('template_candidate_data.xlsx')
print("[OK] Excel 템플릿 생성 완료: template_candidate_data.xlsx")
print("   - 시트 1: 후보자 데이터 (샘플 데이터 포함)")
print("   - 시트 2: 작성 지침 (각 항목 설명)")
