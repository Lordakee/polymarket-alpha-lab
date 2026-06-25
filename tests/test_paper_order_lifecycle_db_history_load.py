"""Tests for loading paper order lifecycle DB history reports."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_order_lifecycle import (
    NEXT_STEP_BY_STATUS,
    PaperOrderLifecycleRecord,
)
from polymarket_alpha_lab.paper_order_lifecycle_db_history import (
    PaperOrderLifecycleDbHistoryConfig,
)
from polymarket_alpha_lab.paper_order_lifecycle_db_history_load import (
    load_paper_order_lifecycle_db_history_report,
)


class ConnectionLike:
    def commit(self) -> None:
        raise AssertionError("history load helper must not commit")

    def rollback(self) -> None:
        raise AssertionError("history load helper must not rollback")

    def close(self) -> None:
        raise AssertionError("history load helper must not close")


def _filled_record(minutes: int, notional: str) -> PaperOrderLifecycleRecord:
    return PaperOrderLifecycleRecord(
        generated_at=datetime(2026, 6, 25, 9, minutes, tzinfo=UTC),
        config_version="paper-order-lifecycle-v0",
        lifecycle_status="paper_filled",
        recommended_next_step=NEXT_STEP_BY_STATUS["paper_filled"],
        source_execution_status="paper_submitted",
        source_execution_notional=Decimal(notional),
        fill_notional=Decimal(notional),
        is_terminal=True,
        reason_codes=("filled",),
    )


def test_load_helper_uses_injected_loader_reverses_desc_read_order_and_does_not_own_connection() -> None:
    connection = ConnectionLike()
    newest = _filled_record(3, "3.000000")
    oldest = _filled_record(1, "1.000000")
    calls: list[dict[str, object]] = []

    def fake_loader(
        supplied_connection: object,
        *,
        lifecycle_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[PaperOrderLifecycleRecord, ...]:
        calls.append(
            {
                "connection": supplied_connection,
                "lifecycle_status": lifecycle_status,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return (newest, oldest)

    report = load_paper_order_lifecycle_db_history_report(
        connection,
        lifecycle_status="paper_filled",
        limit=50,
        table_name="paper_order_lifecycle_records",
        config=PaperOrderLifecycleDbHistoryConfig(config_version="history-v1"),
        generated_at=datetime(2026, 6, 25, 12, tzinfo=UTC),
        loader=fake_loader,
    )

    assert calls == [
        {
            "connection": connection,
            "lifecycle_status": "paper_filled",
            "limit": 50,
            "table_name": "paper_order_lifecycle_records",
        },
    ]
    assert report.config_version == "history-v1"
    assert report.first_record_generated_at == oldest.generated_at
    assert report.latest_record_generated_at == newest.generated_at
    assert report.latest_fill_notional == Decimal("3.000000")


def test_load_helper_validates_config_and_loader() -> None:
    with pytest.raises(ValueError, match="config must be a PaperOrderLifecycleDbHistoryConfig"):
        load_paper_order_lifecycle_db_history_report(
            object(),
            limit=None,
            table_name="paper_order_lifecycle_records",
            config=object(),  # type: ignore[arg-type]
            generated_at=datetime(2026, 6, 25, 12, tzinfo=UTC),
            loader=lambda *args, **kwargs: (),
        )

    with pytest.raises(ValueError, match="loader must be callable"):
        load_paper_order_lifecycle_db_history_report(
            object(),
            limit=None,
            table_name="paper_order_lifecycle_records",
            config=PaperOrderLifecycleDbHistoryConfig(),
            generated_at=datetime(2026, 6, 25, 12, tzinfo=UTC),
            loader=object(),  # type: ignore[arg-type]
        )
