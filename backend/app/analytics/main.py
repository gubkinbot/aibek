"""Entrypoint Analytics-сервиса — детекция аномалий (отдельный Docker контейнер).

Запуск: python -m app.analytics.main

Загружает активные anomaly_rules из PostgreSQL, каждые 60 секунд запрашивает
последние данные из TimescaleDB и прогоняет соответствующие детекторы.
"""

from __future__ import annotations

import asyncio
import json
import logging
import signal
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.detectors import DETECTORS, DetectionResult
from app.database import async_session, engine
from app.models.compressor import (
    CompressorAnomalyEvent,
    CompressorAnomalyRule,
    CompressorStation,
    CompressorTag,
)
from app.services.redis import redis_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("analytics")

# Интервал между циклами анализа (секунды)
ANALYSIS_INTERVAL = 60
# Максимальная глубина запроса данных (минуты)
MAX_LOOKBACK_MINUTES = 120


class AnalyticsManager:
    """Управляет циклом детекции аномалий."""

    def __init__(self) -> None:
        self._running = True
        self._rules: list[CompressorAnomalyRule] = []
        # Кэш: tag_id → station_code
        self._tag_station: dict[str, str] = {}

    async def run(self) -> None:
        logger.info("Analytics service starting...")

        while self._running:
            try:
                await self._reload_rules()
                await self._analyze()
            except Exception as e:
                logger.error("Analysis cycle error: %s", e)

            await asyncio.sleep(ANALYSIS_INTERVAL)

    async def _reload_rules(self) -> None:
        """Загружает активные правила аномалий из БД."""
        async with async_session() as db:
            result = await db.execute(
                select(CompressorAnomalyRule).where(
                    CompressorAnomalyRule.is_active == True,
                ),
            )
            self._rules = list(result.scalars().all())

            # Обновляем кэш tag → station
            if self._rules:
                tag_ids = list({r.tag_id for r in self._rules})
                result = await db.execute(
                    select(CompressorTag.id, CompressorStation.code, CompressorStation.id)
                    .join(CompressorStation, CompressorTag.station_id == CompressorStation.id)
                    .where(CompressorTag.id.in_(tag_ids)),
                )
                self._tag_station = {}
                self._tag_station_id: dict[str, str] = {}
                for tag_id, station_code, station_id in result.all():
                    self._tag_station[str(tag_id)] = station_code
                    self._tag_station_id[str(tag_id)] = station_id

        logger.debug("Loaded %d anomaly rules", len(self._rules))

    async def _analyze(self) -> None:
        """Прогоняет детекторы по всем правилам."""
        if not self._rules:
            return

        async with async_session() as db:
            for rule in self._rules:
                try:
                    await self._analyze_rule(rule, db)
                except Exception as e:
                    logger.error(
                        "Error analyzing rule %s (%s): %s",
                        rule.id, rule.name, e,
                    )
            await db.commit()

    async def _analyze_rule(
        self, rule: CompressorAnomalyRule, db: AsyncSession,
    ) -> None:
        """Анализирует одно правило."""
        detector_cls = DETECTORS.get(rule.detector_type)
        if detector_cls is None:
            logger.warning("Unknown detector type: %s", rule.detector_type)
            return

        # Определяем глубину запроса данных (из конфига правила)
        config = rule.config
        baseline_minutes = config.get("baseline_minutes", 60)
        window_minutes = config.get("window_minutes", 15)
        lookback = min(max(baseline_minutes, window_minutes) + 10, MAX_LOOKBACK_MINUTES)

        # Запрос данных из TimescaleDB
        since = datetime.now(timezone.utc) - timedelta(minutes=lookback)
        result = await db.execute(
            text("""
                SELECT time, value
                FROM compressor_tag_values
                WHERE tag_id = :tag_id
                  AND time >= :since
                  AND quality = 'good'
                  AND value IS NOT NULL
                ORDER BY time
            """),
            {"tag_id": rule.tag_id, "since": since},
        )
        rows = result.all()

        if not rows:
            return

        points: list[tuple[datetime, float]] = [(row.time, row.value) for row in rows]
        current_value = points[-1][1]

        # Запуск детектора
        detection: DetectionResult | None = detector_cls.detect(
            points, config, current_value,
        )

        if detection is None or not detection.is_anomaly:
            return

        # Запись события аномалии
        tag_id_str = str(rule.tag_id)
        station_id = self._tag_station_id.get(tag_id_str)
        station_code = self._tag_station.get(tag_id_str, "unknown")

        if station_id is None:
            return

        now = datetime.now(timezone.utc)
        event = CompressorAnomalyEvent(
            time=now,
            rule_id=rule.id,
            tag_id=rule.tag_id,
            station_id=station_id,
            detector_type=rule.detector_type,
            value=detection.value,
            details=detection.details,
            severity=rule.severity,
            message=f"{rule.name}: {detection.message}",
            acknowledged=False,
        )
        db.add(event)

        # Publish в Redis
        anomaly_payload = json.dumps({
            "type": "anomaly",
            "station": station_code,
            "severity": rule.severity,
            "detector_type": rule.detector_type,
            "message": f"{rule.name}: {detection.message}",
            "tag_id": tag_id_str,
            "value": detection.value,
            "details": detection.details,
            "time": now.isoformat(),
        })
        await redis_client.publish(f"opc:anomalies:{station_code}", anomaly_payload)

        logger.info(
            "[%s] Anomaly detected: %s — %s",
            station_code, rule.name, detection.message,
        )

    async def shutdown(self) -> None:
        logger.info("Shutting down Analytics service...")
        self._running = False


async def main() -> None:
    manager = AnalyticsManager()

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
