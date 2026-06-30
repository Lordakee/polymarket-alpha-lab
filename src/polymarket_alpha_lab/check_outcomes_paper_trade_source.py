"""Paper-trade read source selection for ``check-outcomes``."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.supabase_paper_trade_journal_config import (
    SupabasePaperTradeJournalConfig,
)


class CheckOutcomesPaperTradeDbLoader(Protocol):
    def __call__(
        self,
        *,
        dsn: str,
        table_name: str,
    ) -> tuple[object, ...]:
        """Load paper trades from local Supabase/Postgres."""


def load_check_outcomes_paper_trade_records(
    *,
    journal_path: Path | str,
    db_config: SupabasePaperTradeJournalConfig,
    db_loader: CheckOutcomesPaperTradeDbLoader | None = None,
) -> tuple[PaperTradeRecord, ...]:
    """Return check-outcomes paper trades from DB when enabled, else JSONL.

    The paper trade DB loader returns rows newest-first for operational history
    views. Outcome replay consumes oldest-first records, so enabled DB reads are
    reversed into deterministic replay order before returning.
    """

    if type(db_config) is not SupabasePaperTradeJournalConfig:
        raise ValueError("db_config must be a SupabasePaperTradeJournalConfig")
    if db_config.enabled:
        if db_config.dsn is None:
            raise ValueError("paper trade DB source requires a DB DSN")
        if db_loader is None:
            raise ValueError(
                "db_loader is required when paper trade DB source is enabled",
            )
        records = _normalize_paper_trade_records(
            db_loader(dsn=db_config.dsn, table_name=db_config.table_name),
            source_name="paper trade DB source",
        )
        return tuple(reversed(records))

    try:
        return PaperTradeJournal.read(journal_path)
    except FileNotFoundError:
        return ()


def _normalize_paper_trade_records(
    records: object,
    *,
    source_name: str,
) -> tuple[PaperTradeRecord, ...]:
    if isinstance(records, (str, bytes)):
        raise ValueError(f"{source_name} must return an iterable of PaperTradeRecord values")
    try:
        normalized = tuple(records)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            f"{source_name} must return an iterable of PaperTradeRecord values",
        ) from exc
    for record in normalized:
        if type(record) is not PaperTradeRecord:
            raise ValueError(f"{source_name} must return only PaperTradeRecord values")
    return normalized


__all__ = (
    "CheckOutcomesPaperTradeDbLoader",
    "load_check_outcomes_paper_trade_records",
)
