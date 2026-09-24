import re

import pydantic


class UserRegisterSchema(pydantic.BaseModel):
    username: str = pydantic.Field(..., min_length=3, max_length=20)
    email: str
    password: str = pydantic.Field(..., min_length=8)

    @pydantic.field_validator("username")
    @classmethod
    def username_alphanumeric(cls, value):
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise ValueError(
                "Username must contain only letters, numbers, and underscores"
            )
        return value

    @pydantic.field_validator("password")
    @classmethod
    def password_complexity(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must include at least one uppercase letter.")
        if not re.search(r"\d", value):
            raise ValueError("Password must include at least one number.")
        if not re.search(r"[@#$%^&*]", value):
            raise ValueError(
                "Password must include at least one special character from @#$%^&*."
            )
        return value

    @pydantic.field_validator("email")
    @classmethod
    def email_valid(cls, value):
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            raise ValueError("Invalid email address.")
        return value


class BorrowedItemSchema(pydantic.BaseModel):
    student_name: str = pydantic.Field(..., min_length=2, max_length=100)
    student_id: str = pydantic.Field(..., min_length=3, max_length=30)
    item_id: int = pydantic.Field(..., gt=0)
    quantity: int = pydantic.Field(..., gt=0)
    repayment_due_date: str = pydantic.Field(..., min_length=8, max_length=10)

    @pydantic.field_validator("student_name")
    @classmethod
    def student_name_valid(cls, value):
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z .'-]*", value):
            raise ValueError("Student name must contain letters and valid spacing.")
        return value

    @pydantic.field_validator("student_id")
    @classmethod
    def student_id_valid(cls, value):
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9-]+", value):
            raise ValueError("Student ID must contain only letters, numbers, and hyphens.")
        return value

    @pydantic.field_validator("repayment_due_date")
    @classmethod
    def repayment_due_date_valid(cls, value):
        value = value.strip()
        try:
            from datetime import datetime

            parsed = datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Repayment date must use YYYY-MM-DD format.") from exc
        if parsed.date() < __import__("datetime").date.today():
            raise ValueError("Repayment date cannot be in the past.")
        return value
