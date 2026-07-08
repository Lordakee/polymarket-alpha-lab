"""Expected information gain decay report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_STRATEGY_EXPECTED_INFORMATION_GAIN_DECAY_REPORT_CONFIG_VERSION = (
    "research-strategy-expected-information-gain-decay-report-v0"
)

DECIMAL_CONTEXT_PRECISION = 28
SCORE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_SCORE = Decimal("0").quantize(SCORE_QUANTUM)
ONE_SCORE = Decimal("1").quantize(SCORE_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)

SOURCE_AGING_WEIGHT = Decimal("0.200000")
REDUCED_UNCERTAINTY_WEIGHT = Decimal("0.200000")
MARKET_MOVEMENT_WEIGHT = Decimal("0.100000")
COST_DRAG_WEIGHT = Decimal("0.200000")
LIQUIDITY_RELIABILITY_WEIGHT = Decimal("0.200000")
RESOLUTION_AMBIGUITY_WEIGHT = Decimal("0.100000")

STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
NEXT_STEPS = {
    "pass": "continue_report_only_eig_decay_monitoring",
    "watch": "review_report_only_eig_decay_inputs",
    "block": "pause_report_only_eig_decay_review",
}
STATUS_REASON_CODES = (
    "expected_information_gain_decay_no_inputs",
    "expected_information_gain_decay_pass",
    "expected_information_gain_decay_watch",
    "expected_information_gain_decay_block",
)
DRIVER_REASON_CODES = (
    "source_aging_decay",
    "reduced_uncertainty_decay",
    "market_movement_decay",
    "cost_drag_decay",
    "liquidity_reliability_decay",
    "resolution_ambiguity_decay",
)
BASE_REASON_CODES = STATUS_REASON_CODES + DRIVER_REASON_CODES
_UNSAFE_PUBLIC_FRAGMENTS = (
    "can" + "didate",
    "mar" + "ket_id",
    "mar" + "ket-slug",
    "mar" + "ket_slug",
    "ques" + "tion",
    "source_" + "u" + "rl",
    "source_" + "text",
    "u" + "rl",
    "http",
    "://",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "wa" + "llet",
    "or" + "der",
    "tra" + "de",
    "pos" + "ition",
    "li" + "ve",
    "b" + "uy",
    "se" + "ll",
    "reco" + "mmend",
)


@dataclass(frozen=True)
class ResearchStrategyExpectedInformationGainDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EXPECTED_INFORMATION_GAIN_DECAY_REPORT_CONFIG_VERSION
    )
    fresh_source_age_hours: Decimal = Decimal("2.000000")
    stale_source_age_span_hours: Decimal = Decimal("22.000000")
    watch_decay_threshold: Decimal = Decimal("0.250000")
    block_decay_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyExpectedInformationGainDecayConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "fresh_source_age_hours",
            _normalize_nonnegative_score(
                "fresh_source_age_hours",
                self.fresh_source_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "stale_source_age_span_hours",
            _normalize_positive_score(
                "stale_source_age_span_hours",
                self.stale_source_age_span_hours,
            ),
        )
        for field_name in ("watch_decay_threshold", "block_decay_threshold"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_decay_threshold >= self.block_decay_threshold:
            raise ValueError("watch_decay_threshold must be below block_decay_threshold")
        require_paper_only_flags("config", self)
        reject_unsafe_surface_fields("eig decay config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyExpectedInformationGainDecayObservation:
    public_research_key: str
    observed_at: datetime
    source_age_hours: Decimal
    remaining_uncertainty_probability: Decimal
    market_movement_probability: Decimal
    cost_drag_probability: Decimal
    liquidity_reliability_probability: Decimal
    resolution_ambiguity_probability: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyExpectedInformationGainDecayObservation,
            "observation",
        )
        _require_public_identifier("public_research_key", self.public_research_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_age_hours",
            _normalize_nonnegative_score("source_age_hours", self.source_age_hours),
        )
        for field_name in (
            "remaining_uncertainty_probability",
            "market_movement_probability",
            "cost_drag_probability",
            "liquidity_reliability_probability",
            "resolution_ambiguity_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_public_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
                allow_empty=True,
            ),
        )
        require_paper_only_flags("observation", self)
        reject_unsafe_surface_fields("eig decay observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchStrategyExpectedInformationGainDecayRow:
    public_research_key: str
    observed_at: datetime
    source_age_hours: Decimal
    remaining_uncertainty_probability: Decimal
    market_movement_probability: Decimal
    cost_drag_probability: Decimal
    liquidity_reliability_probability: Decimal
    resolution_ambiguity_probability: Decimal
    source_aging_decay_score: Decimal
    reduced_uncertainty_decay_score: Decimal
    market_movement_decay_score: Decimal
    cost_drag_decay_score: Decimal
    liquidity_reliability_decay_score: Decimal
    resolution_ambiguity_decay_score: Decimal
    expected_information_gain_decay_score: Decimal
    retained_information_gain_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyExpectedInformationGainDecayRow, "row")
        _require_public_identifier("public_research_key", self.public_research_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_age_hours",
            _normalize_nonnegative_score("source_age_hours", self.source_age_hours),
        )
        for field_name in (
            "remaining_uncertainty_probability",
            "market_movement_probability",
            "cost_drag_probability",
            "liquidity_reliability_probability",
            "resolution_ambiguity_probability",
            "source_aging_decay_score",
            "reduced_uncertainty_decay_score",
            "market_movement_decay_score",
            "cost_drag_decay_score",
            "liquidity_reliability_decay_score",
            "resolution_ambiguity_decay_score",
            "expected_information_gain_decay_score",
            "retained_information_gain_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        require_paper_only_flags("row", self)
        reject_unsafe_surface_fields("eig decay row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchStrategyExpectedInformationGainDecayReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_expected_information_gain_decay_score: Decimal
    average_expected_information_gain_decay_score: Decimal
    min_retained_information_gain_score: Decimal
    status: str
    next_step: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyExpectedInformationGainDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyExpectedInformationGainDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_expected_information_gain_decay_score",
            "average_expected_information_gain_decay_score",
            "min_retained_information_gain_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        _require_member("next_step", self.next_step, tuple(NEXT_STEPS.values()))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        require_paper_only_flags("report", self)
        reject_unsafe_surface_fields("eig decay report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError("derived_validation_digest must match report fields")

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_expected_information_gain_decay_report_payload(self)


@dataclass(frozen=True)
class ResearchStrategyExpectedInformationGainDecayReportDigest:
    generated_at: datetime
    config_version: str
    report_digest: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_expected_information_gain_decay_score: Decimal
    average_expected_information_gain_decay_score: Decimal
    min_retained_information_gain_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyExpectedInformationGainDecayReportDigest,
            "digest",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "report_digest",
            _normalize_sha256_digest("report_digest", self.report_digest),
        )
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_expected_information_gain_decay_score",
            "average_expected_information_gain_decay_score",
            "min_retained_information_gain_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        require_paper_only_flags("digest", self)
        reject_unsafe_surface_fields("eig decay digest", self)
        _reject_unsafe_public_payload("digest", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_expected_information_gain_decay_report_payload(self)


def build_research_strategy_expected_information_gain_decay_report(
    observations: tuple[ResearchStrategyExpectedInformationGainDecayObservation, ...]
    | list[ResearchStrategyExpectedInformationGainDecayObservation],
    *,
    config: ResearchStrategyExpectedInformationGainDecayConfig,
    generated_at: datetime,
) -> ResearchStrategyExpectedInformationGainDecayReport:
    if type(config) is not ResearchStrategyExpectedInformationGainDecayConfig:
        raise ValueError(
            "config must be a ResearchStrategyExpectedInformationGainDecayConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations, generated_at_utc)
    rows = tuple(sorted((_row_for_observation(item, config) for item in normalized), key=_row_key))
    status = _report_status(rows)
    return ResearchStrategyExpectedInformationGainDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(normalized)),
        row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        max_expected_information_gain_decay_score=_max_score(
            rows,
            "expected_information_gain_decay_score",
        ),
        average_expected_information_gain_decay_score=_average_decay_score(rows),
        min_retained_information_gain_score=_min_retained_score(rows),
        status=status,
        next_step=NEXT_STEPS[status],
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_strategy_expected_information_gain_decay_report_payload(
    value: ResearchStrategyExpectedInformationGainDecayReport
    | ResearchStrategyExpectedInformationGainDecayReportDigest
    | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchStrategyExpectedInformationGainDecayReport:
        require_paper_only_flags("report", value)
        if value.derived_validation_digest != _report_derived_validation_digest(value):
            raise ValueError("derived_validation_digest must match report fields")
        payload = json_ready_no_floats(value)
    elif type(value) is ResearchStrategyExpectedInformationGainDecayReportDigest:
        require_paper_only_flags("digest", value)
        payload = json_ready_no_floats(value)
    elif type(value) is dict:
        payload = json_ready_no_floats(value)
    else:
        raise ValueError("value must be an expected information gain decay report")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
    reject_unsafe_surface_fields("eig decay payload", payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_strategy_expected_information_gain_decay_report_digest(
    report: ResearchStrategyExpectedInformationGainDecayReport,
) -> ResearchStrategyExpectedInformationGainDecayReportDigest:
    if type(report) is not ResearchStrategyExpectedInformationGainDecayReport:
        raise ValueError(
            "report must be a ResearchStrategyExpectedInformationGainDecayReport",
        )
    require_paper_only_flags("report", report)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    return ResearchStrategyExpectedInformationGainDecayReportDigest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_digest=report.derived_validation_digest,
        status=report.status,
        input_count=report.input_count,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        max_expected_information_gain_decay_score=(
            report.max_expected_information_gain_decay_score
        ),
        average_expected_information_gain_decay_score=(
            report.average_expected_information_gain_decay_score
        ),
        min_retained_information_gain_score=report.min_retained_information_gain_score,
        reason_codes=report.reason_codes,
    )


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_for_observation(
    observation: ResearchStrategyExpectedInformationGainDecayObservation,
    config: ResearchStrategyExpectedInformationGainDecayConfig,
) -> ResearchStrategyExpectedInformationGainDecayRow:
    source_aging_decay_score = _source_aging_decay_score(observation, config)
    reduced_uncertainty_decay_score = _one_minus(
        "reduced_uncertainty_decay_score",
        observation.remaining_uncertainty_probability,
    )
    market_movement_decay_score = observation.market_movement_probability
    cost_drag_decay_score = observation.cost_drag_probability
    liquidity_reliability_decay_score = _one_minus(
        "liquidity_reliability_decay_score",
        observation.liquidity_reliability_probability,
    )
    resolution_ambiguity_decay_score = observation.resolution_ambiguity_probability
    decay_score = _expected_information_gain_decay_score(
        source_aging_decay_score=source_aging_decay_score,
        reduced_uncertainty_decay_score=reduced_uncertainty_decay_score,
        market_movement_decay_score=market_movement_decay_score,
        cost_drag_decay_score=cost_drag_decay_score,
        liquidity_reliability_decay_score=liquidity_reliability_decay_score,
        resolution_ambiguity_decay_score=resolution_ambiguity_decay_score,
    )
    retained_score = _one_minus("retained_information_gain_score", decay_score)
    status = _status_for_score(decay_score, config)
    return ResearchStrategyExpectedInformationGainDecayRow(
        public_research_key=observation.public_research_key,
        observed_at=observation.observed_at,
        source_age_hours=observation.source_age_hours,
        remaining_uncertainty_probability=observation.remaining_uncertainty_probability,
        market_movement_probability=observation.market_movement_probability,
        cost_drag_probability=observation.cost_drag_probability,
        liquidity_reliability_probability=observation.liquidity_reliability_probability,
        resolution_ambiguity_probability=observation.resolution_ambiguity_probability,
        source_aging_decay_score=source_aging_decay_score,
        reduced_uncertainty_decay_score=reduced_uncertainty_decay_score,
        market_movement_decay_score=market_movement_decay_score,
        cost_drag_decay_score=cost_drag_decay_score,
        liquidity_reliability_decay_score=liquidity_reliability_decay_score,
        resolution_ambiguity_decay_score=resolution_ambiguity_decay_score,
        expected_information_gain_decay_score=decay_score,
        retained_information_gain_score=retained_score,
        status=status,
        reason_codes=_row_reason_codes(
            upstream_reason_codes=observation.upstream_reason_codes,
            status=status,
            source_aging_decay_score=source_aging_decay_score,
            reduced_uncertainty_decay_score=reduced_uncertainty_decay_score,
            market_movement_decay_score=market_movement_decay_score,
            cost_drag_decay_score=cost_drag_decay_score,
            liquidity_reliability_decay_score=liquidity_reliability_decay_score,
            resolution_ambiguity_decay_score=resolution_ambiguity_decay_score,
        ),
    )


def _source_aging_decay_score(
    observation: ResearchStrategyExpectedInformationGainDecayObservation,
    config: ResearchStrategyExpectedInformationGainDecayConfig,
) -> Decimal:
    if observation.source_age_hours <= config.fresh_source_age_hours:
        return ZERO_SCORE
    return _clamp_probability(
        _ratio(
            observation.source_age_hours - config.fresh_source_age_hours,
            config.stale_source_age_span_hours,
        ),
    )


def _expected_information_gain_decay_score(
    *,
    source_aging_decay_score: Decimal,
    reduced_uncertainty_decay_score: Decimal,
    market_movement_decay_score: Decimal,
    cost_drag_decay_score: Decimal,
    liquidity_reliability_decay_score: Decimal,
    resolution_ambiguity_decay_score: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        score = (
            source_aging_decay_score * SOURCE_AGING_WEIGHT
            + reduced_uncertainty_decay_score * REDUCED_UNCERTAINTY_WEIGHT
            + market_movement_decay_score * MARKET_MOVEMENT_WEIGHT
            + cost_drag_decay_score * COST_DRAG_WEIGHT
            + liquidity_reliability_decay_score * LIQUIDITY_RELIABILITY_WEIGHT
            + resolution_ambiguity_decay_score * RESOLUTION_AMBIGUITY_WEIGHT
        )
    return _clamp_probability(score)


def _status_for_score(
    score: Decimal,
    config: ResearchStrategyExpectedInformationGainDecayConfig,
) -> str:
    if score >= config.block_decay_threshold:
        return "block"
    if score >= config.watch_decay_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    status: str,
    source_aging_decay_score: Decimal,
    reduced_uncertainty_decay_score: Decimal,
    market_movement_decay_score: Decimal,
    cost_drag_decay_score: Decimal,
    liquidity_reliability_decay_score: Decimal,
    resolution_ambiguity_decay_score: Decimal,
) -> tuple[str, ...]:
    codes = [f"expected_information_gain_decay_{status}"]
    codes.extend(f"input_{code}" for code in upstream_reason_codes)
    if source_aging_decay_score > ZERO_SCORE:
        codes.append("source_aging_decay")
    if reduced_uncertainty_decay_score > ZERO_SCORE:
        codes.append("reduced_uncertainty_decay")
    if market_movement_decay_score > ZERO_SCORE:
        codes.append("market_movement_decay")
    if cost_drag_decay_score > ZERO_SCORE:
        codes.append("cost_drag_decay")
    if liquidity_reliability_decay_score > ZERO_SCORE:
        codes.append("liquidity_reliability_decay")
    if resolution_ambiguity_decay_score > ZERO_SCORE:
        codes.append("resolution_ambiguity_decay")
    return _normalize_public_reason_codes(
        "reason_codes",
        tuple(codes),
        allow_empty=False,
    )


def _report_status(
    rows: tuple[ResearchStrategyExpectedInformationGainDecayRow, ...],
) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyExpectedInformationGainDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("expected_information_gain_decay_no_inputs",)
    status = _report_status(rows)
    codes = [f"expected_information_gain_decay_{status}"]
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in DRIVER_REASON_CODES:
        if code in row_codes:
            codes.append(code)
    return _normalize_public_reason_codes(
        "reason_codes",
        tuple(codes),
        allow_empty=False,
    )


def _normalize_observations(
    observations: tuple[ResearchStrategyExpectedInformationGainDecayObservation, ...]
    | list[ResearchStrategyExpectedInformationGainDecayObservation],
    generated_at: datetime,
) -> tuple[ResearchStrategyExpectedInformationGainDecayObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    seen_keys: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchStrategyExpectedInformationGainDecayObservation:
            raise ValueError(
                "observations must contain "
                "ResearchStrategyExpectedInformationGainDecayObservation values",
            )
        require_paper_only_flags("observation", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if item.public_research_key in seen_keys:
            raise ValueError("observations must contain unique public_research_key values")
        seen_keys.add(item.public_research_key)
    return normalized


def _normalize_rows(
    value: object,
) -> tuple[ResearchStrategyExpectedInformationGainDecayRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategyExpectedInformationGainDecayRow:
            raise ValueError(
                "rows must contain ResearchStrategyExpectedInformationGainDecayRow values",
            )
        require_paper_only_flags("row", row)
    return tuple(sorted(rows, key=_row_key))


def _row_key(row: ResearchStrategyExpectedInformationGainDecayRow) -> tuple[int, Decimal, str]:
    return (
        STATUS_WEIGHT[row.status],
        -row.expected_information_gain_decay_score,
        row.public_research_key,
    )


def _status_count(
    rows: tuple[ResearchStrategyExpectedInformationGainDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _max_score(
    rows: tuple[ResearchStrategyExpectedInformationGainDecayRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_SCORE
    return _normalize_probability(field_name, max(getattr(row, field_name) for row in rows))


def _average_decay_score(
    rows: tuple[ResearchStrategyExpectedInformationGainDecayRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_SCORE
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        score = sum(row.expected_information_gain_decay_score for row in rows) / Decimal(
            len(rows),
        )
    return _normalize_probability("average_expected_information_gain_decay_score", score)


def _min_retained_score(
    rows: tuple[ResearchStrategyExpectedInformationGainDecayRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_SCORE
    return _normalize_probability(
        "min_retained_information_gain_score",
        min(row.retained_information_gain_score for row in rows),
    )


def _validate_row(row: ResearchStrategyExpectedInformationGainDecayRow) -> None:
    expected_retained_score = _one_minus(
        "retained_information_gain_score",
        row.expected_information_gain_decay_score,
    )
    if row.retained_information_gain_score != expected_retained_score:
        raise ValueError("retained_information_gain_score must match decay score")
    expected_decay_score = _expected_information_gain_decay_score(
        source_aging_decay_score=row.source_aging_decay_score,
        reduced_uncertainty_decay_score=row.reduced_uncertainty_decay_score,
        market_movement_decay_score=row.market_movement_decay_score,
        cost_drag_decay_score=row.cost_drag_decay_score,
        liquidity_reliability_decay_score=row.liquidity_reliability_decay_score,
        resolution_ambiguity_decay_score=row.resolution_ambiguity_decay_score,
    )
    if row.expected_information_gain_decay_score != expected_decay_score:
        raise ValueError("expected_information_gain_decay_score must match drivers")
    if f"expected_information_gain_decay_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must match status")


def _validate_report(report: ResearchStrategyExpectedInformationGainDecayReport) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.max_expected_information_gain_decay_score != _max_score(
        report.rows,
        "expected_information_gain_decay_score",
    ):
        raise ValueError("max_expected_information_gain_decay_score must match rows")
    if report.average_expected_information_gain_decay_score != _average_decay_score(
        report.rows,
    ):
        raise ValueError("average_expected_information_gain_decay_score must match rows")
    if report.min_retained_information_gain_score != _min_retained_score(report.rows):
        raise ValueError("min_retained_information_gain_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.next_step != NEXT_STEPS[report.status]:
        raise ValueError("next_step must match status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _report_derived_validation_digest(
    report: ResearchStrategyExpectedInformationGainDecayReport,
) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _derived_validation_digest(values)


def _derived_validation_digest(values: dict[str, object]) -> str:
    ready = json_ready_no_floats(values)
    reject_unsafe_surface_fields("eig decay digest", ready)
    _reject_unsafe_public_payload("digest", ready)
    canonical = json.dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_public_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    if not allow_empty and not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_public_identifier(field_name, code)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    input_codes = tuple(code for code in codes if code.startswith("input_"))
    if tuple(sorted(input_codes)) != input_codes:
        raise ValueError(f"{field_name} must be deterministic")
    if field_name == "upstream_reason_codes":
        if input_codes:
            raise ValueError(f"{field_name} must not be prefixed")
        if tuple(sorted(codes)) != codes:
            raise ValueError(f"{field_name} must be deterministic")
        return codes
    base_codes = tuple(code for code in codes if not code.startswith("input_"))
    if tuple(code for code in BASE_REASON_CODES if code in base_codes) != base_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return codes


def _normalize_nonnegative_score(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, quantum=SCORE_QUANTUM)
    if decimal_value < ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_positive_score(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_score(field_name, value)
    if decimal_value <= ZERO_SCORE:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, quantum=SCORE_QUANTUM)
    if decimal_value < ZERO_SCORE or decimal_value > ONE_SCORE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, quantum=COUNT_QUANTUM)
    if decimal_value != value:
        raise ValueError(f"{field_name} must be integral")
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_decimal(field_name: str, value: object, *, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(quantum)


def _normalize_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return numerator / denominator


def _one_minus(field_name: str, value: Decimal) -> Decimal:
    return _normalize_probability(field_name, ONE_SCORE - value)


def _clamp_probability(value: Decimal) -> Decimal:
    if value <= ZERO_SCORE:
        return ZERO_SCORE
    if value >= ONE_SCORE:
        return ONE_SCORE
    return value.quantize(SCORE_QUANTUM)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a clean public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public identifier in {field_name}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public key in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EXPECTED_INFORMATION_GAIN_DECAY_REPORT_CONFIG_VERSION",
    "ResearchStrategyExpectedInformationGainDecayConfig",
    "ResearchStrategyExpectedInformationGainDecayObservation",
    "ResearchStrategyExpectedInformationGainDecayReport",
    "ResearchStrategyExpectedInformationGainDecayReportDigest",
    "ResearchStrategyExpectedInformationGainDecayRow",
    "STATUSES",
    "build_research_strategy_expected_information_gain_decay_report",
    "research_strategy_expected_information_gain_decay_report_digest",
    "research_strategy_expected_information_gain_decay_report_payload",
)
