"""Metrics package."""

from typing import Any


class Metric:
    """Common metric protocol for perceptual wrappers."""

    name: str = "metric"

    def score(self, target: Any, candidate: Any, sr: int) -> float:
        raise NotImplementedError


class MetricRegistry:
    _items: dict[str, Metric] = {}

    @classmethod
    def register(cls, name: str, metric: Metric) -> None:
        cls._items[name] = metric

    @classmethod
    def get(cls, name: str) -> Metric:
        return cls._items[name]


__all__ = ["Metric", "MetricRegistry"]
