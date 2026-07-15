from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, Inexact, ROUND_UP, Rounded, localcontext
from hashlib import sha256
import importlib
import json
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_authority_contradiction_recheck_sla_report"
)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "contradiction_watch_severity": d("0.350000"),
        "contradiction_block_severity": d("0.700000"),
        "authority_tier_gap_watch": d("1.000000"),
        "authority_tier_gap_block": d("2.000000"),
        "last_checked_watch_age_seconds": d("3600.000000"),
        "last_checked_block_age_seconds": d("14400.000000"),
        "resolution_watch_seconds_remaining": d("86400.000000"),
        "resolution_block_seconds_remaining": d("21600.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityContradictionRecheckSlaConfig(**values)


def item(
    contradiction_bucket: str,
    *,
    contradiction_severity: str = "0.100000",
    authority_tier_gap: str = "0.000000",
    last_checked_age_seconds: str = "600.000000",
    resolution_seconds_remaining: str = "200000.000000",
):
    module = api()
    return module.ResearchSourceAuthorityContradictionRecheckSlaInput(
        contradiction_bucket=contradiction_bucket,
        contradiction_severity=d(contradiction_severity),
        authority_tier_gap=d(authority_tier_gap),
        last_checked_age_seconds=d(last_checked_age_seconds),
        resolution_seconds_remaining=d(resolution_seconds_remaining),
    )


def build_report(*items, cfg=None):
    module = api()
    return module.build_research_source_authority_contradiction_recheck_sla_report(
        list(items),
        config=cfg or config(),
        generated_at=datetime(2026, 7, 9, 12, 0, tzinfo=UTC),
    )


def thaw(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: thaw(item_value) for key, item_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [thaw(item_value) for item_value in value]
    return value


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = thaw(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def resign(payload: dict[str, Any]) -> dict[str, Any]:
    payload["derived_validation_digest"] = canonical_digest(payload)
    return payload


def assert_no_numeric_primitives(value: object) -> None:
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_numeric_primitives(item_value)
        return
    if isinstance(value, (list, tuple)):
        for item_value in value:
            assert_no_numeric_primitives(item_value)
        return
    assert type(value) not in (int, float)


def test_reducer_derives_routine_accelerated_and_immediate_sla_buckets() -> None:
    module = api()
    report = build_report(
        item("routine"),
        item(
            "accelerated",
            contradiction_severity="0.400000",
            authority_tier_gap="1.000000",
            last_checked_age_seconds="4000.000000",
            resolution_seconds_remaining="50000.000000",
        ),
        item(
            "immediate",
            contradiction_severity="0.800000",
            authority_tier_gap="2.000000",
            last_checked_age_seconds="20000.000000",
            resolution_seconds_remaining="10000.000000",
        ),
    )

    assert report.status == "block"
    assert report.contradiction_count == d("3.000000")
    assert report.routine_recheck_count == d("1.000000")
    assert report.accelerated_recheck_count == d("1.000000")
    assert report.immediate_recheck_count == d("1.000000")
    assert report.severe_contradiction_count == d("2.000000")
    assert report.material_authority_tier_gap_count == d("2.000000")
    assert report.stale_last_checked_count == d("2.000000")
    assert report.near_resolution_count == d("2.000000")
    assert report.nearest_resolution_seconds_remaining == d("10000.000000")
    assert [row.contradiction_bucket for row in report.rows] == [
        "immediate",
        "accelerated",
        "routine",
    ]
    assert [row.recheck_sla_bucket for row in report.rows] == [
        "immediate",
        "accelerated",
        "routine",
    ]
    assert [row.status for row in report.rows] == ["block", "watch", "pass"]
    assert report.rows[0].reason_codes == (
        module.CONTRADICTION_SEVERITY_BLOCK_REASON,
        module.AUTHORITY_TIER_GAP_BLOCK_REASON,
        module.LAST_CHECKED_AGE_BLOCK_REASON,
        module.RESOLUTION_PROXIMITY_BLOCK_REASON,
    )
    assert report.rows[2].reason_codes == (module.CLEAR_REASON,)


def test_threshold_boundaries_are_deterministic() -> None:
    module = api()
    report = build_report(
        item(
            "watch-boundary",
            contradiction_severity="0.350000",
            authority_tier_gap="1.000000",
            last_checked_age_seconds="3600.000000",
            resolution_seconds_remaining="86400.000000",
        ),
        item(
            "block-boundary",
            contradiction_severity="0.700000",
            authority_tier_gap="2.000000",
            last_checked_age_seconds="14400.000000",
            resolution_seconds_remaining="21600.000000",
        ),
    )

    watch_row = next(row for row in report.rows if row.contradiction_bucket == "watch-boundary")
    block_row = next(row for row in report.rows if row.contradiction_bucket == "block-boundary")

    assert watch_row.status == "watch"
    assert watch_row.recheck_sla_bucket == "accelerated"
    assert watch_row.reason_codes == (
        module.CONTRADICTION_SEVERITY_WATCH_REASON,
        module.AUTHORITY_TIER_GAP_WATCH_REASON,
        module.LAST_CHECKED_AGE_WATCH_REASON,
        module.RESOLUTION_PROXIMITY_WATCH_REASON,
    )
    assert block_row.status == "block"
    assert block_row.recheck_sla_bucket == "immediate"


def test_empty_report_is_canonical_and_explicit() -> None:
    module = api()
    report = build_report()

    assert report.status == "pass"
    assert report.reason_codes == (module.EMPTY_REASON,)
    assert report.contradiction_count == d("0.000000")
    assert report.highest_contradiction_severity == d("0.000000")
    assert report.nearest_resolution_seconds_remaining == d("0.000000")
    assert report.rows == ()


def test_payload_is_canonical_immutable_and_sha256_validated() -> None:
    module = api()
    report = build_report(item("canonical"))
    payload = module.research_source_authority_contradiction_recheck_sla_report_payload(
        report,
    )

    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["contradiction_count"] == "1.000000"
    assert payload["contradiction_watch_severity"] == "0.350000"
    assert payload["rows"][0]["contradiction_severity"] == "0.100000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    json.dumps(payload, sort_keys=True, allow_nan=False)
    assert_no_numeric_primitives(payload)
    assert module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
        payload,
    )

    with pytest.raises(TypeError, match="immutable"):
        payload["status"] = "watch"
    with pytest.raises(TypeError, match="immutable"):
        payload["rows"].append({})
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_public_validator_rejects_forged_resigned_report_derivations() -> None:
    module = api()
    report = build_report(
        item(
            "blocking",
            contradiction_severity="0.900000",
            authority_tier_gap="3.000000",
            last_checked_age_seconds="30000.000000",
            resolution_seconds_remaining="1000.000000",
        ),
    )
    forged = thaw(
        module.research_source_authority_contradiction_recheck_sla_report_payload(
            report,
        ),
    )
    forged["status"] = "pass"
    forged["reason_codes"] = [module.CLEAR_REASON]
    resign(forged)

    with pytest.raises(ValueError, match="status must match rows|reason_codes must match rows"):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            forged,
        )


def test_public_validator_rejects_forged_resigned_row_reason_logic() -> None:
    module = api()
    report = build_report(
        item(
            "blocking",
            contradiction_severity="0.900000",
            authority_tier_gap="3.000000",
            last_checked_age_seconds="30000.000000",
            resolution_seconds_remaining="1000.000000",
        ),
    )
    forged = thaw(
        module.research_source_authority_contradiction_recheck_sla_report_payload(
            report,
        ),
    )
    forged["rows"][0]["status"] = "pass"
    forged["rows"][0]["recheck_sla_bucket"] = "routine"
    forged["rows"][0]["reason_codes"] = [module.CLEAR_REASON]
    forged["routine_recheck_count"] = "1.000000"
    forged["immediate_recheck_count"] = "0.000000"
    forged["status"] = "pass"
    forged["reason_codes"] = [module.CLEAR_REASON]
    resign(forged)

    with pytest.raises(ValueError, match="reason_codes must match row inputs"):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            forged,
        )


