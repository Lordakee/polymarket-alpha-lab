from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 9, 30, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_signal_redundancy_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


def report_module():
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_signal_redundancy_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    research_theme: str = "macro-policy",
    *,
    signal_family: str = "rate-path",
    evidence_overlap_ratio: str | Decimal = "0.120000",
    catalyst_overlap_ratio: str | Decimal = "0.150000",
    source_class_overlap_ratio: str | Decimal = "0.100000",
    team_confidence_dispersion: str | Decimal = "0.050000",
    resolution_ambiguity_ratio: str | Decimal = "0.080000",
    upstream_reason_codes: tuple[str, ...] = ("public_cross_check",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = report_module()
    return module.ResearchEventSignalRedundancyInput(
        research_theme=research_theme,
        signal_family=signal_family,
        evidence_overlap_ratio=(
            evidence_overlap_ratio
            if isinstance(evidence_overlap_ratio, Decimal)
            else d(evidence_overlap_ratio)
        ),
        catalyst_overlap_ratio=(
            catalyst_overlap_ratio
            if isinstance(catalyst_overlap_ratio, Decimal)
            else d(catalyst_overlap_ratio)
        ),
        source_class_overlap_ratio=(
            source_class_overlap_ratio
            if isinstance(source_class_overlap_ratio, Decimal)
            else d(source_class_overlap_ratio)
        ),
        team_confidence_dispersion=(
            team_confidence_dispersion
            if isinstance(team_confidence_dispersion, Decimal)
            else d(team_confidence_dispersion)
        ),
        resolution_ambiguity_ratio=(
            resolution_ambiguity_ratio
            if isinstance(resolution_ambiguity_ratio, Decimal)
            else d(resolution_ambiguity_ratio)
        ),
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**kwargs: object):
    return report_module().ResearchEventSignalRedundancyConfig(**kwargs)


def report(*rows: object, cfg: object | None = None):
    module = report_module()
    return module.build_research_event_signal_redundancy_report(
        rows,
        config=cfg if cfg is not None else module.ResearchEventSignalRedundancyConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def block_signal():
    return signal(
        "energy-weather",
        signal_family="grid-alerts",
        evidence_overlap_ratio="0.780000",
        catalyst_overlap_ratio="0.760000",
        source_class_overlap_ratio="0.820000",
        team_confidence_dispersion="0.410000",
        resolution_ambiguity_ratio="0.680000",
        upstream_reason_codes=(
            "same_public_documents",
            "same_public_documents",
            "overlapping_timing_window",
        ),
    )


def watch_signal():
    return signal(
        "policy-calendar",
        signal_family="ballot-access",
        evidence_overlap_ratio="0.450000",
        catalyst_overlap_ratio="0.420000",
        source_class_overlap_ratio="0.360000",
        team_confidence_dispersion="0.230000",
        resolution_ambiguity_ratio="0.340000",
        upstream_reason_codes=("parallel_public_filings",),
    )


def test_empty_input_returns_report_only_block_status_with_zero_digest() -> None:
    module = report_module()

    redundancy_report = report()

    assert isinstance(redundancy_report, module.ResearchEventSignalRedundancyReport)
    assert is_dataclass(redundancy_report)
    assert redundancy_report.__dataclass_params__.frozen
    assert redundancy_report.generated_at == GENERATED_AT
    assert redundancy_report.generated_at.tzinfo is UTC
    assert redundancy_report.config_version == "research-event-signal-redundancy-v0"
    assert redundancy_report.redundancy_status == "block"
    assert redundancy_report.recommended_next_step == (
        "block_report_only_research_event_signal_redundancy"
    )
    assert redundancy_report.input_count == d("0.000000")
    assert redundancy_report.row_count == d("0.000000")
    assert redundancy_report.pass_count == d("0.000000")
    assert redundancy_report.watch_count == d("0.000000")
    assert redundancy_report.block_count == d("0.000000")
    assert redundancy_report.redundancy_risk_score == d("0.000000")
    assert redundancy_report.rows == ()
    assert redundancy_report.reason_codes == ("research_event_signal_redundancy_empty",)
    assert redundancy_report.reason_code_counts == (
        module.ResearchEventSignalRedundancyReasonCodeCount(
            reason_code="research_event_signal_redundancy_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert redundancy_report.paper_only is True
    assert redundancy_report.report_only is True
    assert redundancy_report.readonly is True
    assert module.research_event_signal_redundancy_report_digest(
        redundancy_report,
    ) == module.research_event_signal_redundancy_report_digest(redundancy_report)


def test_block_watch_and_pass_signals_summarize_overlap_and_ambiguity() -> None:
    redundancy_report = report(block_signal(), watch_signal(), signal("macro-clean"))

    assert redundancy_report.redundancy_status == "block"
    assert redundancy_report.recommended_next_step == (
        "block_report_only_research_event_signal_redundancy"
    )
    assert redundancy_report.input_count == d("3.000000")
    assert redundancy_report.row_count == d("3.000000")
    assert redundancy_report.block_count == d("1.000000")
    assert redundancy_report.watch_count == d("1.000000")
    assert redundancy_report.pass_count == d("1.000000")
    assert redundancy_report.evidence_overlap_count == d("2.000000")
    assert redundancy_report.catalyst_overlap_count == d("2.000000")
    assert redundancy_report.source_class_overlap_count == d("2.000000")
    assert redundancy_report.team_confidence_dispersion_count == d("2.000000")
    assert redundancy_report.resolution_ambiguity_count == d("2.000000")
    assert redundancy_report.max_evidence_overlap_ratio == d("0.780000")
    assert redundancy_report.max_catalyst_overlap_ratio == d("0.760000")
    assert redundancy_report.max_source_class_overlap_ratio == d("0.820000")
    assert redundancy_report.max_team_confidence_dispersion == d("0.410000")
    assert redundancy_report.max_resolution_ambiguity_ratio == d("0.680000")
    assert redundancy_report.redundancy_risk_score == d("0.500000")

    assert tuple(
        (row.research_theme, row.signal_family, row.redundancy_status)
        for row in redundancy_report.rows
    ) == (
        ("energy-weather", "grid-alerts", "block"),
        ("policy-calendar", "ballot-access", "watch"),
        ("macro-clean", "rate-path", "pass"),
    )

    blocked, watched, passed = redundancy_report.rows
    assert blocked.risk_score == d("1.000000")
    assert blocked.upstream_reason_codes == (
        "overlapping_timing_window",
        "same_public_documents",
    )
    assert blocked.reason_codes == (
        "research_event_signal_evidence_overlap_block",
        "research_event_signal_catalyst_overlap_block",
        "research_event_signal_source_class_overlap_block",
        "research_event_signal_team_confidence_dispersion_block",
        "research_event_signal_resolution_ambiguity_block",
    )
    assert watched.risk_score == d("0.500000")
    assert watched.reason_codes == (
        "research_event_signal_evidence_overlap_watch",
        "research_event_signal_catalyst_overlap_watch",
        "research_event_signal_source_class_overlap_watch",
        "research_event_signal_team_confidence_dispersion_watch",
        "research_event_signal_resolution_ambiguity_watch",
    )
    assert passed.risk_score == d("0.000000")
    assert passed.reason_codes == ("research_event_signal_redundancy_passed",)
    assert redundancy_report.reason_codes == (
        "research_event_signal_evidence_overlap_block",
        "research_event_signal_evidence_overlap_watch",
        "research_event_signal_catalyst_overlap_block",
        "research_event_signal_catalyst_overlap_watch",
        "research_event_signal_source_class_overlap_block",
        "research_event_signal_source_class_overlap_watch",
        "research_event_signal_team_confidence_dispersion_block",
        "research_event_signal_team_confidence_dispersion_watch",
        "research_event_signal_resolution_ambiguity_block",
        "research_event_signal_resolution_ambiguity_watch",
        "research_event_signal_redundancy_watch_present",
    )
    assert redundancy_report.reason_code_counts[-1] == (
        report_module().ResearchEventSignalRedundancyReasonCodeCount(
            reason_code="research_event_signal_redundancy_watch_present",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
    )


def test_non_default_thresholds_can_downgrade_moderate_overlap() -> None:
    cfg = config(
        evidence_overlap_watch_threshold=d("0.500000"),
        catalyst_overlap_watch_threshold=d("0.500000"),
        source_class_overlap_watch_threshold=d("0.500000"),
        team_confidence_dispersion_watch_threshold=d("0.300000"),
        resolution_ambiguity_watch_threshold=d("0.400000"),
    )

    redundancy_report = report(watch_signal(), cfg=cfg)

    assert redundancy_report.redundancy_status == "pass"
    assert redundancy_report.rows[0].redundancy_status == "pass"
    assert redundancy_report.rows[0].reason_codes == (
        "research_event_signal_redundancy_passed",
    )
    assert redundancy_report.reason_codes == ("research_event_signal_redundancy_clear",)
    assert redundancy_report.redundancy_risk_score == d("0.000000")


def test_rows_payload_and_digest_are_deterministic_public_safe() -> None:
    module = report_module()
    forward = report(watch_signal(), block_signal(), signal("macro-clean"))
    reverse = report(signal("macro-clean"), block_signal(), watch_signal())

    assert forward == reverse
    assert module.research_event_signal_redundancy_report_payload(forward) == (
        module.research_event_signal_redundancy_report_payload(reverse)
    )
    assert module.research_event_signal_redundancy_report_digest(forward) == (
        module.research_event_signal_redundancy_report_digest(reverse)
    )
    assert len(module.research_event_signal_redundancy_report_digest(forward)) == 64
    json.dumps(
        module.research_event_signal_redundancy_report_payload(forward),
        sort_keys=True,
    )

    payload = module.research_event_signal_redundancy_report_payload(forward)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "3.000000"
    assert payload["redundancy_risk_score"] == "0.500000"
    assert payload["rows"][0]["evidence_overlap_ratio"] == "0.780000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "0.333333"

    def walk_payload(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "event_id" not in lowered
                assert "market_slug" not in lowered
                assert "source_id" not in lowered
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "auth" not in lowered
                assert "order" not in lowered
                assert "trade" not in lowered
                assert "submit" not in lowered
                assert "cancel" not in lowered
                assert "replace" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)


def test_validation_frozen_dataclasses_decimal_inputs_and_hard_flags() -> None:
    module = report_module()
    input_row = signal("frozen-theme")
    redundancy_report = report(input_row)

    with pytest.raises(FrozenInstanceError):
        input_row.research_theme = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        redundancy_report.redundancy_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        redundancy_report.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):
        type("BadConfig", (module.ResearchEventSignalRedundancyConfig,), {})
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        module.build_research_event_signal_redundancy_report(
            (input_row,),
            config=module.ResearchEventSignalRedundancyConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 9, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="research_theme must be a plain str"):
        signal(_StringSubclass("bad-theme"))
    with pytest.raises(ValueError, match="evidence_overlap_ratio must be a Decimal"):
        signal(evidence_overlap_ratio=_DecimalSubclass("0.120000"))
    with pytest.raises(ValueError, match="inputs must be a tuple"):
        module.build_research_event_signal_redundancy_report(
            [input_row],
            config=module.ResearchEventSignalRedundancyConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate research_theme and signal_family"):
        report(signal("duplicate-theme"), signal("duplicate-theme"))
    with pytest.raises(ValueError, match="paper_only"):
        signal("bad-flags", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="watch_threshold"):
        config(
            evidence_overlap_watch_threshold=d("0.800000"),
            evidence_overlap_block_threshold=d("0.700000"),
        )

    valid_row = redundancy_report.rows[0]
    with pytest.raises(ValueError, match="risk_score must match"):
        replace(valid_row, risk_score=d("1.000000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "research_event_signal_redundancy_passed",
                "research_event_signal_evidence_overlap_watch",
            ),
        )

    for public_record in (
        module.ResearchEventSignalRedundancyConfig(),
        input_row,
        valid_row,
        redundancy_report.reason_code_counts[0],
        redundancy_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal, field.name


def test_module_has_no_forbidden_side_effect_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlite",
        "os",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "event_id",
        "market_slug",
        "source_id",
        "private_key",
        "wallet",
        "auth_token",
        "authentication",
        "urlopen",
        "connect(",
        "execute(",
        "commit(",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "trade",
        "getenv",
        "environ",
    ):
        assert forbidden not in source
