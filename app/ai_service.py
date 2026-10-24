"""Optional bonus: answer natural-language questions with a local Ollama model.

Safety design:
  * The model NEVER sees or writes SQL. Our own code decides which records to fetch
    (using fixed, parameterised queries in crud.py).
  * The fetched records are given to the model as context, and the prompt tells it
    to answer only from that context.
"""
import os
import re
import sqlite3

import httpx

from . import crud


def ollama_url() -> str:
    return os.getenv("OLLAMA_URL", "http://localhost:11434")


def ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3.2:1b")


MAX_RECORDS = 50

SYSTEM_PROMPT = (
    "You answer questions about a student database. Use ONLY the CONTEXT provided. "
    "Do not invent students or facts. If the answer is not in the context, say you "
    "don't know. Trust the numbers stated in the context. Be concise."
)


class OllamaUnavailable(Exception):
    pass


def retrieve(conn: sqlite3.Connection, question: str) -> tuple[list[dict], dict]:
    """Rule-based retrieval: turn the question into safe filters. Returns (records, filters)."""
    q = question.lower()
    filters: dict = {}

    m = re.search(r"born\s+(after|before|in)\s+(\d{4})", q)
    if m:
        kind, year = m.group(1), int(m.group(2))
        if kind == "after":
            filters["born_after"] = f"{year}-12-31"
        elif kind == "before":
            filters["born_before"] = f"{year}-01-01"
        else:
            filters["born_after"] = f"{year - 1}-12-31"
            filters["born_before"] = f"{year + 1}-01-01"

    for course in crud.distinct_courses(conn):
        if course.lower() in q:
            filters["course"] = course
            break

    if not filters:  # try matching a student's name
        for s in crud.list_students(conn, limit=500):
            tokens = [t for t in re.split(r"\s+", s["name"].lower()) if len(t) > 2]
            if s["name"].lower() in q or any(re.search(rf"\b{re.escape(t)}\b", q) for t in tokens):
                filters["name"] = s["name"]
                break

    records = crud.list_students(conn, limit=MAX_RECORDS, **filters)
    return records, filters


def build_context(conn, records: list[dict], filters: dict) -> str:
    total = crud.count_students(conn)
    matched = crud.count_students(conn, **filters)
    lines = [f"Total students in database: {total}",
             f"Students matching the question's filters: {matched}",
             "Records:"]
    for s in records:
        lines.append(
            f"- id={s['id']}, name={s['name']}, dob={s['date_of_birth']}, "
            f"course={s['course'] or 'n/a'}, email={s['email'] or 'n/a'}, "
            f"phone={s['phone'] or 'n/a'}, enrolled={s['enrollment_date'] or 'n/a'}")
    if matched > len(records):
        lines.append(f"(only the first {len(records)} of {matched} records are shown)")
    return "\n".join(lines)


def ask_ollama(question: str, context: str) -> str:
    payload = {
        "model": ollama_model(),
        "stream": False,
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {question}"},
        ],
    }
    try:
        r = httpx.post(f"{ollama_url()}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
    except httpx.ConnectError as exc:
        raise OllamaUnavailable(
            f"Cannot reach Ollama at {ollama_url()}. Start it with `ollama serve`.") from exc
    except httpx.HTTPStatusError as exc:
        raise OllamaUnavailable(
            f"Ollama error {exc.response.status_code}. Is the model pulled? "
            f"Run `ollama pull {ollama_model()}`.") from exc
    except httpx.HTTPError as exc:
        raise OllamaUnavailable(f"Ollama request failed: {exc}") from exc
    return r.json()["message"]["content"].strip()


def answer_question(conn: sqlite3.Connection, question: str) -> dict:
    records, filters = retrieve(conn, question)
    context = build_context(conn, records, filters)
    answer = ask_ollama(question, context)
    return {"question": question, "answer": answer, "model": ollama_model(),
            "total_students": crud.count_students(conn), "records_used": records}
