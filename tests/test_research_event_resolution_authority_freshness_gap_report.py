from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_event_resolution_authority_freshness_gap_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_resolution_authority_freshness_gap_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "fresh_authority_pass_count": d("2.000000"),
        "fresh_authority_watch_count": d("1.000000"),
        "authority_family_pass_count": d("2.000000"),
        "authority_family_watch_count": d("1.000000"),
        "authority_agreement_watch_below": d("0.750000"),
        "authority_agreement_block_below": d("0.500000"),
        "authority_update_watch_age_seconds": d("3600.000000"),
        "authority_update_block_age_seconds": d("7200.000000"),
        "resolution_watch_seconds_remaining": d("1800.000000"),
        "resolution_block_seconds_remaining": d("600.000000"),
        "fresh_authority_count_gap_weight": d("0.250000"),
        "authority_family_gap_weight": d("0.150000"),
        "authority_agreement_gap_weight": d("0.200000"),
        "authority_freshness_gap_weight": d("0.300000"),
        "resolution_window_gap_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchEventResolutionAuthorityFreshnessGapConfig(**values)


def event(
    seed: str,
    *,
    fresh_authority_count: Decimal = d("2.000000"),
    authority_family_count: Decimal = d("2.000000"),
    authority_agreement_score: Decimal = d("0.900000"),
    newest_authority_update_age_seconds: Decimal = d("600.000000"),
    oldest_authority_update_age_seconds: Decimal = d("900.000000"),
    resolution_window_seconds: Decimal = d("3600.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchEventResolutionAuthorityFreshnessGapInput(
        event_digest=digest(f"{seed}-event"),
        resolution_authority_digest=digest(f"{seed}-authority"),
        fresh_authority_count=fresh_authority_count,
        authority_family_count=authority_family_count,
        authority_agreement_score=authority_agreement_score,
        newest_authority_update_age_seconds=newest_authority_update_age_seconds,
        oldest_authority_update_age_seconds=oldest_authority_update_age_seconds,
        resolution_window_seconds=resolution_window_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_event_resolution_authority_freshness_gap_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_is_pass_readonly_digest_validated_and_decimal_only() -> None:
    module = api()
    result = build_report()

    assert type(result) is module.ResearchEventResolutionAuthorityFreshnessGapReport
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.status == "pass"
    assert result.event_count == d("0.000000")
    assert result.pass_event_count == d("0.000000")
    assert result.watch_event_count == d("0.000000")
    assert result.block_event_count == d("0.000000")
    assert result.low_fresh_authority_event_count == d("0.000000")
    assert result.thin_authority_family_event_count == d("0.000000")
    assert result.low_authority_agreement_event_count == d("0.000000")
    assert result.stale_authority_update_event_count == d("0.000000")
    assert result.resolution_window_event_count == d("0.000000")
    assert result.highest_authority_freshness_gap_score == d("0.000000")
    assert result.lowest_authority_readiness_score == d("0.000000")
    assert result.oldest_authority_update_age_seconds == d("0.000000")
    assert result.nearest_resolution_window_seconds == d("0.000000")
    assert result.reason_codes == (
        "research_event_resolution_authority_freshness_gap_empty",
    )
    assert result.rows == ()
    assert len(result.derived_validation_digest) == 64
    int(result.derived_validation_digest, 16)
    assert (
        result.derived_validation_digest
        == module.research_event_resolution_authority_freshness_gap_report_digest(
            result,
        )
    )
    module.validate_research_event_resolution_authority_freshness_gap_report_digest(
        result,
    )
    payload = result.payload
    assert payload == (
        module.research_event_resolution_authority_freshness_gap_report_payload(result)
    )
    assert payload["event_count"] == "0.000000"
    assert_no_numeric_objects(payload)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_rows_classify_pass_watch_and_block_freshness_gaps_deterministically() -> None:
    result = build_report(
        event("official"),
        event(
            "watched",
            fresh_authority_count=d("1.000000"),
            authority_family_count=d("1.000000"),
            authority_agreement_score=d("0.700000"),
            oldest_authority_update_age_seconds=d("4000.000000"),
            resolution_window_seconds=d("1200.000000"),
        ),
        event(
            "blocked",
            fresh_authority_count=d("0.000000"),
            authority_family_count=d("0.000000"),
            authority_agreement_score=d("0.400000"),
            newest_authority_update_age_seconds=d("8000.000000"),
            oldest_authority_update_age_seconds=d("8000.000000"),
            resolution_window_seconds=d("300.000000"),
        ),
    )

    assert result.status == "block"
    assert result.event_count == d("3.000000")
    assert result.pass_event_count == d("1.000000")
    assert result.watch_event_count == d("1.000000")
    assert result.block_event_count == d("1.000000")
    assert result.low_fresh_authority_event_count == d("2.000000")
    assert result.thin_authority_family_event_count == d("2.000000")
    assert result.low_authority_agreement_event_count == d("2.000000")
    assert result.stale_authority_update_event_count == d("2.000000")
    assert result.resolution_window_event_count == d("2.000000")
    assert result.highest_authority_freshness_gap_score == d("0.903333")
    assert result.lowest_authority_readiness_score == d("0.096667")
    assert result.oldest_authority_update_age_seconds == d("8000.000000")
    assert result.nearest_resolution_window_seconds == d("300.000000")
    assert result.reason_codes == (
        "fresh_authority_count_block",
        "authority_family_diversity_block",
        "authority_agreement_low_block",
        "authority_update_age_block",
        "resolution_window_block",
        "fresh_authority_count_watch",
        "authority_family_diversity_watch",
        "authority_agreement_low_watch",
        "authority_update_age_watch",
        "resolution_window_watch",
    )

    assert tuple(row.event_digest for row in result.rows) == (
        digest("blocked-event"),
        digest("watched-event"),
        digest("official-event"),
    )
    blocked, watched, passed = result.rows
    assert blocked.status == "block"
    assert blocked.fresh_authority_band == "missing"
    assert blocked.authority_family_band == "single"
    assert blocked.authority_agreement_band == "fractured"
    assert blocked.authority_freshness_band == "expired"
    assert blocked.resolution_window_band == "immediate"
    assert blocked.authority_freshness_gap_score == d("0.903333")
    assert blocked.authority_readiness_score == d("0.096667")
    assert blocked.reason_codes == (
        "fresh_authority_count_block",
        "authority_family_diversity_block",
        "authority_agreement_low_block",
        "authority_update_age_block",
        "resolution_window_block",
    )

    assert watched.status == "watch"
    assert watched.fresh_authority_band == "thin"
    assert watched.authority_family_band == "thin"
    assert watched.authority_agreement_band == "weak"
    assert watched.authority_freshness_band == "stale"
    assert watched.resolution_window_band == "near"
    assert watched.authority_freshness_gap_score == d("0.460000")
    assert watched.authority_readiness_score == d("0.540000")
    assert watched.reason_codes == (
        "fresh_authority_count_watch",
        "authority_family_diversity_watch",
        "authority_agreement_low_watch",
        "authority_update_age_watch",
        "resolution_window_watch",
    )

    assert passed.status == "pass"
    assert passed.fresh_authority_band == "sufficient"
    assert passed.authority_family_band == "diverse"
    assert passed.authority_agreement_band == "aligned"
    assert passed.authority_freshness_band == "fresh"
    assert passed.resolution_window_band == "open"
    assert passed.authority_freshness_gap_score == d("0.057500")
    assert passed.authority_readiness_score == d("0.942500")
    assert passed.reason_codes == ("event_resolution_authority_freshness_gap_clear",)


def test_payload_is_deterministic_public_safe_and_digest_validated() -> None:
    module = api()
    report_a = build_report(
        event("official"),
        event(
            "blocked",
            fresh_authority_count=d("0.000000"),
            authority_family_count=d("0.000000"),
            authority_agreement_score=d("0.400000"),
            newest_authority_update_age_seconds=d("8000.000000"),
            oldest_authority_update_age_seconds=d("8000.000000"),
            resolution_window_seconds=d("300.000000"),
        ),
    )
    report_b = build_report(
        event(
            "blocked",
            fresh_authority_count=d("0.000000"),
            authority_family_count=d("0.000000"),
            authority_agreement_score=d("0.400000"),
            newest_authority_update_age_seconds=d("8000.000000"),
            oldest_authority_update_age_seconds=d("8000.000000"),
            resolution_window_seconds=d("300.000000"),
        ),
        event("official"),
    )

    payload_a = (
        module.research_event_resolution_authority_freshness_gap_report_payload(
            report_a,
        )
    )
    payload_b = (
        module.research_event_resolution_authority_freshness_gap_report_payload(
            report_b,
        )
    )
    digest_a = module.research_event_resolution_authority_freshness_gap_report_digest(
        report_a,
    )
    digest_b = module.research_event_resolution_authority_freshness_gap_report_digest(
        report_b,
    )
    encoded = json.dumps(payload_a, sort_keys=True, allow_nan=False)

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload_a["rows"][0]["authority_freshness_gap_score"] == "0.903333"
    assert (
        module.research_event_resolution_authority_freshness_gap_report_payload(
            payload_a,
        )
        == payload_a
    )
    module.validate_research_event_resolution_authority_freshness_gap_public_payload(
        payload_a,
    )
    assert_no_numeric_objects(payload_a)

    unsigned_payload = dict(payload_a)
    unsigned_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        unsigned_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert hashlib.sha256(canonical.encode()).hexdigest() == digest_a
    assert_payload_has_no_leaked_values(payload_a)
    for forbidden in unsafe_public_field_names() | {"http://", "https://", "://"}:
        assert forbidden not in encoded.lower()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)
    with pytest.raises(FrozenInstanceError):
        report_a.rows[0].authority_readiness_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_event_resolution_authority_freshness_gap_report_payload(
            {**payload_a, "market_id": "hidden"},
        )
    with pytest.raises(ValueError, match="numeric values"):
        module.research_event_resolution_authority_freshness_gap_report_payload(
            {**payload_a, "event_count": 2},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.research_event_resolution_authority_freshness_gap_report_payload(
            {**payload_a, "readonly": False},
        )


def test_validation_requires_digest_inputs_decimal_inputs_flags_and_safe_surface() -> None:
    module = api()

    with pytest.raises(ValueError, match="sha-256"):
        module.ResearchEventResolutionAuthorityFreshnessGapInput(
            event_digest=_join_parts("raw-", "candidate", "-id"),
            resolution_authority_digest=digest("authority"),
            fresh_authority_count=d("2.000000"),
            authority_family_count=d("2.000000"),
            authority_agreement_score=d("0.900000"),
            newest_authority_update_age_seconds=d("600.000000"),
            oldest_authority_update_age_seconds=d("900.000000"),
            resolution_window_seconds=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="fresh_authority_count must be a Decimal"):
        event("bad-decimal", fresh_authority_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_agreement_score must be a Decimal"):
        event("bad-ratio", authority_agreement_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_agreement_score must be a Decimal"):
        event(
            "bad-subclass",
            authority_agreement_score=_DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="six decimal places"):
        event("bad-scale", fresh_authority_count=d("2.0"))
    with pytest.raises(ValueError, match="integer Decimal"):
        event("bad-count", fresh_authority_count=d("1.500000"))
    with pytest.raises(ValueError, match="between zero and one"):
        event("bad-ratio-range", authority_agreement_score=d("1.000001"))
    with pytest.raises(ValueError, match="oldest_authority_update_age_seconds"):
        event(
            "bad-age-order",
            newest_authority_update_age_seconds=d("900.000000"),
            oldest_authority_update_age_seconds=d("600.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        event("bad-paper", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        event("bad-report", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        event("bad-readonly", readonly=False)
    with pytest.raises(ValueError, match="fresh_authority_watch_count"):
        config(fresh_authority_watch_count=d("3.000000"))
    with pytest.raises(ValueError, match="authority_agreement_block_below"):
        config(authority_agreement_block_below=d("0.800000"))
    with pytest.raises(ValueError, match="authority_update_watch_age_seconds"):
        config(authority_update_watch_age_seconds=d("7200.000000"))
    with pytest.raises(ValueError, match="resolution_block_seconds_remaining"):
        config(resolution_block_seconds_remaining=d("1800.000000"))
    with pytest.raises(ValueError, match="gap weights"):
        config(resolution_window_gap_weight=d("0.200000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_resolution_authority_freshness_gap_report(
            (),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_event_resolution_authority_freshness_gap_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    duplicate = event("duplicate")
    with pytest.raises(ValueError, match="unique"):
        build_report(duplicate, duplicate)

    result = build_report(event("valid"))
    with pytest.raises(ValueError, match="status"):
        replace(result, status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(result.rows[0], status="blocked")
    with pytest.raises(ValueError, match="authority_freshness_gap_score"):
        replace(result.rows[0], authority_freshness_gap_score=d("0.999999"))


def test_exports_frozen_dataclasses_status_vocabulary_and_module_scope() -> None:
    module = api()
    result = build_report(event("official"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_FRESHNESS_GAP_REPORT_CONFIG_VERSION",
        "RESEARCH_EVENT_RESOLUTION_AUTHORITY_FRESHNESS_GAP_STATUSES",
        "ResearchEventResolutionAuthorityFreshnessGapConfig",
        "ResearchEventResolutionAuthorityFreshnessGapInput",
        "ResearchEventResolutionAuthorityFreshnessGapReport",
        "ResearchEventResolutionAuthorityFreshnessGapRow",
        "build_research_event_resolution_authority_freshness_gap_report",
        "research_event_resolution_authority_freshness_gap_report_digest",
        "research_event_resolution_authority_freshness_gap_report_payload",
        "validate_research_event_resolution_authority_freshness_gap_public_payload",
        "validate_research_event_resolution_authority_freshness_gap_report_digest",
    )
    assert module.RESEARCH_EVENT_RESOLUTION_AUTHORITY_FRESHNESS_GAP_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(config())
    assert is_dataclass(event("official"))
    assert is_dataclass(result)
    assert is_dataclass(result.rows[0])

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().fresh_authority_pass_count = d("1.000000")

    public_fields = {
        field.name
        for cls in (type(result), type(result.rows[0]), type(event("official")))
        for field in fields(cls)
    }
    assert unsafe_public_field_names().isdisjoint(public_fields)
    for public_name in module.__all__:
        assert not contains_forbidden_public_surface(public_name)
    for public_field in public_fields:
        assert not contains_forbidden_public_surface(public_field)

    source_text = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "scrape",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("siz", "ing"),
        _join_parts("recomm", "endation"),
    ):
        assert forbidden not in source_text.lower()


def assert_no_numeric_objects(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_objects(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_numeric_objects(item)
    else:
        assert type(value) not in (Decimal, int, float)


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "candidate-",
        "candidate_id",
        "market-",
        "market_id",
        "market_slug",
        "question",
        "source_text",
        "source_url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)


def unsafe_public_field_names() -> set[str]:
    return {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
        "position_size",
        "recommendation",
    }


def contains_forbidden_public_surface(value: str) -> bool:
    lowered = value.lower()
    if any(
        phrase in lowered
        for phrase in (
            _join_parts("candidate", "_", "id"),
            _join_parts("market", "_", "id"),
            _join_parts("market", "_", "slug"),
            _join_parts("source", "_", "url"),
            _join_parts("source", "_", "text"),
            _join_parts("ta", "ble", "_name"),
        )
    ):
        return True
    tokens = tuple(token for token in lowered.replace("_", " ").split() if token)
    forbidden_tokens = frozenset(
        (
            "candidate",
            "market",
            _join_parts("que", "stion"),
            "url",
            "text",
            "dsn",
            _join_parts("ta", "ble"),
            _join_parts("to", "ken"),
            _join_parts("wal", "let"),
            _join_parts("ord", "er"),
            _join_parts("tra", "de"),
            _join_parts("data", "base"),
            _join_parts("net", "work"),
            "buy",
            "sell",
            _join_parts("recomm", "endation"),
            _join_parts("siz", "ing"),
        ),
    )
    return any(token in forbidden_tokens for token in tokens)
