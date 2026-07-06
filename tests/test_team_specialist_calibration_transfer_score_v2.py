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
    / "team_specialist_calibration_transfer_score_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_calibration_transfer_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def transfer(**overrides: object):
    module = api()
    values = {
        "team_id": "alpha_specialists",
        "specialist_id": "macro_mapper",
        "source_domain_id": "macro_rates",
        "target_domain_id": "policy_windows",
        "source_calibration_score": d("0.900000"),
        "target_domain_similarity_score": d("0.850000"),
        "recent_transfer_error": d("0.050000"),
        "transfer_sample_count": d("12"),
        "stale_sample_count": d("0"),
        "specialist_fit_score": d("0.920000"),
    }
    values.update(overrides)
    return module.TeamSpecialistCalibrationTransferScoreV2Input(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop(
        "generated_at",
        datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
    )
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            transfer(),
            transfer(
                team_id="beta_specialists",
                specialist_id="geo_mapper",
                source_domain_id="elections",
                target_domain_id="turnout_models",
                source_calibration_score=d("0.820000"),
                target_domain_similarity_score=d("0.760000"),
                recent_transfer_error=d("0.180000"),
                transfer_sample_count=d("8"),
                stale_sample_count=d("3"),
                specialist_fit_score=d("0.650000"),
            ),
            transfer(
                team_id="gamma_specialists",
                specialist_id="news_mapper",
                source_domain_id="sports_news",
                target_domain_id="event_windows",
                source_calibration_score=d("0.550000"),
                target_domain_similarity_score=d("0.400000"),
                recent_transfer_error=d("0.400000"),
                transfer_sample_count=d("2"),
                stale_sample_count=d("2"),
                specialist_fit_score=d("0.350000"),
            ),
        )
    return module.build_team_specialist_calibration_transfer_score_v2(
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


def test_builds_cross_domain_calibration_transfer_scorecard() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.transfer_scorecard_status == "blocked"
    assert report.candidate_count == d("3")
    assert report.pass_candidate_count == d("1")
    assert report.watch_candidate_count == d("1")
    assert report.blocked_candidate_count == d("1")
    assert report.average_cross_domain_transfer_score == d("0.641667")
    assert report.top_cross_domain_transfer_score == d("0.948000")
    assert report.bottom_cross_domain_transfer_score == d("0.347500")
    assert report.reason_codes == (
        "calibration_transfer_scorecard_blocked_rows",
        "calibration_transfer_scorecard_watch_rows",
    )

    rows = report.rows
    assert tuple(row.team_id for row in rows) == (
        "alpha_specialists",
        "beta_specialists",
        "gamma_specialists",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.cross_domain_transfer_score for row in rows) == (
        d("0.948000"),
        d("0.629500"),
        d("0.347500"),
    )
    assert tuple(row.transfer_status for row in rows) == ("pass", "watch", "blocked")
    assert rows[0].sample_depth_score == d("1.000000")
    assert rows[0].specialist_fit_boost == d("0.030000")
    assert rows[1].stale_sample_penalty == d("0.150000")
    assert rows[2].stale_sample_penalty == d("0.100000")


def test_stale_sample_penalties_reduce_scores_and_emit_reasons() -> None:
    clean = transfer(
        team_id="clean_specialists",
        specialist_id="macro_mapper",
        target_domain_id="policy_windows",
        source_calibration_score=d("0.820000"),
        target_domain_similarity_score=d("0.760000"),
        recent_transfer_error=d("0.180000"),
        transfer_sample_count=d("8"),
        stale_sample_count=d("0"),
        specialist_fit_score=d("0.650000"),
    )
    stale = transfer(
        team_id="stale_specialists",
        specialist_id="macro_mapper",
        target_domain_id="policy_cycles",
        source_calibration_score=d("0.820000"),
        target_domain_similarity_score=d("0.760000"),
        recent_transfer_error=d("0.180000"),
        transfer_sample_count=d("8"),
        stale_sample_count=d("4"),
        specialist_fit_score=d("0.650000"),
    )

    report = build_report(clean, stale)
    clean_row, stale_row = report.rows

    assert clean_row.cross_domain_transfer_score == d("0.779500")
    assert stale_row.cross_domain_transfer_score == d("0.579500")
    assert stale_row.stale_sample_penalty == d("0.200000")
    assert "stale_samples_clear" in clean_row.reason_codes
    assert "stale_sample_penalty_applied" in stale_row.reason_codes
    assert stale_row.transfer_status == "blocked"


def test_specialist_fit_boost_lifts_otherwise_equal_candidates() -> None:
    boosted = transfer(
        team_id="boosted_specialists",
        specialist_id="macro_mapper",
        target_domain_id="policy_windows",
        specialist_fit_score=d("0.950000"),
    )
    supported = transfer(
        team_id="supported_specialists",
        specialist_id="macro_mapper",
        target_domain_id="policy_cycles",
        specialist_fit_score=d("0.800000"),
    )

    report = build_report(boosted, supported)
    boosted_row, supported_row = report.rows

    assert boosted_row.specialist_fit_boost == d("0.037500")
    assert supported_row.specialist_fit_boost == d("0.000000")
    assert boosted_row.cross_domain_transfer_score > supported_row.cross_domain_transfer_score
    assert "specialist_fit_boosted" in boosted_row.reason_codes
    assert "specialist_fit_supported" in supported_row.reason_codes


def test_payload_serializes_decimal_values_as_strings_and_is_report_only() -> None:
    report = build_report()
    payload = report.payload

    assert payload["candidate_count"] == "3"
    assert payload["average_cross_domain_transfer_score"] == "0.641667"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["cross_domain_transfer_score"] == "0.948000"
    assert payload["rows"][0]["specialist_fit_boost"] == "0.030000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_empty_report_is_digest_backed_and_hard_flagged() -> None:
    report = build_report(
        *(),
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
        use_default_items=False,
    )

    assert report.transfer_scorecard_status == "blocked"
    assert report.candidate_count == d("0")
    assert report.average_cross_domain_transfer_score == d("0.000000")
    assert report.top_cross_domain_transfer_score == d("0.000000")
    assert report.bottom_cross_domain_transfer_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("calibration_transfer_scorecard_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistCalibrationTransferScoreV2Config()
    sample = transfer()
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
                "source_calibration_weight",
                "domain_similarity_weight",
                "recent_transfer_accuracy_weight",
                "sample_depth_weight",
                "specialist_fit_weight",
                "full_sample_count",
                "stale_sample_penalty_count",
                "stale_sample_penalty_weight",
                "specialist_fit_boost_floor",
                "specialist_fit_boost_weight",
                "pass_score_floor",
                "watch_score_floor",
                "source_calibration_score",
                "target_domain_similarity_score",
                "recent_transfer_error",
                "transfer_sample_count",
                "stale_sample_count",
                "specialist_fit_score",
                "rank",
                "recent_transfer_accuracy_score",
                "sample_depth_score",
                "stale_sample_penalty",
                "specialist_fit_boost",
                "cross_domain_transfer_score",
                "candidate_count",
                "pass_candidate_count",
                "watch_candidate_count",
                "blocked_candidate_count",
                "average_cross_domain_transfer_score",
                "top_cross_domain_transfer_score",
                "bottom_cross_domain_transfer_score",
            }:
                assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "source_calibration_score",
            _DecimalSubclass("0.900000"),
            "source_calibration_score must be exactly Decimal",
        ),
        (
            "target_domain_similarity_score",
            d("1.000001"),
            "target_domain_similarity_score must be <= 1.000000",
        ),
        (
            "recent_transfer_error",
            d("0.0500004"),
            "recent_transfer_error must use six decimal places or fewer",
        ),
        (
            "specialist_fit_score",
            Decimal("NaN"),
            "specialist_fit_score must be finite",
        ),
        (
            "transfer_sample_count",
            d("1.5"),
            "transfer_sample_count must be an integral Decimal",
        ),
        (
            "stale_sample_count",
            d("-1"),
            "stale_sample_count must be >= 0.000000",
        ),
    ),
)
def test_input_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        transfer(**{field_name: bad_value})


