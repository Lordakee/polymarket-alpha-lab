from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
REASON_PREFIX = "market_research_contradiction_priority_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
EMPTY_REASON = f"{REASON_PREFIX}empty"
CONTRADICTION_COUNT_REASON = f"{REASON_PREFIX}contradiction_count_present"
SOURCE_SPREAD_REASON = f"{REASON_PREFIX}source_reliability_spread_elevated"
EVIDENCE_RECENT_REASON = f"{REASON_PREFIX}evidence_recent"
MARKET_MOVED_REASON = f"{REASON_PREFIX}market_moved_after_contradiction"
NO_CONTRADICTIONS_REASON = f"{REASON_PREFIX}no_contradictions_observed"
HIGH_PRIORITY_REASON = f"{REASON_PREFIX}high_priority_contradiction_review"
MEDIUM_PRIORITY_REASON = f"{REASON_PREFIX}medium_priority_contradiction_review"
LOW_PRIORITY_REASON = f"{REASON_PREFIX}low_priority_contradiction_review"


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


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_contradiction_priority_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    condition_id: str,
    *,
    contradiction_count: Decimal,
    min_source_reliability: Decimal,
    max_source_reliability: Decimal,
    evidence_observed_at: datetime,
    market_probability_at_contradiction: Decimal,
    current_market_probability: Decimal,
    source_reference: str = "manual-research-rollup",
):
    digest_module = module()
    return digest_module.MarketResearchContradictionObservation(
        condition_id=condition_id,
        contradiction_count=contradiction_count,
        min_source_reliability=min_source_reliability,
        max_source_reliability=max_source_reliability,
        evidence_observed_at=evidence_observed_at,
        market_probability_at_contradiction=market_probability_at_contradiction,
        current_market_probability=current_market_probability,
        source_reference=source_reference,
    )


def config(**overrides: object):
    digest_module = module()
    values = {
        "config_version": "market-research-contradiction-priority-v0",
        "recency_watch_window_hours": d("72.000000"),
        "movement_watch_threshold": d("0.050000"),
        "reliability_spread_watch_threshold": d("0.300000"),
        "high_priority_score_threshold": d("7.000000"),
        "medium_priority_score_threshold": d("3.000000"),
    }
    values.update(overrides)
    return digest_module.MarketResearchContradictionPriorityConfig(**values)


def build_report(*observations):
    digest_module = module()
    return digest_module.build_market_research_contradiction_priority_digest(
        observations,
        config=config(),
        generated_at=GENERATED_AT,
    )


