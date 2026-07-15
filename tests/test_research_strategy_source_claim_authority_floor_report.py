from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_source_claim_authority_floor_report import (
    DEFAULT_RESEARCH_STRATEGY_SOURCE_CLAIM_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION,
    SOURCE_CLAIM_AUTHORITY_FLOOR_STATUSES,
    ResearchStrategySourceClaimAuthorityFloorConfig,
    ResearchStrategySourceClaimAuthorityFloorInput,
    ResearchStrategySourceClaimAuthorityFloorReasonCodeCount,
    ResearchStrategySourceClaimAuthorityFloorReport,
    ResearchStrategySourceClaimAuthorityFloorRow,
    build_research_strategy_source_claim_authority_floor_report,
    research_strategy_source_claim_authority_floor_report_digest,
    research_strategy_source_claim_authority_floor_report_payload,
    validate_research_strategy_source_claim_authority_floor_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_source_claim_authority_floor_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategySourceClaimAuthorityFloorConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_SOURCE_CLAIM_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION
        ),
        "min_pass_claim_strength": d("0.800000"),
        "min_watch_claim_strength": d("0.550000"),
        "min_pass_authority_score": d("0.800000"),
        "min_watch_authority_score": d("0.550000"),
        "min_pass_corroboration_score": d("0.750000"),
        "min_watch_corroboration_score": d("0.500000"),
        "min_pass_freshness_score": d("0.700000"),
        "min_watch_freshness_score": d("0.500000"),
        "max_pass_contradiction_pressure": d("0.150000"),
        "max_watch_contradiction_pressure": d("0.350000"),
        "claim_strength_weight": d("0.300000"),
        "authority_score_weight": d("0.300000"),
        "corroboration_weight": d("0.150000"),
        "freshness_weight": d("0.150000"),
        "contradiction_relief_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchStrategySourceClaimAuthorityFloorConfig(**values)


