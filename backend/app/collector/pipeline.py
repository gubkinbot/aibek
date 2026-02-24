"""Конвейер обработки данных: валидация, определение залипаний, вычисляемые теги.

Работает между чтением OPC UA и публикацией в Redis / записью в PostgreSQL.
"""

from __future__ import annotations

import ast
import operator
import time
import uuid
from dataclasses import dataclass, field

from app.models.compressor import CompressorComputedTag, CompressorTag


@dataclass
class ProcessedTag:
    """Результат обработки одного тега."""

    tag_id: uuid.UUID
    value: float | None
    quality: str  # "good", "bad", "stale", "outlier"
    name: str
    unit: str | None
    category: str | None


@dataclass
class ProcessedComputed:
    """Результат вычисляемого тега."""

    ct_id: uuid.UUID
    value: float | None
    status: str | None
    name: str
    category: str | None


class DataPipeline:
    """Очистка, валидация и вычисление тегов."""

    # {tag_id: (last_value, last_change_timestamp)}
    _last_change: dict[uuid.UUID, tuple[float | None, float]] = field(
        default_factory=dict,
    )

    def __init__(self) -> None:
        self._last_change: dict[uuid.UUID, tuple[float | None, float]] = {}

    def process(
        self,
        raw_readings: dict[str, float | None],
        tags: list[CompressorTag],
        computed_tags: list[CompressorComputedTag],
    ) -> tuple[list[ProcessedTag], list[ProcessedComputed]]:
        """Обрабатывает сырые OPC-данные.

        Args:
            raw_readings: {opc_path: raw_value} из OPC
            tags: определения тегов станции
            computed_tags: определения вычисляемых тегов

        Returns:
            (processed_tags, processed_computed)
        """
        now = time.time()
        opc_path_to_tag: dict[str, CompressorTag] = {t.opc_path: t for t in tags}
        processed: list[ProcessedTag] = []
        values_by_id: dict[uuid.UUID, float | None] = {}

        for opc_path, raw_value in raw_readings.items():
            tag = opc_path_to_tag.get(opc_path)
            if tag is None or not tag.is_active:
                continue

            value = _to_float(raw_value)
            quality = "good"

            # 1. Валидация min/max
            if value is not None:
                if tag.valid_min is not None and value < tag.valid_min:
                    quality = "outlier"
                if tag.valid_max is not None and value > tag.valid_max:
                    quality = "outlier"

            # 2. Обнаружение залипаний (stale)
            if tag.stale_timeout and quality == "good":
                prev = self._last_change.get(tag.id)
                if prev is not None:
                    prev_value, prev_ts = prev
                    if _values_equal(value, prev_value):
                        if (now - prev_ts) > tag.stale_timeout:
                            quality = "stale"
                    else:
                        self._last_change[tag.id] = (value, now)
                else:
                    self._last_change[tag.id] = (value, now)

            # Bad quality, если value is None (OPC не вернул значение)
            if value is None and quality == "good":
                quality = "bad"

            processed.append(ProcessedTag(
                tag_id=tag.id,
                value=value,
                quality=quality,
                name=tag.name,
                unit=tag.unit,
                category=tag.category,
            ))
            values_by_id[tag.id] = value

        # 3. Вычисляемые теги
        computed_results = self._compute(computed_tags, values_by_id)

        return processed, computed_results

    def _compute(
        self,
        computed_tags: list[CompressorComputedTag],
        values_by_id: dict[uuid.UUID, float | None],
    ) -> list[ProcessedComputed]:
        """Вычисляет производные теги."""
        results: list[ProcessedComputed] = []

        for ct in computed_tags:
            if not ct.is_active:
                continue

            if ct.compute_type == "status_map":
                result = self._compute_status_map(ct, values_by_id)
            elif ct.compute_type == "formula":
                result = self._compute_formula(ct, values_by_id)
            else:
                continue

            if result is not None:
                results.append(result)

        return results

    def _compute_status_map(
        self,
        ct: CompressorComputedTag,
        values_by_id: dict[uuid.UUID, float | None],
    ) -> ProcessedComputed | None:
        """status_map: комбинация бинарных тегов → статус.

        Config формат:
        {
            "source_tags": ["uuid1", "uuid2", ...],
            "rules": [
                {"when": {"uuid1": 0, "uuid2": 1}, "status": "В работе", "value": 1},
                ...
            ],
            "default": {"status": "Остановлен", "value": 0}
        }
        """
        config = ct.config
        rules = config.get("rules", [])
        default = config.get("default", {"status": "Неизвестно", "value": None})

        for rule in rules:
            when = rule.get("when", {})
            matched = True
            for tag_id_str, expected in when.items():
                try:
                    tag_id = uuid.UUID(tag_id_str)
                except ValueError:
                    matched = False
                    break
                actual = values_by_id.get(tag_id)
                if actual is None or int(actual) != int(expected):
                    matched = False
                    break

            if matched:
                return ProcessedComputed(
                    ct_id=ct.id,
                    value=rule.get("value"),
                    status=rule.get("status"),
                    name=ct.name,
                    category=ct.category,
                )

        return ProcessedComputed(
            ct_id=ct.id,
            value=default.get("value"),
            status=default.get("status"),
            name=ct.name,
            category=ct.category,
        )

    def _compute_formula(
        self,
        ct: CompressorComputedTag,
        values_by_id: dict[uuid.UUID, float | None],
    ) -> ProcessedComputed | None:
        """formula: арифметика из нескольких тегов.

        Config формат:
        {
            "expression": "(a + b) / 2",
            "variables": {"a": "tag_uuid_str", "b": "tag_uuid_str"}
        }
        """
        config = ct.config
        expression = config.get("expression", "")
        variables = config.get("variables", {})

        # Подстановка значений
        local_vars: dict[str, float] = {}
        for var_name, tag_id_str in variables.items():
            try:
                tag_id = uuid.UUID(tag_id_str)
            except ValueError:
                return None
            val = values_by_id.get(tag_id)
            if val is None:
                return ProcessedComputed(
                    ct_id=ct.id, value=None, status=None,
                    name=ct.name, category=ct.category,
                )
            local_vars[var_name] = val

        # Безопасное вычисление
        try:
            result_value = _safe_eval(expression, local_vars)
        except Exception:
            return None

        return ProcessedComputed(
            ct_id=ct.id,
            value=result_value,
            status=None,
            name=ct.name,
            category=ct.category,
        )


# ── Утилиты ─────────────────────────────────────────────────────────────────


_DEAD_BAND = 0.001


def _to_float(value) -> float | None:
    """Безопасная конвертация в float."""
    if value is None:
        return None
    try:
        v = float(value)
        if v != v:  # NaN check
            return None
        return v
    except (ValueError, TypeError):
        return None


def _values_equal(a: float | None, b: float | None) -> bool:
    """Сравнение с dead-band для определения залипаний."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(a - b) < _DEAD_BAND


# Безопасный вычислитель арифметических выражений

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def _safe_eval(expression: str, variables: dict[str, float]) -> float:
    """Вычисляет арифметическое выражение с переменными (без exec/eval)."""
    tree = ast.parse(expression, mode="eval")

    def _eval_node(node):
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in variables:
            return variables[node.id]
        if isinstance(node, ast.BinOp):
            op_fn = _SAFE_OPS.get(type(node.op))
            if op_fn is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op_fn(_eval_node(node.left), _eval_node(node.right))
        if isinstance(node, ast.UnaryOp):
            op_fn = _SAFE_OPS.get(type(node.op))
            if op_fn is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op_fn(_eval_node(node.operand))
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")

    return _eval_node(tree)
