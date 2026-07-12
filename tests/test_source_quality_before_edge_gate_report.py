from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 11, 15, 0, tzinfo=UTC)
ANCHOR_AT = datetime(2026, 7, 11, 14, 50, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.source_quality_before_edge_gate_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "source_quality_before_edge_gate_report.py"
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
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
        "config_version": module.DEFAULT_SOURCE_QUALITY_BEFORE_EDGE_GATE_CONFIG_VERSION,
        "max_official_anchor_age_seconds": d("900.000000"),
        "min_independent_source_family_count": d("3.000000"),
        "min_resolution_rule_clarity_score": d("0.800000"),
        "min_specialist_quorum_count": d("2.000000"),
    }
    values.update(overrides)
    return module.SourceQualityBeforeEdgeGateConfig(**values)


def candidate(**overrides: object) -> Any:
    module = api()
    values = {
        "public_source_ref": "source-quality-market",
        "official_anchor_observed_at": ANCHOR_AT,
        "source_families": (
            "official_resolution_rules",
            "independent_media",
            "specialist_research",
        ),
        "contradiction_status": "reviewed_no_material_contradiction",
        "resolution_rule_clarity_score": d("0.900000"),
        "specialist_quorum_count": d("2.000000"),
        "pre_edge_probability": d("0.070000"),
        "source_config_version": "paper-source-quality-v0",
    }
    values.update(overrides)
    return module.SourceQualityBeforeEdgeGateCandidate(**values)