def input_row(
    private_reference: str = "candidate://secret-alpha?token=not-public",
    public_research_bucket: str = "resolution-claims",
    *,
    claim_strength: Decimal = d("0.900000"),
    authority_score: Decimal = d("0.920000"),
    corroboration_score: Decimal = d("0.900000"),
    freshness_score: Decimal = d("0.850000"),
    contradiction_pressure: Decimal = d("0.050000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategySourceClaimAuthorityFloorInput:
    return ResearchStrategySourceClaimAuthorityFloorInput(
        private_reference=private_reference,
        public_research_bucket=public_research_bucket,
        claim_strength=claim_strength,
        authority_score=authority_score,
        corroboration_score=corroboration_score,
        freshness_score=freshness_score,
        contradiction_pressure=contradiction_pressure,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchStrategySourceClaimAuthorityFloorInput,
    cfg: ResearchStrategySourceClaimAuthorityFloorConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategySourceClaimAuthorityFloorReport:
    return build_research_strategy_source_claim_authority_floor_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def test_empty_input_blocks_with_report_only_digest_and_decimal_payload() -> None:
    floor_report = report()

    assert type(floor_report) is ResearchStrategySourceClaimAuthorityFloorReport
    assert is_dataclass(floor_report)
    assert SOURCE_CLAIM_AUTHORITY_FLOOR_STATUSES == ("pass", "watch", "block")
    assert floor_report.generated_at == GENERATED_AT
    assert (
        floor_report.config_version
        == "research-strategy-source-claim-authority-floor-report-v0"
    )
    assert floor_report.input_count == ZERO
    assert floor_report.pass_count == ZERO
    assert floor_report.watch_count == ZERO
    assert floor_report.block_count == ZERO
    assert floor_report.average_authority_floor_score is None
    assert floor_report.min_claim_strength == ZERO
    assert floor_report.min_authority_score == ZERO
    assert floor_report.min_corroboration_score == ZERO
    assert floor_report.min_freshness_score == ZERO
    assert floor_report.max_contradiction_pressure == ZERO
    assert floor_report.status == "block"
    assert floor_report.reason_codes == ("no_source_claim_authority_inputs",)
    assert floor_report.reason_code_counts == (
        ResearchStrategySourceClaimAuthorityFloorReasonCodeCount(
            reason_code="no_source_claim_authority_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert floor_report.rows == ()
    assert floor_report.paper_only is True
    assert floor_report.report_only is True
    assert floor_report.readonly is True

    payload = research_strategy_source_claim_authority_floor_report_payload(floor_report)
    assert payload == floor_report.payload
    assert payload["status"] == "block"
    assert payload["rows"] == []
    assert payload["input_count"] == "0.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert (
        research_strategy_source_claim_authority_floor_report_digest(floor_report)
        == payload["derived_validation_digest"]
    )
    assert validate_research_strategy_source_claim_authority_floor_report_payload(payload)
    assert_no_public_numbers(payload)
    assert_no_forbidden_public_surface(payload)


def test_source_claim_authority_floor_scores_pass_watch_and_block_rows() -> None:
    floor_report = report(
        input_row(
            "candidate://secret-watch?source_url=https://example.invalid",
            "resolution-claims",
            claim_strength=d("0.650000"),
            authority_score=d("0.700000"),
            corroboration_score=d("0.600000"),
            freshness_score=d("0.600000"),
            contradiction_pressure=d("0.250000"),
        ),
        input_row(
            "candidate://secret-block?dsn=postgres://hidden/table",
            "breaking-update-claims",
            claim_strength=d("0.400000"),
            authority_score=d("0.450000"),
            corroboration_score=d("0.250000"),
            freshness_score=d("0.300000"),
            contradiction_pressure=d("0.600000"),
            reason_codes=("manual_escalation",),
        ),
        input_row(
            "candidate://secret-pass?raw_text=do-not-leak",
            "resolution-claims",
            reason_codes=("analyst_checked",),
        ),
    )

    assert floor_report.input_count == d("3.000000")
    assert floor_report.pass_count == d("1.000000")
    assert floor_report.watch_count == d("1.000000")
    assert floor_report.block_count == d("1.000000")
    assert floor_report.average_authority_floor_score == d("0.647000")
    assert floor_report.min_claim_strength == d("0.400000")
    assert floor_report.min_authority_score == d("0.450000")
    assert floor_report.min_corroboration_score == d("0.250000")
    assert floor_report.min_freshness_score == d("0.300000")
    assert floor_report.max_contradiction_pressure == d("0.600000")
    assert floor_report.status == "block"
    assert floor_report.reason_codes == (
        "source_claim_authority_floor_block",
        "claim_strength_block",
        "authority_score_block",
        "corroboration_score_block",
        "freshness_score_block",
        "contradiction_pressure_block",
        "source_claim_authority_floor_watch",
        "claim_strength_watch",
        "authority_score_watch",
        "corroboration_score_watch",
        "freshness_score_watch",
        "contradiction_pressure_watch",
    )

    block_row, pass_row, watch_row = floor_report.rows
    assert type(block_row) is ResearchStrategySourceClaimAuthorityFloorRow
    assert tuple(row.public_research_bucket for row in floor_report.rows) == (
        "breaking-update-claims",
        "resolution-claims",
        "resolution-claims",
    )
    assert block_row.authority_floor_score == d("0.377500")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "source_claim_authority_floor_block",
        "claim_strength_block",
        "authority_score_block",
        "corroboration_score_block",
        "freshness_score_block",
        "contradiction_pressure_block",
        "input_manual_escalation",
    )
    assert pass_row.authority_floor_score == d("0.903500")
    assert pass_row.status == "pass"
    assert "source_claim_authority_floor_pass" in pass_row.reason_codes
    assert "input_analyst_checked" in pass_row.reason_codes
    assert watch_row.authority_floor_score == d("0.660000")
    assert watch_row.status == "watch"
    assert "claim_strength_watch" in watch_row.reason_codes
    assert "authority_score_watch" in watch_row.reason_codes


def test_payload_is_deterministic_redacted_and_digest_validated() -> None:
    first = report(
        input_row(
            "candidate://secret-z?token=hidden",
            "z-bucket",
            reason_codes=("zeta", "alpha"),
        ),
        input_row("candidate://secret-a?market=hidden", "a-bucket"),
    )
    second = report(
        input_row("candidate://secret-a?market=hidden", "a-bucket"),
        input_row(
            "candidate://secret-z?token=hidden",
            "z-bucket",
            reason_codes=("alpha", "zeta"),
        ),
    )

    first_payload = research_strategy_source_claim_authority_floor_report_payload(first)
    second_payload = research_strategy_source_claim_authority_floor_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert research_strategy_source_claim_authority_floor_report_digest(first) == (
        research_strategy_source_claim_authority_floor_report_digest(second)
    )
    assert len(research_strategy_source_claim_authority_floor_report_digest(first)) == 64
    int(research_strategy_source_claim_authority_floor_report_digest(first), 16)
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert first_payload["rows"][0]["row_label"].startswith(
        "redacted-source-claim-authority-floor-",
    )
    assert first_payload["rows"][0]["authority_floor_score"] == "0.903500"
    assert first_payload["rows"][0]["claim_strength"] == "0.900000"
    assert ": 0." not in encoded
    assert "candidate://secret" not in encoded
    assert "token=hidden" not in encoded
    assert "market=hidden" not in encoded
    assert "secret" not in repr(asdict(first)).casefold()
    assert_no_public_numbers(first_payload)
    assert_no_forbidden_public_surface(first_payload)

    tampered = replace(first)
    object.__setattr__(tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_source_claim_authority_floor_report_payload(tampered)

    unsigned = dict(first_payload)
    unsigned["status"] = "block"
    assert not validate_research_strategy_source_claim_authority_floor_report_payload(
        unsigned,
    )

    forged = dict(first_payload)
    forged["status"] = "hold"
    forged["derived_validation_digest"] = canonical_digest(forged)
    assert not validate_research_strategy_source_claim_authority_floor_report_payload(
        forged,
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_inconsistent_report() -> None:
    populated = report(input_row())

    for value in (
        config(),
        input_row(),
        populated,
        *populated.rows,
        *populated.reason_code_counts,
    ):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_score",
                    "_strength",
                    "_pressure",
                    "_ratio",
                    "_weight",
                ),
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].authority_floor_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                DEFAULT_RESEARCH_STRATEGY_SOURCE_CLAIM_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="claim_strength_weight"):
        config(claim_strength_weight=0.3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_score_weight"):
        config(authority_score_weight=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="authority floor weights"):
        config(claim_strength_weight=d("0.350000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 9, 15, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=_DatetimeSubclass(2026, 7, 9, 15, 0, tzinfo=UTC))
    assert (
        report(input_row(), generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5)))).generated_at
        == GENERATED_AT
    )
    with pytest.raises(ValueError, match="private_reference"):
        input_row("")
    with pytest.raises(ValueError, match="private_reference"):
        input_row(_StringSubclass("secret"))
    with pytest.raises(ValueError, match="public_research_bucket"):
        input_row(public_research_bucket="https://example.invalid/raw")
    with pytest.raises(ValueError, match="claim_strength"):
        input_row(claim_strength=0.88)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="corroboration_score"):
        input_row(corroboration_score=d("1.100000"))
    with pytest.raises(ValueError, match="contradiction_pressure"):
        input_row(contradiction_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(), paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(populated.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)


def test_public_dataclasses_are_frozen_slotted_and_final() -> None:
    populated = report(input_row())
    values = (
        config(),
        input_row(),
        populated.rows[0],
        populated.reason_code_counts[0],
        populated,
    )

    for value in values:
        assert not hasattr(value, "__dict__")
        assert hasattr(type(value), "__slots__")
        with pytest.raises(FrozenInstanceError):
            setattr(value, "paper_only", False)

    for cls in (
        ResearchStrategySourceClaimAuthorityFloorConfig,
        ResearchStrategySourceClaimAuthorityFloorInput,
        ResearchStrategySourceClaimAuthorityFloorRow,
        ResearchStrategySourceClaimAuthorityFloorReasonCodeCount,
        ResearchStrategySourceClaimAuthorityFloorReport,
    ):
        with pytest.raises(TypeError, match="may not be subclassed|does not support subclassing"):
            type("DerivedPublicDataclass", (cls,), {})


def test_decimal_bounds_are_checked_before_quantization_and_signed_zero_is_rejected() -> None:
    for field_name, bad_value in (
        ("claim_strength", d("1.0000004")),
        ("authority_score", d("-0.0000004")),
        ("corroboration_score", d("-0.000000")),
    ):
        with pytest.raises(ValueError, match=field_name):
            input_row(**{field_name: bad_value})

    with pytest.raises(ValueError, match="min_pass_claim_strength"):
        config(min_pass_claim_strength=d("1.0000004"))
    with pytest.raises(ValueError, match="min_watch_claim_strength"):
        config(min_watch_claim_strength=d("-0.0000004"))


def test_direct_report_rejects_unsupported_config_version_after_resigning() -> None:
    populated = report(input_row())

    with pytest.raises(ValueError, match="config_version"):
        replace(
            populated,
            config_version="unsupported-config-v1",
            derived_validation_digest="",
        )


def test_builder_revalidates_supplied_config_and_input_instances() -> None:
    tampered_config = config()
    object.__setattr__(tampered_config, "claim_strength_weight", 0.3)
    with pytest.raises(ValueError, match="claim_strength_weight"):
        report(input_row(), cfg=tampered_config)

    tampered_input = input_row()
    object.__setattr__(tampered_input, "claim_strength", 0.88)
    with pytest.raises(ValueError, match="claim_strength"):
        report(tampered_input)


def test_report_payload_rejects_a_directly_tampered_report_even_after_resigning() -> None:
    populated = report(input_row())
    tampered = replace(populated)
    object.__setattr__(tampered, "status", "block")
    resigned = research_strategy_source_claim_authority_floor_report_payload(populated)
    resigned["status"] = "block"
    object.__setattr__(tampered, "derived_validation_digest", canonical_digest(resigned))

    with pytest.raises(ValueError, match="status"):
        research_strategy_source_claim_authority_floor_report_payload(tampered)


@pytest.mark.parametrize(
    ("field_path", "value", "message"),
    (
        (("status",), "block", "status"),
        (("pass_count",), "0.000000", "pass_count"),
        (("rows", 0, "status"), "block", "status"),
        (("rows", 0, "reason_codes"), ["source_claim_authority_floor_block"], "rows"),
        (("reason_code_counts", 0, "count"), "2.000000", "reason_code_counts"),
    ),
)
def test_resigned_payload_revalidates_derived_report_invariants(
    field_path: tuple[object, ...],
    value: object,
    message: str,
) -> None:
    payload = json.loads(
        json.dumps(research_strategy_source_claim_authority_floor_report_payload(report(input_row())))
    )
    target: Any = payload
    for part in field_path[:-1]:
        target = target[part]
    target[field_path[-1]] = value
    payload["derived_validation_digest"] = canonical_digest(payload)

    assert not validate_research_strategy_source_claim_authority_floor_report_payload(payload), message


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("config_version", "other-config-v1"),
        ("input_count", "01.000000"),
        ("generated_at", "2026-07-09T10:00:00-05:00"),
    ),
)
def test_resigned_payload_rejects_noncanonical_or_unsupported_top_level_values(
    field_name: str,
    value: str,
) -> None:
    payload = json.loads(
        json.dumps(research_strategy_source_claim_authority_floor_report_payload(report(input_row())))
    )
    payload[field_name] = value
    payload["derived_validation_digest"] = canonical_digest(payload)

    assert not validate_research_strategy_source_claim_authority_floor_report_payload(payload)


