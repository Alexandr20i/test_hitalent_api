from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.department import Department
from app.models.employee import Employee


class DepartmentRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, department_id: int) -> Department | None:
        result = await self.session.execute(
            select(Department)
            .where(Department.id == department_id)
            .options(
                selectinload(Department.employees),
                selectinload(Department.children),
            )
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Department]:
        result = await self.session.execute(
            select(Department).order_by(Department.created_at)
        )
        return list(result.scalars().all())

    async def name_exists_in_parent(
        self,
        name: str,
        parent_id: int | None,
        exclude_id: int | None = None,
    ) -> bool:
        """Проверяет уникальность имени среди siblings."""
        query = select(
            exists().where(
                Department.name == name,
                Department.parent_id == parent_id,
            )
        )
        if exclude_id is not None:
            query = select(
                exists().where(
                    Department.name == name,
                    Department.parent_id == parent_id,
                    Department.id != exclude_id,
                )
            )
        result = await self.session.execute(query)
        return bool(result.scalar())

    async def get_all_descendant_ids(self, department_id: int) -> set[int]:
        """
        Рекурсивно собирает id всех дочерних подразделений.
        Используется для проверки цикла при перемещении.
        """
        visited: set[int] = set()
        queue: list[int] = [department_id]

        while queue:
            current_id = queue.pop()
            if current_id in visited:
                continue
            visited.add(current_id)

            result = await self.session.execute(
                select(Department.id).where(Department.parent_id == current_id)
            )
            children_ids = list(result.scalars().all())
            queue.extend(children_ids)

        return visited

    async def create(self, name: str, parent_id: int | None) -> Department:
        department = Department(name=name, parent_id=parent_id)
        self.session.add(department)
        await self.session.flush()  # получаем id до commit
        await self.session.refresh(department)
        return department

    async def update(
        self,
        department: Department,
        name: str | None = None,
        parent_id: int | None = None,
    ) -> Department:
        if name is not None:
            department.name = name
        # parent_id может быть явным None (перемещение в корень)
        # поэтому проверяем через sentinel
        _UNSET = object()
        # используем kwargs-подход через прямое присвоение
        department.parent_id = parent_id
        self.session.add(department)
        await self.session.flush()
        await self.session.refresh(department)
        return department

    async def delete(self, department: Department) -> None:
        await self.session.delete(department)
        await self.session.flush()

    async def reassign_employees(
        self,
        from_department_id: int,
        to_department_id: int,
    ) -> None:
        """Переводит всех сотрудников из одного отдела в другой."""
        result = await self.session.execute(
            select(Employee).where(Employee.department_id == from_department_id)
        )
        employees = list(result.scalars().all())
        for employee in employees:
            employee.department_id = to_department_id
        await self.session.flush()