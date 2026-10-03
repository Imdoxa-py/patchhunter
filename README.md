# PatchHunter

PatchHunter is a Python-based, deterministic synthesizer patch search framework for discovering a synth graph and parameter values whose rendered waveform is perceptually close to a target WAV.

This repository is the initial scaffold for the project described in the design document. It includes the core data model, deterministic rendering primitives, registry pattern, CLI entry point, and a test suite that exercises the most important invariants.

## Status

The implementation is intentionally structured as a clean foundation for the full search loop, but the full perceptual optimization stack (auraloss / ViSQOL / PEAQ / calibration pipeline / evolutionary structure search) is not yet completed in this first pass.

### Apple Silicon environment validation

The project is designed for Apple Silicon (arm64) and expects PyTorch with MPS support when available. The verification and recording of package installs should be performed on an actual M4-class machine. This chat environment does not expose an Apple Silicon runtime, so the installation compatibility check has not been executed here.

The recommended command sequence for an Apple Silicon host is:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install numpy scipy torch torchaudio
python -m pip install auraloss visqol peaq mosqito
python -m pip install -e .
```

If a package fails to build or import on arm64, it should be logged as disabled in the `metrics` registry and reported as a warning rather than crashing the search pipeline.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m patchhunter.cli render /path/to/patch.json --out /tmp/out.wav
```

## Project shape

- `patchhunter/core` — patch/voice graph and serialization
- `patchhunter/sources` — waveform generators
- `patchhunter/boxes` — processing blocks and registries
- `patchhunter/render` — deterministic graph rendering
- `patchhunter/metrics` — perceptual metric wrappers and calibration
- `patchhunter/search` — optimizer and evolutionary search loop
- `patchhunter/cli.py` — command-line interface
- `tests/` — regression tests for rendering and calibration behavior

## Current implementation highlights

- Deterministic patch JSON serialization
- Source generation for sine, square, saw, triangle, white noise, pink noise
- Gain and ADSR processing blocks
- Registry-based box registration
- Rendering pipeline with master chain and polymorphic patch objects
- CLI stubs for `render`, `search`, `calibrate`, and `compare`
- Test coverage for deterministic rendering and NaN safety on core primitives

## Roadmap

The repository is intentionally written to support the phases in the specification document:

1. Environment verification on Apple Silicon
2. Core Patch / Voice / serialization and render path
3. Metric wrappers and calibration
4. Remaining boxes and graph features
5. Evolutionary structure search
6. CLI logs, resume, benchmark, and validation scripts

## License

MIT
