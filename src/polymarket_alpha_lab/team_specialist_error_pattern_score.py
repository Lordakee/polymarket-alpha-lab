"""Readonly team specialist recurring error-pattern score."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_TEAM_SPECIALIST_ERROR_PATTERN_SCORE_CONFIG_VERSION = (
    "team-specialist-error-pattern-score-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_ERROR_PATTERN_STATUSES = frozenset(("pass", "watch", "block"))
_UNSAFE_PUBLIC_TERMS = (
    "market",
    "candidate",
    "slug",
    "question",
    "url",
    "source",
    "ref",
    "text",
    "dsn",
    "table",
    "token",
    "secret",
    "auth",
    "wallet",
    "order",
    "trade",
    "buy",
    "sell",
    "recommendation",
    "position",
    "sizing",
    "live",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
)
_ROW_REASON_CODE_SEQUENCE = (
    "error_pattern_pass",
    "error_pattern_watch",
    "error_pattern_block",
    "resolved_case_depth_full",
    "resolved_case_depth_watch",
    "resolved_case_depth_thin",
    "recurring_errors_clear",
    "recurring_errors_watch",
    "recurring_errors_severe",
    "overconfidence_errors_clear",
    "overconfidence_errors_watch",
    "overconfidence_errors_severe",
    "underreaction_errors_clear",
    "underreaction_errors_watch",
    "underreaction_errors_severe",
    "stale_model_errors_clear",
    "stale_model_errors_watch",
    "stale_model_errors_severe",
    "recent_improvement_strong",
    "recent_improvement_partial",
    "recent_improvement_weak",
)
_REPORT_REASON_CODE_SEQUENCE = (
    "empty_error_pattern_records",
    "error_pattern_score_pass",
    "error_pattern_score_watch",
    "error_pattern_score_block",
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_ERROR_PATTERN_SCORE_CONFIG_VERSION",
    "TeamSpecialistErrorPatternScoreConfig",
    "TeamSpecialistErrorPatternScoreInput",
    "TeamSpecialistErrorPatternScoreRow",
    "TeamSpecialistErrorPatternScoreReport",
    "build_team_specialist_error_pattern_score_report",
    "team_specialist_error_pattern_score_payload",
)


@dataclass(frozen=True)
class TeamSpecialistErrorPatternScoreConfig:
    config_version: str = DEFAULT_TEAM_SPECIALIST_ERROR_PATTERN_SCORE_CONFIG_VERSION
    resolved_case_depth_weight: Decimal = Decimal("0.187500")
    recurring_error_control_weight: Decimal = Decimal("0.287500")
    overconfidence_control_weight: Decimal = Decimal("0.275000")
    underreaction_control_weight: Decimal = Decimal("0.075000")
    stale_model_control_weight: Decimal = Decimal("0.075000")
    recent_improvement_weight: Decimal = Decimal("0.100000")
    max_resolved_case_count: Decimal = Decimal("20.000000")
    max_recurring_error_count: Decimal = Decimal("5.000000")
    watch_recurring_error_count: Decimal = Decimal("2.000000")
    block_recurring_error_count: Decimal = Decimal("4.000000")
    watch_overconfidence_error_ratio: Decimal = Decimal("0.250000")
    block_overconfidence_error_ratio: Decimal = Decimal("0.500000")
    watch_underreaction_error_ratio: Decimal = Decimal("0.200000")
    block_underreaction_error_ratio: Decimal = Decimal("0.500000")
    watch_stale_model_error_ratio: Decimal = Decimal("0.200000")
    block_stale_model_error_ratio: Decimal = Decimal("0.500000")
    recent_improvement_strong_floor: Decimal = Decimal("0.800000")
    recent_improvement_weak_floor: Decimal = Decimal("0.200000")
    pass_score_floor: Decimal = Decimal("0.850000")
    watch_score_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistErrorPatternScoreConfig:
            raise TypeError(
                "TeamSpecialistErrorPatternScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistErrorPatternScoreConfig:
            raise ValueError(
                "config must be exactly TeamSpecialistErrorPatternScoreConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_TEAM_SPECIALIST_ERROR_PATTERN_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "resolved_case_depth_weight",
            "recurring_error_control_weight",
            "overconfidence_control_weight",
            "underreaction_control_weight",
            "stale_model_control_weight",
            "recent_improvement_weight",
            "watch_overconfidence_error_ratio",
            "block_overconfidence_error_ratio",
            "watch_underreaction_error_ratio",
            "block_underreaction_error_ratio",
            "watch_stale_model_error_ratio",
            "block_stale_model_error_ratio",
            "recent_improvement_strong_floor",
            "recent_improvement_weak_floor",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_resolved_case_count",
            "max_recurring_error_count",
            "watch_recurring_error_count",
            "block_recurring_error_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistErrorPatternScoreInput:
    team_id: str
    specialist_id: str
    resolved_case_count: Decimal
    recurring_error_count: Decimal
    overconfidence_error_ratio: Decimal
    underreaction_error_ratio: Decimal
    stale_model_error_ratio: Decimal
    recent_improvement_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistErrorPatternScoreInput:
            raise TypeError(
                "TeamSpecialistErrorPatternScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistErrorPatternScoreInput:
            raise ValueError(
                "record must be exactly TeamSpecialistErrorPatternScoreInput",
            )
        for field_name in ("team_id", "specialist_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in ("resolved_case_count", "recurring_error_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "overconfidence_error_ratio",
            "underreaction_error_ratio",
            "stale_model_error_ratio",
            "recent_improvement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.recurring_error_count > self.resolved_case_count:
            raise ValueError("recurring_error_count must not exceed resolved_case_count")
        _require_hard_flags("record", self)
        _reject_unsafe_public_payload("record", self)


@dataclass(frozen=True)
class TeamSpecialistErrorPatternScoreRow:
    rank: Decimal
    team_id: str
    specialist_id: str
    resolved_case_count: Decimal
    resolved_case_depth_score: Decimal
    recurring_error_count: Decimal
    recurring_error_control_score: Decimal
    overconfidence_error_ratio: Decimal
    overconfidence_control_score: Decimal
    underreaction_error_ratio: Decimal
    underreaction_control_score: Decimal
    stale_model_error_ratio: Decimal
    stale_model_control_score: Decimal
    recent_improvement_score: Decimal
    error_pattern_score: Decimal
    error_pattern_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistErrorPatternScoreRow:
            raise TypeError(
                "TeamSpecialistErrorPatternScoreRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistErrorPatternScoreRow:
            raise ValueError("row must be exactly TeamSpecialistErrorPatternScoreRow")
        for field_name in ("team_id", "specialist_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in ("rank", "resolved_case_count", "recurring_error_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolved_case_depth_score",
            "recurring_error_control_score",
            "overconfidence_error_ratio",
            "overconfidence_control_score",
            "underreaction_error_ratio",
            "underreaction_control_score",
            "stale_model_error_ratio",
            "stale_model_control_score",
            "recent_improvement_score",
            "error_pattern_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_error_pattern_status("error_pattern_status", self.error_pattern_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class TeamSpecialistErrorPatternScoreReport:
    generated_at: datetime
    config_version: str
    error_pattern_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_error_pattern_score: Decimal
    top_error_pattern_score: Decimal
    bottom_error_pattern_score: Decimal
    rows: tuple[TeamSpecialistErrorPatternScoreRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistErrorPatternScoreReport:
            raise TypeError(
                "TeamSpecialistErrorPatternScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistErrorPatternScoreReport:
            raise ValueError(
                "report must be exactly TeamSpecialistErrorPatternScoreReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_TEAM_SPECIALIST_ERROR_PATTERN_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_error_pattern_status("error_pattern_status", self.error_pattern_status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_error_pattern_score",
            "top_error_pattern_score",
            "bottom_error_pattern_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REPORT_REASON_CODE_SEQUENCE),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistErrorPatternScoreReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_error_pattern_score_report(
    records: Sequence[TeamSpecialistErrorPatternScoreInput],
    *,
    generated_at: datetime,
    config: TeamSpecialistErrorPatternScoreConfig | None = None,
) -> TeamSpecialistErrorPatternScoreReport:
    if config is None:
        config = TeamSpecialistErrorPatternScoreConfig()
    if type(config) is not TeamSpecialistErrorPatternScoreConfig:
        raise ValueError("config must be a TeamSpecialistErrorPatternScoreConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_records = _normalize_records(records)
    rows = _rank_rows(tuple(_row_without_rank(record, config) for record in normalized_records))
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "error_pattern_status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_error_pattern_score": _average(
            tuple(row.error_pattern_score for row in rows),
        ),
        "top_error_pattern_score": _top_score(rows),
        "bottom_error_pattern_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamSpecialistErrorPatternScoreReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def team_specialist_error_pattern_score_payload(
    report: TeamSpecialistErrorPatternScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistErrorPatternScoreReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = report.payload
        _require_hard_flags("payload", _DictFlags(payload))
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        return payload
    raise ValueError("report must be a TeamSpecialistErrorPatternScoreReport or payload")


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


def _row_without_rank(
    record: TeamSpecialistErrorPatternScoreInput,
    config: TeamSpecialistErrorPatternScoreConfig,
) -> TeamSpecialistErrorPatternScoreRow:
    resolved_case_depth_score = _clamp_ratio(
        record.resolved_case_count / config.max_resolved_case_count,
    )
    recurring_error_control_score = _clamp_ratio(
        _ONE - record.recurring_error_count / config.max_recurring_error_count,
    )
    overconfidence_control_score = _clamp_ratio(_ONE - record.overconfidence_error_ratio)
    underreaction_control_score = _clamp_ratio(_ONE - record.underreaction_error_ratio)
    stale_model_control_score = _clamp_ratio(_ONE - record.stale_model_error_ratio)
    error_pattern_score = _score(
        resolved_case_depth_score=resolved_case_depth_score,
        recurring_error_control_score=recurring_error_control_score,
        overconfidence_control_score=overconfidence_control_score,
        underreaction_control_score=underreaction_control_score,
        stale_model_control_score=stale_model_control_score,
        recent_improvement_score=record.recent_improvement_score,
        config=config,
    )
    error_pattern_status = _row_status(record, error_pattern_score, config)
    return TeamSpecialistErrorPatternScoreRow(
        rank=_ZERO,
        team_id=record.team_id,
        specialist_id=record.specialist_id,
        resolved_case_count=record.resolved_case_count,
        resolved_case_depth_score=resolved_case_depth_score,
        recurring_error_count=record.recurring_error_count,
        recurring_error_control_score=recurring_error_control_score,
        overconfidence_error_ratio=record.overconfidence_error_ratio,
        overconfidence_control_score=overconfidence_control_score,
        underreaction_error_ratio=record.underreaction_error_ratio,
        underreaction_control_score=underreaction_control_score,
        stale_model_error_ratio=record.stale_model_error_ratio,
        stale_model_control_score=stale_model_control_score,
        recent_improvement_score=record.recent_improvement_score,
        error_pattern_score=error_pattern_score,
        error_pattern_status=error_pattern_status,
        reason_codes=_row_reason_codes(
            resolved_case_depth_score=resolved_case_depth_score,
            recurring_error_count=record.recurring_error_count,
            overconfidence_error_ratio=record.overconfidence_error_ratio,
            underreaction_error_ratio=record.underreaction_error_ratio,
            stale_model_error_ratio=record.stale_model_error_ratio,
            recent_improvement_score=record.recent_improvement_score,
            error_pattern_status=error_pattern_status,
            config=config,
        ),
    )


def _rank_rows(
    rows: tuple[TeamSpecialistErrorPatternScoreRow, ...],
) -> tuple[TeamSpecialistErrorPatternScoreRow, ...]:
    ranked_rows = []
    for index, row in enumerate(
        sorted(
            rows,
            key=lambda item: (
                -item.error_pattern_score,
                item.recurring_error_count,
                item.team_id,
                item.specialist_id,
            ),
        ),
        start=1,
    ):
        ranked_rows.append(replace(row, rank=_decimal_count(index)))
    return tuple(ranked_rows)


def _score(
    *,
    resolved_case_depth_score: Decimal,
    recurring_error_control_score: Decimal,
    overconfidence_control_score: Decimal,
    underreaction_control_score: Decimal,
    stale_model_control_score: Decimal,
    recent_improvement_score: Decimal,
    config: TeamSpecialistErrorPatternScoreConfig,
) -> Decimal:
    return _clamp_ratio(
        resolved_case_depth_score * config.resolved_case_depth_weight
        + recurring_error_control_score * config.recurring_error_control_weight
        + overconfidence_control_score * config.overconfidence_control_weight
        + underreaction_control_score * config.underreaction_control_weight
        + stale_model_control_score * config.stale_model_control_weight
        + recent_improvement_score * config.recent_improvement_weight,
    )


def _row_status(
    record: TeamSpecialistErrorPatternScoreInput,
    error_pattern_score: Decimal,
    config: TeamSpecialistErrorPatternScoreConfig,
) -> str:
    if _has_severe_error_pattern(record, config):
        return "block"
    if error_pattern_score < config.watch_score_floor:
        return "block"
    if error_pattern_score < config.pass_score_floor:
        return "watch"
    if _has_watch_error_pattern(record, config):
        return "watch"
    return "pass"


def _has_severe_error_pattern(
    record: TeamSpecialistErrorPatternScoreInput,
    config: TeamSpecialistErrorPatternScoreConfig,
) -> bool:
    if record.recent_improvement_score > config.recent_improvement_weak_floor:
        return False
    return (
        record.recurring_error_count >= config.block_recurring_error_count
        or record.overconfidence_error_ratio >= config.block_overconfidence_error_ratio
        or record.underreaction_error_ratio >= config.block_underreaction_error_ratio
        or record.stale_model_error_ratio >= config.block_stale_model_error_ratio
    )


def _has_watch_error_pattern(
    record: TeamSpecialistErrorPatternScoreInput,
    config: TeamSpecialistErrorPatternScoreConfig,
) -> bool:
    return (
        record.recurring_error_count >= config.watch_recurring_error_count
        or record.overconfidence_error_ratio >= config.watch_overconfidence_error_ratio
        or record.underreaction_error_ratio >= config.watch_underreaction_error_ratio
        or record.stale_model_error_ratio >= config.watch_stale_model_error_ratio
    )


def _report_status(rows: tuple[TeamSpecialistErrorPatternScoreRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.error_pattern_status == "block" for row in rows):
        return "block"
    if any(row.error_pattern_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    resolved_case_depth_score: Decimal,
    recurring_error_count: Decimal,
    overconfidence_error_ratio: Decimal,
    underreaction_error_ratio: Decimal,
    stale_model_error_ratio: Decimal,
    recent_improvement_score: Decimal,
    error_pattern_status: str,
    config: TeamSpecialistErrorPatternScoreConfig,
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        (
            f"error_pattern_{error_pattern_status}",
            _tier_reason(
                resolved_case_depth_score,
                strong=Decimal("1.000000"),
                watch=Decimal("0.500000"),
                strong_reason="resolved_case_depth_full",
                watch_reason="resolved_case_depth_watch",
                weak_reason="resolved_case_depth_thin",
            ),
            _count_reason(
                recurring_error_count,
                watch=config.watch_recurring_error_count,
                severe=config.block_recurring_error_count,
                clear_reason="recurring_errors_clear",
                watch_reason="recurring_errors_watch",
                severe_reason="recurring_errors_severe",
            ),
            _ratio_reason(
                overconfidence_error_ratio,
                watch=config.watch_overconfidence_error_ratio,
                severe=config.block_overconfidence_error_ratio,
                clear_reason="overconfidence_errors_clear",
                watch_reason="overconfidence_errors_watch",
                severe_reason="overconfidence_errors_severe",
            ),
            _ratio_reason(
                underreaction_error_ratio,
                watch=config.watch_underreaction_error_ratio,
                severe=config.block_underreaction_error_ratio,
                clear_reason="underreaction_errors_clear",
                watch_reason="underreaction_errors_watch",
                severe_reason="underreaction_errors_severe",
            ),
            _ratio_reason(
                stale_model_error_ratio,
                watch=config.watch_stale_model_error_ratio,
                severe=config.block_stale_model_error_ratio,
                clear_reason="stale_model_errors_clear",
                watch_reason="stale_model_errors_watch",
                severe_reason="stale_model_errors_severe",
            ),
            _improvement_reason(recent_improvement_score, config),
        ),
        _ROW_REASON_CODE_SEQUENCE,
    )


def _report_reason_codes(
    rows: tuple[TeamSpecialistErrorPatternScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_error_pattern_records",)
    reason_codes: list[str] = []
    if all(row.error_pattern_status == "pass" for row in rows):
        reason_codes.append("error_pattern_score_pass")
    if any(row.error_pattern_status == "watch" for row in rows):
        reason_codes.append("error_pattern_score_watch")
    if any(row.error_pattern_status == "block" for row in rows):
        reason_codes.append("error_pattern_score_block")
    return _normalize_reason_codes(tuple(reason_codes), _REPORT_REASON_CODE_SEQUENCE)


def _tier_reason(
    value: Decimal,
    *,
    strong: Decimal,
    watch: Decimal,
    strong_reason: str,
    watch_reason: str,
    weak_reason: str,
) -> str:
    if value >= strong:
        return strong_reason
    if value >= watch:
        return watch_reason
    return weak_reason


def _count_reason(
    value: Decimal,
    *,
    watch: Decimal,
    severe: Decimal,
    clear_reason: str,
    watch_reason: str,
    severe_reason: str,
) -> str:
    if value >= severe:
        return severe_reason
    if value >= watch:
        return watch_reason
    return clear_reason


def _ratio_reason(
    value: Decimal,
    *,
    watch: Decimal,
    severe: Decimal,
    clear_reason: str,
    watch_reason: str,
    severe_reason: str,
) -> str:
    if value >= severe:
        return severe_reason
    if value >= watch:
        return watch_reason
    return clear_reason


def _improvement_reason(
    value: Decimal,
    config: TeamSpecialistErrorPatternScoreConfig,
) -> str:
    if value >= config.recent_improvement_strong_floor:
        return "recent_improvement_strong"
    if value <= config.recent_improvement_weak_floor:
        return "recent_improvement_weak"
    return "recent_improvement_partial"


def _status_count(rows: tuple[TeamSpecialistErrorPatternScoreRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.error_pattern_status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _top_score(rows: tuple[TeamSpecialistErrorPatternScoreRow, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return max(row.error_pattern_score for row in rows)


def _bottom_score(rows: tuple[TeamSpecialistErrorPatternScoreRow, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return min(row.error_pattern_score for row in rows)


def _validate_config(config: TeamSpecialistErrorPatternScoreConfig) -> None:
    weights_total = _quantize(
        config.resolved_case_depth_weight
        + config.recurring_error_control_weight
        + config.overconfidence_control_weight
        + config.underreaction_control_weight
        + config.stale_model_control_weight
        + config.recent_improvement_weight,
    )
    if weights_total != _ONE:
        raise ValueError("score weights must sum to 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must not exceed pass_score_floor")
    if config.watch_recurring_error_count > config.block_recurring_error_count:
        raise ValueError(
            "watch_recurring_error_count must not exceed block_recurring_error_count",
        )
    if config.watch_overconfidence_error_ratio > config.block_overconfidence_error_ratio:
        raise ValueError(
            "watch_overconfidence_error_ratio must not exceed "
            "block_overconfidence_error_ratio",
        )
    if config.watch_underreaction_error_ratio > config.block_underreaction_error_ratio:
        raise ValueError(
            "watch_underreaction_error_ratio must not exceed "
            "block_underreaction_error_ratio",
        )
    if config.watch_stale_model_error_ratio > config.block_stale_model_error_ratio:
        raise ValueError(
            "watch_stale_model_error_ratio must not exceed "
            "block_stale_model_error_ratio",
        )
    if config.recent_improvement_weak_floor > config.recent_improvement_strong_floor:
        raise ValueError(
            "recent_improvement_weak_floor must not exceed "
            "recent_improvement_strong_floor",
        )


def _validate_row_consistency(row: TeamSpecialistErrorPatternScoreRow) -> None:
    if row.recurring_error_count > row.resolved_case_count:
        raise ValueError("recurring_error_count must not exceed resolved_case_count")
    if row.error_pattern_status == "pass" and "error_pattern_pass" not in row.reason_codes:
        raise ValueError("pass rows must include error_pattern_pass")
    if row.error_pattern_status == "watch" and "error_pattern_watch" not in row.reason_codes:
        raise ValueError("watch rows must include error_pattern_watch")
    if row.error_pattern_status == "block" and "error_pattern_block" not in row.reason_codes:
        raise ValueError("block rows must include error_pattern_block")


def _validate_report_consistency(report: TeamSpecialistErrorPatternScoreReport) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_error_pattern_score != _average(
        tuple(row.error_pattern_score for row in rows),
    ):
        raise ValueError("average_error_pattern_score must match rows")
    if report.top_error_pattern_score != _top_score(rows):
        raise ValueError("top_error_pattern_score must match rows")
    if report.bottom_error_pattern_score != _bottom_score(rows):
        raise ValueError("bottom_error_pattern_score must match rows")
    if report.error_pattern_status != _report_status(rows):
        raise ValueError("error_pattern_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    _validate_rows_sorted(rows)


def _validate_rows_sorted(rows: tuple[TeamSpecialistErrorPatternScoreRow, ...]) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.error_pattern_score,
                row.recurring_error_count,
                row.team_id,
                row.specialist_id,
            ),
        ),
    )
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    if rows != expected or tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must be sorted by score and rank")


def _normalize_records(
    records: Sequence[TeamSpecialistErrorPatternScoreInput],
) -> tuple[TeamSpecialistErrorPatternScoreInput, ...]:
    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
        raise ValueError("records must be a sequence")
    normalized: list[TeamSpecialistErrorPatternScoreInput] = []
    seen_keys: set[tuple[str, str]] = set()
    for record in records:
        if type(record) is not TeamSpecialistErrorPatternScoreInput:
            raise ValueError(
                "records must contain TeamSpecialistErrorPatternScoreInput",
            )
        key = (record.team_id, record.specialist_id)
        if key in seen_keys:
            raise ValueError("duplicate team/specialist record")
        seen_keys.add(key)
        normalized.append(record)
    return tuple(sorted(normalized, key=lambda item: (item.team_id, item.specialist_id)))


def _normalize_rows(
    rows: Sequence[TeamSpecialistErrorPatternScoreRow],
) -> tuple[TeamSpecialistErrorPatternScoreRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[TeamSpecialistErrorPatternScoreRow] = []
    for row in rows:
        if type(row) is not TeamSpecialistErrorPatternScoreRow:
            raise ValueError("rows must contain TeamSpecialistErrorPatternScoreRow")
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.rank))


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in supported:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in supported if reason_code in normalized)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _require_error_pattern_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _ERROR_PATTERN_STATUSES:
        raise ValueError(f"{field_name} must be a known error-pattern status")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize(value)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: TeamSpecialistErrorPatternScoreReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest payload", payload, allow_json_containers=True)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    value = _json_ready(value) if not allow_json_containers else value
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} has unsafe public field")
            _reject_unsafe_public_key(key, label)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if type(value) is float:
        raise ValueError(f"{label} must not contain float values")
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
