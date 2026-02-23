"""Сервис мониторинга Docker-контейнеров.

Собирает метрики CPU и памяти всех запущенных контейнеров через Docker socket
и сохраняет временные ряды данных в Redis Streams."""

import asyncio
import json
import logging
import time

import aiodocker

from app.services.redis import redis_client

logger = logging.getLogger(__name__)

# Redis key prefix for docker stats streams
STREAM_PREFIX = "docker:stats:"
# Max entries per container stream (~1 hour at 5s interval = 720)
STREAM_MAXLEN = 720
# Collection interval in seconds
COLLECT_INTERVAL = 5


def _calc_cpu_percent(stats: dict) -> float:
    """Вычисляет процент использования CPU из статистики Docker."""
    cpu = stats.get("cpu_stats", {})
    precpu = stats.get("precpu_stats", {})

    cpu_delta = cpu.get("cpu_usage", {}).get("total_usage", 0) - precpu.get("cpu_usage", {}).get("total_usage", 0)
    system_delta = cpu.get("system_cpu_usage", 0) - precpu.get("system_cpu_usage", 0)
    online_cpus = cpu.get("online_cpus") or len(cpu.get("cpu_usage", {}).get("percpu_usage", []) or [1])

    if system_delta > 0 and cpu_delta >= 0:
        return round((cpu_delta / system_delta) * online_cpus * 100, 2)
    return 0.0


def _calc_memory(stats: dict) -> dict:
    """Извлекает использование памяти из статистики Docker."""
    mem = stats.get("memory_stats", {})
    used = mem.get("usage", 0)
    # Subtract cache for more accurate reading
    cache = mem.get("stats", {}).get("cache", 0) if mem.get("stats") else 0
    used_net = used - cache
    limit = mem.get("limit", 0)
    percent = round(used_net / limit * 100, 2) if limit > 0 else 0

    return {
        "used": used_net,
        "limit": limit,
        "percent": percent,
    }


async def _collect_once(docker: aiodocker.Docker) -> dict:
    """Собирает метрики всех запущенных контейнеров (однократно)."""
    containers = await docker.containers.list()
    results = {}

    for container in containers:
        try:
            info = container._container
            name = info.get("Names", ["/unknown"])[0].lstrip("/")

            # Get a single stats snapshot (stream=False not supported, use stream and take first)
            stats = await container.stats(stream=False)

            # stats returns a list when stream=False
            if isinstance(stats, list):
                if not stats:
                    continue
                stat = stats[0]
            else:
                stat = stats

            cpu_percent = _calc_cpu_percent(stat)
            memory = _calc_memory(stat)

            results[name] = {
                "cpu_percent": cpu_percent,
                "memory_used": memory["used"],
                "memory_limit": memory["limit"],
                "memory_percent": memory["percent"],
                "status": info.get("State", "unknown"),
            }
        except Exception as e:
            logger.debug(f"Failed to get stats for container: {e}")

    return results


async def _store_to_redis(stats: dict, timestamp: float) -> None:
    """Сохраняет снимок метрик в Redis Streams."""
    ts = str(int(timestamp * 1000))  # millisecond timestamp as string

    pipe = redis_client.pipeline()
    for container_name, metrics in stats.items():
        stream_key = f"{STREAM_PREFIX}{container_name}"
        entry = {
            "ts": ts,
            "cpu": str(metrics["cpu_percent"]),
            "mem_used": str(metrics["memory_used"]),
            "mem_limit": str(metrics["memory_limit"]),
            "mem_pct": str(metrics["memory_percent"]),
        }
        pipe.xadd(stream_key, entry, maxlen=STREAM_MAXLEN, approximate=True)
    await pipe.execute()

    # Also store latest snapshot for quick access
    await redis_client.set(
        "docker:stats:latest",
        json.dumps({"ts": timestamp, "containers": stats}),
        ex=30,  # expires after 30s if collector stops
    )


async def collect_loop() -> None:
    """Основной цикл сбора метрик — запускается как фоновая задача."""
    docker = None
    try:
        docker = aiodocker.Docker()
        logger.info("Docker monitor started — collecting every %ds", COLLECT_INTERVAL)

        while True:
            try:
                stats = await _collect_once(docker)
                if stats:
                    await _store_to_redis(stats, time.time())
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning("Docker stats collection error: %s", e)

            await asyncio.sleep(COLLECT_INTERVAL)
    except asyncio.CancelledError:
        logger.info("Docker monitor stopped")
    except Exception as e:
        logger.error("Docker monitor failed to start: %s", e)
    finally:
        if docker:
            await docker.close()


async def get_latest_stats() -> dict | None:
    """Получает последний снимок метрик из Redis."""
    data = await redis_client.get("docker:stats:latest")
    if data:
        return json.loads(data)
    return None


async def get_stats_history(container_name: str, count: int = 120) -> list[dict]:
    """Получает историю метрик контейнера из Redis Stream.

    По умолчанию: последние 120 записей (~10 минут при интервале 5 сек)."""
    stream_key = f"{STREAM_PREFIX}{container_name}"

    # Read last N entries
    entries = await redis_client.xrevrange(stream_key, count=count)

    result = []
    for entry_id, fields in reversed(entries):  # chronological order
        result.append({
            "ts": int(fields["ts"]) / 1000,  # back to seconds
            "cpu": float(fields["cpu"]),
            "mem_used": int(fields["mem_used"]),
            "mem_limit": int(fields["mem_limit"]),
            "mem_pct": float(fields["mem_pct"]),
        })
    return result


async def get_container_names() -> list[str]:
    """Получает имена всех контейнеров, для которых есть метрики в Redis."""
    keys = []
    async for key in redis_client.scan_iter(f"{STREAM_PREFIX}*"):
        name = key.removeprefix(STREAM_PREFIX)
        if name != "latest":
            keys.append(name)
    return sorted(keys)
