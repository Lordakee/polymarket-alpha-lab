from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_source_reliability_weight_digest.py"
)
GENERATED_AT = datetime(2026, 7, 3, 16, 30, tzinfo=timezone(timedelta(hours=2)))
OBSERVED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_source_reliability_weight_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    digest = api()
    values = {
        "config_version": "strategy-team-source-reliability-weight-digest-test-v0",
        "min_pass_weighted_reliability_score": d("0.500000"),
        "min_watch_weighted_reliability_score": d("0.250000"),
        "min_source_reliability": d("0.600000"),
        "min_source_coverage_ratio": d("0.600000"),
        "max_source_age_seconds": d("86400.000000"),
        "max_dispute_ratio": d("0.200000"),
    }
    values.update(overrides)
    return digest.StrategyTeamSourceReliabilityWeightDigestConfig(**values)


def source(**overrides: object):
    digest = api()
    values = {
        "team_id": "macro_team",
        "source_id": "source_macro",
        "observed_at": OBSERVED_AT,
        "source_reliability": d("0.900000"),
        "evidence_count": d("10"),
        "settled_evidence_count": d("9"),
        "corroboration_count": d("3"),
        "dispute_count": d("0"),
        "source_age_seconds": d("3600.000000"),
        "team_signal_weight": d("0.800000"),
        "reason_codes": ("source_reliability_history",),
    }
    values.update(overrides)
    return digest.StrategyTeamSourceReliabilityWeightSource(**values)


