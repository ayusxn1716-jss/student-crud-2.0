import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("STUDENTS_DB_PATH", str(tmp_path / "test.db"))
    from app.main import app
    with TestClient(app) as c:  # runs lifespan -> creates tables
        yield c


@pytest.fixture()
def student():
    return {"name": "Test Student", "date_of_birth": "2004-05-10",
            "email": "test@example.com", "phone": "9876543210", "course": "B.Tech AIML"}
