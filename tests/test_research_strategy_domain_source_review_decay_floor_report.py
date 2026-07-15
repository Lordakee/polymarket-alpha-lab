from __future__ import annotations

import ast
import hashlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_domain_source_review_decay_floor_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_domain_source_review_decay_floor_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 13, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_DOMAIN_SOURCE_REVIEW_DECAY_FLOOR_REPORT_CONFIG_VERSION
        ),
        "min_review_source_count_pass": d("3.000000"),
        "min_review_source_count_watch": d("2.000000"),
        "min_domain_source_count_pass": d("2.000000"),
        "min_domain_source_count_watch": d("1.000000"),
        "max_latest_source_review_age_seconds_pass": d("1800.000000"),
        "max_latest_source_review_age_seconds_watch": d("7200.000000"),
        "review_quality_score_pass_floor": d("0.800000"),
        "review_quality_score_watch_floor": d("0.550000"),
        "source_authority_score_pass_floor": d("0.750000"),
        "source_authority_score_watch_floor": d("0.500000"),
        "contradiction_pressure_watch_ceiling": d("0.250000"),
        "contradiction_pressure_block_ceiling": d("0.600000"),
        "decay_floor_score_pass_floor": d("0.750000"),
        "decay_floor_score_watch_floor": d("0.550000"),
    }
    values.update(overrides)
    return module.ResearchStrategyDomainSourceReviewDecayFloorConfig(**values)


