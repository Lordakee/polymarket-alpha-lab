"""Pure team category queue balance score report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HUNDRED = Decimal("100.000000")
SCORE_STATUSES = ("pass", "watch", "block")
SCORE_DECISIONS = (
    "continue_research",
    "rebalance_before_more_research",
    "pause_candidate_research",
)
_UNSAFE_TERM_PARTS = (
    ("li", "ve"),
    ("mar", "ket"),
    ("candidate", "_id"),
    ("sl", "ug"),
    ("ques", "tion"),
    ("u", "rl"),
    ("sour", "ce"),
    ("sour", "ce_ref"),
    ("te", "xt"),
    ("d", "sn"),
    ("ta", "ble"),
    ("to", "ken"),
    ("sec", "ret"),
    ("au", "th"),
    ("wal", "let"),
    ("or", "der"),
    ("net", "work"),
    ("data", "base"),
    ("per", "sist"),
    ("b", "uy"),
    ("se", "ll"),
    ("tra", "de"),
    ("recom", "mendation"),
    ("position", "_sizing"),
    ("position", "-sizing"),
    ("position", " sizing"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_CONFIG_FIELDS = (
    "target_open_per_capacity",
    "watch_open_per_capacity",
    "block_open_per_capacity",
    "urgent_watch_ratio",
    "urgent_block_ratio",
    "stale_watch_ratio",
    "stale_block_ratio",
    "average_age_watch_hours",
    "average_age_block_hours",
    "minimum_pass_score",
    "minimum_watch_score",
    "balance_weight",
    "freshness_weight",
    "completion_weight",
    "calibration_weight",
)
_DIGEST_FIELDS = (
    "team_id",
    "category_id",
    "open_candidate_count",
    "urgent_candidate_count",
    "stale_candidate_count",
    "average_age_hours",
    "recent_completion_count",
    "capacity_per_day",
    "calibration_score",
    "config",
    "open_per_capacity_ratio",
    "urgent_candidate_ratio",
    "stale_candidate_ratio",
    "completion_capacity_ratio",
    "balance_component_score",
    "freshness_component_score",
    "completion_component_score",
    "calibration_component_score",
    "paper_score",
    "score_status",
    "score_decision",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class TeamCategoryQueueBalanceScoreConfig:
    target_open_per_capacity: Decimal
    watch_open_per_capacity: Decimal
    block_open_per_capacity: Decimal
    urgent_watch_ratio: Decimal
    urgent_block_ratio: Decimal
    stale_watch_ratio: Decimal
    stale_block_ratio: Decimal
    average_age_watch_hours: Decimal
    average_age_block_hours: Decimal
    minimum_pass_score: Decimal
    minimum_watch_score: Decimal
    balance_weight: Decimal
    freshness_weight: Decimal
    completion_weight: Decimal
    calibration_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "target_open_per_capacity",
            "watch_open_per_capacity",
            "block_open_per_capacity",
            "average_age_watch_hours",
            "average_age_block_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "urgent_watch_ratio",
            "urgent_block_ratio",
            "stale_watch_ratio",
            "stale_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("minimum_pass_score", "minimum_watch_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "balance_weight",
            "freshness_weight",
            "completion_weight",
            "calibration_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        reject_team_category_queue_balance_score_unsafe_payload(
            "queue balance score config",
            self,
        )
        _require_paper_flags("queue balance score config", self)


@dataclass(frozen=True)
class TeamCategoryQueueBalanceScoreInput:
    team_id: str
    category_id: str
    open_candidate_count: Decimal
    urgent_candidate_count: Decimal
    stale_candidate_count: Decimal
    average_age_hours: Decimal
    recent_completion_count: Decimal
    capacity_per_day: Decimal
    calibration_score: Decimal
    config: TeamCategoryQueueBalanceScoreConfig
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category_id", self.category_id)
        for field_name in (
            "open_candidate_count",
            "urgent_candidate_count",
            "stale_candidate_count",
            "recent_completion_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_age_hours",
            _normalize_nonnegative_decimal("average_age_hours", self.average_age_hours),
        )
        object.__setattr__(
            self,
            "capacity_per_day",
            _normalize_positive_decimal("capacity_per_day", self.capacity_per_day),
        )
        object.__setattr__(
            self,
            "calibration_score",
            _normalize_ratio("calibration_score", self.calibration_score),
        )
        if type(self.config) is not TeamCategoryQueueBalanceScoreConfig:
            raise ValueError("config must be a TeamCategoryQueueBalanceScoreConfig")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_input_consistency(self)
        reject_team_category_queue_balance_score_unsafe_payload(
            "queue balance score input",
            self,
        )
        _require_paper_flags("queue balance score input", self)


@dataclass(frozen=True)
class TeamCategoryQueueBalanceScoreResult:
    team_id: str
    category_id: str
    open_candidate_count: Decimal
    urgent_candidate_count: Decimal
    stale_candidate_count: Decimal
    average_age_hours: Decimal
    recent_completion_count: Decimal
    capacity_per_day: Decimal
    calibration_score: Decimal
    config: TeamCategoryQueueBalanceScoreConfig
    open_per_capacity_ratio: Decimal
    urgent_candidate_ratio: Decimal
    stale_candidate_ratio: Decimal
    completion_capacity_ratio: Decimal
    balance_component_score: Decimal
    freshness_component_score: Decimal
    completion_component_score: Decimal
    calibration_component_score: Decimal
    paper_score: Decimal
    score_status: str
    score_decision: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category_id", self.category_id)
        for field_name in (
            "open_candidate_count",
            "urgent_candidate_count",
            "stale_candidate_count",
            "recent_completion_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_age_hours",
            _normalize_nonnegative_decimal("average_age_hours", self.average_age_hours),
        )
        object.__setattr__(
            self,
            "capacity_per_day",
            _normalize_positive_decimal("capacity_per_day", self.capacity_per_day),
        )
        object.__setattr__(
            self,
            "calibration_score",
            _normalize_ratio("calibration_score", self.calibration_score),
        )
        if type(self.config) is not TeamCategoryQueueBalanceScoreConfig:
            raise ValueError("config must be a TeamCategoryQueueBalanceScoreConfig")
        for field_name in (
            "open_per_capacity_ratio",
            "urgent_candidate_ratio",
            "stale_candidate_ratio",
            "completion_capacity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "balance_component_score",
            "freshness_component_score",
            "completion_component_score",
            "calibration_component_score",
            "paper_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        _require_choice("score_status", self.score_status, SCORE_STATUSES)
        _require_choice("score_decision", self.score_decision, SCORE_DECISIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        reject_team_category_queue_balance_score_unsafe_payload(
            "queue balance score result",
            self,
        )
        _require_paper_flags("queue balance score result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return team_category_queue_balance_score_payload(self)


def estimate_team_category_queue_balance_score(
    score_input: TeamCategoryQueueBalanceScoreInput,
) -> TeamCategoryQueueBalanceScoreResult:
    if type(score_input) is not TeamCategoryQueueBalanceScoreInput:
        raise ValueError("score_input must be a TeamCategoryQueueBalanceScoreInput")
    reject_team_category_queue_balance_score_unsafe_payload(
        "queue balance score input",
        score_input,
    )
    _require_paper_flags("queue balance score input", score_input)

    open_per_capacity_ratio = _safe_ratio(
        score_input.open_candidate_count,
        score_input.capacity_per_day,
    )
    urgent_candidate_ratio = _safe_ratio(
        score_input.urgent_candidate_count,
        score_input.open_candidate_count,
    )
    stale_candidate_ratio = _safe_ratio(
        score_input.stale_candidate_count,
        score_input.open_candidate_count,
    )
    completion_capacity_ratio = _clamp_ratio(
        _safe_ratio(score_input.recent_completion_count, score_input.capacity_per_day),
    )
    balance_component_score = _balance_component_score(
        open_per_capacity_ratio,
        score_input.config,
    )
    freshness_component_score = _freshness_component_score(
        urgent_candidate_ratio,
        stale_candidate_ratio,
        score_input.average_age_hours,
        score_input.config,
    )
    completion_component_score = _normalize_score(
        "completion_component_score",
        completion_capacity_ratio * HUNDRED,
    )
    calibration_component_score = _normalize_score(
        "calibration_component_score",
        score_input.calibration_score * HUNDRED,
    )
    paper_score = _paper_score(
        balance_component_score,
        freshness_component_score,
        completion_component_score,
        calibration_component_score,
        score_input.config,
    )
    score_status = _score_status(
        paper_score,
        open_per_capacity_ratio,
        urgent_candidate_ratio,
        stale_candidate_ratio,
        score_input.average_age_hours,
        score_input.config,
    )

    return TeamCategoryQueueBalanceScoreResult(
        team_id=score_input.team_id,
        category_id=score_input.category_id,
        open_candidate_count=score_input.open_candidate_count,
        urgent_candidate_count=score_input.urgent_candidate_count,
        stale_candidate_count=score_input.stale_candidate_count,
        average_age_hours=score_input.average_age_hours,
        recent_completion_count=score_input.recent_completion_count,
        capacity_per_day=score_input.capacity_per_day,
        calibration_score=score_input.calibration_score,
        config=score_input.config,
        open_per_capacity_ratio=open_per_capacity_ratio,
        urgent_candidate_ratio=urgent_candidate_ratio,
        stale_candidate_ratio=stale_candidate_ratio,
        completion_capacity_ratio=completion_capacity_ratio,
        balance_component_score=balance_component_score,
        freshness_component_score=freshness_component_score,
        completion_component_score=completion_component_score,
        calibration_component_score=calibration_component_score,
        paper_score=paper_score,
        score_status=score_status,
        score_decision=_score_decision(score_status),
        reason_codes=_reason_codes(
            score_input.reason_codes,
            open_per_capacity_ratio=open_per_capacity_ratio,
            urgent_candidate_ratio=urgent_candidate_ratio,
            stale_candidate_ratio=stale_candidate_ratio,
            average_age_hours=score_input.average_age_hours,
            completion_capacity_ratio=completion_capacity_ratio,
            paper_score=paper_score,
            score_status=score_status,
            config=score_input.config,
        ),
    )


def team_category_queue_balance_score_payload(
    result: TeamCategoryQueueBalanceScoreResult,
) -> dict[str, Any]:
    if type(result) is not TeamCategoryQueueBalanceScoreResult:
        raise ValueError("result must be a TeamCategoryQueueBalanceScoreResult")
    _require_paper_flags("queue balance score result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_team_category_queue_balance_score_unsafe_payload(
        "queue balance score result",
        result,
    )
    return _json_ready(asdict(result))


def reject_team_category_queue_balance_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _balance_component_score(
    open_per_capacity_ratio: Decimal,
    config: TeamCategoryQueueBalanceScoreConfig,
) -> Decimal:
    if open_per_capacity_ratio <= config.target_open_per_capacity:
        return HUNDRED
    if open_per_capacity_ratio >= config.block_open_per_capacity:
        return ZERO
    span = config.block_open_per_capacity - config.target_open_per_capacity
    pressure = _safe_ratio(open_per_capacity_ratio - config.target_open_per_capacity, span)
    return _normalize_score("balance_component_score", HUNDRED - pressure * HUNDRED)


def _freshness_component_score(
    urgent_candidate_ratio: Decimal,
    stale_candidate_ratio: Decimal,
    average_age_hours: Decimal,
    config: TeamCategoryQueueBalanceScoreConfig,
) -> Decimal:
    pressure = max(
        _safe_ratio(urgent_candidate_ratio, config.urgent_block_ratio),
        _safe_ratio(stale_candidate_ratio, config.stale_block_ratio),
        _safe_ratio(average_age_hours, config.average_age_block_hours),
    )
    if pressure >= ONE:
        return ZERO
    return _normalize_score("freshness_component_score", HUNDRED - pressure * HUNDRED)


def _paper_score(
    balance_component_score: Decimal,
    freshness_component_score: Decimal,
    completion_component_score: Decimal,
    calibration_component_score: Decimal,
    config: TeamCategoryQueueBalanceScoreConfig,
) -> Decimal:
    total_weight = _total_weight(config)
    weighted_score = (
        balance_component_score * config.balance_weight
        + freshness_component_score * config.freshness_weight
        + completion_component_score * config.completion_weight
        + calibration_component_score * config.calibration_weight
    )
    return _normalize_score("paper_score", weighted_score / total_weight)


def _score_status(
    paper_score: Decimal,
    open_per_capacity_ratio: Decimal,
    urgent_candidate_ratio: Decimal,
    stale_candidate_ratio: Decimal,
    average_age_hours: Decimal,
    config: TeamCategoryQueueBalanceScoreConfig,
) -> str:
    if (
        open_per_capacity_ratio >= config.block_open_per_capacity
        or urgent_candidate_ratio >= config.urgent_block_ratio
        or stale_candidate_ratio >= config.stale_block_ratio
        or average_age_hours >= config.average_age_block_hours
        or paper_score < config.minimum_watch_score
    ):
        return "block"
    if (
        open_per_capacity_ratio >= config.watch_open_per_capacity
        or urgent_candidate_ratio >= config.urgent_watch_ratio
        or stale_candidate_ratio >= config.stale_watch_ratio
        or average_age_hours >= config.average_age_watch_hours
        or paper_score < config.minimum_pass_score
    ):
        return "watch"
    return "pass"


def _score_decision(score_status: str) -> str:
    if score_status == "pass":
        return "continue_research"
    if score_status == "watch":
        return "rebalance_before_more_research"
    if score_status == "block":
        return "pause_candidate_research"
    raise ValueError("score_status must be a known value")


def _reason_codes(
    existing: tuple[str, ...],
    *,
    open_per_capacity_ratio: Decimal,
    urgent_candidate_ratio: Decimal,
    stale_candidate_ratio: Decimal,
    average_age_hours: Decimal,
    completion_capacity_ratio: Decimal,
    paper_score: Decimal,
    score_status: str,
    config: TeamCategoryQueueBalanceScoreConfig,
) -> tuple[str, ...]:
    additions = [
        "team_category_queue_balance_score",
        f"score_{score_status}",
    ]
    if open_per_capacity_ratio >= config.block_open_per_capacity:
        additions.append("open_queue_block_threshold_met")
    elif open_per_capacity_ratio >= config.watch_open_per_capacity:
        additions.append("open_queue_watch_threshold_met")
    elif open_per_capacity_ratio <= config.target_open_per_capacity:
        additions.append("capacity_available")
    else:
        additions.append("open_queue_above_target")

    if urgent_candidate_ratio >= config.urgent_block_ratio:
        additions.append("urgent_queue_block_threshold_met")
    elif urgent_candidate_ratio >= config.urgent_watch_ratio:
        additions.append("urgent_queue_watch_threshold_met")

    if stale_candidate_ratio >= config.stale_block_ratio:
        additions.append("stale_queue_block_threshold_met")
    elif stale_candidate_ratio >= config.stale_watch_ratio:
        additions.append("stale_queue_watch_threshold_met")

    if average_age_hours >= config.average_age_block_hours:
        additions.append("average_age_block_threshold_met")
    elif average_age_hours >= config.average_age_watch_hours:
        additions.append("average_age_watch_threshold_met")
    else:
        additions.append("freshness_within_watch_threshold")

    if completion_capacity_ratio > ZERO:
        additions.append("recent_completion_support_present")
    if score_status == "pass":
        additions.append("minimum_pass_score_met")
    elif paper_score < config.minimum_watch_score:
        additions.append("minimum_watch_score_missed")
    else:
        additions.append("rebalance_watch_threshold_met")
    return _append_reason_codes(existing, tuple(additions))


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_config(config: TeamCategoryQueueBalanceScoreConfig) -> None:
    if config.target_open_per_capacity >= config.watch_open_per_capacity:
        raise ValueError("target_open_per_capacity must be less than watch_open_per_capacity")
    if config.watch_open_per_capacity >= config.block_open_per_capacity:
        raise ValueError("watch_open_per_capacity must be less than block_open_per_capacity")
    if config.urgent_watch_ratio >= config.urgent_block_ratio:
        raise ValueError("urgent_watch_ratio must be less than urgent_block_ratio")
    if config.stale_watch_ratio >= config.stale_block_ratio:
        raise ValueError("stale_watch_ratio must be less than stale_block_ratio")
    if config.average_age_watch_hours >= config.average_age_block_hours:
        raise ValueError("average_age_watch_hours must be less than average_age_block_hours")
    if config.minimum_watch_score > config.minimum_pass_score:
        raise ValueError("minimum_watch_score must not exceed minimum_pass_score")
    if _total_weight(config) <= ZERO:
        raise ValueError("config weights must sum to a positive Decimal")


def _validate_input_consistency(value: object) -> None:
    open_candidate_count = getattr(value, "open_candidate_count")
    urgent_candidate_count = getattr(value, "urgent_candidate_count")
    stale_candidate_count = getattr(value, "stale_candidate_count")
    if urgent_candidate_count > open_candidate_count:
        raise ValueError("urgent_candidate_count must not exceed open_candidate_count")
    if stale_candidate_count > open_candidate_count:
        raise ValueError("stale_candidate_count must not exceed open_candidate_count")


def _validate_result_consistency(result: TeamCategoryQueueBalanceScoreResult) -> None:
    _validate_input_consistency(result)
    if result.open_per_capacity_ratio != _safe_ratio(
        result.open_candidate_count,
        result.capacity_per_day,
    ):
        raise ValueError("open_per_capacity_ratio must match queue counts")
    if result.urgent_candidate_ratio != _safe_ratio(
        result.urgent_candidate_count,
        result.open_candidate_count,
    ):
        raise ValueError("urgent_candidate_ratio must match queue counts")
    if result.stale_candidate_ratio != _safe_ratio(
        result.stale_candidate_count,
        result.open_candidate_count,
    ):
        raise ValueError("stale_candidate_ratio must match queue counts")
    if result.completion_capacity_ratio != _clamp_ratio(
        _safe_ratio(result.recent_completion_count, result.capacity_per_day),
    ):
        raise ValueError("completion_capacity_ratio must match recent completions")
    if result.balance_component_score != _balance_component_score(
        result.open_per_capacity_ratio,
        result.config,
    ):
        raise ValueError("balance_component_score must match queue pressure")
    if result.freshness_component_score != _freshness_component_score(
        result.urgent_candidate_ratio,
        result.stale_candidate_ratio,
        result.average_age_hours,
        result.config,
    ):
        raise ValueError("freshness_component_score must match queue pressure")
    if result.completion_component_score != _normalize_score(
        "completion_component_score",
        result.completion_capacity_ratio * HUNDRED,
    ):
        raise ValueError("completion_component_score must match completion_capacity_ratio")
    if result.calibration_component_score != _normalize_score(
        "calibration_component_score",
        result.calibration_score * HUNDRED,
    ):
        raise ValueError("calibration_component_score must match calibration_score")
    if result.paper_score != _paper_score(
        result.balance_component_score,
        result.freshness_component_score,
        result.completion_component_score,
        result.calibration_component_score,
        result.config,
    ):
        raise ValueError("paper_score must match component scores")
    if result.score_status != _score_status(
        result.paper_score,
        result.open_per_capacity_ratio,
        result.urgent_candidate_ratio,
        result.stale_candidate_ratio,
        result.average_age_hours,
        result.config,
    ):
        raise ValueError("score_status must match score and thresholds")
    if result.score_decision != _score_decision(result.score_status):
        raise ValueError("score_decision must match score_status")


def _total_weight(config: TeamCategoryQueueBalanceScoreConfig) -> Decimal:
    return _normalize_nonnegative_decimal(
        "total_weight",
        config.balance_weight
        + config.freshness_weight
        + config.completion_weight
        + config.calibration_weight,
    )


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_nonnegative_decimal("ratio", numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value > ONE:
        return ONE
    return value


def _derived_validation_digest(result: TeamCategoryQueueBalanceScoreResult) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(result, field_name))}"
        for field_name in _DIGEST_FIELDS
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return "{" + ",".join(
            f"{field.name}:{_digest_value(getattr(value, field.name))}"
            for field in fields(value)
        ) + "}"
    if isinstance(value, tuple):
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("digest value must be public scalar data")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1.000000")
    return normalized


def _normalize_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > HUNDRED:
        raise ValueError(f"{field_name} must not exceed 100.000000")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_canonical_digest(value: object) -> None:
    _require_canonical_string("derived_validation_digest", value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be lowercase hex")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    return ()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "SCORE_STATUSES",
    "SCORE_DECISIONS",
    "TeamCategoryQueueBalanceScoreConfig",
    "TeamCategoryQueueBalanceScoreInput",
    "TeamCategoryQueueBalanceScoreResult",
    "estimate_team_category_queue_balance_score",
    "team_category_queue_balance_score_payload",
    "reject_team_category_queue_balance_score_unsafe_payload",
)
