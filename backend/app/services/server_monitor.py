"""
Server metrics monitoring service.

Collects CPU, memory and disk stats via psutil
and stores time-series data in Redis Streams for history.
"""

import asyncio
import json
import logging
import time

import psutil

from app.services.redis import redis_client

logger = logging.getLogger(__name__)

STREAM_KEY = "server:stats"
STREAM_MAXLEN = 720  # ~1 hour at 5s interval
COLLECT_INTERVAL = 5


async def _collect_once() -> dict:
    """Collect server metrics once."""
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "cpu": round(cpu, 1),
        "mem_used": mem.used,
        "mem_total": mem.total,
        "mem_pct": round(mem.percent, 1),
        "disk_used": disk.used,
        "disk_total": disk.total,
        "disk_pct": round(disk.percent, 1),
    }


async def _store_to_redis(metrics: dict, timestamp: float) -> None:
    """Store metrics to Redis Stream."""
    entry = {
        "ts": str(int(timestamp * 1000)),
        "cpu": str(metrics["cpu"]),
        "mem_used": str(metrics["mem_used"]),
        "mem_total": str(metrics["mem_total"]),
        "mem_pct": str(metrics["mem_pct"]),
        "disk_used": str(metrics["disk_used"]),
        "disk_total": str(metrics["disk_total"]),
        "disk_pct": str(metrics["disk_pct"]),
    }
    await redis_client.xadd(STREAM_KEY, entry, maxlen=STREAM_MAXLEN, approximate=True)


async def collect_loop() -> None:
    """Main collection loop — runs as background task."""
    logger.info("Server monitor started — collecting every %ds", COLLECT_INTERVAL)

    # Prime CPU measurement (first call always returns 0)
    psutil.cpu_percent(interval=None)

    while True:
        try:
            metrics = await _collect_once()
            await _store_to_redis(metrics, time.time())
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning("Server stats collection error: %s", e)

        await asyncio.sleep(COLLECT_INTERVAL)


async def get_stats_history(count: int = 120) -> list[dict]:
    """Get historical server stats from Redis Stream."""
    entries = await redis_client.xrevrange(STREAM_KEY, count=count)

    result = []
    for entry_id, fields in reversed(entries):
        result.append({
            "ts": int(fields["ts"]) / 1000,
            "cpu": float(fields["cpu"]),
            "mem_used": int(fields["mem_used"]),
            "mem_total": int(fields["mem_total"]),
            "mem_pct": float(fields["mem_pct"]),
            "disk_used": int(fields["disk_used"]),
            "disk_total": int(fields["disk_total"]),
            "disk_pct": float(fields["disk_pct"]),
        })
    return result