def review_input(
    module: Any,
    source_review_key: str = "source-review-pass",
    domain_review_key: str = "domain-review-pass",
    *,
    review_source_count: Decimal = d("3.000000"),
    domain_source_count: Decimal = d("2.000000"),
    latest_source_review_age_seconds: Decimal = d("600.000000"),
    review_quality_score: Decimal = d("0.920000"),
    source_authority_score: Decimal = d("0.900000"),
    contradiction_pressure_score: Decimal = d("0.050000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return module.ResearchStrategyDomainSourceReviewDecayFloorInput(
        source_review_key=source_review_key,
        domain_review_key=domain_review_key,
        review_source_count=review_source_count,
        domain_source_count=domain_source_count,
        latest_source_review_age_seconds=latest_source_review_age_seconds,
        review_quality_score=review_quality_score,
        source_authority_score=source_authority_score,
        contradiction_pressure_score=contradiction_pressure_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    module: Any,
    *rows: Any,
    report_config: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_domain_source_review_decay_floor_report(
        rows,
        config=config(module) if report_config is None else report_config,
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("public_digest")
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload["public_digest"] = canonical_digest(payload)
    return payload


def test_source_review_decay_floor_scores_sorts_and_hashes_private_inputs() -> None:
    module = api()
    pass_item = review_input(module)
    watch_item = review_input(
        module,
        "source-review-watch",
        "domain-review-watch",
        review_source_count=d("2.000000"),
        domain_source_count=d("1.000000"),
        latest_source_review_age_seconds=d("3600.000000"),
        review_quality_score=d("0.620000"),
        source_authority_score=d("0.600000"),
        contradiction_pressure_score=d("0.300000"),
    )
    block_item = review_input(
        module,
        "source-review-block",
        "domain-review-block",
        review_source_count=d("1.000000"),
        domain_source_count=d("0.000000"),
        latest_source_review_age_seconds=d("9000.000000"),
        review_quality_score=d("0.450000"),
        source_authority_score=d("0.400000"),
        contradiction_pressure_score=d("0.650000"),
    )

    first = build_report(module, watch_item, block_item, pass_item)
    second = build_report(module, pass_item, watch_item, block_item)

    assert type(first) is module.ResearchStrategyDomainSourceReviewDecayFloorReport
    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_DOMAIN_SOURCE_REVIEW_DECAY_FLOOR_REPORT_CONFIG_VERSION
    )
    assert first.review_item_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.status == "block"
    assert first.review_source_attention_count == d("2.000000")
    assert first.domain_source_attention_count == d("2.000000")
    assert first.freshness_decay_attention_count == d("2.000000")
    assert first.review_quality_attention_count == d("2.000000")
    assert first.source_authority_attention_count == d("2.000000")
    assert first.contradiction_pressure_attention_count == d("2.000000")
    assert first.decay_floor_attention_count == d("2.000000")
    assert first.mean_decay_floor_score == d("0.600371")
    assert first.lowest_decay_floor_score == d("0.255556")
    assert first.highest_contradiction_pressure_score == d("0.650000")
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True

    assert tuple(row.aggregate_row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert first.rows[0].source_review_digest == digest("source-review-block")
    assert first.rows[0].domain_review_digest == digest("domain-review-block")
    assert first.rows[0].freshness_decay_score == ZERO
    assert first.rows[0].decay_floor_score == d("0.255556")
    assert first.rows[1].freshness_decay_score == d("0.500000")
    assert first.rows[1].decay_floor_score == d("0.597778")
    assert first.rows[2].freshness_decay_score == d("0.916667")
    assert first.rows[2].decay_floor_score == d("0.947778")
    assert first.rows[2].reason_codes == (
        "research_strategy_domain_source_review_decay_floor_clear",
    )
    assert not hasattr(first.rows[0], "source_review_key")
    assert not hasattr(first.rows[0], "domain_review_key")

    payload = module.research_strategy_domain_source_review_decay_floor_report_payload(
        first,
    )
    assert payload == (
        module.research_strategy_domain_source_review_decay_floor_report_payload(second)
    )
    assert payload["review_item_count"] == "3.000000"
    assert payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert payload["rows"][0]["decay_floor_score"] == "0.255556"
    assert payload["public_digest"] == first.public_digest
    assert payload["public_digest"] == canonical_digest(payload)
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    payload_text = json.dumps(payload, sort_keys=True)
    assert "source-review-block" not in payload_text
    assert "domain-review-block" not in payload_text
    assert "source_review_key" not in payload_text
    assert "domain_review_key" not in payload_text
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_values(payload)
    assert_public_payload_has_no_private_surfaces(payload)

    digest_value = module.research_strategy_domain_source_review_decay_floor_report_digest(
        first,
    )
    assert digest_value == first.public_digest
    assert len(digest_value) == 64
    int(digest_value, 16)
    module.validate_research_strategy_domain_source_review_decay_floor_report_digest(
        first,
    )
    module.validate_research_strategy_domain_source_review_decay_floor_public_payload(
        payload,
    )


def test_empty_inputs_block_with_no_input_reason_count() -> None:
    module = api()

    report = build_report(module)

    assert report.status == "block"
    assert report.review_item_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.mean_decay_floor_score == ZERO
    assert report.lowest_decay_floor_score == ZERO
    assert report.highest_contradiction_pressure_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == (
        "research_strategy_domain_source_review_decay_floor_no_inputs",
    )
    assert report.reason_code_counts == (
        module.ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount(
            reason_code="research_strategy_domain_source_review_decay_floor_no_inputs",
            count=ONE,
        ),
    )


def test_decimal_datetime_flags_frozen_and_digest_validation() -> None:
    module = api()
    report = build_report(
        module,
        review_input(module),
        generated_at=datetime(2026, 7, 9, 9, 30, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    for item in (config(module), review_input(module), report.rows[0], report):
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True

    with pytest.raises(ValueError, match="Decimal"):
        review_input(module, review_quality_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="exact Decimal"):
        review_input(module, review_quality_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="timezone-aware"):
        build_report(module, generated_at=datetime(2026, 7, 9, 13, 30))
    with pytest.raises(ValueError, match="paper_only"):
        config(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        review_input(module, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="config_version"):
        config(module, config_version="unsupported-version")
    with pytest.raises(ValueError, match="pass.*watch"):
        config(
            module,
            min_review_source_count_pass=d("1.000000"),
            min_review_source_count_watch=d("2.000000"),
        )
    with pytest.raises(ValueError, match="public_digest"):
        replace(report, public_digest="0" * 64)

    payload = module.research_strategy_domain_source_review_decay_floor_report_payload(
        report,
    )
    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="public_digest"):
        module.validate_research_strategy_domain_source_review_decay_floor_public_payload(
            tampered,
        )
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["status"] = "watch"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]


def test_module_scope_is_readonly_report_only_and_payload_rejects_private_surfaces() -> None:
    module = api()
    assert set(module.RESEARCH_STRATEGY_DOMAIN_SOURCE_REVIEW_DECAY_FLOOR_REPORT_STATUSES) == {
        "pass",
        "watch",
        "block",
    }
    assert tuple(module.__all__) == (
        "DEFAULT_RESEARCH_STRATEGY_DOMAIN_SOURCE_REVIEW_DECAY_FLOOR_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_DOMAIN_SOURCE_REVIEW_DECAY_FLOOR_REPORT_STATUSES",
        "ResearchStrategyDomainSourceReviewDecayFloorConfig",
        "ResearchStrategyDomainSourceReviewDecayFloorInput",
        "ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount",
        "ResearchStrategyDomainSourceReviewDecayFloorReport",
        "ResearchStrategyDomainSourceReviewDecayFloorRow",
        "build_research_strategy_domain_source_review_decay_floor_report",
        "research_strategy_domain_source_review_decay_floor_report_digest",
        "research_strategy_domain_source_review_decay_floor_report_payload",
        "validate_research_strategy_domain_source_review_decay_floor_public_payload",
        "validate_research_strategy_domain_source_review_decay_floor_report_digest",
    )

    tree = ast.parse(MODULE_PATH.read_text())
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    assert not imported_roots & {
        "ccxt",
        "httpx",
        "os",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "subprocess",
        "urllib",
        "web3",
    }

    payload = module.research_strategy_domain_source_review_decay_floor_report_payload(
        build_report(
            module,
            review_input(
                module,
                source_review_key=(
                    "raw candidate identifier market slug source url token order wallet"
                ),
                domain_review_key="private domain question source text",
            ),
        ),
    )
    rendered = json.dumps(payload, sort_keys=True)
    assert "raw candidate identifier" not in rendered
    assert "private domain question" not in rendered
    assert_public_payload_has_no_private_surfaces(payload)

    unsafe_payloads = (
        {"paper_only": True, "report_only": True, "readonly": True, "market_id": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "market_slug": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "question": "x"},
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "source_url": "https://example.invalid/a",
        },
        {"paper_only": True, "report_only": True, "readonly": True, "source_text": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "dsn": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "table_name": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "token": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "wallet": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "order": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "trade": "x"},
        {"paper_only": True, "report_only": True, "readonly": False},
    )
    for unsafe in unsafe_payloads:
        with pytest.raises(ValueError):
            module.validate_research_strategy_domain_source_review_decay_floor_public_payload(
                unsafe,
            )


def test_decimal_context_raw_bounds_signed_zero_and_non_finite_are_hardened() -> None:
    module = api()
    item = review_input(
        module,
        review_quality_score=d("0.812345"),
        source_authority_score=d("0.765432"),
        contradiction_pressure_score=d("0.123456"),
    )
    expected = module.research_strategy_domain_source_review_decay_floor_report_payload(
        build_report(module, item),
    )

    with localcontext(Context(prec=6, rounding=ROUND_DOWN)):
        constrained = (
            module.research_strategy_domain_source_review_decay_floor_report_payload(
                build_report(module, item),
            )
        )
    assert constrained == expected

    with pytest.raises(ValueError, match="review_quality_score.*between 0 and 1"):
        review_input(module, review_quality_score=d("1.0000004"))
    with pytest.raises(
        ValueError,
        match="latest_source_review_age_seconds.*nonnegative",
    ):
        review_input(module, latest_source_review_age_seconds=d("-0.0000004"))
    with pytest.raises(ValueError, match="review_source_count.*whole"):
        review_input(module, review_source_count=d("2.0000004"))

    for signed_zero in ("-0", "-0.000000"):
        with pytest.raises(ValueError, match="review_quality_score.*signed zero"):
            review_input(module, review_quality_score=d(signed_zero))
        with pytest.raises(ValueError, match="review_source_count.*signed zero"):
            review_input(module, review_source_count=d(signed_zero))
        with pytest.raises(
            ValueError,
            match="latest_source_review_age_seconds.*signed zero",
        ):
            review_input(
                module,
                latest_source_review_age_seconds=d(signed_zero),
            )

    for non_finite in ("NaN", "sNaN", "Infinity", "-Infinity"):
        with pytest.raises(ValueError, match="review_quality_score.*finite"):
            review_input(module, review_quality_score=d(non_finite))


def test_dataclasses_are_frozen_slotted_final_and_exact() -> None:
    module = api()
    public_types = (
        module.ResearchStrategyDomainSourceReviewDecayFloorConfig,
        module.ResearchStrategyDomainSourceReviewDecayFloorInput,
        module.ResearchStrategyDomainSourceReviewDecayFloorRow,
        module.ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount,
        module.ResearchStrategyDomainSourceReviewDecayFloorReport,
    )

    for public_type in public_types:
        assert public_type.__final__ is True
        assert public_type.__dataclass_params__.frozen is True
        assert public_type.__slots__
        assert "__dict__" not in public_type.__slots__

    report = build_report(module, review_input(module))
    assert not hasattr(report, "__dict__")


def test_config_rejects_equal_pass_and_watch_age_ceiling() -> None:
    module = api()

    with pytest.raises(ValueError, match="max_latest_source_review_age_seconds_pass.*below"):
        config(
            module,
            max_latest_source_review_age_seconds_pass=d("7200.000000"),
            max_latest_source_review_age_seconds_watch=d("7200.000000"),
        )


def test_builder_revalidates_tampered_input_before_decimal_arithmetic() -> None:
    module = api()
    item = review_input(module)
    object.__setattr__(item, "review_quality_score", Decimal("NaN"))

    with pytest.raises(ValueError, match="review_quality_score.*finite"):
        build_report(module, item)


def test_builder_revalidates_tampered_config_before_decimal_arithmetic() -> None:
    module = api()
    report_config = config(module)
    object.__setattr__(
        report_config,
        "min_review_source_count_pass",
        Decimal("NaN"),
    )

    with pytest.raises(ValueError, match="min_review_source_count_pass.*finite"):
        build_report(module, review_input(module), report_config=report_config)


def test_status_and_reason_code_strings_must_be_exact_and_reason_order_is_canonical() -> None:
    module = api()

    class StringSubclass(str):
        pass

    report = build_report(module, review_input(module))
    row = report.rows[0]
    with pytest.raises(ValueError, match="status"):
        replace(row, status=StringSubclass("pass"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=(StringSubclass(row.reason_codes[0]),))

    mixed = review_input(
        module,
        source_review_key="source-review-mixed",
        domain_review_key="domain-review-mixed",
        review_source_count=d("2.000000"),
        domain_source_count=d("0.000000"),
        latest_source_review_age_seconds=d("3600.000000"),
    )
    mixed_report = build_report(module, mixed)
    assert mixed_report.rows[0].reason_codes == (
        "research_strategy_domain_source_review_decay_floor_domain_source_block",
        "research_strategy_domain_source_review_decay_floor_review_source_watch",
        "research_strategy_domain_source_review_decay_floor_freshness_decay_watch",
        "research_strategy_domain_source_review_decay_floor_decay_floor_watch",
    )

    payload = json.loads(
        json.dumps(
            module.research_strategy_domain_source_review_decay_floor_report_payload(
                mixed_report,
            ),
        ),
    )
    payload["rows"][0]["reason_codes"] = list(
        reversed(payload["rows"][0]["reason_codes"]),
    )
    with pytest.raises(ValueError):
        module.validate_research_strategy_domain_source_review_decay_floor_public_payload(
            resign_payload(payload),
        )


def test_public_payload_requires_exact_canonical_nested_schema() -> None:
    module = api()
    payload = json.loads(
        json.dumps(
            module.research_strategy_domain_source_review_decay_floor_report_payload(
                build_report(module, review_input(module)),
            ),
        ),
    )

    assert set(payload) == {
        "generated_at",
        "config_version",
        "config",
        "review_item_count",
        "pass_count",
        "watch_count",
        "block_count",
        "review_source_attention_count",
        "domain_source_attention_count",
        "freshness_decay_attention_count",
        "review_quality_attention_count",
        "source_authority_attention_count",
        "contradiction_pressure_attention_count",
        "decay_floor_attention_count",
        "mean_decay_floor_score",
        "lowest_decay_floor_score",
        "highest_contradiction_pressure_score",
        "status",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "public_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(payload["config"]) == {
        "config_version",
        "min_review_source_count_pass",
        "min_review_source_count_watch",
        "min_domain_source_count_pass",
        "min_domain_source_count_watch",
        "max_latest_source_review_age_seconds_pass",
        "max_latest_source_review_age_seconds_watch",
        "review_quality_score_pass_floor",
        "review_quality_score_watch_floor",
        "source_authority_score_pass_floor",
        "source_authority_score_watch_floor",
        "contradiction_pressure_watch_ceiling",
        "contradiction_pressure_block_ceiling",
        "decay_floor_score_pass_floor",
        "decay_floor_score_watch_floor",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(payload["rows"][0]) == {
        "aggregate_row_number",
        "source_review_digest",
        "domain_review_digest",
        "review_source_count",
        "domain_source_count",
        "latest_source_review_age_seconds",
        "freshness_decay_score",
        "review_quality_score",
        "source_authority_score",
        "contradiction_pressure_score",
        "decay_floor_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(payload["reason_code_counts"][0]) == {
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    }

    forged_payloads: list[dict[str, Any]] = []

    extra_report = json.loads(json.dumps(payload))
    extra_report["diagnostic_note"] = "public"
    forged_payloads.append(extra_report)

    missing_report = json.loads(json.dumps(payload))
    missing_report.pop("mean_decay_floor_score")
    forged_payloads.append(missing_report)

    extra_config = json.loads(json.dumps(payload))
    extra_config["config"]["diagnostic_note"] = "public"
    forged_payloads.append(extra_config)

    extra_row = json.loads(json.dumps(payload))
    extra_row["rows"][0]["diagnostic_note"] = "public"
    forged_payloads.append(extra_row)

    missing_reason_count = json.loads(json.dumps(payload))
    missing_reason_count["reason_code_counts"][0].pop("count")
    forged_payloads.append(missing_reason_count)

    noncanonical_decimal = json.loads(json.dumps(payload))
    noncanonical_decimal["review_item_count"] = "1.0"
    forged_payloads.append(noncanonical_decimal)

    numeric_decimal = json.loads(json.dumps(payload))
    numeric_decimal["review_item_count"] = 1
    forged_payloads.append(numeric_decimal)

    noncanonical_datetime = json.loads(json.dumps(payload))
    noncanonical_datetime["generated_at"] = "2026-07-09T13:30:00Z"
    forged_payloads.append(noncanonical_datetime)

    for forged in forged_payloads:
        with pytest.raises(ValueError):
            module.validate_research_strategy_domain_source_review_decay_floor_public_payload(
                resign_payload(forged),
            )


def test_public_validator_recomputes_all_derived_fields_after_resigning() -> None:
    module = api()
    report = build_report(
        module,
        review_input(module),
        review_input(
            module,
            "source-review-watch-a",
            "domain-review-watch-a",
            review_source_count=d("2.000000"),
            domain_source_count=d("1.000000"),
            latest_source_review_age_seconds=d("3600.000000"),
            review_quality_score=d("0.620000"),
            source_authority_score=d("0.600000"),
            contradiction_pressure_score=d("0.300000"),
        ),
        review_input(
            module,
            "source-review-watch-b",
            "domain-review-watch-b",
            review_source_count=d("2.000000"),
            domain_source_count=d("1.000000"),
            latest_source_review_age_seconds=d("3600.000000"),
            review_quality_score=d("0.620000"),
            source_authority_score=d("0.600000"),
            contradiction_pressure_score=d("0.300000"),
        ),
    )
    payload = json.loads(
        json.dumps(
            module.research_strategy_domain_source_review_decay_floor_report_payload(
                report,
            ),
        ),
    )

    forged_payloads: list[dict[str, Any]] = []

    forged_freshness = json.loads(json.dumps(payload))
    forged_freshness["rows"][1]["freshness_decay_score"] = "0.900000"
    forged_payloads.append(forged_freshness)

    forged_decay_floor = json.loads(json.dumps(payload))
    forged_decay_floor["rows"][1]["decay_floor_score"] = "0.900000"
    forged_payloads.append(forged_decay_floor)

    forged_row_status = json.loads(json.dumps(payload))
    forged_row_status["rows"][1]["status"] = "pass"
    forged_row_status["rows"][1]["reason_codes"] = [
        "research_strategy_domain_source_review_decay_floor_clear",
    ]
    forged_payloads.append(forged_row_status)

    forged_mean = json.loads(json.dumps(payload))
    forged_mean["mean_decay_floor_score"] = "0.900000"
    forged_payloads.append(forged_mean)

    forged_count = json.loads(json.dumps(payload))
    forged_count["watch_count"] = "1.000000"
    forged_payloads.append(forged_count)

    forged_reason_count = json.loads(json.dumps(payload))
    forged_reason_count["reason_code_counts"][0]["count"] = "99.000000"
    forged_payloads.append(forged_reason_count)

    forged_order = json.loads(json.dumps(payload))
    forged_order["rows"][1], forged_order["rows"][2] = (
        forged_order["rows"][2],
        forged_order["rows"][1],
    )
    forged_payloads.append(forged_order)

    forged_config = json.loads(json.dumps(payload))
    forged_config["config"]["max_latest_source_review_age_seconds_watch"] = (
        "3600.000000"
    )
    forged_payloads.append(forged_config)

    for forged in forged_payloads:
        with pytest.raises(ValueError):
            module.validate_research_strategy_domain_source_review_decay_floor_public_payload(
                resign_payload(forged),
            )


def test_stable_digest_tie_break_final_dataclasses_and_private_surfaces() -> None:
    module = api()
    same_status_rows = (
        review_input(
            module,
            "source-review-c",
            "domain-review-c",
            review_quality_score=d("0.600000"),
        ),
        review_input(
            module,
            "source-review-a",
            "domain-review-b",
            review_quality_score=d("0.600000"),
        ),
        review_input(
            module,
            "source-review-a",
            "domain-review-a",
            review_quality_score=d("0.600000"),
        ),
    )
    first = build_report(module, *same_status_rows)
    second = build_report(module, *reversed(same_status_rows))
    expected_keys = tuple(
        sorted(
            (
                (digest(row.source_review_key), digest(row.domain_review_key))
                for row in same_status_rows
            ),
        ),
    )
    assert tuple(
        (row.source_review_digest, row.domain_review_digest) for row in first.rows
    ) == expected_keys
    assert first == second

    for public_type in (
        module.ResearchStrategyDomainSourceReviewDecayFloorConfig,
        module.ResearchStrategyDomainSourceReviewDecayFloorInput,
        module.ResearchStrategyDomainSourceReviewDecayFloorRow,
        module.ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount,
        module.ResearchStrategyDomainSourceReviewDecayFloorReport,
    ):
        with pytest.raises(TypeError):
            type(f"Unsafe{public_type.__name__}", (public_type,), {})

    payload = json.loads(
        json.dumps(
            module.research_strategy_domain_source_review_decay_floor_report_payload(
                first,
            ),
        ),
    )
    for private_field in (
        "team_id",
        "team_name",
        "reviewer_id",
        "source_name",
        "source_review_key",
        "domain_review_key",
    ):
        forged = json.loads(json.dumps(payload))
        forged[private_field] = "private-team-source"
        with pytest.raises(ValueError, match="unsafe public payload text"):
            module.validate_research_strategy_domain_source_review_decay_floor_public_payload(
                resign_payload(forged),
            )


def assert_no_public_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_numeric_values(item)
        return
    assert not isinstance(value, (Decimal, float))


def assert_public_payload_has_no_private_surfaces(payload: object) -> None:
    rendered = json.dumps(payload, sort_keys=True).lower()
    for fragment in (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "https://",
        "http://",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "trading",
        "sizing",
        "recommendation",
    ):
        assert fragment not in rendered
