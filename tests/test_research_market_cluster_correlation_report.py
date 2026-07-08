from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import json
from typing import Any

import pytest

import polymarket_alpha_lab.research_market_cluster_correlation_report as api
from polymarket_alpha_lab.research_market_cluster_correlation_report import (
    ResearchMarketClusterCorrelationConfig,
    ResearchMarketClusterCorrelationDigest,
    ResearchMarketClusterCorrelationObservation,
    ResearchMarketClusterCorrelationReport,
    build_research_market_cluster_correlation_report,
    research_market_cluster_correlation_digest,
    research_market_cluster_correlation_digest_payload,
    research_market_cluster_correlation_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "none-offset"


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    candidate_label: str,
    *,
    theme_label: str = "policy",
    risk_label: str = "calendar",
    resolution_window: str = "same_week",
    observed_at: datetime = GENERATED_AT,
    theme_similarity_score: Decimal = Decimal("0.100000"),
    risk_correlation_score: Decimal = Decimal("0.100000"),
    shared_driver_score: Decimal = Decimal("0.100000"),
    evidence_overlap_score: Decimal = Decimal("0.100000"),
    confidence_score: Decimal = Decimal("0.900000"),
) -> ResearchMarketClusterCorrelationObservation:
    return ResearchMarketClusterCorrelationObservation(
        candidate_label=candidate_label,
        theme_label=theme_label,
        risk_label=risk_label,
        resolution_window=resolution_window,
        observed_at=observed_at,
        theme_similarity_score=theme_similarity_score,
        risk_correlation_score=risk_correlation_score,
        shared_driver_score=shared_driver_score,
        evidence_overlap_score=evidence_overlap_score,
        confidence_score=confidence_score,
    )


def config(**overrides: object) -> ResearchMarketClusterCorrelationConfig:
    values: dict[str, object] = {
        "config_version": "research-market-cluster-correlation-report-v0",
        "watch_correlation_score": d("0.450000"),
        "block_correlation_score": d("0.700000"),
        "watch_risk_overlap_score": d("0.450000"),
        "block_risk_overlap_score": d("0.700000"),
        "watch_cluster_event_count": d("2.000000"),
        "block_cluster_event_count": d("3.000000"),
        "watch_confidence_floor": d("0.500000"),
        "block_confidence_floor": d("0.300000"),
    }
    values.update(overrides)
    return ResearchMarketClusterCorrelationConfig(**values)


def report(
    *observations: ResearchMarketClusterCorrelationObservation,
    cfg: ResearchMarketClusterCorrelationConfig | None = None,
) -> ResearchMarketClusterCorrelationReport:
    return build_research_market_cluster_correlation_report(
        observations,
        generated_at=GENERATED_AT,
        config=cfg or config(),
    )


def walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for child in value.values():
            values.extend(walk_payload_values(child))
    elif isinstance(value, list):
        for child in value:
            values.extend(walk_payload_values(child))
    else:
        values.append(value)
    return tuple(values)


def assert_six_decimal_string(value: object) -> None:
    assert isinstance(value, str)
    before, separator, after = value.partition(".")
    assert before
    assert separator == "."
    assert len(after) == 6
    Decimal(value)


def assert_public_numeric_fields_are_decimals(instance: object) -> None:
    for field in fields(instance):
        if field.name.endswith(("_count", "_score", "_floor")):
            value = getattr(instance, field.name)
            assert type(value) is Decimal, (field.name, type(value))
            assert value.as_tuple().exponent == -6


def test_clusters_roll_up_pass_watch_and_block_statuses() -> None:
    cluster_report = report(
        observation("candidate-pass", theme_label="rates", risk_label="macro"),
        observation(
            "candidate-watch",
            theme_label="policy",
            risk_label="calendar",
            theme_similarity_score=d("0.500000"),
            risk_correlation_score=d("0.500000"),
            shared_driver_score=d("0.400000"),
            evidence_overlap_score=d("0.400000"),
            confidence_score=d("0.700000"),
        ),
        observation(
            "candidate-block",
            theme_label="weather",
            risk_label="storm",
            resolution_window="same_day",
            theme_similarity_score=d("0.800000"),
            risk_correlation_score=d("0.850000"),
            shared_driver_score=d("0.750000"),
            evidence_overlap_score=d("0.800000"),
            confidence_score=d("0.600000"),
        ),
    )

    assert cluster_report.status == "block"
    assert cluster_report.cluster_count == d("3.000000")
    assert cluster_report.event_count == d("3.000000")
    assert cluster_report.pass_count == d("1.000000")
    assert cluster_report.watch_count == d("1.000000")
    assert cluster_report.block_count == d("1.000000")
    assert cluster_report.max_correlation_score == d("0.800000")
    assert cluster_report.average_correlation_score == d("0.450000")

    rows_by_status = {row.status: row for row in cluster_report.rows}
    assert rows_by_status["block"].theme_label == "weather"
    assert rows_by_status["block"].correlation_score == d("0.800000")
    assert rows_by_status["block"].reason_codes == (
        "correlation_block",
        "risk_overlap_block",
    )
    assert rows_by_status["watch"].correlation_score == d("0.450000")
    assert rows_by_status["watch"].reason_codes == (
        "correlation_watch",
        "risk_overlap_watch",
    )
    assert rows_by_status["pass"].reason_codes == ("cluster_pass",)
    assert {cluster_report.status, *(row.status for row in cluster_report.rows)} <= {
        "pass",
        "watch",
        "block",
    }


