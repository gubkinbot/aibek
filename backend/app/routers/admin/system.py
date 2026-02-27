"""Admin-роутер мониторинга системы: статус сервисов, метрики, Docker, тест-отчёт."""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil
from fastapi import APIRouter, Depends, HTTPException, Request, status as http_status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_permission
from app.models.user import User
from app.schemas.admin import DefaultAccessUpdate
from app.services.redis import redis_client

router = APIRouter(prefix="/system", tags=["admin-system"])

_process = psutil.Process(os.getpid())


def _format_bytes(b: int) -> str:
    """Форматирует байты в человекочитаемый формат (KB, MB, GB)."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(b) < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


async def _check_backend() -> dict:
    """Собирает метрики бэкенда: CPU, память, диск, время работы."""
    uptime_seconds = int(time.time() - psutil.boot_time())

    # System-level metrics
    cpu_percent = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # Process-level metrics
    proc_mem = _process.memory_info()

    return {
        "status": "ok",
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_percent": cpu_percent,
        "memory_used": mem.used,
        "memory_total": mem.total,
        "memory_percent": mem.percent,
        "memory_used_fmt": _format_bytes(mem.used),
        "memory_total_fmt": _format_bytes(mem.total),
        "disk_used": disk.used,
        "disk_total": disk.total,
        "disk_percent": disk.percent,
        "disk_used_fmt": _format_bytes(disk.used),
        "disk_total_fmt": _format_bytes(disk.total),
        "process_memory": proc_mem.rss,
        "process_memory_fmt": _format_bytes(proc_mem.rss),
    }


async def _check_database(db: AsyncSession) -> dict:
    """Собирает метрики PostgreSQL: версия, аптайм, размер БД, соединения."""
    try:
        # Version
        result = await db.execute(text("SELECT version()"))
        version = result.scalar()

        # Uptime
        result = await db.execute(
            text("SELECT EXTRACT(EPOCH FROM (now() - pg_postmaster_start_time()))::int FROM pg_stat_activity LIMIT 1")
        )
        uptime_seconds = result.scalar()

        # Database size
        result = await db.execute(text("SELECT pg_database_size(current_database())"))
        db_size = result.scalar()

        # Active connections
        result = await db.execute(text("SELECT count(*) FROM pg_stat_activity"))
        connections = result.scalar()

        # Max connections
        result = await db.execute(text("SHOW max_connections"))
        max_connections = int(result.scalar())

        return {
            "status": "ok",
            "version": version,
            "uptime_seconds": uptime_seconds,
            "db_size": db_size,
            "db_size_fmt": _format_bytes(db_size) if db_size else "-",
            "connections": connections,
            "max_connections": max_connections,
            "connections_percent": round(connections / max_connections * 100, 1) if max_connections else 0,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def _check_redis() -> dict:
    """Собирает метрики Redis: версия, память, клиенты, команды."""
    try:
        info_server = await redis_client.info("server")
        info_memory = await redis_client.info("memory")
        info_clients = await redis_client.info("clients")
        info_stats = await redis_client.info("stats")
        pong = await redis_client.ping()

        used_memory = info_memory.get("used_memory", 0)
        max_memory = info_memory.get("maxmemory", 0)

        return {
            "status": "ok" if pong else "error",
            "version": info_server.get("redis_version", "unknown"),
            "uptime_seconds": info_server.get("uptime_in_seconds"),
            "memory_used": used_memory,
            "memory_used_fmt": _format_bytes(used_memory),
            "memory_max": max_memory,
            "memory_max_fmt": _format_bytes(max_memory) if max_memory else "unlimited",
            "memory_percent": round(used_memory / max_memory * 100, 1) if max_memory else 0,
            "connected_clients": info_clients.get("connected_clients", 0),
            "total_commands": info_stats.get("total_commands_processed", 0),
            "keys_count": await redis_client.dbsize(),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/status")
async def system_status(
    current_user: User = Depends(require_permission("system.view")),
    db: AsyncSession = Depends(get_db),
):
    """Получение текущего состояния всех сервисов (Backend, DB, Redis)."""
    backend = await _check_backend()
    database = await _check_database(db)
    redis = await _check_redis()

    return {
        "backend": backend,
        "database": database,
        "redis": redis,
    }


@router.get("/server-stats")
async def server_stats_history(
    count: int = 120,
    current_user: User = Depends(require_permission("system.view")),
):
    """Получение истории метрик сервера (CPU, память, диск)."""
    from app.services.server_monitor import get_stats_history, STREAM_MAXLEN

    count = min(count, STREAM_MAXLEN)
    history = await get_stats_history(count)

    return {"points": history}


@router.get("/docker-stats")
async def docker_stats(
    current_user: User = Depends(require_permission("system.view")),
):
    """Получение текущих метрик Docker-контейнеров и списка контейнеров."""
    from app.services.docker_monitor import get_latest_stats, get_container_names

    latest = await get_latest_stats()
    names = await get_container_names()

    return {
        "latest": latest,
        "containers": names,
    }


@router.get("/docker-stats/{container_name}")
async def docker_stats_history(
    container_name: str,
    count: int = 120,
    current_user: User = Depends(require_permission("system.view")),
):
    """Получение истории метрик конкретного контейнера."""
    from app.services.docker_monitor import get_stats_history, STREAM_MAXLEN

    count = min(count, STREAM_MAXLEN)
    history = await get_stats_history(container_name, count)

    return {"container": container_name, "points": history}


# ── Default Access ────────────────────────────────────────


@router.get("/default-access")
async def get_default_access_settings(
    current_user: User = Depends(require_permission("system.view")),
):
    """Получение настроек доступа по умолчанию для новых пользователей."""
    from app.services.module_access import (
        get_default_access,
        get_valid_modules,
        get_valid_levels,
    )

    defaults = await get_default_access()
    # Исключаем модуль admin из доступных для настройки по умолчанию
    modules = [m for m in get_valid_modules() if m != "admin"]
    levels = get_valid_levels(modules[0]) if modules else []

    return {
        "defaults": defaults,
        "available_modules": modules,
        "available_levels": [lvl for lvl in levels],
    }


@router.put("/default-access")
async def update_default_access_settings(
    data: DefaultAccessUpdate,
    request: Request,
    current_user: User = Depends(require_permission("system.manage")),
    db: AsyncSession = Depends(get_db),
):
    """Обновление настроек доступа по умолчанию для новых пользователей."""
    from app.services.module_access import (
        set_default_access,
        get_valid_modules,
        get_valid_levels,
    )
    from app.services.audit import log_action
    from app.dependencies import get_client_ip

    valid_modules = set(get_valid_modules()) - {"admin"}

    for module, level in data.defaults.items():
        if module not in valid_modules:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый модуль: {module}",
            )
        if level not in get_valid_levels(module):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый уровень '{level}' для модуля '{module}'",
            )

    await set_default_access(data.defaults)

    await log_action(
        db=db,
        actor_id=current_user.id,
        action="default_access.update",
        target_type="system",
        target_id=current_user.id,
        details={"defaults": data.defaults},
        ip_address=get_client_ip(request),
    )

    return {"message": "Настройки сохранены", "defaults": data.defaults}


# ── Test Report ──────────────────────────────────────

TEST_REPORT_PATH = Path(__file__).resolve().parent.parent.parent.parent / "test-report.json"


@router.get("/test-report")
async def test_report(
    current_user: User = Depends(require_permission("system.view")),
):
    """Получение результата последнего прогона pytest (из JSON-файла)."""
    if not TEST_REPORT_PATH.exists():
        return {"available": False}

    try:
        raw = json.loads(TEST_REPORT_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"available": False}

    summary = raw.get("summary", {})
    created = datetime.fromtimestamp(
        raw.get("created", TEST_REPORT_PATH.stat().st_mtime),
        tz=timezone.utc,
    ).isoformat()

    tests = []
    for t in raw.get("tests", []):
        nodeid = t.get("nodeid", "")
        parts = nodeid.split("::")
        tests.append({
            "name": parts[-1] if parts else nodeid,
            "file": parts[0].replace("tests/", "") if len(parts) > 1 else "",
            "outcome": t.get("outcome", "unknown"),
            "duration": round(t.get("duration", 0), 3),
        })

    return {
        "available": True,
        "created": created,
        "summary": {
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "errors": summary.get("error", 0),
            "total": summary.get("total", 0),
        },
        "duration": round(raw.get("duration", 0), 2),
        "tests": tests,
    }
