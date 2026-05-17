from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository
from app.schemas.department import (
    DepartmentCreate,
    DepartmentNode,
    DepartmentRead,
    DepartmentUpdate,
)
from app.schemas.employee import EmployeeCreate, EmployeeRead
from app.services.department import DepartmentService
from app.services.employee import EmployeeService

router = APIRouter(prefix="/departments", tags=["departments"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def get_department_service(session: DbSession) -> DepartmentService:
    department_repo = DepartmentRepository(session)
    employee_repo = EmployeeRepository(session)
    return DepartmentService(
        department_repo=department_repo,
        employee_repo=employee_repo,
    )


def get_employee_service(session: DbSession) -> EmployeeService:
    department_repo = DepartmentRepository(session)
    employee_repo = EmployeeRepository(session)
    return EmployeeService(
        department_repo=department_repo,
        employee_repo=employee_repo,
    )


DepartmentServiceDep = Annotated[DepartmentService, Depends(get_department_service)]
EmployeeServiceDep = Annotated[EmployeeService, Depends(get_employee_service)]


@router.post(
    "/",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать подразделение",
)
async def create_department(
    body: DepartmentCreate,
    service: DepartmentServiceDep,
) -> DepartmentRead:
    department = await service.create(
        name=body.name,
        parent_id=body.parent_id,
    )
    return DepartmentRead.model_validate(department)


@router.get(
    "/{department_id}",
    response_model=DepartmentNode,
    summary="Получить подразделение с деревом и сотрудниками",
)
async def get_department(
    department_id: int,
    service: DepartmentServiceDep,
    depth: Annotated[int, Query(ge=1, le=5)] = 1,
    include_employees: bool = True,
) -> DepartmentNode:
    return await service.get(
        department_id=department_id,
        depth=depth,
        include_employees=include_employees,
    )


@router.patch(
    "/{department_id}",
    response_model=DepartmentRead,
    summary="Обновить подразделение (имя и/или родитель)",
)
async def update_department(
    department_id: int,
    body: DepartmentUpdate,
    service: DepartmentServiceDep,
) -> DepartmentRead:
    # Определяем был ли parent_id явно передан в теле запроса
    parent_id_provided = "parent_id" in body.model_fields_set

    department = await service.update(
        department_id=department_id,
        name=body.name,
        parent_id=body.parent_id,
        parent_id_provided=parent_id_provided,
    )
    return DepartmentRead.model_validate(department)


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить подразделение",
)
async def delete_department(
    department_id: int,
    service: DepartmentServiceDep,
    mode: Annotated[str, Query(pattern="^(cascade|reassign)$")] = "cascade",
    reassign_to_department_id: int | None = None,
) -> None:
    await service.delete(
        department_id=department_id,
        mode=mode,
        reassign_to_department_id=reassign_to_department_id,
    )


@router.post(
    "/{department_id}/employees/",
    response_model=EmployeeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать сотрудника в подразделении",
)
async def create_employee(
    department_id: int,
    body: EmployeeCreate,
    service: EmployeeServiceDep,
) -> EmployeeRead:
    employee = await service.create(
        department_id=department_id,
        full_name=body.full_name,
        position=body.position,
        hired_at=body.hired_at,
    )
    return EmployeeRead.model_validate(employee)