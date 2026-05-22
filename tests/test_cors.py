from backend.app import create_app


def test_localhost_and_loopback_origins_are_allowed(tmp_path, monkeypatch):
    monkeypatch.delenv("HRIS_CORS_ORIGIN", raising=False)
    app = create_app(tmp_path / "hris.sqlite3")
    app.testing = False

    client = app.test_client()
    localhost = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    loopback = client.get("/api/health", headers={"Origin": "http://127.0.0.1:5173"})

    assert localhost.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert loopback.headers["Access-Control-Allow-Origin"] == "http://127.0.0.1:5173"
    assert "PUT" in loopback.headers["Access-Control-Allow-Methods"]
    assert "DELETE" in loopback.headers["Access-Control-Allow-Methods"]
