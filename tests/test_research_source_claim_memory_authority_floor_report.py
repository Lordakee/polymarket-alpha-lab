from __future__ import annotations

import ast
import hashlib
import importlib
import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_claim_memory_authority_floor_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_claim_memory_authority_floor_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "raw_candidate_id",
    "candidate-private",
    "candidate_private",
    "market-private",
    "market_private",
    "market_slug",
    "market_question",
    "will alpha resolve",
    "https://authority.example.test",
    "dsn=postgres",
    "authority_table",
    "token=secret",
    "wallet=0xabc",
    "order=1",
    "live feed",
    "source url",
    "source text",
    "private_candidate_reference",
    "private_market_reference",
    "private_source_reference",
)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "fresh_authority_age_seconds": d("3600.000000"),
        "stale_authority_age_seconds": d("86400.000000"),
        "pass_authority_floor_score": d("0.800000"),
        "watch_authority_floor_score": d("0.550000"),
        "watch_contradiction_risk_score": d("0.300000"),
        "block_contradiction_risk_score": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchSourceClaimMemoryAuthorityFloorConfig(**values)


def item(
    index: int,
    *,
    claim_bucket: str = "claim-alpha",
    authority_bucket: str | None = None,
    authority_updated_at: datetime | None = None,
    authority_score: Decimal = d("0.940000"),
    memory_confidence_score: Decimal = d("0.910000"),
    evidence_coverage_score: Decimal = d("0.930000"),
    contradiction_risk_score: Decimal = d("0.040000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceClaimMemoryAuthorityFloorInput(
        claim_bucket=claim_bucket,
        authority_bucket=authority_bucket or f"authority-{index:03d}",
        private_candidate_reference=(
            f"raw_candidate_id=candidate-private-{index}; token=secret-{index}"
        ),
        private_market_reference=(
            f"market-private-{index}; market_slug=will-alpha-{index}; "
            f"market_question=Will Alpha resolve {index}?"
        ),
        private_source_reference=(
            "source URL https://authority.example.test/private?"
            f"dsn=postgres://user:pass@host/db&table=authority_table_{index}; "
            f"wallet=0xabc; order={index}; live feed; source text"
        ),
        observed_at=GENERATED_AT - timedelta(hours=2),
        authority_updated_at=authority_updated_at
        if authority_updated_at is not None
        else GENERATED_AT - timedelta(minutes=20),
        authority_score=authority_score,
        memory_confidence_score=memory_confidence_score,
        evidence_coverage_score=evidence_coverage_score,
        contradiction_risk_score=contradiction_risk_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    rows: tuple[Any, ...],
    *,
    config: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_source_claim_memory_authority_floor_report(
        rows,
        config=config if config is not None else cfg(),
        generated_at=generated_at,
    )


def walk_payload_values(value: object) -> list[object]:
    values: list[object] = [value]
    if type(value) is dict:
        for key, item_value in value.items():
            values.extend(walk_payload_values(key))
            values.extend(walk_payload_values(item_value))
    elif type(value) is list:
        for item_value in value:
            values.extend(walk_payload_values(item_value))
    return values


def assert_public_payload_is_decimal_string_only(value: object) -> None:
    for item_value in walk_payload_values(value):
        if type(item_value) in (int, float, Decimal):
            raise AssertionError(f"public payload leaked numeric scalar {item_value!r}")


def assert_no_public_raw_leaks(payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, sort_keys=True).lower()
    for fragment in FORBIDDEN_PUBLIC_FRAGMENTS:
        assert fragment not in encoded


def payload_with_recomputed_digest(module: Any, payload: dict[str, object]) -> dict[str, object]:
    updated = dict(payload)
    digest_material = {
        key: value
        for key, value in updated.items()
        if key != "derived_validation_digest"
    }
    updated["derived_validation_digest"] = (
        module.research_source_claim_memory_authority_floor_report_digest(
            digest_material,
        )
    )
    return updated


def assert_dataclass_decimal_only(value: object) -> None:
    assert is_dataclass(value)
    for field in fields(value):
        field_value = getattr(value, field.name)
        if field.name in {
            "fresh_authority_age_seconds",
            "stale_authority_age_seconds",
            "pass_authority_floor_score",
            "watch_authority_floor_score",
            "watch_contradiction_risk_score",
            "block_contradiction_risk_score",
            "authority_score",
            "memory_confidence_score",
            "evidence_coverage_score",
            "contradiction_risk_score",
            "authority_age_seconds",
            "authority_recency_score",
            "authority_floor_score",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_authority_count",
            "low_authority_floor_count",
            "contradiction_risk_count",
            "average_authority_floor_score",
            "max_authority_floor_score",
        }:
            assert type(field_value) is Decimal


def test_authority_floor_scores_rows_and_sanitizes_public_payload() -> None:
    module = api()
    report = build_report(
        (
            item(
                3,
                claim_bucket="gamma-block",
                authority_bucket="authority-block",
                authority_updated_at=GENERATED_AT - timedelta(days=4),
                authority_score=d("0.500000"),
                memory_confidence_score=d("0.450000"),
                evidence_coverage_score=d("0.400000"),
                contradiction_risk_score=d("0.750000"),
                reason_codes=("primary_memory_stale",),
            ),
            item(
                1,
                claim_bucket="alpha-pass",
                authority_bucket="authority-pass",
            ),
            item(
                2,
                claim_bucket="beta-watch",
                authority_bucket="authority-watch",
                authority_updated_at=GENERATED_AT - timedelta(hours=3),
                authority_score=d("0.700000"),
                memory_confidence_score=d("0.720000"),
                evidence_coverage_score=d("0.600000"),
                contradiction_risk_score=d("0.100000"),
                reason_codes=("manual_recheck",),
            ),
        ),
    )

    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.stale_authority_count == d("1.000000")
    assert report.low_authority_floor_count == d("2.000000")
    assert report.contradiction_risk_count == d("1.000000")
    assert report.average_authority_floor_score == d("0.503333")
    assert report.max_authority_floor_score == d("0.910000")

    block_row, watch_row, pass_row = report.rows
    assert type(block_row) is module.ResearchSourceClaimMemoryAuthorityFloorRow
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert block_row.claim_ref_digest.startswith("sha256:")
    assert block_row.authority_ref_digest.startswith("sha256:")
    assert block_row.status == "block"
    assert block_row.authority_age_seconds == d("345600.000000")
    assert block_row.authority_recency_score == d("0.000000")
    assert block_row.authority_floor_score == d("0.000000")
    assert block_row.reason_codes == (
        "authority_floor_block",
        "authority_memory_stale",
        "contradiction_risk_block",
        "input_primary_memory_stale",
    )

    assert watch_row.status == "watch"
    assert watch_row.authority_age_seconds == d("10800.000000")
    assert watch_row.authority_recency_score == d("0.913043")
    assert watch_row.authority_floor_score == d("0.600000")
    assert watch_row.reason_codes == (
        "authority_floor_watch",
        "input_manual_recheck",
    )

    assert pass_row.status == "pass"
    assert pass_row.authority_floor_score == d("0.910000")
    assert pass_row.reason_codes == ("authority_floor_pass",)

    payload = module.research_source_claim_memory_authority_floor_report_public_payload(
        report,
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["row_count"] == "3.000000"
    assert payload["average_authority_floor_score"] == "0.503333"
    assert payload["rows"][0]["authority_floor_score"] == "0.000000"
    assert_public_payload_is_decimal_string_only(payload)
    assert_no_public_raw_leaks(payload)


def test_payload_digest_is_deterministic_and_validated() -> None:
    module = api()
    first = build_report(
        (
            item(
                2,
                claim_bucket="beta-watch",
                authority_updated_at=GENERATED_AT - timedelta(hours=3),
                evidence_coverage_score=d("0.600000"),
            ),
            item(1, claim_bucket="alpha-pass"),
        ),
    )
    second = build_report(
        (
            item(1, claim_bucket="alpha-pass"),
            item(
                2,
                claim_bucket="beta-watch",
                authority_updated_at=GENERATED_AT - timedelta(hours=3),
                evidence_coverage_score=d("0.600000"),
            ),
        ),
    )

    first_payload = module.research_source_claim_memory_authority_floor_report_public_payload(first)
    second_payload = module.research_source_claim_memory_authority_floor_report_public_payload(second)
    assert first_payload == second_payload

    digest_material = {
        key: value
        for key, value in first_payload.items()
        if key != "derived_validation_digest"
    }
    expected_digest = hashlib.sha256(
        json.dumps(
            digest_material,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert first_payload["derived_validation_digest"] == expected_digest
    assert module.validate_research_source_claim_memory_authority_floor_report_public_payload(
        first_payload,
    )

    tampered = dict(first_payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_claim_memory_authority_floor_report_public_payload(
            tampered,
        )


def test_public_payload_requires_canonical_scalar_and_reason_code_encodings() -> None:
    module = api()
    payload = module.research_source_claim_memory_authority_floor_report_public_payload(
        build_report(
            (
                item(
                    1,
                    authority_updated_at=GENERATED_AT - timedelta(days=4),
                    contradiction_risk_score=d("0.750000"),
                    reason_codes=("manual_recheck",),
                ),
            ),
        ),
    )

    noncanonical_count = deepcopy(payload)
    noncanonical_count["low_authority_floor_count"] = "1"
    with pytest.raises(ValueError, match="canonical Decimal string"):
        module.validate_research_source_claim_memory_authority_floor_report_public_payload(
            payload_with_recomputed_digest(module, noncanonical_count),
        )

    noncanonical_ratio = deepcopy(payload)
    noncanonical_ratio["rows"][0]["authority_score"] = "0.94"
    with pytest.raises(ValueError, match="canonical Decimal string"):
        module.validate_research_source_claim_memory_authority_floor_report_public_payload(
            payload_with_recomputed_digest(module, noncanonical_ratio),
        )

    noncanonical_datetime = deepcopy(payload)
    noncanonical_datetime["generated_at"] = "2026-07-09T08:00:00-04:00"
    with pytest.raises(ValueError, match="canonical UTC datetime"):
        module.validate_research_source_claim_memory_authority_floor_report_public_payload(
            payload_with_recomputed_digest(module, noncanonical_datetime),
        )

    noncanonical_reasons = deepcopy(payload)
    noncanonical_reasons["rows"][0]["reason_codes"] = list(
        reversed(noncanonical_reasons["rows"][0]["reason_codes"]),
    )
    with pytest.raises(ValueError, match="canonical reason code order"):
        module.validate_research_source_claim_memory_authority_floor_report_public_payload(
            payload_with_recomputed_digest(module, noncanonical_reasons),
        )


def test_public_payload_rejects_recomputed_summary_and_row_order_tampering() -> None:
    module = api()
    payload = module.research_source_claim_memory_authority_floor_report_public_payload(
        build_report(
            (
                item(1, claim_bucket="alpha-pass"),
                item(
                    2,
                    claim_bucket="beta-block",
                    authority_updated_at=GENERATED_AT - timedelta(days=4),
                ),
            ),
        ),
    )

    wrong_low_count = deepcopy(payload)
    wrong_low_count["low_authority_floor_count"] = "0.000000"
    with pytest.raises(ValueError, match="low_authority_floor_count"):
        module.validate_research_source_claim_memory_authority_floor_report_public_payload(
            payload_with_recomputed_digest(module, wrong_low_count),
        )

    reordered_rows = deepcopy(payload)
    reordered_rows["rows"] = list(reversed(reordered_rows["rows"]))
    with pytest.raises(ValueError, match="canonical order"):
        module.validate_research_source_claim_memory_authority_floor_report_public_payload(
            payload_with_recomputed_digest(module, reordered_rows),
        )


@pytest.mark.parametrize(
    "field_name",
    ("observed_at", "authority_updated_at"),
)
def test_public_payload_rejects_resigned_future_row_timestamps(
    field_name: str,
) -> None:
    module = api()
    payload = module.research_source_claim_memory_authority_floor_report_public_payload(
        build_report((item(1),)),
    )
    tampered = deepcopy(payload)
    tampered["rows"][0][field_name] = (  # type: ignore[index]
        GENERATED_AT + timedelta(seconds=1)
    ).isoformat()
    if field_name == "authority_updated_at":
        tampered["rows"][0]["authority_age_seconds"] = "0.000000"  # type: ignore[index]
        tampered["rows"][0]["authority_recency_score"] = "1.000000"  # type: ignore[index]

    with pytest.raises(ValueError, match=field_name):
        module.validate_research_source_claim_memory_authority_floor_report_public_payload(
            payload_with_recomputed_digest(module, tampered),
        )


def test_public_payload_rejects_resigned_duplicate_row_identities() -> None:
    module = api()
    payload = module.research_source_claim_memory_authority_floor_report_public_payload(
        build_report((item(1),)),
    )
    tampered = deepcopy(payload)
    tampered["rows"] = [
        deepcopy(payload["rows"][0]),  # type: ignore[index]
        deepcopy(payload["rows"][0]),  # type: ignore[index]
    ]
    tampered["row_count"] = "2.000000"
    tampered["pass_count"] = "2.000000"

    with pytest.raises(ValueError, match="duplicate"):
        module.validate_research_source_claim_memory_authority_floor_report_public_payload(
            payload_with_recomputed_digest(module, tampered),
        )


def test_public_payload_rejects_resigned_derived_semantic_drift() -> None:
    module = api()
    payload = module.research_source_claim_memory_authority_floor_report_public_payload(
        build_report((item(1),)),
    )

    forged_status = deepcopy(payload)
    forged_status["rows"][0]["status"] = "watch"  # type: ignore[index]
    forged_status["rows"][0]["reason_codes"] = ["authority_floor_watch"]  # type: ignore[index]
    forged_status["status"] = "watch"
    forged_status["reason_codes"] = ["authority_floor_watch"]
    forged_status["pass_count"] = "0.000000"
    forged_status["watch_count"] = "1.000000"

    forged_reason = deepcopy(payload)
    forged_reason["reason_codes"] = ["authority_floor_watch"]

    forged_count = deepcopy(payload)
    forged_count["pass_count"] = "0.000000"

    forged_score = deepcopy(payload)
    forged_score["rows"][0]["authority_floor_score"] = "0.800000"  # type: ignore[index]

    for tampered, message in (
        (forged_status, "status"),
        (forged_reason, "reason_codes"),
        (forged_count, "pass_count"),
        (forged_score, "authority_floor_score"),
    ):
        with pytest.raises(ValueError, match=message):
            module.validate_research_source_claim_memory_authority_floor_report_public_payload(
                payload_with_recomputed_digest(module, tampered),
            )


def test_public_payload_requires_exact_report_and_row_schemas_when_resigned() -> None:
    module = api()
    payload = module.research_source_claim_memory_authority_floor_report_public_payload(
        build_report((item(1),)),
    )

    extra_report_field = deepcopy(payload)
    extra_report_field["safe_extra"] = "pass"
    with pytest.raises(ValueError, match="report schema"):
        module.validate_research_source_claim_memory_authority_floor_report_public_payload(
            payload_with_recomputed_digest(module, extra_report_field),
        )

    missing_row_field = deepcopy(payload)
    del missing_row_field["rows"][0]["readonly"]  # type: ignore[index]
    with pytest.raises(ValueError, match="row schema"):
        module.validate_research_source_claim_memory_authority_floor_report_public_payload(
            payload_with_recomputed_digest(module, missing_row_field),
        )


def test_public_payload_rejects_resigned_signed_zero() -> None:
    module = api()
    payload = module.research_source_claim_memory_authority_floor_report_public_payload(
        build_report(()),
    )
    payload["average_authority_floor_score"] = "-0.000000"

    with pytest.raises(ValueError, match="average_authority_floor_score"):
        module.validate_research_source_claim_memory_authority_floor_report_public_payload(
            payload_with_recomputed_digest(module, payload),
        )


def test_public_payload_validation_rejects_recomputed_invalid_schema() -> None:
    module = api()
    payload = module.research_source_claim_memory_authority_floor_report_public_payload(
        build_report((item(1),)),
    )

    invalid_status = dict(payload)
    invalid_status["status"] = "blocked"
    with pytest.raises(ValueError, match="status"):
        module.validate_research_source_claim_memory_authority_floor_report_public_payload(
            payload_with_recomputed_digest(module, invalid_status),
        )

    invalid_numeric = dict(payload)
    invalid_numeric["row_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        module.validate_research_source_claim_memory_authority_floor_report_public_payload(
            payload_with_recomputed_digest(module, invalid_numeric),
        )

    invalid_flag = dict(payload)
    invalid_flag["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_source_claim_memory_authority_floor_report_public_payload(
            payload_with_recomputed_digest(module, invalid_flag),
        )


def test_report_rejects_manual_summary_count_tampering() -> None:
    module = api()
    report = build_report(
        (
            item(1),
            item(2, authority_updated_at=GENERATED_AT - timedelta(days=4)),
        ),
    )
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["stale_authority_count"] = d("0.000000")
    values["derived_validation_digest"] = ""

    with pytest.raises(ValueError, match="stale_authority_count"):
        module.ResearchSourceClaimMemoryAuthorityFloorReport(**values)


def test_report_rejects_low_count_and_row_order_tampering() -> None:
    module = api()
    report = build_report(
        (
            item(1, claim_bucket="alpha-pass"),
            item(
                2,
                claim_bucket="beta-block",
                authority_updated_at=GENERATED_AT - timedelta(days=4),
            ),
        ),
    )

    wrong_low_count = {field.name: getattr(report, field.name) for field in fields(report)}
    wrong_low_count["low_authority_floor_count"] = d("0.000000")
    wrong_low_count["derived_validation_digest"] = ""
    with pytest.raises(ValueError, match="low_authority_floor_count"):
        module.ResearchSourceClaimMemoryAuthorityFloorReport(**wrong_low_count)

    wrong_order = {field.name: getattr(report, field.name) for field in fields(report)}
    wrong_order["rows"] = tuple(reversed(report.rows))
    wrong_order["derived_validation_digest"] = ""
    with pytest.raises(ValueError, match="canonical order"):
        module.ResearchSourceClaimMemoryAuthorityFloorReport(**wrong_order)


def test_direct_row_rejects_forged_authority_floor_score() -> None:
    report = build_report((item(1),))

    with pytest.raises(ValueError, match="authority_floor_score"):
        replace(
            report.rows[0],
            authority_floor_score=d("0.800000"),
        )


def test_direct_row_requires_explicit_status_reason_code() -> None:
    report = build_report((item(1),))

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            report.rows[0],
            reason_codes=("input_manual_recheck",),
        )


def test_builder_and_report_revalidate_tampered_frozen_inputs() -> None:
    module = api()

    tampered_config = cfg()
    object.__setattr__(
        tampered_config,
        "pass_authority_floor_score",
        d("0.100000"),
    )
    with pytest.raises(ValueError, match="pass_authority_floor_score"):
        build_report((item(1),), config=tampered_config)

    tampered_input = item(1)
    object.__setattr__(tampered_input, "authority_score", d("1.500000"))
    with pytest.raises(ValueError, match="authority_score"):
        build_report((tampered_input,))

    report = build_report((item(1),))
    object.__setattr__(report.rows[0], "readonly", False)
    report_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    report_values["derived_validation_digest"] = ""
    with pytest.raises(ValueError, match="readonly"):
        module.ResearchSourceClaimMemoryAuthorityFloorReport(**report_values)


@pytest.mark.parametrize(
    "field_name",
    ("observed_at", "authority_updated_at"),
)
def test_builder_rejects_future_input_timestamps(field_name: str) -> None:
    future_input = replace(
        item(1),
        **{field_name: GENERATED_AT + timedelta(seconds=1)},
    )

    with pytest.raises(ValueError, match=field_name):
        build_report((future_input,))


def test_builder_rejects_duplicate_row_identities() -> None:
    duplicate = item(1)

    with pytest.raises(ValueError, match="duplicate"):
        build_report((duplicate, duplicate))


def test_digest_rejects_non_public_numeric_scalars() -> None:
    module = api()

    with pytest.raises(ValueError, match="numeric"):
        module.research_source_claim_memory_authority_floor_report_digest(
            {"row_count": 1},
        )


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    sample_config = cfg()
    sample_input = item(1)
    sample_report = build_report((sample_input,))
    sample_row = sample_report.rows[0]

    for sample in (sample_config, sample_input, sample_row, sample_report):
        assert_dataclass_decimal_only(sample)
        assert sample.paper_only is True
        assert sample.report_only is True
        assert sample.readonly is True
        with pytest.raises(FrozenInstanceError):
            sample.paper_only = False  # type: ignore[misc]
        for field in fields(sample):
            field_value = getattr(sample, field.name)
            if type(field_value) is Decimal and field_value.is_zero():
                assert not field_value.is_signed()

    for public_dataclass in (
        module.ResearchSourceClaimMemoryAuthorityFloorConfig,
        module.ResearchSourceClaimMemoryAuthorityFloorInput,
        module.ResearchSourceClaimMemoryAuthorityFloorRow,
        module.ResearchSourceClaimMemoryAuthorityFloorReport,
    ):
        with pytest.raises(TypeError, match="subclassed"):
            type("UnsafeSubclass", (public_dataclass,), {})

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        item(1, report_only=False)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="readonly"):
        build_report((item(1, readonly=False),))  # type: ignore[call-arg]


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("authority_score", DecimalSubclass("0.900000"), "authority_score"),
        ("memory_confidence_score", d("1.000001"), "memory_confidence_score"),
        ("evidence_coverage_score", d("-0.000001"), "evidence_coverage_score"),
        ("contradiction_risk_score", 0.1, "contradiction_risk_score"),
    ),
)
def test_rejects_non_decimal_or_out_of_range_numeric_inputs(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        item(1, **{field_name: bad_value})


def test_rejects_string_reason_codes_in_input() -> None:
    with pytest.raises(ValueError, match="reason_codes"):
        item(1, reason_codes="abc")  # type: ignore[arg-type]


def test_status_domain_and_empty_report_are_only_pass_watch_block() -> None:
    empty = build_report(())
    report = build_report(
        (
            item(1),
            item(2, authority_updated_at=GENERATED_AT - timedelta(hours=3), evidence_coverage_score=d("0.600000")),
            item(3, authority_updated_at=GENERATED_AT - timedelta(days=4)),
        ),
    )

    assert empty.status == "block"
    assert empty.reason_codes == ("no_claim_memory_authority_inputs",)
    statuses = {empty.status, report.status}
    statuses.update(row.status for row in report.rows)
    assert statuses <= {"pass", "watch", "block"}
    assert "blocked" not in repr(report)


def test_module_has_no_db_network_wallet_auth_order_or_live_trading_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "order",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "recommend",
        "rollback",
        "send",
        "size",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
