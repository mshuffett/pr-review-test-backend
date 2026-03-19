import pytest

from src.storage import KeyNotFoundError, Storage


@pytest.fixture
def store() -> Storage:
    return Storage()


def test_set_and_get(store: Storage) -> None:
    store.set("foo", 42)
    assert store.get("foo") == 42


def test_get_missing_key_raises(store: Storage) -> None:
    with pytest.raises(KeyNotFoundError):
        store.get("nope")


def test_delete(store: Storage) -> None:
    store.set("k", "v")
    store.delete("k")
    assert not store.exists("k")


def test_delete_missing_raises(store: Storage) -> None:
    with pytest.raises(KeyNotFoundError):
        store.delete("missing")


def test_exists(store: Storage) -> None:
    assert not store.exists("x")
    store.set("x", 1)
    assert store.exists("x")


def test_keys(store: Storage) -> None:
    store.set("a", 1)
    store.set("b", 2)
    assert sorted(store.keys()) == ["a", "b"]


def test_clear(store: Storage) -> None:
    store.set("a", 1)
    store.set("b", 2)
    store.clear()
    assert store.keys() == []
