from __future__ import annotations

import ast
import importlib
import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Context, Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
from hashlib import sha256
from itertools import permutations
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_cross_domain_authority_memory_router_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_cross_domain_authority_memory_router_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 16, 0, tzinfo=UTC)

REPORT_FIELDS = (
    "generated_at",
    "config_version",
    "status",
    "route_count",
    "domain_count",
    "authority_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_router_score",
    "lowest_domain_alignment_score",
    "lowest_authority_score",
    "lowest_memory_score",
    "highest_conflict_score",
    "highest_memory_age_seconds",
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_FIELDS = (
    "route_ref",
    "domain_label",
    "authority_label",
    "memory_label",
    "domain_alignment_score",
    "authority_score",
    "memory_score",
    "memory_observed_at",
    "memory_age_seconds",
    "max_watch_memory_age_seconds",
    "conflict_score",
    "memory_freshness_score",
    "router_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_pass_domain_alignment_score": d("0.700000"),
        "min_watch_domain_alignment_score": d("0.500000"),
        "min_pass_authority_score": d("0.700000"),
        "min_watch_authority_score": d("0.500000"),
        "min_pass_memory_score": d("0.700000"),
        "min_watch_memory_score": d("0.500000"),
        "max_pass_memory_age_seconds": d("604800.000000"),
        "max_watch_memory_age_seconds": d("1209600.000000"),
        "max_pass_conflict_score": d("0.250000"),
        "max_watch_conflict_score": d("0.500000"),
    }
    values |= overrides
    return module.ResearchStrategyCrossDomainAuthorityMemoryRouterConfig(**values)


def signal(**overrides: object) -> Any:
    module = api()
    values = {
        "route_ref": "route-alpha",
        "domain_label": "macro",
        "authority_label": "primary-clock",
        "memory_label": "settlement-pattern",
        "domain_alignment_score": d("0.850000"),
        "authority_score": d("0.900000"),
        "memory_score": d("0.800000"),
        "memory_observed_at": GENERATED_AT - timedelta(days=3),
        "conflict_score": d("0.100000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values |= overrides
    return module.ResearchStrategyCrossDomainAuthorityMemoryRouterSignal(**values)


def report(
    *items: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_strategy_cross_domain_authority_memory_router_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def resign_payload(payload: dict[str, Any]) -> None:
    payload["derived_validation_digest"] = canonical_digest(payload)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        if field.name.endswith(("_count", "_score", "_seconds")):
            assert type(item) is Decimal
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_fields_are_decimal(nested)


def assert_no_raw_numbers(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_raw_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_raw_numbers(item)


def test_builds_cross_domain_authority_memory_router_pass_watch_and_block() -> None:
    module = api()
    result = report(
        signal(
            route_ref="route-watch",
            domain_label="rates",
            authority_label="filing-clock",
            memory_label="deadline-pattern",
            domain_alignment_score=d("0.620000"),
            authority_score=d("0.650000"),
            memory_score=d("0.600000"),
            memory_observed_at=GENERATED_AT - timedelta(days=10),
            conflict_score=d("0.350000"),
        ),
        signal(
            route_ref="route-pass",
            domain_label="weather",
            authority_label="agency-clock",
            memory_label="resolution-window",
            domain_alignment_score=d("0.850000"),
            authority_score=d("0.900000"),
            memory_score=d("0.800000"),
            memory_observed_at=GENERATED_AT - timedelta(days=3),
            conflict_score=d("0.100000"),
        ),
        signal(
            route_ref="route-block",
            domain_label="crypto",
            authority_label="settlement-clock",
            memory_label="conflict-pattern",
            domain_alignment_score=d("0.400000"),
            authority_score=d("0.450000"),
            memory_score=d("0.490000"),
            memory_observed_at=GENERATED_AT - timedelta(days=20),
            conflict_score=d("0.700000"),
        ),
    )

    assert module.RESEARCH_STRATEGY_CROSS_DOMAIN_AUTHORITY_MEMORY_ROUTER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.route_count == d("3.000000")
    assert result.domain_count == d("3.000000")
    assert result.authority_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.average_router_score == d("0.578762")
    assert result.lowest_domain_alignment_score == d("0.400000")
    assert result.lowest_authority_score == d("0.450000")
    assert result.lowest_memory_score == d("0.490000")
    assert result.highest_conflict_score == d("0.700000")
    assert result.highest_memory_age_seconds == d("1728000.000000")
    assert result.status == "block"
    assert result.reason_codes == (
        "domain_alignment_block",
        "authority_score_block",
        "memory_score_block",
        "memory_age_block",
        "conflict_score_block",
        "domain_alignment_watch",
        "authority_score_watch",
        "memory_score_watch",
        "memory_age_watch",
        "conflict_score_watch",
        "cross_domain_authority_memory_router_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.derived_validation_digest)
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.route_ref for row in result.rows) == (
        "route-block",
        "route-watch",
        "route-pass",
    )

    blocked = result.rows[0]
    assert blocked.status == "block"
    assert blocked.memory_age_seconds == d("1728000.000000")
    assert blocked.memory_freshness_score == d("0.000000")
    assert blocked.router_score == d("0.328000")
    assert blocked.reason_codes == (
        "domain_alignment_block",
        "authority_score_block",
        "memory_score_block",
        "memory_age_block",
        "conflict_score_block",
    )

    watched = result.rows[1]
    assert watched.status == "watch"
    assert watched.memory_age_seconds == d("864000.000000")
    assert watched.memory_freshness_score == d("0.285714")
    assert watched.router_score == d("0.561143")
    assert watched.reason_codes == (
        "domain_alignment_watch",
        "authority_score_watch",
        "memory_score_watch",
        "memory_age_watch",
        "conflict_score_watch",
    )

    passed = result.rows[2]
    assert passed.status == "pass"
    assert passed.memory_freshness_score == d("0.785714")
    assert passed.router_score == d("0.847143")
    assert passed.reason_codes == ("cross_domain_authority_memory_router_pass",)


def test_threshold_boundaries_are_inclusive_for_pass_and_watch() -> None:
    at_pass = report(
        signal(
            route_ref="route-pass-edge",
            domain_alignment_score=d("0.700000"),
            authority_score=d("0.700000"),
            memory_score=d("0.700000"),
            memory_observed_at=GENERATED_AT - timedelta(seconds=604800),
            conflict_score=d("0.250000"),
        ),
    )
    just_watch = report(
        signal(
            route_ref="route-watch-edge",
            memory_observed_at=GENERATED_AT - timedelta(seconds=604801),
        ),
    )
    just_block = report(
        signal(
            route_ref="route-block-edge",
            memory_observed_at=GENERATED_AT - timedelta(seconds=1209601),
        ),
    )

    assert at_pass.rows[0].status == "pass"
    assert at_pass.rows[0].reason_codes == (
        "cross_domain_authority_memory_router_pass",
    )
    assert just_watch.rows[0].status == "watch"
    assert just_watch.rows[0].reason_codes == ("memory_age_watch",)
    assert just_block.rows[0].status == "block"
    assert just_block.rows[0].reason_codes == ("memory_age_block",)


def test_public_payload_digest_is_deterministic_and_rejects_leaks() -> None:
    module = api()
    first = report(
        signal(route_ref="route-beta", domain_label="rates"),
        signal(route_ref="route-alpha", domain_label="weather"),
    )
    second = report(
        signal(route_ref="route-alpha", domain_label="weather"),
        signal(route_ref="route-beta", domain_label="rates"),
    )

    first_payload = (
        module.research_strategy_cross_domain_authority_memory_router_report_payload(
            first,
        )
    )
    second_payload = (
        module.research_strategy_cross_domain_authority_memory_router_report_payload(
            second,
        )
    )
    encoded = json.dumps(first_payload, sort_keys=True, allow_nan=False)

    assert first == second
    assert first_payload == second_payload
    assert first.public_payload == first_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert (
        module.research_strategy_cross_domain_authority_memory_router_report_digest(
            first,
        )
        == first.derived_validation_digest
    )
    assert module.verify_research_strategy_cross_domain_authority_memory_router_payload(
        first_payload,
    )
    assert first_payload["generated_at"] == "2026-07-09T16:00:00+00:00"
    assert first_payload["route_count"] == "2.000000"
    assert first_payload["rows"][0]["router_score"] == "0.847143"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert_no_raw_numbers(first_payload)
    assert '"0.847143"' in encoded

    forbidden_public_terms = (
        "can" "didate",
        "mar" "ket",
        "sou" "rce",
        "http://",
        "https://",
        "u" "rl",
        "te" "xt",
        "d" "sn",
        "ta" "ble",
        "tok" "en",
    )
    lowered = encoded.lower()
    for term in forbidden_public_terms:
        assert term not in lowered

    tampered = dict(first_payload)
    tampered["route_count"] = "3.000000"
    assert (
        module.verify_research_strategy_cross_domain_authority_memory_router_payload(
            tampered,
        )
        is False
    )


def test_report_and_digest_are_invariant_under_every_input_permutation() -> None:
    module = api()
    items = (
        signal(route_ref="route-pass"),
        signal(
            route_ref="route-watch",
            domain_alignment_score=d("0.600000"),
        ),
        signal(
            route_ref="route-block",
            domain_alignment_score=d("0.400000"),
        ),
    )
    payloads = tuple(
        module.research_strategy_cross_domain_authority_memory_router_report_payload(
            report(*ordered),
        )
        for ordered in permutations(items)
    )

    assert all(payload == payloads[0] for payload in payloads)
    assert tuple(row["route_ref"] for row in payloads[0]["rows"]) == (
        "route-block",
        "route-watch",
        "route-pass",
    )


def test_empty_input_and_digest_validation() -> None:
    module = api()
    result = report()

    assert result.status == "block"
    assert result.route_count == d("0.000000")
    assert result.domain_count == d("0.000000")
    assert result.authority_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.average_router_score == d("0.000000")
    assert result.lowest_domain_alignment_score == d("0.000000")
    assert result.lowest_authority_score == d("0.000000")
    assert result.lowest_memory_score == d("0.000000")
    assert result.highest_conflict_score == d("0.000000")
    assert result.highest_memory_age_seconds == d("0.000000")
    assert result.rows == ()
    assert result.reason_codes == ("cross_domain_authority_memory_router_empty",)
    assert result.public_payload["derived_validation_digest"] == canonical_digest(
        result.public_payload,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)

    payload = dict(result.public_payload)
    payload["derived_validation_digest"] = "0" * 64
    assert (
        module.verify_research_strategy_cross_domain_authority_memory_router_payload(
            payload,
        )
        is False
    )


def test_verifier_rejects_resigned_nonexact_mapping_schemas() -> None:
    module = api()
    original = (
        module.research_strategy_cross_domain_authority_memory_router_report_payload(
            report(signal()),
        )
    )

    assert tuple(original) == REPORT_FIELDS
    assert tuple(original["rows"][0]) == ROW_FIELDS

    invalid_payloads: list[dict[str, Any]] = []

    missing_report_field = deepcopy(original)
    missing_report_field.pop("status")
    resign_payload(missing_report_field)
    invalid_payloads.append(missing_report_field)

    unknown_report_field = deepcopy(original)
    unknown_report_field["safe_extension"] = "pass"
    resign_payload(unknown_report_field)
    invalid_payloads.append(unknown_report_field)

    reordered_report = dict(reversed(tuple(deepcopy(original).items())))
    resign_payload(reordered_report)
    invalid_payloads.append(reordered_report)

    missing_row_field = deepcopy(original)
    missing_row_field["rows"][0].pop("router_score")
    resign_payload(missing_row_field)
    invalid_payloads.append(missing_row_field)

    unknown_row_field = deepcopy(original)
    unknown_row_field["rows"][0]["safe_extension"] = "pass"
    resign_payload(unknown_row_field)
    invalid_payloads.append(unknown_row_field)

    reordered_row = deepcopy(original)
    reordered_row["rows"][0] = dict(
        reversed(tuple(reordered_row["rows"][0].items())),
    )
    resign_payload(reordered_row)
    invalid_payloads.append(reordered_row)

    for invalid_payload in invalid_payloads:
        assert (
            module.verify_research_strategy_cross_domain_authority_memory_router_payload(
                invalid_payload,
            )
            is False
        )


def test_verifier_rejects_resigned_noncanonical_public_values() -> None:
    module = api()
    original = (
        module.research_strategy_cross_domain_authority_memory_router_report_payload(
            report(signal()),
        )
    )
    invalid_payloads: list[dict[str, Any]] = []

    false_report_flag = deepcopy(original)
    false_report_flag["readonly"] = False
    invalid_payloads.append(false_report_flag)

    false_row_flag = deepcopy(original)
    false_row_flag["rows"][0]["paper_only"] = False
    invalid_payloads.append(false_row_flag)

    raw_numeric = deepcopy(original)
    raw_numeric["route_count"] = 1
    invalid_payloads.append(raw_numeric)

    short_decimal = deepcopy(original)
    short_decimal["route_count"] = "1"
    invalid_payloads.append(short_decimal)

    signed_zero = deepcopy(original)
    signed_zero["block_count"] = "-0.000000"
    invalid_payloads.append(signed_zero)

    non_utc_datetime = deepcopy(original)
    non_utc_datetime["generated_at"] = "2026-07-09T16:00:00Z"
    invalid_payloads.append(non_utc_datetime)

    tuple_report_reasons = deepcopy(original)
    tuple_report_reasons["reason_codes"] = tuple(
        tuple_report_reasons["reason_codes"],
    )
    invalid_payloads.append(tuple_report_reasons)

    short_row_decimal = deepcopy(original)
    short_row_decimal["rows"][0]["router_score"] = "0.8"
    invalid_payloads.append(short_row_decimal)

    tuple_row_reasons = deepcopy(original)
    tuple_row_reasons["rows"][0]["reason_codes"] = tuple(
        tuple_row_reasons["rows"][0]["reason_codes"],
    )
    invalid_payloads.append(tuple_row_reasons)

    for invalid_payload in invalid_payloads:
        resign_payload(invalid_payload)
        assert (
            module.verify_research_strategy_cross_domain_authority_memory_router_payload(
                invalid_payload,
            )
            is False
        )


def test_verifier_rejects_resigned_derived_field_tampering() -> None:
    module = api()
    original = (
        module.research_strategy_cross_domain_authority_memory_router_report_payload(
            report(signal()),
        )
    )
    mutations = (
        ("status", "watch"),
        ("route_count", "2.000000"),
        ("domain_count", "2.000000"),
        ("authority_count", "2.000000"),
        ("pass_count", "0.000000"),
        ("watch_count", "1.000000"),
        ("average_router_score", "0.000000"),
        ("lowest_domain_alignment_score", "0.000000"),
        ("lowest_authority_score", "0.000000"),
        ("lowest_memory_score", "0.000000"),
        ("highest_conflict_score", "0.000000"),
        ("highest_memory_age_seconds", "0.000000"),
    )
    invalid_payloads: list[dict[str, Any]] = []

    for field_name, value in mutations:
        tampered = deepcopy(original)
        tampered[field_name] = value
        invalid_payloads.append(tampered)

    tampered_report_reasons = deepcopy(original)
    tampered_report_reasons["reason_codes"] = [
        "domain_alignment_watch",
    ]
    invalid_payloads.append(tampered_report_reasons)

    tampered_freshness = deepcopy(original)
    tampered_freshness["rows"][0]["memory_freshness_score"] = "0.000000"
    invalid_payloads.append(tampered_freshness)

    tampered_router_score = deepcopy(original)
    tampered_router_score["rows"][0]["router_score"] = "0.000000"
    invalid_payloads.append(tampered_router_score)

    tampered_row_status = deepcopy(original)
    tampered_row_status["rows"][0]["status"] = "watch"
    invalid_payloads.append(tampered_row_status)

    for invalid_payload in invalid_payloads:
        resign_payload(invalid_payload)
        assert (
            module.verify_research_strategy_cross_domain_authority_memory_router_payload(
                invalid_payload,
            )
            is False
        )


def test_verifier_rejects_coordinated_resigned_memory_age_forgery() -> None:
    module = api()
    forged = (
        module.research_strategy_cross_domain_authority_memory_router_report_payload(
            report(signal()),
        )
    )
    forged["rows"][0]["memory_age_seconds"] = "864000.000000"
    forged["rows"][0]["memory_freshness_score"] = "0.285714"
    forged["rows"][0]["router_score"] = "0.747143"
    forged["average_router_score"] = "0.747143"
    forged["highest_memory_age_seconds"] = "864000.000000"
    resign_payload(forged)

    assert (
        module.verify_research_strategy_cross_domain_authority_memory_router_payload(
            forged,
        )
        is False
    )


def test_validation_rejects_bad_inputs_and_private_material() -> None:
    module = api()
    private = (
        "postgres://raw-" + "can" + "didate.raw-" + "mar" + "ket.invalid/"
        "?raw_" + "sou" + "rce_" + "url" + "=https://raw.invalid"
        "&raw_" + "te" + "xt" + "=raw-" + "dsn" + "-table-token"
    )

    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at="2026-07-09T16:00:00Z")
    with pytest.raises(ValueError, match="items"):
        module.build_research_strategy_cross_domain_authority_memory_router_report(
            object(),
            generated_at=GENERATED_AT,
            config=config(),
        )
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="domain_alignment_score"):
        signal(domain_alignment_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_score"):
        signal(authority_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_observed_at"):
        signal(memory_observed_at=datetime(2026, 7, 9, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="future"):
        report(signal(memory_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate"):
        report(signal(route_ref="route-one"), signal(route_ref="route-one"))
    with pytest.raises(ValueError, match="route_ref"):
        signal(route_ref="route?unsafe")
    with pytest.raises(ValueError, match="authority_label"):
        signal(authority_label="raw-" + "tok" + "en")
    with pytest.raises(ValueError, match="memory_label"):
        signal(memory_label=private)

    assert private not in repr(signal(memory_label="safe-memory"))


def test_public_dataclasses_are_frozen_and_types_are_strict() -> None:
    module = api()

    class DecimalSubclass(Decimal):
        pass

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_AUTHORITY_MEMORY_ROUTER_CONFIG_VERSION",
        "RESEARCH_STRATEGY_CROSS_DOMAIN_AUTHORITY_MEMORY_ROUTER_STATUSES",
        "ResearchStrategyCrossDomainAuthorityMemoryRouterConfig",
        "ResearchStrategyCrossDomainAuthorityMemoryRouterReport",
        "ResearchStrategyCrossDomainAuthorityMemoryRouterRow",
        "ResearchStrategyCrossDomainAuthorityMemoryRouterSignal",
        "build_research_strategy_cross_domain_authority_memory_router_report",
        "research_strategy_cross_domain_authority_memory_router_report_digest",
        "research_strategy_cross_domain_authority_memory_router_report_payload",
        "verify_research_strategy_cross_domain_authority_memory_router_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    config_value = config()
    signal_value = signal(route_ref="route-frozen")
    result = report(signal_value, cfg=config_value)
    for value in (config_value, signal_value, result.rows[0], result):
        assert type(value) in {
            module.ResearchStrategyCrossDomainAuthorityMemoryRouterConfig,
            module.ResearchStrategyCrossDomainAuthorityMemoryRouterSignal,
            module.ResearchStrategyCrossDomainAuthorityMemoryRouterRow,
            module.ResearchStrategyCrossDomainAuthorityMemoryRouterReport,
        }
        assert_numeric_fields_are_decimal(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        with pytest.raises(TypeError):
            type("DerivedPublicValue", (type(value),), {})

    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):
        type("Derived", (module.ResearchStrategyCrossDomainAuthorityMemoryRouterRow,), {})
    with pytest.raises(ValueError, match="route_count"):
        replace(result, route_count=DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(result, status="blocked")
    with pytest.raises(ValueError, match="reason_code"):
        replace(result.rows[0], reason_codes=("unknown_reason",))


@pytest.mark.parametrize("value", (d("-0"), d("-0.000000")))
def test_public_decimal_inputs_reject_signed_zero(value: Decimal) -> None:
    summary = report(signal())
    public_values = (config(), signal(), summary.rows[0], summary)

    for public_value in public_values:
        for field in fields(public_value):
            if field.name.endswith(("_count", "_score", "_seconds")):
                with pytest.raises(ValueError, match="signed zero"):
                    replace(public_value, **{field.name: value})


@pytest.mark.parametrize(
    ("overrides", "error_pattern"),
    (
        (
            {
                "min_pass_domain_alignment_score": d("0.5000004"),
                "min_watch_domain_alignment_score": d("0.50000049"),
            },
            "min_watch_domain_alignment_score",
        ),
        (
            {
                "min_pass_authority_score": d("0.5000004"),
                "min_watch_authority_score": d("0.50000049"),
            },
            "min_watch_authority_score",
        ),
        (
            {
                "min_pass_memory_score": d("0.5000004"),
                "min_watch_memory_score": d("0.50000049"),
            },
            "min_watch_memory_score",
        ),
        (
            {
                "max_pass_memory_age_seconds": d("1.00000049"),
                "max_watch_memory_age_seconds": d("1.0000004"),
            },
            "max_watch_memory_age_seconds",
        ),
        (
            {
                "max_pass_conflict_score": d("0.50000049"),
                "max_watch_conflict_score": d("0.5000004"),
            },
            "max_pass_conflict_score",
        ),
    ),
)
def test_config_rejects_raw_threshold_inversions_hidden_by_quantization(
    overrides: dict[str, Decimal],
    error_pattern: str,
) -> None:
    with pytest.raises(ValueError, match=error_pattern):
        config(**overrides)


def test_decimal_arithmetic_is_independent_of_caller_context() -> None:
    module = api()
    item = signal(
        memory_observed_at=(
            GENERATED_AT - timedelta(days=3, microseconds=123456)
        ),
    )
    expected = (
        module.research_strategy_cross_domain_authority_memory_router_report_payload(
            report(item),
        )
    )
    hostile_context = Context(prec=3, rounding=ROUND_DOWN)
    hostile_context.traps[Inexact] = True
    hostile_context.traps[Rounded] = True

    with localcontext(hostile_context):
        actual = (
            module.research_strategy_cross_domain_authority_memory_router_report_payload(
                report(item),
            )
        )

    assert actual == expected


def test_datetimes_normalize_to_canonical_utc_and_large_ages_remain_exact() -> None:
    module = api()
    offset = timezone(timedelta(hours=5, minutes=45))
    offset_generated_at = GENERATED_AT.astimezone(offset)
    offset_observed_at = (GENERATED_AT - timedelta(days=3)).astimezone(offset)
    canonical = report(
        signal(memory_observed_at=offset_observed_at),
        generated_at=offset_generated_at,
    )

    assert canonical.generated_at.tzinfo is UTC
    assert canonical.rows[0].memory_observed_at.tzinfo is UTC
    assert canonical.public_payload["generated_at"] == "2026-07-09T16:00:00+00:00"
    assert canonical.public_payload["rows"][0]["memory_observed_at"] == (
        "2026-07-06T16:00:00+00:00"
    )
    assert module.verify_research_strategy_cross_domain_authority_memory_router_payload(
        canonical.public_payload,
    )

    far_future = datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=UTC)
    far_past = datetime(1, 1, 1, 0, 0, 0, 1, tzinfo=UTC)
    long_range = report(
        signal(memory_observed_at=far_past),
        generated_at=far_future,
    )
    assert long_range.rows[0].memory_age_seconds == d("315537897599.999998")


@pytest.mark.parametrize(
    "invalid_decimal",
    (
        "NaN",
        "Infinity",
        "-Infinity",
        "1E+999999",
        "+0.000000",
        "00.000000",
        "0.0000000",
        "-1.000000",
    ),
)
def test_verifier_rejects_hostile_decimal_spellings(
    invalid_decimal: str,
) -> None:
    module = api()
    payload = dict(report().public_payload)
    payload["average_router_score"] = invalid_decimal
    resign_payload(payload)

    assert (
        module.verify_research_strategy_cross_domain_authority_memory_router_payload(
            payload,
        )
        is False
    )


def test_public_apis_reject_object_setattr_tampering() -> None:
    module = api()

    tampered_signal = signal()
    object.__setattr__(tampered_signal, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        report(tampered_signal)

    tampered_config = config()
    object.__setattr__(
        tampered_config,
        "min_pass_domain_alignment_score",
        d("0.100000"),
    )
    with pytest.raises(ValueError, match="min_watch_domain_alignment_score"):
        report(signal(), cfg=tampered_config)

    row_tampered_report = report(signal())
    object.__setattr__(
        row_tampered_report.rows[0],
        "router_score",
        d("0.000000"),
    )
    with pytest.raises(ValueError, match="router_score|derived_validation_digest"):
        module.research_strategy_cross_domain_authority_memory_router_report_payload(
            row_tampered_report,
        )
    with pytest.raises(ValueError, match="router_score|derived_validation_digest"):
        module.research_strategy_cross_domain_authority_memory_router_report_digest(
            row_tampered_report,
        )

    outer_tampered_report = report(signal())
    object.__setattr__(outer_tampered_report, "status", "watch")
    with pytest.raises(ValueError, match="status|derived_validation_digest"):
        _ = outer_tampered_report.public_payload


def test_report_rejects_resigned_nested_row_with_noncanonical_utc() -> None:
    module = api()
    summary = report(signal())
    offset = timezone(timedelta(hours=3))
    object.__setattr__(
        summary.rows[0],
        "memory_observed_at",
        summary.rows[0].memory_observed_at.astimezone(offset),
    )
    forged_digest = module._digest_mapping(
        module._public_payload_without_digest(summary),
    )

    with pytest.raises(ValueError, match="canonical|memory_observed_at"):
        replace(summary, derived_validation_digest=forged_digest)


def test_report_count_fields_reject_fractional_values_hidden_by_quantization() -> None:
    summary = report(signal())

    for field_name in (
        "route_count",
        "domain_count",
        "authority_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        fractional_value = getattr(summary, field_name) + d("0.0000004")
        with pytest.raises(ValueError, match="integral"):
            replace(summary, **{field_name: fractional_value})


def test_row_reason_codes_reject_empty_duplicates_and_pass_mixtures() -> None:
    module = api()
    row = report(signal()).rows[0]
    invalid_values = (
        ("watch", ()),
        ("pass", (module.PASS_REASON, module.PASS_REASON)),
        (
            "watch",
            (module.PASS_REASON, module.DOMAIN_WATCH_REASON),
        ),
    )

    for status, reason_codes in invalid_values:
        with pytest.raises(ValueError, match="reason_codes"):
            replace(row, status=status, reason_codes=reason_codes)


@pytest.mark.parametrize(
    "unsafe_term",
    (
        "auth",
        "wallet",
        "live",
        "order",
        "trade",
        "recommend",
        "sizing",
        "persist",
        "database",
        "network",
        "browser",
        "subprocess",
    ),
)
def test_public_identifiers_reject_phase_one_execution_surface_tokens(
    unsafe_term: str,
) -> None:
    with pytest.raises(ValueError, match="private material"):
        signal(route_ref=f"route-{unsafe_term}-surface")


def test_public_identifier_token_guard_does_not_overblock_harmless_words() -> None:
    assert signal(route_ref="route-delivery-research").route_ref == (
        "route-delivery-research"
    )


def test_module_static_forbidden_surface_terms_are_absent() -> None:
    source = MODULE_PATH.read_text()
    lowered = source.lower()

    for forbidden in (
        "d" "b",
        "data" "base",
        "net" "work",
        "wal" "let",
        "or" "der",
        "li" "ve",
        "trad" "ing",
        "siz" "ing",
        "reco" "mmendation",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", 1)[0]
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
        elif isinstance(node, ast.Constant) and type(node.value) is float:
            float_constants.append(node.value)

    assert imported_roots.isdisjoint(
        {
            "ccxt",
            "http",
            "httpx",
            "os",
            "pathlib",
            "playwright",
            "psycopg",
            "requests",
            "selenium",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "subprocess",
            "supabase",
            "urllib",
            "web3",
        },
    )
    assert called_names.isdisjoint(
        {
            "Popen",
            "buy",
            "commit",
            "connect",
            "create_connection",
            "cursor",
            "execute",
            "getenv",
            "open",
            "read_text",
            "request",
            "run",
            "sell",
            "send",
            "system",
            "trade",
            "urlopen",
            "write_text",
        },
    )
    assert not float_constants
