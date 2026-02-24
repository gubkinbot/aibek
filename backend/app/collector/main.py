"""Entrypoint OPC-коллектора — отдельный процесс (Docker контейнер).

Запуск: python -m app.collector.main

Загружает активные станции из PostgreSQL, запускает по одному StationWorker
на каждую, периодически перечитывает список для hot-reload.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from sqlalchemy import select

from app.database import async_session, engine
from app.models.compressor import CompressorStation
from app.collector.worker import StationWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("opc-collector")


class CollectorManager:
    """Управляет всеми StationWorker-ами."""

    def __init__(self) -> None:
        self._workers: dict[str, tuple[StationWorker, asyncio.Task]] = {}
        self._running = True

    async def run(self) -> None:
        """Основной цикл: загрузка станций → запуск workers → горячая перезагрузка."""
        logger.info("OPC Collector starting...")

        # Первоначальная загрузка
        await self._sync_workers()

        # Периодическая синхронизация
        while self._running:
            await asyncio.sleep(60)
            if self._running:
                await self._sync_workers()

    async def _sync_workers(self) -> None:
        """Синхронизирует workers с текущим списком активных станций в БД."""
        try:
            async with async_session() as db:
                result = await db.execute(
                    select(CompressorStation).where(CompressorStation.is_active == True),
                )
                stations = {s.code: s for s in result.scalars().all()}
        except Exception as e:
            logger.error("Failed to load stations: %s", e)
            return

        active_codes = set(stations.keys())
        running_codes = set(self._workers.keys())

        # Остановить workers для удалённых / деактивированных станций
        for code in running_codes - active_codes:
            worker, task = self._workers.pop(code)
            logger.info("Stopping worker for station '%s'", code)
            worker.stop()
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

        # Запустить workers для новых станций
        for code in active_codes - running_codes:
            station = stations[code]
            worker = StationWorker(station)
            task = asyncio.create_task(worker.run(async_session))
            self._workers[code] = (worker, task)
            logger.info(
                "Started worker for station '%s' (%s)",
                code, station.opc_url,
            )

        logger.info(
            "Workers synced: %d active stations, %d workers",
            len(active_codes), len(self._workers),
        )

    async def shutdown(self) -> None:
        """Graceful shutdown всех workers."""
        logger.info("Shutting down OPC Collector...")
        self._running = False

        for code, (worker, task) in self._workers.items():
            worker.stop()
            task.cancel()

        for code, (worker, task) in self._workers.items():
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

        self._workers.clear()
        logger.info("All workers stopped")


async def main() -> None:
    manager = CollectorManager()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(manager.shutdown()))

    try:
        await manager.run()
    except asyncio.CancelledError:
        pass
    finally:
        await manager.shutdown()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
