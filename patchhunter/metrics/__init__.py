"""Sources package."""

from patchhunter.core.patch import PatchRegistry, generate_source


def _register_default_sources() -> None:
    for source_name in ["sine", "square", "saw", "triangle", "white_noise", "pink_noise"]:
        PatchRegistry.register_source(source_name, generate_source)


_register_default_sources()

__all__ = ["PatchRegistry", "generate_source"]
