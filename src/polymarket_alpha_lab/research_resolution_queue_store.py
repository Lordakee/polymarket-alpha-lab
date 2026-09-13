"""One consistent private-PostgreSQL snapshot for unconfirmed resolution work.

Reuse the existing driver, identity binding, readonly transaction and codec.
No DDL, connection implementation, hidden truncation or public fetch occurs.
"""
from __future__ import annotations

from polymarket_alpha_lab import research_capture_psycopg as capture
from polymarket_alpha_lab import research_resolution_store as reviews
from polymarket_alpha_lab.research_resolution import utc
from polymarket_alpha_lab.research_resolution_queue import (
    MAX_WORKLIST_BYTES, MAX_WORKLIST_MARKETS, ResolutionWorkItem, ResolutionWorklist,
)
from polymarket_alpha_lab.team_research_agent_types import integer

_UNRESOLVED = (" FROM research_capture.markets m WHERE m.registered_at<=%s AND NOT EXISTS "
    "(SELECT 1 FROM research_capture.outcomes o WHERE o.condition_id=m.condition_id AND o.recorded_at<=%s)")
_LATEST = ("WITH latest AS (SELECT DISTINCT ON (condition_id) " + reviews._COLUMNS
    + " FROM research_capture.resolution_reviews WHERE condition_id=ANY(%s) AND recorded_at<=%s "
      "ORDER BY condition_id,checked_at DESC,recorded_at DESC,review_id DESC) ")


def _counts(cursor, query, args, allowed):
    cursor.execute(query, args)
    counts = {}
    for cid, count in cursor.fetchall():
        integer("queue history count", count, 0, 2**63 - 1)
        if cid not in allowed or cid in counts:
            raise ValueError("resolution_queue_count_scope_invalid")
        counts[cid] = count
    return counts


def load_resolution_worklist_with_psycopg(
    dsn: str, *, max_markets: int = MAX_WORKLIST_MARKETS, recheck_after_seconds: int = 300,
) -> ResolutionWorklist:
    """List ALL visible registered markets lacking an outcome, or fail on limits.

    Unregistered public markets are not discovered. Unsupported legacy IDs,
    markets before their forecast cutoff, and incomplete research claims remain
    visible rather than disappearing. Only each market's latest visible review
    (by checked_at, receipt time, then ID) is decoded; this is not a full audit of
    older reviews or outcome truth. No caller-provided historical/future clock.
    """
    integer("max_markets", max_markets, 1, MAX_WORKLIST_MARKETS)
    integer("recheck_after_seconds", recheck_after_seconds, 60, 86400)

    def operation(cursor):
        cursor.execute("SELECT clock_timestamp()")
        at = utc("database clock", cursor.fetchone()[0])
        cursor.execute("SELECT count(*) FROM research_capture.markets WHERE registered_at<=%s", (at,))
        total = cursor.fetchone()[0]
        integer("registered count", total, 0, 2**63 - 1)
        cursor.execute("SELECT count(*)" + _UNRESOLVED, (at, at))
        count = cursor.fetchone()[0]
        integer("unresolved count", count, 0, 2**63 - 1)
        if count > max_markets:
            raise capture.ResearchCaptureConflict("resolution_queue_market_limit")
        if count > total:
            raise ValueError("resolution_queue_inventory_invalid")
        # Include incomplete work even for already settled markets. An empty
        # unresolved list must never look like a complete execution history.
        cursor.execute("SELECT count(*) FROM research_capture.execution_claims c "
            "LEFT JOIN research_capture.attempts a ON a.record_id=c.record_id AND a.recorded_at<=%s "
            "WHERE c.claimed_at<=%s AND a.record_id IS NULL", (at, at))
        all_incomplete = cursor.fetchone()[0]
        integer("incomplete execution count", all_incomplete, 0, 2**63 - 1)
        if not count:
            return ResolutionWorklist(at, (), total, recheck_after_seconds, all_incomplete)
        columns = ",".join("m." + name for name in capture._MARKET_COLUMNS.split(","))
        cursor.execute("SELECT " + columns + _UNRESOLVED + " ORDER BY m.forecast_cutoff_at,m.condition_id", (at, at))
        markets = tuple(capture.RegisteredResearchMarket(*row) for row in cursor.fetchall())
        ids = [market.condition_id for market in markets]
        if len(markets) != count or len(set(ids)) != count:
            raise ValueError("resolution_queue_inventory_invalid")
        cursor.execute(_LATEST + "SELECT count(*),coalesce(sum(octet_length(payload)),0) FROM latest", (ids, at))
        review_count, size = cursor.fetchone()
        if (type(review_count) is not int or not 0 <= review_count <= count
                or type(size) is not int or not 0 <= size <= MAX_WORKLIST_BYTES):
            raise capture.ResearchCaptureConflict("resolution_queue_payload_limit")
        cursor.execute(_LATEST + "SELECT " + reviews._COLUMNS + " FROM latest ORDER BY condition_id", (ids, at))
        rows = cursor.fetchall()  # Materialize before codec link lookups use this cursor.
        if len(rows) != review_count:
            raise ValueError("resolution_queue_inventory_invalid")
        latest = {}
        for row in rows:
            decoded = reviews._decode_row(cursor, row)
            cid = decoded.submission.condition_id
            if cid not in ids or cid in latest:
                raise ValueError("resolution_queue_review_scope_invalid")
            latest[cid] = decoded
        attempts = _counts(cursor,
            "SELECT condition_id,count(*) FROM research_capture.attempts "
            "WHERE condition_id=ANY(%s) AND recorded_at<=%s GROUP BY condition_id", (ids, at), ids)
        incomplete = _counts(cursor,
            "SELECT c.condition_id,count(*) FROM research_capture.execution_claims c "
            "LEFT JOIN research_capture.attempts a ON a.record_id=c.record_id AND a.recorded_at<=%s "
            "WHERE c.condition_id=ANY(%s) AND c.claimed_at<=%s AND a.record_id IS NULL GROUP BY c.condition_id",
            (at, ids, at), ids)
        return ResolutionWorklist(at, tuple(ResolutionWorkItem(market,
            attempts.get(market.condition_id, 0), incomplete.get(market.condition_id, 0), latest.get(market.condition_id))
            for market in markets), total, recheck_after_seconds, all_incomplete)

    return capture._local_transaction(dsn, operation, readonly=True)


__all__ = ("load_resolution_worklist_with_psycopg",)
