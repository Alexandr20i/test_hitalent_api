from datetime import date

from app.config import logger
from app.exceptions import NotFoundError
from app.models.employee import Employee
from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository


class EmployeeService:

    def __init__(
        self,
        department_repo: DepartmentRepository,
        employee_repo: EmployeeRepository,
    ) -> None:
        self.department_repo = department_repo
        self.employee_repo = employee_repo

    async def create(
        self,
        department_id: int,
        full_name: str,
        position: str,
        hired_at: date | None,
    ) -> Employee:
        department = await self.department_repo.get_by_id(department_id)
        if department is None:
            raise NotFoundError("Department", department_id)

        employee = await self.employee_repo.create(
            department_id=department_id,
            full_name=full_name,
            position=position,
            hired_at=hired_at,
        )
        logger.info(
            "Создан сотрудник id=%d full_name=%r department_id=%d",
            employee.id, employee.full_name, employee.department_id,
        )
        return employee