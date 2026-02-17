from fastapi import APIRouter

from app.routers.admin import audit_logs, departments, groups, permissions, roles, users

router = APIRouter(prefix="/api/admin", tags=["admin"])

router.include_router(users.router)
router.include_router(roles.router)
router.include_router(groups.router)
router.include_router(departments.router)
router.include_router(permissions.router)
router.include_router(audit_logs.router)
