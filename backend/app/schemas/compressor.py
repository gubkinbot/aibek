"""Pydantic-схемы модуля «Компрессорные станции»."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Станции ──────────────────────────────────────────────────────────────────

class StationCreate(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50, pattern=r"^[a-z0-9_-]+$")
    opc_url: str = Field(..., max_length=255)
    opc_security_policy: str = "Basic128Rsa15"
    opc_security_mode: str = "Sign"
    opc_cert_path: str | None = None
    opc_key_path: str | None = None
    polling_interval: int = 300
    realtime_interval: int = 1
    is_active: bool = True
    description: str | None = None


class StationUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    opc_url: str | None = Field(None, max_length=255)
    opc_security_policy: str | None = None
    opc_security_mode: str | None = None
    opc_cert_path: str | None = None
    opc_key_path: str | None = None
    polling_interval: int | None = None
    realtime_interval: int | None = None
    is_active: bool | None = None
    description: str | None = None


class StationResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    opc_url: str
    opc_security_policy: str
    opc_security_mode: str
    opc_cert_path: str | None
    opc_key_path: str | None
    polling_interval: int
    realtime_interval: int
    is_active: bool
    description: str | None
    created_at: datetime
    updated_at: datetime | None
    tags_count: int = 0

    model_config = {"from_attributes": True}


class StationStatusResponse(BaseModel):
    """Статус OPC-подключения станции (из Redis)."""
    code: str
    connected: bool = False
    last_seen: datetime | None = None
    error: str | None = None
    tags_count: int = 0


# ── Теги ─────────────────────────────────────────────────────────────────────

class TagCreate(BaseModel):
    opc_path: str = Field(..., max_length=255)
    name: str = Field(..., max_length=100)
    unit: str | None = Field(None, max_length=50)
    data_type: str | None = Field(None, max_length=50)
    category: str | None = Field(None, max_length=100)
    sort_order: int = 0
    valid_min: float | None = None
    valid_max: float | None = None
    stale_timeout: int | None = None
    is_active: bool = True


class TagBulkCreate(BaseModel):
    tags: list[TagCreate]


class TagUpdate(BaseModel):
    opc_path: str | None = Field(None, max_length=255)
    name: str | None = Field(None, max_length=100)
    unit: str | None = None
    data_type: str | None = None
    category: str | None = None
    sort_order: int | None = None
    valid_min: float | None = None
    valid_max: float | None = None
    stale_timeout: int | None = None
    is_active: bool | None = None


class TagResponse(BaseModel):
    id: uuid.UUID
    station_id: uuid.UUID
    opc_path: str
    name: str
    unit: str | None
    data_type: str | None
    category: str | None
    sort_order: int
    valid_min: float | None
    valid_max: float | None
    stale_timeout: int | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Вычисляемые теги ────────────────────────────────────────────────────────

class ComputedTagCreate(BaseModel):
    name: str = Field(..., max_length=100)
    unit: str | None = Field(None, max_length=50)
    category: str | None = Field(None, max_length=100)
    sort_order: int = 0
    compute_type: str = Field(..., pattern=r"^(status_map|formula)$")
    config: dict
    is_active: bool = True


class ComputedTagUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    unit: str | None = None
    category: str | None = None
    sort_order: int | None = None
    compute_type: str | None = Field(None, pattern=r"^(status_map|formula)$")
    config: dict | None = None
    is_active: bool | None = None


class ComputedTagResponse(BaseModel):
    id: uuid.UUID
    station_id: uuid.UUID
    name: str
    unit: str | None
    category: str | None
    sort_order: int
    compute_type: str
    config: dict
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Realtime данные ──────────────────────────────────────────────────────────

class RealtimeTagValue(BaseModel):
    value: float | None
    quality: str
    name: str
    unit: str | None
    category: str | None


class RealtimeComputedValue(BaseModel):
    value: float | None
    status: str | None = None
    name: str
    category: str | None


class RealtimeResponse(BaseModel):
    station: str
    timestamp: datetime | None
    connected: bool
    tags: dict[str, RealtimeTagValue]
    computed: dict[str, RealtimeComputedValue]


# ── Исторические данные ──────────────────────────────────────────────────────

class HistoryPoint(BaseModel):
    time: datetime
    tag_id: uuid.UUID
    avg: float | None
    min: float | None
    max: float | None


class HistoryResponse(BaseModel):
    station: str
    points: list[HistoryPoint]


# ── Правила аварий ───────────────────────────────────────────────────────────

class AlarmRuleCreate(BaseModel):
    tag_id: uuid.UUID
    name: str = Field(..., max_length=200)
    condition: str = Field(..., pattern=r"^(gt|lt|gte|lte)$")
    threshold: float
    severity: str = Field(..., pattern=r"^(info|warning|critical)$")
    is_active: bool = True


class AlarmRuleUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    condition: str | None = Field(None, pattern=r"^(gt|lt|gte|lte)$")
    threshold: float | None = None
    severity: str | None = Field(None, pattern=r"^(info|warning|critical)$")
    is_active: bool | None = None


class AlarmRuleResponse(BaseModel):
    id: uuid.UUID
    tag_id: uuid.UUID
    name: str
    condition: str
    threshold: float
    severity: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── События аварий ───────────────────────────────────────────────────────────

class AlarmEventResponse(BaseModel):
    time: datetime
    rule_id: uuid.UUID | None
    tag_id: uuid.UUID
    station_id: uuid.UUID
    value: float
    threshold: float
    severity: str
    message: str
    acknowledged: bool
    acknowledged_by: uuid.UUID | None
    acknowledged_at: datetime | None

    model_config = {"from_attributes": True}


class AlarmEventListResponse(BaseModel):
    items: list[AlarmEventResponse]
    total: int
    page: int
    per_page: int
    pages: int


# ── Правила аномалий ─────────────────────────────────────────────────────────

class AnomalyRuleCreate(BaseModel):
    tag_id: uuid.UUID
    name: str = Field(..., max_length=200)
    detector_type: str = Field(..., pattern=r"^(trend|volatility|stabilization|spike)$")
    config: dict
    severity: str = Field(..., pattern=r"^(info|warning|critical)$")
    is_active: bool = True


class AnomalyRuleUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    detector_type: str | None = Field(None, pattern=r"^(trend|volatility|stabilization|spike)$")
    config: dict | None = None
    severity: str | None = Field(None, pattern=r"^(info|warning|critical)$")
    is_active: bool | None = None


class AnomalyRuleResponse(BaseModel):
    id: uuid.UUID
    tag_id: uuid.UUID
    name: str
    detector_type: str
    config: dict
    severity: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── События аномалий ─────────────────────────────────────────────────────────

class AnomalyEventResponse(BaseModel):
    time: datetime
    rule_id: uuid.UUID | None
    tag_id: uuid.UUID
    station_id: uuid.UUID
    detector_type: str
    value: float
    details: dict | None
    severity: str
    message: str
    acknowledged: bool
    acknowledged_by: uuid.UUID | None
    acknowledged_at: datetime | None

    model_config = {"from_attributes": True}


class AnomalyEventListResponse(BaseModel):
    items: list[AnomalyEventResponse]
    total: int
    page: int
    per_page: int
    pages: int


# ── Импорт ───────────────────────────────────────────────────────────────────

class ImportResult(BaseModel):
    created: int = 0
    skipped: int = 0
    imported: int = 0
    errors: list[str] = []


# ── Общие ────────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