def report(*, sources=(), cfg=None, generated_at: datetime = GENERATED_AT):
    digest = api()
    return digest.build_strategy_team_source_reliability_weight_digest(
        sources,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_digest_reduces_source_reliability_weights_with_stable_reasons() -> None:
    digest_report = report(
        sources=(
            source(
                team_id="sports_team",
                source_id="source_sports",
                source_reliability=d("0.500000"),
                evidence_count=d("10"),
                settled_evidence_count=d("4"),
                dispute_count=d("2"),
                source_age_seconds=d("172800.000000"),
                team_signal_weight=d("0.300000"),
            ),
            source(
                team_id="crypto_team",
                source_id="source_crypto",
                source_reliability=d("0.650000"),
                evidence_count=d("10"),
                settled_evidence_count=d("6"),
                dispute_count=d("1"),
                source_age_seconds=d("43200.000000"),
                team_signal_weight=d("0.400000"),
            ),
            source(
                team_id="macro_team",
                source_id="source_macro",
                source_reliability=d("0.900000"),
                evidence_count=d("10"),
                settled_evidence_count=d("9"),
                dispute_count=d("0"),
                source_age_seconds=d("3600.000000"),
                team_signal_weight=d("0.800000"),
            ),
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == datetime(2026, 7, 3, 14, 30, tzinfo=UTC)
    assert digest_report.config_version == (
        "strategy-team-source-reliability-weight-digest-test-v0"
    )
    assert digest_report.source_count == d("3")
    assert digest_report.pass_count == d("1")
    assert digest_report.watch_count == d("1")
    assert digest_report.block_count == d("1")
    assert digest_report.average_reliability_weight == d("0.649444")
    assert digest_report.average_weighted_reliability_score == d("0.477542")
    assert digest_report.status == "blocked"
    assert digest_report.reason_codes == (
        "source_reliability_weight_pass",
        "source_reliability_weight_watch",
        "source_reliability_weight_block",
        "source_reliability_low",
        "source_coverage_low",
        "source_stale",
        "source_dispute_ratio_high",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple(row.team_id for row in digest_report.rows) == (
        "macro_team",
        "crypto_team",
        "sports_team",
    )
    assert tuple(row.source_id for row in digest_report.rows) == (
        "source_macro",
        "source_crypto",
        "source_sports",
    )
    assert tuple(row.status for row in digest_report.rows) == (
        "pass",
        "watch",
        "block",
    )

    passed, watched, blocked = digest_report.rows
    assert passed.source_coverage_ratio == d("0.900000")
    assert passed.dispute_ratio == ZERO
    assert passed.freshness_weight == d("0.958333")
    assert passed.reliability_weight == d("0.910833")
    assert passed.weighted_reliability_score == d("0.819750")
    assert passed.reason_codes == (
        "source_reliability_history",
        "source_reliability_weight_pass",
        "source_reliability_strong",
        "source_coverage_met",
        "source_fresh",
        "source_dispute_ratio_contained",
    )

    assert watched.source_coverage_ratio == d("0.600000")
    assert watched.dispute_ratio == d("0.166667")
    assert watched.freshness_weight == d("0.500000")
    assert watched.reliability_weight == d("0.627500")
    assert watched.weighted_reliability_score == d("0.407875")
    assert watched.reason_codes == (
        "source_reliability_history",
        "source_reliability_weight_watch",
        "source_coverage_met",
        "source_fresh",
        "source_dispute_ratio_contained",
    )

    assert blocked.source_coverage_ratio == d("0.400000")
    assert blocked.dispute_ratio == d("0.500000")
    assert blocked.freshness_weight == ZERO
    assert blocked.reliability_weight == d("0.410000")
    assert blocked.weighted_reliability_score == d("0.205000")
    assert blocked.reason_codes == (
        "source_reliability_history",
        "source_reliability_weight_block",
        "source_reliability_low",
        "source_coverage_low",
        "source_stale",
        "source_dispute_ratio_high",
    )


def test_empty_digest_is_watch_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.source_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.block_count == d("0")
    assert empty.average_reliability_weight == ZERO
    assert empty.average_weighted_reliability_score == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == ("strategy_team_source_reliability_weight_digest_empty",)
    assert empty.reason_rollups == ()
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(sources=(source(),))
    for value in (empty, populated, *populated.rows, *populated.reason_rollups):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_ratio",
                    "_score",
                    "_weight",
                    "_reliability",
                    "_seconds",
                ),
            ):
                assert type(item_value) is Decimal


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    digest = api()
    numeric_suffixes = (
        "_count",
        "_ratio",
        "_score",
        "_weight",
        "_reliability",
        "_seconds",
    )

    for cls in (
        digest.StrategyTeamSourceReliabilityWeightDigestConfig,
        digest.StrategyTeamSourceReliabilityWeightSource,
        digest.StrategyTeamSourceReliabilityWeightDigestRow,
        digest.StrategyTeamSourceReliabilityWeightReasonRollup,
        digest.StrategyTeamSourceReliabilityWeightDigestReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name.endswith(numeric_suffixes):
                assert hints[item.name] is Decimal

    with pytest.raises(ValueError, match="source_ratio must be a Decimal"):
        digest.StrategyTeamSourceReliabilityWeightReasonRollup(
            reason_code="source_reliability_weight_pass",
            source_count=d("1"),
            source_ratio=None,
        )


def test_payload_uses_decimal_strings_utc_datetimes_and_no_floats() -> None:
    digest = api()
    digest_report = report(
        sources=(
            source(
                team_id="crypto_team",
                source_id="source_crypto",
                observed_at=datetime(2026, 7, 3, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
                source_reliability=d("0.650000"),
                evidence_count=d("10"),
                settled_evidence_count=d("6"),
                dispute_count=d("1"),
                source_age_seconds=d("43200.000000"),
                team_signal_weight=d("0.400000"),
            ),
        ),
    )

    payload = digest.strategy_team_source_reliability_weight_digest_payload(digest_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T14:30:00+00:00"
    assert payload["source_count"] == "1"
    assert payload["average_reliability_weight"] == "0.627500"
    assert payload["average_weighted_reliability_score"] == "0.407875"
    assert payload["derived_validation_digest"] == digest_report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["rows"][0]["observed_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["rows"][0]["source_coverage_ratio"] == "0.600000"
    assert '"0.407875"' in encoded
    assert_no_float_values(payload)


def test_validation_rejects_bad_types_duplicates_naive_time_and_flags() -> None:
    digest = api()

    with pytest.raises(ValueError, match="config"):
        digest.build_strategy_team_source_reliability_weight_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="source_reliability must be a Decimal"):
        source(source_reliability=0.9)

    with pytest.raises(ValueError, match="source_reliability must be a Decimal"):
        source(source_reliability=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="source_age_seconds must be finite"):
        source(source_age_seconds=Decimal("NaN"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 3, 14, 30))

    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        source(observed_at=_DatetimeSubclass(2026, 7, 3, 12, 0, tzinfo=UTC))

    with pytest.raises(ValueError, match="duplicate team_id/source_id"):
        report(sources=(source(), source()))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(source(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        digest.StrategyTeamSourceReliabilityWeightDigestConfig(readonly=False)

    with pytest.raises(FrozenInstanceError):
        row = source()
        row.source_id = "other"  # type: ignore[misc]


def test_public_strings_reject_secret_like_values_before_leakage() -> None:
    with pytest.raises(ValueError, match="must not contain sensitive material"):
        config(config_version="strategy-team-password-secret")

    with pytest.raises(ValueError, match="must not contain sensitive material"):
        source(team_id="team_secret")

    with pytest.raises(ValueError, match="must not contain sensitive material"):
        source(source_id="postgresql://user:secret@db.example.local/postgres")

    with pytest.raises(ValueError, match="must not contain sensitive material"):
        source(reason_codes=("api_key_secret",))


def test_payload_rejects_tampered_report_digest_before_serialization() -> None:
    digest = api()
    digest_report = report(sources=(source(),))

    assert len(digest_report.derived_validation_digest) == 64

    object.__setattr__(
        digest_report,
        "generated_at",
        digest_report.generated_at + timedelta(seconds=1),
    )

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        digest.strategy_team_source_reliability_weight_digest_payload(digest_report)


def test_payload_rejects_injected_unsafe_public_surface_fields() -> None:
    digest = api()
    digest_report = report(sources=(source(),))

    object.__setattr__(digest_report, "api_key", "redacted")

    with pytest.raises(ValueError, match="unsafe public payload field"):
        digest.strategy_team_source_reliability_weight_digest_payload(digest_report)


def test_module_scope_has_no_forbidden_live_network_file_store_or_execution_surface() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    unsafe_public_fragments = (
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
    )
    forbidden_import_roots = (
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
    )
    forbidden_call_names = ("open", "exec", "eval")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
            assert node.func.id not in forbidden_call_names
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    field_name = child.target.id.lower()
                    assert not any(
                        fragment in field_name for fragment in unsafe_public_fragments
                    )
