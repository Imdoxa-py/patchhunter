"""Rendering package root."""

from patchhunter.core.patch import Patch


def render_patch(patch: Patch, *, sr: int | None = None, length: int | None = None):
    return patch.render(sr=sr, length=length)


__all__ = ["render_patch"]
