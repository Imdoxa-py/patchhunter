"""Boxes package."""

from patchhunter.core.patch import BoxSpec, PatchRegistry


def _register_default_boxes() -> None:
    PatchRegistry.register_box("gain", lambda x, params: x)
    PatchRegistry.register_box("adsr", lambda x, params: x)


_register_default_boxes()

__all__ = ["BoxSpec", "PatchRegistry"]
