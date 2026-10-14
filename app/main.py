"""Students Database CRUD API - FastAPI + SQLite."""
from contextlib import asynccontextmanager
from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import ValidationError

from . import ai, crud
from .database import init_db
from .schemas import (AskRequest, AskResponse, StudentCreate, StudentOut,
                      StudentUpdate)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Students Database API",
    description="CRUD API for student records (FastAPI + SQLite) with an optional Ollama Q&A endpoint.",
    version="1.0.0",
    lifespan=lifespan,
)

NOT_FOUND = "Student not found"
DUPLICATE = "A student with this email already exists"


@app.get("/", tags=["health"])
def root():
    return {"message": "Students API is running. See /docs for interactive documentation."}


@app.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED, tags=["students"])
def create_student(student: StudentCreate):
    try:
        return crud.create_student(student.model_dump())
    except crud.DuplicateEmail:
        raise HTTPException(status.HTTP_409_CONFLICT, DUPLICATE)


@app.get("/students", response_model=list[StudentOut], tags=["students"])
def list_students(
    name: Optional[str] = Query(None, description="Partial name match"),
    course: Optional[str] = Query(None, description="Partial course match"),
    born_after: Optional[date] = Query(None, description="DOB strictly after YYYY-MM-DD"),
    born_before: Optional[date] = Query(None, description="DOB strictly before YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return crud.list_students(name, course, born_after, born_before, limit, offset)


@app.get("/students/{student_id}", response_model=StudentOut, tags=["students"])
def get_student(student_id: int):
    student = crud.get_student(student_id)
    if not student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return student


@app.put("/students/{student_id}", response_model=StudentOut, tags=["students"])
def replace_student(student_id: int, student: StudentCreate):
    """Full update: every required field must be supplied."""
    try:
        updated = crud.update_student(student_id, student.model_dump())
    except crud.DuplicateEmail:
        raise HTTPException(status.HTTP_409_CONFLICT, DUPLICATE)
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return updated


@app.patch("/students/{student_id}", response_model=StudentOut, tags=["students"])
def patch_student(student_id: int, changes: StudentUpdate):
    """Partial update: send only the fields you want to change."""
    existing = crud.get_student(student_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    merged = {**existing, **changes.model_dump(exclude_unset=True)}
    try:  # re-run full validation on the merged record
        valid = StudentCreate(**{k: v for k, v in merged.items() if k != "id"})
    except ValidationError as exc:
        raise HTTPException(422,
                            detail=[{"loc": e["loc"], "msg": e["msg"]} for e in exc.errors()])
    try:
        return crud.update_student(student_id, valid.model_dump())
    except crud.DuplicateEmail:
        raise HTTPException(status.HTTP_409_CONFLICT, DUPLICATE)


@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["students"])
def delete_student(student_id: int):
    if not crud.delete_student(student_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/ask", response_model=AskResponse, tags=["ai (optional)"])
def ask(body: AskRequest):
    """Optional bonus: ask a natural-language question about the stored students (needs Ollama)."""
    try:
        answer, used = ai.answer_question(body.question)
    except ai.OllamaUnavailable:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Ollama is not reachable. Start it with `ollama serve` and pull the model "
            f"(`ollama pull {ai.OLLAMA_MODEL}`).")
    return AskResponse(question=body.question, answer=answer, records_used=used)
