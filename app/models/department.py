from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Связь на родителя
    parent: Mapped["Department | None"] = relationship(
        "Department",
        back_populates="children",
        remote_side="Department.id",
        lazy="selectin",
    )

    # Связь на детей
    children: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="parent",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    # Связь на сотрудников
    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="department",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Department id={self.id} name={self.name!r} parent_id={self.parent_id}>"