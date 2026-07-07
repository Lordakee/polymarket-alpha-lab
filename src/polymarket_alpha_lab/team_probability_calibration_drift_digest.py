"""Pure Phase 1 digest for strategy team probability calibration drift."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.strategy_team_taxonomy import (
    STRATEGY_TEAM_IDS,
    require_strategy_team_id,
)
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_TEAM_PROBABILITY_CALIBRATION_DRIFT_DIGEST_CONFIG_VERSION = (
    "team-probability-calibration-drift-digest-v0"
)

EMPTY_REASON = "team_probability_calibration_drift_digest_empty_facts"
INSUFFICIENT_SAMPLE_REASON = (
    "team_probability_calibration_drift_digest_insufficient_settled_sample"
)
HIGH_RECENT_BRIER_REASON = (
    "team_probability_calibration_drift_digest_high_recent_brier_error"
)
CALIBRATION_DRIFT_BLOCK_REASON = (
    "team_probability_calibration_drift_digest_calibration_error_drift_block"
)
CALIBRATION_DRIFT_WATCH_REASON = (
    "team_probability_calibration_drift_digest_calibration_error_drift_watch"
)
CONFIDENCE_OVERSTATEMENT_WATCH_REASON = (
    "team_probability_calibration_drift_digest_confidence_overstatement_watch"
)
SOURCE_RELIABILITY_DECLINE_WATCH_REASON = (
    "team_probability_calibration_drift_digest_source_reliability_decline_watch"
)
PASS_REASON = "team_probability_calibration_drift_digest_passed"

REASON_CODES = (
    EMPTY_REASON,
    INSUFFICIENT_SAMPLE_REASON,
    HIGH_RECENT_BRIER_REASON,
    CALIBRATION_DRIFT_BLOCK_REASON,
    CALIBRATION_DRIFT_WATCH_REASON,
    CONFIDENCE_OVERSTATEMENT_WATCH_REASON,
    SOURCE_RELIABILITY_DECLINE_WATCH_REASON,
    PASS_REASON,
)
REASON_CODE_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
BLOCK_REASONS = (
    EMPTY_REASON,
    INSUFFICIENT_SAMPLE_REASON,
    HIGH_RECENT_BRIER_REASON,
    CALIBRATION_DRIFT_BLOCK_REASON,
)
WATCH_REASONS = (
    CALIBRATION_DRIFT_WATCH_REASON,
    CONFIDENCE_OVERSTATEMENT_WATCH_REASON,
    SOURCE_RELIABILITY_DECLINE_WATCH_REASON,
)
MEMORY_STATUSES = ("pass", "watch", "blocked")
NEXT_REVIEW_STEPS = {
    "pass": "reuse_team_probability_memory",
    "watch": "review_team_probability_calibration_drift",
    "blocked": "pause_team_probability_memory_use",
}

COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1.000000")
NEGATIVE_ONE = Decimal("-1.000000")
STRATEGY_TEAM_ID_RANK = {
    team_id: index for index, team_id in enumerate(STRATEGY_TEAM_IDS)
}
UNSAFE_KEY_FRAGMENTS = (
    "au" + "th",
    "priv" + "ate" + "_" + "key",
    "wall" + "et",
    "acc" + "ount",
    "ord" + "er",
    "can" + "cel",
    "rep" + "lace",
    "sig" + "ning",
    "sec" + "ret",
)


__all__ = (
    "DEFAULT_TEAM_PROBABILITY_CALIBRATION_DRIFT_DIGEST_CONFIG_VERSION",
    "TeamProbabilityCalibrationDriftDigestConfig",
    "TeamProbabilityCalibrationDriftDigestReasonCodeCount",
    "TeamProbabilityCalibrationDriftDigestReport",
    "TeamProbabilityCalibrationDriftDigestRow",
    "TeamProbabilityCalibrationDriftFact",
    "build_team_probability_calibration_drift_digest",
    "team_probability_calibration_drift_digest_payload",
)


@dataclass(frozen=True)
class TeamProbabilityCalibrationDriftDigestConfig:
    config_version: str = (
        DEFAULT_TEAM_PROBABILITY_CALIBRATION_DRIFT_DIGEST_CONFIG_VERSION
    )
    min_settled_sample_count: Decimal = Decimal("10")
    recent_brier_block_threshold: Decimal = Decimal("0.260000")
    calibration_delta_watch_threshold: Decimal = Decimal("0.050000")
    calibration_delta_block_threshold: Decimal = Decimal("0.150000")
    confidence_overstatement_watch_threshold: Decimal = Decimal("0.200000")
    source_reliability_decline_watch_threshold: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_settled_sample_count",
            _normalize_positive_count(
                "min_settled_sample_count",
                self.min_settled_sample_count,
            ),
        )
        for field_name in (
            "recent_brier_block_threshold",
            "calibration_delta_watch_threshold",
            "calibration_delta_block_threshold",
            "confidence_overstatement_watch_threshold",
            "source_reliability_decline_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if (
            self.calibration_delta_watch_threshold
            >= self.calibration_delta_block_threshold
        ):
            raise ValueError("watch threshold must be below block threshold")
        require_paper_only_flags("team probability calibration drift config", self)


@dataclass(frozen=True)
class TeamProbabilityCalibrationDriftFact:
    team_id: str
    settled_sample_count: Decimal
    recent_brier_error: Decimal
    trailing_brier_error: Decimal
    calibration_error_delta: Decimal
    confidence_overstatement_rate: Decimal
    source_reliability_delta: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "team_id",
            require_strategy_team_id("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "settled_sample_count",
            _normalize_nonnegative_count(
                "settled_sample_count",
                self.settled_sample_count,
            ),
        )
        for field_name in (
            "recent_brier_error",
            "trailing_brier_error",
            "confidence_overstatement_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("calibration_error_delta", "source_reliability_delta"):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("team probability calibration drift fact", self)


@dataclass(frozen=True)
class TeamProbabilityCalibrationDriftDigestRow:
    team_id: str
    memory_status: str
    settled_sample_count: Decimal
    recent_brier_error: Decimal
    trailing_brier_error: Decimal
    calibration_error_delta: Decimal
    confidence_overstatement_rate: Decimal
    source_reliability_delta: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "team_id",
            require_strategy_team_id("team_id", self.team_id),
        )
        _require_memory_status("memory_status", self.memory_status)
        object.__setattr__(
            self,
            "settled_sample_count",
            _normalize_nonnegative_count(
                "settled_sample_count",
                self.settled_sample_count,
            ),
        )
        for field_name in (
            "recent_brier_error",
            "trailing_brier_error",
            "confidence_overstatement_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("calibration_error_delta", "source_reliability_delta"):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.memory_status != _status_for_reason_codes(self.reason_codes):
            raise ValueError("memory_status must match reason_codes")
        require_paper_only_flags("team probability calibration drift row", self)


@dataclass(frozen=True)
class TeamProbabilityCalibrationDriftDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        require_paper_only_flags(
            "team probability calibration drift reason count",
            self,
        )


@dataclass(frozen=True)
class TeamProbabilityCalibrationDriftDigestReport:
    config_version: str
    memory_status: str
    next_review_step: str
    fact_count: Decimal
    row_count: Decimal
    total_settled_sample_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_recent_brier_error: Decimal | None
    average_trailing_brier_error: Decimal | None
    average_calibration_error_delta: Decimal | None
    average_confidence_overstatement_rate: Decimal | None
    average_source_reliability_delta: Decimal | None
    rows: tuple[TeamProbabilityCalibrationDriftDigestRow, ...]
    reason_code_counts: tuple[TeamProbabilityCalibrationDriftDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_memory_status("memory_status", self.memory_status)
        _require_canonical_string("next_review_step", self.next_review_step)
        for field_name in (
            "fact_count",
            "row_count",
            "total_settled_sample_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_recent_brier_error",
            _normalize_optional_ratio(
                "average_recent_brier_error",
                self.average_recent_brier_error,
            ),
        )
        object.__setattr__(
            self,
            "average_trailing_brier_error",
            _normalize_optional_ratio(
                "average_trailing_brier_error",
                self.average_trailing_brier_error,
            ),
        )
        object.__setattr__(
            self,
            "average_calibration_error_delta",
            _normalize_optional_signed_ratio(
                "average_calibration_error_delta",
                self.average_calibration_error_delta,
            ),
        )
        object.__setattr__(
            self,
            "average_confidence_overstatement_rate",
            _normalize_optional_ratio(
                "average_confidence_overstatement_rate",
                self.average_confidence_overstatement_rate,
            ),
        )
        object.__setattr__(
            self,
            "average_source_reliability_delta",
            _normalize_optional_signed_ratio(
                "average_source_reliability_delta",
                self.average_source_reliability_delta,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("team probability calibration drift report", self)


def build_team_probability_calibration_drift_digest(
    facts: list[TeamProbabilityCalibrationDriftFact]
    | tuple[TeamProbabilityCalibrationDriftFact, ...],
    *,
    config: TeamProbabilityCalibrationDriftDigestConfig,
) -> TeamProbabilityCalibrationDriftDigestReport:
    if type(config) is not TeamProbabilityCalibrationDriftDigestConfig:
        raise ValueError(
            "config must be a TeamProbabilityCalibrationDriftDigestConfig",
        )
    require_paper_only_flags("team probability calibration drift config", config)
    normalized_facts = _normalize_facts(facts)
    rows = tuple(_build_row(item, config=config) for item in normalized_facts)
    reason_codes = _report_reason_codes(rows)
    memory_status = _status_for_reason_codes(reason_codes)

    return TeamProbabilityCalibrationDriftDigestReport(
        config_version=config.config_version,
        memory_status=memory_status,
        next_review_step=NEXT_REVIEW_STEPS[memory_status],
        fact_count=_decimal_count(len(normalized_facts)),
        row_count=_decimal_count(len(rows)),
        total_settled_sample_count=sum(
            (row.settled_sample_count for row in rows),
            ZERO,
        ),
        pass_count=_decimal_count(
            sum(1 for row in rows if row.memory_status == "pass"),
        ),
        watch_count=_decimal_count(
            sum(1 for row in rows if row.memory_status == "watch"),
        ),
        blocked_count=_decimal_count(
            sum(1 for row in rows if row.memory_status == "blocked"),
        ),
        average_recent_brier_error=_weighted_row_average(
            rows,
            "recent_brier_error",
        ),
        average_trailing_brier_error=_weighted_row_average(
            rows,
            "trailing_brier_error",
        ),
        average_calibration_error_delta=_weighted_row_average(
            rows,
            "calibration_error_delta",
        ),
        average_confidence_overstatement_rate=_weighted_row_average(
            rows,
            "confidence_overstatement_rate",
        ),
        average_source_reliability_delta=_weighted_row_average(
            rows,
            "source_reliability_delta",
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def team_probability_calibration_drift_digest_payload(value: object) -> dict[str, Any]:
    if isinstance(
        value,
        (
            TeamProbabilityCalibrationDriftDigestConfig,
            TeamProbabilityCalibrationDriftFact,
            TeamProbabilityCalibrationDriftDigestRow,
            TeamProbabilityCalibrationDriftDigestReasonCodeCount,
            TeamProbabilityCalibrationDriftDigestReport,
        ),
    ):
        require_paper_only_flags("team probability calibration drift payload", value)
    elif type(value) is not dict:
        raise ValueError(
            "value must be a team probability calibration drift dataclass "
            "or JSON object",
        )

    _reject_unsafe_payload_keys(value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("team probability calibration drift payload must be a JSON object")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_payload_keys(payload)
    return payload


def _normalize_facts(
    facts: list[TeamProbabilityCalibrationDriftFact]
    | tuple[TeamProbabilityCalibrationDriftFact, ...],
) -> tuple[TeamProbabilityCalibrationDriftFact, ...]:
    if type(facts) not in (list, tuple):
        raise ValueError("facts must be a list or tuple")
    normalized_facts = tuple(facts)
    seen_team_ids: set[str] = set()
    for item in normalized_facts:
        if type(item) is not TeamProbabilityCalibrationDriftFact:
            raise ValueError("facts must contain TeamProbabilityCalibrationDriftFact")
        require_paper_only_flags("team probability calibration drift fact", item)
        if item.team_id in seen_team_ids:
            raise ValueError("team_id values must be unique")
        seen_team_ids.add(item.team_id)
    return tuple(sorted(normalized_facts, key=lambda item: _team_sort_key(item.team_id)))


def _build_row(
    fact: TeamProbabilityCalibrationDriftFact,
    *,
    config: TeamProbabilityCalibrationDriftDigestConfig,
) -> TeamProbabilityCalibrationDriftDigestRow:
    reason_codes = _row_reason_codes(fact, config=config)
    return TeamProbabilityCalibrationDriftDigestRow(
        team_id=fact.team_id,
        memory_status=_status_for_reason_codes(reason_codes),
        settled_sample_count=fact.settled_sample_count,
        recent_brier_error=fact.recent_brier_error,
        trailing_brier_error=fact.trailing_brier_error,
        calibration_error_delta=fact.calibration_error_delta,
        confidence_overstatement_rate=fact.confidence_overstatement_rate,
        source_reliability_delta=fact.source_reliability_delta,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    fact: TeamProbabilityCalibrationDriftFact,
    *,
    config: TeamProbabilityCalibrationDriftDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if fact.settled_sample_count < config.min_settled_sample_count:
        reason_codes.append(INSUFFICIENT_SAMPLE_REASON)
    if fact.recent_brier_error >= config.recent_brier_block_threshold:
        reason_codes.append(HIGH_RECENT_BRIER_REASON)
    if fact.calibration_error_delta >= config.calibration_delta_block_threshold:
        reason_codes.append(CALIBRATION_DRIFT_BLOCK_REASON)
    elif fact.calibration_error_delta >= config.calibration_delta_watch_threshold:
        reason_codes.append(CALIBRATION_DRIFT_WATCH_REASON)
    if (
        fact.confidence_overstatement_rate
        >= config.confidence_overstatement_watch_threshold
    ):
        reason_codes.append(CONFIDENCE_OVERSTATEMENT_WATCH_REASON)
    if (
        fact.source_reliability_delta
        <= -config.source_reliability_decline_watch_threshold
    ):
        reason_codes.append(SOURCE_RELIABILITY_DECLINE_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _combined_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[TeamProbabilityCalibrationDriftDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    return _combined_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _combined_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if any(reason_code != PASS_REASON for reason_code in reason_codes):
        reason_codes = tuple(
            reason_code for reason_code in reason_codes if reason_code != PASS_REASON
        )
    return tuple(
        sorted(
            set(reason_codes),
            key=lambda reason_code: REASON_CODE_RANK[reason_code],
        )
    )


def _reason_code_counts(
    rows: tuple[TeamProbabilityCalibrationDriftDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[TeamProbabilityCalibrationDriftDigestReasonCodeCount, ...]:
    if reason_codes == (EMPTY_REASON,):
        return (
            TeamProbabilityCalibrationDriftDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in reason_codes:
                counter[reason_code] += 1
    return tuple(
        TeamProbabilityCalibrationDriftDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
    )


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _validate_report(report: TeamProbabilityCalibrationDriftDigestReport) -> None:
    if report.fact_count != _decimal_count(len(report.rows)):
        raise ValueError("fact_count must match rows")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.total_settled_sample_count != sum(
        (row.settled_sample_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("total_settled_sample_count must match rows")
    if report.pass_count != _decimal_count(
        sum(1 for row in report.rows if row.memory_status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(
        sum(1 for row in report.rows if row.memory_status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(
        sum(1 for row in report.rows if row.memory_status == "blocked"),
    ):
        raise ValueError("blocked_count must match rows")
    for field_name in (
        "recent_brier_error",
        "trailing_brier_error",
        "calibration_error_delta",
        "confidence_overstatement_rate",
        "source_reliability_delta",
    ):
        report_field_name = f"average_{field_name}"
        if getattr(report, report_field_name) != _weighted_row_average(
            report.rows,
            field_name,
        ):
            raise ValueError(f"{report_field_name} must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.memory_status != _status_for_reason_codes(report.reason_codes):
        raise ValueError("memory_status must match reason_codes")
    if report.next_review_step != NEXT_REVIEW_STEPS[report.memory_status]:
        raise ValueError("next_review_step must match memory_status")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[TeamProbabilityCalibrationDriftDigestRow, ...],
) -> tuple[TeamProbabilityCalibrationDriftDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized_rows = tuple(rows)
    seen_team_ids: set[str] = set()
    for row in normalized_rows:
        if type(row) is not TeamProbabilityCalibrationDriftDigestRow:
            raise ValueError("rows must contain TeamProbabilityCalibrationDriftDigestRow")
        require_paper_only_flags("team probability calibration drift row", row)
        if row.team_id in seen_team_ids:
            raise ValueError("rows team_id values must be unique")
        seen_team_ids.add(row.team_id)
    if normalized_rows != tuple(
        sorted(normalized_rows, key=lambda row: _team_sort_key(row.team_id))
    ):
        raise ValueError("rows must be deterministically sorted")
    return normalized_rows


def _normalize_reason_code_counts(
    counts: tuple[TeamProbabilityCalibrationDriftDigestReasonCodeCount, ...],
) -> tuple[TeamProbabilityCalibrationDriftDigestReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized_counts = tuple(counts)
    seen_reason_codes: set[str] = set()
    for count in normalized_counts:
        if type(count) is not TeamProbabilityCalibrationDriftDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TeamProbabilityCalibrationDriftDigestReasonCodeCount",
            )
        require_paper_only_flags(
            "team probability calibration drift reason count",
            count,
        )
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    if normalized_counts != tuple(
        sorted(
            normalized_counts,
            key=lambda count: REASON_CODE_RANK[count.reason_code],
        )
    ):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return normalized_counts


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_member("reason_codes", reason_code, REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    stable_codes = tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_codes)
    if stable_codes != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _payload_value(value: object) -> object:
    if type(value) is bool or value is None or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("payload must not contain integer values")
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _payload_value(getattr(value, item.name)) for item in fields(value)}
    if type(value) is dict:
        return _payload_dict(value)
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _payload_dict(value: dict[Any, Any]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("payload keys must be strings")
        payload[key] = _payload_value(item)
    return payload


def _validate_payload_flags(value: object, field_path: str) -> None:
    if type(value) is dict:
        for flag in ("paper_only", "report_only", "readonly"):
            if flag not in value:
                raise ValueError(f"{field_path}.{flag} must be present")
            if value[flag] is not True:
                raise ValueError(f"{field_path}.{flag} must be True")
        for key, item in value.items():
            if type(item) is dict:
                _validate_payload_flags(item, f"{field_path}.{key}")
            elif type(item) is list:
                for index, nested_item in enumerate(item):
                    if type(nested_item) is dict:
                        _validate_payload_flags(nested_item, f"{field_path}.{key}.{index}")


def _reject_unsafe_payload_keys(value: object) -> None:
    for key in _iter_payload_keys(value):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_KEY_FRAGMENTS):
            raise ValueError(f"unsafe surface field in payload: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        keys: list[str] = []
        for item in fields(value):
            keys.append(item.name)
            keys.extend(_iter_payload_keys(getattr(value, item.name)))
        return tuple(keys)
    if type(value) is dict:
        keys = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if type(value) in (list, tuple):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _weighted_row_average(
    rows: tuple[TeamProbabilityCalibrationDriftDigestRow, ...],
    field_name: str,
) -> Decimal | None:
    total = ZERO
    weight = ZERO
    for row in rows:
        if row.settled_sample_count > ZERO:
            total += getattr(row, field_name) * row.settled_sample_count
            weight += row.settled_sample_count
    if weight == ZERO:
        return None
    return _quantize_ratio(total / weight)


def _team_sort_key(team_id: str) -> tuple[int, str]:
    return (STRATEGY_TEAM_ID_RANK[require_strategy_team_id("team_id", team_id)], team_id)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is float:
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is int:
        raise ValueError(f"{field_name} must not be an integer")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_optional_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_ratio(field_name, value)


def _normalize_signed_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < NEGATIVE_ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _normalize_optional_signed_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_signed_ratio(field_name, value)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is float:
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is int:
        raise ValueError(f"{field_name} must not be an integer")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize_ratio(value)
    if quantized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return quantized


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_memory_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, MEMORY_STATUSES)
