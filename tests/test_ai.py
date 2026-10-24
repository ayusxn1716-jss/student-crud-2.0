"""AI tests mock the Ollama call, so no model is needed to run them."""
from app import ai_service


def _seed(client):
    for i, (n, dob, c) in enumerate([("A One", "2004-01-01", "BCA"),
                                     ("B Two", "2006-06-06", "BBA"),
                                     ("C Three", "2007-07-07", "BCA")]):
        client.post("/students", json={"name": n, "date_of_birth": dob,
                                       "email": f"s{i}@example.com", "course": c})


def test_born_after_retrieves_correct_records(client, monkeypatch):
    _seed(client)
    seen = {}

    def fake(question, context):
        seen["context"] = context
        return "ok"

    monkeypatch.setattr(ai_service, "ask_ollama", fake)
    r = client.post("/ai/ask", json={"question": "List students born after 2005"})
    assert r.status_code == 200
    assert {s["name"] for s in r.json()["records_used"]} == {"B Two", "C Three"}
    assert "Total students in database: 3" in seen["context"]
    assert "A One" not in seen["context"]


def test_count_question_includes_total(client, monkeypatch):
    _seed(client)
    monkeypatch.setattr(ai_service, "ask_ollama", lambda q, c: c)
    r = client.post("/ai/ask", json={"question": "How many students are there?"})
    assert "Total students in database: 3" in r.json()["answer"]


def test_ollama_down_returns_503(client, monkeypatch):
    monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:1")
    r = client.post("/ai/ask", json={"question": "How many students are there?"})
    assert r.status_code == 503