def test_public_validator_rejects_forged_resigned_sla_bucket_only() -> None:
    module = api()
    report = build_report(
        item("watch", contradiction_severity="0.500000"),
    )
    forged = thaw(
        module.research_source_authority_contradiction_recheck_sla_report_payload(
            report,
        ),
    )
    forged["rows"][0]["recheck_sla_bucket"] = "routine"
    resign(forged)

    with pytest.raises(ValueError, match="recheck_sla_bucket must match reason_codes"):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            forged,
        )


def test_public_validator_enforces_exact_schema_decimal_strings_and_flags() -> None:
    module = api()
    report = build_report(item("schema"))
    base = thaw(
        module.research_source_authority_contradiction_recheck_sla_report_payload(
            report,
        ),
    )

    unexpected = thaw(base)
    unexpected["recommendation"] = "hold"
    resign(unexpected)
    with pytest.raises(ValueError, match="public payload schema|unsafe key"):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            unexpected,
        )

    noncanonical = thaw(base)
    noncanonical["contradiction_count"] = "1"
    resign(noncanonical)
    with pytest.raises(ValueError, match="contradiction_count"):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            noncanonical,
        )

    numeric_primitive = thaw(base)
    numeric_primitive["rows"][0]["authority_tier_gap"] = 0
    resign(numeric_primitive)
    with pytest.raises(ValueError, match="authority_tier_gap"):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            numeric_primitive,
        )

    downgraded = thaw(base)
    downgraded["readonly"] = False
    resign(downgraded)
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            downgraded,
        )


