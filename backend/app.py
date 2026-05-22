from __future__ import annotations

import json
import os
import secrets
import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
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


def create_app(db_path: str | os.PathLike[str] | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = str(db_path or os.environ.get("HRIS_DB_PATH", DEFAULT_DB_PATH))
    init_db(app.config["DB_PATH"])

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = os.environ.get("HRIS_CORS_ORIGIN", "*")
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
            conn.execute(
                "INSERT INTO auth_sessions (token, employee_id) VALUES (?, ?)",
                (token, employee_id),
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

            rows = conn.execute(
                """
                SELECT occurred_at AS time, user_name AS user, role, action, target, result, risk, ip_address AS ip
                FROM audit_logs
                ORDER BY occurred_at DESC, id DESC
                LIMIT 200
                """
            ).fetchall()
            log_audit_event(conn, user=user, action="감사 로그 조회", target="/api/audit-logs", result="성공", risk="주의")
            conn.commit()
        return jsonify({"items": [dict(row) for row in rows]})

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
            """
        )
        ensure_candidate_columns(conn)
        seed_demo_users(conn)


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


def seed_demo_users(conn: sqlite3.Connection) -> None:
    users = [
        ("E24017", "김도현", "hr", "password"),
        ("E90001", "박민수", "viewer", "password"),
    ]
    for employee_id, name, role, password in users:
        exists = conn.execute("SELECT 1 FROM users WHERE employee_id = ?", (employee_id,)).fetchone()
        if exists is None:
            conn.execute(
                """
                INSERT INTO users (employee_id, name, role, password_hash)
                VALUES (?, ?, ?, ?)
                """,
                (employee_id, name, role, generate_password_hash(password)),
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
        WHERE auth_sessions.token = ? AND users.active = 1
        """,
        (token,),
    ).fetchone()
    return dict(row) if row else None


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
