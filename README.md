# Students Database CRUD API

Python backend for managing student records, built for the **EWB Edu Tech internship assignment**.
Stack: **FastAPI + SQLite** (standard `sqlite3`), with an **optional Ollama** Q&A endpoint.

## Features
- Full CRUD: create, list/filter, view, update (PUT + PATCH), delete
- SQLite persistence (`students.db`, created automatically)
- Input validation (email format, phone, DOB in the past, at least one contact) and clean error codes (404 missing, 409 duplicate email, 422 invalid)
- Filters: `name`, `course`, `born_after`, `born_before`, plus `limit` / `offset`
- Optional `POST /ask`: natural-language questions answered by a local Ollama model, grounded in retrieved records. The model never runs SQL.
- Automated tests (pytest) and dummy seed data

## Project structure
```
app/
  main.py       API routes
  schemas.py    Pydantic validation models
  crud.py       Parameterised SQL operations
  database.py   SQLite connection + schema
  ai.py         Optional Ollama integration
tests/test_api.py
seed.py         Dummy sample data
requirements.txt
```

## Prerequisites
- Python 3.10+
- (Optional, for AI bonus) [Ollama](https://ollama.com) installed

## Installation
```bash
git clone <your-repo-url>
cd students-crud
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python seed.py                    # optional: load 5 dummy students
uvicorn app.main:app --reload
```
Open **http://127.0.0.1:8000/docs** for interactive Swagger UI.

## Student fields
| Field | Required | Notes |
|---|---|---|
| id | auto | unique, auto-increment |
| name | yes | 2-100 chars |
| date_of_birth | yes | `YYYY-MM-DD`, must be in the past |
| email / phone | at least one | email must be unique |
| course, address, enrollment_date | no | |

## API endpoints
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/students` | Create a student (201) |
| GET | `/students` | List / filter students |
| GET | `/students/{id}` | View one student |
| PUT | `/students/{id}` | Full update |
| PATCH | `/students/{id}` | Partial update |
| DELETE | `/students/{id}` | Delete (204) |
| POST | `/ask` | Optional AI Q&A (needs Ollama) |

## Testing the API (curl)
```bash
# Create
curl -X POST http://127.0.0.1:8000/students -H "Content-Type: application/json" \
  -d '{"name":"Aarav Sharma","date_of_birth":"2004-05-17","email":"aarav@example.com","phone":"+91 90000 00001","course":"BCA"}'

# List + filter
curl "http://127.0.0.1:8000/students"
curl "http://127.0.0.1:8000/students?course=BCA&born_after=2004-01-01"

# View one
curl http://127.0.0.1:8000/students/1

# Partial update
curl -X PATCH http://127.0.0.1:8000/students/1 -H "Content-Type: application/json" -d '{"course":"MCA"}'

# Delete
curl -X DELETE http://127.0.0.1:8000/students/1
```

### Run automated tests
```bash
pytest -q
```

## Optional: AI questions with Ollama
```bash
ollama pull llama3.2:1b
ollama serve                      # if not already running
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" \
  -d '{"question":"List students born after 2005"}'
```
**How it stays safe and accurate:** backend code detects the intent (total count, `born after/before <year>`, a course name), fetches matching rows with fixed parameterised queries, and passes only those records to the model as context. The model is told to answer only from that data, and it has no database access. If Ollama is not running, `/ask` returns `503` with instructions; the CRUD API is unaffected.

Configure with env vars: `OLLAMA_URL` (default `http://localhost:11434`), `OLLAMA_MODEL` (default `llama3.2:1b`), `STUDENTS_DB` (default `students.db`).

## Notes
- Only dummy data is included. `.gitignore` excludes `*.db`, `.env` and virtual environments. No secrets are stored in the repo.