def test_inputs_and_config_are_decimal_only_and_validate_threshold_order() -> None:
    module = api()

    with pytest.raises(ValueError, match="contradiction_severity must be a Decimal"):
        module.ResearchSourceAuthorityContradictionRecheckSlaInput(
            contradiction_bucket="bad",
            contradiction_severity=0.5,
            authority_tier_gap=d("1.000000"),
            last_checked_age_seconds=d("1.000000"),
            resolution_seconds_remaining=d("1.000000"),
        )

    with pytest.raises(ValueError, match="authority_tier_gap must be a whole Decimal"):
        item("fractional-gap", authority_tier_gap="1.500000")

    with pytest.raises(ValueError, match="last_checked_age_seconds"):
        item("negative-age", last_checked_age_seconds="-1.000000")

    with pytest.raises(ValueError, match="contradiction_block_severity"):
        config(contradiction_block_severity=d("0.300000"))

    with pytest.raises(ValueError, match="resolution_block_seconds_remaining"):
        config(resolution_block_seconds_remaining=d("90000.000000"))

    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchSourceAuthorityContradictionRecheckSlaInput(
            contradiction_bucket="unsafe-flags",
            contradiction_severity=d("0.100000"),
            authority_tier_gap=d("0.000000"),
            last_checked_age_seconds=d("0.000000"),
            resolution_seconds_remaining=d("1.000000"),
            paper_only=False,
        )


def test_builder_rejects_duplicates_naive_time_and_bypassed_config() -> None:
    cfg = config()
    object.__setattr__(
        cfg,
        "last_checked_watch_age_seconds",
        d("20000.000000"),
    )

    with pytest.raises(ValueError, match="last_checked_block_age_seconds"):
        build_report(item("config"), cfg=cfg)

    with pytest.raises(ValueError, match="unique by contradiction_bucket"):
        build_report(item("duplicate"), item("duplicate"))

    module = api()
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_authority_contradiction_recheck_sla_report(
            [item("naive")],
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )


@pytest.mark.parametrize("target", ("config", "input"))
def test_builder_rejects_valid_post_initialization_tampering(target: str) -> None:
    if target == "config":
        cfg = config()
        object.__setattr__(
            cfg,
            "contradiction_watch_severity",
            d("0.400000"),
        )
        with pytest.raises(ValueError, match="config was modified after initialization"):
            build_report(item("tampered-config"), cfg=cfg)
        return

    input_value = item("original-input")
    object.__setattr__(
        input_value,
        "contradiction_bucket",
        "tampered-input",
    )
    with pytest.raises(ValueError, match="input was modified after initialization"):
        build_report(input_value)


def test_public_dataclasses_are_frozen_and_do_not_support_subclassing() -> None:
    module = api()
    input_value = item("frozen")
    report = build_report(input_value)

    with pytest.raises(FrozenInstanceError):
        input_value.contradiction_severity = d("0.200000")
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"

    with pytest.raises(TypeError, match="does not support subclassing"):

        class InvalidSubclass(
            module.ResearchSourceAuthorityContradictionRecheckSlaReport,
        ):
            pass


