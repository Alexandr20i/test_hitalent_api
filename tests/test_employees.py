import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_create_employee(client: AsyncClient):
    dept = await client.post("/departments/", json={"name": "Engineering"})
    dept_id = dept.json()["id"]

    response = await client.post(
        f"/departments/{dept_id}/employees/",
        json={"full_name": "Alice Smith", "position": "Backend Developer"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Alice Smith"
    assert data["position"] == "Backend Developer"
    assert data["department_id"] == dept_id
    assert data["hired_at"] is None


async def test_create_employee_with_hired_at(client: AsyncClient):
    dept = await client.post("/departments/", json={"name": "Engineering"})
    dept_id = dept.json()["id"]

    response = await client.post(
        f"/departments/{dept_id}/employees/",
        json={
            "full_name": "Bob Jones",
            "position": "QA Engineer",
            "hired_at": "2023-06-01",
        },
    )
    assert response.status_code == 201
    assert response.json()["hired_at"] == "2023-06-01"


async def test_create_employee_nonexistent_department(client: AsyncClient):
    response = await client.post(
        "/departments/99999/employees/",
        json={"full_name": "Ghost", "position": "Nobody"},
    )
    assert response.status_code == 404


async def test_create_employee_empty_full_name(client: AsyncClient):
    dept = await client.post("/departments/", json={"name": "Engineering"})
    dept_id = dept.json()["id"]

    response = await client.post(
        f"/departments/{dept_id}/employees/",
        json={"full_name": "", "position": "Dev"},
    )
    assert response.status_code == 422


async def test_create_employee_whitespace_position(client: AsyncClient):
    dept = await client.post("/departments/", json={"name": "Engineering"})
    dept_id = dept.json()["id"]

    response = await client.post(
        f"/departments/{dept_id}/employees/",
        json={"full_name": "Alice", "position": "   "},
    )
    assert response.status_code == 422


async def test_create_employee_fields_are_trimmed(client: AsyncClient):
    dept = await client.post("/departments/", json={"name": "Engineering"})
    dept_id = dept.json()["id"]

    response = await client.post(
        f"/departments/{dept_id}/employees/",
        json={"full_name": "  Alice Smith  ", "position": "  Dev  "},
    )
    assert response.status_code == 201
    assert response.json()["full_name"] == "Alice Smith"
    assert response.json()["position"] == "Dev"


async def test_employees_visible_in_department(client: AsyncClient):
    dept = await client.post("/departments/", json={"name": "Engineering"})
    dept_id = dept.json()["id"]

    await client.post(
        f"/departments/{dept_id}/employees/",
        json={"full_name": "Alice", "position": "Dev"},
    )
    await client.post(
        f"/departments/{dept_id}/employees/",
        json={"full_name": "Bob", "position": "QA"},
    )

    response = await client.get(f"/departments/{dept_id}?include_employees=true")
    assert response.status_code == 200
    employees = response.json()["employees"]
    assert len(employees) == 2
    names = {e["full_name"] for e in employees}
    assert names == {"Alice", "Bob"}