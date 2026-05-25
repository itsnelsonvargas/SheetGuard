"""
Plugin extension point for future validators and integrations.

Register custom validators via entry points or dynamic import:

    from sheetguard.plugins import register_validator
    register_validator("my_check", MyValidatorClass)
"""

from __future__ import annotations

from typing import Any, Type

_VALIDATORS: dict[str, Type[Any]] = {}


def register_validator(name: str, cls: Type[Any]) -> None:
    """Register a plugin validator class for future pipeline integration."""
    _VALIDATORS[name] = cls


def get_validator(name: str) -> Type[Any] | None:
    return _VALIDATORS.get(name)


def list_validators() -> list[str]:
    return list(_VALIDATORS.keys())
