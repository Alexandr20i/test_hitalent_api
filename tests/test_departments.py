import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

async def test_create_root_department(client: AsyncClient):
    response = await client.post("/departments/", json={"name": "Engineering"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Engineering"
    assert data["parent_id"] is None
    assert "id" in data
    assert "created_at" in data


async def test_create_child_department(client: AsyncClient):
    parent = await client.post("/departments/", json={"name": "Engineering"})
    parent_id = parent.json()["id"]

    response = await client.post(
        "/departments/",
        json={"name": "Backend", "parent_id": parent_id},
    )
    assert response.status_code == 201
    assert response.json()["parent_id"] == parent_id


async def test_create_department_nonexistent_parent(client: AsyncClient):
    response = await client.post(
        "/departments/",
        json={"name": "Ghost", "parent_id": 99999},
    )
    assert response.status_code == 404


async def test_create_department_duplicate_name_same_parent(client: AsyncClient):
    parent = await client.post("/departments/", json={"name": "Engineering"})
    parent_id = parent.json()["id"]

    await client.post("/departments/", json={"name": "Backend", "parent_id": parent_id})
    response = await client.post(
        "/departments/",
        json={"name": "Backend", "parent_id": parent_id},
    )
    assert response.status_code == 409


async def test_create_department_same_name_different_parents(client: AsyncClient):
    """Одинаковое имя допустимо в разных родителях."""
    parent1 = await client.post("/departments/", json={"name": "Division A"})
    parent2 = await client.post("/departments/", json={"name": "Division B"})

    r1 = await client.post(
        "/departments/",
        json={"name": "Backend", "parent_id": parent1.json()["id"]},
    )
    r2 = await client.post(
        "/departments/",
        json={"name": "Backend", "parent_id": parent2.json()["id"]},
    )
    assert r1.status_code == 201
    assert r2.status_code == 201


async def test_create_department_empty_name(client: AsyncClient):
    response = await client.post("/departments/", json={"name": ""})
    assert response.status_code == 422


async def test_create_department_whitespace_name(client: AsyncClient):
    response = await client.post("/departments/", json={"name": "   "})
    assert response.status_code == 422


async def test_create_department_name_is_trimmed(client: AsyncClient):
    response = await client.post("/departments/", json={"name": "  HR  "})
    assert response.status_code == 201
    assert response.json()["name"] == "HR"


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------

async def test_get_department(client: AsyncClient):
    created = await client.post("/departments/", json={"name": "Engineering"})
    dept_id = created.json()["id"]

    response = await client.get(f"/departments/{dept_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dept_id
    assert data["name"] == "Engineering"
    assert "employees" in data
    assert "children" in data


async def test_get_department_not_found(client: AsyncClient):
    response = await client.get("/departments/99999")
    assert response.status_code == 404


async def test_get_department_with_children_depth(client: AsyncClient):
    root = await client.post("/departments/", json={"name": "Root"})
    root_id = root.json()["id"]

    child = await client.post(
        "/departments/",
        json={"name": "Child", "parent_id": root_id},
    )
    child_id = child.json()["id"]

    grandchild = await client.post(
        "/departments/",
        json={"name": "Grandchild", "parent_id": child_id},
    )
    grandchild_id = grandchild.json()["id"]

    # depth=1 — видим только Child, Grandchild не виден
    r1 = await client.get(f"/departments/{root_id}?depth=1")
    assert r1.status_code == 200
    children = r1.json()["children"]
    assert len(children) == 1
    assert children[0]["id"] == child_id
    assert children[0]["children"] == []

    # depth=2 — видим Child и Grandchild
    r2 = await client.get(f"/departments/{root_id}?depth=2")
    assert r2.status_code == 200
    children = r2.json()["children"]
    assert children[0]["children"][0]["id"] == grandchild_id


async def test_get_department_without_employees(client: AsyncClient):
    created = await client.post("/departments/", json={"name": "Engineering"})
    dept_id = created.json()["id"]

    await client.post(
        f"/departments/{dept_id}/employees/",
        json={"full_name": "Alice", "position": "Dev"},
    )

    response = await client.get(f"/departments/{dept_id}?include_employees=false")
    assert response.status_code == 200
    assert response.json()["employees"] == []


async def test_get_department_depth_exceeds_max(client: AsyncClient):
    created = await client.post("/departments/", json={"name": "Engineering"})
    dept_id = created.json()["id"]

    response = await client.get(f"/departments/{dept_id}?depth=6")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

async def test_update_department_name(client: AsyncClient):
    created = await client.post("/departments/", json={"name": "Old Name"})
    dept_id = created.json()["id"]

    response = await client.patch(
        f"/departments/{dept_id}",
        json={"name": "New Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


async def test_update_department_move_to_parent(client: AsyncClient):
    parent = await client.post("/departments/", json={"name": "Parent"})
    parent_id = parent.json()["id"]
    child = await client.post("/departments/", json={"name": "Child"})
    child_id = child.json()["id"]

    response = await client.patch(
        f"/departments/{child_id}",
        json={"parent_id": parent_id},
    )
    assert response.status_code == 200
    assert response.json()["parent_id"] == parent_id


async def test_update_department_self_parent(client: AsyncClient):
    created = await client.post("/departments/", json={"name": "Engineering"})
    dept_id = created.json()["id"]

    response = await client.patch(
        f"/departments/{dept_id}",
        json={"parent_id": dept_id},
    )
    assert response.status_code == 422


async def test_update_department_cycle(client: AsyncClient):
    """Нельзя переместить родителя внутрь своего поддерева."""
    root = await client.post("/departments/", json={"name": "Root"})
    root_id = root.json()["id"]

    child = await client.post(
        "/departments/",
        json={"name": "Child", "parent_id": root_id},
    )
    child_id = child.json()["id"]

    grandchild = await client.post(
        "/departments/",
        json={"name": "Grandchild", "parent_id": child_id},
    )
    grandchild_id = grandchild.json()["id"]

    # Пытаемся переместить Root внутрь Grandchild — цикл
    response = await client.patch(
        f"/departments/{root_id}",
        json={"parent_id": grandchild_id},
    )
    assert response.status_code == 409


async def test_update_department_not_found(client: AsyncClient):
    response = await client.patch(
        "/departments/99999",
        json={"name": "Ghost"},
    )
    assert response.status_code == 404


async def test_update_department_duplicate_name_in_parent(client: AsyncClient):
    parent = await client.post("/departments/", json={"name": "Engineering"})
    parent_id = parent.json()["id"]

    await client.post(
        "/departments/",
        json={"name": "Backend", "parent_id": parent_id},
    )
    other = await client.post(
        "/departments/",
        json={"name": "Frontend", "parent_id": parent_id},
    )
    other_id = other.json()["id"]

    response = await client.patch(
        f"/departments/{other_id}",
        json={"name": "Backend"},
    )
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

async def test_delete_department_cascade(client: AsyncClient):
    parent = await client.post("/departments/", json={"name": "Engineering"})
    parent_id = parent.json()["id"]

    child = await client.post(
        "/departments/",
        json={"name": "Backend", "parent_id": parent_id},
    )
    child_id = child.json()["id"]

    await client.post(
        f"/departments/{child_id}/employees/",
        json={"full_name": "Alice", "position": "Dev"},
    )

    response = await client.delete(f"/departments/{parent_id}?mode=cascade")
    assert response.status_code == 204

    assert (await client.get(f"/departments/{parent_id}")).status_code == 404
    assert (await client.get(f"/departments/{child_id}")).status_code == 404


async def test_delete_department_reassign(client: AsyncClient):
    source = await client.post("/departments/", json={"name": "Source"})
    source_id = source.json()["id"]
    target = await client.post("/departments/", json={"name": "Target"})
    target_id = target.json()["id"]

    emp = await client.post(
        f"/departments/{source_id}/employees/",
        json={"full_name": "Bob", "position": "QA"},
    )
    emp_id = emp.json()["id"]

    response = await client.delete(
        f"/departments/{source_id}?mode=reassign&reassign_to_department_id={target_id}"
    )
    assert response.status_code == 204

    # Отдел удалён
    assert (await client.get(f"/departments/{source_id}")).status_code == 404

    # Сотрудник переведён в target
    target_data = await client.get(f"/departments/{target_id}?include_employees=true")
    employee_ids = [e["id"] for e in target_data.json()["employees"]]
    assert emp_id in employee_ids


async def test_delete_department_reassign_without_target(client: AsyncClient):
    dept = await client.post("/departments/", json={"name": "Engineering"})
    dept_id = dept.json()["id"]

    response = await client.delete(f"/departments/{dept_id}?mode=reassign")
    assert response.status_code == 422


async def test_delete_department_not_found(client: AsyncClient):
    response = await client.delete("/departments/99999?mode=cascade")
    assert response.status_code == 404


async def test_delete_department_invalid_mode(client: AsyncClient):
    dept = await client.post("/departments/", json={"name": "Engineering"})
    dept_id = dept.json()["id"]

    response = await client.delete(f"/departments/{dept_id}?mode=wrong")
    assert response.status_code == 422