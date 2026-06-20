"""Paper portfolio NAV v0 orchestrator (Stage 5).

Reads a paper-trade journal, builds the paper portfolio, fetches the current
order book for every held token, and marks NAV -- closing the "did I make
money?" loop. The only net-new logic here is the composition: every downstream
primitive (``PaperTradeJournal.read``, ``build_paper_portfolio``,
``normalize_order_book``, ``mark_paper_nav``) is already tested in isolation.

Protocol-only (Q5-style): this module does NOT import ``api``. It depends on a
local ``MarketNavClient`` Protocol whose only method is ``get_order_book``;
``cli.py`` constructs the concrete ``PolymarketPublicClient`` and injects it.

Phase 1 boundary: read local JSONL + read-only ``get_order_book`` fetch + pure
local NAV computation. No live orders, auth, wallets, private keys, credentials,
account/position/exchange-state reads, or exchange writes. The output
``PaperNavSnapshot`` is paper-only (``paper_only is True`` is hard-enforced).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.normalize import normalize_order_book
from polymarket_alpha_lab.positions import (
    PaperNavLog,
    PaperNavSnapshot,
    build_paper_portfolio,
    mark_paper_nav,
)

__all__ = ("mark_paper_portfolio_nav",)


@runtime_checkable
class MarketNavClient(Protocol):
    """Read-only order-book surface for NAV marking (Protocol-only).

    Only ``get_order_book(token_id=)`` is required. The concrete client is
    constructed in ``cli.py`` and injected into ``mark_paper_portfolio_nav``;
    this module never imports ``api``.
    """

    def get_order_book(self, *, token_id: str) -> Any:
        """Return the raw public CLOB order book payload for one token id."""


def mark_paper_portfolio_nav(
    journal_path: Path | str,
    *,
    starting_cash: Decimal,
    client: MarketNavClient,
    marked_at: datetime,
    nav_log_path: Path | str | None = None,
    nav_snapshot_sink: Callable[[PaperNavSnapshot], object] | None = None,
) -> PaperNavSnapshot:
    """Mark the paper portfolio NAV from a journal + live order books.

    Chain: read the journal -> build the portfolio -> fetch one book per held
    token -> mark NAV. An empty journal yields an empty portfolio, so the
    dict-comprehension over ``portfolio.positions`` performs no fetches and the
    resulting NAV equals ``starting_cash``.
    """
    _validate_nav_mark_inputs(
        starting_cash=starting_cash,
        client=client,
        marked_at=marked_at,
        nav_snapshot_sink=nav_snapshot_sink,
    )
    return _mark_paper_portfolio_nav_from_records(
        _read_paper_trade_journal_records(journal_path),
        starting_cash=starting_cash,
        client=client,
        marked_at=marked_at,
        nav_log_path=nav_log_path,
        nav_snapshot_sink=nav_snapshot_sink,
    )


def _read_paper_trade_journal_records(
    journal_path: Path | str,
) -> tuple[PaperTradeRecord, ...]:
    return PaperTradeJournal.read(journal_path)


def _mark_paper_portfolio_nav_from_records(
    records: tuple[PaperTradeRecord, ...],
    *,
    starting_cash: Decimal,
    client: MarketNavClient,
    marked_at: datetime,
    nav_log_path: Path | str | None = None,
    nav_snapshot_sink: Callable[[PaperNavSnapshot], object] | None = None,
) -> PaperNavSnapshot:
    _validate_nav_mark_inputs(
        starting_cash=starting_cash,
        client=client,
        marked_at=marked_at,
        nav_snapshot_sink=nav_snapshot_sink,
    )
    portfolio = build_paper_portfolio(records, starting_cash=starting_cash)
    books_by_token_id = {
        position.token_id: normalize_order_book(
            client.get_order_book(token_id=position.token_id),
            captured_at=marked_at,
        )
        for position in portfolio.positions
    }
    snapshot = mark_paper_nav(portfolio, books_by_token_id, marked_at=marked_at)
    if nav_log_path is not None:
        PaperNavLog(nav_log_path).append(snapshot)
    if nav_snapshot_sink is not None:
        nav_snapshot_sink(snapshot)
    return snapshot


def _validate_nav_mark_inputs(
    *,
    starting_cash: Decimal,
    client: MarketNavClient,
    marked_at: datetime,
    nav_snapshot_sink: Callable[[PaperNavSnapshot], object] | None,
) -> None:
    if not isinstance(starting_cash, Decimal):
        raise ValueError("starting_cash must be a Decimal")
    if starting_cash <= 0:
        raise ValueError("starting_cash must be positive")
    if not isinstance(client, MarketNavClient):
        raise ValueError("client must be a MarketNavClient")
    if not isinstance(marked_at, datetime):
        raise ValueError("marked_at must be a datetime")
    if nav_snapshot_sink is not None and not callable(nav_snapshot_sink):
        raise ValueError("nav_snapshot_sink must be callable or None")