def test_public_report_apis_revalidate_bypassed_objects() -> None:
    module = api()
    report = build_report(
        item(
            "blocking",
            contradiction_severity="0.900000",
            authority_tier_gap="3.000000",
            last_checked_age_seconds="30000.000000",
            resolution_seconds_remaining="1000.000000",
        ),
    )
    object.__setattr__(report.rows[0], "status", "pass")
    object.__setattr__(report.rows[0], "recheck_sla_bucket", "routine")
    object.__setattr__(report.rows[0], "reason_codes", (module.CLEAR_REASON,))

    for public_api in (
        module.research_source_authority_contradiction_recheck_sla_report_digest,
        module.validate_research_source_authority_contradiction_recheck_sla_report_digest,
        module.research_source_authority_contradiction_recheck_sla_report_payload,
    ):
        with pytest.raises(ValueError, match="reason_codes must match row inputs"):
            public_api(report)


@pytest.mark.parametrize(
    "public_api_name",
    (
        "research_source_authority_contradiction_recheck_sla_report_digest",
        "validate_research_source_authority_contradiction_recheck_sla_report_digest",
        "research_source_authority_contradiction_recheck_sla_report_payload",
    ),
)
def test_public_report_apis_reject_validly_resigned_object_tampering(
    public_api_name: str,
) -> None:
    module = api()
    report = build_report(item("original-bucket"))
    resigned = thaw(
        module.research_source_authority_contradiction_recheck_sla_report_payload(
            report,
        ),
    )
    resigned["rows"][0]["contradiction_bucket"] = "tampered-bucket"
    resign(resigned)

    object.__setattr__(
        report.rows[0],
        "contradiction_bucket",
        "tampered-bucket",
    )
    object.__setattr__(
        report,
        "derived_validation_digest",
        resigned["derived_validation_digest"],
    )

    with pytest.raises(ValueError, match="modified after initialization"):
        getattr(module, public_api_name)(report)


@pytest.mark.parametrize("field_name", ("paper_only", "report_only", "readonly"))
def test_report_revalidates_bypassed_nested_phase_one_flags(field_name: str) -> None:
    module = api()
    report = build_report(item("nested-flag"))
    object.__setattr__(report.rows[0], field_name, False)

    with pytest.raises(ValueError, match=rf"row {field_name} must be exactly True"):
        replace(report, derived_validation_digest="")


def test_public_dataclass_instances_have_no_dynamic_attribute_surface() -> None:
    module = api()
    input_value = item("exact-instance")
    report = build_report(input_value)
    values = (
        config(),
        input_value,
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )

    for value in values:
        with pytest.raises(AttributeError, match="has no attribute"):
            object.__setattr__(value, "unexpected", "forbidden")


def test_raw_decimal_constraints_are_checked_before_quantization() -> None:
    with pytest.raises(ValueError, match="contradiction_severity must be between 0 and 1"):
        item("ratio-overflow", contradiction_severity="1.0000004")

    with pytest.raises(ValueError, match="last_checked_age_seconds must be nonnegative"):
        item("negative-age", last_checked_age_seconds="-0.0000004")

    with pytest.raises(ValueError, match="authority_tier_gap must be a whole Decimal"):
        item("fractional-gap", authority_tier_gap="1.0000004")


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("last_checked_age_seconds", "3599.9999996"),
        ("last_checked_age_seconds", "14399.9999996"),
        ("resolution_seconds_remaining", "21600.0000004"),
        ("resolution_seconds_remaining", "86400.0000004"),
    ),
)
def test_subquantum_time_values_cannot_leak_across_sla_boundaries(
    field_name: str,
    value: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        item("subquantum-time", **{field_name: value})


@pytest.mark.parametrize(
    ("field_name", "overrides"),
    (
        ("contradiction_severity", {"contradiction_severity": "-0"}),
        ("authority_tier_gap", {"authority_tier_gap": "-0"}),
        ("last_checked_age_seconds", {"last_checked_age_seconds": "-0"}),
        ("resolution_seconds_remaining", {"resolution_seconds_remaining": "-0"}),
    ),
)
def test_signed_zero_is_rejected_for_public_decimals(
    field_name: str,
    overrides: dict[str, str],
) -> None:
    with pytest.raises(ValueError, match=rf"{field_name} must not be negative zero"):
        item("signed-zero", **overrides)


@pytest.mark.parametrize("value", ("NaN", "sNaN", "Infinity", "-Infinity"))
def test_nonfinite_decimals_are_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="contradiction_severity must be finite"):
        item("nonfinite", contradiction_severity=value)


