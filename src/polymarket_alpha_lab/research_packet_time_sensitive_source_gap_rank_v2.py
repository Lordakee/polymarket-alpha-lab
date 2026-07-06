"""Phase 1 readonly source-gap ranking report."""

from __future__ import annotations

from dataclasses import asdict as _asdict
from dataclasses import dataclass as _dataclass
from dataclasses import fields as _fields
from dataclasses import is_dataclass as _is_dataclass
from datetime import UTC as _UTC
from datetime import datetime as _datetime
from decimal import Decimal as _Decimal
from decimal import ROUND_HALF_UP as _ROUND_HALF_UP
import hashlib as _hashlib
import json as _json
import re as _re
from typing import Sequence as _Sequence


DEFAULT_RESEARCH_PACKET_TIME_SENSITIVE_SOURCE_GAP_RANK_V2_CONFIG_VERSION = (
    "research-packet-time-sensitive-source-gap-rank-v2"
)

STATUSES = ("urgent", "watch", "blocked")

REASON_CODES = (
    "no_time_sensitive_source_gaps",
    "source_age_penalty",
    "official_source_gap",
    "urgent_official_source_boost",
    "high_time_sensitivity",
    "high_gap_severity",
    "time_sensitive_source_gap_urgent",
    "time_sensitive_source_gap_watch",
    "time_sensitive_source_gap_blocked",
)

_QUANT = _Decimal("0.000001")
_ZERO = _Decimal("0.000000")
_ONE = _Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = _re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_DIGEST_RE = _re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sign" + "ing",
    "muta" + "tion",
    "b" + "uy",
    "s" + "ell",
    "tra" + "de",
)


