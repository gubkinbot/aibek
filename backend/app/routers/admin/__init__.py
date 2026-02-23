"""Агрегация всех admin-роутеров."""
from fastapi import APIRouter

from app.routers.admin import audit_logs, module_access, permissions, system, users

router = APIRouter(prefix="/api/admin", tags=["admin"])

router.include_router(users.router)
router.include_router(permissions.router)
router.include_router(audit_logs.router)
router.include_router(system.router)
router.include_router(module_access.router)
