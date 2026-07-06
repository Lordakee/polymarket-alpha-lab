from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 16, 30, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_basketball_three_point_variance_regression_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    team_id: str = "team-alpha",
    sample_id: str = "last-five-games",
    recent_three_point_attempt_rate: str | Decimal = "0.410000",
    baseline_three_point_attempt_rate: str | Decimal = "0.350000",
    recent_three_point_accuracy: str | Decimal = "0.430000",
    baseline_three_point_accuracy: str | Decimal = "0.340000",
    recent_game_count: str | Decimal = "5.000000",
    data_timestamp: datetime = datetime(2026, 7, 4, 15, 0, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("official_box_score",),
):
    module = digest()
    return module.BasketballThreePointVarianceRegressionObservation(
        source_id=source_id,
        team_id=team_id,
        sample_id=sample_id,
        recent_three_point_attempt_rate=(
            recent_three_point_attempt_rate
            if isinstance(recent_three_point_attempt_rate, Decimal)
            else d(recent_three_point_attempt_rate)
        ),
        baseline_three_point_attempt_rate=(
            baseline_three_point_attempt_rate
            if isinstance(baseline_three_point_attempt_rate, Decimal)
            else d(baseline_three_point_attempt_rate)
        ),
        recent_three_point_accuracy=(
            recent_three_point_accuracy
            if isinstance(recent_three_point_accuracy, Decimal)
            else d(recent_three_point_accuracy)
        ),
        baseline_three_point_accuracy=(
            baseline_three_point_accuracy
            if isinstance(baseline_three_point_accuracy, Decimal)
            else d(baseline_three_point_accuracy)
        ),
        recent_game_count=(
            recent_game_count
            if isinstance(recent_game_count, Decimal)
            else d(recent_game_count)
        ),
        data_timestamp=data_timestamp,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_basketball_three_point_variance_regression_digest(
        rows,
        config=cfg
        or module.BasketballThreePointVarianceRegressionDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(
        digest_report,
        module.BasketballThreePointVarianceRegressionDigestReport,
    )
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-basketball-three-point-variance-regression-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_basketball_three_point_variance_regression_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.elevated_accuracy_count == d("0.000000")
    assert digest_report.attempt_rate_spike_count == d("0.000000")
    assert digest_report.small_sample_count == d("0.000000")
    assert digest_report.max_accuracy_delta == d("0.000000")
    assert digest_report.average_accuracy_delta == d("0.000000")
    assert digest_report.regression_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "basketball_three_point_variance_regression_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.BasketballThreePointVarianceRegressionReasonCodeCount(
            reason_code="basketball_three_point_variance_regression_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_hot_three_point_variance_blocks_probability_event_screening() -> None:
    digest_report = report(
        observation(
            "source-hot",
            team_id="team-hot",
            recent_three_point_attempt_rate="0.430000",
            baseline_three_point_attempt_rate="0.350000",
            recent_three_point_accuracy="0.470000",
            baseline_three_point_accuracy="0.330000",
            recent_game_count="4.000000",
        ),
        observation(
            "source-watch",
            team_id="team-watch",
            recent_three_point_attempt_rate="0.360000",
            baseline_three_point_attempt_rate="0.340000",
            recent_three_point_accuracy="0.410000",
            baseline_three_point_accuracy="0.340000",
            recent_game_count="8.000000",
            data_timestamp=datetime(2026, 7, 4, 10, 0, tzinfo=timezone(timedelta(hours=-5))),
        ),
        observation(
            "source-pass",
            team_id="team-pass",
            recent_three_point_attempt_rate="0.330000",
            baseline_three_point_attempt_rate="0.320000",
            recent_three_point_accuracy="0.360000",
            baseline_three_point_accuracy="0.350000",
            recent_game_count="12.000000",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_basketball_three_point_variance_regression_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.elevated_accuracy_count == d("2.000000")
    assert digest_report.attempt_rate_spike_count == d("1.000000")
    assert digest_report.small_sample_count == d("1.000000")
    assert digest_report.max_accuracy_delta == d("0.140000")
    assert digest_report.average_accuracy_delta == d("0.073333")
    assert digest_report.regression_risk_score == d("1.000000")
    assert digest_report.reason_codes == (
        "basketball_three_point_variance_regression_high_accuracy_delta_present",
        "basketball_three_point_variance_regression_attempt_rate_spike_present",
        "basketball_three_point_variance_regression_small_sample_present",
        "basketball_three_point_variance_regression_multi_team_signal_present",
    )
    assert tuple(row.team_id for row in digest_report.rows) == (
        "team-hot",
        "team-watch",
        "team-pass",
    )

    blocked, watch, passed = digest_report.rows
    assert blocked.regression_status == "blocked"
    assert blocked.attempt_rate_delta == d("0.080000")
    assert blocked.accuracy_delta == d("0.140000")
    assert blocked.data_timestamp == datetime(2026, 7, 4, 15, 0, tzinfo=UTC)
    assert blocked.reason_codes == (
        "basketball_three_point_variance_regression_attempt_rate_spike",
        "basketball_three_point_variance_regression_high_accuracy_delta",
        "basketball_three_point_variance_regression_small_sample",
    )
    assert watch.regression_status == "watch"
    assert watch.reason_codes == (
        "basketball_three_point_variance_regression_watch_accuracy_delta",
    )
    assert passed.regression_status == "pass"
    assert passed.reason_codes == (
        "basketball_three_point_variance_regression_inline",
    )


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        team_id="team-watch-b",
        recent_three_point_accuracy="0.410000",
        baseline_three_point_accuracy="0.340000",
    )
    second = observation(
        "source-blocked",
        team_id="team-blocked",
        recent_three_point_accuracy="0.480000",
        baseline_three_point_accuracy="0.330000",
    )
    third = observation(
        "source-watch-a",
        team_id="team-watch-a",
        recent_three_point_accuracy="0.420000",
        baseline_three_point_accuracy="0.340000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.team_id for row in forward.rows) == (
        "team-blocked",
        "team-watch-a",
        "team-watch-b",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "basketball_three_point_variance_regression_high_accuracy_delta_present",
        "basketball_three_point_variance_regression_attempt_rate_spike_present",
        "basketball_three_point_variance_regression_small_sample_present",
        "basketball_three_point_variance_regression_multi_team_signal_present",
    )


def test_non_default_thresholds_can_downgrade_moderate_regression_risk() -> None:
    module = digest()
    cfg = module.BasketballThreePointVarianceRegressionDigestConfig(
        watch_accuracy_delta=d("0.100000"),
        blocked_accuracy_delta=d("0.200000"),
        attempt_rate_spike_delta=d("0.100000"),
        small_sample_games=d("3.000000"),
    )

    digest_report = report(observation("source-moderate"), cfg=cfg)

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_basketball_three_point_variance_regression_screening"
    )
    assert digest_report.rows[0].regression_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "basketball_three_point_variance_regression_inline",
    )
    assert digest_report.regression_risk_score == d("0.000000")
    assert digest_report.reason_codes == (
        "basketball_three_point_variance_regression_digest_clear",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="recent_three_point_accuracy must be a Decimal"):
        observation(recent_three_point_accuracy=_DecimalSubclass("0.430000"))
    with pytest.raises(ValueError, match="recent_game_count must be positive"):
        observation(recent_game_count="0.000000")
    with pytest.raises(ValueError, match="recent_game_count must be a whole number"):
        observation(recent_game_count="5.500000")
    with pytest.raises(ValueError, match="data_timestamp must be timezone-aware"):
        observation(data_timestamp=datetime(2026, 7, 4, 15, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_basketball_three_point_variance_regression_digest(
            (),
            config=module.BasketballThreePointVarianceRegressionDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 16, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="watch_accuracy_delta"):
        module.BasketballThreePointVarianceRegressionDigestConfig(
            watch_accuracy_delta=d("0.300000"),
            blocked_accuracy_delta=d("0.200000"),
        )
    with pytest.raises(ValueError, match="upstream_reason_codes must be a tuple"):
        observation(upstream_reason_codes=["official_box_score"])  # type: ignore[arg-type]

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="accuracy_delta must match"):
        replace(valid_row, accuracy_delta=d("0.999000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "basketball_three_point_variance_regression_inline",
                "basketball_three_point_variance_regression_watch_accuracy_delta",
            ),
        )

    valid_report = report(observation("source-reconcile"))
    with pytest.raises(ValueError, match="count must be positive"):
        module.BasketballThreePointVarianceRegressionReasonCodeCount(
            reason_code=(
                "basketball_three_point_variance_regression_digest_clear"
            ),
            count=d("0.000000"),
            row_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="count must be a whole number"):
        module.BasketballThreePointVarianceRegressionReasonCodeCount(
            reason_code=(
                "basketball_three_point_variance_regression_digest_clear"
            ),
            count=d("1.500000"),
            row_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="reason_code_counts must match reason_codes"):
        replace(
            valid_report,
            reason_code_counts=(
                module.BasketballThreePointVarianceRegressionReasonCodeCount(
                    reason_code=(
                        "basketball_three_point_variance_regression_digest_clear"
                    ),
                    count=d("2.000000"),
                    row_ratio=d("1.000000"),
                ),
            ),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):

        class _ObservationSubclass(
            module.BasketballThreePointVarianceRegressionObservation,
        ):
            pass


def test_hard_flags_are_enforced_on_config_observations_rows_and_report() -> None:
    module = digest()

    digest_report = report(observation("source-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.BasketballThreePointVarianceRegressionDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_string_numerics_and_revalidates_nested_public_dataclasses() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_basketball_three_point_variance_regression_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["recent_three_point_accuracy"] == "0.430000"
    assert payload["rows"][0]["data_timestamp"] == "2026-07-04T15:00:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "market_slug" not in lowered
                assert "question" not in lowered
                assert "payload_json" not in lowered
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "order" not in lowered
                assert "auth" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.BasketballThreePointVarianceRegressionDigestConfig(),
        observation("source-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            assert field.name not in {"market_slug", "question", "payload_json"}
            field_value = getattr(public_record, field.name)
            assert not isinstance(field_value, list)
            if _is_public_numeric(field_value):
                assert type(field_value) is Decimal, field.name

    tampered_row = _raw_dataclass_copy(digest_report.rows[0])
    object.__setattr__(tampered_row, "accuracy_delta", d("0.999000"))
    tampered_report = _raw_dataclass_copy(digest_report)
    object.__setattr__(tampered_report, "rows", (tampered_row,))
    with pytest.raises(ValueError, match="accuracy_delta must match"):
        module.market_research_basketball_three_point_variance_regression_digest_payload(
            tampered_report,
        )

    tampered_reason_code_count = _raw_dataclass_copy(
        digest_report.reason_code_counts[0],
    )
    object.__setattr__(tampered_reason_code_count, "count", d("999.000000"))
    tampered_reason_report = _raw_dataclass_copy(digest_report)
    object.__setattr__(
        tampered_reason_report,
        "reason_code_counts",
        (tampered_reason_code_count,),
    )
    with pytest.raises(ValueError, match="reason_code_counts|count"):
        module.market_research_basketball_three_point_variance_regression_digest_payload(
            tampered_reason_report,
        )

    source = Path(
        "src/polymarket_alpha_lab/"
        "market_research_basketball_three_point_variance_regression_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Attribute) and node.attr == "asdict":
            raise AssertionError("module must not call dataclasses.asdict")
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "submit_order",
        "cancel_order",
        "replace_order",
        "market_slug",
        "payload_json",
    ):
        assert forbidden not in source.lower()


def _raw_dataclass_copy(value: Any) -> Any:
    copied = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(copied, field.name, getattr(value, field.name))
    return copied


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
