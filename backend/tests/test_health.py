from sqlalchemy import inspect


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_docs_disabled_by_default(client):
    assert client.get("/api/docs").status_code == 404
    assert client.get("/api/openapi.json").status_code == 404


def test_all_tables_created(engine):
    assert set(inspect(engine).get_table_names()) == {
        "customers",
        "sessions",
        "accounts",
        "transactions",
        "recurring_items",
        "insight_feedback",
        "goals",
    }
