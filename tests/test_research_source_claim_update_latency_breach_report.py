from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_claim_update_latency_breach_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def ago(seconds: int) -> datetime:
    return GENERATED_AT - timedelta(seconds=seconds)


def ahead(seconds: int) -> datetime:
    return GENERATED_AT + timedelta(seconds=seconds)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-source-claim-update-latency-breach-v0",
        "watch_latency_ratio": d("1.500000"),
        "block_latency_ratio": d("3.000000"),
        "watch_source_authority_score": d("0.500000"),
        "block_source_authority_score": d("0.250000"),
        "watch_contradiction_pressure": d("0.400000"),
        "block_contradiction_pressure": d("0.750000"),
        "watch_corroboration_depth": d("2"),
        "block_corroboration_depth": d("0"),
        "watch_extraction_confidence": d("0.700000"),
        "block_extraction_confidence": d("0.400000"),
        "watch_missing_field_count": d("1"),
        "block_missing_field_count": d("3"),
        "watch_deadline_seconds": d("7200.000000"),
        "block_deadline_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceClaimUpdateLatencyBreachConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "claim_bucket": "official-policy",
        "expected_update_cadence_seconds": d("3600.000000"),
        "latest_verified_at": ago(1800),
        "source_authority_score": d("0.950000"),
        "contradiction_pressure": d("0.050000"),
        "corroboration_depth": d("4"),
        "extraction_confidence": d("0.920000"),
        "missing_field_count": d("0"),
        "deadline_at": ahead(86400),
    }
    values.update(overrides)
    return module.ResearchSourceClaimUpdateLatencyObservation(**values)


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_source_claim_update_latency_breach_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float(item)
    else:
        assert type(value) is not float


def canonical_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def mutable_payload(value: object) -> dict[str, object]:
    module = api()
    payload = module.research_source_claim_update_latency_breach_report_payload(value)
    return json.loads(json.dumps(payload))


def resign_payload(payload: dict[str, object]) -> dict[str, object]:
    payload["derived_validation_digest"] = canonical_digest(payload)
    return payload


def test_builds_claim_update_latency_breach_report_from_public_signal_inputs() -> None:
    breach_report = report(
        observation(claim_bucket="official-policy"),
        observation(
            claim_bucket="regional-board",
            latest_verified_at=ago(7200),
            source_authority_score=d("0.450000"),
            contradiction_pressure=d("0.500000"),
            corroboration_depth=d("1"),
            extraction_confidence=d("0.650000"),
            missing_field_count=d("1"),
            deadline_at=ahead(5400),
        ),
        observation(
            claim_bucket="thin-feed",
            latest_verified_at=ago(14400),
            source_authority_score=d("0.200000"),
            contradiction_pressure=d("0.900000"),
            corroboration_depth=d("0"),
            extraction_confidence=d("0.300000"),
            missing_field_count=d("4"),
            deadline_at=ahead(900),
        ),
    )

    assert breach_report.generated_at == GENERATED_AT
    assert breach_report.claim_bucket_count == d("3")
    assert breach_report.pass_count == d("1")
    assert breach_report.watch_count == d("1")
    assert breach_report.block_count == d("1")
    assert breach_report.max_latest_verification_age_seconds == d("14400.000000")
    assert breach_report.max_latency_ratio == d("4.000000")
    assert breach_report.max_contradiction_pressure == d("0.900000")
    assert breach_report.min_extraction_confidence == d("0.300000")
    assert breach_report.min_deadline_seconds == d("900.000000")
    assert breach_report.status == "block"
    assert breach_report.paper_only is True
    assert breach_report.report_only is True
    assert breach_report.readonly is True

    rows = {row.claim_bucket: row for row in breach_report.rows}
    assert tuple(sorted(rows)) == ("official-policy", "regional-board", "thin-feed")

    assert rows["official-policy"].status == "pass"
    assert rows["official-policy"].latency_ratio == d("0.500000")
    assert rows["official-policy"].breach_score == d("0.000000")
    assert rows["official-policy"].reason_codes == ("claim_update_latency_pass",)

    assert rows["regional-board"].status == "watch"
    assert rows["regional-board"].latest_verification_age_seconds == d("7200.000000")
    assert rows["regional-board"].latency_ratio == d("2.000000")
    assert rows["regional-board"].breach_score == d("0.553571")
    assert rows["regional-board"].reason_codes == (
        "update_latency_watch",
        "source_authority_watch",
        "contradiction_pressure_watch",
        "corroboration_depth_watch",
        "extraction_confidence_watch",
        "missing_fields_watch",
        "deadline_proximity_watch",
    )

    assert rows["thin-feed"].status == "block"
    assert rows["thin-feed"].latest_verification_age_seconds == d("14400.000000")
    assert rows["thin-feed"].latency_ratio == d("4.000000")
    assert rows["thin-feed"].breach_score == d("1.000000")
    assert rows["thin-feed"].reason_codes == (
        "update_latency_block",
        "source_authority_block",
        "contradiction_pressure_block",
        "corroboration_depth_block",
        "extraction_confidence_block",
        "missing_fields_block",
        "deadline_proximity_block",
    )


