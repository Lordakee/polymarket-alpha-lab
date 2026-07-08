from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_domain_signal_decay_watch_report import (
    DEFAULT_RESEARCH_DOMAIN_SIGNAL_DECAY_WATCH_REPORT_CONFIG_VERSION,
    RESEARCH_DOMAIN_SIGNAL_DECAY_WATCH_REPORT_STATUSES,
    ResearchDomainSignalDecayWatchConfig,
    ResearchDomainSignalDecayWatchInput,
    ResearchDomainSignalDecayWatchReasonCodeCount,
    ResearchDomainSignalDecayWatchReport,
    ResearchDomainSignalDecayWatchRow,
    build_research_domain_signal_decay_watch_report,
    research_domain_signal_decay_watch_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
SIX_DECIMAL_RE = re.compile(r"^-?\d+\.\d{6}$")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _MissingOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchDomainSignalDecayWatchConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_DOMAIN_SIGNAL_DECAY_WATCH_REPORT_CONFIG_VERSION,
        "max_forecast_age_seconds": d("7200.000000"),
        "block_forecast_age_seconds": d("14400.000000"),
        "max_evidence_age_seconds": d("3600.000000"),
        "block_evidence_age_seconds": d("10800.000000"),
        "max_catalyst_age_seconds": d("21600.000000"),
        "block_catalyst_age_seconds": d("43200.000000"),
        "min_source_reliability_score": d("0.700000"),
        "block_source_reliability_score": d("0.400000"),
        "max_calibration_drift_ratio": d("0.100000"),
        "block_calibration_drift_ratio": d("0.250000"),
        "min_forecast_sample_count": d("2.000000"),
        "min_evidence_sample_count": d("2.000000"),
    }
    values.update(overrides)
    return ResearchDomainSignalDecayWatchConfig(**values)


