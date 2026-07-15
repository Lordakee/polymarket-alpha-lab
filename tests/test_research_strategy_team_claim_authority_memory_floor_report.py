from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_team_claim_authority_memory_floor_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_team_claim_authority_memory_floor_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")

RAW_PRIVATE_VALUES = (
    "candi" + "date-alpha",
    "mar" + "ket-resolution-yes",
    "https://example.test/private-resolution?to" + "ken=secret-alpha",
    "raw " + "source " + "text says final outcome is yes",
    "postgres://user:pass@example.test:5432/private_claims",
    "resolution_claim_" + "table",
)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            "research-strategy-team-claim-authority-memory-floor-report-v0"
        ),
        "min_pass_team_authority_score": d("0.800000"),
        "min_watch_team_authority_score": d("0.550000"),
        "min_pass_claim_memory_score": d("0.750000"),
        "min_watch_claim_memory_score": d("0.500000"),
        "max_pass_memory_age_seconds": d("86400.000000"),
        "max_watch_memory_age_seconds": d("259200.000000"),
        "min_pass_cross_team_support_count": d("2.000000"),
        "min_watch_cross_team_support_count": d("1.000000"),
        "max_pass_contradiction_pressure": d("0.150000"),
        "max_watch_contradiction_pressure": d("0.350000"),
        "team_authority_weight": d("0.300000"),
        "claim_memory_weight": d("0.300000"),
        "freshness_weight": d("0.150000"),
        "support_weight": d("0.150000"),
        "contradiction_relief_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchStrategyTeamClaimAuthorityMemoryFloorConfig(**values)


