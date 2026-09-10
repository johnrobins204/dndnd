# data/__init__.py
"""
Data package exports.

Expose models and repos for easy wiring:
    from data import models, repos
"""

__all__ = ["models", "repos"]

from . import (
    models,  # noqa: F401
    repos,  # noqa: F401
)
