from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_crypto_event_memory_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_EVENT_MEMORY_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoEventMemoryDigestConfig,
    MarketResearchCryptoEventMemoryDigestEvent,
    MarketResearchCryptoEventMemoryDigestReasonCodeCount,
    MarketResearchCryptoEventMemoryDigestReport,
    MarketResearchCryptoEventMemoryDigestRow,
    build_market_research_crypto_event_memory_digest,
    market_research_crypto_event_memory_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _IntSubclass(int):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> MarketResearchCryptoEventMemoryDigestConfig:
    values = {
        "config_version": DEFAULT_MARKET_RESEARCH_CRYPTO_EVENT_MEMORY_DIGEST_CONFIG_VERSION,
        "max_event_age_seconds": d("7200.000000"),
        "min_memory_match_count": d("2.000000"),
        "min_memory_recall_ratio": d("0.500000"),
    }
    values.update(overrides)
    return MarketResearchCryptoEventMemoryDigestConfig(**values)


def _event(
    condition_id: str = "condition_alpha",
    event_key: str = "btc_etf_flow",
    *,
    event_family: str = "btc",
    observed_at: datetime = GENERATED_AT,
    memory_match_count: Decimal = d("2.000000"),
    candidate_memory_count: Decimal = d("3.000000"),
    source_count: Decimal = d("2.000000"),
    evidence_conflict_count: Decimal = d("0.000000"),
    event_config_version: str = "crypto-memory-event-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchCryptoEventMemoryDigestEvent:
    return MarketResearchCryptoEventMemoryDigestEvent(
        condition_id=condition_id,
        event_key=event_key,
        event_family=event_family,
        observed_at=observed_at,
        memory_match_count=memory_match_count,
        candidate_memory_count=candidate_memory_count,
        source_count=source_count,
        evidence_conflict_count=evidence_conflict_count,
        event_config_version=event_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    *events: MarketResearchCryptoEventMemoryDigestEvent,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoEventMemoryDigestConfig | None = None,
) -> MarketResearchCryptoEventMemoryDigestReport:
    return build_market_research_crypto_event_memory_digest(
        events,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_crypto_event_memory_digest_summarizes_stale_missing_and_conflicting_memory() -> None:
    report = _report(
        _event(
            "condition_beta",
            "eth_dencun",
            event_family="eth",
            observed_at=GENERATED_AT - timedelta(seconds=8_000),
            memory_match_count=d("1.000000"),
            candidate_memory_count=d("4.000000"),
            source_count=d("1.000000"),
            evidence_conflict_count=d("1.000000"),
        ),
        _event(
            "condition_alpha",
            "btc_etf_flow",
            event_family="btc",
            observed_at=GENERATED_AT - timedelta(seconds=60),
            memory_match_count=d("3.000000"),
            candidate_memory_count=d("4.000000"),
            source_count=d("3.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.summary_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_event_memory_digest"
    )
    assert report.event_count == d("2.000000")
    assert report.clear_event_count == d("1.000000")
    assert report.watch_event_count == d("0.000000")
    assert report.blocked_event_count == d("1.000000")
    assert report.memory_match_count == d("4.000000")
    assert report.candidate_memory_count == d("8.000000")
    assert report.memory_recall_ratio == d("0.500000")
    assert report.stale_event_count == d("1.000000")
    assert report.conflict_event_count == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.event_key) for row in report.rows) == (
        ("condition_beta", "eth_dencun"),
        ("condition_alpha", "btc_etf_flow"),
    )
    beta = report.rows[0]
    assert beta.summary_status == "blocked"
    assert beta.memory_recall_ratio == d("0.250000")
    assert beta.event_age_seconds == d("8000.000000")
    assert beta.reason_codes == (
        "market_research_crypto_event_memory_conflict_present",
        "market_research_crypto_event_memory_insufficient_memory_matches",
        "market_research_crypto_event_memory_low_recall_ratio",
        "market_research_crypto_event_memory_single_source",
        "market_research_crypto_event_memory_stale_event",
    )
    assert report.reason_codes == beta.reason_codes


def test_crypto_event_memory_digest_normalizes_timezones_counts_reasons_and_sorting() -> None:
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 2, 12, 0, tzinfo=timezone(timedelta(hours=1)))
    event = _event(
        "condition_gamma",
        "sol_etf",
        event_family="sol",
        observed_at=observed_at,
        memory_match_count=d("0.000000"),
        candidate_memory_count=d("2.000000"),
        source_count=d("2.000000"),
    )

    report = _report(
        event,
        generated_at=generated_at,
    )

    assert event.observed_at == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    assert event.observed_at.tzinfo is UTC
    assert report.generated_at == GENERATED_AT
    assert report.max_event_age_seconds == d("7200.000000")
    assert report.max_observed_event_age_seconds == d("3600.000000")
    assert report.summary_status == "blocked"
    assert report.reason_code_counts == (
        MarketResearchCryptoEventMemoryDigestReasonCodeCount(
            reason_code="market_research_crypto_event_memory_insufficient_memory_matches",
            count=d("1.000000"),
            event_ratio=d("1.000000"),
        ),
        MarketResearchCryptoEventMemoryDigestReasonCodeCount(
            reason_code="market_research_crypto_event_memory_low_recall_ratio",
            count=d("1.000000"),
            event_ratio=d("1.000000"),
        ),
    )
    assert report.event_config_versions == (
        ("sol_etf", "crypto-memory-event-v0"),
    )


def test_crypto_event_memory_digest_reports_no_inputs_without_io() -> None:
    report = _report()
    payload = market_research_crypto_event_memory_digest_payload(report)

    assert report.summary_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_market_research_crypto_event_memory_digest"
    )
    assert report.event_count == d("0.000000")
    assert report.max_observed_event_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_crypto_event_memory_empty",
    )
    assert payload["event_count"] == "0.000000"
    assert payload["rows"] == []
    assert payload["reason_codes"] == [
        "market_research_crypto_event_memory_empty",
    ]


