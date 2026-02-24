"""Модели данных модуля «Компрессорные станции».

Таблицы:
  - compressor_stations      — конфигурация станций и OPC-подключений
  - compressor_tags          — определения тегов (OPC-точек) по станциям
  - compressor_computed_tags — вычисляемые теги (status_map, formula)
  - compressor_tag_values    — исторические значения (TimescaleDB hypertable)
  - compressor_alarm_rules   — правила пороговых аварий
  - compressor_alarm_events  — журнал сработавших аварий (hypertable)
  - compressor_anomaly_rules — правила детекции аномалий
  - compressor_anomaly_events — журнал обнаруженных аномалий (hypertable)
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ---------------------------------------------------------------------------
# compressor_stations
# ---------------------------------------------------------------------------

class CompressorStation(Base):
    """Компрессорная станция с настройками OPC UA подключения."""

    __tablename__ = "compressor_stations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    opc_url: Mapped[str] = mapped_column(String(255))
    opc_security_policy: Mapped[str] = mapped_column(
        String(100), server_default="Basic128Rsa15",
    )
    opc_security_mode: Mapped[str] = mapped_column(
        String(50), server_default="Sign",
    )
    opc_cert_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opc_key_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    polling_interval: Mapped[int] = mapped_column(Integer, server_default="300")
    realtime_interval: Mapped[int] = mapped_column(Integer, server_default="1")
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default="true",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True,
    )

    # relationships
    tags: Mapped[list["CompressorTag"]] = relationship(
        back_populates="station", cascade="all, delete-orphan", lazy="selectin",
    )
    computed_tags: Mapped[list["CompressorComputedTag"]] = relationship(
        back_populates="station", cascade="all, delete-orphan", lazy="selectin",
    )


# ---------------------------------------------------------------------------
# compressor_tags
# ---------------------------------------------------------------------------

class CompressorTag(Base):
    """OPC UA тег (точка измерения), привязанный к станции."""

    __tablename__ = "compressor_tags"
    __table_args__ = (
        UniqueConstraint("station_id", "opc_path", name="uq_station_opc_path"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compressor_stations.id", ondelete="CASCADE"),
        index=True,
    )
    opc_path: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")

    # валидация и очистка
    valid_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    valid_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    stale_timeout: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )

    # relationships
    station: Mapped["CompressorStation"] = relationship(back_populates="tags")
    alarm_rules: Mapped[list["CompressorAlarmRule"]] = relationship(
        back_populates="tag", cascade="all, delete-orphan", lazy="selectin",
    )
    anomaly_rules: Mapped[list["CompressorAnomalyRule"]] = relationship(
        back_populates="tag", cascade="all, delete-orphan", lazy="selectin",
    )


# ---------------------------------------------------------------------------
# compressor_computed_tags
# ---------------------------------------------------------------------------

class CompressorComputedTag(Base):
    """Вычисляемый тег: status_map (из бинарных) или formula (арифметика)."""

    __tablename__ = "compressor_computed_tags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compressor_stations.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100))
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")
    compute_type: Mapped[str] = mapped_column(String(20))  # "status_map" | "formula"
    config: Mapped[dict] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )

    # relationships
    station: Mapped["CompressorStation"] = relationship(back_populates="computed_tags")


# ---------------------------------------------------------------------------
# compressor_tag_values  (TimescaleDB hypertable)
# ---------------------------------------------------------------------------

class CompressorTagValue(Base):
    """Историческое значение тега (time-series, hypertable)."""

    __tablename__ = "compressor_tag_values"

    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compressor_tags.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality: Mapped[str] = mapped_column(String(20), server_default="good")


# ---------------------------------------------------------------------------
# compressor_alarm_rules
# ---------------------------------------------------------------------------

class CompressorAlarmRule(Base):
    """Правило пороговой аварии для конкретного тега."""

    __tablename__ = "compressor_alarm_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compressor_tags.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200))
    condition: Mapped[str] = mapped_column(String(20))  # gt, lt, gte, lte
    threshold: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(20))  # info, warning, critical
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )

    # relationships
    tag: Mapped["CompressorTag"] = relationship(back_populates="alarm_rules")


# ---------------------------------------------------------------------------
# compressor_alarm_events  (TimescaleDB hypertable)
# ---------------------------------------------------------------------------

class CompressorAlarmEvent(Base):
    """Сработавшая пороговая авария."""

    __tablename__ = "compressor_alarm_events"

    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True,
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compressor_alarm_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compressor_tags.id", ondelete="CASCADE"),
    )
    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compressor_stations.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    value: Mapped[float] = mapped_column(Float)
    threshold: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(String(500))
    acknowledged: Mapped[bool] = mapped_column(Boolean, server_default="false")
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )


# ---------------------------------------------------------------------------
# compressor_anomaly_rules
# ---------------------------------------------------------------------------

class CompressorAnomalyRule(Base):
    """Правило детекции аномалий (trend, volatility, stabilization, spike)."""

    __tablename__ = "compressor_anomaly_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compressor_tags.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200))
    detector_type: Mapped[str] = mapped_column(String(30))
    config: Mapped[dict] = mapped_column(JSON)
    severity: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )

    # relationships
    tag: Mapped["CompressorTag"] = relationship(back_populates="anomaly_rules")


# ---------------------------------------------------------------------------
# compressor_anomaly_events  (TimescaleDB hypertable)
# ---------------------------------------------------------------------------

class CompressorAnomalyEvent(Base):
    """Обнаруженная аномалия."""

    __tablename__ = "compressor_anomaly_events"

    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True,
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compressor_anomaly_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compressor_tags.id", ondelete="CASCADE"),
    )
    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compressor_stations.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    detector_type: Mapped[str] = mapped_column(String(30))
    value: Mapped[float] = mapped_column(Float)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    severity: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(String(500))
    acknowledged: Mapped[bool] = mapped_column(Boolean, server_default="false")
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
