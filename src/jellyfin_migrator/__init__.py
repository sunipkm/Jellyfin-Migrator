import importlib.metadata
from .migrator import program_main

__version__ = importlib.metadata.version("jellyfin-migrator")

__all__ = [
    "__version__",
    "program_main",]