@_dataclass(frozen=True)
class ResearchPacketTimeSensitiveSourceGapRankV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_TIME_SENSITIVE_SOURCE_GAP_RANK_V2_CONFIG_VERSION
    )
    source_age_penalty_window_seconds: _Decimal = _Decimal("3600.000000")
    max_source_age_penalty: _Decimal = _Decimal("0.300000")
    urgent_window_seconds: _Decimal = _Decimal("900.000000")
    urgent_official_source_boost: _Decimal = _Decimal("0.250000")
    time_sensitivity_weight: _Decimal = _Decimal("0.400000")
    gap_severity_weight: _Decimal = _Decimal("0.350000")
    source_relevance_weight: _Decimal = _Decimal("0.250000")
    urgent_score_floor: _Decimal = _Decimal("0.800000")
    watch_score_floor: _Decimal = _Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketTimeSensitiveSourceGapRankV2Config:
            raise TypeError(
                "ResearchPacketTimeSensitiveSourceGapRankV2Config does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketTimeSensitiveSourceGapRankV2Config:
            raise ValueError(
                "config must be exactly "
                "ResearchPacketTimeSensitiveSourceGapRankV2Config",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_TIME_SENSITIVE_SOURCE_GAP_RANK_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "source_age_penalty_window_seconds",
            _require_positive_decimal(
                "source_age_penalty_window_seconds",
                self.source_age_penalty_window_seconds,
            ),
        )
        object.__setattr__(
            self,
            "urgent_window_seconds",
            _require_nonnegative_decimal(
                "urgent_window_seconds",
                self.urgent_window_seconds,
            ),
        )
        for field_name in (
            "max_source_age_penalty",
            "urgent_official_source_boost",
            "time_sensitivity_weight",
            "gap_severity_weight",
            "source_relevance_weight",
            "urgent_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config_weights(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@_dataclass(frozen=True)
class ResearchPacketTimeSensitiveSourceGapRankV2Input:
    packet_id: str
    gap_id: str
    question_ref: str
    source_ref: str
    source_observed_at: _datetime
    required_by_at: _datetime
    source_relevance_score: _Decimal
    gap_severity_score: _Decimal
    time_sensitivity_score: _Decimal
    official_source_required: bool = False
    official_source_observed: bool = False
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketTimeSensitiveSourceGapRankV2Input:
            raise TypeError(
                "ResearchPacketTimeSensitiveSourceGapRankV2Input does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketTimeSensitiveSourceGapRankV2Input:
            raise ValueError(
                "input row must be exactly "
                "ResearchPacketTimeSensitiveSourceGapRankV2Input",
            )
        for field_name in ("packet_id", "gap_id", "question_ref", "source_ref"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "required_by_at",
            _as_utc("required_by_at", self.required_by_at),
        )
        for field_name in (
            "source_relevance_score",
            "gap_severity_score",
            "time_sensitivity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("official_source_required", self.official_source_required)
        _require_bool("official_source_observed", self.official_source_observed)
        object.__setattr__(
            self,
            "public_note",
            _normalize_optional_public_text("public_note", self.public_note),
        )
        _require_hard_flags("input row", self)
        _reject_unsafe_public_payload("input row", self)


@_dataclass(frozen=True)
class ResearchPacketTimeSensitiveSourceGapRankV2Row:
    rank: _Decimal
    packet_id: str
    gap_id: str
    question_ref: str
    source_ref: str
    source_age_seconds: _Decimal
    seconds_until_required: _Decimal
    source_age_penalty: _Decimal
    urgent_official_source_boost: _Decimal
    time_sensitive_source_gap_score: _Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketTimeSensitiveSourceGapRankV2Row:
            raise TypeError(
                "ResearchPacketTimeSensitiveSourceGapRankV2Row does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketTimeSensitiveSourceGapRankV2Row:
            raise ValueError(
                "rank row must be exactly ResearchPacketTimeSensitiveSourceGapRankV2Row",
            )
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        for field_name in ("packet_id", "gap_id", "question_ref", "source_ref"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "seconds_until_required",
            _require_decimal("seconds_until_required", self.seconds_until_required),
        )
        for field_name in (
            "source_age_penalty",
            "urgent_official_source_boost",
            "time_sensitive_source_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_reason_codes(self)
        _require_hard_flags("rank row", self)
        _reject_unsafe_public_payload("rank row", self)


@_dataclass(frozen=True)
class ResearchPacketTimeSensitiveSourceGapRankV2Report:
    generated_at: _datetime
    config_version: str
    input_count: _Decimal
    row_count: _Decimal
    urgent_count: _Decimal
    watch_count: _Decimal
    blocked_count: _Decimal
    average_time_sensitive_source_gap_score: _Decimal
    top_time_sensitive_source_gap_score: _Decimal
    rows: tuple[ResearchPacketTimeSensitiveSourceGapRankV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketTimeSensitiveSourceGapRankV2Report:
            raise TypeError(
                "ResearchPacketTimeSensitiveSourceGapRankV2Report does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketTimeSensitiveSourceGapRankV2Report:
            raise ValueError(
                "report must be exactly "
                "ResearchPacketTimeSensitiveSourceGapRankV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_TIME_SENSITIVE_SOURCE_GAP_RANK_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "urgent_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_time_sensitive_source_gap_score",
            "top_time_sensitive_source_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(_asdict(self))
        _require_payload_hard_flags(payload)
        _reject_unsafe_public_payload(
            "ResearchPacketTimeSensitiveSourceGapRankV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_packet_time_sensitive_source_gap_rank_v2_report(
    rows: _Sequence[ResearchPacketTimeSensitiveSourceGapRankV2Input],
    *,
    generated_at: _datetime,
    config: ResearchPacketTimeSensitiveSourceGapRankV2Config | None = None,
) -> ResearchPacketTimeSensitiveSourceGapRankV2Report:
    """Build a local Phase 1 time-sensitive source gap ranking report."""

    if config is None:
        config = ResearchPacketTimeSensitiveSourceGapRankV2Config()
    if type(config) is not ResearchPacketTimeSensitiveSourceGapRankV2Config:
        raise ValueError(
            "config must be a ResearchPacketTimeSensitiveSourceGapRankV2Config",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(rows)
    for row in normalized_rows:
        if row.source_observed_at > generated_at:
            raise ValueError("source_observed_at must not be after generated_at")
    ranked_rows = _ranked_rows(normalized_rows, generated_at, config)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "input_count": _decimal_count(len(normalized_rows)),
        "row_count": _decimal_count(len(ranked_rows)),
        "urgent_count": _status_count(ranked_rows, "urgent"),
        "watch_count": _status_count(ranked_rows, "watch"),
        "blocked_count": _status_count(ranked_rows, "blocked"),
        "average_time_sensitive_source_gap_score": _average_score(ranked_rows),
        "top_time_sensitive_source_gap_score": _top_score(ranked_rows),
        "rows": ranked_rows,
        "reason_codes": _report_reason_codes(ranked_rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return ResearchPacketTimeSensitiveSourceGapRankV2Report(**values)


def research_packet_time_sensitive_source_gap_rank_v2_payload(
    value: object,
) -> dict[str, object]:
    if type(value) is ResearchPacketTimeSensitiveSourceGapRankV2Report:
        return value.payload
    if type(value) is not dict:
        raise ValueError("payload source must be a report or dict")
    _require_payload_hard_flags(value)
    _reject_unsafe_public_payload(
        "research_packet_time_sensitive_source_gap_rank_v2_payload",
        value,
    )
    digest = value.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(value):
        raise ValueError("derived_validation_digest must match payload fields")
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _ranked_rows(
    rows: tuple[ResearchPacketTimeSensitiveSourceGapRankV2Input, ...],
    generated_at: _datetime,
    config: ResearchPacketTimeSensitiveSourceGapRankV2Config,
) -> tuple[ResearchPacketTimeSensitiveSourceGapRankV2Row, ...]:
    row_values = tuple(_row_values(row, generated_at, config) for row in rows)
    ranked_values = tuple(
        sorted(
            row_values,
            key=lambda item: (
                -item["time_sensitive_source_gap_score"],
                item["seconds_until_required"],
                -item["source_age_seconds"],
                item["packet_id"],
                item["gap_id"],
                item["source_ref"],
            ),
        ),
    )
    return tuple(
        ResearchPacketTimeSensitiveSourceGapRankV2Row(
            rank=_decimal_count(rank),
            **values,
        )
        for rank, values in enumerate(ranked_values, start=1)
    )


def _row_values(
    row: ResearchPacketTimeSensitiveSourceGapRankV2Input,
    generated_at: _datetime,
    config: ResearchPacketTimeSensitiveSourceGapRankV2Config,
) -> dict[str, object]:
    source_age_seconds = _decimal_seconds(generated_at - row.source_observed_at)
    seconds_until_required = _decimal_seconds(row.required_by_at - generated_at)
    source_age_penalty = _source_age_penalty(source_age_seconds, config)
    urgent_boost = _urgent_official_source_boost(row, seconds_until_required, config)
    score = _clamp_ratio(
        (row.time_sensitivity_score * config.time_sensitivity_weight)
        + (row.gap_severity_score * config.gap_severity_weight)
        + (row.source_relevance_score * config.source_relevance_weight)
        + source_age_penalty
        + urgent_boost,
    )
    status = _status_for_score(score, config)
    return {
        "packet_id": row.packet_id,
        "gap_id": row.gap_id,
        "question_ref": row.question_ref,
        "source_ref": row.source_ref,
        "source_age_seconds": source_age_seconds,
        "seconds_until_required": seconds_until_required,
        "source_age_penalty": source_age_penalty,
        "urgent_official_source_boost": urgent_boost,
        "time_sensitive_source_gap_score": score,
        "status": status,
        "reason_codes": _row_reason_codes(
            row,
            source_age_penalty=source_age_penalty,
            urgent_boost=urgent_boost,
            status=status,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _source_age_penalty(
    source_age_seconds: _Decimal,
    config: ResearchPacketTimeSensitiveSourceGapRankV2Config,
) -> _Decimal:
    if source_age_seconds <= _ZERO:
        return _ZERO
    ratio = source_age_seconds / config.source_age_penalty_window_seconds
    return min(_clamp_ratio(ratio * config.max_source_age_penalty), config.max_source_age_penalty)


def _urgent_official_source_boost(
    row: ResearchPacketTimeSensitiveSourceGapRankV2Input,
    seconds_until_required: _Decimal,
    config: ResearchPacketTimeSensitiveSourceGapRankV2Config,
) -> _Decimal:
    if (
        row.official_source_required
        and not row.official_source_observed
        and seconds_until_required <= config.urgent_window_seconds
    ):
        return config.urgent_official_source_boost
    return _ZERO


def _row_reason_codes(
    row: ResearchPacketTimeSensitiveSourceGapRankV2Input,
    *,
    source_age_penalty: _Decimal,
    urgent_boost: _Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_age_penalty > _ZERO:
        reason_codes.append("source_age_penalty")
    if row.official_source_required and not row.official_source_observed:
        reason_codes.append("official_source_gap")
    if urgent_boost > _ZERO:
        reason_codes.append("urgent_official_source_boost")
    if row.time_sensitivity_score >= _Decimal("0.750000"):
        reason_codes.append("high_time_sensitivity")
    if row.gap_severity_score >= _Decimal("0.750000"):
        reason_codes.append("high_gap_severity")
    reason_codes.append(f"time_sensitive_source_gap_{status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _status_for_score(
    score: _Decimal,
    config: ResearchPacketTimeSensitiveSourceGapRankV2Config,
) -> str:
    if score >= config.urgent_score_floor:
        return "urgent"
    if score >= config.watch_score_floor:
        return "watch"
    return "blocked"


def _normalize_input_rows(
    value: object,
) -> tuple[ResearchPacketTimeSensitiveSourceGapRankV2Input, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("rows must be an iterable")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchPacketTimeSensitiveSourceGapRankV2Input:
            raise ValueError(
                "rows must contain ResearchPacketTimeSensitiveSourceGapRankV2Input",
            )
        _require_hard_flags("input row", row)
    keys = tuple((row.packet_id, row.gap_id) for row in rows)
    if len(set(keys)) != len(keys):
        raise ValueError("rows must not contain duplicate packet gap keys")
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchPacketTimeSensitiveSourceGapRankV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchPacketTimeSensitiveSourceGapRankV2Row:
            raise ValueError(
                "rows must contain ResearchPacketTimeSensitiveSourceGapRankV2Row",
            )
        _require_hard_flags("rank row", row)
    return value


def _validate_config_weights(
    config: ResearchPacketTimeSensitiveSourceGapRankV2Config,
) -> None:
    if (
        config.time_sensitivity_weight
        + config.gap_severity_weight
        + config.source_relevance_weight
    ) != _ONE:
        raise ValueError("score weights must sum to 1.000000")
    if config.watch_score_floor > config.urgent_score_floor:
        raise ValueError("watch_score_floor must not exceed urgent_score_floor")


def _validate_row_reason_codes(
    row: ResearchPacketTimeSensitiveSourceGapRankV2Row,
) -> None:
    status_code = f"time_sensitive_source_gap_{row.status}"
    if status_code not in row.reason_codes:
        raise ValueError("reason_codes must include the status reason")
    if row.source_age_penalty > _ZERO and "source_age_penalty" not in row.reason_codes:
        raise ValueError("reason_codes must include source_age_penalty")
    if (
        row.urgent_official_source_boost > _ZERO
        and "urgent_official_source_boost" not in row.reason_codes
    ):
        raise ValueError("reason_codes must include urgent_official_source_boost")


def _validate_report_consistency(
    report: ResearchPacketTimeSensitiveSourceGapRankV2Report,
) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.input_count < report.row_count:
        raise ValueError("input_count must be greater than or equal to row_count")
    if (
        report.urgent_count != _status_count(rows, "urgent")
        or report.watch_count != _status_count(rows, "watch")
        or report.blocked_count != _status_count(rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    if report.urgent_count + report.watch_count + report.blocked_count != report.row_count:
        raise ValueError("status counts must sum to row_count")
    _validate_rows_ranked(rows)
    if report.average_time_sensitive_source_gap_score != _average_score(rows):
        raise ValueError("average_time_sensitive_source_gap_score must match rows")
    if report.top_time_sensitive_source_gap_score != _top_score(rows):
        raise ValueError("top_time_sensitive_source_gap_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.derived_validation_digest != _derived_validation_digest(_asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_rows_ranked(
    rows: tuple[ResearchPacketTimeSensitiveSourceGapRankV2Row, ...],
) -> None:
    expected_ranks = tuple(_decimal_count(rank) for rank in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("row ranks must be contiguous")
    expected_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.time_sensitive_source_gap_score,
                row.seconds_until_required,
                -row.source_age_seconds,
                row.packet_id,
                row.gap_id,
                row.source_ref,
            ),
        ),
    )
    if rows != expected_rows:
        raise ValueError("rows must be ranked by time-sensitive source gap score")


def _report_reason_codes(
    rows: tuple[ResearchPacketTimeSensitiveSourceGapRankV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_time_sensitive_source_gaps",)
    selected: set[str] = set()
    for row in rows:
        selected.update(row.reason_codes)
    return _normalize_reason_codes(tuple(code for code in REASON_CODES if code in selected))


def _status_count(
    rows: tuple[ResearchPacketTimeSensitiveSourceGapRankV2Row, ...],
    status: str,
) -> _Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _average_score(
    rows: tuple[ResearchPacketTimeSensitiveSourceGapRankV2Row, ...],
) -> _Decimal:
    if not rows:
        return _ZERO
    return _clamp_ratio(
        sum((row.time_sensitive_source_gap_score for row in rows), _ZERO)
        / _decimal_count(len(rows)),
    )


def _top_score(
    rows: tuple[ResearchPacketTimeSensitiveSourceGapRankV2Row, ...],
) -> _Decimal:
    return max((row.time_sensitive_source_gap_score for row in rows), default=_ZERO)


def _decimal_seconds(value: object) -> _Decimal:
    total_seconds = getattr(value, "total_seconds", None)
    if not callable(total_seconds):
        raise ValueError("time delta must expose total_seconds")
    return _quantize(_Decimal(str(total_seconds())))


def _decimal_count(value: int) -> _Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _Decimal(value).quantize(_QUANT)


def _clamp_ratio(value: _Decimal) -> _Decimal:
    value = _quantize(value)
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return value


def _require_ratio_decimal(field_name: str, value: object) -> _Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return value


def _require_positive_decimal(field_name: str, value: object) -> _Decimal:
    value = _require_decimal(field_name, value)
    if value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> _Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_decimal(field_name: str, value: object) -> _Decimal:
    if type(value) is not _Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return _quantize(value)


def _quantize(value: _Decimal) -> _Decimal:
    return value.quantize(_QUANT, rounding=_ROUND_HALF_UP)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for item in value:
        if type(item) is not str:
            raise ValueError("reason_codes must contain strings")
        if item not in REASON_CODES:
            raise ValueError(f"reason_codes has unsupported value: {item}")
        if item in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(item)
    return tuple(item for item in REASON_CODES if item in seen)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical public identifier")
    _reject_unsafe_public_payload(field_name, value)


def _normalize_optional_public_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_text(field_name, value)


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be canonical public text")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _as_utc(field_name: str, value: object) -> _datetime:
    if type(value) is not _datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(_UTC)


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in _PHASE_FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _require_payload_hard_flags(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_flags_at("payload", value, require_current=True)


def _require_payload_flags_at(
    field_name: str,
    value: object,
    *,
    require_current: bool = False,
) -> None:
    if isinstance(value, dict):
        if require_current or any(flag_name in value for flag_name in _PHASE_FLAG_FIELDS):
            for flag_name in _PHASE_FLAG_FIELDS:
                if value.get(flag_name) is not True:
                    raise ValueError(f"{field_name} {flag_name} must be present and true")
        for key, item in value.items():
            _require_payload_flags_at(f"{field_name}.{key}", item)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _require_payload_flags_at(f"{field_name}.{index}", item)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(value: object) -> str:
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("digest source must serialize to a dict")
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    encoded = _json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _hashlib.sha256(encoded).hexdigest()


def _payload_value(value: object) -> object:
    if _is_dataclass(value) and not isinstance(value, type):
        return _payload_value(_asdict(value))
    if type(value) is _Decimal:
        return _format_decimal(value)
    if type(value) is _datetime:
        return _format_datetime(value)
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"payload has unsupported value: {type(value).__name__}")


def _format_decimal(value: _Decimal) -> str:
    value = _require_decimal("payload decimal", value)
    return format(value, "f")


def _format_datetime(value: _datetime) -> str:
    value = _as_utc("payload datetime", value)
    if value.tzinfo is not _UTC:
        raise ValueError("payload datetimes must be UTC")
    return value.isoformat()


def _reject_unsafe_public_payload(
    field_name: str,
    value: object,
) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{field_name} public payload keys must be strings")
            _reject_unsafe_public_text(f"{field_name}.{key}", key)
            _reject_unsafe_public_payload(f"{field_name}.{key}", item)
    elif _is_dataclass(value) and not isinstance(value, type):
        for item_field in _fields(value):
            _reject_unsafe_public_text(
                f"{field_name}.{item_field.name}",
                item_field.name,
            )
            _reject_unsafe_public_payload(
                f"{field_name}.{item_field.name}",
                getattr(value, item_field.name),
            )
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{field_name}.{index}", item)
    elif type(value) is str:
        _reject_unsafe_public_text(field_name, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    compact = _re.sub(r"[^a-z0-9]+", "", lowered)
    for term in _UNSAFE_PUBLIC_TERMS:
        if term in lowered or term in compact:
            raise ValueError(f"{field_name} contains unsafe public payload")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_TIME_SENSITIVE_SOURCE_GAP_RANK_V2_CONFIG_VERSION",
    "REASON_CODES",
    "ResearchPacketTimeSensitiveSourceGapRankV2Config",
    "ResearchPacketTimeSensitiveSourceGapRankV2Input",
    "ResearchPacketTimeSensitiveSourceGapRankV2Report",
    "ResearchPacketTimeSensitiveSourceGapRankV2Row",
    "STATUSES",
    "build_research_packet_time_sensitive_source_gap_rank_v2_report",
    "research_packet_time_sensitive_source_gap_rank_v2_payload",
)
