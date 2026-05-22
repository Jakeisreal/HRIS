from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request

from backend.parsing import parse_candidate_workbook


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "hris.sqlite3"


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

    @app.get("/api/candidates")
    def list_candidates():
        with connect(app.config["DB_PATH"]) as conn:
            rows = conn.execute(
                """
                SELECT employee_id, name, dept, position, tenure, performance, leadership,
                       language, language_score, overseas, overseas_months, certificate,
                       expat_fit, leader_fit, purpose, updated_at
                FROM candidates
                ORDER BY updated_at DESC, employee_id ASC
                """
            ).fetchall()
        return jsonify({"items": [dict(row) for row in rows]})

    @app.post("/api/candidates/upload")
    def upload_candidates():
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

        if dry_run:
            return jsonify(summary)

        with connect(app.config["DB_PATH"]) as conn:
            run_id = create_upload_run(conn, uploaded.filename, summary)
            upserted = upsert_candidates(conn, [candidate.data for candidate in result.candidates])
            save_upload_errors(conn, run_id, result.errors)
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
                position TEXT,
                tenure REAL,
                performance TEXT,
                leadership TEXT,
                language TEXT,
                language_score REAL,
                overseas TEXT,
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
            """
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


def upsert_candidates(conn: sqlite3.Connection, candidates: list[dict[str, Any]]) -> int:
    if not candidates:
        return 0

    fields = (
        "employee_id",
        "name",
        "dept",
        "position",
        "tenure",
        "performance",
        "leadership",
        "language",
        "language_score",
        "overseas",
        "overseas_months",
        "certificate",
        "expat_fit",
        "leader_fit",
        "purpose",
    )
    values = [tuple(_serialize_value(candidate.get(field)) for field in fields) for candidate in candidates]
    placeholders = ", ".join("?" for _ in fields)
    update_clause = ", ".join(f"{field}=excluded.{field}" for field in fields if field != "employee_id")

    conn.executemany(
        f"""
        INSERT INTO candidates ({", ".join(fields)})
        VALUES ({placeholders})
        ON CONFLICT(employee_id) DO UPDATE SET
            {update_clause},
            updated_at=CURRENT_TIMESTAMP
        """,
        values,
    )
    return len(candidates)


def _serialize_value(value: Any) -> Any:
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    return value


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=True)
