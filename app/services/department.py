from app.config import logger
from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.department import Department
from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository
from app.schemas.department import DepartmentNode
from app.schemas.employee import EmployeeRead


class DepartmentService:

    def __init__(
        self,
        department_repo: DepartmentRepository,
        employee_repo: EmployeeRepository,
    ) -> None:
        self.department_repo = department_repo
        self.employee_repo = employee_repo

    async def create(
        self,
        name: str,
        parent_id: int | None,
    ) -> Department:
        # Проверяем что родитель существует
        if parent_id is not None:
            parent = await self.department_repo.get_by_id(parent_id)
            if parent is None:
                raise NotFoundError("Department", parent_id)

        # Проверяем уникальность имени среди siblings
        name_taken = await self.department_repo.name_exists_in_parent(
            name=name,
            parent_id=parent_id,
        )
        if name_taken:
            raise ConflictError(
                f"Подразделение с именем '{name}' уже существует "
                f"в родителе parent_id={parent_id}"
            )

        department = await self.department_repo.create(
            name=name,
            parent_id=parent_id,
        )
        logger.info("Создано подразделение id=%d name=%r", department.id, department.name)
        return department

    async def get(
        self,
        department_id: int,
        depth: int = 1,
        include_employees: bool = True,
    ) -> DepartmentNode:
        department = await self.department_repo.get_by_id(department_id)
        if department is None:
            raise NotFoundError("Department", department_id)

        return await self._build_node(
            department=department,
            depth=depth,
            current_depth=0,
            include_employees=include_employees,
        )

    async def _build_node(
        self,
        department: Department,
        depth: int,
        current_depth: int,
        include_employees: bool,
    ) -> DepartmentNode:
        employees: list[EmployeeRead] = []
        if include_employees:
            db_employees = await self.employee_repo.get_by_department(
                department_id=department.id,
                order_by="created_at",
            )
            employees = [EmployeeRead.model_validate(e) for e in db_employees]

        children: list[DepartmentNode] = []
        if current_depth < depth:
            for child in department.children:
                child_dept = await self.department_repo.get_by_id(child.id)
                if child_dept is not None:
                    children.append(
                        await self._build_node(
                            department=child_dept,
                            depth=depth,
                            current_depth=current_depth + 1,
                            include_employees=include_employees,
                        )
                    )

        return DepartmentNode(
            id=department.id,
            name=department.name,
            parent_id=department.parent_id,
            created_at=department.created_at,
            employees=employees,
            children=children,
        )

    async def update(
        self,
        department_id: int,
        name: str | None,
        parent_id: int | None,
        parent_id_provided: bool,
    ) -> Department:
        department = await self.department_repo.get_by_id(department_id)
        if department is None:
            raise NotFoundError("Department", department_id)

        new_name = name if name is not None else department.name
        new_parent_id = parent_id if parent_id_provided else department.parent_id

        # Нельзя сделать родителем самого себя
        if new_parent_id == department_id:
            raise ValidationError("Подразделение не может быть родителем самого себя")

        # Проверяем цикл — нельзя переместить внутрь своего поддерева
        if new_parent_id is not None:
            descendant_ids = await self.department_repo.get_all_descendant_ids(
                department_id
            )
            # убираем сам department_id из множества — нас интересуют только потомки
            descendant_ids.discard(department_id)
            if new_parent_id in descendant_ids:
                raise ConflictError(
                    "Нельзя переместить подразделение внутрь своего поддерева"
                )

            # Проверяем что новый родитель существует
            new_parent = await self.department_repo.get_by_id(new_parent_id)
            if new_parent is None:
                raise NotFoundError("Department", new_parent_id)

        # Проверяем уникальность имени среди siblings нового родителя
        name_taken = await self.department_repo.name_exists_in_parent(
            name=new_name,
            parent_id=new_parent_id,
            exclude_id=department_id,
        )
        if name_taken:
            raise ConflictError(
                f"Подразделение с именем '{new_name}' уже существует "
                f"в родителе parent_id={new_parent_id}"
            )

        updated = await self.department_repo.update(
            department=department,
            name=new_name,
            parent_id=new_parent_id,
        )
        logger.info(
            "Обновлено подразделение id=%d name=%r parent_id=%s",
            updated.id, updated.name, updated.parent_id,
        )
        return updated

    async def delete(
        self,
        department_id: int,
        mode: str,
        reassign_to_department_id: int | None,
    ) -> None:
        department = await self.department_repo.get_by_id(department_id)
        if department is None:
            raise NotFoundError("Department", department_id)

        if mode == "reassign":
            if reassign_to_department_id is None:
                raise ValidationError(
                    "reassign_to_department_id обязателен при mode=reassign"
                )
            if reassign_to_department_id == department_id:
                raise ValidationError(
                    "reassign_to_department_id не может совпадать с удаляемым подразделением"
                )

            target = await self.department_repo.get_by_id(reassign_to_department_id)
            if target is None:
                raise NotFoundError("Department", reassign_to_department_id)

            # Переводим сотрудников
            await self.department_repo.reassign_employees(
                from_department_id=department_id,
                to_department_id=reassign_to_department_id,
            )
            logger.info(
                "Сотрудники переведены из department_id=%d в department_id=%d",
                department_id, reassign_to_department_id,
            )

        elif mode == "cascade":
            # Каскадное удаление через ORM — SQLAlchemy удалит детей и сотрудников
            # благодаря cascade="all, delete-orphan" на relationships
            pass

        else:
            raise ValidationError(f"Неизвестный mode='{mode}'. Допустимые: cascade, reassign")

        await self.department_repo.delete(department)
        logger.info("Удалено подразделение id=%d mode=%s", department_id, mode)