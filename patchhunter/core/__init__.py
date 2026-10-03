"""PatchHunter core data model."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class ParameterRange:
    """Normalized parameter metadata used for safe conversion between [0, 1] and real values."""

    min_value: float
    max_value: float
    default_value: float | None = None

    def denormalize(self, value: float) -> float:
        value = float(np.clip(value, 0.0, 1.0))
        return self.min_value + (self.max_value - self.min_value) * value

    def normalize(self, value: float) -> float:
        value = float(value)
        if self.max_value == self.min_value:
            return 0.0
        clipped = np.clip(value, self.min_value, self.max_value)
        return (clipped - self.min_value) / (self.max_value - self.min_value)


@dataclass
class SourceSpec:
    kind: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class BoxSpec:
    kind: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Voice:
    start_time: float = 0.0
    duration: float = 1.0
    source: SourceSpec | None = None
    boxes: list[BoxSpec] = field(default_factory=list)


@dataclass
class Patch:
    voices: list[Voice] = field(default_factory=list)
    master: list[BoxSpec] = field(default_factory=list)
    seed: int = 0
    sample_rate: int = 44100

    def to_json(self, *, indent: int | None = None) -> str:
        payload = asdict(self)
        return json.dumps(payload, sort_keys=True, indent=indent)

    @classmethod
    def from_json(cls, payload: str | bytes | dict[str, Any]) -> "Patch":
        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode("utf-8")
        if isinstance(payload, str):
            payload = json.loads(payload)

        voices = []
        for voice in payload.get("voices", []):
            source = voice.get("source")
            if source is not None:
                source = SourceSpec(**source)
            boxes = [BoxSpec(**box) for box in voice.get("boxes", [])]
            voices.append(Voice(**{k: v for k, v in voice.items() if k not in {"source", "boxes"}}, source=source, boxes=boxes))

        master = [BoxSpec(**box) for box in payload.get("master", [])]
        return cls(
            voices=voices,
            master=master,
            seed=int(payload.get("seed", 0)),
            sample_rate=int(payload.get("sample_rate", 44100)),
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "Patch":
        with Path(path).open("r", encoding="utf-8") as fh:
            return cls.from_json(fh.read())

    def render(self, *, sr: int | None = None, length: int | None = None) -> np.ndarray:
        """Render the patch as a deterministic mixture of voices."""
        target_sr = self.sample_rate if sr is None else int(sr)
        total_samples = self._compute_total_samples(target_sr) if length is None else int(length)
        mix = np.zeros(total_samples, dtype=np.float32)

        for voice in self.voices:
            voice_signal = self._render_voice(voice, target_sr, total_samples)
            start_idx = int(round(voice.start_time * target_sr))
            if start_idx < 0:
                raise ValueError("Voice start time cannot be negative.")
            end_idx = start_idx + len(voice_signal)
            if end_idx > total_samples:
                pad = end_idx - total_samples
                voice_signal = voice_signal[: len(voice_signal) - pad]
                if voice_signal.size == 0:
                    continue
                end_idx = total_samples
            mix[start_idx:end_idx] += voice_signal[: end_idx - start_idx]

        for box in self.master:
            mix = apply_box(mix, box)

        return np.asarray(mix, dtype=np.float32)

    def _compute_total_samples(self, sr: int) -> int:
        duration = 0.0
        for voice in self.voices:
            duration = max(duration, voice.start_time + voice.duration)
        return int(max(1, np.ceil(duration * sr)))

    def _render_voice(self, voice: Voice, sr: int, total_samples: int) -> np.ndarray:
        if voice.source is None:
            signal = np.zeros(int(np.ceil(voice.duration * sr)), dtype=np.float32)
        else:
            signal = generate_source(voice.source, sr, voice.duration, self.seed)

        for box in voice.boxes:
            signal = apply_box(signal, box)

        if len(signal) > total_samples:
            signal = signal[:total_samples]
        return np.asarray(signal, dtype=np.float32)


class PatchRegistry:
    """Simple registry for source and box kind names."""

    _sources: dict[str, Any] = {}
    _boxes: dict[str, Any] = {}

    @classmethod
    def register_source(cls, name: str, fn: Any) -> None:
        cls._sources[name] = fn

    @classmethod
    def register_box(cls, name: str, fn: Any) -> None:
        cls._boxes[name] = fn

    @classmethod
    def get_source(cls, name: str) -> Any:
        return cls._sources[name]

    @classmethod
    def get_box(cls, name: str) -> Any:
        return cls._boxes[name]


def gaussian_rng(seed: int, size: int, *, kind: str = "white") -> np.ndarray:
    rng = np.random.default_rng(seed)
    if kind == "pink":
        white = rng.standard_normal(size)
        result = np.empty_like(white, dtype=np.float32)
        b = np.empty_like(white, dtype=np.float32)
        b[0] = white[0]
        for i in range(1, size):
            b[i] = 0.99886 * b[i - 1] + white[i] * 0.055 + 0.05442 * white[i - 1]
        result = b
        return np.asarray(result, dtype=np.float32)
    return np.asarray(rng.standard_normal(size), dtype=np.float32)


def _db_to_amp(db: float) -> float:
    return float(10.0 ** (db / 20.0))


def generate_source(source: SourceSpec, sr: int, duration: float, global_seed: int = 0) -> np.ndarray:
    samples = int(np.ceil(duration * sr))
    t = np.linspace(0.0, duration, samples, endpoint=False, dtype=np.float32)
    base_seed = int(source.params.get("seed", global_seed))
    freqs = float(source.params.get("frequency", 220.0))
    phase = float(source.params.get("phase", 0.0))

    if source.kind == "sine":
        return np.sin(2.0 * np.pi * freqs * t + phase).astype(np.float32)
    if source.kind == "square":
        duty = float(np.clip(source.params.get("duty", 0.5), 0.05, 0.95))
        phase_norm = (freqs * t + phase / (2 * np.pi)) % 1.0
        y = np.sign(np.sin(2.0 * np.pi * (phase_norm + 0.5 * duty)))
        return np.where(np.isclose(y, 0.0), 1.0, y).astype(np.float32)
    if source.kind == "saw":
        phase_norm = (freqs * t + phase / (2 * np.pi)) % 1.0
        return (2.0 * phase_norm - 1.0).astype(np.float32)
    if source.kind == "triangle":
        phase_norm = (freqs * t + phase / (2 * np.pi)) % 1.0
        return (1.0 - 4.0 * np.abs(phase_norm - 0.5)).astype(np.float32)
    if source.kind == "white_noise":
        rng = np.random.default_rng(base_seed)
        return np.asarray(rng.standard_normal(samples), dtype=np.float32)
    if source.kind == "pink_noise":
        return gaussian_rng(base_seed, samples, kind="pink")
    raise ValueError(f"Unsupported source kind: {source.kind}")


def apply_box(signal: np.ndarray, box: BoxSpec) -> np.ndarray:
    kind = box.kind.lower()
    params = box.params or {}

    if kind == "gain":
        gain_db = float(params.get("gain_db", 0.0))
        gain = _db_to_amp(gain_db)
        return np.asarray(signal * gain, dtype=np.float32)

    if kind == "adsr":
        attack = float(params.get("attack", 0.01))
        decay = float(params.get("decay", 0.1))
        sustain = float(params.get("sustain", 0.8))
        release = float(params.get("release", 0.1))
        gate_length = max(float(params.get("gate_length", 0.2)), 1e-6)
        sr = max(int(params.get("sample_rate", 44100)), 1)
        total = signal.size
        pad = max(int(np.ceil(gate_length * sr)), 1)
        envelope = np.ones(total, dtype=np.float32)
        attack_samples = max(int(np.ceil(attack * sr)), 1)
        decay_samples = max(int(np.ceil(decay * sr)), 1)
        release_samples = max(int(np.ceil(release * sr)), 1)
        sustain_samples = max(pad - attack_samples - decay_samples, 1)

        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0.0, 1.0, attack_samples, endpoint=False, dtype=np.float32)
        if decay_samples > 0:
            decay_scale = np.linspace(1.0, sustain, decay_samples, endpoint=False, dtype=np.float32)
            envelope[attack_samples : attack_samples + decay_samples] = decay_scale
        if sustain_samples > 0:
            envelope[attack_samples + decay_samples : attack_samples + decay_samples + sustain_samples] = sustain
        release_start = min(total, attack_samples + decay_samples + sustain_samples)
        if release_samples > 0 and total > release_start:
            release_vals = np.linspace(sustain, 0.0, total - release_start, endpoint=True, dtype=np.float32)
            envelope[release_start:] = release_vals
        return np.asarray(signal * envelope, dtype=np.float32)

    raise ValueError(f"Unsupported box kind: {box.kind}")
