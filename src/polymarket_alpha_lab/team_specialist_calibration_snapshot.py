"""Readonly Decimal report for specialist calibration snapshots."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_CALIBRATION_SNAPSHOT_CONFIG_VERSION = (
    "team-specialist-calibration-snapshot-v1"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

SNAPSHOT_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "snapshot_pass",
    "snapshot_watch",
    "snapshot_block",
    "sample_size_strong",
    "sample_size_watch",
    "sample_size_low",
    "sample_fresh",
    "sample_stale_watch",
    "sample_stale_block",
    "brier_score_strong",
    "brier_score_watch",
    "brier_score_block",
    "calibration_error_low",
    "calibration_error_watch",
    "calibration_error_block",
    "hit_rate_strong",
    "hit_rate_watch",
    "hit_rate_block",
    "confidence_bias_low",
    "confidence_bias_watch",
    "confidence_bias_block",
)
REPORT_REASON_CODES = (
    "calibration_snapshot_report_pass",
    "calibration_snapshot_report_watch_rows",
    "calibration_snapshot_report_block_rows",
    "calibration_snapshot_report_empty",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "market",
    "candidate",
    "slug",
    "question",
    "url",
    "http://",
    "https://",
    "source",
    "ref",
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
    "persist",
    "supabase",
    "network",
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_CALIBRATION_SNAPSHOT_CONFIG_VERSION",
    "TeamSpecialistCalibrationSnapshotConfig",
    "TeamSpecialistCalibrationSnapshotInput",
    "TeamSpecialistCalibrationSnapshotRow",
    "TeamSpecialistCalibrationSnapshotReport",
    "build_team_specialist_calibration_snapshot_report",
)


@dataclass(frozen=True)
class TeamSpecialistCalibrationSnapshotConfig:
    config_version: str = DEFAULT_TEAM_SPECIALIST_CALIBRATION_SNAPSHOT_CONFIG_VERSION
    brier_score_weight: Decimal = Decimal("0.250000")
    calibration_error_score_weight: Decimal = Decimal("0.250000")
    recent_hit_rate_weight: Decimal = Decimal("0.200000")
    confidence_bias_score_weight: Decimal = Decimal("0.150000")
    sample_size_weight: Decimal = Decimal("0.100000")
    sample_freshness_weight: Decimal = Decimal("0.050000")
    min_resolved_prediction_count: Decimal = Decimal("30")
    watch_resolved_prediction_count: Decimal = Decimal("60")
    pass_brier_score_ceiling: Decimal = Decimal("0.200000")
    block_brier_score_ceiling: Decimal = Decimal("0.350000")
    pass_calibration_error_score_ceiling: Decimal = Decimal("0.100000")
    block_calibration_error_score_ceiling: Decimal = Decimal("0.250000")
    pass_recent_hit_rate_floor: Decimal = Decimal("0.550000")
    block_recent_hit_rate_floor: Decimal = Decimal("0.350000")
    pass_confidence_bias_score_ceiling: Decimal = Decimal("0.100000")
    block_confidence_bias_score_ceiling: Decimal = Decimal("0.250000")
    watch_stale_sample_days: Decimal = Decimal("21")
    max_stale_sample_days: Decimal = Decimal("45")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "brier_score_weight",
            "calibration_error_score_weight",
            "recent_hit_rate_weight",
            "confidence_bias_score_weight",
            "sample_size_weight",
            "sample_freshness_weight",
            "pass_brier_score_ceiling",
            "block_brier_score_ceiling",
            "pass_calibration_error_score_ceiling",
            "block_calibration_error_score_ceiling",
            "pass_recent_hit_rate_floor",
            "block_recent_hit_rate_floor",
            "pass_confidence_bias_score_ceiling",
            "block_confidence_bias_score_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_resolved_prediction_count",
            "watch_resolved_prediction_count",
            "watch_stale_sample_days",
            "max_stale_sample_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistCalibrationSnapshotConfig", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationSnapshotConfig",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCalibrationSnapshotInput:
    team_id: str
    specialist_id: str
    resolved_prediction_count: Decimal
    brier_score: Decimal
    calibration_error_score: Decimal
    recent_hit_rate: Decimal
    confidence_bias_score: Decimal
    stale_sample_days: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "team_id",
            _require_non_empty_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_non_empty_string("specialist_id", self.specialist_id),
        )
        for field_name in (
            "brier_score",
            "calibration_error_score",
            "recent_hit_rate",
            "confidence_bias_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("resolved_prediction_count", "stale_sample_days"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_hard_flags("TeamSpecialistCalibrationSnapshotInput", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationSnapshotInput",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCalibrationSnapshotRow:
    rank: Decimal
    team_id: str
    specialist_id: str
    resolved_prediction_count: Decimal
    brier_score: Decimal
    brier_health_score: Decimal
    calibration_error_score: Decimal
    calibration_error_health_score: Decimal
    recent_hit_rate: Decimal
    confidence_bias_score: Decimal
    confidence_bias_health_score: Decimal
    stale_sample_days: Decimal
    sample_size_score: Decimal
    sample_freshness_score: Decimal
    calibration_snapshot_score: Decimal
    routing_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        object.__setattr__(
            self,
            "team_id",
            _require_non_empty_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_non_empty_string("specialist_id", self.specialist_id),
        )
        for field_name in (
            "brier_score",
            "brier_health_score",
            "calibration_error_score",
            "calibration_error_health_score",
            "recent_hit_rate",
            "confidence_bias_score",
            "confidence_bias_health_score",
            "sample_size_score",
            "sample_freshness_score",
            "calibration_snapshot_score",
            "routing_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("resolved_prediction_count", "stale_sample_days"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_snapshot_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("TeamSpecialistCalibrationSnapshotRow", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationSnapshotRow",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class TeamSpecialistCalibrationSnapshotReport:
    generated_at: datetime
    config_version: str
    report_status: str
    snapshot_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_calibration_snapshot_score: Decimal
    top_calibration_snapshot_score: Decimal
    bottom_calibration_snapshot_score: Decimal
    max_routing_priority_score: Decimal
    rows: tuple[TeamSpecialistCalibrationSnapshotRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_report_status("report_status", self.report_status)
        for field_name in (
            "snapshot_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_calibration_snapshot_score",
            "top_calibration_snapshot_score",
            "bottom_calibration_snapshot_score",
            "max_routing_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("TeamSpecialistCalibrationSnapshotReport", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationSnapshotReport",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationSnapshotReport.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_calibration_snapshot_report(
    snapshots: object,
    *,
    config: TeamSpecialistCalibrationSnapshotConfig | None = None,
    generated_at: datetime,
) -> TeamSpecialistCalibrationSnapshotReport:
    if config is None:
        config = TeamSpecialistCalibrationSnapshotConfig()
    if type(config) is not TeamSpecialistCalibrationSnapshotConfig:
        raise ValueError("config must be a TeamSpecialistCalibrationSnapshotConfig")
    _require_hard_flags("TeamSpecialistCalibrationSnapshotConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)

    rows = tuple(
        _row_for_snapshot(rank=index, snapshot=item, config=config)
        for index, item in enumerate(
            _sorted_snapshots(normalized_snapshots, config),
            start=1,
        )
    )
    status = _report_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": status,
        "snapshot_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_calibration_snapshot_score": _average_snapshot_score(rows),
        "top_calibration_snapshot_score": _top_snapshot_score(rows),
        "bottom_calibration_snapshot_score": _bottom_snapshot_score(rows),
        "max_routing_priority_score": _max_routing_priority_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistCalibrationSnapshotReport(**values)


def _sorted_snapshots(
    snapshots: tuple[TeamSpecialistCalibrationSnapshotInput, ...],
    config: TeamSpecialistCalibrationSnapshotConfig,
) -> tuple[TeamSpecialistCalibrationSnapshotInput, ...]:
    return tuple(
        sorted(
            snapshots,
            key=lambda item: (
                -_routing_priority_score(item, config),
                item.team_id,
                item.specialist_id,
            ),
        ),
    )


def _row_for_snapshot(
    *,
    rank: int,
    snapshot: TeamSpecialistCalibrationSnapshotInput,
    config: TeamSpecialistCalibrationSnapshotConfig,
) -> TeamSpecialistCalibrationSnapshotRow:
    status = _snapshot_status(snapshot, config)
    snapshot_score = _calibration_snapshot_score(snapshot, config)
    return TeamSpecialistCalibrationSnapshotRow(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        team_id=snapshot.team_id,
        specialist_id=snapshot.specialist_id,
        resolved_prediction_count=snapshot.resolved_prediction_count,
        brier_score=snapshot.brier_score,
        brier_health_score=_inverse_ratio(snapshot.brier_score),
        calibration_error_score=snapshot.calibration_error_score,
        calibration_error_health_score=_inverse_ratio(snapshot.calibration_error_score),
        recent_hit_rate=snapshot.recent_hit_rate,
        confidence_bias_score=snapshot.confidence_bias_score,
        confidence_bias_health_score=_inverse_ratio(snapshot.confidence_bias_score),
        stale_sample_days=snapshot.stale_sample_days,
        sample_size_score=_sample_size_score(snapshot.resolved_prediction_count, config),
        sample_freshness_score=_sample_freshness_score(snapshot.stale_sample_days, config),
        calibration_snapshot_score=snapshot_score,
        routing_priority_score=_routing_priority_from_status(snapshot_score, status),
        status=status,
        reason_codes=_row_reason_codes(snapshot, status, config),
    )


def _calibration_snapshot_score(
    snapshot: TeamSpecialistCalibrationSnapshotInput,
    config: TeamSpecialistCalibrationSnapshotConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            _inverse_ratio(snapshot.brier_score) * config.brier_score_weight
            + _inverse_ratio(snapshot.calibration_error_score)
            * config.calibration_error_score_weight
            + snapshot.recent_hit_rate * config.recent_hit_rate_weight
            + _inverse_ratio(snapshot.confidence_bias_score)
            * config.confidence_bias_score_weight
            + _sample_size_score(snapshot.resolved_prediction_count, config)
            * config.sample_size_weight
            + _sample_freshness_score(snapshot.stale_sample_days, config)
            * config.sample_freshness_weight
        )
        return _clamp_ratio(score)


def _routing_priority_score(
    snapshot: TeamSpecialistCalibrationSnapshotInput,
    config: TeamSpecialistCalibrationSnapshotConfig,
) -> Decimal:
    status = _snapshot_status(snapshot, config)
    score = _calibration_snapshot_score(snapshot, config)
    return _routing_priority_from_status(score, status)


def _routing_priority_from_status(score: Decimal, status: str) -> Decimal:
    base_priority = _inverse_ratio(score)
    if status == "block":
        return max(base_priority, Decimal("0.900000")).quantize(SCORE_QUANT)
    if status == "watch":
        return max(base_priority, Decimal("0.500000")).quantize(SCORE_QUANT)
    return base_priority


def _snapshot_status(
    snapshot: TeamSpecialistCalibrationSnapshotInput,
    config: TeamSpecialistCalibrationSnapshotConfig,
) -> str:
    if (
        snapshot.resolved_prediction_count < config.min_resolved_prediction_count
        or snapshot.stale_sample_days > config.max_stale_sample_days
        or snapshot.brier_score > config.block_brier_score_ceiling
        or snapshot.calibration_error_score
        > config.block_calibration_error_score_ceiling
        or snapshot.recent_hit_rate < config.block_recent_hit_rate_floor
        or snapshot.confidence_bias_score > config.block_confidence_bias_score_ceiling
    ):
        return "block"
    if (
        snapshot.resolved_prediction_count < config.watch_resolved_prediction_count
        or snapshot.stale_sample_days > config.watch_stale_sample_days
        or snapshot.brier_score > config.pass_brier_score_ceiling
        or snapshot.calibration_error_score
        > config.pass_calibration_error_score_ceiling
        or snapshot.recent_hit_rate < config.pass_recent_hit_rate_floor
        or snapshot.confidence_bias_score > config.pass_confidence_bias_score_ceiling
    ):
        return "watch"
    return "pass"


def _report_status(rows: tuple[TeamSpecialistCalibrationSnapshotRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    snapshot: TeamSpecialistCalibrationSnapshotInput,
    status: str,
    config: TeamSpecialistCalibrationSnapshotConfig,
) -> tuple[str, ...]:
    return (
        f"snapshot_{status}",
        _sample_size_reason(snapshot.resolved_prediction_count, config),
        _sample_freshness_reason(snapshot.stale_sample_days, config),
        _ceiling_reason(
            snapshot.brier_score,
            pass_ceiling=config.pass_brier_score_ceiling,
            block_ceiling=config.block_brier_score_ceiling,
            strong_reason="brier_score_strong",
            watch_reason="brier_score_watch",
            block_reason="brier_score_block",
        ),
        _ceiling_reason(
            snapshot.calibration_error_score,
            pass_ceiling=config.pass_calibration_error_score_ceiling,
            block_ceiling=config.block_calibration_error_score_ceiling,
            strong_reason="calibration_error_low",
            watch_reason="calibration_error_watch",
            block_reason="calibration_error_block",
        ),
        _floor_reason(
            snapshot.recent_hit_rate,
            pass_floor=config.pass_recent_hit_rate_floor,
            block_floor=config.block_recent_hit_rate_floor,
            strong_reason="hit_rate_strong",
            watch_reason="hit_rate_watch",
            block_reason="hit_rate_block",
        ),
        _ceiling_reason(
            snapshot.confidence_bias_score,
            pass_ceiling=config.pass_confidence_bias_score_ceiling,
            block_ceiling=config.block_confidence_bias_score_ceiling,
            strong_reason="confidence_bias_low",
            watch_reason="confidence_bias_watch",
            block_reason="confidence_bias_block",
        ),
    )


def _report_reason_codes(
    rows: tuple[TeamSpecialistCalibrationSnapshotRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("calibration_snapshot_report_empty",)
    reasons: list[str] = []
    if any(row.status == "block" for row in rows):
        reasons.append("calibration_snapshot_report_block_rows")
    if any(row.status == "watch" for row in rows):
        reasons.append("calibration_snapshot_report_watch_rows")
    if not reasons and status == "pass":
        reasons.append("calibration_snapshot_report_pass")
    return tuple(reasons)


def _sample_size_score(
    resolved_prediction_count: Decimal,
    config: TeamSpecialistCalibrationSnapshotConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            resolved_prediction_count / config.watch_resolved_prediction_count,
        )


def _sample_freshness_score(
    stale_sample_days: Decimal,
    config: TeamSpecialistCalibrationSnapshotConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - stale_sample_days / config.max_stale_sample_days)


def _inverse_ratio(value: Decimal) -> Decimal:
    return _clamp_ratio(ONE - value)


def _sample_size_reason(
    value: Decimal,
    config: TeamSpecialistCalibrationSnapshotConfig,
) -> str:
    if value < config.min_resolved_prediction_count:
        return "sample_size_low"
    if value < config.watch_resolved_prediction_count:
        return "sample_size_watch"
    return "sample_size_strong"


def _sample_freshness_reason(
    value: Decimal,
    config: TeamSpecialistCalibrationSnapshotConfig,
) -> str:
    if value > config.max_stale_sample_days:
        return "sample_stale_block"
    if value > config.watch_stale_sample_days:
        return "sample_stale_watch"
    return "sample_fresh"


def _ceiling_reason(
    value: Decimal,
    *,
    pass_ceiling: Decimal,
    block_ceiling: Decimal,
    strong_reason: str,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value > block_ceiling:
        return block_reason
    if value > pass_ceiling:
        return watch_reason
    return strong_reason


def _floor_reason(
    value: Decimal,
    *,
    pass_floor: Decimal,
    block_floor: Decimal,
    strong_reason: str,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value < block_floor:
        return block_reason
    if value < pass_floor:
        return watch_reason
    return strong_reason


def _status_count(
    rows: tuple[TeamSpecialistCalibrationSnapshotRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.status == status)).quantize(COUNT_QUANT)


def _average_snapshot_score(
    rows: tuple[TeamSpecialistCalibrationSnapshotRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.calibration_snapshot_score for row in rows), ZERO)
            / Decimal(len(rows)),
        )


def _top_snapshot_score(
    rows: tuple[TeamSpecialistCalibrationSnapshotRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.calibration_snapshot_score for row in rows)


def _bottom_snapshot_score(
    rows: tuple[TeamSpecialistCalibrationSnapshotRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.calibration_snapshot_score for row in rows)


def _max_routing_priority_score(
    rows: tuple[TeamSpecialistCalibrationSnapshotRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.routing_priority_score for row in rows)


def _normalize_snapshots(
    value: object,
) -> tuple[TeamSpecialistCalibrationSnapshotInput, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("snapshots must be an iterable")
    snapshots = tuple(value)
    for item in snapshots:
        if type(item) is not TeamSpecialistCalibrationSnapshotInput:
            raise ValueError(
                "snapshot items must be TeamSpecialistCalibrationSnapshotInput",
            )
        _require_hard_flags("TeamSpecialistCalibrationSnapshotInput", item)
    keys = tuple((item.team_id, item.specialist_id) for item in snapshots)
    if len(set(keys)) != len(keys):
        raise ValueError("snapshot items must not contain duplicate team/specialist keys")
    return snapshots


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistCalibrationSnapshotRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistCalibrationSnapshotRow:
            raise ValueError("rows must contain TeamSpecialistCalibrationSnapshotRow")
    return value


def _validate_config(config: TeamSpecialistCalibrationSnapshotConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.brier_score_weight
            + config.calibration_error_score_weight
            + config.recent_hit_rate_weight
            + config.confidence_bias_score_weight
            + config.sample_size_weight
            + config.sample_freshness_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("snapshot weights must sum to 1.000000")
    if config.min_resolved_prediction_count > config.watch_resolved_prediction_count:
        raise ValueError(
            "min_resolved_prediction_count must not exceed watch_resolved_prediction_count",
        )
    if config.watch_stale_sample_days > config.max_stale_sample_days:
        raise ValueError("watch_stale_sample_days must not exceed max_stale_sample_days")
    if config.pass_brier_score_ceiling > config.block_brier_score_ceiling:
        raise ValueError("pass_brier_score_ceiling must not exceed block_brier_score_ceiling")
    if (
        config.pass_calibration_error_score_ceiling
        > config.block_calibration_error_score_ceiling
    ):
        raise ValueError(
            "pass_calibration_error_score_ceiling must not exceed block_calibration_error_score_ceiling",
        )
    if config.block_recent_hit_rate_floor > config.pass_recent_hit_rate_floor:
        raise ValueError("block_recent_hit_rate_floor must not exceed pass_recent_hit_rate_floor")
    if (
        config.pass_confidence_bias_score_ceiling
        > config.block_confidence_bias_score_ceiling
    ):
        raise ValueError(
            "pass_confidence_bias_score_ceiling must not exceed block_confidence_bias_score_ceiling",
        )


def _validate_row_consistency(row: TeamSpecialistCalibrationSnapshotRow) -> None:
    if row.brier_health_score != _inverse_ratio(row.brier_score):
        raise ValueError("brier_health_score must match brier_score")
    if row.calibration_error_health_score != _inverse_ratio(
        row.calibration_error_score,
    ):
        raise ValueError(
            "calibration_error_health_score must match calibration_error_score",
        )
    if row.confidence_bias_health_score != _inverse_ratio(row.confidence_bias_score):
        raise ValueError("confidence_bias_health_score must match confidence_bias_score")
    if row.routing_priority_score != _routing_priority_from_status(
        row.calibration_snapshot_score,
        row.status,
    ):
        raise ValueError("routing_priority_score must match status and score")


def _validate_report_consistency(
    report: TeamSpecialistCalibrationSnapshotReport,
) -> None:
    rows = report.rows
    if report.snapshot_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("snapshot_count must match rows")
    if (
        report.pass_count != _status_count(rows, "pass")
        or report.watch_count != _status_count(rows, "watch")
        or report.block_count != _status_count(rows, "block")
    ):
        raise ValueError("status counts must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.snapshot_count:
        raise ValueError("status counts must sum to snapshot_count")
    _validate_rows_sorted(rows)
    expected_status = _report_status(rows)
    if report.report_status != expected_status:
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.report_status):
        raise ValueError("reason_codes must match report_status")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_calibration_snapshot_score != _average_snapshot_score(rows):
        raise ValueError("average_calibration_snapshot_score must match rows")
    if report.top_calibration_snapshot_score != _top_snapshot_score(rows):
        raise ValueError("top_calibration_snapshot_score must match rows")
    if report.bottom_calibration_snapshot_score != _bottom_snapshot_score(rows):
        raise ValueError("bottom_calibration_snapshot_score must match rows")
    if report.max_routing_priority_score != _max_routing_priority_score(rows):
        raise ValueError("max_routing_priority_score must match rows")


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistCalibrationSnapshotRow, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.routing_priority_score,
                row.team_id,
                row.specialist_id,
            ),
        ),
    )
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by routing priority and rank")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _require_snapshot_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in SNAPSHOT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_report_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is float:
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
