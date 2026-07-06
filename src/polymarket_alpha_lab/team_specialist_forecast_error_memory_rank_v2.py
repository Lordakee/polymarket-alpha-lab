"""Phase 1 report-only team specialist forecast error memory ranking."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_TEAM_SPECIALIST_FORECAST_ERROR_MEMORY_RANK_V2_CONFIG_VERSION = (
    "team-specialist-forecast-error-memory-rank-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_MEMORY_STATUSES = frozenset(("pass", "watch", "blocked"))
_UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
_REASON_CODE_SEQUENCE = (
    "empty_memory_records",
    "memory_rank_blocked",
    "recent_error_watch",
    "repeated_error_penalty_applied",
    "recent_improvement_boost_applied",
    "memory_rank_watch",
    "memory_rank_pass",
)


@dataclass(frozen=True)
class TeamSpecialistForecastErrorMemoryRankConfig:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_FORECAST_ERROR_MEMORY_RANK_V2_CONFIG_VERSION
    )
    repeated_error_watch_threshold: Decimal = Decimal("0.400000")
    repeated_error_block_threshold: Decimal = Decimal("0.500000")
    repeated_error_penalty_per_record: Decimal = Decimal("0.100000")
    recent_improvement_threshold: Decimal = Decimal("0.100000")
    recent_improvement_boost_per_record: Decimal = Decimal("0.100000")
    recent_window_days: Decimal = Decimal("7.000000")
    pass_memory_score_floor: Decimal = Decimal("0.650000")
    watch_memory_score_floor: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistForecastErrorMemoryRankConfig:
            raise TypeError(
                "TeamSpecialistForecastErrorMemoryRankConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistForecastErrorMemoryRankConfig:
            raise ValueError(
                "config must be exactly TeamSpecialistForecastErrorMemoryRankConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_FORECAST_ERROR_MEMORY_RANK_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "repeated_error_watch_threshold",
            "repeated_error_block_threshold",
            "repeated_error_penalty_per_record",
            "recent_improvement_threshold",
            "recent_improvement_boost_per_record",
            "pass_memory_score_floor",
            "watch_memory_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recent_window_days",
            _require_positive_decimal("recent_window_days", self.recent_window_days),
        )
        if self.repeated_error_watch_threshold > self.repeated_error_block_threshold:
            raise ValueError(
                "repeated_error_watch_threshold must not exceed "
                "repeated_error_block_threshold",
            )
        if self.watch_memory_score_floor > self.pass_memory_score_floor:
            raise ValueError(
                "watch_memory_score_floor must not exceed pass_memory_score_floor",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistForecastErrorMemoryRankRecord:
    team_id: str
    specialist_id: str
    market_id: str
    forecast_probability: Decimal
    resolved_probability: Decimal
    observed_at: datetime
    prior_absolute_error: Decimal | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistForecastErrorMemoryRankRecord:
            raise TypeError(
                "TeamSpecialistForecastErrorMemoryRankRecord does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistForecastErrorMemoryRankRecord:
            raise ValueError(
                "record must be exactly TeamSpecialistForecastErrorMemoryRankRecord",
            )
        for field_name in ("team_id", "specialist_id", "market_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "forecast_probability",
            _require_ratio_decimal("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "resolved_probability",
            _require_ratio_decimal("resolved_probability", self.resolved_probability),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.prior_absolute_error is not None:
            object.__setattr__(
                self,
                "prior_absolute_error",
                _require_ratio_decimal(
                    "prior_absolute_error",
                    self.prior_absolute_error,
                ),
            )
        _require_hard_flags("record", self)
        _reject_unsafe_public_payload("record", self)


@dataclass(frozen=True)
class TeamSpecialistForecastErrorMemoryPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistForecastErrorMemoryPublicPayloadItem:
            raise TypeError(
                "TeamSpecialistForecastErrorMemoryPublicPayloadItem does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistForecastErrorMemoryPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "TeamSpecialistForecastErrorMemoryPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class TeamSpecialistForecastErrorMemoryRankRow:
    team_id: str
    specialist_id: str
    rank: Decimal
    record_count: Decimal
    market_count: Decimal
    average_forecast_probability: Decimal
    average_resolved_probability: Decimal
    average_absolute_error: Decimal
    repeated_error_count: Decimal
    repeated_error_penalty: Decimal
    recent_improvement_count: Decimal
    recent_improvement_boost: Decimal
    memory_score: Decimal
    memory_status: str
    latest_observed_at: datetime
    market_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistForecastErrorMemoryRankRow:
            raise TypeError(
                "TeamSpecialistForecastErrorMemoryRankRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistForecastErrorMemoryRankRow:
            raise ValueError(
                "row must be exactly TeamSpecialistForecastErrorMemoryRankRow",
            )
        _require_public_identifier("team_id", self.team_id)
        _require_public_identifier("specialist_id", self.specialist_id)
        for field_name in (
            "rank",
            "record_count",
            "market_count",
            "repeated_error_count",
            "recent_improvement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_forecast_probability",
            "average_resolved_probability",
            "average_absolute_error",
            "repeated_error_penalty",
            "recent_improvement_boost",
            "memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_memory_status("memory_status", self.memory_status)
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "market_ids",
            _normalize_public_identifiers("market_ids", self.market_ids),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class TeamSpecialistForecastErrorMemoryRankReport:
    generated_at: datetime
    config_version: str
    memory_status: str
    specialist_count: Decimal
    record_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_memory_score: Decimal
    rows: tuple[TeamSpecialistForecastErrorMemoryRankRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[TeamSpecialistForecastErrorMemoryPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistForecastErrorMemoryRankReport:
            raise TypeError(
                "TeamSpecialistForecastErrorMemoryRankReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistForecastErrorMemoryRankReport:
            raise ValueError(
                "report must be exactly TeamSpecialistForecastErrorMemoryRankReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_FORECAST_ERROR_MEMORY_RANK_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_memory_status("memory_status", self.memory_status)
        for field_name in (
            "specialist_count",
            "record_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_memory_score",
            _require_ratio_decimal("average_memory_score", self.average_memory_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
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
            "TeamSpecialistForecastErrorMemoryRankReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_forecast_error_memory_rank_v2_report(
    records: Sequence[TeamSpecialistForecastErrorMemoryRankRecord],
    *,
    generated_at: datetime,
    config: TeamSpecialistForecastErrorMemoryRankConfig | None = None,
    public_payload: Sequence[TeamSpecialistForecastErrorMemoryPublicPayloadItem] = (),
) -> TeamSpecialistForecastErrorMemoryRankReport:
    """Build a local Phase 1 report-only specialist forecast-error memory rank."""

    if config is None:
        config = TeamSpecialistForecastErrorMemoryRankConfig()
    if type(config) is not TeamSpecialistForecastErrorMemoryRankConfig:
        raise ValueError(
            "config must be a TeamSpecialistForecastErrorMemoryRankConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_records = _normalize_records(records)
    for item in normalized_records:
        if item.observed_at > generated_at:
            raise ValueError("record observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows_without_rank = _build_rows(normalized_records, generated_at, config)
    rows = _rank_rows(rows_without_rank)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "memory_status": _report_status(rows),
        "specialist_count": _decimal_count(len(rows)),
        "record_count": _decimal_count(len(normalized_records)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "blocked_count": _decimal_count(_status_count(rows, "blocked")),
        "average_memory_score": _average(tuple(row.memory_score for row in rows)),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamSpecialistForecastErrorMemoryRankReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def team_specialist_forecast_error_memory_rank_v2_payload(
    report: TeamSpecialistForecastErrorMemoryRankReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistForecastErrorMemoryRankReport:
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
    raise ValueError(
        "report must be a TeamSpecialistForecastErrorMemoryRankReport or payload",
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


def _build_rows(
    records: tuple[TeamSpecialistForecastErrorMemoryRankRecord, ...],
    generated_at: datetime,
    config: TeamSpecialistForecastErrorMemoryRankConfig,
) -> tuple[TeamSpecialistForecastErrorMemoryRankRow, ...]:
    grouped: dict[tuple[str, str], list[TeamSpecialistForecastErrorMemoryRankRecord]] = {}
    for item in records:
        grouped.setdefault((item.team_id, item.specialist_id), []).append(item)
    rows = [
        _row_for_group(team_id, specialist_id, tuple(items), generated_at, config)
        for (team_id, specialist_id), items in sorted(grouped.items())
    ]
    return tuple(rows)


def _row_for_group(
    team_id: str,
    specialist_id: str,
    records: tuple[TeamSpecialistForecastErrorMemoryRankRecord, ...],
    generated_at: datetime,
    config: TeamSpecialistForecastErrorMemoryRankConfig,
) -> TeamSpecialistForecastErrorMemoryRankRow:
    absolute_errors = tuple(_absolute_error(item) for item in records)
    average_absolute_error = _average(absolute_errors)
    repeated_error_count = _repeated_error_count(average_absolute_error, records, config)
    repeated_error_penalty = _clamp_ratio(
        repeated_error_count * config.repeated_error_penalty_per_record,
    )
    recent_improvement_count = _recent_improvement_count(records, generated_at, config)
    recent_improvement_boost = _clamp_ratio(
        recent_improvement_count * config.recent_improvement_boost_per_record,
    )
    memory_score = _clamp_ratio(
        _ONE - average_absolute_error - repeated_error_penalty + recent_improvement_boost,
    )
    memory_status = _row_status(memory_score, config)
    reason_codes = _row_reason_codes(
        average_absolute_error=average_absolute_error,
        repeated_error_count=repeated_error_count,
        recent_improvement_count=recent_improvement_count,
        memory_status=memory_status,
        config=config,
    )
    return TeamSpecialistForecastErrorMemoryRankRow(
        team_id=team_id,
        specialist_id=specialist_id,
        rank=_ZERO,
        record_count=_decimal_count(len(records)),
        market_count=_decimal_count(len({item.market_id for item in records})),
        average_forecast_probability=_average(
            tuple(item.forecast_probability for item in records),
        ),
        average_resolved_probability=_average(
            tuple(item.resolved_probability for item in records),
        ),
        average_absolute_error=average_absolute_error,
        repeated_error_count=repeated_error_count,
        repeated_error_penalty=repeated_error_penalty,
        recent_improvement_count=recent_improvement_count,
        recent_improvement_boost=recent_improvement_boost,
        memory_score=memory_score,
        memory_status=memory_status,
        latest_observed_at=max(item.observed_at for item in records),
        market_ids=tuple(sorted({item.market_id for item in records})),
        reason_codes=reason_codes,
    )


def _rank_rows(
    rows: tuple[TeamSpecialistForecastErrorMemoryRankRow, ...],
) -> tuple[TeamSpecialistForecastErrorMemoryRankRow, ...]:
    ranked_rows = []
    for index, row in enumerate(
        sorted(
            rows,
            key=lambda item: (
                -item.memory_score,
                item.average_absolute_error,
                item.team_id,
                item.specialist_id,
            ),
        ),
        start=1,
    ):
        ranked_rows.append(
            TeamSpecialistForecastErrorMemoryRankRow(
                team_id=row.team_id,
                specialist_id=row.specialist_id,
                rank=_decimal_count(index),
                record_count=row.record_count,
                market_count=row.market_count,
                average_forecast_probability=row.average_forecast_probability,
                average_resolved_probability=row.average_resolved_probability,
                average_absolute_error=row.average_absolute_error,
                repeated_error_count=row.repeated_error_count,
                repeated_error_penalty=row.repeated_error_penalty,
                recent_improvement_count=row.recent_improvement_count,
                recent_improvement_boost=row.recent_improvement_boost,
                memory_score=row.memory_score,
                memory_status=row.memory_status,
                latest_observed_at=row.latest_observed_at,
                market_ids=row.market_ids,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked_rows)


def _absolute_error(record: TeamSpecialistForecastErrorMemoryRankRecord) -> Decimal:
    return _quantize(abs(record.forecast_probability - record.resolved_probability))


def _repeated_error_count(
    average_absolute_error: Decimal,
    records: tuple[TeamSpecialistForecastErrorMemoryRankRecord, ...],
    config: TeamSpecialistForecastErrorMemoryRankConfig,
) -> Decimal:
    if average_absolute_error >= config.repeated_error_block_threshold:
        return _decimal_count(len(records))
    if average_absolute_error >= config.repeated_error_watch_threshold:
        return _ONE
    return _ZERO


def _recent_improvement_count(
    records: tuple[TeamSpecialistForecastErrorMemoryRankRecord, ...],
    generated_at: datetime,
    config: TeamSpecialistForecastErrorMemoryRankConfig,
) -> Decimal:
    recent_count = 0
    recent_seconds = config.recent_window_days * Decimal("86400.000000")
    for item in records:
        if item.prior_absolute_error is None:
            continue
        age_seconds = Decimal(str((generated_at - item.observed_at).total_seconds()))
        if age_seconds < _ZERO or age_seconds > recent_seconds:
            continue
        if item.prior_absolute_error - _absolute_error(item) >= config.recent_improvement_threshold:
            recent_count += 1
    return _decimal_count(recent_count)


def _row_reason_codes(
    *,
    average_absolute_error: Decimal,
    repeated_error_count: Decimal,
    recent_improvement_count: Decimal,
    memory_status: str,
    config: TeamSpecialistForecastErrorMemoryRankConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if memory_status == "blocked":
        reason_codes.append("memory_rank_blocked")
    if average_absolute_error >= config.repeated_error_watch_threshold:
        reason_codes.append("recent_error_watch")
    if repeated_error_count > _ONE:
        reason_codes.append("repeated_error_penalty_applied")
    if recent_improvement_count > _ZERO:
        reason_codes.append("recent_improvement_boost_applied")
    if memory_status == "pass":
        reason_codes.append("memory_rank_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(
    memory_score: Decimal,
    config: TeamSpecialistForecastErrorMemoryRankConfig,
) -> str:
    if memory_score >= config.pass_memory_score_floor:
        return "pass"
    if memory_score >= config.watch_memory_score_floor:
        return "watch"
    return "blocked"


def _report_status(rows: tuple[TeamSpecialistForecastErrorMemoryRankRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.memory_status == "blocked" for row in rows):
        return "blocked"
    if any(row.memory_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[TeamSpecialistForecastErrorMemoryRankRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_memory_records",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[TeamSpecialistForecastErrorMemoryRankRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.memory_status == status)


def _validate_row_consistency(row: TeamSpecialistForecastErrorMemoryRankRow) -> None:
    if row.market_count > row.record_count:
        raise ValueError("market_count must not exceed record_count")
    if row.memory_status == "pass" and "memory_rank_pass" not in row.reason_codes:
        raise ValueError("pass rows must include memory_rank_pass")
    if row.memory_status == "blocked" and "memory_rank_blocked" not in row.reason_codes:
        raise ValueError("blocked rows must include memory_rank_blocked")


def _validate_report_consistency(
    report: TeamSpecialistForecastErrorMemoryRankReport,
) -> None:
    if report.specialist_count != _decimal_count(len(report.rows)):
        raise ValueError("specialist_count must match rows")
    if report.record_count != _sum_counts(row.record_count for row in report.rows):
        raise ValueError("record_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_memory_score != _average(tuple(row.memory_score for row in report.rows)):
        raise ValueError("average_memory_score must match rows")
    if report.memory_status != _report_status(report.rows):
        raise ValueError("memory_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_records(
    records: Sequence[TeamSpecialistForecastErrorMemoryRankRecord],
) -> tuple[TeamSpecialistForecastErrorMemoryRankRecord, ...]:
    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
        raise ValueError("records must be a sequence")
    normalized: list[TeamSpecialistForecastErrorMemoryRankRecord] = []
    seen_keys: set[tuple[str, str, str, datetime]] = set()
    for item in records:
        if type(item) is not TeamSpecialistForecastErrorMemoryRankRecord:
            raise ValueError(
                "records must contain TeamSpecialistForecastErrorMemoryRankRecord",
            )
        key = (item.team_id, item.specialist_id, item.market_id, item.observed_at)
        if key in seen_keys:
            raise ValueError("records must not contain duplicate specialist snapshots")
        seen_keys.add(key)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.team_id,
                item.specialist_id,
                item.observed_at,
                item.market_id,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[TeamSpecialistForecastErrorMemoryRankRow],
) -> tuple[TeamSpecialistForecastErrorMemoryRankRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[TeamSpecialistForecastErrorMemoryRankRow] = []
    for row in rows:
        if type(row) is not TeamSpecialistForecastErrorMemoryRankRow:
            raise ValueError(
                "rows must contain TeamSpecialistForecastErrorMemoryRankRow",
            )
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (row.rank, row.team_id, row.specialist_id),
        ),
    )


def _normalize_public_payload(
    public_payload: Sequence[TeamSpecialistForecastErrorMemoryPublicPayloadItem],
) -> tuple[TeamSpecialistForecastErrorMemoryPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[TeamSpecialistForecastErrorMemoryPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not TeamSpecialistForecastErrorMemoryPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "TeamSpecialistForecastErrorMemoryPublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_public_identifiers(
    field_name: str,
    values: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_public_identifier(field_name, value))
    return tuple(sorted(dict.fromkeys(normalized)))


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
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


def _require_memory_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _MEMORY_STATUSES:
        raise ValueError(f"{field_name} must be a known memory status")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
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


def _sum_counts(values: Sequence[Decimal]) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


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
    report: TeamSpecialistForecastErrorMemoryRankReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, float):
        raise ValueError("numeric payload values must not be float")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is datetime or value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError(f"{current_path} must not be a float")
    if type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not a supported public payload value")


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_FORECAST_ERROR_MEMORY_RANK_V2_CONFIG_VERSION",
    "TeamSpecialistForecastErrorMemoryPublicPayloadItem",
    "TeamSpecialistForecastErrorMemoryRankConfig",
    "TeamSpecialistForecastErrorMemoryRankRecord",
    "TeamSpecialistForecastErrorMemoryRankReport",
    "TeamSpecialistForecastErrorMemoryRankRow",
    "build_team_specialist_forecast_error_memory_rank_v2_report",
    "team_specialist_forecast_error_memory_rank_v2_payload",
)
