from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_shadow_outcome_replay_report import (
    DEFAULT_RESEARCH_STRATEGY_SHADOW_OUTCOME_REPLAY_REPORT_VERSION,
    ResearchStrategyShadowOutcomeReplayConfig,
    ResearchStrategyShadowOutcomeReplayInput,
    ResearchStrategyShadowOutcomeReplayReasonCodeCount,
    ResearchStrategyShadowOutcomeReplayReport,
    ResearchStrategyShadowOutcomeReplayRow,
    build_research_strategy_shadow_outcome_replay_report,
    research_strategy_shadow_outcome_replay_report_digest,
    research_strategy_shadow_outcome_replay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_shadow_outcome_replay_report.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyShadowOutcomeReplayConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_STRATEGY_SHADOW_OUTCOME_REPLAY_REPORT_VERSION,
        "probability_gap_watch": d("0.150000"),
        "probability_gap_block": d("0.300000"),
        "low_confidence_floor": d("0.550000"),
        "review_age_seconds_watch": d("2592000.000000"),
    }
    values.update(overrides)
    return ResearchStrategyShadowOutcomeReplayConfig(**values)


def observation(
    public_label: str = "research-alpha",
    *,
    submitted_probability: Decimal = d("0.800000"),
    outcome_probability: Decimal = d("1.000000"),
    calibration_weight: Decimal = d("1.000000"),
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    hypothetical: bool = False,
    reason_codes: tuple[str, ...] = ("shadow_replay_input_available",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyShadowOutcomeReplayInput:
    return ResearchStrategyShadowOutcomeReplayInput(
        public_label=public_label,
        submitted_probability=submitted_probability,
        outcome_probability=outcome_probability,
        calibration_weight=calibration_weight,
        observed_at=observed_at,
        hypothetical=hypothetical,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchStrategyShadowOutcomeReplayInput,
    cfg: ResearchStrategyShadowOutcomeReplayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyShadowOutcomeReplayReport:
    return build_research_strategy_shadow_outcome_replay_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def test_pass_report_uses_decimal_payload_strings() -> None:
    replay = report(
        observation(
            "research-clear",
            submitted_probability=d("0.900000"),
            outcome_probability=d("1.000000"),
        ),
    )

    assert is_dataclass(replay)
    assert replay.generated_at == GENERATED_AT
    assert replay.config_version == DEFAULT_RESEARCH_STRATEGY_SHADOW_OUTCOME_REPLAY_REPORT_VERSION
    assert replay.candidate_count == d("1.000000")
    assert replay.pass_count == d("1.000000")
    assert replay.watch_count == ZERO
    assert replay.block_count == ZERO
    assert replay.hypothetical_count == ZERO
    assert replay.status == "pass"
    assert replay.reason_codes == ("shadow_outcome_replay_pass",)
    assert replay.paper_only is True
    assert replay.report_only is True
    assert replay.readonly is True

    row = replay.replay_rows[0]
    assert row.public_label == "research-clear"
    assert row.status == "pass"
    assert row.absolute_probability_error == d("0.100000")
    assert row.weighted_probability_error == d("0.100000")
    assert row.age_seconds == d("3600.000000")
    assert row.reason_codes == (
        "shadow_replay_calibrated",
        "shadow_replay_input_available",
    )

    payload = research_strategy_shadow_outcome_replay_report_payload(replay)
    assert payload["candidate_count"] == "1.000000"
    assert payload["replay_rows"][0]["absolute_probability_error"] == "0.100000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float(payload)
    json.dumps(payload, sort_keys=True)


def test_watch_and_block_status_rollups_are_public_only() -> None:
    replay = report(
        observation(
            "watch-gap",
            submitted_probability=d("0.800000"),
            outcome_probability=d("0.600000"),
            observed_at=GENERATED_AT - timedelta(days=40),
        ),
        observation(
            "block-gap",
            submitted_probability=d("0.700000"),
            outcome_probability=d("0.000000"),
            calibration_weight=d("2.000000"),
        ),
        observation(
            "hypothetical-watch",
            submitted_probability=d("0.520000"),
            outcome_probability=d("0.600000"),
            hypothetical=True,
        ),
    )

    assert replay.status == "block"
    assert replay.pass_count == ZERO
    assert replay.watch_count == d("2.000000")
    assert replay.block_count == d("1.000000")
    assert replay.hypothetical_count == d("1.000000")
    assert replay.mean_absolute_probability_error == d("0.326667")
    assert replay.max_absolute_probability_error == d("0.700000")
    assert replay.weighted_probability_error_total == d("1.680000")
    assert replay.reason_codes == (
        "shadow_outcome_replay_block",
        "hypothetical_settlement_watch",
        "low_confidence_watch",
        "probability_gap_block",
        "probability_gap_watch",
        "replay_age_watch",
    )
    assert tuple(row.status for row in replay.replay_rows) == ("block", "watch", "watch")
    assert set(row.status for row in replay.replay_rows) <= {"pass", "watch", "block"}


def test_empty_inputs_block_with_no_inputs_reason_count() -> None:
    replay = report()

    assert replay.status == "block"
    assert replay.candidate_count == ZERO
    assert replay.pass_count == ZERO
    assert replay.watch_count == ZERO
    assert replay.block_count == ZERO
    assert replay.mean_absolute_probability_error == ZERO
    assert replay.max_absolute_probability_error == ZERO
    assert replay.reason_codes == ("research_strategy_shadow_outcome_replay_no_inputs",)
    assert replay.reason_code_counts == (
        ResearchStrategyShadowOutcomeReplayReasonCodeCount(
            reason_code="research_strategy_shadow_outcome_replay_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert replay.replay_rows == ()


def test_utc_normalization_for_generated_and_observed_times() -> None:
    replay = report(
        observation(
            observed_at=datetime(
                2026,
                7,
                4,
                7,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            4,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert replay.generated_at == GENERATED_AT
    assert replay.replay_rows[0].observed_at == datetime(2026, 7, 4, 11, 0, tzinfo=UTC)
    assert replay.replay_rows[0].age_seconds == d("3600.000000")


def test_decimal_and_type_rejection_at_public_boundary() -> None:
    with pytest.raises(ValueError, match="submitted_probability"):
        observation(submitted_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="outcome_probability"):
        observation(outcome_probability=d("1.000001"))
    with pytest.raises(ValueError, match="calibration_weight"):
        observation(calibration_weight=d("0.000000"))
    with pytest.raises(ValueError, match="probability_gap_watch"):
        config(probability_gap_watch=_DecimalSubclass("0.150000"))
    with pytest.raises(ValueError, match="probability_gap_watch"):
        config(probability_gap_watch=d("0.400000"), probability_gap_block=d("0.300000"))
    with pytest.raises(ValueError, match="hypothetical"):
        observation(hypothetical=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 4, 11, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation("aware-time"), generated_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, 11, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        observation(
            observed_at=datetime(2026, 7, 4, 11, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))


def test_public_leak_rejection_for_values_and_payload_revalidation() -> None:
    unsafe_values = (
        "raw" + "_" + "candidate" + "-42",
        "market" + "_" + "id" + "-99",
        "market" + "_" + "slug" + "-event",
        "market" + "_" + "question" + "-copy",
        "sou" + "rce" + "-paragraph",
        "http" + "s://example.test/a",
        "d" + "sn" + "-value",
        "ta" + "ble" + "-name",
        "to" + "ken" + "-value",
        "wa" + "llet" + "-field",
        "au" + "th" + "-field",
        "or" + "der" + "-field",
        "pos" + "ition" + "-field",
        "tr" + "ade" + "-field",
        "bu" + "y" + "-field",
        "se" + "ll" + "-field",
        "re" + "commend" + "-field",
    )

    for value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe"):
            observation(public_label=value)
        with pytest.raises(ValueError, match="unsafe"):
            observation(reason_codes=(value,))

    replay = report(observation("tampered-safe"))
    object.__setattr__(replay.replay_rows[0], "public_label", "market" + "_" + "id")
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_shadow_outcome_replay_report_payload(replay)


def test_hard_flags_frozen_dataclasses_and_decimal_public_numbers() -> None:
    replay = report(observation("frozen"))

    assert is_dataclass(ResearchStrategyShadowOutcomeReplayConfig)
    assert is_dataclass(ResearchStrategyShadowOutcomeReplayInput)
    assert is_dataclass(ResearchStrategyShadowOutcomeReplayRow)
    assert is_dataclass(ResearchStrategyShadowOutcomeReplayReasonCodeCount)
    assert is_dataclass(ResearchStrategyShadowOutcomeReplayReport)
    with pytest.raises(FrozenInstanceError):
        replay.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        replay.replay_rows[0].absolute_probability_error = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(replay, readonly=False)

    for item in (replay, *replay.replay_rows, *replay.reason_code_counts):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name
    for field_name in (
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "hypothetical_count",
        "mean_absolute_probability_error",
        "max_absolute_probability_error",
        "weighted_probability_error_total",
    ):
        assert type(getattr(replay, field_name)) is Decimal


def test_deterministic_payload_sorting_reason_counts_and_digest_consistency() -> None:
    first = report(
        observation(
            "zeta-watch",
            submitted_probability=d("0.800000"),
            outcome_probability=d("0.600000"),
        ),
        observation(
            "alpha-block",
            submitted_probability=d("0.700000"),
            outcome_probability=d("0.000000"),
        ),
        observation(
            "alpha-pass",
            submitted_probability=d("0.900000"),
            outcome_probability=d("1.000000"),
            reason_codes=("calibration_notes_available", "shadow_replay_input_available"),
        ),
    )
    second = report(
        observation(
            "alpha-pass",
            submitted_probability=d("0.900000"),
            outcome_probability=d("1.000000"),
            reason_codes=("calibration_notes_available", "shadow_replay_input_available"),
        ),
        observation(
            "alpha-block",
            submitted_probability=d("0.700000"),
            outcome_probability=d("0.000000"),
        ),
        observation(
            "zeta-watch",
            submitted_probability=d("0.800000"),
            outcome_probability=d("0.600000"),
        ),
    )

    assert research_strategy_shadow_outcome_replay_report_payload(first) == (
        research_strategy_shadow_outcome_replay_report_payload(second)
    )
    assert tuple(row.public_label for row in first.replay_rows) == (
        "alpha-block",
        "zeta-watch",
        "alpha-pass",
    )
    assert first.reason_code_counts == (
        ResearchStrategyShadowOutcomeReplayReasonCodeCount(
            reason_code="shadow_replay_input_available",
            count=d("3.000000"),
        ),
        ResearchStrategyShadowOutcomeReplayReasonCodeCount(
            reason_code="calibration_notes_available",
            count=d("1.000000"),
        ),
        ResearchStrategyShadowOutcomeReplayReasonCodeCount(
            reason_code="probability_gap_block",
            count=d("1.000000"),
        ),
        ResearchStrategyShadowOutcomeReplayReasonCodeCount(
            reason_code="probability_gap_watch",
            count=d("1.000000"),
        ),
        ResearchStrategyShadowOutcomeReplayReasonCodeCount(
            reason_code="shadow_replay_calibrated",
            count=d("1.000000"),
        ),
    )
    payload = research_strategy_shadow_outcome_replay_report_payload(first)
    digest = research_strategy_shadow_outcome_replay_report_digest(first)
    assert digest == hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()
    assert digest == research_strategy_shadow_outcome_replay_report_digest(second)


def test_report_consistency_rejects_tampering() -> None:
    replay = report(
        observation("consistent-a"),
        observation(
            "consistent-b",
            submitted_probability=d("0.900000"),
            outcome_probability=d("1.000000"),
        ),
    )

    with pytest.raises(ValueError, match="candidate_count"):
        replace(replay, candidate_count=d("3.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(replay, status="block")
    with pytest.raises(ValueError, match="mean_absolute_probability_error"):
        replace(replay, mean_absolute_probability_error=d("2.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(replay, reason_codes=("shadow_outcome_replay_block",))
    with pytest.raises(ValueError, match="replay_rows"):
        replace(replay, replay_rows=tuple(reversed(replay.replay_rows)))

    object.__setattr__(replay.replay_rows[0], "absolute_probability_error", d("0.1000000"))
    with pytest.raises(ValueError, match="six decimal"):
        research_strategy_shadow_outcome_replay_report_payload(replay)


def test_public_dataclasses_reject_subclassing_and_subclass_instances() -> None:
    replay = report(observation("exact-type"))
    public_values = (
        config(),
        observation("exact-input"),
        replay.replay_rows[0],
        replay.reason_code_counts[0],
        replay,
    )

    for value in public_values:
        public_type = type(value)
        kwargs = {field.name: getattr(value, field.name) for field in fields(value)}

        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})

        subclass = _make_subclass_bypassing_final_guard(public_type)
        with pytest.raises(ValueError, match="must be exactly"):
            subclass(**kwargs)


def test_public_exports_are_exact() -> None:
    import polymarket_alpha_lab.research_strategy_shadow_outcome_replay_report as replay

    assert replay.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_SHADOW_OUTCOME_REPLAY_REPORT_VERSION",
        "ResearchStrategyShadowOutcomeReplayConfig",
        "ResearchStrategyShadowOutcomeReplayInput",
        "ResearchStrategyShadowOutcomeReplayReasonCodeCount",
        "ResearchStrategyShadowOutcomeReplayReport",
        "ResearchStrategyShadowOutcomeReplayRow",
        "build_research_strategy_shadow_outcome_replay_report",
        "research_strategy_shadow_outcome_replay_report_digest",
        "research_strategy_shadow_outcome_replay_report_payload",
    )


def test_static_forbidden_io_and_public_surface_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "sqlite3",
        "psycopg",
        "supabase",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_dataclass_helpers = {"asdict"}
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__", *forbidden_dataclass_helpers}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
            assert all(
                alias.name not in forbidden_dataclass_helpers
                for alias in node.names
            )


def _make_subclass_bypassing_final_guard(public_type: type[object]) -> type[object]:
    sentinel = object()
    original_init_subclass = public_type.__dict__.get("__init_subclass__", sentinel)
    public_type.__init_subclass__ = classmethod(lambda cls, **kwargs: None)  # type: ignore[attr-defined]
    try:
        return type(f"{public_type.__name__}BypassedSubclass", (public_type,), {})
    finally:
        if original_init_subclass is sentinel:
            delattr(public_type, "__init_subclass__")
        else:
            public_type.__init_subclass__ = original_init_subclass  # type: ignore[attr-defined]
