"""Command line interface for PatchHunter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from patchhunter.core import Patch


def _write_wav(path: Path, audio: np.ndarray, *, sample_rate: int = 44100) -> None:
    try:
        from scipy.io import wavfile
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("scipy is required to write WAV files.") from exc

    audio = np.asarray(audio, dtype=np.float32)
    wavfile.write(path, sample_rate, audio)


def _render_patch_file(patch_path: str | Path, *, output: str | Path | None = None, sr: int = 44100) -> np.ndarray:
    patch = Patch.from_file(patch_path)
    rendered = patch.render(sr=sr)
    if output is not None:
        _write_wav(Path(output), rendered, sample_rate=sr)
    return rendered


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="patchhunter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render = subparsers.add_parser("render", help="Render a patch JSON file to WAV")
    render.add_argument("patch_json", type=str)
    render.add_argument("--out", type=str, default=None)
    render.add_argument("--sr", type=int, default=44100)

    search = subparsers.add_parser("search", help="Run the search loop")
    search.add_argument("target", type=str)
    search.add_argument("--out", type=str, default="runs/exp1")
    search.add_argument("--time-budget", type=float, default=3600.0)
    search.add_argument("--max-nodes", type=int, default=32)
    search.add_argument("--seed", type=int, default=0)

    calibrate = subparsers.add_parser("calibrate", help="Perform calibration on a target WAV")
    calibrate.add_argument("target", type=str)
    calibrate.add_argument("--out", type=str, default="runs/exp1/calibration.json")

    compare = subparsers.add_parser("compare", help="Compare target and candidate WAVs")
    compare.add_argument("target", type=str)
    compare.add_argument("candidate", type=str)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "render":
        _render_patch_file(args.patch_json, output=args.out, sr=args.sr)
        return

    if args.command == "search":
        print(json.dumps({
            "status": "not_implemented",
            "target": args.target,
            "out": args.out,
            "time_budget": args.time_budget,
            "max_nodes": args.max_nodes,
            "seed": args.seed,
        }, sort_keys=True))
        return

    if args.command == "calibrate":
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"status": "not_implemented", "target": args.target}, sort_keys=True, indent=2), encoding="utf-8")
        return

    if args.command == "compare":
        print(json.dumps({"status": "not_implemented", "target": args.target, "candidate": args.candidate}, sort_keys=True))
        return


if __name__ == "__main__":
    main()
