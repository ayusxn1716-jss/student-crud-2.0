# Students Database CRUD API

Internship project for **EWB Edu Tech Pvt. Ltd.** A Python backend to manage student records
(Create, Read, Update, Delete) built with **FastAPI** and **SQLite**, plus an **optional local AI
extension** using Ollama.

## Features
- Full CRUD for students with persistent SQLite storage
- Filtering (name, course, date-of-birth range) and pagination on the list endpoint
- Input validation (email format, phone format, no future dates, at least one contact method)
- Proper error handling: `404` for missing records, `409` for duplicate email, `422` for invalid input
- **Simple web dashboard** (stats, search, add/edit/delete popup form, Ask AI) at the home page
- Auto-generated API docs at `/docs` (for developers)
- Automated tests (pytest)
- Optional: ask natural-language questions answered by a local Ollama model, grounded in database records

## Project structure
```
students-crud/
├── app/
│   ├── main.py            # FastAPI app + startup (creates DB table)
│   ├── database.py        # SQLite connection + schema
│   ├── schemas.py         # Pydantic validation models
│   ├── crud.py            # All SQL (parameterised queries)
│   ├── ai_service.py      # Optional Ollama integration
│   ├── static/            # Web UI: index.html, style.css, app.js (plain HTML/CSS/JS)
│   └── routers/
│       ├── students.py    # /students endpoints
│       └── ai.py          # /ai/ask endpoint
├── tests/                 # pytest suite
├── seed.py                # Loads DUMMY data
├── requirements.txt
└── README.md
```

## Prerequisites
- Python 3.10+
- (Optional, for the AI bonus) [Ollama](https://ollama.com/download)

## Installation
```bash
git clone <your-repo-url>
cd students-crud

python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

## Run
```bash
uvicorn app.main:app --reload
```
- **Web app (use this): http://127.0.0.1:8000**
- API docs for developers: http://127.0.0.1:8000/docs

The SQLite file `students.db` is created automatically on first run.

Optional: load 8 dummy students for testing:
```bash
python seed.py
```

## API endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/students` | Create a student |
| GET | `/students` | List / filter students |
| GET | `/students/{student_id}` | View one student |
| PUT | `/students/{student_id}` | Replace all details |
| PATCH | `/students/{student_id}` | Update some details |
| DELETE | `/students/{student_id}` | Delete a student |
| POST | `/ai/ask` | (Optional) Ask a question about the data |

**Student fields:** `id` (auto), `name`*, `date_of_birth`* (YYYY-MM-DD), `email` and/or `phone`
(at least one required), `course`, `address`, `enrollment_date`.

**List filters:** `?name=`, `?course=`, `?born_after=YYYY-MM-DD`, `?born_before=YYYY-MM-DD`, `?limit=`, `?offset=`

## Testing the API (sample requests)
```bash
# Create
curl -X POST http://127.0.0.1:8000/students -H "Content-Type: application/json" \
  -d '{"name":"Riya Das","date_of_birth":"2005-04-20","email":"riya@example.com","phone":"9876501234","course":"B.Tech AIML"}'

# List all / filter
curl http://127.0.0.1:8000/students
curl "http://127.0.0.1:8000/students?course=AIML&born_after=2005-01-01"

# View one
curl http://127.0.0.1:8000/students/1

# Update some fields
curl -X PATCH http://127.0.0.1:8000/students/1 -H "Content-Type: application/json" -d '{"course":"BCA"}'

# Replace all fields
curl -X PUT http://127.0.0.1:8000/students/1 -H "Content-Type: application/json" \
  -d '{"name":"Riya Das","date_of_birth":"2005-04-20","email":"riya@example.com","course":"BBA"}'

# Delete
curl -X DELETE http://127.0.0.1:8000/students/1
```
Error examples: `GET /students/999` returns `404`; posting the same email twice returns `409`;
an invalid email or a future date of birth returns `422`.

## Run the automated tests
```bash
pip install -r requirements-dev.txt
pytest
```
Tests use a temporary database, so your real `students.db` is never touched.

## Optional bonus: local AI with Ollama
1. Install Ollama and pull a small model:
   ```bash
   ollama pull llama3.2:1b
   ollama serve        # skip if Ollama is already running
   ```
2. Make sure there's some (dummy) data: `python seed.py`
3. Ask questions:
   ```bash
   curl -X POST http://127.0.0.1:8000/ai/ask -H "Content-Type: application/json" \
     -d '{"question":"How many students are there?"}'

   curl -X POST http://127.0.0.1:8000/ai/ask -H "Content-Type: application/json" \
     -d '{"question":"List students born after 2005"}'
   ```
The response contains the `answer` and the exact `records_used`, so you can verify it.

**How it stays grounded and safe**
- The model **never writes or runs SQL.** The backend detects the intent
  (e.g. "born after 2005", a course name, a student name), fetches matching rows with fixed
  parameterised queries, and passes them to the model as context.
- The context always includes the true total and match count, so counting questions don't depend
  on a small model counting rows itself.
- The prompt instructs the model to answer only from the context; temperature is 0.
- If Ollama isn't running, `/ai/ask` returns a clear `503` message and the CRUD API is unaffected.

Config (optional env vars): `OLLAMA_URL` (default `http://localhost:11434`), `OLLAMA_MODEL`
(default `llama3.2:1b`), `STUDENTS_DB_PATH`. See `.env.example`.

## Notes
- Only dummy data is included. Do not commit real student information (`*.db` and `.env` are git-ignored).
- Architecture in one line: **router** (HTTP + validation) → **crud** (SQL) → **SQLite**.
