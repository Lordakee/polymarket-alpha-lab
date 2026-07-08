from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_market_source_update_volatility_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_market_source_update_volatility_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def cfg(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "research-market-source-update-volatility-report-test-v0",
        "min_update_interval_seconds": d("1800.000000"),
        "max_source_age_seconds": d("7200.000000"),
        "min_corroboration_readiness_score": d("0.750000"),
        "claim_reversal_watch_pressure": d("0.250000"),
        "claim_reversal_block_pressure": d("0.600000"),
        "watch_manual_escalation_urgency_score": d("0.350000"),
        "block_manual_escalation_urgency_score": d("0.700000"),
        "update_frequency_weight": d("0.250000"),
        "claim_reversal_weight": d("0.300000"),
        "source_recency_weight": d("0.200000"),
        "corroboration_gap_weight": d("0.250000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchMarketSourceUpdateVolatilityReportConfig(**values)


def observation(
    research_bucket: str,
    *,
    update_family: str = "official_update",
    source_class: str = "official_reporting",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
    claim_reversed: bool = False,
    corroborating_source_count: Decimal = d("3.000000"),
    required_corroborating_source_count: Decimal = d("3.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketSourceUpdateObservation(
        research_bucket=research_bucket,
        update_family=update_family,
        source_class=source_class,
        observed_at=observed_at,
        claim_reversed=claim_reversed,
        corroborating_source_count=corroborating_source_count,
        required_corroborating_source_count=required_corroborating_source_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: object,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
) -> Any:
    module = api()
    return module.build_research_market_source_update_volatility_report(
        observations,
        config=config or cfg(),
        generated_at=generated_at,
    )


def assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        if field.name in {"rows", "reason_code_counts"}:
            continue
        field_value = getattr(value, field.name)
        if isinstance(field_value, bool) or field_value is None:
            continue
        if any(
            marker in field.name
            for marker in (
                "age",
                "count",
                "interval",
                "pressure",
                "readiness",
                "score",
            )
        ):
            assert type(field_value) is Decimal, field.name


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_public_number_payload(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_public_number_payload(item_value)


def assert_no_raw_identifier_surface(value: Any) -> None:
    forbidden_key_fragments = (
        "market_id",
        "market_slug",
        "condition_id",
        "source_id",
        "source_url",
        "raw",
        "question",
        "wallet",
        "order",
        "database",
        "recommendation",
    )
    forbidden_value_fragments = (
        "://",
        "www.",
        "wallet",
        "order",
        "database",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered, key
            assert_no_raw_identifier_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_raw_identifier_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered, value


def test_empty_report_is_pass_report_only_decimal_digest_bound_and_json_safe() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.__dataclass_params__.frozen is True
    assert module.VOLATILITY_STATUSES == ("pass", "watch", "block")
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == "research-market-source-update-volatility-report-test-v0"
    assert empty_report.status == "pass"
    assert empty_report.group_count == d("0.000000")
    assert empty_report.update_count == d("0.000000")
    assert empty_report.pass_count == d("0.000000")
    assert empty_report.watch_count == d("0.000000")
    assert empty_report.block_count == d("0.000000")
    assert empty_report.max_manual_escalation_urgency_score == d("0.000000")
    assert empty_report.average_manual_escalation_urgency_score == d("0.000000")
    assert empty_report.average_update_frequency_pressure == d("0.000000")
    assert empty_report.max_claim_reversal_pressure == d("0.000000")
    assert empty_report.average_corroboration_readiness_score == d("0.000000")
    assert empty_report.max_source_age_seconds == d("0.000000")
    assert empty_report.reason_codes == ("source_update_volatility_pass",)
    assert empty_report.reason_code_counts == ()
    assert empty_report.rows == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_numbers(empty_report)

    payload = empty_report.payload
    digest_value = module.research_market_source_update_volatility_report_digest(
        empty_report,
    )
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["status"] == "pass"
    assert payload["group_count"] == "0.000000"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64
    assert module.validate_research_market_source_update_volatility_public_payload(payload)
    assert_no_public_number_payload(payload)
    assert_no_raw_identifier_surface(payload)


def test_report_aggregates_update_frequency_reversal_recency_and_corroboration() -> None:
    built = report(
        observation(
            "bucket-pass",
            source_class="official_reporting",
            observed_at=GENERATED_AT - timedelta(minutes=60),
        ),
        observation(
            "bucket-pass",
            update_family="corroboration",
            source_class="independent_archive",
            observed_at=GENERATED_AT - timedelta(minutes=15),
            corroborating_source_count=d("4.000000"),
            required_corroborating_source_count=d("4.000000"),
        ),
        observation(
            "bucket-watch",
            source_class="official_reporting",
            observed_at=GENERATED_AT - timedelta(minutes=60),
            claim_reversed=True,
            corroborating_source_count=d("2.000000"),
            required_corroborating_source_count=d("4.000000"),
        ),
        observation(
            "bucket-watch",
            update_family="corroboration",
            source_class="domain_specialist",
            observed_at=GENERATED_AT - timedelta(minutes=40),
            corroborating_source_count=d("3.000000"),
            required_corroborating_source_count=d("4.000000"),
        ),
        observation(
            "bucket-block",
            source_class="official_reporting",
            observed_at=GENERATED_AT - timedelta(hours=4),
            claim_reversed=True,
            corroborating_source_count=d("1.000000"),
            required_corroborating_source_count=d("4.000000"),
        ),
        observation(
            "bucket-block",
            update_family="corroboration",
            source_class="domain_specialist",
            observed_at=GENERATED_AT - timedelta(hours=3, minutes=50),
            claim_reversed=True,
            corroborating_source_count=d("1.000000"),
            required_corroborating_source_count=d("4.000000"),
        ),
        observation(
            "bucket-block",
            update_family="revision",
            source_class="independent_archive",
            observed_at=GENERATED_AT - timedelta(hours=3, minutes=40),
            corroborating_source_count=d("1.000000"),
            required_corroborating_source_count=d("4.000000"),
        ),
    )

    assert built.status == "block"
    assert built.group_count == d("3.000000")
    assert built.update_count == d("7.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.max_manual_escalation_urgency_score == d("0.754167")
    assert built.average_manual_escalation_urgency_score == d("0.390972")
    assert built.average_update_frequency_pressure == d("0.333333")
    assert built.max_claim_reversal_pressure == d("0.666667")
    assert built.average_corroboration_readiness_score == d("0.625000")
    assert built.max_source_age_seconds == d("13200.000000")
    assert built.reason_codes == (
        "update_frequency_watch",
        "claim_reversal_pressure_watch",
        "claim_reversal_pressure_block",
        "source_recency_block",
        "corroboration_readiness_watch",
        "corroboration_readiness_block",
        "manual_escalation_urgency_watch",
        "manual_escalation_urgency_block",
    )

    assert tuple(row.research_bucket for row in built.rows) == (
        "bucket-block",
        "bucket-watch",
        "bucket-pass",
    )

    blocked, watched, passed = built.rows
    assert blocked.status == "block"
    assert blocked.update_count == d("3.000000")
    assert blocked.source_class_count == d("3.000000")
    assert blocked.update_family_count == d("3.000000")
    assert blocked.average_update_interval_seconds == d("600.000000")
    assert blocked.update_frequency_pressure == d("0.666667")
    assert blocked.claim_reversal_pressure == d("0.666667")
    assert blocked.source_age_seconds == d("13200.000000")
    assert blocked.corroboration_readiness_score == d("0.250000")
    assert blocked.manual_escalation_urgency_score == d("0.754167")
    assert blocked.reason_codes == (
        "update_frequency_watch",
        "claim_reversal_pressure_block",
        "source_recency_block",
        "corroboration_readiness_block",
        "manual_escalation_urgency_block",
    )

    assert watched.status == "watch"
    assert watched.update_count == d("2.000000")
    assert watched.average_update_interval_seconds == d("1200.000000")
    assert watched.update_frequency_pressure == d("0.333333")
    assert watched.claim_reversal_pressure == d("0.500000")
    assert watched.source_age_seconds == d("2400.000000")
    assert watched.corroboration_readiness_score == d("0.625000")
    assert watched.manual_escalation_urgency_score == d("0.393750")
    assert watched.reason_codes == (
        "update_frequency_watch",
        "claim_reversal_pressure_watch",
        "corroboration_readiness_watch",
        "manual_escalation_urgency_watch",
    )

    assert passed.status == "pass"
    assert passed.update_count == d("2.000000")
    assert passed.update_frequency_pressure == d("0.000000")
    assert passed.claim_reversal_pressure == d("0.000000")
    assert passed.source_age_seconds == d("900.000000")
    assert passed.corroboration_readiness_score == d("1.000000")
    assert passed.manual_escalation_urgency_score == d("0.025000")
    assert passed.reason_codes == ("source_update_volatility_pass",)


def test_payload_digest_is_deterministic_validated_and_identifier_sanitized() -> None:
    module = api()
    observations = (
        observation(
            "bucket-alpha",
            source_class="official_reporting",
            observed_at=GENERATED_AT - timedelta(minutes=20),
        ),
        observation(
            "bucket-alpha",
            update_family="corroboration",
            source_class="independent_archive",
            observed_at=GENERATED_AT - timedelta(minutes=10),
            claim_reversed=True,
            corroborating_source_count=d("2.000000"),
            required_corroborating_source_count=d("4.000000"),
        ),
        observation(
            "bucket-beta",
            source_class="official_reporting",
            observed_at=GENERATED_AT - timedelta(minutes=90),
        ),
    )

    first = report(*observations)
    second = report(*reversed(observations))

    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_market_source_update_volatility_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first.payload["derived_validation_digest"] == first.derived_validation_digest
    assert module.validate_research_market_source_update_volatility_public_payload(first.payload)
    assert_no_public_number_payload(first.payload)
    assert_no_raw_identifier_surface(first.payload)

    tampered = dict(first.payload)
    tampered["status"] = "pass" if first.status != "pass" else "watch"
    assert not module.validate_research_market_source_update_volatility_public_payload(tampered)


def test_dataclasses_are_frozen_strict_and_reject_live_or_unsafe_surfaces() -> None:
    module = api()
    built = report(observation("bucket-decimal"))

    public_classes = (
        module.ResearchMarketSourceUpdateVolatilityReportConfig,
        module.ResearchMarketSourceUpdateObservation,
        module.ResearchMarketSourceUpdateVolatilityReasonCodeCount,
        module.ResearchMarketSourceUpdateVolatilityRow,
        module.ResearchMarketSourceUpdateVolatilityReport,
    )
    for public_class in public_classes:
        assert is_dataclass(public_class)
        assert public_class.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(module.ResearchMarketSourceUpdateVolatilityReport):
            pass

    with pytest.raises(ValueError, match="corroborating_source_count must be exactly Decimal"):
        observation("bucket-float", corroborating_source_count=1.0)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="required_corroborating_source_count must be exactly Decimal"):
        observation(
            "bucket-decimal-subclass",
            required_corroborating_source_count=_DecimalSubclass("4.000000"),
        )

    with pytest.raises(ValueError, match="claim_reversed must be a bool"):
        observation("bucket-bool", claim_reversed=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only must be a bool"):
        observation("bucket-flag", paper_only=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="timezone-aware"):
        observation("bucket-naive", observed_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="utcoffset"):
        observation(
            "bucket-offset",
            observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()),
        )

    with pytest.raises(ValueError, match="unsafe"):
        observation("https://example.invalid/raw-market")

    with pytest.raises(ValueError, match="report_only"):
        replace(built.rows[0], report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)

    with pytest.raises(ValueError, match="weights must sum to one"):
        cfg(source_recency_weight=d("0.100000"))

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)
    public_names = set(dir(module))
    assert "client" not in public_names
    assert "wallet" not in public_names
    assert "order" not in public_names
    assert "recommendation" not in public_names