def report(*values: object, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_source_quality_before_edge_gate_report(
        values,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_public_numeric(value: object) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, (Decimal, int, float)):
        raise AssertionError(f"unexpected public numeric value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric(item)


def unsafe_text(*parts: str) -> str:
    return "".join(parts)


def test_source_quality_gate_blocks_before_edge_and_zeroes_blocked_edge() -> None:
    result = report(
        candidate(
            public_source_ref="z-clear",
            pre_edge_probability=d("0.030000"),
        ),
        candidate(
            public_source_ref="a-stale-high-edge",
            official_anchor_observed_at=GENERATED_AT - timedelta(seconds=901),
            pre_edge_probability=d("0.450000"),
        ),
        candidate(
            public_source_ref="m-unclear-low-edge",
            resolution_rule_clarity_score=d("0.700000"),
            pre_edge_probability=d("0.010000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "source-quality-before-edge-gate-v1"
    assert result.candidate_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.blocked_count == d("1.000000")
    assert result.source_blocker_count == d("1.000000")
    assert result.pre_edge_candidate_count == d("3.000000")
    assert result.edge_eligible_count == d("1.000000")
    assert result.total_pre_edge_probability == d("0.490000")
    assert result.total_edge_eligible_probability == d("0.030000")
    assert result.max_official_anchor_age_seconds == d("901.000000")
    assert result.min_resolution_rule_clarity_score == d("0.700000")
    assert result.gate_status == "blocked"
    assert result.recommended_next_step == "block_edge_until_source_quality_clears"
    assert result.reason_codes == (
        "official_anchor_stale",
        "resolution_rule_clarity_below_minimum",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    stale, unclear, clear = result.rows
    assert tuple(row.public_source_ref for row in result.rows) == (
        "a-stale-high-edge",
        "m-unclear-low-edge",
        "z-clear",
    )
    assert stale.pre_edge_probability == d("0.450000")
    assert stale.edge_eligible_probability == ZERO
    assert stale.gate_status == "blocked"
    assert stale.reason_codes == ("official_anchor_stale",)
    assert unclear.pre_edge_probability == d("0.010000")
    assert unclear.edge_eligible_probability == ZERO
    assert unclear.gate_status == "watch"
    assert unclear.reason_codes == ("resolution_rule_clarity_below_minimum",)
    assert clear.pre_edge_probability == d("0.030000")
    assert clear.edge_eligible_probability == d("0.030000")
    assert clear.gate_status == "pass"
    assert clear.reason_codes == ("source_quality_before_edge_gate_passed",)
    assert len({row.derived_validation_digest for row in result.rows}) == 3


def test_all_source_blockers_override_high_edge() -> None:
    blocked = report(
        candidate(
            public_source_ref="stale-anchor",
            official_anchor_observed_at=GENERATED_AT - timedelta(seconds=901),
            pre_edge_probability=d("0.990000"),
        ),
        candidate(
            public_source_ref="few-families",
            source_families=("official_resolution_rules", "independent_media"),
            pre_edge_probability=d("0.990000"),
        ),
        candidate(
            public_source_ref="contradicted",
            contradiction_status="material_contradiction_found",
            pre_edge_probability=d("0.990000"),
        ),
        candidate(
            public_source_ref="thin-quorum",
            specialist_quorum_count=d("1.000000"),
            pre_edge_probability=d("0.990000"),
        ),
    )

    assert blocked.gate_status == "blocked"
    assert blocked.source_blocker_count == d("4.000000")
    assert blocked.edge_eligible_count == ZERO
    assert blocked.total_pre_edge_probability == d("3.960000")
    assert blocked.total_edge_eligible_probability == ZERO
    assert blocked.reason_codes == (
        "official_anchor_stale",
        "independent_source_family_count_below_minimum",
        "contradiction_status_not_clear",
        "specialist_quorum_below_minimum",
    )
    assert tuple(row.gate_status for row in blocked.rows) == (
        "blocked",
        "blocked",
        "blocked",
        "blocked",
    )
    assert all(row.edge_eligible_probability == ZERO for row in blocked.rows)


def test_empty_report_is_readonly_zeroed_and_digest_bound() -> None:
    module = api()
    empty = report()

    assert type(empty) is module.SourceQualityBeforeEdgeGateReport
    assert empty.candidate_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.blocked_count == ZERO
    assert empty.source_blocker_count == ZERO
    assert empty.pre_edge_candidate_count == ZERO
    assert empty.edge_eligible_count == ZERO
    assert empty.total_pre_edge_probability == ZERO
    assert empty.total_edge_eligible_probability == ZERO
    assert empty.max_official_anchor_age_seconds == ZERO
    assert empty.min_resolution_rule_clarity_score == ZERO
    assert empty.gate_status == "pass"
    assert empty.recommended_next_step == "continue_report_only_source_quality_before_edge"
    assert empty.reason_codes == ("source_quality_before_edge_gate_empty",)
    assert empty.reason_code_counts == ()
    assert empty.rows == ()
    assert len(empty.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in empty.derived_validation_digest)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    for public_value in (config(), candidate(), empty):
        assert is_dataclass(public_value)
        assert public_value.__dataclass_params__.frozen is True


def test_public_payload_uses_decimal_strings_and_rejects_tampering() -> None:
    module = api()
    result = report(
        candidate(
            public_source_ref="payload-source",
            pre_edge_probability=d("0.120000"),
        ),
        generated_at=datetime(2026, 7, 11, 11, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.source_quality_before_edge_gate_public_payload(result)

    assert payload["generated_at"] == "2026-07-11T15:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["total_edge_eligible_probability"] == "0.120000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["official_anchor_observed_at"] == "2026-07-11T14:50:00+00:00"
    assert payload["rows"][0]["edge_eligible_probability"] == "0.120000"
    assert module.validate_source_quality_before_edge_gate_public_payload(payload)
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    numeric_payload = {**payload, "candidate_count": 1}
    with pytest.raises(ValueError, match="Decimal strings|numeric"):
        module.validate_source_quality_before_edge_gate_public_payload(numeric_payload)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_source_quality_before_edge_gate_public_payload(missing_digest)

    tampered = {**payload, "edge_eligible_count": "0.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_source_quality_before_edge_gate_public_payload(tampered)

    tampered_report = replace(result)
    object.__setattr__(tampered_report, "edge_eligible_count", d("99.000000"))
    with pytest.raises(ValueError, match="edge_eligible_count|derived_validation_digest"):
        module.source_quality_before_edge_gate_public_payload(tampered_report)


@pytest.mark.parametrize(
    ("key", "value"),
    (
        (unsafe_text("li", "ve", "_enabled"), "not allowed"),
        (unsafe_text("au", "th", "_token"), "not allowed"),
        (unsafe_text("wal", "let", "_address"), "not allowed"),
        (unsafe_text("ord", "er", "_id"), "not allowed"),
        (unsafe_text("per", "sist", "_path"), "not allowed"),
        ("operator_note", unsafe_text("configured ", "li", "ve", " surface")),
        ("operator_note", unsafe_text("configured ", "au", "th", " surface")),
        ("operator_note", unsafe_text("configured ", "wal", "let", " surface")),
        ("operator_note", unsafe_text("configured ", "ord", "er", " surface")),
    ),
)
def test_public_payload_rejects_unsafe_public_keys_and_values(
    key: str,
    value: str,
) -> None:
    module = api()
    payload = module.source_quality_before_edge_gate_public_payload(
        report(candidate(public_source_ref="unsafe-check")),
    )

    unsafe_payload = {**payload, key: value}
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_source_quality_before_edge_gate_public_payload(unsafe_payload)


def test_validation_rejects_bad_types_flags_duplicates_time_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_source_quality_before_edge_gate_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 11, 15, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="official_anchor_observed_at"):
        candidate(official_anchor_observed_at=datetime(2026, 7, 11, 14, 50))
    with pytest.raises(ValueError, match="official_anchor_observed_at"):
        candidate(
            official_anchor_observed_at=datetime(
                2026,
                7,
                11,
                14,
                50,
                tzinfo=_NoneOffsetTz(),
            ),
        )
    with pytest.raises(ValueError, match="after generated_at"):
        report(candidate(official_anchor_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate source quality candidate"):
        report(
            candidate(public_source_ref="duplicate"),
            candidate(public_source_ref="duplicate"),
        )
    with pytest.raises(ValueError, match="pre_edge_probability"):
        candidate(pre_edge_probability=1)
    with pytest.raises(ValueError, match="specialist_quorum_count"):
        candidate(specialist_quorum_count=_DecimalSubclass("2.000000"))
    with pytest.raises(ValueError, match="source_families"):
        candidate(source_families=("official_resolution_rules", "official_resolution_rules"))
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)

    clear_report = report(candidate(public_source_ref="consistent"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(clear_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="edge_eligible_count"):
        replace(clear_report, edge_eligible_count=d("2.000000"))

    with pytest.raises(FrozenInstanceError):
        clear_report.gate_status = "blocked"  # type: ignore[misc]


def test_export_contract_and_static_no_external_surfaces() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_SOURCE_QUALITY_BEFORE_EDGE_GATE_CONFIG_VERSION",
        "SourceQualityBeforeEdgeGateCandidate",
        "SourceQualityBeforeEdgeGateConfig",
        "SourceQualityBeforeEdgeGateReasonCodeCount",
        "SourceQualityBeforeEdgeGateReport",
        "SourceQualityBeforeEdgeGateRow",
        "build_source_quality_before_edge_gate_report",
        "source_quality_before_edge_gate_public_payload",
        "validate_source_quality_before_edge_gate_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    for instance in (
        config(),
        candidate(),
        *report(candidate()).rows,
        report(candidate()),
    ):
        for field in fields(instance):
            value = getattr(instance, field.name)
            assert type(value) is not float
            if field.name.endswith(
                (
                    "_count",
                    "_probability",
                    "_score",
                    "_seconds",
                ),
            ):
                assert value is None or type(value) is Decimal

    source = MODULE_PATH.read_text()
    lowered_source = source.lower()
    forbidden_source_fragments = (
        "asyncio",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "web3",
        "py_clob_client",
        "private_key",
        "api_key",
        unsafe_text("au", "th", "_token"),
        unsafe_text("wal", "let"),
        unsafe_text("per", "sist", "_path"),
        "place_" + unsafe_text("ord", "er"),
        "create_" + unsafe_text("ord", "er"),
        "cancel_" + unsafe_text("ord", "er"),
        "submit_" + unsafe_text("ord", "er"),
        unsafe_text("li", "ve", "_trading"),
    )
    for fragment in forbidden_source_fragments:
        assert fragment not in lowered_source

    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "read",
        "write",
    }
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_source_fragments
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_source_fragments
        elif isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_call_names