def test_decimal_operations_use_a_fixed_local_context() -> None:
    inputs = (item("source-b"), item("source-a"))
    hostile_context = Context(prec=1, rounding=ROUND_UP)
    hostile_context.traps[Inexact] = True
    hostile_context.traps[Rounded] = True

    with localcontext(hostile_context):
        report = build_report(*inputs)

    assert report.contradiction_count == d("2.000000")
    assert tuple(row.contradiction_bucket for row in report.rows) == (
        "source-a",
        "source-b",
    )


def test_all_public_dataclasses_are_frozen_and_non_subclassable() -> None:
    module = api()
    contract_classes = (
        module.ResearchSourceAuthorityContradictionRecheckSlaConfig,
        module.ResearchSourceAuthorityContradictionRecheckSlaInput,
        module.ResearchSourceAuthorityContradictionRecheckSlaRow,
        module.ResearchSourceAuthorityContradictionRecheckSlaReasonCodeCount,
        module.ResearchSourceAuthorityContradictionRecheckSlaReport,
    )

    for contract_class in contract_classes:
        assert is_dataclass(contract_class)
        assert contract_class.__dataclass_params__.frozen is True
        assert {
            field.name: field.default
            for field in fields(contract_class)
            if field.name in {"paper_only", "report_only", "readonly"}
        } == {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Invalid{contract_class.__name__}", (contract_class,), {})


def test_public_validator_requires_exact_canonical_object_schema() -> None:
    module = api()
    base = thaw(
        module.research_source_authority_contradiction_recheck_sla_report_payload(
            build_report(item("schema-sequence")),
        ),
    )

    class DictSubclass(dict[str, Any]):
        pass

    with pytest.raises(ValueError, match="public payload schema must match exactly"):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            DictSubclass(base),
        )

    reordered = {
        "config_version": base["config_version"],
        **{key: value for key, value in base.items() if key != "config_version"},
    }
    resign(reordered)
    with pytest.raises(ValueError, match="public payload schema must match exactly"):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            reordered,
        )

    reordered_row = thaw(base)
    row = reordered_row["rows"][0]
    reordered_row["rows"][0] = {
        "status": row["status"],
        **{key: value for key, value in row.items() if key != "status"},
    }
    resign(reordered_row)
    with pytest.raises(ValueError, match="row public payload schema must match exactly"):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            reordered_row,
        )


def test_public_validator_requires_canonical_json_array_types() -> None:
    module = api()
    forged = thaw(
        module.research_source_authority_contradiction_recheck_sla_report_payload(
            build_report(item("array-schema")),
        ),
    )
    forged["rows"] = tuple(forged["rows"])
    resign(forged)

    with pytest.raises(ValueError, match="rows must be a JSON array"):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            forged,
        )


def test_digest_requires_lowercase_ascii_sha256_hex() -> None:
    module = api()
    forged = thaw(
        module.research_source_authority_contradiction_recheck_sla_report_payload(
            build_report(item("digest-schema")),
        ),
    )
    forged["derived_validation_digest"] = "٠" * 64

    with pytest.raises(ValueError, match="SHA-256 hex string"):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            forged,
        )


def test_resigned_public_payload_rejects_signed_zero() -> None:
    module = api()
    forged = thaw(
        module.research_source_authority_contradiction_recheck_sla_report_payload(
            build_report(item("signed-zero-payload")),
        ),
    )
    forged["contradiction_count"] = "-0.000000"
    resign(forged)

    with pytest.raises(ValueError, match="contradiction_count must not be negative zero"):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            forged,
        )


