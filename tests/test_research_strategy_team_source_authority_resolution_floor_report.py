from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_team_source_authority_resolution_floor_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_team_source_authority_resolution_floor_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 18, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 17, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")

RAW_PRIVATE_VALUES = (
    "candi" + "date-id:alpha",
    "mar" + "ket-id:123",
    "mar" + "ket-slug:hidden-event",
    "Will the hidden event resolve Yes?",
    "https://example.test/private?to" + "ken=secret",
    "raw " + "source " + "text final outcome",
    "postgres://user:pass@example.test:5432/private",
    "resolution_claim_" + "table",
    "wallet-0xabc",
    "order-id-42",
    "trade-id-99",
)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


class StringSubclass(str):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_AUTHORITY_RESOLUTION_FLOOR_REPORT_CONFIG_VERSION
        ),
        "min_pass_authority_score": d("0.800000"),
        "min_watch_authority_score": d("0.600000"),
        "min_pass_resolution_alignment_score": d("0.750000"),
        "min_watch_resolution_alignment_score": d("0.550000"),
        "min_pass_authority_quorum_count": d("2.000000"),
        "min_watch_authority_quorum_count": d("1.000000"),
        "max_pass_resolution_latency_seconds": d("86400.000000"),
        "max_watch_resolution_latency_seconds": d("259200.000000"),
        "pass_min_resolution_floor_score": d("0.800000"),
        "watch_min_resolution_floor_score": d("0.550000"),
        "authority_weight": d("0.350000"),
        "resolution_alignment_weight": d("0.300000"),
        "authority_quorum_weight": d("0.200000"),
        "latency_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchStrategyTeamSourceAuthorityResolutionFloorConfig(**values)


