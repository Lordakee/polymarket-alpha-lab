from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_consensus_drift_score.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_consensus_drift_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def consensus(**overrides: object):
    module = api()
    values = {
        "team_id": "alpha_specialists",
        "specialist_id": "macro_mapper",
        "consensus_case_count": d("24"),
        "recent_consensus_score": d("0.830000"),
        "historical_consensus_score": d("0.800000"),
        "dissent_ratio": d("0.060000"),
        "calibration_score": d("0.900000"),
        "source_quality_score": d("0.880000"),
    }
    values.update(overrides)
    return module.TeamSpecialistConsensusDriftScoreInput(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop(
        "generated_at",
        datetime(2026, 7, 7, 12, 0, tzinfo=UTC),
    )
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            consensus(),
            consensus(
                team_id="beta_specialists",
                specialist_id="policy_mapper",
                consensus_case_count=d("12"),
                recent_consensus_score=d("0.660000"),
                historical_consensus_score=d("0.790000"),
                dissent_ratio=d("0.220000"),
                calibration_score=d("0.700000"),
                source_quality_score=d("0.720000"),
            ),
            consensus(
                team_id="gamma_specialists",
                specialist_id="event_mapper",
                consensus_case_count=d("5"),
                recent_consensus_score=d("0.400000"),
                historical_consensus_score=d("0.810000"),
                dissent_ratio=d("0.470000"),
                calibration_score=d("0.420000"),
                source_quality_score=d("0.450000"),
            ),
        )
    return module.build_team_specialist_consensus_drift_score(
        items,
        config=config,
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_stable_consensus_passes_with_low_drift() -> None:
    report = build_report(consensus())
    row = report.rows[0]

    assert is_dataclass(report)
    assert report.consensus_drift_scorecard_status == "pass"
    assert report.candidate_count == d("1")
    assert report.pass_candidate_count == d("1")
    assert row.consensus_drift_score == d("0.939500")
    assert row.absolute_consensus_drift == d("0.030000")
    assert row.consensus_stability_score == d("0.970000")
    assert row.consensus_depth_score == d("1.000000")
    assert row.consensus_drift_status == "pass"
    assert row.reason_codes == (
        "consensus_drift_pass",
        "consensus_stability_strong",
        "dissent_low",
        "consensus_depth_full",
        "calibration_strong",
        "source_quality_strong",
    )


def test_sharp_consensus_drift_blocks() -> None:
    report = build_report(
        consensus(
            consensus_case_count=d("5"),
            recent_consensus_score=d("0.400000"),
            historical_consensus_score=d("0.810000"),
            dissent_ratio=d("0.470000"),
            calibration_score=d("0.420000"),
            source_quality_score=d("0.450000"),
        ),
    )
    row = report.rows[0]

    assert report.consensus_drift_scorecard_status == "block"
    assert report.block_candidate_count == d("1")
    assert row.consensus_drift_score == d("0.489000")
    assert row.absolute_consensus_drift == d("0.410000")
    assert row.consensus_drift_status == "block"
    assert "consensus_stability_weak" in row.reason_codes
    assert "dissent_high" in row.reason_codes


def test_moderate_consensus_drift_watches() -> None:
    report = build_report(
        consensus(
            consensus_case_count=d("12"),
            recent_consensus_score=d("0.660000"),
            historical_consensus_score=d("0.790000"),
            dissent_ratio=d("0.220000"),
            calibration_score=d("0.700000"),
            source_quality_score=d("0.720000"),
        ),
    )
    row = report.rows[0]

    assert report.consensus_drift_scorecard_status == "watch"
    assert report.watch_candidate_count == d("1")
    assert row.consensus_drift_score == d("0.768500")
    assert row.absolute_consensus_drift == d("0.130000")
    assert row.consensus_depth_score == d("0.600000")
    assert row.consensus_drift_status == "watch"
    assert "consensus_stability_watch" in row.reason_codes
    assert "dissent_watch" in row.reason_codes


def test_payload_is_deterministic_decimal_backed_and_report_only() -> None:
    first = build_report()
    second = build_report()

    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    payload = first.payload
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["candidate_count"] == "3"
    assert payload["average_consensus_drift_score"] == "0.732333"
    assert payload["rows"][0]["team_id"] == "alpha_specialists"
    assert payload["rows"][0]["consensus_drift_score"] == "0.939500"
    assert payload["rows"][1]["consensus_drift_status"] == "watch"
    assert payload["rows"][2]["consensus_drift_status"] == "block"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(first.derived_validation_digest) == 64
    assert_no_float_values(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistConsensusDriftScoreConfig()
    sample = consensus()
    report = build_report(sample)
    row = report.rows[0]

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {
                "stability_weight",
                "dissent_weight",
                "calibration_weight",
                "source_quality_weight",
                "depth_weight",
                "full_consensus_case_count",
                "sharp_drift_threshold",
                "moderate_drift_threshold",
                "pass_score_floor",
                "watch_score_floor",
                "consensus_case_count",
                "recent_consensus_score",
                "historical_consensus_score",
                "dissent_ratio",
                "calibration_score",
                "source_quality_score",
                "rank",
                "absolute_consensus_drift",
                "consensus_stability_score",
                "dissent_stability_score",
                "consensus_depth_score",
                "consensus_drift_score",
                "candidate_count",
                "pass_candidate_count",
                "watch_candidate_count",
                "block_candidate_count",
                "average_consensus_drift_score",
                "top_consensus_drift_score",
                "bottom_consensus_drift_score",
            }:
                assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "recent_consensus_score",
            _DecimalSubclass("0.830000"),
            "recent_consensus_score must be exactly Decimal",
        ),
        (
            "historical_consensus_score",
            d("1.000001"),
            "historical_consensus_score must be <= 1.000000",
        ),
        (
            "dissent_ratio",
            d("0.0600004"),
            "dissent_ratio must use six decimal places or fewer",
        ),
        (
            "calibration_score",
            Decimal("NaN"),
            "calibration_score must be finite",
        ),
        (
            "consensus_case_count",
            d("1.5"),
            "consensus_case_count must be an integral Decimal",
        ),
        (
            "source_quality_score",
            d("-0.100000"),
            "source_quality_score must be >= 0.000000",
        ),
    ),
)
def test_decimal_exact_type_rejection(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        consensus(**{field_name: bad_value})


def test_leak_rejection_blocks_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "market_ref",
        "candidate_ref",
        "slug_ref",
        "question_ref",
        "url_ref",
        "source_ref",
        "dsn_ref",
        "table_ref",
        "token_ref",
        "secret_ref",
        "auth_ref",
        "wallet_ref",
        "order_ref",
        "trade_ref",
        "buy_ref",
        "sell_ref",
        "recommendation_ref",
        "position_sizing_ref",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            consensus(team_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"market_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "token note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": 1})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], consensus_drift_status="blocked")


def test_hard_flags_are_required() -> None:
    module = api()

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistConsensusDriftScoreConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        consensus(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        consensus(readonly=False)


def test_report_consistency_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by score and rank"):
        replace(report, rows=(report.rows[1], report.rows[0], report.rows[2]))
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(report, pass_candidate_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(report, reason_codes=("consensus_drift_scorecard_passed",))
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="average_consensus_drift_score must match rows"):
        replace(report, average_consensus_drift_score=d("0.600000"))


def test_build_validation_rejects_wrong_types_duplicates_and_naive_time() -> None:
    module = api()

    with pytest.raises(ValueError, match="consensus_inputs must be an iterable"):
        module.build_team_specialist_consensus_drift_score(
            object(),
            generated_at=datetime(2026, 7, 7, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="consensus items must be TeamSpecialistConsensusDriftScoreInput",
    ):
        module.build_team_specialist_consensus_drift_score(
            [object()],
            generated_at=datetime(2026, 7, 7, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_consensus_drift_score(
            [consensus()],
            generated_at=datetime(2026, 7, 7),
        )
    duplicate = consensus()
    with pytest.raises(ValueError, match="duplicate consensus keys"):
        build_report(duplicate, duplicate)


def test_public_status_vocabulary_never_uses_blocked_ready_or_supported() -> None:
    payload = build_report().payload
    encoded = json.dumps(payload, sort_keys=True)

    assert '"pass"' in encoded
    assert '"watch"' in encoded
    assert '"block"' in encoded
    for forbidden in ("blocked", "ready", "matched", "supported"):
        assert forbidden not in encoded


def test_module_scope_has_no_file_database_network_or_trading_surface() -> None:
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
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
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
        "place_order",
        "rollback",
        "sell",
        "send",
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
    assert_no_float_values([imports, call_names, attribute_names])