def test_crypto_event_memory_digest_payload_redacts_references_and_uses_decimal_strings() -> None:
    report = _report(
        _event(
            "condition_payload",
            "btc_halving",
            event_family="btc",
            memory_match_count=d("1.000000"),
            candidate_memory_count=d("2.000000"),
        ),
    )

    payload = market_research_crypto_event_memory_digest_payload(report)
    encoded = repr(payload).lower()

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["event_count"] == "1.000000"
    assert payload["rows"][0]["memory_recall_ratio"] == "0.500000"
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    for forbidden in ("wallet", "account", "token", "secret", "private_key", "0xabc"):
        assert forbidden not in encoded


def test_crypto_event_memory_digest_validates_exact_types_flags_and_redaction() -> None:
    assert MarketResearchCryptoEventMemoryDigestReport.__dataclass_params__.frozen
    assert MarketResearchCryptoEventMemoryDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoEventMemoryDigestReasonCodeCount.__dataclass_params__.frozen
    assert MarketResearchCryptoEventMemoryDigestEvent.__dataclass_params__.frozen
    assert MarketResearchCryptoEventMemoryDigestConfig.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("crypto-event-memory-v0"))
    with pytest.raises(ValueError, match="config_version"):
        _config(
            config_version=(
                " "
                + DEFAULT_MARKET_RESEARCH_CRYPTO_EVENT_MEMORY_DIGEST_CONFIG_VERSION
            ),
        )
    with pytest.raises(ValueError, match="max_event_age_seconds"):
        _config(max_event_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="min_memory_match_count"):
        _config(min_memory_match_count=2)
    with pytest.raises(ValueError, match="min_memory_recall_ratio"):
        _config(min_memory_recall_ratio=0.5)
    for flag_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=flag_name):
            _config(**{flag_name: False})
    with pytest.raises(ValueError, match="condition_id"):
        _event(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="event_key"):
        _event(event_key=" btc_etf_flow")
    with pytest.raises(ValueError, match="event_config_version"):
        _event(event_config_version="crypto-memory-event-v0 ")
    with pytest.raises(ValueError, match="memory_match_count"):
        _event(memory_match_count=Decimal("NaN"))
    with pytest.raises(ValueError, match="memory_match_count"):
        _event(memory_match_count=d("3.000000"), candidate_memory_count=d("2.000000"))
    with pytest.raises(ValueError, match="candidate_memory_count"):
        _event(candidate_memory_count=1.0)
    for flag_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=flag_name):
            _event(**{flag_name: False})
    with pytest.raises(ValueError, match="generated_at"):
        _report(_event(), generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="future"):
        _report(_event(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="redacted"):
        _event(event_key="private_key_0xabc")
    cfg = _config()
    report = _report(_event())
    row = report.rows[0]
    reason_count = report.reason_code_counts[0]

    with pytest.raises(FrozenInstanceError):
        cfg.paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        _event().paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_count.paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.paper_only = False  # type: ignore[misc]

    for flag_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=flag_name):
            replace(row, **{flag_name: False})
        with pytest.raises(ValueError, match=flag_name):
            replace(reason_count, **{flag_name: False})
        with pytest.raises(ValueError, match=flag_name):
            replace(report, **{flag_name: False})
    with pytest.raises(ValueError, match="reason_code"):
        MarketResearchCryptoEventMemoryDigestReasonCodeCount(
            reason_code="market_research_crypto_event_memory_unknown",
            count=d("1.000000"),
            event_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            row,
            summary_status="watch",
            reason_codes=(
                "market_research_crypto_event_memory_single_source",
                "market_research_crypto_event_memory_single_source",
            ),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            row,
            summary_status="watch",
            reason_codes=(
                "market_research_crypto_event_memory_stale_event",
                "market_research_crypto_event_memory_single_source",
            ),
        )
    with pytest.raises(ValueError, match="reason_code"):
        replace(
            row,
            summary_status="watch",
            reason_codes=("market_research_crypto_event_memory_unknown",),
        )


