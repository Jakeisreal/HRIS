from __future__ import annotations

import csv
import io
import json
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, Response
from werkzeug.security import check_password_hash, generate_password_hash

from backend.parsing import parse_candidate_workbook


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "hris.sqlite3"

CANDIDATE_FIELDS = (
    "employee_id",
    "name",
    "dept",
    "job_family",
    "position",
    "grade",
    "hire_date",
    "location",
    "email",
    "tenure",
    "performance",
    "performance_2024",
    "performance_2025",
    "performance_2026",
    "leadership",
    "language",
    "language_type",
    "language_score",
    "overseas",
    "overseas_country",
    "overseas_type",
    "overseas_months",
    "certificate",
    "expat_fit",
    "leader_fit",
    "purpose",
)

CHANGE_TRACKED_FIELDS = tuple(field for field in CANDIDATE_FIELDS if field != "employee_id")


DEFAULT_SESSION_TTL_SECONDS = int(os.environ.get("HRIS_AUTH_SESSION_TTL_SECONDS", 8 * 3600))
MAX_UPLOAD_BYTES = int(os.environ.get("HRIS_MAX_UPLOAD_BYTES", 10 * 1024 * 1024))

DEMO_PASSWORD_DEFAULT = os.environ.get("HRIS_DEMO_PASSWORD", "password")
DEMO_PASSWORDS = {
    "hr": os.environ.get("HRIS_DEMO_PASSWORD_HR", DEMO_PASSWORD_DEFAULT),
    "viewer": os.environ.get("HRIS_DEMO_PASSWORD_VIEWER", DEMO_PASSWORD_DEFAULT),
}