def test_empty_report_blocks_for_manual_review_without_rows() -> None:
    cluster_report = report()
    payload = research_market_cluster_correlation_report_payload(cluster_report)

    assert cluster_report.status == "block"
    assert cluster_report.digest.status == "block"
    assert cluster_report.cluster_count == d("0.000000")
    assert cluster_report.event_count == d("0.000000")
    assert cluster_report.rows == ()
    assert cluster_report.reason_codes == ("empty_observations",)
    assert payload["status"] == "block"
    assert payload["digest"]["reason_codes"] == ["empty_observations"]


def test_group_size_and_confidence_trigger_watch_and_block_flags() -> None:
    watch_report = report(
        observation("candidate-a", theme_label="macro", risk_label="prints"),
        observation("candidate-b", theme_label="macro", risk_label="prints"),
    )
    block_report = report(
        observation("candidate-c", theme_label="courts", risk_label="deadline"),
        observation("candidate-d", theme_label="courts", risk_label="deadline"),
        observation("candidate-e", theme_label="courts", risk_label="deadline"),
    )
    low_confidence_report = report(
        observation(
            "candidate-f",
            theme_label="weather",
            risk_label="model",
            confidence_score=d("0.250000"),
        ),
    )

    assert watch_report.status == "watch"
    assert watch_report.rows[0].reason_codes == ("cluster_size_watch",)
    assert block_report.status == "block"
    assert block_report.rows[0].reason_codes == ("cluster_size_block",)
    assert low_confidence_report.status == "block"
    assert low_confidence_report.rows[0].reason_codes == ("confidence_block",)


def test_payload_redacts_candidates_serializes_decimals_and_preserves_digest_consistency() -> None:
    cluster_report = report(
        observation("candidate-alpha"),
        observation(
            "candidate-beta",
            theme_label="policy",
            risk_label="deadline",
            theme_similarity_score=d("0.500000"),
            risk_correlation_score=d("0.500000"),
            shared_driver_score=d("0.400000"),
            evidence_overlap_score=d("0.400000"),
        ),
    )

    report_payload = research_market_cluster_correlation_report_payload(cluster_report)
    digest_payload = research_market_cluster_correlation_digest_payload(
        research_market_cluster_correlation_digest(cluster_report),
    )
    encoded = json.dumps(report_payload, sort_keys=True)

    assert report_payload == cluster_report.payload
    assert digest_payload == cluster_report.digest.payload
    assert report_payload["digest"] == digest_payload
    assert cluster_report.digest.status == cluster_report.status
    assert cluster_report.digest.cluster_count == cluster_report.cluster_count
    assert cluster_report.digest.event_count == cluster_report.event_count
    assert cluster_report.digest.max_correlation_score == cluster_report.max_correlation_score
    assert report_payload["cluster_count"] == "2.000000"
    assert report_payload["rows"][0]["correlation_score"] == "0.450000"
    assert report_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert isinstance(report_payload["derived_validation_digest"], str)
    assert len(report_payload["derived_validation_digest"]) == 64
    assert isinstance(digest_payload["derived_validation_digest"], str)
    assert len(digest_payload["derived_validation_digest"]) == 64
    assert "candidate-alpha" not in encoded
    assert "candidate-beta" not in encoded
    assert all(type(value) is not Decimal for value in walk_payload_values(report_payload))
    assert all(type(value) is not float for value in walk_payload_values(report_payload))
    assert_six_decimal_string(report_payload["event_count"])
    assert_six_decimal_string(report_payload["rows"][0]["average_confidence_score"])