def _walk_payload(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for child in value.values():
            values.extend(_walk_payload(child))
    elif isinstance(value, list):
        for child in value:
            values.extend(_walk_payload(child))
    else:
        values.append(value)
    return tuple(values)


def _assert_six_decimal_string(value: object) -> None:
    assert isinstance(value, str)
    before, separator, after = value.partition(".")
    assert before
    assert separator == "."
    assert len(after) == 6
    Decimal(value)


def _assert_public_numeric_fields_are_exact_decimals(instance: object) -> None:
    numeric_suffixes = ("_count", "_ratio", "_score", "_hours", "_threshold")
    for field in fields(instance):
        if field.name.endswith(numeric_suffixes):
            value = getattr(instance, field.name)
            assert type(value) is Decimal, (field.name, type(value))
            assert value.as_tuple().exponent == -6, (field.name, value)


def test_prioritizes_contradictions_with_deterministic_sort_reasons_and_counts() -> None:
    digest_module = module()

    report = build_report(
        observation(
            "condition-medium",
            contradiction_count=d("2.000000"),
            min_source_reliability=d("0.500000"),
            max_source_reliability=d("0.800000"),
            evidence_observed_at=GENERATED_AT - timedelta(hours=70),
            market_probability_at_contradiction=d("0.500000"),
            current_market_probability=d("0.560000"),
        ),
        observation(
            "condition-low",
            contradiction_count=d("0.000000"),
            min_source_reliability=d("0.700000"),
            max_source_reliability=d("0.720000"),
            evidence_observed_at=GENERATED_AT - timedelta(hours=120),
            market_probability_at_contradiction=d("0.330000"),
            current_market_probability=d("0.340000"),
        ),
        observation(
            "condition-high",
            contradiction_count=d("5.000000"),
            min_source_reliability=d("0.250000"),
            max_source_reliability=d("0.950000"),
            evidence_observed_at=GENERATED_AT - timedelta(hours=6),
            market_probability_at_contradiction=d("0.400000"),
            current_market_probability=d("0.600000"),
        ),
    )

    assert tuple(row.condition_id for row in report.rows) == (
        "condition-high",
        "condition-medium",
        "condition-low",
    )
    assert report.priority_status == "high"
    assert report.total_market_count == d("3.000000")
    assert report.high_priority_count == d("1.000000")
    assert report.medium_priority_count == d("1.000000")
    assert report.low_priority_count == d("1.000000")
    assert report.max_priority_score == d("9.900000")
    assert report.average_priority_score == d("4.346667")
    assert report.rows[0].source_reliability_spread == d("0.700000")
    assert report.rows[0].evidence_age_hours == d("6.000000")
    assert report.rows[0].market_movement_since_contradiction == d("0.200000")
    assert report.rows[0].priority_score == d("9.900000")
    assert report.rows[0].priority_status == "high"
    assert report.rows[0].reason_codes == (
        CONTRADICTION_COUNT_REASON,
        SOURCE_SPREAD_REASON,
        EVIDENCE_RECENT_REASON,
        MARKET_MOVED_REASON,
        HIGH_PRIORITY_REASON,
    )
    assert report.rows[1].priority_status == "medium"
    assert MEDIUM_PRIORITY_REASON in report.rows[1].reason_codes
    assert report.rows[2].reason_codes == (
        NO_CONTRADICTIONS_REASON,
        LOW_PRIORITY_REASON,
    )
    assert report.reason_codes == tuple(
        reason_count.reason_code for reason_count in report.reason_code_counts
    )
    assert report.reason_code_counts == (
        digest_module.MarketResearchContradictionPriorityDigestReasonCodeCount(
            reason_code=CONTRADICTION_COUNT_REASON,
            count=d("2.000000"),
            market_ratio=d("0.666667"),
        ),
        digest_module.MarketResearchContradictionPriorityDigestReasonCodeCount(
            reason_code=SOURCE_SPREAD_REASON,
            count=d("2.000000"),
            market_ratio=d("0.666667"),
        ),
        digest_module.MarketResearchContradictionPriorityDigestReasonCodeCount(
            reason_code=EVIDENCE_RECENT_REASON,
            count=d("2.000000"),
            market_ratio=d("0.666667"),
        ),
        digest_module.MarketResearchContradictionPriorityDigestReasonCodeCount(
            reason_code=MARKET_MOVED_REASON,
            count=d("2.000000"),
            market_ratio=d("0.666667"),
        ),
        digest_module.MarketResearchContradictionPriorityDigestReasonCodeCount(
            reason_code=NO_CONTRADICTIONS_REASON,
            count=d("1.000000"),
            market_ratio=d("0.333333"),
        ),
        digest_module.MarketResearchContradictionPriorityDigestReasonCodeCount(
            reason_code=HIGH_PRIORITY_REASON,
            count=d("1.000000"),
            market_ratio=d("0.333333"),
        ),
        digest_module.MarketResearchContradictionPriorityDigestReasonCodeCount(
            reason_code=MEDIUM_PRIORITY_REASON,
            count=d("1.000000"),
            market_ratio=d("0.333333"),
        ),
        digest_module.MarketResearchContradictionPriorityDigestReasonCodeCount(
            reason_code=LOW_PRIORITY_REASON,
            count=d("1.000000"),
            market_ratio=d("0.333333"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_input_blocks_as_missing_evidence_with_synthetic_reason_counts() -> None:
    digest_module = module()

    report = build_report()

    assert report.priority_status == "blocked"
    assert report.total_market_count == d("0.000000")
    assert report.high_priority_count == d("0.000000")
    assert report.medium_priority_count == d("0.000000")
    assert report.low_priority_count == d("0.000000")
    assert report.max_priority_score == d("0.000000")
    assert report.average_priority_score == d("0.000000")
    assert report.reason_codes == (NO_INPUTS_REASON, EMPTY_REASON)
    assert report.rows == ()
    assert report.reason_code_counts == (
        digest_module.MarketResearchContradictionPriorityDigestReasonCodeCount(
            reason_code=NO_INPUTS_REASON,
            count=d("1.000000"),
            market_ratio=d("0.000000"),
        ),
        digest_module.MarketResearchContradictionPriorityDigestReasonCodeCount(
            reason_code=EMPTY_REASON,
            count=d("1.000000"),
            market_ratio=d("0.000000"),
        ),
    )


def test_payload_serializes_six_decimal_strings_and_redacts_references() -> None:
    digest_module = module()
    secret = "postgres://reader:secret-token@localhost/research"
    source = observation(
        "condition-secret",
        contradiction_count=d("1.000000"),
        min_source_reliability=d("0.400000"),
        max_source_reliability=d("0.800000"),
        evidence_observed_at=GENERATED_AT,
        market_probability_at_contradiction=d("0.500000"),
        current_market_probability=d("0.550000"),
        source_reference=secret,
    )

    report = build_report(source)
    payload = digest_module.market_research_contradiction_priority_digest_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert source.source_reference == "<redacted-source-reference>"
    assert report.rows[0].source_reference == "<redacted-source-reference>"
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["total_market_count"] == "1.000000"
    assert payload["rows"][0]["contradiction_count"] == "1.000000"
    assert payload["rows"][0]["priority_score"] == "4.400000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["market_ratio"] == "1.000000"
    assert secret not in repr(source)
    assert secret not in repr(report)
    assert secret not in encoded
    assert all(type(value) is not float for value in _walk_payload(payload))
    assert all(type(value) is not Decimal for value in _walk_payload(payload))
    _assert_six_decimal_string(payload["total_market_count"])
    _assert_six_decimal_string(payload["rows"][0]["priority_score"])
    _assert_six_decimal_string(payload["reason_code_counts"][0]["market_ratio"])


def test_payload_rejects_tampered_nested_public_values() -> None:
    digest_module = module()
    report = build_report(
        observation(
            "condition-tamper",
            contradiction_count=d("1.000000"),
            min_source_reliability=d("0.400000"),
            max_source_reliability=d("0.600000"),
            evidence_observed_at=GENERATED_AT,
            market_probability_at_contradiction=d("0.500000"),
            current_market_probability=d("0.520000"),
        ),
    )

    object.__setattr__(report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        digest_module.market_research_contradiction_priority_digest_payload(report)
    object.__setattr__(report.rows[0], "readonly", True)

    object.__setattr__(report.reason_code_counts[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        digest_module.market_research_contradiction_priority_digest_payload(report)
    object.__setattr__(report.reason_code_counts[0], "report_only", True)

    object.__setattr__(report.rows[0], "priority_score", d("4.4000001"))
    with pytest.raises(ValueError, match="six decimals"):
        digest_module.market_research_contradiction_priority_digest_payload(report)


def test_dataclasses_are_frozen_decimal_only_and_public_api_is_local() -> None:
    digest_module = module()

    assert digest_module.__all__ == (
        "DEFAULT_MARKET_RESEARCH_CONTRADICTION_PRIORITY_CONFIG_VERSION",
        "MarketResearchContradictionObservation",
        "MarketResearchContradictionPriorityConfig",
        "MarketResearchContradictionPriorityDigest",
        "MarketResearchContradictionPriorityDigestReasonCodeCount",
        "MarketResearchContradictionPriorityRow",
        "build_market_research_contradiction_priority_digest",
        "market_research_contradiction_priority_digest_payload",
    )
    public_classes = tuple(
        getattr(digest_module, name)
        for name in digest_module.__all__
        if isinstance(getattr(digest_module, name), type)
    )
    for public_class in public_classes:
        assert is_dataclass(public_class)
        assert public_class.__dataclass_params__.frozen is True
        for field in fields(public_class):
            if field.name.endswith(("_count", "_ratio", "_score", "_hours", "_threshold")):
                assert field.type in (Decimal, "Decimal")

    report = build_report(
        observation(
            "condition-frozen",
            contradiction_count=d("1.000000"),
            min_source_reliability=d("0.400000"),
            max_source_reliability=d("0.600000"),
            evidence_observed_at=GENERATED_AT,
            market_probability_at_contradiction=d("0.500000"),
            current_market_probability=d("0.520000"),
        ),
    )
    for instance in (
        config(),
        report,
        report.rows[0],
        report.reason_code_counts[0],
    ):
        _assert_public_numeric_fields_are_exact_decimals(instance)

    with pytest.raises(FrozenInstanceError):
        report.rows[0].priority_status = "high"  # type: ignore[misc]


def test_generated_at_and_evidence_observed_at_are_normalized_to_utc() -> None:
    digest_module = module()
    eastern_observed = datetime(2026, 7, 2, 6, 0, tzinfo=timezone(timedelta(hours=-4)))

    report = digest_module.build_market_research_contradiction_priority_digest(
        (
            observation(
                "condition-time",
                contradiction_count=d("1.000000"),
                min_source_reliability=d("0.400000"),
                max_source_reliability=d("0.600000"),
                evidence_observed_at=eastern_observed,
                market_probability_at_contradiction=d("0.500000"),
                current_market_probability=d("0.520000"),
            ),
        ),
        config=digest_module.MarketResearchContradictionPriorityConfig(),
        generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=timezone.utc),
    )

    assert report.generated_at == datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
    assert report.rows[0].evidence_observed_at == datetime(2026, 7, 2, 10, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        digest_module.build_market_research_contradiction_priority_digest(
            (),
            config=digest_module.MarketResearchContradictionPriorityConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 8, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest_module.build_market_research_contradiction_priority_digest(
            (),
            config=digest_module.MarketResearchContradictionPriorityConfig(),
            generated_at=datetime(2026, 7, 2, 8, 0),
        )
    with pytest.raises(ValueError, match="evidence_observed_at must be timezone-aware"):
        observation(
            "condition-none-offset",
            contradiction_count=d("1.000000"),
            min_source_reliability=d("0.400000"),
            max_source_reliability=d("0.600000"),
            evidence_observed_at=datetime(2026, 7, 2, 8, 0, tzinfo=_NoneOffsetTz()),
            market_probability_at_contradiction=d("0.500000"),
            current_market_probability=d("0.520000"),
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "contradiction_count",
        "min_source_reliability",
        "max_source_reliability",
        "market_probability_at_contradiction",
        "current_market_probability",
    ],
)
def test_rejects_float_public_numerics_to_keep_public_fields_decimal_only(
    field_name: str,
) -> None:
    kwargs: dict[str, Any] = {
        "condition_id": "condition-float",
        "contradiction_count": d("1.000000"),
        "min_source_reliability": d("0.400000"),
        "max_source_reliability": d("0.600000"),
        "evidence_observed_at": GENERATED_AT,
        "market_probability_at_contradiction": d("0.500000"),
        "current_market_probability": d("0.520000"),
    }
    kwargs[field_name] = 0.5

    with pytest.raises(ValueError, match=f"{field_name} must be a Decimal"):
        module().MarketResearchContradictionObservation(**kwargs)


def test_rejects_non_finite_decimal_subclasses_and_fractional_counts() -> None:
    digest_module = module()

    with pytest.raises(ValueError, match="min_source_reliability must be finite"):
        observation(
            "condition-nonfinite",
            contradiction_count=d("1.000000"),
            min_source_reliability=Decimal("NaN"),
            max_source_reliability=d("0.600000"),
            evidence_observed_at=GENERATED_AT,
            market_probability_at_contradiction=d("0.500000"),
            current_market_probability=d("0.520000"),
        )
    with pytest.raises(ValueError, match="min_source_reliability must be a Decimal"):
        observation(
            "condition-decimal-subclass",
            contradiction_count=d("1.000000"),
            min_source_reliability=_DecimalSubclass("0.400000"),
            max_source_reliability=d("0.600000"),
            evidence_observed_at=GENERATED_AT,
            market_probability_at_contradiction=d("0.500000"),
            current_market_probability=d("0.520000"),
        )
    with pytest.raises(ValueError, match="contradiction_count must be a whole-count Decimal"):
        observation(
            "condition-fractional-count",
            contradiction_count=d("1.500000"),
            min_source_reliability=d("0.400000"),
            max_source_reliability=d("0.600000"),
            evidence_observed_at=GENERATED_AT,
            market_probability_at_contradiction=d("0.500000"),
            current_market_probability=d("0.520000"),
        )
    with pytest.raises(ValueError, match="count must be positive"):
        digest_module.MarketResearchContradictionPriorityDigestReasonCodeCount(
            reason_code=NO_INPUTS_REASON,
            count=d("0.000000"),
            market_ratio=d("0.000000"),
        )


def test_rejects_invalid_counts_reliability_ranges_and_false_flags_without_leaks() -> None:
    digest_module = module()
    secret = "token=research-secret"

    with pytest.raises(ValueError) as negative_count:
        digest_module.MarketResearchContradictionObservation(
            condition_id="condition-bad-count",
            contradiction_count=d("-1.000000"),
            min_source_reliability=d("0.400000"),
            max_source_reliability=d("0.600000"),
            evidence_observed_at=GENERATED_AT,
            market_probability_at_contradiction=d("0.500000"),
            current_market_probability=d("0.520000"),
            source_reference=secret,
        )
    assert "contradiction_count must be nonnegative" in str(negative_count.value)
    assert secret not in str(negative_count.value)

    with pytest.raises(ValueError, match="max_source_reliability must be >= min_source_reliability"):
        observation(
            "condition-bad-range",
            contradiction_count=d("1.000000"),
            min_source_reliability=d("0.800000"),
            max_source_reliability=d("0.600000"),
            evidence_observed_at=GENERATED_AT,
            market_probability_at_contradiction=d("0.500000"),
            current_market_probability=d("0.520000"),
        )

    report = build_report(
        observation(
            "condition-flags",
            contradiction_count=d("1.000000"),
            min_source_reliability=d("0.400000"),
            max_source_reliability=d("0.600000"),
            evidence_observed_at=GENERATED_AT,
            market_probability_at_contradiction=d("0.500000"),
            current_market_probability=d("0.520000"),
        ),
    )
    false_flag_cases = (
        lambda: config(paper_only=False),
        lambda: config(report_only=False),
        lambda: config(readonly=False),
        lambda: replace(report.rows[0], paper_only=False),
        lambda: replace(report.rows[0], report_only=False),
        lambda: replace(report.rows[0], readonly=False),
        lambda: replace(report.reason_code_counts[0], paper_only=False),
        lambda: replace(report.reason_code_counts[0], report_only=False),
        lambda: replace(report.reason_code_counts[0], readonly=False),
        lambda: replace(report, paper_only=False),
        lambda: replace(report, report_only=False),
        lambda: replace(report, readonly=False),
    )
    for make_invalid in false_flag_cases:
        with pytest.raises(ValueError, match="must be True"):
            make_invalid()


def test_public_constructors_reject_noncanonical_rows_reasons_and_counts() -> None:
    report = build_report(
        observation(
            "condition-a",
            contradiction_count=d("5.000000"),
            min_source_reliability=d("0.200000"),
            max_source_reliability=d("0.950000"),
            evidence_observed_at=GENERATED_AT - timedelta(hours=2),
            market_probability_at_contradiction=d("0.300000"),
            current_market_probability=d("0.550000"),
        ),
        observation(
            "condition-b",
            contradiction_count=d("2.000000"),
            min_source_reliability=d("0.500000"),
            max_source_reliability=d("0.700000"),
            evidence_observed_at=GENERATED_AT - timedelta(hours=80),
            market_probability_at_contradiction=d("0.500000"),
            current_market_probability=d("0.520000"),
        ),
    )

    with pytest.raises(ValueError, match="rows must use deterministic sequence"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_codes must use deterministic sequence"):
        replace(report, reason_codes=tuple(reversed(report.reason_codes)))
    with pytest.raises(ValueError, match="reason_code_counts must use deterministic sequence"):
        replace(report, reason_code_counts=tuple(reversed(report.reason_code_counts)))
    with pytest.raises(ValueError, match="reason_codes must use deterministic sequence"):
        replace(report.rows[0], reason_codes=tuple(reversed(report.rows[0].reason_codes)))
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(report, reason_code_counts=report.reason_code_counts[1:])


def test_public_dataclasses_reject_subclassing_at_definition_and_instantiation() -> None:
    digest_module = module()
    report = build_report(
        observation(
            "condition-subclass",
            contradiction_count=d("1.000000"),
            min_source_reliability=d("0.400000"),
            max_source_reliability=d("0.600000"),
            evidence_observed_at=GENERATED_AT,
            market_probability_at_contradiction=d("0.500000"),
            current_market_probability=d("0.520000"),
        ),
    )
    values = (
        config(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
        observation(
            "condition-subclass-input",
            contradiction_count=d("1.000000"),
            min_source_reliability=d("0.400000"),
            max_source_reliability=d("0.600000"),
            evidence_observed_at=GENERATED_AT,
            market_probability_at_contradiction=d("0.500000"),
            current_market_probability=d("0.520000"),
        ),
    )

    for value in values:
        public_type = type(value)
        kwargs = {field.name: getattr(value, field.name) for field in fields(public_type)}

        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})

        subclass = _make_subclass_bypassing_final_guard(public_type)
        with pytest.raises(ValueError, match="must be exactly"):
            subclass(**kwargs)

    with pytest.raises(ValueError, match="config must be a MarketResearchContradictionPriorityConfig"):
        digest_module.build_market_research_contradiction_priority_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_module_omits_forbidden_external_action_io_and_secret_surfaces() -> None:
    source = module().__loader__.get_source(module().__name__)
    assert source is not None
    lowered = source.lower()
    tree = ast.parse(source)

    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imported_roots.isdisjoint(
        {
            "httpx",
            "os",
            "pathlib",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "subprocess",
            "urllib",
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

    for forbidden in (
        "live",
        "auth",
        "wallet",
        "order",
        "cancel",
        "replace",
        "exchange",
        "mutation",
        "private_key",
        "api_key",
        "secret",
    ):
        assert forbidden not in lowered


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