def create_app(db_path: str | os.PathLike[str] | None = None) -> Flask:
    app = Flask(__name__)
    app.testing = bool(os.environ.get("PYTEST_CURRENT_TEST"))
    app.config["DB_PATH"] = str(db_path or os.environ.get("HRIS_DB_PATH", DEFAULT_DB_PATH))
    init_db(app.config["DB_PATH"])

    @app.after_request
    def add_cors_headers(response):
        allowed_origin = os.environ.get("HRIS_CORS_ORIGIN")
        if not allowed_origin:
            if app.testing:
                allowed_origin = "http://localhost"
            else:
                raise RuntimeError("HRIS_CORS_ORIGIN environment 변수가 설정되어 있어야 합니다.")
        response.headers["Access-Control-Allow-Origin"] = allowed_origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.post("/api/auth/login")
    def login():
        payload = request.get_json(silent=True) or {}
        employee_id = str(payload.get("employee_id") or "").strip()
        password = str(payload.get("password") or "")
        if not employee_id or not password:
            return jsonify({"error": "사번과 비밀번호가 필요합니다."}), 400

        with connect(app.config["DB_PATH"]) as conn:
            user = conn.execute(
                """
                SELECT employee_id, name, role, password_hash, active
                FROM users
                WHERE employee_id = ?
                """,
                (employee_id,),
            ).fetchone()
            if user is None or not user["active"] or not check_password_hash(user["password_hash"], password):
                log_audit_event(
                    conn,
                    user=None,
                    action="로그인 실패",
                    target=employee_id or "-",
                    result="실패",
                    risk="주의",
                )
                conn.commit()
                return jsonify({"error": "아이디 또는 비밀번호가 올바르지 않습니다."}), 401

            token = secrets.token_urlsafe(32)
            expires_at = (datetime.utcnow() + timedelta(seconds=DEFAULT_SESSION_TTL_SECONDS)).strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT INTO auth_sessions (token, employee_id, expires_at) VALUES (?, ?, ?)",
                (token, employee_id, expires_at),
            )
            log_audit_event(
                conn,
                user=dict(user),
                action="로그인",
                target=employee_id,
                result="성공",
                risk="정상",
            )
            conn.commit()

        return jsonify(
            {
                "token": token,
                "user": {
                    "employee_id": user["employee_id"],
                    "name": user["name"],
                    "role": user["role"],
                },
            }
        )

    @app.get("/api/auth/me")
    def me():
        with connect(app.config["DB_PATH"]) as conn:
            user = authenticate_request(conn)
        if user is None:
            return jsonify({"error": "인증이 필요합니다."}), 401
        return jsonify({"user": user})

    @app.post("/api/auth/logout")
    def logout():
        token = get_bearer_token()
        if token:
            with connect(app.config["DB_PATH"]) as conn:
                user = authenticate_request(conn)
                conn.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
                log_audit_event(conn, user=user, action="로그아웃", target="-", result="성공", risk="정상")
                conn.commit()
        return jsonify({"ok": True})

    @app.get("/api/candidates")
    def list_candidates():
        with connect(app.config["DB_PATH"]) as conn:
            user = authenticate_request(conn)
            if user is None:
                log_audit_event(
                    conn,
                    user=None,
                    action="후보자 목록 조회",
                    target="/api/candidates",
                    result="차단",
                    risk="위험",
                )
                conn.commit()
                return jsonify({"error": "인증이 필요합니다."}), 401
            rows = conn.execute(
                f"""
                SELECT {", ".join(CANDIDATE_FIELDS)}, updated_at
                FROM candidates
                ORDER BY updated_at DESC, employee_id ASC
                """
            ).fetchall()
            log_audit_event(
                conn,
                user=user,
                action="후보자 목록 조회",
                target=f"{len(rows)}명",
                result="성공",
                risk="정상",
            )
            conn.commit()
        return jsonify({"items": [dict(row) for row in rows]})

    @app.get("/api/audit-logs")
    def list_audit_logs():
        with connect(app.config["DB_PATH"]) as conn:
            user = authenticate_request(conn)
            if user is None:
                log_audit_event(conn, user=None, action="감사 로그 조회", target="/api/audit-logs", result="차단", risk="위험")
                conn.commit()
                return jsonify({"error": "인증이 필요합니다."}), 401
            if user["role"] != "hr":
                log_audit_event(conn, user=user, action="감사 로그 조회", target="/api/audit-logs", result="차단", risk="위험")
                conn.commit()
                return jsonify({"error": "인사담당자 권한이 필요합니다."}), 403

            filters = parse_audit_log_query_params(request.args)
            where_clause, params = build_audit_log_filter_query(filters)
            rows = conn.execute(
                f"""
                SELECT occurred_at AS time, user_name AS user, role, action, target, result, risk, ip_address AS ip
                FROM audit_logs
                {where_clause}
                ORDER BY occurred_at DESC, id DESC
                LIMIT 200
                """,
                params,
            ).fetchall()
            log_audit_event(conn, user=user, action="감사 로그 조회", target="/api/audit-logs", result="성공", risk="주의", detail=filters)
            conn.commit()
        return jsonify({"items": [dict(row) for row in rows]})

    @app.get("/api/audit-logs/export")
    def export_audit_logs():
        with connect(app.config["DB_PATH"]) as conn:
            user = authenticate_request(conn)
            if user is None:
                log_audit_event(conn, user=None, action="감사 로그 CSV 내보내기", target="/api/audit-logs/export", result="차단", risk="위험")
                conn.commit()
                return jsonify({"error": "인증이 필요합니다."}), 401
            if user["role"] != "hr":
                log_audit_event(conn, user=user, action="감사 로그 CSV 내보내기", target="/api/audit-logs/export", result="차단", risk="위험")
                conn.commit()
                return jsonify({"error": "인사담당자 권한이 필요합니다."}), 403

            filters = parse_audit_log_query_params(request.args)
            where_clause, params = build_audit_log_filter_query(filters)
            rows = conn.execute(
                f"""
                SELECT occurred_at AS time, user_name AS user, role, action, target, result, risk, ip_address AS ip
                FROM audit_logs
                {where_clause}
                ORDER BY occurred_at DESC, id DESC
                """,
                params,
            ).fetchall()

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["time", "user", "role", "action", "target", "result", "risk", "ip"])
            for row in rows:
                writer.writerow([row["time"], row["user"], row["role"], row["action"], row["target"], row["result"], row["risk"], row["ip"]])

            log_audit_event(conn, user=user, action="감사 로그 CSV 내보내기", target="/api/audit-logs/export", result="성공", risk="주의", detail=filters)
            conn.commit()

            return Response(
                output.getvalue(),
                mimetype="text/csv; charset=utf-8",
                headers={"Content-Disposition": "attachment; filename= audit_logs.csv"},
            )

    @app.get("/api/templates")
    def list_templates():
        with connect(app.config["DB_PATH"]) as conn:
            user = authenticate_request(conn)
            if user is None:
                return jsonify({"error": "인증이 필요합니다."}), 401
            rows = fetch_templates_for_user(conn, user)
            log_audit_event(conn, user=user, action="템플릿 목록 조회", target=f"{len(rows)}건", result="성공", risk="정상")
            conn.commit()
        return jsonify({"items": [template_row_to_dict(row) for row in rows]})

    @app.post("/api/templates")
    def create_template():
        with connect(app.config["DB_PATH"]) as conn:
            user = authenticate_request(conn)
            if user is None:
                return jsonify({"error": "인증이 필요합니다."}), 401
            if user["role"] != "hr":
                log_audit_event(conn, user=user, action="템플릿 생성", target="/api/templates", result="차단", risk="위험")
                conn.commit()
                return jsonify({"error": "인사담당자 권한이 필요합니다."}), 403

            payload = request.get_json(silent=True) or {}
            template = normalize_template_payload(payload)
            if not template["name"]:
                return jsonify({"error": "템플릿 이름이 필요합니다."}), 400
            template_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO templates (
                    id, name, purpose, scope, owner_employee_id, owner_name, filters_json, filter_state_json, count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    template_id,
                    template["name"],
                    template["purpose"],
                    template["scope"],
                    user["employee_id"],
                    user["name"],
                    json.dumps(template["filters"], ensure_ascii=False),
                    json.dumps(template["filter_state"], ensure_ascii=False),
                    template["count"],
                ),
            )
            row = conn.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()
            log_audit_event(conn, user=user, action="템플릿 생성", target=template["name"], result="성공", risk="정상")
            conn.commit()
        return jsonify({"item": template_row_to_dict(row)}), 201

    @app.put("/api/templates/<template_id>")
    def update_template(template_id):
        with connect(app.config["DB_PATH"]) as conn:
            user = authenticate_request(conn)
            if user is None:
                return jsonify({"error": "인증이 필요합니다."}), 401
            row = conn.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()
            if row is None:
                return jsonify({"error": "템플릿을 찾을 수 없습니다."}), 404
            if not can_modify_template(row, user):
                log_audit_event(conn, user=user, action="템플릿 수정", target=template_id, result="차단", risk="위험")
                conn.commit()
                return jsonify({"error": "템플릿 수정 권한이 없습니다."}), 403

            payload = request.get_json(silent=True) or {}
            template = normalize_template_payload(payload, existing=template_row_to_dict(row))
            conn.execute(
                """
                UPDATE templates
                SET name = ?, purpose = ?, scope = ?, filters_json = ?, filter_state_json = ?,
                    count = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    template["name"],
                    template["purpose"],
                    template["scope"],
                    json.dumps(template["filters"], ensure_ascii=False),
                    json.dumps(template["filter_state"], ensure_ascii=False),
                    template["count"],
                    template_id,
                ),
            )
            row = conn.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()
            log_audit_event(conn, user=user, action="템플릿 수정", target=template["name"], result="성공", risk="정상")
            conn.commit()
        return jsonify({"item": template_row_to_dict(row)})

    @app.post("/api/templates/<template_id>/share")
    def share_template(template_id):
        with connect(app.config["DB_PATH"]) as conn:
            user = authenticate_request(conn)
            if user is None:
                return jsonify({"error": "인증이 필요합니다."}), 401
            row = conn.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()
            if row is None:
                return jsonify({"error": "템플릿을 찾을 수 없습니다."}), 404
            if not can_modify_template(row, user):
                log_audit_event(conn, user=user, action="템플릿 공유", target=template_id, result="차단", risk="위험")
                conn.commit()
                return jsonify({"error": "템플릿 공유 권한이 없습니다."}), 403
            conn.execute(
                "UPDATE templates SET scope = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                ("인사팀 공유", template_id),
            )
            row = conn.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()
            log_audit_event(conn, user=user, action="템플릿 공유", target=row["name"], result="성공", risk="정상")
            conn.commit()
        return jsonify({"item": template_row_to_dict(row)})

    @app.post("/api/templates/<template_id>/unshare")
    def unshare_template(template_id):
        with connect(app.config["DB_PATH"]) as conn:
            user = authenticate_request(conn)
            if user is None:
                return jsonify({"error": "인증이 필요합니다."}), 401
            row = conn.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()
            if row is None:
                return jsonify({"error": "템플릿을 찾을 수 없습니다."}), 404
            if not can_modify_template(row, user):
                log_audit_event(conn, user=user, action="템플릿 공유 해제", target=template_id, result="차단", risk="위험")
                conn.commit()
                return jsonify({"error": "템플릿 공유 해제 권한이 없습니다."}), 403
            conn.execute(
                "UPDATE templates SET scope = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                ("나만 보기", template_id),
            )
            row = conn.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()
            log_audit_event(conn, user=user, action="템플릿 공유 해제", target=row["name"], result="성공", risk="정상")
            conn.commit()
        return jsonify({"item": template_row_to_dict(row)})

    @app.delete("/api/templates/<template_id>")
    def delete_template_route(template_id):
        with connect(app.config["DB_PATH"]) as conn:
            user = authenticate_request(conn)
            if user is None:
                return jsonify({"error": "인증이 필요합니다."}), 401
            row = conn.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()
            if row is None:
                return jsonify({"error": "템플릿을 찾을 수 없습니다."}), 404
            if not can_modify_template(row, user):
                log_audit_event(conn, user=user, action="템플릿 삭제", target=template_id, result="차단", risk="위험")
                conn.commit()
                return jsonify({"error": "템플릿 삭제 권한이 없습니다."}), 403
            deleted = delete_template(conn, template_id)
            if deleted == 0:
                return jsonify({"error": "템플릿 삭제에 실패했습니다."}), 500
            log_audit_event(conn, user=user, action="템플릿 삭제", target=row["name"], result="성공", risk="주의")
            conn.commit()
        return jsonify({"ok": True, "id": template_id})

    @app.post("/api/candidates/upload")
    def upload_candidates():
        with connect(app.config["DB_PATH"]) as conn:
            user = authenticate_request(conn)
        if user is None:
            with connect(app.config["DB_PATH"]) as conn:
                log_audit_event(conn, user=None, action="엑셀 업로드", target="/api/candidates/upload", result="차단", risk="위험")
                conn.commit()
            return jsonify({"error": "인증이 필요합니다."}), 401
        if user["role"] != "hr":
            with connect(app.config["DB_PATH"]) as conn:
                log_audit_event(conn, user=user, action="엑셀 업로드", target="/api/candidates/upload", result="차단", risk="위험")
                conn.commit()
            return jsonify({"error": "인사담당자 권한이 필요합니다."}), 403

        uploaded = request.files.get("file")
        if uploaded is None:
            return jsonify({"error": "multipart form-data의 file 필드가 필요합니다."}), 400
        if not uploaded.filename.lower().endswith(".xlsx"):
            return jsonify({"error": "xlsx 파일만 업로드할 수 있습니다."}), 400

        if uploaded.content_length is not None and uploaded.content_length > MAX_UPLOAD_BYTES:
            return jsonify({"error": f"파일 크기는 {MAX_UPLOAD_BYTES // (1024 * 1024)}MB 이하만 허용합니다."}), 400

        uploaded.stream.seek(0, os.SEEK_END)
        file_size = uploaded.stream.tell()
        uploaded.stream.seek(0)
        if file_size > MAX_UPLOAD_BYTES:
            return jsonify({"error": f"파일 크기는 {MAX_UPLOAD_BYTES // (1024 * 1024)}MB 이하만 허용합니다."}), 400

        header = uploaded.stream.read(4)
        uploaded.stream.seek(0)
        if header != b"PK\x03\x04":
            return jsonify({"error": "유효하지 않은 파일 형식입니다."}), 400

        result = parse_candidate_workbook(uploaded.stream)
        dry_run = request.form.get("dry_run", "").lower() in {"1", "true", "yes"}
        summary: dict[str, Any] = {
            "file": uploaded.filename,
            "dry_run": dry_run,
            "rows_valid": len(result.candidates),
            "rows_error": len(result.errors),
            "headers": result.headers,
            "errors": [error.__dict__ for error in result.errors[:50]],
        }

        with connect(app.config["DB_PATH"]) as conn:
            change_summary = analyze_candidate_changes(conn, [candidate.data for candidate in result.candidates])

        summary.update(change_summary["counts"])
        summary["change_details"] = change_summary["changes"][:100]

        if dry_run:
            with connect(app.config["DB_PATH"]) as conn:
                log_audit_event(conn, user=user, action="엑셀 업로드 검증", target=uploaded.filename, result="성공", risk="정상")
                conn.commit()
            return jsonify(summary)

        with connect(app.config["DB_PATH"]) as conn:
            run_id = create_upload_run(conn, uploaded.filename, summary)
            upserted = upsert_candidates(conn, [candidate.data for candidate in result.candidates])
            save_upload_changes(conn, run_id, change_summary["changes"])
            save_upload_errors(conn, run_id, result.errors)
            log_audit_event(
                conn,
                user=user,
                action="엑셀 업로드",
                target=uploaded.filename,
                result="성공",
                risk="주의" if result.errors else "정상",
            )
            conn.commit()

        summary["upload_run_id"] = run_id
        summary["upserted"] = upserted
        return jsonify(summary), 201

    @app.post("/api/upload-runs/<int:run_id>/rollback")
    def rollback_upload(run_id):
        with connect(app.config["DB_PATH"]) as conn:
            user = authenticate_request(conn)
            if user is None:
                log_audit_event(conn, user=None, action="업로드 롤백", target=str(run_id), result="차단", risk="위험")
                conn.commit()
                return jsonify({"error": "인증이 필요합니다."}), 401
            if user["role"] != "hr":
                log_audit_event(conn, user=user, action="업로드 롤백", target=str(run_id), result="차단", risk="위험")
                conn.commit()
                return jsonify({"error": "인사담당자 권한이 필요합니다."}), 403

            changes = conn.execute(
                "SELECT employee_id, change_type, field_name, old_value FROM upload_changes WHERE upload_run_id = ? ORDER BY id DESC",
                (run_id,),
            ).fetchall()
            if not changes:
                return jsonify({"error": "Rollback 대상 업로드를 찾을 수 없습니다."}), 404

            for change in changes:
                employee_id = change["employee_id"]
                if change["change_type"] == "new":
                    conn.execute("DELETE FROM candidates WHERE employee_id = ?", (employee_id,))
                elif change["change_type"] == "changed" and change["field_name"] in CHANGE_TRACKED_FIELDS:
                    conn.execute(
                        f"UPDATE candidates SET {change['field_name']} = ? WHERE employee_id = ?",
                        (change["old_value"], employee_id),
                    )

            log_audit_event(conn, user=user, action="업로드 롤백", target=str(run_id), result="성공", risk="주의")
            conn.commit()

        return jsonify({"ok": True, "run_id": run_id})

    return app


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(str(path)) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS candidates (
                employee_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                dept TEXT,
                job_family TEXT,
                position TEXT,
                grade TEXT,
                hire_date TEXT,
                location TEXT,
                email TEXT,
                tenure REAL,
                performance TEXT,
                performance_2024 TEXT,
                performance_2025 TEXT,
                performance_2026 TEXT,
                leadership TEXT,
                language TEXT,
                language_type TEXT,
                language_score REAL,
                overseas TEXT,
                overseas_country TEXT,
                overseas_type TEXT,
                overseas_months REAL,
                certificate TEXT,
                expat_fit REAL,
                leader_fit REAL,
                purpose TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS upload_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                summary_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS upload_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_run_id INTEGER NOT NULL,
                row_number INTEGER NOT NULL,
                message TEXT NOT NULL,
                FOREIGN KEY(upload_run_id) REFERENCES upload_runs(id)
            );

            CREATE TABLE IF NOT EXISTS upload_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_run_id INTEGER NOT NULL,
                employee_id TEXT NOT NULL,
                change_type TEXT NOT NULL,
                field_name TEXT,
                old_value TEXT,
                new_value TEXT,
                FOREIGN KEY(upload_run_id) REFERENCES upload_runs(id)
            );

            CREATE TABLE IF NOT EXISTS users (
                employee_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('hr', 'viewer')),
                password_hash TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS auth_sessions (
                token TEXT PRIMARY KEY,
                employee_id TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                FOREIGN KEY(employee_id) REFERENCES users(employee_id)
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                employee_id TEXT,
                user_name TEXT NOT NULL,
                role TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT NOT NULL,
                result TEXT NOT NULL,
                risk TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                detail_json TEXT
            );

            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                purpose TEXT NOT NULL,
                scope TEXT NOT NULL,
                owner_employee_id TEXT,
                owner_name TEXT NOT NULL,
                filters_json TEXT NOT NULL,
                filter_state_json TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        ensure_candidate_columns(conn)
        ensure_auth_session_columns(conn)
        seed_demo_users(conn)
        seed_default_templates(conn)


def ensure_candidate_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(candidates)").fetchall()}
    column_sql = {
        "job_family": "TEXT",
        "grade": "TEXT",
        "hire_date": "TEXT",
        "location": "TEXT",
        "email": "TEXT",
        "performance_2024": "TEXT",
        "performance_2025": "TEXT",
        "performance_2026": "TEXT",
        "language_type": "TEXT",
        "overseas_country": "TEXT",
        "overseas_type": "TEXT",
    }
    for column, column_type in column_sql.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE candidates ADD COLUMN {column} {column_type}")

def ensure_auth_session_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(auth_sessions)").fetchall()}
    if "expires_at" not in existing:
        conn.execute("ALTER TABLE auth_sessions ADD COLUMN expires_at TEXT")


def seed_demo_users(conn: sqlite3.Connection) -> None:
    users = [
        ("E24017", "김도현", "hr"),
        ("E90001", "박민수", "viewer"),
    ]
    for employee_id, name, role in users:
        password = DEMO_PASSWORDS.get(role, DEMO_PASSWORD_DEFAULT)
        exists = conn.execute("SELECT 1 FROM users WHERE employee_id = ?", (employee_id,)).fetchone()
        if exists is None:
            conn.execute(
                """
                INSERT INTO users (employee_id, name, role, password_hash)
                VALUES (?, ?, ?, ?)
                """,
                (employee_id, name, role, generate_password_hash(password)),
            )


def seed_default_templates(conn: sqlite3.Connection) -> None:
    defaults = [
        {
            "id": "expat-basic",
            "name": "주재원 기본 템플릿",
            "purpose": "주재원",
            "scope": "기본 제공",
            "owner_employee_id": None,
            "owner_name": "System",
            "filters": ["TOEIC 800 이상", "최근 평가 A 이상", "해외 경험 보유", "근속 5년 이상"],
            "filter_state": {"purpose": "주재원", "minLanguage": 800, "overseasOnly": True},
            "count": 86,
        },
        {
            "id": "leader-basic",
            "name": "차기 팀장 기본 템플릿",
            "purpose": "차기 팀장",
            "scope": "기본 제공",
            "owner_employee_id": None,
            "owner_name": "System",
            "filters": ["최근 3년 평균 B+ 이상", "리더십 A 이상", "근속 7년 이상", "조직관리 가능성"],
            "filter_state": {"purpose": "차기 팀장", "minLanguage": 700, "overseasOnly": False},
            "count": 124,
        },
    ]
    for template in defaults:
        exists = conn.execute("SELECT 1 FROM templates WHERE id = ?", (template["id"],)).fetchone()
        if exists is None:
            conn.execute(
                """
                INSERT INTO templates (
                    id, name, purpose, scope, owner_employee_id, owner_name,
                    filters_json, filter_state_json, count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    template["id"],
                    template["name"],
                    template["purpose"],
                    template["scope"],
                    template["owner_employee_id"],
                    template["owner_name"],
                    json.dumps(template["filters"], ensure_ascii=False),
                    json.dumps(template["filter_state"], ensure_ascii=False),
                    template["count"],
                ),
            )


