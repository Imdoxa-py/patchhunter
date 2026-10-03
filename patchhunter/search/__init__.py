"""Calibration utilities and thresholds for perceptual matching."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CalibrationResult:
    ceilings: dict[str, float] = field(default_factory=dict)
    thresholds: dict[str, float] = field(default_factory=dict)
    tolerances: dict[str, float] = field(default_factory=dict)

    def save(self, path: str | Path) -> None:
        payload = {
            "ceilings": self.ceilings,
            "thresholds": self.thresholds,
            "tolerances": self.tolerances,
        }
        Path(path).write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "CalibrationResult":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            ceilings=payload.get("ceilings", {}),
            thresholds=payload.get("thresholds", {}),
            tolerances=payload.get("tolerances", {}),
        )


__all__ = ["CalibrationResult"]
