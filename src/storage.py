"""Simple key-value storage abstraction."""

from __future__ import annotations

from typing import Any


class KeyNotFoundError(Exception):
    """Raised when a key does not exist in storage."""


class Storage:
    """In-memory key-value store."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def get(self, key: str) -> Any:
        """Return the value for *key*, or raise KeyNotFoundError."""
        try:
            return self._data[key]
        except KeyError:
            raise KeyNotFoundError(key) from None

    def set(self, key: str, value: Any) -> None:
        """Store *value* under *key*."""
        self._data[key] = value

    def delete(self, key: str) -> None:
        """Remove *key* from the store. Raises KeyNotFoundError if missing."""
        try:
            del self._data[key]
        except KeyError:
            raise KeyNotFoundError(key) from None

    def exists(self, key: str) -> bool:
        """Return True if *key* is present."""
        return key in self._data

    def keys(self) -> list[str]:
        """Return all stored keys."""
        return list(self._data.keys())

    def clear(self) -> None:
        """Remove all entries."""
        self._data.clear()
