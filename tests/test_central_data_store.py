from datetime import UTC, datetime

import pytest

from polymarket_alpha_lab.central_data_contracts import (
    EvidenceReference,
    Freshness,
    NormalizedObservation,
    ParseState,
    RawResponse,
    SourceDefinition,
)
from polymarket_alpha_lab.central_data_db_row import NormalizedObservationRow, RawEventRow
from polymarket_alpha_lab.central_data_store import (
    CentralDataStore,
    CentralDataStoreError,
)


def _row() -> RawEventRow:
    source = SourceDefinition("source-a", "official", "https://example.com/data", "application/json", 60)
    raw = RawResponse(
        200,
        {"content-type": "application/json"},
        b"{}",
        source.url_template,
        retrieval_time=datetime.now(UTC),
        request_url=source.url_template,
        content_type="application/json",
    )
    return RawEventRow.from_contracts(source, raw)


class FakeCursor:
    def __init__(self, results: list[object]) -> None:
        self.results = iter(results)
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self.close_count = 0

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> None:
        self.calls.append((sql, params))

    def fetchone(self) -> object:
        try:
            return next(self.results)
        except StopIteration:
            return None

    def fetchall(self) -> list[object]:
        return []

    def close(self) -> None:
        self.close_count += 1


class FakeConnection:
    def __init__(self, cursor_results: list[list[object]]) -> None:
        self.cursors = [FakeCursor(results) for results in cursor_results]

    def cursor(self) -> FakeCursor:
        return self.cursors.pop(0)


def test_raw_insert_checks_retention_before_binding_and_closes_cursors() -> None:
    row = _row()
    connection = FakeConnection([[{"retention_ready": False}]])
    with pytest.raises(CentralDataStoreError) as caught:
        CentralDataStore(connection).insert_raw_event(row)
    assert caught.value.code == "central_data_retention_not_ready"
    assert len(connection.cursors) == 0


def test_raw_insert_is_parameterized_and_returns_idempotent_status() -> None:
    row = _row()
    connection = FakeConnection([[{"retention_ready": True}], [(row.raw_event_id,)]])
    result = CentralDataStore(connection).insert_raw_event(row)
    assert result.inserted is True
    insert_cursor = connection.cursors  # both cursors were consumed
    assert result.identity == row.raw_event_id


def test_normalized_insert_refuses_orphaned_raw_row() -> None:
    row = _row()
    connection = FakeConnection([[None]])
    observation = NormalizedObservation(
        row.source_id,
        row.retrieval_time,
        None,
        Freshness.UNKNOWN,
        ParseState.UNKNOWN,
        EvidenceReference(
            row.source_id,
            row.retrieval_time,
            row.retrieval_time,
            row.raw_payload_sha256,
        ),
    )
    normalized = NormalizedObservationRow.from_contracts(
        SourceDefinition(row.source_id, row.source_family, row.endpoint_url, row.content_type, 60, row.official_source),
        observation,
        row.identity,
    )
    with pytest.raises(CentralDataStoreError) as caught:
        CentralDataStore(connection).insert_normalized_observation(normalized)
    assert caught.value.code == "raw_event_unavailable"


def test_normalized_read_filters_validate_source_and_raw_event_identifiers() -> None:
    store = CentralDataStore(FakeConnection([]))
    with pytest.raises(ValueError, match="source_id"):
        store.get_normalized_observations(source_id=" source-a")
    with pytest.raises(ValueError, match="raw_event_id"):
        store.get_normalized_observations(raw_event_id="not-a-sha256")