def test_deterministic_payload_for_reversed_inputs_and_report_digest_tampering() -> None:
    rows = (
        observation("candidate-z", theme_label="policy", risk_label="calendar"),
        observation(
            "candidate-a",
            theme_label="weather",
            risk_label="storm",
            theme_similarity_score=d("0.800000"),
            risk_correlation_score=d("0.850000"),
            shared_driver_score=d("0.750000"),
            evidence_overlap_score=d("0.800000"),
        ),
        observation(
            "candidate-m",
            theme_label="policy",
            risk_label="calendar",
            theme_similarity_score=d("0.500000"),
            risk_correlation_score=d("0.500000"),
            shared_driver_score=d("0.400000"),
            evidence_overlap_score=d("0.400000"),
        ),
    )

    first = report(*rows)
    second = report(*tuple(reversed(rows)))
    first_payload = research_market_cluster_correlation_report_payload(first)
    second_payload = research_market_cluster_correlation_report_payload(second)

    assert first == second
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )

    bad_digest = first.digest
    object.__setattr__(bad_digest, "max_correlation_score", d("0.000000"))
    with pytest.raises(ValueError, match="digest"):
        replace(first, digest=bad_digest)
    with pytest.raises(ValueError, match="payload"):
        research_market_cluster_correlation_report_payload(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="digest"):
        research_market_cluster_correlation_digest_payload(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    [
        "theme_similarity_score",
        "risk_correlation_score",
        "shared_driver_score",
        "evidence_overlap_score",
        "confidence_score",
    ],
)
def test_rejects_float_and_decimal_subclasses_for_public_numerics(field_name: str) -> None:
    values: dict[str, Any] = {
        "candidate_label": "candidate-float",
        "theme_label": "policy",
        "risk_label": "calendar",
        "resolution_window": "same_week",
        "observed_at": GENERATED_AT,
        "theme_similarity_score": d("0.100000"),
        "risk_correlation_score": d("0.100000"),
        "shared_driver_score": d("0.100000"),
        "evidence_overlap_score": d("0.100000"),
        "confidence_score": d("0.900000"),
    }
    values[field_name] = 0.5
    with pytest.raises(ValueError, match=f"{field_name} must be a Decimal"):
        ResearchMarketClusterCorrelationObservation(**values)

    values[field_name] = _DecimalSubclass("0.500000")
    with pytest.raises(ValueError, match=f"{field_name} must be a Decimal"):
        ResearchMarketClusterCorrelationObservation(**values)