def test_crypto_event_memory_digest_rejects_duplicates_and_bad_report_consistency() -> None:
    with pytest.raises(ValueError, match="unique"):
        _report(_event(event_key="duplicate"), _event(event_key="duplicate"))

    row = MarketResearchCryptoEventMemoryDigestRow(
        condition_id="condition_alpha",
        event_key="btc_etf_flow",
        event_family="btc",
        summary_status="clear",
        event_age_seconds=d("60.000000"),
        memory_match_count=d("2.000000"),
        candidate_memory_count=d("3.000000"),
        source_count=d("2.000000"),
        evidence_conflict_count=d("0.000000"),
        memory_recall_ratio=d("0.666667"),
        reason_codes=("market_research_crypto_event_memory_clear",),
    )
    reason_count = MarketResearchCryptoEventMemoryDigestReasonCodeCount(
        reason_code="market_research_crypto_event_memory_clear",
        count=d("1.000000"),
        event_ratio=d("1.000000"),
    )
    kwargs = dict(
        generated_at=GENERATED_AT,
        config_version=DEFAULT_MARKET_RESEARCH_CRYPTO_EVENT_MEMORY_DIGEST_CONFIG_VERSION,
        summary_status="clear",
        recommended_next_step="allow_report_only_market_research_crypto_event_memory_digest",
        event_count=d("1.000000"),
        clear_event_count=d("1.000000"),
        watch_event_count=d("0.000000"),
        blocked_event_count=d("0.000000"),
        memory_match_count=d("2.000000"),
        candidate_memory_count=d("3.000000"),
        source_count=d("2.000000"),
        stale_event_count=d("0.000000"),
        conflict_event_count=d("0.000000"),
        memory_recall_ratio=d("0.666667"),
        max_event_age_seconds=d("7200.000000"),
        min_memory_match_count=d("2.000000"),
        min_memory_recall_ratio=d("0.500000"),
        max_observed_event_age_seconds=d("60.000000"),
        rows=(row,),
        event_config_versions=(("btc_etf_flow", "crypto-memory-event-v0"),),
        reason_code_counts=(reason_count,),
        reason_codes=("market_research_crypto_event_memory_clear",),
    )

    assert MarketResearchCryptoEventMemoryDigestReport(**kwargs).summary_status == "clear"
    with pytest.raises(ValueError, match="event_count"):
        MarketResearchCryptoEventMemoryDigestReport(
            **{**kwargs, "event_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="summary_status"):
        MarketResearchCryptoEventMemoryDigestReport(
            **{**kwargs, "summary_status": "blocked"},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoEventMemoryDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoEventMemoryDigestReasonCodeCount(
                        reason_code="market_research_crypto_event_memory_clear",
                        count=d("2.000000"),
                        event_ratio=d("1.000000"),
                    ),
                ),
            },
        )
    with pytest.raises(ValueError, match="memory_match_count"):
        MarketResearchCryptoEventMemoryDigestReport(
            **{**kwargs, "memory_match_count": d("3.000000")},
        )
    with pytest.raises(ValueError, match="candidate_memory_count"):
        MarketResearchCryptoEventMemoryDigestReport(
            **{**kwargs, "candidate_memory_count": d("4.000000")},
        )
    with pytest.raises(ValueError, match="source_count"):
        MarketResearchCryptoEventMemoryDigestReport(
            **{**kwargs, "source_count": d("3.000000")},
        )
    with pytest.raises(ValueError, match="stale_event_count"):
        MarketResearchCryptoEventMemoryDigestReport(
            **{**kwargs, "stale_event_count": d("1.000000")},
        )
    with pytest.raises(ValueError, match="conflict_event_count"):
        MarketResearchCryptoEventMemoryDigestReport(
            **{**kwargs, "conflict_event_count": d("1.000000")},
        )
    with pytest.raises(ValueError, match="memory_recall_ratio"):
        MarketResearchCryptoEventMemoryDigestReport(
            **{**kwargs, "memory_recall_ratio": d("0.500000")},
        )
    with pytest.raises(ValueError, match="min_memory_recall_ratio"):
        MarketResearchCryptoEventMemoryDigestReport(
            **{**kwargs, "min_memory_recall_ratio": d("1.500000")},
        )
    with pytest.raises(ValueError, match="max_observed_event_age_seconds"):
        MarketResearchCryptoEventMemoryDigestReport(
            **{**kwargs, "max_observed_event_age_seconds": d("120.000000")},
        )
    with pytest.raises(ValueError, match="event_config_versions"):
        MarketResearchCryptoEventMemoryDigestReport(
            **{
                **kwargs,
                "event_config_versions": (
                    ("eth_memory", "crypto-memory-event-v0"),
                ),
            },
        )


def test_crypto_event_memory_digest_module_scope_excludes_execution_io_network_and_persistence() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_event_memory_digest",
    )
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "market_slug",
        "question",
        "trading",
        "auth",
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "order",
        "replace",
        "exchange",
        "mutation",
        "account",
        "advice",
        "network",
        "supabase",
        "persist",
    )
    assert not any(token in lowered for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            callee_name = ""
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in {"open", "read", "write", "submit", "cancel"}

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "socket",
        "urllib",
        "pathlib",
        "sqlite",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _walk_values(value: object):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_values(item)
    else:
        yield value
