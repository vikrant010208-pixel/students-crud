"""Optional bonus: answer natural-language questions with a local Ollama model.

Safety design (per assignment):
  * The model NEVER writes or runs SQL.
  * Backend code decides which records to fetch (count, year filters, course)
    using fixed, parameterised queries, then passes them to the model as context.
  * The model is told to answer only from that context.
"""
import json
import os
import re
import urllib.error
import urllib.request
from datetime import date

from . import crud

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
MAX_RECORDS = 50


class OllamaUnavailable(Exception):
    pass


def retrieve_context(question: str) -> tuple[int, list[dict], list[str]]:
    """Return (total_count, matching_records, notes describing the filters used)."""
    q = question.lower()
    total = crud.count_students()
    notes, filters = [], {}

    m = re.search(r"born\s+(?:after|since)\s+(\d{4})", q)
    if m:  # "born after 2005" -> DOB later than 31 Dec 2005
        filters["born_after"] = date(int(m.group(1)), 12, 31)
        notes.append(f"born after year {m.group(1)} (DOB from {int(m.group(1)) + 1}-01-01)")
    m = re.search(r"born\s+before\s+(\d{4})", q)
    if m:
        filters["born_before"] = date(int(m.group(1)), 1, 1)
        notes.append(f"born before year {m.group(1)}")

    # Match a known course name mentioned in the question.
    for s in crud.list_students(limit=1000):
        c = (s.get("course") or "").strip()
        if c and c.lower() in q and "course" not in filters:
            filters["course"] = c
            notes.append(f"course = {c}")

    records = crud.list_students(limit=MAX_RECORDS, **filters)
    return total, records, notes


def build_prompt(question: str, total: int, records: list[dict], notes: list[str]) -> str:
    lines = [
        f"- id={r['id']}, name={r['name']}, dob={r['date_of_birth']}, "
        f"course={r['course'] or 'N/A'}, enrolled={r['enrollment_date'] or 'N/A'}"
        for r in records
    ]
    return (
        "You are an assistant for a student database. Answer ONLY using the data below. "
        "If the answer is not in the data, say you don't know. Be brief and accurate.\n\n"
        f"Total students in database: {total}\n"
        f"Filters already applied by the system: {', '.join(notes) or 'none'}\n"
        f"Matching records ({len(records)}):\n" + ("\n".join(lines) or "(none)") +
        f"\n\nQuestion: {question}\nAnswer:"
    )


def ask_ollama(prompt: str) -> str:
    body = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0},
    }).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())["message"]["content"].strip()
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
        raise OllamaUnavailable(str(exc))


def answer_question(question: str) -> tuple[str, int]:
    total, records, notes = retrieve_context(question)
    return ask_ollama(build_prompt(question, total, records, notes)), len(records)