def test_owned_module_has_no_effectful_terms_or_raw_public_surfaces() -> None:
    text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = text.casefold()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "wallet",
        "private_key",
        "authorization",
        "bearer",
        "api_key",
        "place_order",
        "submit_order",
        "live_trading",
        "position_size",
        "sizing",
        "recommendation",
    )
    forbidden_word_patterns = (
        r"\bdb\b",
        r"\bdatabase\b",
        r"\bnetwork\b",
        r"\bauth\b",
        r"\border\b",
        r"\blive\s+trading\b",
        r"\brecommend\b",
    )

    assert all(term not in lowered for term in forbidden_terms)
    assert not any(re.search(pattern, lowered) for pattern in forbidden_word_patterns)

    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float


def assert_no_public_numbers(value: object) -> None:
    if type(value) in {int, float, Decimal}:
        raise AssertionError(f"public payload leaked raw numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numbers(item)


def assert_no_forbidden_public_surface(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, sort_keys=True).casefold()
    forbidden_fragments = (
        "raw_candidate",
        "candidate://",
        "candidate_ref",
        "market_id",
        "market_slug",
        "market=hidden",
        "source_url",
        "source_text",
        "raw_text",
        "http://",
        "https://",
        "www.",
        "dsn",
        "postgres://",
        "table",
        "token",
        "wallet",
        "private_key",
        "secret",
    )
    assert all(fragment not in rendered for fragment in forbidden_fragments)