def test_validation_rejects_bad_counts_config_types_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="stale_sample_count must not exceed"):
        transfer(transfer_sample_count=d("1"), stale_sample_count=d("2"))
    with pytest.raises(ValueError, match="source_calibration_weight must be exactly Decimal"):
        module.TeamSpecialistCalibrationTransferScoreV2Config(
            source_calibration_weight=0,
        )
    with pytest.raises(ValueError, match="transfer score weights must sum to 1.000000"):
        module.TeamSpecialistCalibrationTransferScoreV2Config(
            sample_depth_weight=d("0.160000"),
        )
    with pytest.raises(ValueError, match="watch_score_floor must not exceed pass_score_floor"):
        module.TeamSpecialistCalibrationTransferScoreV2Config(
            watch_score_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistCalibrationTransferScoreV2Config(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        transfer(readonly=False)


def test_build_validation_rejects_wrong_types_and_duplicate_transfer_keys() -> None:
    module = api()

    with pytest.raises(ValueError, match="transfer_inputs must be an iterable"):
        module.build_team_specialist_calibration_transfer_score_v2(
            object(),
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="transfer items must be TeamSpecialistCalibrationTransferScoreV2Input",
    ):
        module.build_team_specialist_calibration_transfer_score_v2(
            [object()],
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_calibration_transfer_score_v2(
            [transfer()],
            generated_at=datetime(2026, 7, 6),
        )
    duplicate = transfer()
    with pytest.raises(ValueError, match="duplicate transfer keys"):
        build_report(duplicate, duplicate)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(
            report,
            average_cross_domain_transfer_score=d("0.600000"),
        )


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "live_ref",
        "auth_ref",
        "wallet_ref",
        "order_ref",
        "network_ref",
        "database_ref",
        "persist_ref",
        "signing_ref",
        "mutation_ref",
        "buy_ref",
        "sell_ref",
        "trade_ref",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            transfer(team_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"wallet_ref": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": 1})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_report_revalidates_order_counts_reason_codes_and_status() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by score and rank"):
        replace(
            report,
            rows=(report.rows[1], report.rows[0], report.rows[2]),
        )
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(
            report,
            pass_candidate_count=d("2"),
        )
    with pytest.raises(ValueError, match="reason_codes must match transfer_scorecard_status"):
        replace(
            report,
            reason_codes=("calibration_transfer_scorecard_passed",),
        )


def test_module_scope_has_no_file_database_network_or_order_surface() -> None:
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
