from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    parent_id: int | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Название не может состоять только из пробелов")
        return v


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: int | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_and_validate_name(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Название не может состоять только из пробелов")
        return v


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None
    created_at: datetime


class DepartmentNode(BaseModel):
    """
    Рекурсивная схема для GET /departments/{id} —
    возвращает отдел с сотрудниками и деревом дочерних отделов.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None
    created_at: datetime

    employees: list[EmployeeRead] = []
    children: list[DepartmentNode] = []


# Pydantic v2 требует явного вызова model_rebuild()
# для схем с рекурсивными ссылками на самих себя
from app.schemas.employee import EmployeeRead  # noqa: E402
DepartmentNode.model_rebuild()