def input_row(
    private_reference: str = "; ".join(RAW_PRIVATE_VALUES),
    public_team_bucket: str = "resolution-team",
    *,
    authority_score: Decimal = d("0.900000"),
    resolution_alignment_score: Decimal = d("0.850000"),
    authority_quorum_count: Decimal = d("3.000000"),
    resolution_latency_seconds: Decimal = d("3600.000000"),
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchStrategyTeamSourceAuthorityResolutionFloorInput(
        private_reference=private_reference,
        public_team_bucket=public_team_bucket,
        authority_score=authority_score,
        resolution_alignment_score=resolution_alignment_score,
        authority_quorum_count=authority_quorum_count,
        resolution_latency_seconds=resolution_latency_seconds,
        observed_at=observed_at,
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
    return module.build_research_strategy_team_source_authority_resolution_floor_report(
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


def test_empty_input_blocks_with_report_only_digest_and_decimal_payload() -> None:
    module = api()
    result = report()

    assert type(result) is module.ResearchStrategyTeamSourceAuthorityResolutionFloorReport
    assert is_dataclass(result)
    assert module.TEAM_SOURCE_AUTHORITY_RESOLUTION_FLOOR_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert result.generated_at == GENERATED_AT
    assert result.status == "block"
    assert result.row_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.average_resolution_floor_score is None
    assert result.min_authority_score == ZERO
    assert result.min_resolution_alignment_score == ZERO
    assert result.min_authority_quorum_count == ZERO
    assert result.max_resolution_latency_seconds == ZERO
    assert result.reason_codes == ("no_team_source_authority_resolution_floor_inputs",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = (
        module.research_strategy_team_source_authority_resolution_floor_report_payload(
            result,
        )
    )
    assert payload == result.payload
    assert payload["rows"] == []
    assert payload["row_count"] == "0.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert (
        module.research_strategy_team_source_authority_resolution_floor_report_digest(
            result,
        )
        == payload["derived_validation_digest"]
    )
    assert (
        module.validate_research_strategy_team_source_authority_resolution_floor_report_payload(
            payload,
        )
        is True
    )
    assert_no_public_payload_numbers(payload)
    assert_no_forbidden_public_surface(payload)


def test_floor_scores_pass_watch_and_block_rows_deterministically() -> None:
    module = api()
    first = report(
        input_row(
            private_reference=RAW_PRIVATE_VALUES[0] + "-watch",
            public_team_bucket="team-beta",
            authority_score=d("0.650000"),
            resolution_alignment_score=d("0.650000"),
            authority_quorum_count=d("1.000000"),
            resolution_latency_seconds=d("172800.000000"),
            reason_codes=("manual_watch",),
        ),
        input_row(
            private_reference=RAW_PRIVATE_VALUES[0] + "-block",
            public_team_bucket="team-alpha",
            authority_score=d("0.400000"),
            resolution_alignment_score=d("0.450000"),
            authority_quorum_count=d("0.000000"),
            resolution_latency_seconds=d("400000.000000"),
            reason_codes=("manual_block",),
        ),
        input_row(
            private_reference=RAW_PRIVATE_VALUES[0] + "-pass",
            public_team_bucket="team-gamma",
            reason_codes=("analyst_checked",),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )
    second = report(
        input_row(
            private_reference=RAW_PRIVATE_VALUES[0] + "-pass",
            public_team_bucket="team-gamma",
            reason_codes=("analyst_checked",),
        ),
        input_row(
            private_reference=RAW_PRIVATE_VALUES[0] + "-block",
            public_team_bucket="team-alpha",
            authority_score=d("0.400000"),
            resolution_alignment_score=d("0.450000"),
            authority_quorum_count=d("0.000000"),
            resolution_latency_seconds=d("400000.000000"),
            reason_codes=("manual_block",),
        ),
        input_row(
            private_reference=RAW_PRIVATE_VALUES[0] + "-watch",
            public_team_bucket="team-beta",
            authority_score=d("0.650000"),
            resolution_alignment_score=d("0.650000"),
            authority_quorum_count=d("1.000000"),
            resolution_latency_seconds=d("172800.000000"),
            reason_codes=("manual_watch",),
        ),
    )

    assert first.generated_at == GENERATED_AT
    assert first.generated_at.tzinfo is UTC
    assert first.row_count == d("3.000000")
    assert first.pass_count == d("1.000000")
    assert first.watch_count == d("1.000000")
    assert first.block_count == d("1.000000")
    assert first.average_resolution_floor_score == d("0.588472")
    assert first.min_authority_score == d("0.400000")
    assert first.min_resolution_alignment_score == d("0.450000")
    assert first.min_authority_quorum_count == d("0.000000")
    assert first.max_resolution_latency_seconds == d("400000.000000")
    assert first.status == "block"
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert first.reason_codes == (
        "team_source_authority_resolution_floor_block",
        "authority_score_block",
        "resolution_alignment_score_block",
        "authority_quorum_count_block",
        "resolution_latency_block",
        "resolution_floor_score_block",
        "team_source_authority_resolution_floor_watch",
        "authority_score_watch",
        "resolution_alignment_score_watch",
        "authority_quorum_count_watch",
        "resolution_latency_watch",
        "team_source_authority_resolution_floor_pass",
    )

    block_row, watch_row, pass_row = first.rows
    assert block_row.public_team_bucket == "team-alpha"
    assert block_row.resolution_floor_score == d("0.275000")
    assert block_row.latency_score == ZERO
    assert block_row.authority_quorum_score == ZERO
    assert block_row.reason_codes == (
        "team_source_authority_resolution_floor_block",
        "authority_score_block",
        "resolution_alignment_score_block",
        "authority_quorum_count_block",
        "resolution_latency_block",
        "resolution_floor_score_block",
        "input_manual_block",
    )
    assert watch_row.public_team_bucket == "team-beta"
    assert watch_row.resolution_floor_score == d("0.572500")
    assert watch_row.latency_score == d("0.333333")
    assert watch_row.authority_quorum_score == d("0.500000")
    assert watch_row.reason_codes == (
        "team_source_authority_resolution_floor_watch",
        "authority_score_watch",
        "resolution_alignment_score_watch",
        "authority_quorum_count_watch",
        "resolution_latency_watch",
        "input_manual_watch",
    )
    assert pass_row.public_team_bucket == "team-gamma"
    assert pass_row.resolution_floor_score == d("0.917917")
    assert pass_row.latency_score == d("0.986111")
    assert pass_row.authority_quorum_score == d("1.000000")
    assert pass_row.reason_codes == (
        "team_source_authority_resolution_floor_pass",
        "input_analyst_checked",
    )

    first_payload = (
        module.research_strategy_team_source_authority_resolution_floor_report_payload(
            first,
        )
    )
    second_payload = (
        module.research_strategy_team_source_authority_resolution_floor_report_payload(
            second,
        )
    )
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert first_payload["rows"][0]["item_digest"].startswith("sha256:")
    assert first_payload["rows"][0]["resolution_floor_score"] == "0.275000"
    assert json.dumps(
        first_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert_no_public_payload_numbers(first_payload)
    assert_no_forbidden_public_surface(first_payload)
    rendered_payload = json.dumps(first_payload, sort_keys=True).casefold()
    rendered_report = repr(asdict(first)).casefold()
    for private_value in RAW_PRIVATE_VALUES:
        assert private_value.casefold() not in rendered_payload
        assert private_value.casefold() not in rendered_report


def test_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    module = api()
    sample_config = cfg()
    sample_input = input_row()
    sample_report = report(sample_input)
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
        sample_row.resolution_floor_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="authority_weight"):
        cfg(authority_weight=0.35)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="resolution_alignment_weight"):
        cfg(resolution_alignment_weight=DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="config_version"):
        cfg(
            config_version=StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_AUTHORITY_RESOLUTION_FLOOR_REPORT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 9, 18, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            input_row(),
            generated_at=DatetimeSubclass(2026, 7, 9, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=DatetimeSubclass(2026, 7, 9, 17, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report(input_row(observed_at=datetime(2026, 7, 9, 18, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="private_reference"):
        input_row(private_reference="")
    with pytest.raises(ValueError, match="public_team_bucket"):
        input_row(public_team_bucket="https://example.invalid/raw")
    with pytest.raises(ValueError, match="authority_score"):
        input_row(authority_score=0.88)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_quorum_count"):
        input_row(authority_quorum_count=d("1.500000"))
    with pytest.raises(ValueError, match="resolution_latency_seconds"):
        input_row(resolution_latency_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(), paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(sample_row, status="hold")
    with pytest.raises(ValueError, match="resolution_floor_score"):
        replace(sample_row, resolution_floor_score=ZERO)
    with pytest.raises(ValueError, match="readonly"):
        replace(sample_report, readonly=False)
    with pytest.raises(TypeError):
        class _BadRow(  # type: ignore[misc, valid-type]
            module.ResearchStrategyTeamSourceAuthorityResolutionFloorRow,
        ):
            pass


def test_payload_validation_rejects_unsafe_surface_raw_numbers_and_tampering() -> None:
    module = api()
    payload = (
        module.research_strategy_team_source_authority_resolution_floor_report_payload(
            report(input_row()),
        )
    )

    with pytest.raises(TypeError, match="immutable"):
        payload["status"] = "pass"
    with pytest.raises(TypeError, match="immutable"):
        payload["rows"].append({})

    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_team_source_authority_resolution_floor_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_team_source_authority_resolution_floor_report_payload(
            {**payload, "candidate_id": RAW_PRIVATE_VALUES[0]},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_team_source_authority_resolution_floor_report_payload(
            {**payload, "public_note": "source_url=https://example.test"},
        )
    with pytest.raises(ValueError, match="Decimal\\|string"):
        module.research_strategy_team_source_authority_resolution_floor_report_payload(
            {**payload, "row_count": 1.0},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_team_source_authority_resolution_floor_report_payload(
            {**payload, "row_count": "4.000000"},
        )
    assert (
        module.validate_research_strategy_team_source_authority_resolution_floor_report_payload(
            {**payload, "row_count": "4.000000"},
        )
        is False
    )


def test_public_api_and_module_scope_stay_report_only_safe_and_decimal_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_AUTHORITY_RESOLUTION_FLOOR_REPORT_CONFIG_VERSION",
        "TEAM_SOURCE_AUTHORITY_RESOLUTION_FLOOR_STATUSES",
        "ResearchStrategyTeamSourceAuthorityResolutionFloorConfig",
        "ResearchStrategyTeamSourceAuthorityResolutionFloorInput",
        "ResearchStrategyTeamSourceAuthorityResolutionFloorReasonCodeCount",
        "ResearchStrategyTeamSourceAuthorityResolutionFloorReport",
        "ResearchStrategyTeamSourceAuthorityResolutionFloorRow",
        "build_research_strategy_team_source_authority_resolution_floor_report",
        "research_strategy_team_source_authority_resolution_floor_report_digest",
        "research_strategy_team_source_authority_resolution_floor_report_payload",
        "validate_research_strategy_team_source_authority_resolution_floor_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    sample_report = report(input_row())
    unsafe_public_fields = {
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "position_size",
        "recommendation",
    }
    exported_fields = {
        field.name
        for cls in (
            type(cfg()),
            type(input_row()),
            type(sample_report),
            type(sample_report.rows[0]),
            type(sample_report.reason_code_counts[0]),
        )
        for field in fields(cls)
    }
    assert unsafe_public_fields.isdisjoint(exported_fields)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "asyncio",
        "http",
        "httpx",
        "os",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "approve",
        "buy",
        "cancel",
        "connect",
        "execute",
        "executemany",
        "open",
        "patch",
        "place_order",
        "post",
        "put",
        "request",
        "sell",
        "sign_transaction",
        "submit",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_calls

    assert imported_roots.isdisjoint(forbidden_import_roots)
    payload = (
        module.research_strategy_team_source_authority_resolution_floor_report_payload(
            sample_report,
        )
    )
    assert_no_public_payload_numbers(payload)
    assert_no_forbidden_public_surface(payload)


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


def assert_no_public_payload_numbers(value: object) -> None:
    if type(value) in {int, float, Decimal}:
        raise AssertionError(f"public payload leaked raw numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_payload_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_payload_numbers(item)


def assert_no_forbidden_public_surface(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, sort_keys=True).casefold()
    forbidden_fragments = (
        "raw_candidate",
        "candidate_id",
        "candidate://",
        "market_id",
        "market_slug",
        "market_question",
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
        "order_id",
        "trade_id",
        "position_size",
        "recommendation",
        "private_",
        "secret",
    )
    assert all(fragment not in rendered for fragment in forbidden_fragments)