def input_row(
    private_subject_ref: str = RAW_PRIVATE_VALUES[0],
    private_evidence_ref: str = (
        f"{RAW_PRIVATE_VALUES[2]}; {RAW_PRIVATE_VALUES[3]}; {RAW_PRIVATE_VALUES[4]}"
    ),
    private_memory_ref: str = f"{RAW_PRIVATE_VALUES[1]}; {RAW_PRIVATE_VALUES[5]}",
    public_team_bucket: str = "resolution-team",
    public_claim_bucket: str = "resolution-claim",
    *,
    team_authority_score: Decimal = d("0.900000"),
    claim_memory_score: Decimal = d("0.880000"),
    memory_age_seconds: Decimal = d("21600.000000"),
    cross_team_support_count: Decimal = d("3.000000"),
    contradiction_pressure: Decimal = d("0.050000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchStrategyTeamClaimAuthorityMemoryFloorInput(
        private_subject_ref=private_subject_ref,
        private_evidence_ref=private_evidence_ref,
        private_memory_ref=private_memory_ref,
        public_team_bucket=public_team_bucket,
        public_claim_bucket=public_claim_bucket,
        team_authority_score=team_authority_score,
        claim_memory_score=claim_memory_score,
        memory_age_seconds=memory_age_seconds,
        cross_team_support_count=cross_team_support_count,
        contradiction_pressure=contradiction_pressure,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: object,
    config: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_strategy_team_claim_authority_memory_floor_report(
        items,
        config=config if config is not None else cfg(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = deepcopy(payload)
    resigned["derived_validation_digest"] = canonical_digest(resigned)
    return resigned


def test_empty_input_blocks_with_report_only_digest_and_decimal_payload() -> None:
    module = api()
    result = report()

    assert type(result) is module.ResearchStrategyTeamClaimAuthorityMemoryFloorReport
    assert is_dataclass(result)
    assert module.TEAM_CLAIM_AUTHORITY_MEMORY_FLOOR_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "research-strategy-team-claim-authority-memory-floor-report-v0"
    )
    assert result.row_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.average_authority_memory_floor_score is None
    assert result.min_team_authority_score == ZERO
    assert result.min_claim_memory_score == ZERO
    assert result.max_memory_age_seconds == ZERO
    assert result.max_contradiction_pressure == ZERO
    assert result.status == "block"
    assert result.reason_codes == ("no_team_claim_authority_memory_floor_inputs",)
    assert result.reason_code_counts == (
        module.ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount(
            reason_code="no_team_claim_authority_memory_floor_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = module.research_strategy_team_claim_authority_memory_floor_report_payload(
        result,
    )
    assert payload["status"] == "block"
    assert payload["rows"] == []
    assert payload["row_count"] == "0.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.research_strategy_team_claim_authority_memory_floor_report_digest(
        result,
    ) == payload["derived_validation_digest"]
    assert module.validate_research_strategy_team_claim_authority_memory_floor_report_payload(
        payload,
    )
    assert_no_public_numbers(payload)
    assert_no_forbidden_public_surface(payload)


def test_team_claim_authority_floor_scores_pass_watch_and_block_rows() -> None:
    result = report(
        input_row(
            private_subject_ref=RAW_PRIVATE_VALUES[0] + "-watch",
            public_team_bucket="team-beta",
            public_claim_bucket="claim-watch",
            team_authority_score=d("0.650000"),
            claim_memory_score=d("0.700000"),
            memory_age_seconds=d("172800.000000"),
            cross_team_support_count=d("1.000000"),
            contradiction_pressure=d("0.250000"),
            reason_codes=("manual_watch",),
        ),
        input_row(
            private_subject_ref=RAW_PRIVATE_VALUES[0] + "-block",
            public_team_bucket="team-alpha",
            public_claim_bucket="claim-block",
            team_authority_score=d("0.400000"),
            claim_memory_score=d("0.450000"),
            memory_age_seconds=d("400000.000000"),
            cross_team_support_count=d("0.000000"),
            contradiction_pressure=d("0.600000"),
            reason_codes=("manual_block",),
        ),
        input_row(
            private_subject_ref=RAW_PRIVATE_VALUES[0] + "-pass",
            public_team_bucket="team-gamma",
            public_claim_bucket="claim-pass",
            reason_codes=("analyst_checked",),
        ),
    )

    assert result.row_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.average_authority_memory_floor_score == d("0.605500")
    assert result.min_team_authority_score == d("0.400000")
    assert result.min_claim_memory_score == d("0.450000")
    assert result.max_memory_age_seconds == d("400000.000000")
    assert result.max_contradiction_pressure == d("0.600000")
    assert result.status == "block"
    assert result.reason_codes == (
        "team_claim_authority_memory_floor_block",
        "team_authority_score_block",
        "claim_memory_score_block",
        "memory_age_block",
        "cross_team_support_count_block",
        "contradiction_pressure_block",
        "team_claim_authority_memory_floor_watch",
        "team_authority_score_watch",
        "claim_memory_score_watch",
        "memory_age_watch",
        "cross_team_support_count_watch",
        "contradiction_pressure_watch",
    )

    block_row, watch_row, pass_row = result.rows
    assert block_row.status == "block"
    assert block_row.public_team_bucket == "team-alpha"
    assert block_row.authority_memory_floor_score == d("0.295000")
    assert block_row.memory_freshness_score == ZERO
    assert block_row.support_score == ZERO
    assert block_row.reason_codes == (
        "team_claim_authority_memory_floor_block",
        "team_authority_score_block",
        "claim_memory_score_block",
        "memory_age_block",
        "cross_team_support_count_block",
        "contradiction_pressure_block",
        "input_manual_block",
    )
    assert watch_row.status == "watch"
    assert watch_row.authority_memory_floor_score == d("0.605000")
    assert watch_row.memory_freshness_score == d("0.333333")
    assert watch_row.support_score == d("0.500000")
    assert watch_row.reason_codes == (
        "team_claim_authority_memory_floor_watch",
        "team_authority_score_watch",
        "claim_memory_score_watch",
        "memory_age_watch",
        "cross_team_support_count_watch",
        "contradiction_pressure_watch",
        "input_manual_watch",
    )
    assert pass_row.status == "pass"
    assert pass_row.authority_memory_floor_score == d("0.916500")
    assert pass_row.memory_freshness_score == d("0.916667")
    assert pass_row.support_score == d("1.000000")
    assert pass_row.reason_codes == (
        "team_claim_authority_memory_floor_pass",
        "input_analyst_checked",
    )
    assert_public_numeric_values_are_decimal(result)


def test_payload_is_deterministic_redacted_and_digest_validated() -> None:
    module = api()
    first = report(
        input_row(
            private_subject_ref=RAW_PRIVATE_VALUES[0] + "-z",
            public_team_bucket="team-zeta",
            public_claim_bucket="claim-zeta",
            reason_codes=("zeta", "alpha"),
        ),
        input_row(
            private_subject_ref=RAW_PRIVATE_VALUES[0] + "-a",
            public_team_bucket="team-alpha",
            public_claim_bucket="claim-alpha",
        ),
    )
    second = report(
        input_row(
            private_subject_ref=RAW_PRIVATE_VALUES[0] + "-a",
            public_team_bucket="team-alpha",
            public_claim_bucket="claim-alpha",
        ),
        input_row(
            private_subject_ref=RAW_PRIVATE_VALUES[0] + "-z",
            public_team_bucket="team-zeta",
            public_claim_bucket="claim-zeta",
            reason_codes=("alpha", "zeta"),
        ),
    )

    first_payload = (
        module.research_strategy_team_claim_authority_memory_floor_report_payload(first)
    )
    second_payload = (
        module.research_strategy_team_claim_authority_memory_floor_report_payload(second)
    )
    encoded = json.dumps(first_payload, sort_keys=True).lower()

    assert first_payload == second_payload
    assert module.research_strategy_team_claim_authority_memory_floor_report_digest(
        first,
    ) == module.research_strategy_team_claim_authority_memory_floor_report_digest(second)
    assert len(
        module.research_strategy_team_claim_authority_memory_floor_report_digest(first),
    ) == 64
    int(module.research_strategy_team_claim_authority_memory_floor_report_digest(first), 16)
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert first_payload["rows"][0]["row_label"].startswith(
        "redacted-team-claim-authority-memory-floor-",
    )
    assert first_payload["rows"][0]["authority_memory_floor_score"] == "0.916500"
    assert first_payload["rows"][0]["cross_team_support_count"] == "3.000000"
    assert_no_public_numbers(first_payload)
    assert_no_forbidden_public_surface(first_payload)
    for private_value in RAW_PRIVATE_VALUES:
        assert private_value.lower() not in encoded

    tampered = replace(first)
    object.__setattr__(tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_team_claim_authority_memory_floor_report_payload(
            tampered,
        )

    tampered_payload = dict(first_payload)
    tampered_payload["status"] = "block"
    assert not module.validate_research_strategy_team_claim_authority_memory_floor_report_payload(
        tampered_payload,
    )


def test_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    module = api()
    sample_config = cfg()
    sample_input = input_row()
    sample_report = report(sample_input)
    multi_row_report = report(
        input_row(private_subject_ref=RAW_PRIVATE_VALUES[0] + "-a", public_team_bucket="a"),
        input_row(private_subject_ref=RAW_PRIVATE_VALUES[0] + "-b", public_team_bucket="b"),
    )
    sample_row = sample_report.rows[0]

    for value in (
        sample_config,
        sample_input,
        sample_report,
        sample_row,
        *sample_report.reason_code_counts,
    ):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        assert_public_numeric_values_are_decimal(value)

    with pytest.raises(FrozenInstanceError):
        sample_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        sample_row.authority_memory_floor_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="team_authority_weight"):
        cfg(team_authority_weight=0.3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="claim_memory_weight"):
        cfg(claim_memory_weight=DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="private_subject_ref"):
        input_row(private_subject_ref="")
    with pytest.raises(ValueError, match="public_team_bucket"):
        input_row(public_team_bucket="https://example.invalid/raw")
    with pytest.raises(ValueError, match="team_authority_score"):
        input_row(team_authority_score=0.88)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cross_team_support_count"):
        input_row(cross_team_support_count=d("1.500000"))
    with pytest.raises(ValueError, match="contradiction_pressure"):
        input_row(contradiction_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(), paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(sample_row, status="blocked")
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(multi_row_report, rows=tuple(reversed(multi_row_report.rows)))
    with pytest.raises(ValueError, match="readonly"):
        replace(sample_report, readonly=False)


def test_payload_validation_rejects_raw_numbers_and_public_raw_terms() -> None:
    module = api()
    payload = module.research_strategy_team_claim_authority_memory_floor_report_payload(
        report(input_row()),
    )

    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_team_claim_authority_memory_floor_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_team_claim_authority_memory_floor_report_payload(
            {**payload, "raw_candidate": RAW_PRIVATE_VALUES[0]},
        )
    with pytest.raises(ValueError, match="Decimal\\|string"):
        module.research_strategy_team_claim_authority_memory_floor_report_payload(
            {**payload, "row_count": 1.0},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_team_claim_authority_memory_floor_report_payload(
            {**payload, "row_count": "4.000000"},
        )
    assert not module.validate_research_strategy_team_claim_authority_memory_floor_report_payload(
        {**payload, "row_count": "4.000000"},
    )


def test_public_dataclasses_are_slotted_final_and_payload_has_exact_schema() -> None:
    module = api()
    sample_input = input_row()
    sample_report = report(sample_input)
    record_types = (
        module.ResearchStrategyTeamClaimAuthorityMemoryFloorConfig,
        module.ResearchStrategyTeamClaimAuthorityMemoryFloorInput,
        module.ResearchStrategyTeamClaimAuthorityMemoryFloorRow,
        module.ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount,
        module.ResearchStrategyTeamClaimAuthorityMemoryFloorReport,
    )

    for record_type in record_types:
        assert record_type.__dataclass_params__.frozen is True
        assert "__dict__" not in record_type.__dict__
        with pytest.raises(TypeError):
            type("ForbiddenSubclass", (record_type,), {})

    payload = module.research_strategy_team_claim_authority_memory_floor_report_payload(
        sample_report,
    )
    assert "config" in payload

    extra_report_field = deepcopy(payload)
    extra_report_field["safe_extra"] = "value"
    missing_report_field = deepcopy(payload)
    missing_report_field.pop("status")
    extra_row_field = deepcopy(payload)
    extra_row_field["rows"][0]["safe_extra"] = "value"
    missing_row_field = deepcopy(payload)
    missing_row_field["rows"][0].pop("status")

    for forged in (
        extra_report_field,
        missing_report_field,
        extra_row_field,
        missing_row_field,
    ):
        resigned = resign_payload(forged)
        with pytest.raises(ValueError, match="schema"):
            module.research_strategy_team_claim_authority_memory_floor_report_payload(
                resigned,
            )
        assert not module.validate_research_strategy_team_claim_authority_memory_floor_report_payload(
            resigned,
        )


def test_signed_zero_and_noncanonical_utc_are_rejected_at_all_public_boundaries() -> None:
    module = api()

    with pytest.raises(ValueError, match="signed zero"):
        input_row(team_authority_score=d("-0.000000"))

    payload = module.research_strategy_team_claim_authority_memory_floor_report_payload(
        report(input_row()),
    )
    signed_zero = deepcopy(payload)
    signed_zero["rows"][0]["team_authority_score"] = "-0.000000"
    signed_zero = resign_payload(signed_zero)
    with pytest.raises(ValueError, match="signed zero"):
        module.research_strategy_team_claim_authority_memory_floor_report_payload(
            signed_zero,
        )
    assert not module.validate_research_strategy_team_claim_authority_memory_floor_report_payload(
        signed_zero,
    )

    noncanonical_datetime = deepcopy(payload)
    noncanonical_datetime["generated_at"] = "2026-07-09T12:00:00Z"
    noncanonical_datetime = resign_payload(noncanonical_datetime)
    with pytest.raises(ValueError, match="canonical UTC"):
        module.research_strategy_team_claim_authority_memory_floor_report_payload(
            noncanonical_datetime,
        )


def test_builder_and_resigned_payload_revalidate_config_input_and_derived_fields() -> None:
    module = api()

    tampered_config = cfg()
    object.__setattr__(tampered_config, "min_pass_team_authority_score", d("0.8000004"))
    with pytest.raises(ValueError, match="config"):
        report(input_row(), config=tampered_config)

    tampered_input = input_row()
    object.__setattr__(tampered_input, "team_authority_score", d("0.9000004"))
    with pytest.raises(ValueError, match="input"):
        report(tampered_input)

    payload = module.research_strategy_team_claim_authority_memory_floor_report_payload(
        report(input_row()),
    )
    forged_derived = deepcopy(payload)
    forged_derived["rows"][0]["authority_memory_floor_score"] = "0.123456"
    forged_derived["average_authority_memory_floor_score"] = "0.123456"
    forged_derived = resign_payload(forged_derived)
    with pytest.raises(ValueError, match="match"):
        module.research_strategy_team_claim_authority_memory_floor_report_payload(
            forged_derived,
        )
    assert not module.validate_research_strategy_team_claim_authority_memory_floor_report_payload(
        forged_derived,
    )


def test_module_is_report_only_and_has_no_effectful_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    lowered = MODULE_PATH.read_text(encoding="utf-8").lower()

    def joined(*pieces: str) -> str:
        return "".join(pieces)

    banned_imports = {
        "asyncio",
        "http",
        "httpx",
        "os",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    banned_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "submit",
        "post",
        "send",
        "login",
        "place_order",
        "cancel",
    }
    banned_attributes = banned_calls | {"commit", "rollback", "session"}
    forbidden_patterns = (
        r"\b" + joined("d", "b") + r"\b",
        r"\b" + joined("data", "base") + r"\b",
        r"\b" + joined("net", "work") + r"\b",
        r"\b" + joined("wal", "let") + r"\b",
        r"\b" + joined("auth") + r"\b",
        r"\b" + joined("or", "der") + r"\b",
        r"\b" + joined("live", r"\s+", "trading") + r"\b",
        r"\b" + joined("si", "zing") + r"\b",
        r"\b" + joined("recommen", "dation") + r"\b",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes

    assert [pattern for pattern in forbidden_patterns if re.search(pattern, lowered)] == []


def test_public_api_is_exactly_the_report_only_surface() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_TEAM_CLAIM_AUTHORITY_MEMORY_FLOOR_REPORT_CONFIG_VERSION",
        "TEAM_CLAIM_AUTHORITY_MEMORY_FLOOR_STATUSES",
        "ResearchStrategyTeamClaimAuthorityMemoryFloorConfig",
        "ResearchStrategyTeamClaimAuthorityMemoryFloorInput",
        "ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount",
        "ResearchStrategyTeamClaimAuthorityMemoryFloorReport",
        "ResearchStrategyTeamClaimAuthorityMemoryFloorRow",
        "build_research_strategy_team_claim_authority_memory_floor_report",
        "research_strategy_team_claim_authority_memory_floor_report_digest",
        "research_strategy_team_claim_authority_memory_floor_report_payload",
        "validate_research_strategy_team_claim_authority_memory_floor_report_payload",
    )


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


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
        "private_",
        "secret",
    )
    assert all(fragment not in rendered for fragment in forbidden_fragments)
