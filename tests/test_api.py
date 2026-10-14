import os
import tempfile

os.environ["STUDENTS_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

import pytest
from fastapi.testclient import TestClient

from app import ai
from app.main import app

VALID = {"name": "Test User", "date_of_birth": "2004-01-01", "email": "t@example.com",
         "phone": "+91 99999 99999", "course": "BCA"}


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
        for s in c.get("/students").json():
            c.delete(f"/students/{s['id']}")


def test_full_crud(client):
    r = client.post("/students", json=VALID)
    assert r.status_code == 201
    sid = r.json()["id"]

    assert client.get(f"/students/{sid}").json()["name"] == "Test User"
    assert len(client.get("/students").json()) == 1

    r = client.put(f"/students/{sid}", json={**VALID, "name": "Renamed User"})
    assert r.json()["name"] == "Renamed User"

    r = client.patch(f"/students/{sid}", json={"course": "MCA"})
    assert r.json()["course"] == "MCA" and r.json()["name"] == "Renamed User"

    assert client.delete(f"/students/{sid}").status_code == 204
    assert client.get(f"/students/{sid}").status_code == 404


def test_missing_record(client):
    assert client.get("/students/999").status_code == 404
    assert client.put("/students/999", json=VALID).status_code == 404
    assert client.patch("/students/999", json={"course": "x"}).status_code == 404
    assert client.delete("/students/999").status_code == 404


def test_validation(client):
    assert client.post("/students", json={**VALID, "email": "bad"}).status_code == 422
    assert client.post("/students", json={**VALID, "date_of_birth": "2999-01-01"}).status_code == 422
    assert client.post("/students", json={"name": "No Contact", "date_of_birth": "2004-01-01"}).status_code == 422
    assert client.post("/students", json={**VALID, "phone": "abc"}).status_code == 422


def test_duplicate_email(client):
    client.post("/students", json=VALID)
    assert client.post("/students", json=VALID).status_code == 409


def test_filters(client):
    client.post("/students", json={**VALID, "email": "a@example.com", "date_of_birth": "2003-05-05"})
    client.post("/students", json={**VALID, "email": "b@example.com", "name": "Zed Young",
                                   "date_of_birth": "2006-05-05", "course": "BBA"})
    assert len(client.get("/students", params={"born_after": "2005-01-01"}).json()) == 1
    assert len(client.get("/students", params={"course": "BBA"}).json()) == 1
    assert len(client.get("/students", params={"name": "zed"}).json()) == 1


def test_patch_cannot_remove_all_contacts(client):
    sid = client.post("/students", json={**VALID, "phone": None}).json()["id"]
    r = client.patch(f"/students/{sid}", json={"email": None})
    assert r.status_code == 422


def test_ai_context_is_built_from_db(client, monkeypatch):
    client.post("/students", json={**VALID, "date_of_birth": "2006-02-02"})
    client.post("/students", json={**VALID, "email": "old@example.com", "name": "Old Timer",
                                   "date_of_birth": "2001-02-02"})
    captured = {}

    def fake(prompt):
        captured["p"] = prompt
        return "ok"

    monkeypatch.setattr(ai, "ask_ollama", fake)
    r = client.post("/ask", json={"question": "List students born after 2005"})
    assert r.status_code == 200 and r.json()["records_used"] == 1
    assert "Test User" in captured["p"] and "Old Timer" not in captured["p"]


def test_ai_unavailable_returns_503(client, monkeypatch):
    monkeypatch.setattr(ai, "OLLAMA_URL", "http://127.0.0.1:1")
    assert client.post("/ask", json={"question": "How many students?"}).status_code == 503
