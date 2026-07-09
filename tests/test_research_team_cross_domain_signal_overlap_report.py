from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_cross_domain_signal_overlap_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _MissingOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_cross_domain_signal_overlap_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_handoff_team_count": d("2"),
        "min_merge_team_count": d("3"),
        "min_handoff_domain_count": d("2"),
        "min_merge_domain_count": d("3"),
        "watch_merge_review_score_threshold": d("0.550000"),
        "block_merge_review_score_threshold": d("0.850000"),
    }
    values.update(overrides)
    return module.ResearchTeamCrossDomainSignalOverlapConfig(**values)


def observation(**overrides: object) -> Any:
    module = api()
    values = {
        "team_id": "politics",
        "category_id": "politics",
        "signal_name": "policy-liquidity-volatility",
        "evidence_strength": d("0.900000"),
        "confidence_score": d("0.800000"),
        "handoff_ready": True,
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return module.ResearchTeamCrossDomainSignalObservation(**values)


def build_report(*signals: Any) -> Any:
    module = api()
    return module.build_research_team_cross_domain_signal_overlap_report(
        signals,
        config=config(),
        generated_at=GENERATED_AT,
    )


def assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_float_or_int(item)


def assert_no_decimal_or_datetime(value: Any) -> None:
    if isinstance(value, (Decimal, datetime)):
        raise AssertionError(f"unexpected raw public value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_or_datetime(item)
    if isinstance(value, list):
        for item in value:
            assert_no_decimal_or_datetime(item)


def test_aggregates_cross_domain_signal_overlap_without_raw_identifiers() -> None:
    module = api()
    report = build_report(
        observation(
            signal_name="single-domain-weather-signal",
            team_id="sports_basketball",
            category_id="sports.basketball",
            evidence_strength=d("0.500000"),
            confidence_score=d("0.700000"),
            handoff_ready=False,
        ),
        observation(
            signal_name="calendar-volatility",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            evidence_strength=d("0.600000"),
            confidence_score=d("0.700000"),
            handoff_ready=True,
        ),
        observation(
            signal_name="calendar-volatility",
            team_id="macro_rates",
            category_id="finance.macro.rates",
            evidence_strength=d("0.500000"),
            confidence_score=d("0.650000"),
            handoff_ready=False,
        ),
        observation(),
        observation(
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            evidence_strength=d("0.800000"),
            confidence_score=d("0.850000"),
            handoff_ready=True,
        ),
        observation(
            team_id="macro_rates",
            category_id="finance.macro.rates",
            evidence_strength=d("0.950000"),
            confidence_score=d("0.900000"),
            handoff_ready=True,
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.input_count == d("6")
    assert report.overlap_group_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.handoff_review_count == d("1")
    assert report.merge_review_count == d("1")
    assert report.status == "block"
    assert report.reason_codes == (
        "cross_domain_signal_overlap",
        "handoff_review_needed",
        "merge_review_needed",
        "high_evidence_strength",
        "high_confidence_overlap",
        "single_team_signal",
    )
    assert len(report.public_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.signal_name for row in report.rows) == (
        "policy-liquidity-volatility",
        "calendar-volatility",
        "single-domain-weather-signal",
    )
    block_row, watch_row, pass_row = report.rows
    assert block_row.status == "block"
    assert block_row.review_need == "merge_review"
    assert block_row.team_count == d("3")
    assert block_row.domain_count == d("3")
    assert block_row.handoff_ready_count == d("3")
    assert block_row.mean_evidence_strength == d("0.883333")
    assert block_row.mean_confidence_score == d("0.850000")
    assert block_row.merge_review_score == d("0.946667")
    assert block_row.reason_codes == (
        "cross_domain_signal_overlap",
        "merge_review_needed",
        "high_evidence_strength",
        "high_confidence_overlap",
    )

    assert watch_row.status == "watch"
    assert watch_row.review_need == "handoff_review"
    assert watch_row.team_ids == ("crypto_btc", "macro_rates")
    assert watch_row.category_ids == ("finance.crypto.btc", "finance.macro.rates")
    assert watch_row.domain_count == d("2")
    assert watch_row.merge_review_score == d("0.611667")
    assert watch_row.reason_codes == (
        "cross_domain_signal_overlap",
        "handoff_review_needed",
    )

    assert pass_row.status == "pass"
    assert pass_row.review_need == "none"
    assert pass_row.reason_codes == ("single_team_signal",)

    payload = module.research_team_cross_domain_signal_overlap_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "raw_id",
        "market_id",
        "market_slug",
        "source_id",
        "source_url",
        "source_text",
        "condition_id",
        "question",
    ):
        assert forbidden not in encoded
    assert payload["public_digest"] == report.public_digest
    assert module.validate_research_team_cross_domain_signal_overlap_report_payload(
        payload,
    )
    assert_no_public_float_or_int(payload)
    assert_no_decimal_or_datetime(payload)


def test_payload_and_digest_are_deterministic_across_input_order() -> None:
    module = api()
    signals = (
        observation(
            signal_name="calendar-volatility",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            evidence_strength=d("0.600000"),
            confidence_score=d("0.700000"),
        ),
        observation(
            signal_name="calendar-volatility",
            team_id="macro_rates",
            category_id="finance.macro.rates",
            evidence_strength=d("0.500000"),
            confidence_score=d("0.650000"),
        ),
        observation(),
        observation(
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            evidence_strength=d("0.800000"),
            confidence_score=d("0.850000"),
        ),
        observation(
            team_id="macro_rates",
            category_id="finance.macro.rates",
            evidence_strength=d("0.950000"),
            confidence_score=d("0.900000"),
        ),
    )

    forward = build_report(*signals)
    reversed_report = build_report(*reversed(signals))

    assert forward == reversed_report
    assert forward.public_digest == reversed_report.public_digest
    assert module.research_team_cross_domain_signal_overlap_report_digest(
        forward,
    ) == forward.public_digest
    assert module.research_team_cross_domain_signal_overlap_report_payload(
        forward,
    ) == module.research_team_cross_domain_signal_overlap_report_payload(reversed_report)


def test_dataclasses_are_frozen_exact_decimal_only_and_flags_hard() -> None:
    module = api()
    report = build_report(observation(), observation(team_id="crypto_btc", category_id="finance.crypto.btc"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_SIGNAL_OVERLAP_CONFIG_VERSION",
        "ResearchTeamCrossDomainSignalObservation",
        "ResearchTeamCrossDomainSignalOverlapConfig",
        "ResearchTeamCrossDomainSignalOverlapReasonCodeCount",
        "ResearchTeamCrossDomainSignalOverlapReport",
        "ResearchTeamCrossDomainSignalOverlapRow",
        "build_research_team_cross_domain_signal_overlap_report",
        "research_team_cross_domain_signal_overlap_report_digest",
        "research_team_cross_domain_signal_overlap_report_payload",
        "validate_research_team_cross_domain_signal_overlap_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "pass"  # type: ignore[misc]

    for public_record in (config(), observation(), report, *report.rows):
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="evidence_strength"):
        observation(evidence_strength=1)
    with pytest.raises(ValueError, match="confidence_score"):
        observation(confidence_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="min_handoff_team_count"):
        config(min_handoff_team_count=d("0"))
    with pytest.raises(ValueError, match="block_merge_review_score_threshold"):
        config(block_merge_review_score_threshold=d("0.500000"))
    with pytest.raises(ValueError, match="handoff_ready"):
        observation(handoff_ready=1)
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_validation_rejects_time_taxonomy_duplicates_and_tampering() -> None:
    module = api()

    local_observed_at = datetime(
        2026,
        7,
        8,
        7,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    normalized = build_report(
        observation(observed_at=local_observed_at),
        observation(team_id="crypto_btc", category_id="finance.crypto.btc"),
    )
    assert normalized.rows[0].latest_observed_at == OBSERVED_AT

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 8, 11, 0, tzinfo=_MissingOffsetTz()))
    with pytest.raises(ValueError, match="observed_at must be <= generated_at"):
        build_report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="team/category"):
        observation(team_id="politics", category_id="finance.crypto.btc")
    with pytest.raises(ValueError, match="duplicate"):
        build_report(observation(), observation())
    with pytest.raises(ValueError, match="signals"):
        module.build_research_team_cross_domain_signal_overlap_report(
            "not-signals",
            config=config(),
            generated_at=GENERATED_AT,
        )

    report = build_report(
        observation(),
        observation(team_id="crypto_btc", category_id="finance.crypto.btc"),
    )
    with pytest.raises(ValueError, match="public_digest"):
        replace(report, public_digest="0" * 64)
    with pytest.raises(ValueError, match="watch_count"):
        replace(report, watch_count=d("0"))
    payload = module.research_team_cross_domain_signal_overlap_report_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["input_count"] = "99"
    with pytest.raises(ValueError, match="public_digest"):
        module.validate_research_team_cross_domain_signal_overlap_report_payload(
            tampered_payload,
        )


def test_public_status_values_are_exactly_pass_watch_block() -> None:
    module = api()
    report = build_report(
        observation(signal_name="pass-signal"),
        observation(
            signal_name="watch-signal",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            evidence_strength=d("0.600000"),
            confidence_score=d("0.700000"),
        ),
        observation(
            signal_name="watch-signal",
            team_id="macro_rates",
            category_id="finance.macro.rates",
            evidence_strength=d("0.500000"),
            confidence_score=d("0.650000"),
        ),
        observation(),
        observation(team_id="crypto_btc", category_id="finance.crypto.btc"),
        observation(team_id="macro_rates", category_id="finance.macro.rates"),
    )
    payload = module.research_team_cross_domain_signal_overlap_report_payload(report)
    statuses = {payload["status"]}
    statuses.update(row["status"] for row in payload["rows"])

    assert statuses == {"pass", "watch", "block"}
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")


def test_public_surface_and_module_scope_are_report_only_readonly_and_io_free() -> None:
    module = api()
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    for forbidden in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "route",
        "execute",
        "place",
        "size",
        "sizing",
        "recommend",
        "buy",
        "sell",
        "trade",
    ):
        assert forbidden not in source.lower()

    report = build_report(
        observation(
            signal_name="unsafe-signal-check",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
        ),
        observation(
            signal_name="unsafe-signal-check",
            team_id="macro_rates",
            category_id="finance.macro.rates",
        ),
    )
    payload = module.research_team_cross_domain_signal_overlap_report_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    with pytest.raises(ValueError, match="unsafe public surface"):
        observation(signal_name=f"has-{'market' + '_slug'}")
    with pytest.raises(ValueError, match="unsafe public surface"):
        observation(signal_name=f"has-{'candidate' + '_id'}")
    with pytest.raises(ValueError, match="unsafe public surface"):
        observation(signal_name=f"has-{'source' + '_id'}")
    with pytest.raises(ValueError, match="unsafe public surface"):
        observation(signal_name=f"has-{'https' + '://'}example.test")
    with pytest.raises(ValueError, match="unsafe public surface"):
        observation(signal_name=f"has-{'rou' + 'te'}")
    with pytest.raises(ValueError, match="unsafe public surface"):
        observation(signal_name=f"has-{'exec' + 'ute'}")
    with pytest.raises(ValueError, match="unsafe public surface"):
        observation(signal_name=f"has-{'pla' + 'ce'}")
    with pytest.raises(ValueError, match="unsafe public surface"):
        observation(signal_name=f"has-{'siz' + 'e'}")
