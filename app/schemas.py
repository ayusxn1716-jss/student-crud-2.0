"""Pydantic models: request validation and response shapes."""
from datetime import date

from pydantic import (BaseModel, ConfigDict, EmailStr, Field,
                      field_validator, model_validator)

PHONE_PATTERN = r"^\+?[0-9\s\-]{7,15}$"


def _not_future(v: date | None) -> date | None:
    if v is not None and v > date.today():
        raise ValueError("date cannot be in the future")
    return v


class StudentBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    email: EmailStr | None = None
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    course: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    enrollment_date: date | None = None

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be blank")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def _dob_valid(cls, v: date) -> date:
        return _not_future(v)

    @model_validator(mode="after")
    def _need_contact(self):
        if not self.email and not self.phone:
            raise ValueError("provide at least one of: email, phone")
        return self


class StudentCreate(StudentBase):
    """Used for POST and PUT (full record)."""


class StudentUpdate(BaseModel):
    """Used for PATCH: every field optional."""
    name: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    course: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    enrollment_date: date | None = None

    @field_validator("name", "date_of_birth", mode="before")
    @classmethod
    def _required_not_null(cls, v):
        if v is None:
            raise ValueError("this field cannot be set to null")
        return v

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("name cannot be blank")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def _dob_valid(cls, v):
        return _not_future(v)


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    date_of_birth: date
    email: str | None = None
    phone: str | None = None
    course: str | None = None
    address: str | None = None
    enrollment_date: date | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    total_students: int
    records_used: list[StudentOut]