def domain_input(
    domain_key: str = "macro.rates",
    *,
    observed_at: datetime | None = None,
    forecast_sample_count: Decimal = d("3.000000"),
    evidence_sample_count: Decimal = d("4.000000"),
    aggregate_forecast_age_seconds: Decimal = d("1800.000000"),
    evidence_freshness_seconds: Decimal = d("1200.000000"),
    catalyst_recency_seconds: Decimal = d("2400.000000"),
    source_reliability_score: Decimal = d("0.900000"),
    calibration_drift_ratio: Decimal = d("0.020000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchDomainSignalDecayWatchInput:
    return ResearchDomainSignalDecayWatchInput(
        domain_key=domain_key,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=15),
        forecast_sample_count=forecast_sample_count,
        evidence_sample_count=evidence_sample_count,
        aggregate_forecast_age_seconds=aggregate_forecast_age_seconds,
        evidence_freshness_seconds=evidence_freshness_seconds,
        catalyst_recency_seconds=catalyst_recency_seconds,
        source_reliability_score=source_reliability_score,
        calibration_drift_ratio=calibration_drift_ratio,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchDomainSignalDecayWatchInput, ...],
    *,
    cfg: ResearchDomainSignalDecayWatchConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchDomainSignalDecayWatchReport:
    return build_research_domain_signal_decay_watch_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_builds_domain_decay_report_with_pass_watch_block_statuses_and_sorted_rows() -> None:
    summary = report(
        (
            domain_input(
                "consumer.prices",
                aggregate_forecast_age_seconds=d("9000.000000"),
                evidence_freshness_seconds=d("7200.000000"),
                catalyst_recency_seconds=d("25000.000000"),
                source_reliability_score=d("0.650000"),
                calibration_drift_ratio=d("0.120000"),
            ),
            domain_input(
                "energy.supply",
                observed_at=GENERATED_AT - timedelta(hours=2),
                forecast_sample_count=d("1.000000"),
                evidence_sample_count=d("1.000000"),
                aggregate_forecast_age_seconds=d("20000.000000"),
                evidence_freshness_seconds=d("12000.000000"),
                catalyst_recency_seconds=d("50000.000000"),
                source_reliability_score=d("0.350000"),
                calibration_drift_ratio=d("0.300000"),
            ),
            domain_input(
                "macro.rates",
                observed_at=(GENERATED_AT - timedelta(minutes=15)).astimezone(
                    timezone(timedelta(hours=-4)),
                ),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=2))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert RESEARCH_DOMAIN_SIGNAL_DECAY_WATCH_REPORT_STATUSES == ("pass", "watch", "block")
    assert summary.config_version == DEFAULT_RESEARCH_DOMAIN_SIGNAL_DECAY_WATCH_REPORT_CONFIG_VERSION
    assert summary.status == "block"
    assert summary.public_next_step == "block_report_only_domain_signal_decay_review"
    assert summary.domain_count == d("3.000000")
    assert summary.pass_domain_count == d("1.000000")
    assert summary.watch_domain_count == d("1.000000")
    assert summary.block_domain_count == d("1.000000")
    assert summary.forecast_age_decay_count == d("2.000000")
    assert summary.evidence_freshness_decay_count == d("2.000000")
    assert summary.catalyst_recency_decay_count == d("2.000000")
    assert summary.source_reliability_decay_count == d("2.000000")
    assert summary.calibration_drift_decay_count == d("2.000000")
    assert summary.average_forecast_age_seconds == d("10266.666667")
    assert summary.average_evidence_freshness_seconds == d("6800.000000")
    assert summary.average_catalyst_recency_seconds == d("25800.000000")
    assert summary.average_source_reliability_score == d("0.633333")
    assert summary.average_calibration_drift_ratio == d("0.146667")
    assert summary.max_forecast_age_seconds == d("20000.000000")
    assert summary.max_evidence_freshness_seconds == d("12000.000000")
    assert summary.max_catalyst_recency_seconds == d("50000.000000")
    assert summary.max_calibration_drift_ratio == d("0.300000")
    assert summary.min_source_reliability_score == d("0.350000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64

    assert tuple((row.status, row.domain_key) for row in summary.rows) == (
        ("block", "energy.supply"),
        ("watch", "consumer.prices"),
        ("pass", "macro.rates"),
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchDomainSignalDecayWatchRow)
    assert blocked.observed_at == GENERATED_AT - timedelta(hours=2)
    assert blocked.observation_age_seconds == d("7200.000000")
    assert blocked.reason_codes == (
        "block_forecast_age_decay",
        "block_evidence_freshness_decay",
        "block_catalyst_recency_decay",
        "block_source_reliability_decay",
        "block_calibration_drift_decay",
        "block_forecast_sample_gap",
        "block_evidence_sample_gap",
    )
    assert len(blocked.derived_validation_digest) == 64

    watched = summary.rows[1]
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "watch_forecast_age_decay",
        "watch_evidence_freshness_decay",
        "watch_catalyst_recency_decay",
        "watch_source_reliability_decay",
        "watch_calibration_drift_decay",
    )

    passed = summary.rows[2]
    assert passed.observed_at == GENERATED_AT - timedelta(minutes=15)
    assert passed.reason_codes == ("pass_domain_signal_decay_watch",)

    assert summary.reason_code_counts == (
        ResearchDomainSignalDecayWatchReasonCodeCount(
            reason_code="block_forecast_age_decay",
            count=d("1.000000"),
            domain_ratio=d("0.333333"),
        ),
        ResearchDomainSignalDecayWatchReasonCodeCount(
            reason_code="block_evidence_freshness_decay",
            count=d("1.000000"),
            domain_ratio=d("0.333333"),
        ),
        ResearchDomainSignalDecayWatchReasonCodeCount(
            reason_code="block_catalyst_recency_decay",
            count=d("1.000000"),
            domain_ratio=d("0.333333"),
        ),
        ResearchDomainSignalDecayWatchReasonCodeCount(
            reason_code="block_source_reliability_decay",
            count=d("1.000000"),
            domain_ratio=d("0.333333"),
        ),
        ResearchDomainSignalDecayWatchReasonCodeCount(
            reason_code="block_calibration_drift_decay",
            count=d("1.000000"),
            domain_ratio=d("0.333333"),
        ),
        ResearchDomainSignalDecayWatchReasonCodeCount(
            reason_code="block_forecast_sample_gap",
            count=d("1.000000"),
            domain_ratio=d("0.333333"),
        ),
        ResearchDomainSignalDecayWatchReasonCodeCount(
            reason_code="block_evidence_sample_gap",
            count=d("1.000000"),
            domain_ratio=d("0.333333"),
        ),
        ResearchDomainSignalDecayWatchReasonCodeCount(
            reason_code="watch_forecast_age_decay",
            count=d("1.000000"),
            domain_ratio=d("0.333333"),
        ),
        ResearchDomainSignalDecayWatchReasonCodeCount(
            reason_code="watch_evidence_freshness_decay",
            count=d("1.000000"),
            domain_ratio=d("0.333333"),
        ),
        ResearchDomainSignalDecayWatchReasonCodeCount(
            reason_code="watch_catalyst_recency_decay",
            count=d("1.000000"),
            domain_ratio=d("0.333333"),
        ),
        ResearchDomainSignalDecayWatchReasonCodeCount(
            reason_code="watch_source_reliability_decay",
            count=d("1.000000"),
            domain_ratio=d("0.333333"),
        ),
        ResearchDomainSignalDecayWatchReasonCodeCount(
            reason_code="watch_calibration_drift_decay",
            count=d("1.000000"),
            domain_ratio=d("0.333333"),
        ),
        ResearchDomainSignalDecayWatchReasonCodeCount(
            reason_code="pass_domain_signal_decay_watch",
            count=d("1.000000"),
            domain_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(item.reason_code for item in summary.reason_code_counts)


def test_empty_report_blocks_as_report_only_missing_public_aggregate_inputs() -> None:
    summary = report(())

    assert summary.status == "block"
    assert summary.public_next_step == "block_report_only_domain_signal_decay_review"
    assert summary.domain_count == ZERO
    assert summary.pass_domain_count == ZERO
    assert summary.watch_domain_count == ZERO
    assert summary.block_domain_count == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == ("block_domain_signal_decay_no_inputs",)
    assert summary.reason_code_counts == (
        ResearchDomainSignalDecayWatchReasonCodeCount(
            reason_code="block_domain_signal_decay_no_inputs",
            count=d("1.000000"),
            domain_ratio=ZERO,
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_is_deterministic_json_safe_digest_bound_and_identifier_safe() -> None:
    rows = (
        domain_input("macro.rates"),
        domain_input(
            "energy.supply",
            aggregate_forecast_age_seconds=d("20000.000000"),
            evidence_freshness_seconds=d("12000.000000"),
            catalyst_recency_seconds=d("50000.000000"),
            source_reliability_score=d("0.350000"),
            calibration_drift_ratio=d("0.300000"),
        ),
    )
    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = research_domain_signal_decay_watch_report_payload(first_report)
    second_payload = research_domain_signal_decay_watch_report_payload(second_report)

    assert first_payload == second_payload
    json.dumps(first_payload, sort_keys=True)
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_payload["generated_at"] == GENERATED_AT.isoformat()
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert first_payload["domain_count"] == "2.000000"
    assert first_payload["rows"][0]["aggregate_forecast_age_seconds"] == "20000.000000"
    assert first_payload["rows"][0]["source_reliability_score"] == "0.350000"
    assert first_payload["reason_code_counts"][0]["domain_ratio"] == "0.500000"
    assert_payload_is_plain_json(first_payload)
    assert_six_decimal_strings(first_payload)
    assert_no_raw_identifiers(first_payload)

    tampered_payload = dict(first_payload)
    tampered_payload["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_domain_signal_decay_watch_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="readonly"):
        research_domain_signal_decay_watch_report_payload({**first_payload, "readonly": False})


def test_public_contracts_are_frozen_exact_decimal_only_and_reject_false_flags() -> None:
    summary = report((domain_input(),))
    instances = (
        config(),
        domain_input(),
        summary.rows[0],
        summary.reason_code_counts[0],
        summary,
    )
    for instance in instances:
        assert is_dataclass(instance)
        assert instance.__dataclass_params__.frozen
        assert_public_numeric_fields_are_exact_decimals(instance)

    with pytest.raises(FrozenInstanceError):
        summary.rows[0].status = "block"  # type: ignore[misc]

    false_flag_cases = (
        lambda: config(paper_only=False),
        lambda: config(report_only=False),
        lambda: config(readonly=False),
        lambda: domain_input(paper_only=False),
        lambda: domain_input(report_only=False),
        lambda: domain_input(readonly=False),
        lambda: replace(summary.rows[0], paper_only=False),
        lambda: replace(summary.rows[0], report_only=False),
        lambda: replace(summary.rows[0], readonly=False),
        lambda: replace(summary.reason_code_counts[0], paper_only=False),
        lambda: replace(summary.reason_code_counts[0], report_only=False),
        lambda: replace(summary.reason_code_counts[0], readonly=False),
        lambda: replace(summary, paper_only=False),
        lambda: replace(summary, report_only=False),
        lambda: replace(summary, readonly=False),
    )
    for make_value in false_flag_cases:
        with pytest.raises(ValueError, match="must be True"):
            make_value()


def test_validation_rejects_bad_inputs_timestamps_sequences_and_unsafe_identifiers() -> None:
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("research-domain-signal-decay-watch-report-v1"))
    with pytest.raises(ValueError, match="max_forecast_age_seconds"):
        config(max_forecast_age_seconds=7200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_forecast_age_seconds"):
        config(block_forecast_age_seconds=d("7200.000000"))
    with pytest.raises(ValueError, match="min_source_reliability_score"):
        config(min_source_reliability_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="block_source_reliability_score"):
        config(block_source_reliability_score=d("0.700000"))
    with pytest.raises(ValueError, match="max_calibration_drift_ratio"):
        config(max_calibration_drift_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="min_forecast_sample_count"):
        config(min_forecast_sample_count=d("1.500000"))

    with pytest.raises(ValueError, match="domain_key"):
        domain_input("bad domain")
    with pytest.raises(ValueError, match="domain_key"):
        domain_input("raw_market_slug")
    with pytest.raises(ValueError, match="observed_at"):
        domain_input(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        domain_input(
            observed_at=datetime(2026, 7, 8, 12, 0, tzinfo=_MissingOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        domain_input(observed_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="forecast_sample_count"):
        domain_input(forecast_sample_count=d("1.500000"))
    with pytest.raises(ValueError, match="evidence_sample_count"):
        domain_input(evidence_sample_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="aggregate_forecast_age_seconds"):
        domain_input(aggregate_forecast_age_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="evidence_freshness_seconds"):
        domain_input(evidence_freshness_seconds=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="source_reliability_score"):
        domain_input(source_reliability_score=d("1.000001"))
    with pytest.raises(ValueError, match="calibration_drift_ratio"):
        domain_input(calibration_drift_ratio=Decimal("NaN"))
    with pytest.raises(ValueError, match="config"):
        build_research_domain_signal_decay_watch_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_domain_signal_decay_watch_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unique"):
        report((domain_input("macro.rates"), domain_input("macro.rates")))
    with pytest.raises(ValueError, match="observed_at"):
        report((domain_input(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    ready_summary = report((domain_input(),))
    ready = ready_summary.rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(ready, reason_codes=("pass_domain_signal_decay_watch", "watch_forecast_age_decay"))
    with pytest.raises(ValueError, match="status"):
        replace(ready, status="blocked")
    with pytest.raises(ValueError, match="rows"):
        replace(
            report((domain_input("zeta.risk"), domain_input("alpha.risk"))),
            rows=tuple(reversed(report((domain_input("zeta.risk"), domain_input("alpha.risk"))).rows)),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(ready_summary, derived_validation_digest="0" * 64)


def test_module_has_no_io_or_execution_surface_and_no_advice_language() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_domain_signal_decay_watch_report",
    )
    module_source = module.__loader__.get_source(module.__name__)
    assert module_source is not None
    tree = ast.parse(module_source)
    lowered_source = module_source.lower()
    lowered_report = repr(asdict(report((domain_input(),)))).lower()

    forbidden_fragments = (
        "api_key",
        "auth",
        "buy",
        "cancel_order",
        "database",
        "exchange",
        "live_execution",
        "live_trading",
        "place_order",
        "private_key",
        "recommend",
        "sell",
        "submit_order",
        "token",
        "trade",
        "wallet",
    )
    assert not any(fragment in lowered_source for fragment in forbidden_fragments)
    assert not any(fragment in lowered_report for fragment in forbidden_fragments)

    imported_roots: set[str] = set()
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            leaf = call_leaf_name(node.func)
            if leaf is not None:
                call_names.append(leaf)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    assert imported_roots.isdisjoint(
        {
            "aiohttp",
            "ccxt",
            "eth_account",
            "httpx",
            "psycopg",
            "requests",
            "socket",
            "sqlalchemy",
            "sqlite3",
            "subprocess",
            "supabase",
            "urllib",
            "web3",
        },
    )
    assert not (
        set(call_names)
        & {
            "close",
            "commit",
            "connect",
            "cursor",
            "environ",
            "execute",
            "executemany",
            "getenv",
            "open",
            "rollback",
            "send",
            "urlopen",
            "write",
        }
    )
    assert not (
        set(attribute_names)
        & {
            "close",
            "commit",
            "connect",
            "cursor",
            "environ",
            "execute",
            "executemany",
            "getenv",
            "rollback",
            "send",
            "write",
        }
    )

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_domain_signal_decay_watch_report.py"
    )
    assert module_path.name == "research_domain_signal_decay_watch_report.py"


def assert_payload_is_plain_json(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            assert_payload_is_plain_json(child)
    elif isinstance(value, list):
        for child in value:
            assert_payload_is_plain_json(child)
    else:
        assert not isinstance(value, (Decimal, datetime, float))
        assert type(value) is not int


def assert_six_decimal_strings(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if is_public_numeric_field(str(key)):
                assert type(child) is str, key
                assert SIX_DECIMAL_RE.fullmatch(child), (key, child)
            assert_six_decimal_strings(child)
    elif isinstance(value, list):
        for child in value:
            assert_six_decimal_strings(child)


def assert_public_numeric_fields_are_exact_decimals(value: object) -> None:
    for field in fields(value):
        field_value = getattr(value, field.name)
        if is_public_numeric_field(field.name):
            assert type(field_value) is Decimal, (field.name, field_value, type(field_value))
            assert field_value.as_tuple().exponent == -6, field.name


def assert_no_raw_identifiers(value: object) -> None:
    lowered = json.dumps(value, sort_keys=True).lower()
    forbidden_identifier_fragments = (
        "condition_id",
        "event_id",
        "market_slug",
        "question",
        "source_id",
        "source_url",
        "url",
    )
    assert not any(fragment in lowered for fragment in forbidden_identifier_fragments)


def is_public_numeric_field(field_name: str) -> bool:
    return field_name.endswith(
        (
            "_seconds",
            "_count",
            "_ratio",
            "_score",
        ),
    )


def call_leaf_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