def test_private_source_bucket_is_deterministically_redacted() -> None:
    module = api()
    private_bucket = "https://private.example/source?api_key=secret"
    expected = f"redacted_{sha256(private_bucket.encode('utf-8')).hexdigest()[:16]}"

    report = build_report(item(private_bucket))
    payload = module.research_source_authority_contradiction_recheck_sla_report_payload(
        report,
    )
    rendered = json.dumps(payload, sort_keys=True)

    assert report.rows[0].contradiction_bucket == expected
    assert payload["rows"][0]["contradiction_bucket"] == expected
    assert private_bucket not in rendered
    assert "api_key" not in rendered
    assert "secret" not in rendered


def test_row_sorting_and_digest_are_stable_across_input_order() -> None:
    module = api()
    inputs = (
        item("source-z", contradiction_severity="0.500000"),
        item("source-a", contradiction_severity="0.900000"),
        item("source-m"),
    )

    first = build_report(*inputs)
    second = build_report(*reversed(inputs))

    assert first.rows == second.rows
    assert first.derived_validation_digest == second.derived_validation_digest
    assert (
        module.research_source_authority_contradiction_recheck_sla_report_payload(
            first,
        )
        == module.research_source_authority_contradiction_recheck_sla_report_payload(
            second,
        )
    )


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("contradiction_count", "3.000000"),
        ("routine_recheck_count", "0.000000"),
        ("accelerated_recheck_count", "1.000000"),
        ("immediate_recheck_count", "0.000000"),
        ("severe_contradiction_count", "0.000000"),
        ("material_authority_tier_gap_count", "0.000000"),
        ("stale_last_checked_count", "0.000000"),
        ("near_resolution_count", "0.000000"),
        ("highest_contradiction_severity", "0.800000"),
        ("highest_authority_tier_gap", "2.000000"),
        ("oldest_last_checked_age_seconds", "20000.000000"),
        ("nearest_resolution_seconds_remaining", "2000.000000"),
        ("status", "pass"),
        ("reason_codes", ["source_authority_contradiction_recheck_sla_clear"]),
    ),
)
def test_resigned_payload_recomputes_every_report_derivation(
    field_name: str,
    forged_value: object,
) -> None:
    module = api()
    report = build_report(
        item("routine"),
        item(
            "blocking",
            contradiction_severity="0.900000",
            authority_tier_gap="3.000000",
            last_checked_age_seconds="30000.000000",
            resolution_seconds_remaining="1000.000000",
        ),
    )
    forged = thaw(
        module.research_source_authority_contradiction_recheck_sla_report_payload(
            report,
        ),
    )
    forged[field_name] = forged_value
    resign(forged)

    with pytest.raises(ValueError, match=field_name):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            forged,
        )


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    (
        ("row_status", "status must match reason_codes"),
        ("row_sla", "recheck_sla_bucket must match reason_codes"),
        ("row_reasons", "reason_codes must match row inputs"),
        ("reason_count", "reason_code_counts must match rows"),
        ("row_order", "rows must use deterministic sorting"),
    ),
)
def test_resigned_payload_recomputes_nested_derivations_and_sorting(
    mutation: str,
    expected_error: str,
) -> None:
    module = api()
    report = build_report(
        item("routine"),
        item("watch", contradiction_severity="0.500000"),
        item("block", contradiction_severity="0.900000"),
    )
    forged = thaw(
        module.research_source_authority_contradiction_recheck_sla_report_payload(
            report,
        ),
    )

    if mutation == "row_status":
        forged["rows"][0]["status"] = "pass"
    elif mutation == "row_sla":
        forged["rows"][0]["recheck_sla_bucket"] = "routine"
    elif mutation == "row_reasons":
        forged["rows"][0]["status"] = "pass"
        forged["rows"][0]["recheck_sla_bucket"] = "routine"
        forged["rows"][0]["reason_codes"] = [module.CLEAR_REASON]
    elif mutation == "reason_count":
        forged["reason_code_counts"][0]["count"] = "2.000000"
    else:
        forged["rows"] = list(reversed(forged["rows"]))
    resign(forged)

    with pytest.raises(ValueError, match=expected_error):
        module.validate_research_source_authority_contradiction_recheck_sla_public_payload(
            forged,
        )