def get_bearer_token() -> str | None:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = header.removeprefix("Bearer ").strip()
    return token or None


def authenticate_request(conn: sqlite3.Connection) -> dict[str, Any] | None:
    token = get_bearer_token()
    if token is None:
        return None
    row = conn.execute(
        """
        SELECT users.employee_id, users.name, users.role
        FROM auth_sessions
        JOIN users ON users.employee_id = auth_sessions.employee_id
        WHERE auth_sessions.token = ?
          AND users.active = 1
          AND auth_sessions.expires_at > CURRENT_TIMESTAMP
        """,
        (token,),
    ).fetchone()
    return dict(row) if row else None


def fetch_templates_for_user(conn: sqlite3.Connection, user: dict[str, Any]) -> list[sqlite3.Row]:
    if user["role"] == "hr":
        return conn.execute(
            """
            SELECT * FROM templates
            WHERE scope IN ('기본 제공', '인사팀 공유')
               OR owner_employee_id = ?
            ORDER BY updated_at DESC, name ASC
            """,
            (user["employee_id"],),
        ).fetchall()
    return conn.execute(
        """
        SELECT * FROM templates
        WHERE scope IN ('기본 제공', '인사팀 공유')
        ORDER BY updated_at DESC, name ASC
        """
    ).fetchall()