def test_rejects_bad_times_counts_thresholds_and_config_types() -> None:
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        observation("candidate-time", observed_at=_DateTimeSubclass(2026, 7, 8, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation("candidate-none-offset", observed_at=datetime(2026, 7, 8, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(observation("candidate-future", observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_market_cluster_correlation_report(
            (),
            generated_at=datetime(2026, 7, 8),
        )
    with pytest.raises(ValueError, match="config"):
        build_research_market_cluster_correlation_report(
            (),
            generated_at=GENERATED_AT,
            config=object(),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="whole-count Decimal"):
        config(watch_cluster_event_count=d("1.500000"))
    with pytest.raises(ValueError, match="watch threshold"):
        config(watch_correlation_score=d("0.800000"), block_correlation_score=d("0.700000"))
    with pytest.raises(ValueError, match="candidate_label values must be unique"):
        report(observation("candidate-dup"), observation("candidate-dup", theme_label="weather"))

    eastern_observed = datetime(2026, 7, 8, 7, 0, tzinfo=timezone(timedelta(hours=-4)))
    normalized = report(observation("candidate-eastern", observed_at=eastern_observed))
    assert normalized.rows[0].event_count == d("1.000000")


def test_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    cluster_report = report(observation("candidate-frozen"))

    public_classes = tuple(
        getattr(api, name)
        for name in api.__all__
        if isinstance(getattr(api, name), type)
    )
    for public_class in public_classes:
        assert public_class.__dataclass_params__.frozen is True
        for field in fields(public_class):
            if field.name.endswith(("_count", "_score", "_floor")):
                assert field.type in (Decimal, "Decimal")

    for instance in (
        config(),
        observation("candidate-decimal-check"),
        cluster_report.rows[0],
        cluster_report.digest,
        cluster_report,
    ):
        assert_public_numeric_fields_are_decimals(instance)

    with pytest.raises(FrozenInstanceError):
        cluster_report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):
        type("BadReport", (ResearchMarketClusterCorrelationReport,), {})

    subclass = _make_subclass_bypassing_final_guard(ResearchMarketClusterCorrelationDigest)
    with pytest.raises(ValueError, match="must be exactly"):
        subclass(**{field.name: getattr(cluster_report.digest, field.name) for field in fields(cluster_report.digest)})


def test_hard_flags_are_required_for_config_inputs_rows_digest_and_report() -> None:
    cluster_report = report(observation("candidate-flags"))

    invalid_cases = (
        lambda: config(paper_only=False),
        lambda: ResearchMarketClusterCorrelationObservation(
            candidate_label="candidate-flag-input",
            theme_label="policy",
            risk_label="calendar",
            resolution_window="same_week",
            observed_at=GENERATED_AT,
            theme_similarity_score=d("0.100000"),
            risk_correlation_score=d("0.100000"),
            shared_driver_score=d("0.100000"),
            evidence_overlap_score=d("0.100000"),
            confidence_score=d("0.900000"),
            report_only=False,
        ),
        lambda: replace(cluster_report.rows[0], readonly=False),
        lambda: replace(cluster_report.digest, paper_only=False),
        lambda: replace(cluster_report, report_only=False),
    )
    for make_invalid in invalid_cases:
        with pytest.raises(ValueError, match="must be True"):
            make_invalid()

    object.__setattr__(cluster_report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        research_market_cluster_correlation_report_payload(cluster_report)
    object.__setattr__(cluster_report.rows[0], "readonly", True)

    object.__setattr__(cluster_report.digest, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        research_market_cluster_correlation_report_payload(cluster_report)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("candidate_label", "raw_candidate_id_abc"),
        ("candidate_label", "candidate_id_abc"),
        ("theme_label", "market_slug_abc"),
        ("risk_label", "market_question_abc"),
        ("resolution_window", "source_ref_abc"),
        ("theme_label", "https://example.test/path"),
        ("risk_label", "postgres_dsn_value"),
        ("theme_label", "table_value"),
        ("risk_label", "token_value"),
        ("candidate_label", "wallet_value"),
        ("candidate_label", "order_value"),
        ("candidate_label", "trade_value"),
        ("candidate_label", "position_value"),
        ("candidate_label", "buy_value"),
        ("candidate_label", "sell_value"),
        ("candidate_label", "recommend_value"),
    ),
)
def test_public_leak_rejection(field_name: str, value: str) -> None:
    values: dict[str, object] = {
        "candidate_label": "candidate-safe",
        "theme_label": "policy",
        "risk_label": "calendar",
        "resolution_window": "same_week",
        "observed_at": GENERATED_AT,
        "theme_similarity_score": d("0.100000"),
        "risk_correlation_score": d("0.100000"),
        "shared_driver_score": d("0.100000"),
        "evidence_overlap_score": d("0.100000"),
        "confidence_score": d("0.900000"),
    }
    values[field_name] = value
    with pytest.raises(ValueError, match="unsafe public"):
        ResearchMarketClusterCorrelationObservation(**values)


def test_public_payload_contains_no_private_surfaces_or_external_capabilities() -> None:
    cluster_report = report(
        observation("candidate-hidden-a"),
        observation(
            "candidate-hidden-b",
            theme_similarity_score=d("0.500000"),
            risk_correlation_score=d("0.500000"),
            shared_driver_score=d("0.400000"),
            evidence_overlap_score=d("0.400000"),
        ),
    )
    payload = research_market_cluster_correlation_report_payload(cluster_report)
    encoded = json.dumps(payload, sort_keys=True).lower()

    forbidden_payload_terms = (
        "candidate-hidden-a",
        "candidate-hidden-b",
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    for forbidden in forbidden_payload_terms:
        assert forbidden not in encoded

    module_source = api.__loader__.get_source(api.__name__)
    assert module_source is not None
    tree = ast.parse(module_source)
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imported_roots.isdisjoint(
        {
            "aiohttp",
            "httpx",
            "os",
            "pathlib",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "subprocess",
            "urllib",
            "web3",
        },
    )
    forbidden_calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name) and function.id in {"open", "float"}:
                forbidden_calls.append(function.id)
            elif isinstance(function, ast.Attribute) and function.attr in {
                "connect",
                "glob",
                "iterdir",
                "open",
                "read_bytes",
                "read_text",
                "request",
                "write_bytes",
                "write_text",
            }:
                forbidden_calls.append(function.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
    assert forbidden_calls == []


def _make_subclass_bypassing_final_guard(public_type: type[object]) -> type[object]:
    sentinel = object()
    original_init_subclass = public_type.__dict__.get("__init_subclass__", sentinel)
    public_type.__init_subclass__ = classmethod(lambda cls, **kwargs: None)  # type: ignore[attr-defined]
    try:
        return type(f"{public_type.__name__}BypassedSubclass", (public_type,), {})
    finally:
        if original_init_subclass is sentinel:
            delattr(public_type, "__init_subclass__")
        else:
            public_type.__init_subclass__ = original_init_subclass  # type: ignore[attr-defined]
