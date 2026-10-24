import sqlite3
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from .. import crud
from ..database import get_db
from ..schemas import StudentCreate, StudentOut, StudentUpdate

router = APIRouter(prefix="/students", tags=["Students"])

NOT_FOUND = "Student not found"
DUPLICATE = "A student with this email already exists"


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED,
             summary="Create a student")
def create_student(payload: StudentCreate, db: sqlite3.Connection = Depends(get_db)):
    try:
        return crud.create_student(db, payload.model_dump(mode="json"))
    except crud.DuplicateEmailError:
        raise HTTPException(status.HTTP_409_CONFLICT, DUPLICATE)


@router.get("", response_model=list[StudentOut], summary="List / filter students")
def list_students(
    name: str | None = Query(None, description="Partial name match"),
    course: str | None = Query(None, description="Partial course match"),
    born_after: date | None = Query(None, description="DOB strictly after YYYY-MM-DD"),
    born_before: date | None = Query(None, description="DOB strictly before YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: sqlite3.Connection = Depends(get_db),
):
    return crud.list_students(db, name=name, course=course, born_after=born_after,
                              born_before=born_before, limit=limit, offset=offset)


@router.get("/{student_id}", response_model=StudentOut, summary="View a student")
def get_student(student_id: int, db: sqlite3.Connection = Depends(get_db)):
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return student


@router.put("/{student_id}", response_model=StudentOut,
            summary="Replace a student (full update)")
def replace_student(student_id: int, payload: StudentCreate,
                    db: sqlite3.Connection = Depends(get_db)):
    try:
        student = crud.update_student(db, student_id, payload.model_dump(mode="json"))
    except crud.DuplicateEmailError:
        raise HTTPException(status.HTTP_409_CONFLICT, DUPLICATE)
    if not student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return student


@router.patch("/{student_id}", response_model=StudentOut,
              summary="Update some fields of a student")
def patch_student(student_id: int, payload: StudentUpdate,
                  db: sqlite3.Connection = Depends(get_db)):
    existing = crud.get_student(db, student_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    changes = payload.model_dump(mode="json", exclude_unset=True)
    merged = {**existing, **changes}
    if not merged.get("email") and not merged.get("phone"):
        raise HTTPException(422,
                            "A student must keep at least one of: email, phone")
    try:
        return crud.update_student(db, student_id, changes)
    except crud.DuplicateEmailError:
        raise HTTPException(status.HTTP_409_CONFLICT, DUPLICATE)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a student")
def delete_student(student_id: int, db: sqlite3.Connection = Depends(get_db)):
    if not crud.delete_student(db, student_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
