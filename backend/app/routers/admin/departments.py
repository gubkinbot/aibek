import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_client_ip, require_permission
from app.models.department import Department
from app.models.user import User
from app.schemas.admin import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentTreeResponse,
    DepartmentUpdate,
    SetGroupMembersRequest,
)
from app.services.audit import log_action

router = APIRouter(prefix="/departments", tags=["admin-departments"])


def _build_tree(departments: list[Department], parent_id: uuid.UUID | None = None) -> list[DepartmentTreeResponse]:
    tree = []
    for dept in departments:
        if dept.parent_id == parent_id:
            node = DepartmentTreeResponse(
                id=dept.id,
                name=dept.name,
                description=dept.description,
                parent_id=dept.parent_id,
                created_at=dept.created_at,
                user_count=len(dept.users),
                children=_build_tree(departments, dept.id),
            )
            tree.append(node)
    return tree


@router.get("/", response_model=list[DepartmentTreeResponse])
async def list_departments(
    current_user: User = Depends(require_permission("departments.view")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Department).order_by(Department.name))
    departments = result.scalars().unique().all()
    return _build_tree(list(departments))


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreate,
    request: Request,
    current_user: User = Depends(require_permission("departments.manage")),
    db: AsyncSession = Depends(get_db),
):
    if data.parent_id:
        parent = await db.execute(select(Department).where(Department.id == data.parent_id))
        if not parent.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Родительское подразделение не найдено")

    dept = Department(name=data.name, description=data.description, parent_id=data.parent_id)
    db.add(dept)
    await db.flush()

    await log_action(db, current_user.id, "department.create", "department", dept.id, ip_address=get_client_ip(request))
    await db.commit()
    await db.refresh(dept)

    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        parent_id=dept.parent_id,
        created_at=dept.created_at,
        user_count=len(dept.users),
    )


@router.patch("/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: uuid.UUID,
    data: DepartmentUpdate,
    request: Request,
    current_user: User = Depends(require_permission("departments.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Подразделение не найдено")

    changes = {}
    if data.name is not None:
        changes["name"] = {"old": dept.name, "new": data.name}
        dept.name = data.name
    if data.description is not None:
        changes["description"] = {"old": dept.description, "new": data.description}
        dept.description = data.description
    if data.parent_id is not None:
        if data.parent_id == dept.id:
            raise HTTPException(status_code=400, detail="Подразделение не может быть родителем самого себя")
        if data.parent_id != uuid.UUID(int=0):
            parent = await db.execute(select(Department).where(Department.id == data.parent_id))
            if not parent.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Родительское подразделение не найдено")
            dept.parent_id = data.parent_id
        else:
            dept.parent_id = None

    if changes:
        await log_action(db, current_user.id, "department.edit", "department", dept.id, details=changes, ip_address=get_client_ip(request))

    await db.commit()
    await db.refresh(dept)

    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        parent_id=dept.parent_id,
        created_at=dept.created_at,
        user_count=len(dept.users),
    )


@router.delete("/{dept_id}")
async def delete_department(
    dept_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission("departments.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Подразделение не найдено")

    if dept.children:
        raise HTTPException(status_code=400, detail="Нельзя удалить подразделение с дочерними подразделениями")

    if dept.users:
        raise HTTPException(status_code=400, detail="Нельзя удалить подразделение с сотрудниками")

    await log_action(
        db, current_user.id, "department.delete", "department", dept.id,
        details={"name": dept.name}, ip_address=get_client_ip(request),
    )
    await db.delete(dept)
    await db.commit()
    return {"message": f"Подразделение «{dept.name}» удалено"}


@router.put("/{dept_id}/members", response_model=DepartmentResponse)
async def set_department_members(
    dept_id: uuid.UUID,
    data: SetGroupMembersRequest,
    request: Request,
    current_user: User = Depends(require_permission("departments.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Подразделение не найдено")

    result = await db.execute(select(User).where(User.id.in_(data.user_ids)))
    new_members = result.scalars().unique().all()

    old_count = len(dept.users)
    dept.users = list(new_members)

    await log_action(
        db, current_user.id, "department.members.set", "department", dept.id,
        details={"old_count": old_count, "new_count": len(new_members)},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(dept)

    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        parent_id=dept.parent_id,
        created_at=dept.created_at,
        user_count=len(dept.users),
    )
