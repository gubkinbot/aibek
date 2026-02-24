"""Per-station OPC UA worker: подключение, чтение тегов, публикация в Redis, запись в PostgreSQL."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from asyncua import Client as OpcClient
from asyncua import ua
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collector.pipeline import DataPipeline, ProcessedComputed, ProcessedTag
from app.models.compressor import (
    CompressorAlarmEvent,
    CompressorAlarmRule,
    CompressorComputedTag,
    CompressorStation,
    CompressorTag,
    CompressorTagValue,
)
from app.services.redis import redis_client

logger = logging.getLogger("opc-collector")


class StationWorker:
    """Один worker на одну станцию. Держит постоянное OPC-соединение."""

    def __init__(self, station: CompressorStation) -> None:
        self.station = station
        self.code = station.code
        self._client: OpcClient | None = None
        self._pipeline = DataPipeline()
        self._tags: list[CompressorTag] = []
        self._computed_tags: list[CompressorComputedTag] = []
        self._alarm_rules: list[CompressorAlarmRule] = []
        self._running = True
        self._backoff = 2

    async def run(self, session_factory) -> None:
        """Основной цикл: connect → read loop → reconnect при ошибке."""
        while self._running:
            try:
                # Загружаем конфигурацию из БД
                async with session_factory() as db:
                    await self._load_config(db)

                await self._connect()
                logger.info("[%s] Connected to %s (%d tags)", self.code, self.station.opc_url, len(self._tags))
                await self._publish_status(connected=True)
                self._backoff = 2

                # Parallel: realtime tick + history tick
                realtime_task = asyncio.create_task(self._realtime_loop(session_factory))
                history_task = asyncio.create_task(self._history_loop(session_factory))
                config_task = asyncio.create_task(self._config_reload_loop(session_factory))

                done, pending = await asyncio.wait(
                    [realtime_task, history_task, config_task],
                    return_when=asyncio.FIRST_EXCEPTION,
                )
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                # Re-raise exception from finished tasks
                for task in done:
                    if task.exception():
                        raise task.exception()

            except asyncio.CancelledError:
                break
            except Exception as e:
                err_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
                logger.error("[%s] %s, reconnecting in %ds", self.code, err_msg, self._backoff)
                await self._publish_status(connected=False, error=err_msg)
                await self._disconnect()
                await asyncio.sleep(self._backoff)
                self._backoff = min(self._backoff * 2, 60)

        await self._disconnect()
        logger.info("[%s] Worker stopped", self.code)

    def stop(self) -> None:
        self._running = False

    # ── OPC Connection ───────────────────────────────────────────────────────

    async def _connect(self) -> None:
        """Подключение к OPC UA серверу с security policy из конфигурации станции."""
        self._client = OpcClient(url=self.station.opc_url)

        # Security settings
        policy = self.station.opc_security_policy
        mode = self.station.opc_security_mode

        if policy and policy != "None" and self.station.opc_cert_path:
            security_mode_map = {
                "Sign": ua.MessageSecurityMode.Sign,
                "SignAndEncrypt": ua.MessageSecurityMode.SignAndEncrypt,
            }
            security_policy_map = {
                "Basic128Rsa15": f"http://opcfoundation.org/UA/SecurityPolicy#Basic128Rsa15",
                "Basic256": f"http://opcfoundation.org/UA/SecurityPolicy#Basic256",
                "Basic256Sha256": f"http://opcfoundation.org/UA/SecurityPolicy#Basic256Sha256",
            }
            policy_uri = security_policy_map.get(policy)
            sec_mode = security_mode_map.get(mode, ua.MessageSecurityMode.Sign)

            if policy_uri:
                await self._client.set_security(
                    policy=policy_uri,
                    certificate=self.station.opc_cert_path,
                    private_key=self.station.opc_key_path,
                    mode=sec_mode,
                )

        await self._client.connect()

    async def _disconnect(self) -> None:
        if self._client:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            self._client = None

    # ── Config Loading ───────────────────────────────────────────────────────

    async def _load_config(self, db: AsyncSession) -> None:
        """Загружает теги, вычисляемые теги и правила аварий из БД."""
        result = await db.execute(
            select(CompressorTag).where(
                CompressorTag.station_id == self.station.id,
                CompressorTag.is_active == True,
            ),
        )
        self._tags = list(result.scalars().all())

        result = await db.execute(
            select(CompressorComputedTag).where(
                CompressorComputedTag.station_id == self.station.id,
                CompressorComputedTag.is_active == True,
            ),
        )
        self._computed_tags = list(result.scalars().all())

        tag_ids = [t.id for t in self._tags]
        if tag_ids:
            result = await db.execute(
                select(CompressorAlarmRule).where(
                    CompressorAlarmRule.tag_id.in_(tag_ids),
                    CompressorAlarmRule.is_active == True,
                ),
            )
            self._alarm_rules = list(result.scalars().all())
        else:
            self._alarm_rules = []

    async def _config_reload_loop(self, session_factory) -> None:
        """Перечитывает конфигурацию каждые 60 секунд."""
        while self._running:
            await asyncio.sleep(60)
            try:
                async with session_factory() as db:
                    await self._load_config(db)
                logger.debug("[%s] Config reloaded: %d tags", self.code, len(self._tags))
            except Exception as e:
                logger.warning("[%s] Config reload error: %s", self.code, e)

    # ── Realtime Loop ────────────────────────────────────────────────────────

    async def _realtime_loop(self, session_factory) -> None:
        """Каждые N сек: batch read → pipeline → publish Redis → check alarms."""
        interval = max(1, self.station.realtime_interval)
        while self._running:
            try:
                raw_readings = await self._read_all_tags()
                processed_tags, computed = self._pipeline.process(
                    raw_readings, self._tags, self._computed_tags,
                )

                await self._publish_realtime(processed_tags, computed)
                await self._check_alarms(processed_tags, session_factory)

            except Exception as e:
                err_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
                logger.error("[%s] Realtime tick error: %s", self.code, err_msg)
                raise

            await asyncio.sleep(interval)

    # ── History Loop ─────────────────────────────────────────────────────────

    async def _history_loop(self, session_factory) -> None:
        """Каждые M сек: batch INSERT в compressor_tag_values."""
        interval = max(10, self.station.polling_interval)
        while self._running:
            await asyncio.sleep(interval)
            try:
                raw_readings = await self._read_all_tags()
                processed_tags, _ = self._pipeline.process(
                    raw_readings, self._tags, self._computed_tags,
                )

                if processed_tags:
                    now = datetime.now(timezone.utc)
                    rows = [
                        {
                            "time": now,
                            "tag_id": pt.tag_id,
                            "value": pt.value,
                            "quality": pt.quality,
                        }
                        for pt in processed_tags
                    ]
                    async with session_factory() as db:
                        await db.execute(CompressorTagValue.__table__.insert(), rows)
                        await db.commit()
                    logger.debug("[%s] History: wrote %d values", self.code, len(rows))

            except Exception as e:
                err_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
                logger.error("[%s] History tick error: %s", self.code, err_msg)

    # ── OPC Reading ──────────────────────────────────────────────────────────

    async def _read_all_tags(self) -> dict[str, float | None]:
        """Batch-чтение всех тегов через OPC UA."""
        if not self._client or not self._tags:
            return {}

        # Kepware NodeID формат: ns=2;s={opc_path}
        nodes = []
        paths = []
        for tag in self._tags:
            node = self._client.get_node(f"ns=2;s={tag.opc_path}")
            nodes.append(node)
            paths.append(tag.opc_path)

        try:
            values = await asyncio.gather(
                *(node.read_value() for node in nodes),
                return_exceptions=True,
            )
        except Exception:
            values = [None] * len(nodes)

        result: dict[str, float | None] = {}
        for path, val in zip(paths, values):
            if isinstance(val, Exception):
                result[path] = None
            else:
                result[path] = _to_float(val)

        return result

    # ── Redis Publishing ─────────────────────────────────────────────────────

    async def _publish_realtime(
        self,
        processed_tags: list[ProcessedTag],
        computed: list[ProcessedComputed],
    ) -> None:
        """Публикует snapshot в Redis (pub/sub + SET с TTL)."""
        now = datetime.now(timezone.utc)
        tags_dict = {
            str(pt.tag_id): {
                "value": pt.value,
                "quality": pt.quality,
                "name": pt.name,
                "unit": pt.unit,
                "category": pt.category,
            }
            for pt in processed_tags
        }
        computed_dict = {
            str(c.ct_id): {
                "value": c.value,
                "status": c.status,
                "name": c.name,
                "category": c.category,
            }
            for c in computed
        }

        payload = json.dumps({
            "type": "realtime",
            "station": self.code,
            "timestamp": now.isoformat(),
            "connected": True,
            "tags": tags_dict,
            "computed": computed_dict,
        })

        pipe = redis_client.pipeline()
        pipe.publish(f"opc:realtime:{self.code}", payload)
        pipe.set(f"opc:snapshot:{self.code}", payload, ex=10)
        await pipe.execute()

    async def _publish_status(
        self, connected: bool, error: str | None = None,
    ) -> None:
        """Публикует статус подключения в Redis."""
        data = json.dumps({
            "connected": connected,
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "error": error,
            "tags_count": len(self._tags),
        })
        await redis_client.set(f"opc:status:{self.code}", data, ex=30)

    # ── Alarms ───────────────────────────────────────────────────────────────

    async def _check_alarms(
        self,
        processed_tags: list[ProcessedTag],
        session_factory,
    ) -> None:
        """Проверяет пороговые правила и создаёт события аварий."""
        if not self._alarm_rules:
            return

        values_by_tag: dict[uuid.UUID, ProcessedTag] = {
            pt.tag_id: pt for pt in processed_tags
        }
        now = datetime.now(timezone.utc)
        events: list[dict] = []

        for rule in self._alarm_rules:
            pt = values_by_tag.get(rule.tag_id)
            if pt is None or pt.value is None or pt.quality != "good":
                continue

            triggered = False
            cond = rule.condition
            val = pt.value
            thr = rule.threshold

            if cond == "gt" and val > thr:
                triggered = True
            elif cond == "lt" and val < thr:
                triggered = True
            elif cond == "gte" and val >= thr:
                triggered = True
            elif cond == "lte" and val <= thr:
                triggered = True

            if triggered:
                message = f"{rule.name}: {pt.name} = {val:.2f} ({cond} {thr})"
                events.append({
                    "time": now,
                    "rule_id": rule.id,
                    "tag_id": rule.tag_id,
                    "station_id": self.station.id,
                    "value": val,
                    "threshold": thr,
                    "severity": rule.severity,
                    "message": message,
                    "acknowledged": False,
                })

                # Publish alarm to Redis
                alarm_payload = json.dumps({
                    "type": "alarm",
                    "station": self.code,
                    "severity": rule.severity,
                    "message": message,
                    "tag_id": str(rule.tag_id),
                    "value": val,
                    "threshold": thr,
                    "time": now.isoformat(),
                })
                await redis_client.publish(f"opc:alarms:{self.code}", alarm_payload)

        if events:
            try:
                async with session_factory() as db:
                    await db.execute(CompressorAlarmEvent.__table__.insert(), events)
                    await db.commit()
                logger.info("[%s] %d alarm events created", self.code, len(events))
            except Exception as e:
                logger.error("[%s] Failed to write alarm events: %s", self.code, e)


def _to_float(value) -> float | None:
    """Безопасная конвертация в float."""
    if value is None:
        return None
    try:
        v = float(value)
        if v != v:  # NaN
            return None
        return v
    except (ValueError, TypeError):
        return None
