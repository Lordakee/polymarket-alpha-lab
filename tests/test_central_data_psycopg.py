import pytest

from polymarket_alpha_lab import central_data_psycopg as module
from polymarket_alpha_lab.central_data_psycopg import (
    CentralDataPsycopg,
    CentralDataPsycopgError,
)


LOCAL = "postgresql://postgres:secret@localhost:54322/postgres"


class FakeConnection:
    def __init__(self) -> None:
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0
        self.autocommit = False

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    def close(self) -> None:
        self.close_count += 1


def test_validation_precedes_driver_import(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fail_driver() -> object:
        nonlocal called
        called = True
        raise AssertionError("driver imported")

    monkeypatch.setattr(module, "_driver_parts", fail_driver)
    with pytest.raises(ValueError):
        module._connect("postgresql://postgres@remote.example/postgres", readonly=False)
    assert called is False


def test_write_commits_and_closes(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = FakeConnection()
    adapter = module._JsonConnection(raw, lambda value: value)
    monkeypatch.setattr(module, "_connect", lambda dsn, readonly: adapter)
    result = module._write(LOCAL, lambda store: "ok")
    assert result == "ok"
    assert raw.commit_count == 1
    assert raw.rollback_count == 0
    assert raw.close_count == 1


def test_write_rolls_back_and_preserves_fixed_error(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = FakeConnection()
    adapter = module._JsonConnection(raw, lambda value: value)
    monkeypatch.setattr(module, "_connect", lambda dsn, readonly: adapter)
    with pytest.raises(CentralDataPsycopgError) as caught:
        module._write(LOCAL, lambda store: (_ for _ in ()).throw(RuntimeError("secret body")))
    assert caught.value.code == "central_data_persistence_failed"
    assert "secret body" not in str(caught.value)
    assert raw.rollback_count == 1
    assert raw.close_count == 1


def test_adapter_repr_redacts_dsn() -> None:
    adapter = CentralDataPsycopg(LOCAL)
    assert "secret" not in repr(adapter)
    assert "<redacted>" in repr(adapter)
