"""Pydantic models: request validation and response shapes."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

PHONE_CHARS = set("0123456789+-() ")


class StudentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Aarav Sharma"])
    date_of_birth: date = Field(..., examples=["2004-05-17"])
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, examples=["+91 98765 43210"])
    course: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    enrollment_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("name must have at least 2 characters")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_future(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("date_of_birth must be in the past")
        return v

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        digits = [c for c in v if c.isdigit()]
        if not set(v) <= PHONE_CHARS or not 7 <= len(digits) <= 15:
            raise ValueError("phone must contain 7-15 digits (allowed: + - ( ) space)")
        return v

    @model_validator(mode="after")
    def needs_contact(self):
        if not self.email and not self.phone:
            raise ValueError("provide at least one contact: email and/or phone")
        return self


class StudentUpdate(BaseModel):
    """All fields optional - used by PATCH."""
    name: Optional[str] = None
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[date] = None


class StudentOut(BaseModel):
    id: int
    name: str
    date_of_birth: date
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[date] = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500,
                          examples=["How many students are there?"])


class AskResponse(BaseModel):
    question: str
    answer: str
    records_used: int