def test_payload_is_public_safe_deterministic_decimal_only_and_digest_validated() -> None:
    module = api()
    observations = (
        observation(claim_bucket="regional-board", latest_verified_at=ago(7200)),
        observation(claim_bucket="official-policy"),
    )

    first = report(
        *observations,
        generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    second = report(*tuple(reversed(observations)))
    first_payload = module.research_source_claim_update_latency_breach_report_payload(first)
    second_payload = module.research_source_claim_update_latency_breach_report_payload(second)
    payload_text = repr(first_payload).lower()

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["claim_bucket_count"] == "2"
    assert first_payload["rows"][0]["claim_bucket"] == "regional-board"
    assert first_payload["rows"][0]["latest_verification_age_seconds"] == "7200.000000"
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert first.derived_validation_digest == second.derived_validation_digest
    assert_no_float(first_payload)

    for unsafe in (
        "candidate",
        "market",
        "slug",
        "question",
        "http",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    ):
        assert unsafe not in payload_text

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_validates_inputs_statuses_flags_and_frozen_outputs() -> None:
    module = api()
    breach_report = report(observation())

    assert module.STATUSES == ("pass", "watch", "block")
    with pytest.raises(FrozenInstanceError):
        breach_report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="latest_verified_at must be a datetime"):
        observation(latest_verified_at=_DatetimeSubclass(2026, 7, 8, 11, tzinfo=UTC))

    with pytest.raises(ValueError, match="latest_verified_at must be timezone-aware"):
        observation(latest_verified_at=datetime(2026, 7, 8, 11, tzinfo=_NoneOffsetTimezone()))

    with pytest.raises(ValueError, match="expected_update_cadence_seconds must be positive"):
        observation(expected_update_cadence_seconds=d("0"))

    with pytest.raises(ValueError, match="source_authority_score must be a Decimal"):
        observation(source_authority_score=1)

    with pytest.raises(ValueError, match="watch_latency_ratio must be finite"):
        config(watch_latency_ratio=Decimal("NaN"))

    with pytest.raises(ValueError, match="config_version"):
        config(config_version="research-source-claim-update-latency-breach-v1")

    for unsafe_bucket in (
        "candidate-alpha",
        "market-alpha",
        "slug-alpha",
        "question-alpha",
        "https-alpha",
        "url-alpha",
        "text-alpha",
        "dsn-alpha",
        "table-alpha",
        "token-alpha",
        "wallet-alpha",
        "order-alpha",
        "trade-alpha",
        "live-alpha",
    ):
        with pytest.raises(ValueError, match="claim_bucket has unsafe public value"):
            observation(claim_bucket=unsafe_bucket)

    with pytest.raises(ValueError, match="config must be readonly"):
        config(readonly=False)

    with pytest.raises(ValueError, match="observation must be paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="status"):
        replace(breach_report.rows[0], status="blocked")

    with pytest.raises(ValueError, match="claim_bucket_count"):
        replace(breach_report, claim_bucket_count=d("2"))


def test_rejects_temporal_inconsistency_empty_inputs_and_missing_verification() -> None:
    with pytest.raises(ValueError, match="observations must not be empty"):
        report()

    with pytest.raises(ValueError, match="latest_verified_at must not be after generated_at"):
        report(observation(latest_verified_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="deadline_at must not be before generated_at"):
        report(observation(deadline_at=GENERATED_AT - timedelta(seconds=1)))

    breach_report = report(
        observation(
            claim_bucket="missing-check",
            latest_verified_at=None,
            missing_field_count=d("2"),
            deadline_at=None,
        ),
    )
    row = breach_report.rows[0]

    assert row.status == "block"
    assert row.latest_verification_age_seconds == d("10800.000000")
    assert row.deadline_seconds == d("0.000000")
    assert "update_latency_block" in row.reason_codes
    assert "deadline_proximity_block" in row.reason_codes


def test_module_scope_has_no_forbidden_runtime_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_source_claim_update_latency_breach_report.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlite",
        "supabase",
    )
    forbidden_runtime_names = (
        "wallet",
        "signing",
        "private_key",
        "api_key",
        "auth",
        "token",
        "dsn",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "submit",
        "cancel",
        "replace_order",
        "create_order",
        "execute",
        "connect",
        "commit",
        "rollback",
        "cursor",
        "open",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", maxsplit=1)[0] not in forbidden_modules
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", maxsplit=1)[0] not in forbidden_modules
        if isinstance(node, ast.Name):
            assert node.id.lower() not in forbidden_runtime_names
        if isinstance(node, ast.Attribute):
            assert node.attr.lower() not in forbidden_runtime_names
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id != "float"
                assert node.func.id.lower() not in forbidden_runtime_names
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr.lower() not in forbidden_runtime_names


def test_elapsed_time_uses_decimal_safe_datetime_arithmetic() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_source_claim_update_latency_breach_report.py",
    ).read_text(encoding="utf-8")

    assert ".timestamp(" not in source
    assert ".total_seconds(" not in source


def test_decimal_arithmetic_is_independent_of_ambient_context() -> None:
    module = api()
    cfg = config()
    item = observation(
        expected_update_cadence_seconds=d("3.000000"),
        latest_verified_at=ago(2),
    )
    expected = report(item, cfg=cfg)
    expected_payload = module.research_source_claim_update_latency_breach_report_payload(
        expected,
    )

    with localcontext() as ambient:
        ambient.prec = 4
        ambient.rounding = ROUND_DOWN
        constrained = report(item, cfg=cfg)
        constrained_payload = (
            module.research_source_claim_update_latency_breach_report_payload(
                constrained,
            )
        )

    assert constrained == expected
    assert constrained_payload == expected_payload
    assert constrained.rows[0].latency_ratio == d("0.666667")


def test_decimal_validation_uses_raw_bounds_and_rejects_signed_zero_and_non_finite() -> None:
    with pytest.raises(ValueError, match="between zero and one"):
        config(watch_source_authority_score=d("1.0000004"))

    with pytest.raises(ValueError, match="nonnegative"):
        config(watch_deadline_seconds=d("-0.0000004"))

    with pytest.raises(ValueError, match="between zero and one"):
        observation(contradiction_pressure=d("-0.0000004"))

    with pytest.raises(ValueError, match="whole"):
        observation(missing_field_count=d("1.0000004"))

    for signed_zero_field in (
        {"watch_source_authority_score": d("-0.000000")},
        {"watch_deadline_seconds": d("-0.000000")},
        {"watch_missing_field_count": d("-0")},
    ):
        with pytest.raises(ValueError, match="signed zero"):
            config(**signed_zero_field)

    for non_finite in ("NaN", "Infinity", "-Infinity"):
        with pytest.raises(ValueError, match="finite"):
            observation(source_authority_score=d(non_finite))


def test_public_dataclasses_are_frozen_final_and_exact_schema() -> None:
    module = api()
    breach_report = report(observation())
    public_values = (
        config(),
        observation(),
        breach_report.rows[0],
        breach_report,
    )

    for value in public_values:
        value_type = type(value)
        assert is_dataclass(value)
        assert value_type.__dataclass_params__.frozen is True
        first_field = fields(value_type)[0].name
        with pytest.raises(FrozenInstanceError):
            setattr(value, first_field, getattr(value, first_field))
        with pytest.raises(TypeError, match="cannot be subclassed"):
            type(f"{value_type.__name__}Subclass", (value_type,), {})

    assert tuple(field.name for field in fields(type(config()))) == (
        "config_version",
        "watch_latency_ratio",
        "block_latency_ratio",
        "watch_source_authority_score",
        "block_source_authority_score",
        "watch_contradiction_pressure",
        "block_contradiction_pressure",
        "watch_corroboration_depth",
        "block_corroboration_depth",
        "watch_extraction_confidence",
        "block_extraction_confidence",
        "watch_missing_field_count",
        "block_missing_field_count",
        "watch_deadline_seconds",
        "block_deadline_seconds",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(field.name for field in fields(type(observation()))) == (
        "claim_bucket",
        "expected_update_cadence_seconds",
        "latest_verified_at",
        "source_authority_score",
        "contradiction_pressure",
        "corroboration_depth",
        "extraction_confidence",
        "missing_field_count",
        "deadline_at",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(field.name for field in fields(type(breach_report.rows[0]))) == (
        "claim_bucket",
        "expected_update_cadence_seconds",
        "latest_verification_age_seconds",
        "latency_ratio",
        "source_authority_score",
        "contradiction_pressure",
        "corroboration_depth",
        "extraction_confidence",
        "missing_field_count",
        "deadline_seconds",
        "breach_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(field.name for field in fields(type(breach_report))) == (
        "generated_at",
        "config_version",
        "claim_bucket_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_latest_verification_age_seconds",
        "max_latency_ratio",
        "max_contradiction_pressure",
        "min_extraction_confidence",
        "min_deadline_seconds",
        "status",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )


def test_public_payload_enforces_exact_canonical_schema_digest_and_privacy() -> None:
    module = api()
    breach_report = report(observation())
    payload = mutable_payload(breach_report)

    assert (
        module.validate_research_source_claim_update_latency_breach_public_payload(
            payload,
        )
        == payload
    )
    assert module.research_source_claim_update_latency_breach_report_payload(payload) == payload

    unexpected_top_level = mutable_payload(breach_report)
    unexpected_top_level["safe_extra"] = "safe"
    resign_payload(unexpected_top_level)
    with pytest.raises(ValueError, match="public payload schema"):
        module.validate_research_source_claim_update_latency_breach_public_payload(
            unexpected_top_level,
        )

    missing_top_level = mutable_payload(breach_report)
    missing_top_level.pop("status")
    resign_payload(missing_top_level)
    with pytest.raises(ValueError, match="public payload schema"):
        module.validate_research_source_claim_update_latency_breach_public_payload(
            missing_top_level,
        )

    unexpected_row = mutable_payload(breach_report)
    rows = unexpected_row["rows"]
    assert type(rows) is list
    rows[0]["safe_extra"] = "safe"
    resign_payload(unexpected_row)
    with pytest.raises(ValueError, match="row schema"):
        module.validate_research_source_claim_update_latency_breach_public_payload(
            unexpected_row,
        )

    noncanonical_decimal = mutable_payload(breach_report)
    noncanonical_decimal["claim_bucket_count"] = "1.0"
    resign_payload(noncanonical_decimal)
    with pytest.raises(ValueError, match="claim_bucket_count"):
        module.validate_research_source_claim_update_latency_breach_public_payload(
            noncanonical_decimal,
        )

    unsafe_value = mutable_payload(breach_report)
    unsafe_rows = unsafe_value["rows"]
    assert type(unsafe_rows) is list
    unsafe_rows[0]["claim_bucket"] = "market-alpha"
    resign_payload(unsafe_value)
    with pytest.raises(ValueError, match="unsafe public value"):
        module.validate_research_source_claim_update_latency_breach_public_payload(
            unsafe_value,
        )

    forged_digest = mutable_payload(breach_report)
    forged_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_claim_update_latency_breach_public_payload(
            forged_digest,
        )


@pytest.mark.parametrize("reorder_target", ("report", "row"))
def test_public_payload_rejects_resigned_report_and_row_field_order_changes(
    reorder_target: str,
) -> None:
    module = api()
    breach_report = report(observation())
    payload = mutable_payload(breach_report)

    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "claim_bucket_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_latest_verification_age_seconds",
        "max_latency_ratio",
        "max_contradiction_pressure",
        "min_extraction_confidence",
        "min_deadline_seconds",
        "status",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    rows = payload["rows"]
    assert type(rows) is list
    assert tuple(rows[0]) == (
        "claim_bucket",
        "expected_update_cadence_seconds",
        "latest_verification_age_seconds",
        "latency_ratio",
        "source_authority_score",
        "contradiction_pressure",
        "corroboration_depth",
        "extraction_confidence",
        "missing_field_count",
        "deadline_seconds",
        "breach_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )

    if reorder_target == "report":
        payload = dict(reversed(tuple(payload.items())))
        match = "public payload schema"
    else:
        rows[0] = dict(reversed(tuple(rows[0].items())))
        match = "row schema"
    resign_payload(payload)
    assert payload["derived_validation_digest"] == canonical_digest(payload)

    with pytest.raises(ValueError, match=match):
        module.validate_research_source_claim_update_latency_breach_public_payload(
            payload,
        )


def test_builder_revalidates_object_setattr_tampered_config() -> None:
    cfg = config()
    object.__setattr__(cfg, "watch_latency_ratio", d("4.000000"))

    with pytest.raises(ValueError, match="block_latency_ratio"):
        report(observation(), cfg=cfg)


def test_builder_revalidates_object_setattr_tampered_observations() -> None:
    tampered_observation = observation()
    object.__setattr__(
        tampered_observation,
        "latest_verified_at",
        _DatetimeSubclass(2026, 7, 8, 11, 30, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="latest_verified_at must be a datetime"):
        report(tampered_observation)


def test_report_reconstruction_revalidates_object_setattr_tampered_nested_rows() -> None:
    module = api()
    breach_report = report(observation())
    payload = mutable_payload(breach_report)
    rows = payload["rows"]
    assert type(rows) is list
    row = breach_report.rows[0]
    object.__setattr__(row, "source_authority_score", d("1.500000"))
    rows[0]["source_authority_score"] = "1.500000"
    resign_payload(payload)

    report_kwargs = {
        field.name: getattr(breach_report, field.name)
        for field in fields(type(breach_report))
    }
    report_kwargs["derived_validation_digest"] = payload["derived_validation_digest"]

    with pytest.raises(ValueError, match="source_authority_score"):
        module.ResearchSourceClaimUpdateLatencyBreachReport(
            **report_kwargs,
            validation_config=config(),
        )


def test_resigned_payload_recomputes_and_rejects_all_derived_field_forgery() -> None:
    module = api()
    breach_report = report(
        observation(
            claim_bucket="regional-board",
            latest_verified_at=ago(7200),
            source_authority_score=d("0.450000"),
            contradiction_pressure=d("0.500000"),
            corroboration_depth=d("1"),
            extraction_confidence=d("0.650000"),
            missing_field_count=d("1"),
            deadline_at=ahead(5400),
        ),
    )

    forged_ratio = mutable_payload(breach_report)
    ratio_rows = forged_ratio["rows"]
    assert type(ratio_rows) is list
    ratio_rows[0]["latency_ratio"] = "2.500000"
    forged_ratio["max_latency_ratio"] = "2.500000"
    resign_payload(forged_ratio)
    with pytest.raises(ValueError, match="latency_ratio must match"):
        module.validate_research_source_claim_update_latency_breach_public_payload(
            forged_ratio,
        )

    forged_score = mutable_payload(breach_report)
    score_rows = forged_score["rows"]
    assert type(score_rows) is list
    score_rows[0]["breach_score"] = "0.900000"
    resign_payload(forged_score)
    with pytest.raises(ValueError, match="breach_score must match"):
        module.validate_research_source_claim_update_latency_breach_public_payload(
            forged_score,
        )

    forged_reasons = mutable_payload(breach_report)
    reason_rows = forged_reasons["rows"]
    assert type(reason_rows) is list
    reason_rows[0]["reason_codes"] = ["claim_update_latency_pass"]
    reason_rows[0]["status"] = "pass"
    reason_rows[0]["breach_score"] = "0.000000"
    forged_reasons["pass_count"] = "1"
    forged_reasons["watch_count"] = "0"
    forged_reasons["status"] = "pass"
    forged_reasons["reason_codes"] = ["claim_update_latency_pass"]
    resign_payload(forged_reasons)
    with pytest.raises(ValueError, match="reason_codes must match row inputs"):
        module.validate_research_source_claim_update_latency_breach_public_payload(
            forged_reasons,
        )

    forged_summary = mutable_payload(breach_report)
    forged_summary["max_contradiction_pressure"] = "0.600000"
    resign_payload(forged_summary)
    with pytest.raises(ValueError, match="max_contradiction_pressure must match rows"):
        module.validate_research_source_claim_update_latency_breach_public_payload(
            forged_summary,
        )


def test_rows_use_complete_stable_severity_sorting() -> None:
    first = report(
        observation(claim_bucket="pass-row"),
        observation(
            claim_bucket="watch-z",
            latest_verified_at=ago(7200),
            source_authority_score=d("0.450000"),
        ),
        observation(
            claim_bucket="block-row",
            latest_verified_at=ago(14400),
            source_authority_score=d("0.200000"),
        ),
        observation(
            claim_bucket="watch-a",
            latest_verified_at=ago(7200),
            source_authority_score=d("0.450000"),
        ),
    )
    second = report(
        observation(
            claim_bucket="watch-a",
            latest_verified_at=ago(7200),
            source_authority_score=d("0.450000"),
        ),
        observation(
            claim_bucket="block-row",
            latest_verified_at=ago(14400),
            source_authority_score=d("0.200000"),
        ),
        observation(
            claim_bucket="watch-z",
            latest_verified_at=ago(7200),
            source_authority_score=d("0.450000"),
        ),
        observation(claim_bucket="pass-row"),
    )

    assert tuple(row.claim_bucket for row in first.rows) == (
        "block-row",
        "watch-a",
        "watch-z",
        "pass-row",
    )
    assert first == second
