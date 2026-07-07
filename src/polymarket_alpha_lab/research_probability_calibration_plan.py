"""Pure probability event research calibration plan."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_PROBABILITY_CALIBRATION_PLAN_VERSION = (
    "research-probability-calibration-plan-v1"
)

COUNT_QUANTUM = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_SCORE = Decimal("0.000000")
ONE_SCORE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

CALIBRATION_STATUSES = ("pass", "watch", "block")
STATUS_PRIORITY = {
    "block": Decimal("1"),
    "watch": Decimal("2"),
    "pass": Decimal("3"),
}
INPUT_REASON_CODES = ("research_probability_calibration_plan_input",)
STEP_REASON_CODES = (
    "research_probability_calibration_plan_gap_block",
    "research_probability_calibration_plan_low_confidence_block",
    "research_probability_calibration_plan_thin_history_watch",
    "research_probability_calibration_plan_low_confidence_watch",
    "research_probability_calibration_plan_gap_watch",
    "research_probability_calibration_plan_pass",
)
PLAN_REASON_CODES = (
    "research_probability_calibration_plan_no_cases",
    *STEP_REASON_CODES,
)
NEXT_RESEARCH_STEPS = {
    "research_probability_calibration_plan_gap_block": (
        "hold_public_probability_score_for_review"
    ),
    "research_probability_calibration_plan_low_confidence_block": (
        "hold_public_probability_score_for_review"
    ),
    "research_probability_calibration_plan_thin_history_watch": (
        "expand_resolution_sample_review"
    ),
    "research_probability_calibration_plan_low_confidence_watch": (
        "refresh_confidence_review"
    ),
    "research_probability_calibration_plan_gap_watch": (
        "track_calibration_gap_next_cycle"
    ),
    "research_probability_calibration_plan_pass": "clear_for_report_publication",
}

__all__ = (
    "DEFAULT_RESEARCH_PROBABILITY_CALIBRATION_PLAN_VERSION",
    "ResearchProbabilityCalibrationCaseInput",
    "ResearchProbabilityCalibrationPlan",
    "ResearchProbabilityCalibrationPlanConfig",
    "ResearchProbabilityCalibrationStep",
    "build_research_probability_calibration_plan",
    "research_probability_calibration_plan_payload",
)


@dataclass(frozen=True)
class ResearchProbabilityCalibrationPlanConfig:
    plan_version: str = DEFAULT_RESEARCH_PROBABILITY_CALIBRATION_PLAN_VERSION
    watch_gap_threshold: Decimal = Decimal("0.050000")
    block_gap_threshold: Decimal = Decimal("0.120000")
    minimum_observation_count: Decimal = Decimal("20")
    minimum_confidence_score: Decimal = Decimal("0.600000")
    block_confidence_floor: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("plan_version", self.plan_version)
        for field_name in (
            "watch_gap_threshold",
            "block_gap_threshold",
            "minimum_confidence_score",
            "block_confidence_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_observation_count",
            _normalize_positive_count(
                "minimum_observation_count",
                self.minimum_observation_count,
            ),
        )
        if self.block_gap_threshold <= self.watch_gap_threshold:
            raise ValueError("block_gap_threshold must exceed watch_gap_threshold")
        if self.block_confidence_floor >= self.minimum_confidence_score:
            raise ValueError("block_confidence_floor must be below minimum_confidence_score")
        require_paper_only_flags("ResearchProbabilityCalibrationPlanConfig", self)


@dataclass(frozen=True)
class ResearchProbabilityCalibrationCaseInput:
    case_sequence: Decimal
    forecast_probability: Decimal
    observed_frequency: Decimal
    observation_count: Decimal
    evidence_confidence_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "case_sequence",
            _normalize_positive_count("case_sequence", self.case_sequence),
        )
        for field_name in (
            "forecast_probability",
            "observed_frequency",
            "evidence_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "observation_count",
            _normalize_nonnegative_count("observation_count", self.observation_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                INPUT_REASON_CODES,
            ),
        )
        require_paper_only_flags("ResearchProbabilityCalibrationCaseInput", self)


@dataclass(frozen=True)
class ResearchProbabilityCalibrationStep:
    priority_rank: Decimal
    case_sequence: Decimal
    forecast_probability: Decimal
    observed_frequency: Decimal
    observation_count: Decimal
    evidence_confidence_score: Decimal
    calibration_gap: Decimal
    reliability_score: Decimal
    calibration_status: str
    next_research_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("priority_rank", "case_sequence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "forecast_probability",
            "observed_frequency",
            "evidence_confidence_score",
            "calibration_gap",
            "reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "observation_count",
            _normalize_nonnegative_count("observation_count", self.observation_count),
        )
        _require_member("calibration_status", self.calibration_status, CALIBRATION_STATUSES)
        object.__setattr__(
            self,
            "next_research_step",
            _require_member(
                "next_research_step",
                self.next_research_step,
                tuple(NEXT_RESEARCH_STEPS.values()),
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                STEP_REASON_CODES,
            ),
        )
        _validate_step(self)
        require_paper_only_flags("ResearchProbabilityCalibrationStep", self)


@dataclass(frozen=True)
class ResearchProbabilityCalibrationPlan:
    plan_version: str
    input_case_count: Decimal
    step_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_calibration_gap: Decimal
    average_reliability_score: Decimal
    plan_status: str
    reason_codes: tuple[str, ...]
    steps: tuple[ResearchProbabilityCalibrationStep, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("plan_version", self.plan_version)
        for field_name in (
            "input_case_count",
            "step_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_calibration_gap", "average_reliability_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        _require_member("plan_status", self.plan_status, CALIBRATION_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                PLAN_REASON_CODES,
            ),
        )
        object.__setattr__(self, "steps", _normalize_steps(self.steps))
        _validate_plan(self)
        reject_unsafe_surface_fields("research probability calibration plan", self)
        require_paper_only_flags("ResearchProbabilityCalibrationPlan", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_probability_calibration_plan_payload(self)


def build_research_probability_calibration_plan(
    inputs: list[ResearchProbabilityCalibrationCaseInput]
    | tuple[ResearchProbabilityCalibrationCaseInput, ...],
    *,
    config: ResearchProbabilityCalibrationPlanConfig,
) -> ResearchProbabilityCalibrationPlan:
    if type(config) is not ResearchProbabilityCalibrationPlanConfig:
        raise ValueError("config must be a ResearchProbabilityCalibrationPlanConfig")
    require_paper_only_flags("config", config)
    rows = _normalize_inputs(inputs)
    unsorted_steps = tuple(_step_for_case(row, config) for row in rows)
    sorted_steps = tuple(sorted(unsorted_steps, key=_step_sort_key))
    steps = tuple(
        _copy_step_with_priority_rank(step, _count(index + 1))
        for index, step in enumerate(sorted_steps)
    )
    return ResearchProbabilityCalibrationPlan(
        plan_version=config.plan_version,
        input_case_count=_count(len(rows)),
        step_count=_count(len(steps)),
        pass_count=_status_count(steps, "pass"),
        watch_count=_status_count(steps, "watch"),
        block_count=_status_count(steps, "block"),
        average_calibration_gap=_average_score(
            tuple(step.calibration_gap for step in steps),
        ),
        average_reliability_score=_average_score(
            tuple(step.reliability_score for step in steps),
        ),
        plan_status=_plan_status(steps),
        reason_codes=_plan_reason_codes(steps),
        steps=steps,
    )


def research_probability_calibration_plan_payload(
    report: ResearchProbabilityCalibrationPlan,
) -> dict[str, Any]:
    if type(report) is not ResearchProbabilityCalibrationPlan:
        raise ValueError("report must be a ResearchProbabilityCalibrationPlan")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("research probability calibration plan", report)
    return json_ready_no_floats(report)


def _step_for_case(
    row: ResearchProbabilityCalibrationCaseInput,
    config: ResearchProbabilityCalibrationPlanConfig,
) -> ResearchProbabilityCalibrationStep:
    calibration_gap = _calibration_gap(
        row.forecast_probability,
        row.observed_frequency,
    )
    reliability_score = _reliability_score(
        calibration_gap,
        row.evidence_confidence_score,
    )
    reason_codes = _step_reason_codes(row, config, calibration_gap)
    return ResearchProbabilityCalibrationStep(
        priority_rank=Decimal("1"),
        case_sequence=row.case_sequence,
        forecast_probability=row.forecast_probability,
        observed_frequency=row.observed_frequency,
        observation_count=row.observation_count,
        evidence_confidence_score=row.evidence_confidence_score,
        calibration_gap=calibration_gap,
        reliability_score=reliability_score,
        calibration_status=_status_for_reason_codes(reason_codes),
        next_research_step=NEXT_RESEARCH_STEPS[reason_codes[0]],
        reason_codes=reason_codes,
    )


def _copy_step_with_priority_rank(
    step: ResearchProbabilityCalibrationStep,
    priority_rank: Decimal,
) -> ResearchProbabilityCalibrationStep:
    return ResearchProbabilityCalibrationStep(
        priority_rank=priority_rank,
        case_sequence=step.case_sequence,
        forecast_probability=step.forecast_probability,
        observed_frequency=step.observed_frequency,
        observation_count=step.observation_count,
        evidence_confidence_score=step.evidence_confidence_score,
        calibration_gap=step.calibration_gap,
        reliability_score=step.reliability_score,
        calibration_status=step.calibration_status,
        next_research_step=step.next_research_step,
        reason_codes=step.reason_codes,
    )


def _calibration_gap(forecast_probability: Decimal, observed_frequency: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_score(abs(forecast_probability - observed_frequency))


def _reliability_score(
    calibration_gap: Decimal,
    evidence_confidence_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_score((ONE_SCORE - calibration_gap) * evidence_confidence_score)


def _step_reason_codes(
    row: ResearchProbabilityCalibrationCaseInput,
    config: ResearchProbabilityCalibrationPlanConfig,
    calibration_gap: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if calibration_gap >= config.block_gap_threshold:
        codes.append("research_probability_calibration_plan_gap_block")
    if row.evidence_confidence_score <= config.block_confidence_floor:
        codes.append("research_probability_calibration_plan_low_confidence_block")
    if row.observation_count < config.minimum_observation_count:
        codes.append("research_probability_calibration_plan_thin_history_watch")
    if (
        row.evidence_confidence_score < config.minimum_confidence_score
        and row.evidence_confidence_score > config.block_confidence_floor
    ):
        codes.append("research_probability_calibration_plan_low_confidence_watch")
    if (
        calibration_gap >= config.watch_gap_threshold
        and calibration_gap < config.block_gap_threshold
    ):
        codes.append("research_probability_calibration_plan_gap_watch")
    if not codes:
        codes.append("research_probability_calibration_plan_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes), STEP_REASON_CODES)


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _step_sort_key(
    step: ResearchProbabilityCalibrationStep,
) -> tuple[Decimal, Decimal, Decimal]:
    return (
        STATUS_PRIORITY[step.calibration_status],
        -step.calibration_gap,
        step.case_sequence,
    )


def _plan_reason_codes(
    steps: tuple[ResearchProbabilityCalibrationStep, ...],
) -> tuple[str, ...]:
    if not steps:
        return ("research_probability_calibration_plan_no_cases",)
    return tuple(
        reason_code
        for reason_code in STEP_REASON_CODES
        if any(reason_code in step.reason_codes for step in steps)
    )


def _plan_status(steps: tuple[ResearchProbabilityCalibrationStep, ...]) -> str:
    if not steps:
        return "watch"
    if any(step.calibration_status == "block" for step in steps):
        return "block"
    if any(step.calibration_status == "watch" for step in steps):
        return "watch"
    return "pass"


def _status_count(
    steps: tuple[ResearchProbabilityCalibrationStep, ...],
    calibration_status: str,
) -> Decimal:
    return _count(sum(1 for step in steps if step.calibration_status == calibration_status))


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_score(sum(values, ZERO_SCORE) / _count(len(values)))


def _normalize_inputs(
    inputs: list[ResearchProbabilityCalibrationCaseInput]
    | tuple[ResearchProbabilityCalibrationCaseInput, ...],
) -> tuple[ResearchProbabilityCalibrationCaseInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_case_sequences: set[Decimal] = set()
    for row in rows:
        if type(row) is not ResearchProbabilityCalibrationCaseInput:
            raise ValueError(
                "inputs must contain ResearchProbabilityCalibrationCaseInput values",
            )
        require_paper_only_flags("input", row)
        if row.case_sequence in seen_case_sequences:
            raise ValueError("inputs must not contain duplicate case_sequence values")
        seen_case_sequences.add(row.case_sequence)
    return rows


def _normalize_steps(
    value: object,
) -> tuple[ResearchProbabilityCalibrationStep, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("steps must be a list or tuple")
    steps = tuple(value)
    seen_case_sequences: set[Decimal] = set()
    for step in steps:
        if type(step) is not ResearchProbabilityCalibrationStep:
            raise ValueError("steps must contain ResearchProbabilityCalibrationStep values")
        require_paper_only_flags("step", step)
        if step.case_sequence in seen_case_sequences:
            raise ValueError("steps must contain unique case_sequence values")
        seen_case_sequences.add(step.case_sequence)
    expected_ranks = tuple(_count(index + 1) for index in range(len(steps)))
    if tuple(step.priority_rank for step in steps) != expected_ranks:
        raise ValueError("steps must use contiguous priority_rank values")
    if steps != tuple(sorted(steps, key=_step_sort_key)):
        raise ValueError("steps must use deterministic priority sort")
    return steps


def _validate_step(step: ResearchProbabilityCalibrationStep) -> None:
    expected_gap = _calibration_gap(step.forecast_probability, step.observed_frequency)
    if step.calibration_gap != expected_gap:
        raise ValueError("calibration_gap must match probabilities")
    expected_reliability = _reliability_score(
        step.calibration_gap,
        step.evidence_confidence_score,
    )
    if step.reliability_score != expected_reliability:
        raise ValueError("reliability_score must match calibration inputs")
    if step.calibration_status != _status_for_reason_codes(step.reason_codes):
        raise ValueError("calibration_status must match reason_codes")
    if step.next_research_step != NEXT_RESEARCH_STEPS[step.reason_codes[0]]:
        raise ValueError("next_research_step must match reason_codes")


def _validate_plan(report: ResearchProbabilityCalibrationPlan) -> None:
    if report.input_case_count != report.step_count:
        raise ValueError("input_case_count must match step_count")
    if report.step_count != _count(len(report.steps)):
        raise ValueError("step_count must match steps")
    if report.pass_count != _status_count(report.steps, "pass"):
        raise ValueError("pass_count must match steps")
    if report.watch_count != _status_count(report.steps, "watch"):
        raise ValueError("watch_count must match steps")
    if report.block_count != _status_count(report.steps, "block"):
        raise ValueError("block_count must match steps")
    if report.average_calibration_gap != _average_score(
        tuple(step.calibration_gap for step in report.steps),
    ):
        raise ValueError("average_calibration_gap must match steps")
    if report.average_reliability_score != _average_score(
        tuple(step.reliability_score for step in report.steps),
    ):
        raise ValueError("average_reliability_score must match steps")
    if report.plan_status != _plan_status(report.steps):
        raise ValueError("plan_status must match steps")
    if report.reason_codes != _plan_reason_codes(report.steps):
        raise ValueError("reason_codes must match steps")


def _require_canonical_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{name} must be canonical")
    return value


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be supported")
    return value


def _normalize_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must not be empty")
    for reason_code in reason_codes:
        _require_member(name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{name} must not contain duplicates")
    if reason_codes != tuple(code for code in allowed if code in reason_codes):
        raise ValueError(f"{name} must use deterministic sort")
    return reason_codes


def _normalize_positive_count(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO_COUNT:
        raise ValueError(f"{name} must be positive")
    return _quantize_count(name, decimal_value)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize_count(name, decimal_value)


def _normalize_score(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO_SCORE or decimal_value > ONE_SCORE:
        raise ValueError(f"{name} must be between zero and one")
    quantized = _quantize_score(decimal_value)
    if quantized != decimal_value:
        raise ValueError(f"{name} must use six decimal places")
    return quantized


def _quantize_count(name: str, value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{name} must be an integer Decimal")
    return quantized


def _quantize_score(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANTUM)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)
