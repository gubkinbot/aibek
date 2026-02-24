"""Детекторы аномалий для данных компрессорных станций.

Каждый детектор принимает массив (time, value) и конфигурацию,
возвращает результат анализа.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np


@dataclass
class DetectionResult:
    """Результат работы детектора."""

    is_anomaly: bool
    value: float
    details: dict
    message: str


class TrendDetector:
    """Линейная регрессия на скользящем окне.

    Аномалия если |slope| > threshold И R² > min_r_squared.
    Конфигурация: {window_minutes, slope_threshold, min_r_squared}
    """

    @staticmethod
    def detect(
        points: list[tuple[datetime, float]],
        config: dict,
        current_value: float,
    ) -> DetectionResult | None:
        window_minutes = config.get("window_minutes", 15)
        slope_threshold = config.get("slope_threshold", 0.5)
        min_r_squared = config.get("min_r_squared", 0.7)

        if len(points) < 3:
            return None

        # Фильтруем по окну
        latest = points[-1][0]
        cutoff_seconds = window_minutes * 60
        window_points = [
            (t, v) for t, v in points
            if (latest - t).total_seconds() <= cutoff_seconds
        ]

        if len(window_points) < 3:
            return None

        # Время в секундах от начала окна
        t0 = window_points[0][0]
        x = np.array([(t - t0).total_seconds() for t, _ in window_points])
        y = np.array([v for _, v in window_points])

        # Линейная регрессия
        n = len(x)
        sx = np.sum(x)
        sy = np.sum(y)
        sxy = np.sum(x * y)
        sxx = np.sum(x * x)
        syy = np.sum(y * y)

        denom = n * sxx - sx * sx
        if abs(denom) < 1e-10:
            return None

        slope = (n * sxy - sx * sy) / denom
        intercept = (sy - slope * sx) / n

        # R²
        ss_res = np.sum((y - (slope * x + intercept)) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 1e-10 else 0

        # Slope в единицах/минуту
        slope_per_min = slope * 60

        is_anomaly = abs(slope_per_min) > slope_threshold and r_squared > min_r_squared

        direction = "рост" if slope_per_min > 0 else "падение"
        message = (
            f"Тренд: {direction} {abs(slope_per_min):.3f}/мин, R²={r_squared:.2f}"
        )

        return DetectionResult(
            is_anomaly=is_anomaly,
            value=current_value,
            details={
                "slope_per_min": round(slope_per_min, 4),
                "r_squared": round(r_squared, 4),
                "window_minutes": window_minutes,
                "points_count": len(window_points),
            },
            message=message,
        )


class VolatilityDetector:
    """Сравнение std текущего окна с baseline.

    Аномалия если std_current > std_baseline * multiplier.
    Конфигурация: {window_minutes, baseline_minutes, std_multiplier}
    """

    @staticmethod
    def detect(
        points: list[tuple[datetime, float]],
        config: dict,
        current_value: float,
    ) -> DetectionResult | None:
        window_minutes = config.get("window_minutes", 10)
        baseline_minutes = config.get("baseline_minutes", 60)
        std_multiplier = config.get("std_multiplier", 3.0)

        if len(points) < 5:
            return None

        latest = points[-1][0]
        window_cutoff = window_minutes * 60
        baseline_cutoff = baseline_minutes * 60

        window_vals = np.array([
            v for t, v in points
            if (latest - t).total_seconds() <= window_cutoff
        ])
        baseline_vals = np.array([
            v for t, v in points
            if (latest - t).total_seconds() <= baseline_cutoff
        ])

        if len(window_vals) < 3 or len(baseline_vals) < 5:
            return None

        std_current = float(np.std(window_vals))
        std_baseline = float(np.std(baseline_vals))

        if std_baseline < 1e-10:
            return None

        ratio = std_current / std_baseline
        is_anomaly = std_current > std_baseline * std_multiplier

        message = (
            f"Волатильность: std={std_current:.3f} "
            f"(baseline={std_baseline:.3f}, ratio={ratio:.2f}x)"
        )

        return DetectionResult(
            is_anomaly=is_anomaly,
            value=current_value,
            details={
                "std_current": round(std_current, 4),
                "std_baseline": round(std_baseline, 4),
                "ratio": round(ratio, 4),
                "window_minutes": window_minutes,
                "baseline_minutes": baseline_minutes,
            },
            message=message,
        )


class StabilizationDetector:
    """Обратная волатильность — подозрительно низкие колебания.

    Может означать залипание датчика или искусственное сглаживание.
    Аномалия если std_current / std_baseline < ratio_threshold.
    Конфигурация: {window_minutes, baseline_minutes, std_ratio_threshold}
    """

    @staticmethod
    def detect(
        points: list[tuple[datetime, float]],
        config: dict,
        current_value: float,
    ) -> DetectionResult | None:
        window_minutes = config.get("window_minutes", 10)
        baseline_minutes = config.get("baseline_minutes", 60)
        std_ratio_threshold = config.get("std_ratio_threshold", 0.1)

        if len(points) < 5:
            return None

        latest = points[-1][0]
        window_cutoff = window_minutes * 60
        baseline_cutoff = baseline_minutes * 60

        window_vals = np.array([
            v for t, v in points
            if (latest - t).total_seconds() <= window_cutoff
        ])
        baseline_vals = np.array([
            v for t, v in points
            if (latest - t).total_seconds() <= baseline_cutoff
        ])

        if len(window_vals) < 3 or len(baseline_vals) < 5:
            return None

        std_current = float(np.std(window_vals))
        std_baseline = float(np.std(baseline_vals))

        if std_baseline < 1e-10:
            return None

        ratio = std_current / std_baseline
        is_anomaly = ratio < std_ratio_threshold

        message = (
            f"Стабилизация: std={std_current:.4f} "
            f"(baseline={std_baseline:.4f}, ratio={ratio:.3f})"
        )

        return DetectionResult(
            is_anomaly=is_anomaly,
            value=current_value,
            details={
                "std_current": round(std_current, 4),
                "std_baseline": round(std_baseline, 4),
                "ratio": round(ratio, 4),
                "window_minutes": window_minutes,
                "baseline_minutes": baseline_minutes,
            },
            message=message,
        )


class SpikeDetector:
    """Z-score на скользящем среднем.

    Аномалия если |value - mean| > sigma_threshold * std.
    Конфигурация: {window_minutes, sigma_threshold}
    """

    @staticmethod
    def detect(
        points: list[tuple[datetime, float]],
        config: dict,
        current_value: float,
    ) -> DetectionResult | None:
        window_minutes = config.get("window_minutes", 5)
        sigma_threshold = config.get("sigma_threshold", 4.0)

        if len(points) < 3:
            return None

        latest = points[-1][0]
        window_cutoff = window_minutes * 60

        window_vals = np.array([
            v for t, v in points
            if (latest - t).total_seconds() <= window_cutoff
        ])

        if len(window_vals) < 3:
            return None

        mean = float(np.mean(window_vals))
        std = float(np.std(window_vals))

        if std < 1e-10:
            return None

        z_score = abs(current_value - mean) / std
        is_anomaly = z_score > sigma_threshold

        message = (
            f"Выброс: z-score={z_score:.2f} "
            f"(value={current_value:.2f}, mean={mean:.2f}, std={std:.3f})"
        )

        return DetectionResult(
            is_anomaly=is_anomaly,
            value=current_value,
            details={
                "z_score": round(z_score, 4),
                "mean": round(mean, 4),
                "std": round(std, 4),
                "window_minutes": window_minutes,
            },
            message=message,
        )


# Реестр детекторов по имени
DETECTORS: dict[str, type] = {
    "trend": TrendDetector,
    "volatility": VolatilityDetector,
    "stabilization": StabilizationDetector,
    "spike": SpikeDetector,
}
