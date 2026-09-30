from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_client(tmp_path, with_dist: bool = True) -> TestClient:
    dist = tmp_path / "dist"
    if with_dist:
        (dist / "assets").mkdir(parents=True)
        (dist / "index.html").write_text("<!doctype html><title>TM</title>")
        (dist / "assets" / "app.js").write_text("console.log(1)")
    settings = Settings(_env_file=None, database_url="sqlite://", frontend_dist=str(dist))
    return TestClient(create_app(settings))


def test_index_and_client_routes_serve_the_app(tmp_path):
    client = make_client(tmp_path)
    for path in ("/", "/goals/1", "/insights/spend:food:2026-09/scenario"):
        response = client.get(path)
        assert response.status_code == 200
        assert "<title>TM</title>" in response.text
        assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_assets_are_served(tmp_path):
    response = make_client(tmp_path).get("/assets/app.js")
    assert response.status_code == 200 and "console.log" in response.text


def test_unknown_api_path_is_a_json_404_not_the_app(tmp_path):
    response = make_client(tmp_path).get("/api/nope")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_without_a_build_nothing_is_served(tmp_path):
    assert make_client(tmp_path, with_dist=False).get("/").status_code == 404
