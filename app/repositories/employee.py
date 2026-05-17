from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee

from datetime import date


class EmployeeRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, employee_id: int) -> Employee | None:
        result = await self.session.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        return result.scalar_one_or_none()

    async def get_by_department(
        self,
        department_id: int,
        order_by: str = "created_at",
    ) -> list[Employee]:
        order_col = (
            Employee.full_name
            if order_by == "full_name"
            else Employee.created_at
        )
        result = await self.session.execute(
            select(Employee)
            .where(Employee.department_id == department_id)
            .order_by(order_col)
        )
        return list(result.scalars().all())

    async def create(
        self,
        department_id: int,
        full_name: str,
        position: str,
        hired_at: date | None,
    ) -> Employee:
        employee = Employee(
            department_id=department_id,
            full_name=full_name,
            position=position,
            hired_at=hired_at,
        )
        self.session.add(employee)
        await self.session.flush()
        await self.session.refresh(employee)
        return employee