def delete_template(conn: sqlite3.Connection, template_id: str) -> int:
    result = conn.execute("DELETE FROM templates WHERE id = ?", (template_id,))
    return result.rowcount


def build_audit_log_filter_query(filters: dict[str, Any]) -> tuple[str, list[Any]]:
    clauses = []
    params: list[Any] = []
    if filters.get("from"):
        clauses.append("occurred_at >= ?")
        params.append(filters["from"])
    if filters.get("to"):
        clauses.append("occurred_at <= ?")
        params.append(filters["to"])
    if filters.get("user"):
        clauses.append("user_name LIKE ?")
        params.append(f"%{filters['user']}%")
    if filters.get("risk"):
        clauses.append("risk = ?")
        params.append(filters["risk"])
    where_clause = "WHERE " + " AND ".join(clauses) if clauses else ""
    return where_clause, params


def parse_audit_log_query_params(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "from": parse_audit_log_date(args.get("from"), start_of_day=True),
        "to": parse_audit_log_date(args.get("to"), end_of_day=True),
        "user": str(args.get("user") or "").strip() or None,
        "risk": str(args.get("risk") or "").strip() or None,
    }


def parse_audit_log_date(value: str | None, start_of_day: bool = False, end_of_day: bool = False) -> str | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None
    if start_of_day:
        parsed = parsed.replace(hour=0, minute=0, second=0, microsecond=0)
    if end_of_day:
        parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=0)
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def template_row_to_dict(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    data = dict(row)
    return {
        "id": data["id"],
        "name": data["name"],
        "purpose": data["purpose"],
        "scope": data["scope"],
        "owner_employee_id": data.get("owner_employee_id"),
        "owner": data["owner_name"],
        "filters": json.loads(data["filters_json"]),
        "filter_state": json.loads(data["filter_state_json"]),
        "count": data["count"],
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
    }


def normalize_template_payload(payload: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    existing = existing or {}
    filter_state = payload.get("filter_state") or existing.get("filter_state") or {}
    filters = payload.get("filters") or existing.get("filters") or describe_filter_state(filter_state)
    return {
        "name": str(payload.get("name") or existing.get("name") or "").strip(),
        "purpose": str(payload.get("purpose") or existing.get("purpose") or filter_state.get("purpose") or "전체"),
        "scope": str(payload.get("scope") or existing.get("scope") or "나만 보기"),
        "filters": filters,
        "filter_state": filter_state,
        "count": int(payload.get("count") if payload.get("count") is not None else existing.get("count") or 0),
    }


def describe_filter_state(filter_state: dict[str, Any]) -> list[str]:
    labels = []
    purpose = filter_state.get("purpose")
    if purpose and purpose != "전체":
        labels.append(f"{purpose} 목적")
    if filter_state.get("minLanguage") is not None:
        labels.append(f"어학 {filter_state['minLanguage']} 이상")
    if filter_state.get("overseasOnly"):
        labels.append("해외 경험 보유")
    return labels or ["전체 후보"]


def can_modify_template(row: sqlite3.Row, user: dict[str, Any]) -> bool:
    if user["role"] != "hr":
        return False
    return row["scope"] == "기본 제공" or row["owner_employee_id"] in (None, user["employee_id"])


def log_audit_event(
    conn: sqlite3.Connection,
    user: dict[str, Any] | None,
    action: str,
    target: str,
    result: str,
    risk: str,
    detail: dict[str, Any] | None = None,
) -> None:
    user = user or {}
    conn.execute(
        """
        INSERT INTO audit_logs (
            employee_id, user_name, role, action, target, result, risk, ip_address, detail_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user.get("employee_id"),
            user.get("name") or "Anonymous",
            user.get("role") or "anonymous",
            action,
            target,
            result,
            risk,
            request.headers.get("X-Forwarded-For", request.remote_addr or "-").split(",")[0].strip(),
            json.dumps(detail, ensure_ascii=False) if detail else None,
        ),
    )


def create_upload_run(conn: sqlite3.Connection, filename: str, summary: dict[str, Any]) -> int:
    cursor = conn.execute(
        "INSERT INTO upload_runs (filename, summary_json) VALUES (?, ?)",
        (filename, json.dumps(summary, ensure_ascii=False)),
    )
    return int(cursor.lastrowid)


def save_upload_errors(conn: sqlite3.Connection, upload_run_id: int, errors) -> None:
    conn.executemany(
        "INSERT INTO upload_errors (upload_run_id, row_number, message) VALUES (?, ?, ?)",
        [(upload_run_id, error.row_number, error.message) for error in errors],
    )


def save_upload_changes(conn: sqlite3.Connection, upload_run_id: int, changes: list[dict[str, Any]]) -> None:
    rows = []
    for change in changes:
        fields = change.get("fields") or []
        if not fields:
            rows.append((upload_run_id, change["employee_id"], change["change_type"], None, None, None))
            continue
        for field in fields:
            rows.append(
                (
                    upload_run_id,
                    change["employee_id"],
                    change["change_type"],
                    field["field_name"],
                    _serialize_for_compare(field.get("old_value")),
                    _serialize_for_compare(field.get("new_value")),
                )
            )
    conn.executemany(
        """
        INSERT INTO upload_changes (upload_run_id, employee_id, change_type, field_name, old_value, new_value)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def analyze_candidate_changes(conn: sqlite3.Connection, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    existing = fetch_existing_candidates(conn, [candidate["employee_id"] for candidate in candidates])
    changes: list[dict[str, Any]] = []
    counts = {"newRows": 0, "changedRows": 0, "dup": 0}

    for candidate in candidates:
        normalized = normalize_candidate(candidate)
        employee_id = normalized["employee_id"]
        before = existing.get(employee_id)
        if before is None:
            counts["newRows"] += 1
            changes.append({"employee_id": employee_id, "change_type": "new", "fields": []})
            continue

        field_changes = diff_candidate(before, normalized)
        if field_changes:
            counts["changedRows"] += 1
            changes.append({"employee_id": employee_id, "change_type": "changed", "fields": field_changes})
        else:
            counts["dup"] += 1
            changes.append({"employee_id": employee_id, "change_type": "unchanged", "fields": []})

    return {"counts": counts, "changes": changes}


def fetch_existing_candidates(conn: sqlite3.Connection, employee_ids: list[str]) -> dict[str, dict[str, Any]]:
    ids = [str(employee_id) for employee_id in employee_ids]
    if not ids:
        return {}
    placeholders = ", ".join("?" for _ in ids)
    rows = conn.execute(
        f"SELECT {', '.join(CANDIDATE_FIELDS)} FROM candidates WHERE employee_id IN ({placeholders})",
        ids,
    ).fetchall()
    return {row["employee_id"]: dict(row) for row in rows}


def diff_candidate(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    changes = []
    for field in CHANGE_TRACKED_FIELDS:
        old_value = _serialize_for_compare(before.get(field))
        new_value = _serialize_for_compare(after.get(field))
        if old_value != new_value:
            changes.append({"field_name": field, "old_value": before.get(field), "new_value": after.get(field)})
    return changes


def upsert_candidates(conn: sqlite3.Connection, candidates: list[dict[str, Any]]) -> int:
    if not candidates:
        return 0

    values = [tuple(normalize_candidate(candidate).get(field) for field in CANDIDATE_FIELDS) for candidate in candidates]
    placeholders = ", ".join("?" for _ in CANDIDATE_FIELDS)
    update_clause = ", ".join(f"{field}=excluded.{field}" for field in CANDIDATE_FIELDS if field != "employee_id")

    conn.executemany(
        f"""
        INSERT INTO candidates ({", ".join(CANDIDATE_FIELDS)})
        VALUES ({placeholders})
        ON CONFLICT(employee_id) DO UPDATE SET
            {update_clause},
            updated_at=CURRENT_TIMESTAMP
        """,
        values,
    )
    return len(candidates)


def normalize_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    normalized = {field: _serialize_value(candidate.get(field)) for field in CANDIDATE_FIELDS}
    normalized["employee_id"] = str(normalized["employee_id"]).strip()
    normalized["name"] = str(normalized["name"]).strip()
    return normalized


def _serialize_value(value: Any) -> Any:
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    return value


def _serialize_for_compare(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(_serialize_value(value)).strip()


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=True)
