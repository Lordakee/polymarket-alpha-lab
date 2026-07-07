import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import ROUND_DOWN, Decimal, localcontext

import pytest

from polymarket_alpha_lab.market_close_resolution_readiness_digest import (
    DEFAULT_MARKET_CLOSE_RESOLUTION_READINESS_DIGEST_CONFIG_VERSION,
    MarketCloseResolutionReadinessDigestConfig,
    MarketCloseResolutionReadinessDigestInput,
    MarketCloseResolutionReadinessDigestReasonCodeCount,
    build_market_close_resolution_readiness_digest,
    market_close_resolution_readiness_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def config(**overrides: object) -> MarketCloseResolutionReadinessDigestConfig:
    values = {
        "config_version": "market-close-resolution-readiness-digest-v0",
        "watch_close_within_seconds": Decimal("3600"),
        "block_close_after_seconds": Decimal("300"),
        "acknowledgement_freshness_seconds": Decimal("900"),
        "min_outcome_evidence_count": Decimal("2"),
    }
    values.update(overrides)
    return MarketCloseResolutionReadinessDigestConfig(**values)


def market_input(
    market_slug: str = "alpha",
    *,
    category: str = "crypto",
    event_slug: str = "btc-daily",
    close_time: datetime | None = None,
    required_resolution_sources: tuple[str, ...] = ("rules", "oracle"),
    covered_resolution_sources: tuple[str, ...] = ("oracle", "rules"),
    acknowledged_at: datetime | None = None,
    outcome_evidence_count: Decimal = Decimal("2"),
    unresolved_ambiguity_count: Decimal = Decimal("0"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketCloseResolutionReadinessDigestInput:
    return MarketCloseResolutionReadinessDigestInput(
        market_slug=market_slug,
        category=category,
        event_slug=event_slug,
        close_time=close_time or GENERATED_AT + timedelta(hours=2),
        required_resolution_sources=required_resolution_sources,
        covered_resolution_sources=covered_resolution_sources,
        acknowledged_at=acknowledged_at or GENERATED_AT - timedelta(minutes=5),
        outcome_evidence_count=outcome_evidence_count,
        unresolved_ambiguity_count=unresolved_ambiguity_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    markets: tuple[MarketCloseResolutionReadinessDigestInput, ...],
    *,
    cfg: MarketCloseResolutionReadinessDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
):
    return build_market_close_resolution_readiness_digest(
        markets,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_without_rows() -> None:
    readiness = report(())

    assert readiness.generated_at == GENERATED_AT
    assert readiness.generated_at.tzinfo is UTC
    assert readiness.config_version == "market-close-resolution-readiness-digest-v0"
    assert readiness.digest_status == "blocked"
    assert readiness.recommended_next_step == "block_market_close_resolution_use"
    assert readiness.input_count == Decimal("0")
    assert readiness.row_count == Decimal("0")
    assert readiness.ready_count == Decimal("0")
    assert readiness.watch_count == Decimal("0")
    assert readiness.blocked_count == Decimal("0")
    assert readiness.category_rollups == ()
    assert readiness.rows == ()
    assert readiness.reason_codes == (
        "market_close_resolution_readiness_digest_empty_input",
    )
    assert readiness.reason_code_counts == (
        MarketCloseResolutionReadinessDigestReasonCodeCount(
            reason_code="market_close_resolution_readiness_digest_empty_input",
            count=Decimal("1"),
        ),
    )
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True


def test_ready_markets_have_complete_sources_fresh_ack_and_evidence() -> None:
    readiness = report(
        (
            market_input("beta", category="sports"),
            market_input("alpha", category="crypto"),
        )
    )

    assert readiness.digest_status == "ready"
    assert readiness.recommended_next_step == "allow_market_close_resolution_use"
    assert readiness.input_count == Decimal("2")
    assert readiness.row_count == Decimal("2")
    assert readiness.ready_count == Decimal("2")
    assert readiness.watch_count == Decimal("0")
    assert readiness.blocked_count == Decimal("0")
    assert readiness.required_resolution_source_count == Decimal("4")
    assert readiness.covered_resolution_source_count == Decimal("4")
    assert readiness.resolution_source_coverage_ratio == Decimal("1.000000")
    assert tuple(row.market_slug for row in readiness.rows) == ("alpha", "beta")
    assert tuple(row.readiness_status for row in readiness.rows) == ("ready", "ready")
    assert readiness.rows[0].seconds_until_close == Decimal("7200")
    assert readiness.rows[0].acknowledgement_age_seconds == Decimal("300")
    assert readiness.rows[0].resolution_source_coverage_ratio == Decimal("1.000000")
    assert readiness.rows[0].reason_codes == (
        "acknowledgement_fresh",
        "close_window_clear",
        "outcome_evidence_complete",
        "resolution_sources_complete",
        "unresolved_ambiguity_absent",
    )
    assert tuple(rollup.category for rollup in readiness.category_rollups) == (
        "crypto",
        "sports",
    )
    assert readiness.reason_code_counts == (
        MarketCloseResolutionReadinessDigestReasonCodeCount(
            reason_code="acknowledgement_fresh",
            count=Decimal("2"),
        ),
        MarketCloseResolutionReadinessDigestReasonCodeCount(
            reason_code="close_window_clear",
            count=Decimal("2"),
        ),
        MarketCloseResolutionReadinessDigestReasonCodeCount(
            reason_code="outcome_evidence_complete",
            count=Decimal("2"),
        ),
        MarketCloseResolutionReadinessDigestReasonCodeCount(
            reason_code="resolution_sources_complete",
            count=Decimal("2"),
        ),
        MarketCloseResolutionReadinessDigestReasonCodeCount(
            reason_code="unresolved_ambiguity_absent",
            count=Decimal("2"),
        ),
    )


def test_watch_close_pressure_before_block_window() -> None:
    readiness = report(
        (
            market_input(
                "alpha",
                close_time=GENERATED_AT + timedelta(minutes=30),
            ),
        )
    )

    assert readiness.digest_status == "watch"
    assert readiness.ready_count == Decimal("0")
    assert readiness.watch_count == Decimal("1")
    assert readiness.blocked_count == Decimal("0")
    assert readiness.rows[0].readiness_status == "watch"
    assert readiness.rows[0].seconds_until_close == Decimal("1800")
    assert readiness.rows[0].reason_codes == (
        "acknowledgement_fresh",
        "close_window_near",
        "outcome_evidence_complete",
        "resolution_sources_complete",
        "unresolved_ambiguity_absent",
    )
    assert readiness.category_rollups[0].watch_count == Decimal("1")


def test_blocked_missing_required_resolution_source() -> None:
    readiness = report(
        (
            market_input(
                "alpha",
                required_resolution_sources=("rules", "oracle", "settlement_policy"),
                covered_resolution_sources=("rules",),
            ),
        )
    )

    assert readiness.digest_status == "blocked"
    assert readiness.ready_count == Decimal("0")
    assert readiness.blocked_count == Decimal("1")
    assert readiness.required_resolution_source_count == Decimal("3")
    assert readiness.covered_resolution_source_count == Decimal("1")
    assert readiness.resolution_source_coverage_ratio == Decimal("0.333333")
    assert readiness.rows[0].readiness_status == "blocked"
    assert readiness.rows[0].missing_resolution_sources == (
        "oracle",
        "settlement_policy",
    )
    assert "resolution_sources_missing" in readiness.rows[0].reason_codes
    assert readiness.reason_code_counts == tuple(
        sorted(readiness.reason_code_counts, key=lambda item: item.reason_code)
    )


def test_resolution_source_coverage_rounding_is_context_independent() -> None:
    with localcontext() as ctx:
        ctx.rounding = ROUND_DOWN
        readiness = report(
            (
                market_input(
                    "alpha",
                    required_resolution_sources=("rules", "oracle", "settlement_policy"),
                    covered_resolution_sources=("rules", "oracle"),
                ),
            )
        )

    assert readiness.resolution_source_coverage_ratio == Decimal("0.666667")
    assert readiness.rows[0].resolution_source_coverage_ratio == Decimal("0.666667")
    assert readiness.category_rollups[0].resolution_source_coverage_ratio == Decimal(
        "0.666667"
    )


def test_stale_acknowledgement_blocks_otherwise_ready_market() -> None:
    readiness = report(
        (
            market_input(
                "alpha",
                acknowledged_at=GENERATED_AT - timedelta(minutes=20),
            ),
        )
    )

    assert readiness.digest_status == "blocked"
    assert readiness.blocked_count == Decimal("1")
    assert readiness.rows[0].acknowledgement_age_seconds == Decimal("1200")
    assert "acknowledgement_stale" in readiness.rows[0].reason_codes


def test_unresolved_ambiguity_blocks_and_incomplete_evidence_watches() -> None:
    readiness = report(
        (
            market_input(
                "ambiguous",
                unresolved_ambiguity_count=Decimal("1"),
            ),
            market_input(
                "thin-evidence",
                outcome_evidence_count=Decimal("1"),
            ),
        )
    )

    assert readiness.digest_status == "blocked"
    assert tuple(row.market_slug for row in readiness.rows) == (
        "ambiguous",
        "thin-evidence",
    )
    assert tuple(row.readiness_status for row in readiness.rows) == (
        "blocked",
        "watch",
    )
    assert "unresolved_ambiguity_present" in readiness.rows[0].reason_codes
    assert "outcome_evidence_incomplete" in readiness.rows[1].reason_codes
    assert readiness.category_rollups[0].blocked_count == Decimal("1")
    assert readiness.category_rollups[0].watch_count == Decimal("1")


def test_sorting_is_deterministic_for_rows_and_category_rollups() -> None:
    readiness = report(
        (
            market_input("zulu", category="sports", event_slug="event-b"),
            market_input("alpha", category="crypto", event_slug="event-b"),
            market_input("alpha", category="crypto", event_slug="event-a"),
        )
    )

    assert tuple(
        (row.category, row.event_slug, row.market_slug) for row in readiness.rows
    ) == (
        ("crypto", "event-a", "alpha"),
        ("crypto", "event-b", "alpha"),
        ("sports", "event-b", "zulu"),
    )
    assert tuple(rollup.category for rollup in readiness.category_rollups) == (
        "crypto",
        "sports",
    )


def test_payload_helper_serializes_decimals_as_strings_and_no_floats() -> None:
    readiness = report(
        (
            market_input("alpha"),
            market_input("pressure", close_time=GENERATED_AT + timedelta(minutes=30)),
        ),
        generated_at=datetime(2026, 7, 2, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = market_close_resolution_readiness_digest_payload(readiness)
    dumped = json.dumps(payload, sort_keys=True)
    loaded = json.loads(dumped)

    assert loaded["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert loaded["paper_only"] is True
    assert loaded["report_only"] is True
    assert loaded["readonly"] is True
    assert loaded["derived_validation_digest"].startswith("mcrrd-v0:")
    assert loaded["rows"][0]["derived_validation_digest"].startswith("mcrrd-v0:")
    assert loaded["category_rollups"][0]["derived_validation_digest"].startswith("mcrrd-v0:")
    assert loaded["reason_code_counts"][0]["derived_validation_digest"].startswith("mcrrd-v0:")
    assert loaded["row_count"] == "2"
    assert loaded["rows"][0]["seconds_until_close"] == "7200"
    assert loaded["rows"][0]["resolution_source_coverage_ratio"] == "1.000000"
    assert not any(isinstance(value, float) for value in _walk_values(loaded))


def test_payload_accepts_plain_readonly_dicts_and_rejects_numeric_drift() -> None:
    payload = market_close_resolution_readiness_digest_payload(
        {
            "generated_at": GENERATED_AT,
            "row_count": Decimal("1"),
            "rows": (
                {
                    "market_slug": "alpha",
                    "resolution_source_coverage_ratio": Decimal("1.000000"),
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            ),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
    )

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["row_count"] == "1"
    assert payload["rows"][0]["resolution_source_coverage_ratio"] == "1.000000"

    with pytest.raises(ValueError, match="paper_only"):
        market_close_resolution_readiness_digest_payload(
            {"paper_only": False, "report_only": True, "readonly": True}
        )

    with pytest.raises(ValueError, match="unsupported value"):
        market_close_resolution_readiness_digest_payload(
            {"row_count": 1, "paper_only": True, "report_only": True, "readonly": True}
        )

    with pytest.raises(ValueError, match="unsupported value"):
        market_close_resolution_readiness_digest_payload(
            {
                "row_count": _DecimalSubclass("1"),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            }
        )


def test_payload_rejects_nested_plain_objects_without_hard_flags() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        market_close_resolution_readiness_digest_payload(
            {
                "rows": ({"market_slug": "alpha"},),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            }
        )


def test_derived_validation_digest_revalidates_public_report_payload() -> None:
    readiness = report((market_input("alpha"),))
    row = readiness.rows[0]

    assert readiness.derived_validation_digest.startswith("mcrrd-v0:")
    assert row.derived_validation_digest.startswith("mcrrd-v0:")

    object.__setattr__(row, "market_slug", "beta")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        market_close_resolution_readiness_digest_payload(readiness)


def test_unsafe_public_surface_is_rejected_for_inputs_and_payloads() -> None:
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
    )

    for unsafe_term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public surface"):
            market_input(market_slug=f"{unsafe_term}-surface")

        with pytest.raises(ValueError, match="unsafe public surface"):
            market_close_resolution_readiness_digest_payload(
                {"note": unsafe_term, "paper_only": True, "report_only": True, "readonly": True}
            )


def test_validation_errors_reject_invalid_types_values_flags_and_consistency() -> None:
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=" digest-v0")
    with pytest.raises(ValueError, match="watch_close_within_seconds"):
        config(watch_close_within_seconds=Decimal("-1"))
    with pytest.raises(ValueError, match="block_close_after_seconds"):
        config(block_close_after_seconds=_DecimalSubclass("300"))
    with pytest.raises(ValueError, match="min_outcome_evidence_count"):
        config(min_outcome_evidence_count=_IntSubclass(2))
    with pytest.raises(ValueError, match="market_slug"):
        market_input(market_slug=" alpha")
    with pytest.raises(ValueError, match="close_time"):
        market_input(close_time=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="required_resolution_sources"):
        market_input(required_resolution_sources=())
    with pytest.raises(ValueError, match="covered_resolution_sources"):
        market_input(covered_resolution_sources=("rules", "rules"))
    with pytest.raises(ValueError, match="outcome_evidence_count"):
        market_input(outcome_evidence_count=Decimal("1.5"))
    with pytest.raises(ValueError, match="unresolved_ambiguity_count"):
        market_input(unresolved_ambiguity_count=Decimal("-1"))
    with pytest.raises(ValueError, match="paper_only"):
        market_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        market_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        market_input(readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        report((market_input("alpha"),), generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="acknowledged_at"):
        market_input(
            acknowledged_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTz()),
        )

    readiness = report((market_input("alpha"),))
    with pytest.raises(ValueError, match="row_count"):
        replace(readiness, row_count=Decimal("2"))
    with pytest.raises(ValueError, match="ready_count"):
        replace(readiness, ready_count=Decimal("0"))
    with pytest.raises(ValueError, match="resolution_source_coverage_ratio"):
        replace(readiness, resolution_source_coverage_ratio=Decimal("0.500000"))


def test_public_dataclasses_are_frozen() -> None:
    readiness = report((market_input("alpha"),))
    values = (
        config(),
        market_input("alpha"),
        readiness.rows[0],
        readiness.category_rollups[0],
        readiness.reason_code_counts[0],
        readiness,
    )

    for value in values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_static_forbidden_surface_terms_and_no_float_literals() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_close_resolution_readiness_digest"
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    forbidden_terms = (
        "psycopg",
        "sql",
        "sqlite",
        "requests",
        "urllib",
        "httpx",
        "socket",
        "open(",
        "click",
        "argparse",
        "trade",
        "trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "signing",
        "advice",
    )
    lowered = source.lower()
    assert not any(term in lowered for term in forbidden_terms)


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values: list[object] = []
        for item in value.values():
            values.extend(_walk_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_values(item))
        return tuple(values)
    return (value,)
