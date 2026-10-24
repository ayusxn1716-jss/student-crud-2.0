def test_create_and_read(client, student):
    r = client.post("/students", json=student)
    assert r.status_code == 201
    sid = r.json()["id"]
    assert client.get(f"/students/{sid}").json()["name"] == "Test Student"
    assert len(client.get("/students").json()) == 1


def test_update_put_and_patch(client, student):
    sid = client.post("/students", json=student).json()["id"]
    r = client.patch(f"/students/{sid}", json={"course": "BCA"})
    assert r.status_code == 200 and r.json()["course"] == "BCA"
    assert r.json()["name"] == "Test Student"  # untouched
    r = client.put(f"/students/{sid}", json={**student, "name": "New Name"})
    assert r.json()["name"] == "New Name"


def test_delete(client, student):
    sid = client.post("/students", json=student).json()["id"]
    assert client.delete(f"/students/{sid}").status_code == 204
    assert client.get(f"/students/{sid}").status_code == 404


def test_missing_record_404(client, student):
    assert client.get("/students/999").status_code == 404
    assert client.put("/students/999", json=student).status_code == 404
    assert client.patch("/students/999", json={"course": "x"}).status_code == 404
    assert client.delete("/students/999").status_code == 404


def test_validation(client, student):
    assert client.post("/students", json={**student, "email": "not-an-email"}).status_code == 422
    assert client.post("/students", json={**student, "date_of_birth": "2999-01-01"}).status_code == 422
    assert client.post("/students", json={**student, "name": "  "}).status_code == 422
    no_contact = {k: v for k, v in student.items() if k not in ("email", "phone")}
    assert client.post("/students", json=no_contact).status_code == 422
    assert client.post("/students", json={**student, "phone": "abc"}).status_code == 422


def test_duplicate_email(client, student):
    client.post("/students", json=student)
    assert client.post("/students", json=student).status_code == 409


def test_patch_cannot_remove_all_contact(client, student):
    sid = client.post("/students", json={**student, "phone": None}).json()["id"]
    assert client.patch(f"/students/{sid}", json={"email": None}).status_code == 422


def test_filters(client, student):
    client.post("/students", json=student)
    client.post("/students", json={**student, "name": "Other", "email": "o@example.com",
                                   "date_of_birth": "2006-02-02", "course": "BCA"})
    assert len(client.get("/students?course=BCA").json()) == 1
    assert len(client.get("/students?born_after=2005-01-01").json()) == 1
    assert len(client.get("/students?name=test").json()) == 1


def test_data_persists_across_connections(client, student):
    client.post("/students", json=student)
    from app.database import connect
    conn = connect()
    assert conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 1
    conn.close()


def test_dashboard_page_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "Student Manager" in r.text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200
