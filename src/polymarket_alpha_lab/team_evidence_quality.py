"""Pure quality diagnostics for team evidence rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, InvalidOperation, localcontext
from typing import Any

from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastEvidenceDbRow,
    team_forecast_evidence_from_db_row,
)
from polymarket_alpha_lab.team_forecast_packet import TeamForecastEvidencePacket


QUALITY_PASS = "evidence_quality_pass"
QUALITY_WATCH = "evidence_quality_watch"
QUALITY_BLOCKED = "evidence_quality_blocked"
STATUSES = frozenset((QUALITY_PASS, QUALITY_WATCH, QUALITY_BLOCKED))
STATUS_KEYS = ("total", "pass", "watch", "blocked")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
SOURCE_SCORE = Decimal("0.350000")
RECENCY_SCORE = Decimal("0.250000")
WEIGHT_SCORE = Decimal("0.250000")
TEXT_SCORE = Decimal("0.150000")
HARD_FLAGS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class TeamEvidenceQualityConfig:
    config_version: str = "team-evidence-quality-v0"
    stale_after_seconds: int = 86400
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("stale_after_seconds", self.stale_after_seconds)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TeamEvidenceQualityRow:
    forecast_id: str
    evidence_id: str
    team_id: str
    market_slug: str
    source_id: str
    evidence_generated_at: datetime
    data_timestamp: datetime | None
    quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "forecast_id",
            "evidence_id",
            "team_id",
            "market_slug",
            "source_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "evidence_generated_at",
            _as_utc("evidence_generated_at", self.evidence_generated_at),
        )
        if self.data_timestamp is not None:
            object.__setattr__(
                self,
                "data_timestamp",
                _as_utc("data_timestamp", self.data_timestamp),
            )
        object.__setattr__(
            self,
            "quality_score",
            _normalize_probability("quality_score", self.quality_score),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("quality row", self)


@dataclass(frozen=True)
class TeamEvidenceQualityReport:
    generated_at: datetime
    config_version: str
    status: str
    total_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    average_quality_score: Decimal
    rows: tuple[TeamEvidenceQualityRow, ...]
    counts_by_team_id: dict[str, dict[str, int]]
    counts_by_market_slug: dict[str, dict[str, int]]
    reason_code_counts: dict[str, int]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "total_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "average_quality_score",
            _normalize_probability("average_quality_score", self.average_quality_score),
        )
        object.__setattr__(
            self,
            "rows",
            _normalize_quality_rows(self.rows),
        )
        _validate_report_totals(self)
        object.__setattr__(
            self,
            "counts_by_team_id",
            _normalize_count_map("counts_by_team_id", self.counts_by_team_id),
        )
        object.__setattr__(
            self,
            "counts_by_market_slug",
            _normalize_count_map("counts_by_market_slug", self.counts_by_market_slug),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("quality report", self)


def build_team_evidence_quality_report(
    evidence_rows: list[TeamForecastEvidenceDbRow] | tuple[TeamForecastEvidenceDbRow, ...],
    *,
    config: TeamEvidenceQualityConfig,
    generated_at: datetime,
) -> TeamEvidenceQualityReport:
    if type(config) is not TeamEvidenceQualityConfig:
        raise ValueError("config must be a TeamEvidenceQualityConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    if type(evidence_rows) not in (list, tuple):
        raise ValueError("evidence_rows must be a list or tuple")

    quality_rows = tuple(
        _build_quality_row(row, config=config, generated_at=generated_at)
        for row in evidence_rows
    )
    pass_count = _status_total(quality_rows, QUALITY_PASS)
    watch_count = _status_total(quality_rows, QUALITY_WATCH)
    blocked_count = _status_total(quality_rows, QUALITY_BLOCKED)

    return TeamEvidenceQualityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(watch_count=watch_count, blocked_count=blocked_count),
        total_count=len(quality_rows),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        average_quality_score=_average_score(quality_rows),
        rows=quality_rows,
        counts_by_team_id=_counts_by_field(quality_rows, "team_id"),
        counts_by_market_slug=_counts_by_field(quality_rows, "market_slug"),
        reason_code_counts=_reason_code_counts(quality_rows),
    )


def _build_quality_row(
    row: object,
    *,
    config: TeamEvidenceQualityConfig,
    generated_at: datetime,
) -> TeamEvidenceQualityRow:
    if type(row) is not TeamForecastEvidenceDbRow:
        raise ValueError("evidence_rows must contain TeamForecastEvidenceDbRow values")
    _require_hard_flags("evidence row", row)
    _require_payload_hard_flags(row.payload_json)

    packet = _recover_packet(row)
    payload = row.payload_json if isinstance(row.payload_json, dict) else {}
    evidence_payload = _evidence_payload(payload)
    identity_missing = not all(
        _is_nonblank_string(getattr(row, field_name, None))
        for field_name in ("forecast_id", "evidence_id", "team_id", "market_slug")
    )

    if identity_missing:
        return TeamEvidenceQualityRow(
            forecast_id=_canonical_or_missing(row.forecast_id, "missing_forecast_id"),
            evidence_id=_canonical_or_missing(row.evidence_id, "missing_evidence_id"),
            team_id=_canonical_or_missing(row.team_id, "missing_team_id"),
            market_slug=_canonical_or_missing(row.market_slug, "missing_market_slug"),
            source_id=_source_id(row, packet, evidence_payload),
            evidence_generated_at=_safe_datetime(row.generated_at, generated_at),
            data_timestamp=_safe_optional_datetime(
                _first_present(
                    _packet_attr(packet, "data_timestamp"),
                    getattr(row, "data_timestamp", None),
                    evidence_payload.get("data_timestamp"),
                ),
            ),
            quality_score=ZERO,
            status=QUALITY_BLOCKED,
            reason_codes=("evidence_quality_missing_identity",),
        )

    source_present = _has_source_value(row, packet, payload, evidence_payload)
    fresh = _is_fresh(row.generated_at, generated_at, config.stale_after_seconds)
    future = _as_utc("evidence row generated_at", row.generated_at) > generated_at
    text_present = _has_reason_text(packet, evidence_payload)
    field_weight = _field_weight(row, packet, payload, evidence_payload)

    reason_codes: list[str] = []
    if not source_present:
        reason_codes.append("evidence_quality_missing_source_metadata")
    if future:
        reason_codes.append("evidence_quality_future_generated_at")
    elif not fresh:
        reason_codes.append("evidence_quality_stale")
    if not text_present:
        reason_codes.append("evidence_quality_missing_reason_text")
    if field_weight is None:
        reason_codes.append("evidence_quality_missing_weight")

    status = QUALITY_PASS if not reason_codes else QUALITY_WATCH
    score = _quality_score(
        source_present=source_present,
        fresh=fresh and not future,
        field_weight=field_weight,
        text_present=text_present,
    )

    return TeamEvidenceQualityRow(
        forecast_id=row.forecast_id,
        evidence_id=row.evidence_id,
        team_id=row.team_id,
        market_slug=row.market_slug,
        source_id=_source_id(row, packet, evidence_payload),
        evidence_generated_at=_as_utc("evidence row generated_at", row.generated_at),
        data_timestamp=_safe_optional_datetime(
            _first_present(
                _packet_attr(packet, "data_timestamp"),
                getattr(row, "data_timestamp", None),
                evidence_payload.get("data_timestamp"),
            ),
        ),
        quality_score=score,
        status=status,
        reason_codes=tuple(reason_codes or ("evidence_quality_complete",)),
    )


def _recover_packet(row: TeamForecastEvidenceDbRow) -> TeamForecastEvidencePacket | None:
    try:
        packet = team_forecast_evidence_from_db_row(row)
    except ValueError:
        return None
    if type(packet) is TeamForecastEvidencePacket:
        return packet
    return None


def _quality_score(
    *,
    source_present: bool,
    fresh: bool,
    field_weight: Decimal | None,
    text_present: bool,
) -> Decimal:
    score = ZERO
    if source_present:
        score += SOURCE_SCORE
    if fresh:
        score += RECENCY_SCORE
    if field_weight is not None:
        score += field_weight * WEIGHT_SCORE
    if text_present:
        score += TEXT_SCORE
    return _quantize_probability(score)


def _has_source_value(
    row: TeamForecastEvidenceDbRow,
    packet: TeamForecastEvidencePacket | None,
    payload: dict[str, Any],
    evidence_payload: dict[str, Any],
) -> bool:
    values = (
        getattr(row, "source_id", None),
        _packet_attr(packet, "source_id"),
        evidence_payload.get("source_id"),
        evidence_payload.get("source_url"),
        evidence_payload.get("source_title"),
        payload.get("source_id"),
        payload.get("source_url"),
        payload.get("source_title"),
    )
    if any(_is_nonblank_string(value) for value in values):
        return True
    return any(
        _contains_nonblank_string(value)
        for value in (
            evidence_payload.get("source_references"),
            evidence_payload.get("sources"),
            payload.get("source_references"),
            payload.get("sources"),
        )
    )


def _has_reason_text(
    packet: TeamForecastEvidencePacket | None,
    evidence_payload: dict[str, Any],
) -> bool:
    if _is_nonblank_string(_packet_attr(packet, "evidence_text")):
        return True
    for field_name in ("evidence_text", "reason", "rationale", "summary"):
        if _is_nonblank_string(evidence_payload.get(field_name)):
            return True
    return _contains_nonblank_string(evidence_payload.get("reason_codes"))


def _field_weight(
    row: TeamForecastEvidenceDbRow,
    packet: TeamForecastEvidencePacket | None,
    payload: dict[str, Any],
    evidence_payload: dict[str, Any],
) -> Decimal | None:
    for value in (
        _packet_attr(packet, "weight"),
        getattr(row, "weight", None),
        evidence_payload.get("weight"),
        evidence_payload.get("confidence"),
        payload.get("weight"),
        payload.get("confidence"),
    ):
        probability = _coerce_probability(value)
        if probability is not None:
            return probability
    return None


def _source_id(
    row: TeamForecastEvidenceDbRow,
    packet: TeamForecastEvidencePacket | None,
    evidence_payload: dict[str, Any],
) -> str:
    for value in (
        getattr(row, "source_id", None),
        _packet_attr(packet, "source_id"),
        evidence_payload.get("source_id"),
        evidence_payload.get("source_url"),
        evidence_payload.get("source_title"),
    ):
        if _is_nonblank_string(value):
            return value
    return "missing_source_metadata"


def _is_fresh(
    evidence_generated_at: datetime,
    report_generated_at: datetime,
    stale_after_seconds: int,
) -> bool:
    evidence_generated_at = _as_utc("evidence row generated_at", evidence_generated_at)
    if evidence_generated_at > report_generated_at:
        return False
    return evidence_generated_at + timedelta(seconds=stale_after_seconds) >= report_generated_at


def _counts_by_field(
    rows: tuple[TeamEvidenceQualityRow, ...],
    field_name: str,
) -> dict[str, dict[str, int]]:
    values: dict[str, dict[str, int]] = {}
    for row in rows:
        key = getattr(row, field_name)
        if key not in values:
            values[key] = _empty_status_counts()
        _increment_status_counts(values[key], row.status)
    return dict(sorted(values.items()))


def _reason_code_counts(rows: tuple[TeamEvidenceQualityRow, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return dict(sorted(counts.items()))


def _average_score(rows: tuple[TeamEvidenceQualityRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_probability(
            sum((row.quality_score for row in rows), ZERO) / Decimal(len(rows)),
        )


def _status_total(rows: tuple[TeamEvidenceQualityRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _report_status(*, watch_count: int, blocked_count: int) -> str:
    if blocked_count:
        return QUALITY_BLOCKED
    if watch_count:
        return QUALITY_WATCH
    return QUALITY_PASS


def _empty_status_counts() -> dict[str, int]:
    return {key: 0 for key in STATUS_KEYS}


def _increment_status_counts(counts: dict[str, int], status: str) -> None:
    counts["total"] += 1
    if status == QUALITY_PASS:
        counts["pass"] += 1
    elif status == QUALITY_WATCH:
        counts["watch"] += 1
    elif status == QUALITY_BLOCKED:
        counts["blocked"] += 1
    else:
        raise ValueError("status must be a known evidence quality status")


def _evidence_payload(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("evidence")
    if isinstance(value, dict):
        return value
    return {}


def _packet_attr(packet: TeamForecastEvidencePacket | None, field_name: str) -> object:
    if packet is None:
        return None
    return getattr(packet, field_name)


def _first_present(*values: object) -> object:
    for value in values:
        if value is not None:
            return value
    return None


def _safe_datetime(value: object, fallback: datetime) -> datetime:
    try:
        return _as_utc("datetime", value)
    except ValueError:
        return fallback


def _safe_optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    try:
        return _as_utc("datetime", value)
    except ValueError:
        if type(value) is str:
            try:
                return _as_utc("datetime", datetime.fromisoformat(value))
            except ValueError:
                return None
        return None


def _canonical_or_missing(value: object, fallback: str) -> str:
    if _is_nonblank_string(value):
        return value
    return fallback


def _contains_nonblank_string(value: object) -> bool:
    if _is_nonblank_string(value):
        return True
    if isinstance(value, (list, tuple)):
        return any(_contains_nonblank_string(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_nonblank_string(item) for item in value.values())
    return False


def _is_nonblank_string(value: object) -> bool:
    return type(value) is str and bool(value) and value.strip() == value


def _coerce_probability(value: object) -> Decimal | None:
    if type(value) is Decimal:
        probability = value
    elif type(value) is str:
        try:
            probability = Decimal(value)
        except InvalidOperation:
            return None
    elif type(value) is int:
        probability = Decimal(value)
    else:
        return None
    if not probability.is_finite() or probability < ZERO or probability > ONE:
        return None
    return _quantize_probability(probability)


def _normalize_quality_rows(value: object) -> tuple[TeamEvidenceQualityRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must contain TeamEvidenceQualityRow values")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain TeamEvidenceQualityRow values") from exc
    for row in rows:
        if type(row) is not TeamEvidenceQualityRow:
            raise ValueError("rows must contain TeamEvidenceQualityRow values")
    return rows


def _normalize_count_map(
    field_name: str,
    value: object,
) -> dict[str, dict[str, int]]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a count map")
    normalized: dict[str, dict[str, int]] = {}
    for key, counts in value.items():
        _require_canonical_string(field_name, key)
        if not isinstance(counts, dict):
            raise ValueError(f"{field_name} values must be count maps")
        normalized_counts = _empty_status_counts()
        for status_key in STATUS_KEYS:
            count_value = counts.get(status_key)
            _require_nonnegative_int(status_key, count_value)
            normalized_counts[status_key] = count_value
        normalized[key] = normalized_counts
    return dict(sorted(normalized.items()))


def _normalize_reason_code_counts(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        raise ValueError("reason_code_counts must be a count map")
    normalized: dict[str, int] = {}
    for reason_code, count in value.items():
        _require_canonical_string("reason_code", reason_code)
        _require_nonnegative_int("reason_code count", count)
        normalized[reason_code] = count
    return dict(sorted(normalized.items()))


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain canonical strings") from exc
    if not items:
        raise ValueError("reason_codes must contain canonical strings")
    for item in items:
        _require_canonical_string("reason_codes", item)
    return tuple(sorted(set(items)))


def _validate_report_totals(report: TeamEvidenceQualityReport) -> None:
    if report.total_count != len(report.rows):
        raise ValueError("total_count must equal rows length")
    if report.pass_count != _status_total(report.rows, QUALITY_PASS):
        raise ValueError("pass_count must equal rows")
    if report.watch_count != _status_total(report.rows, QUALITY_WATCH):
        raise ValueError("watch_count must equal rows")
    if report.blocked_count != _status_total(report.rows, QUALITY_BLOCKED):
        raise ValueError("blocked_count must equal rows")


def _require_payload_hard_flags(payload: object) -> None:
    if not isinstance(payload, dict):
        return
    for flag_name in HARD_FLAGS:
        if payload.get(flag_name) is not True:
            raise ValueError(f"payload_json {flag_name} must be True")
    evidence_payload = payload.get("evidence")
    if isinstance(evidence_payload, dict):
        for flag_name in HARD_FLAGS:
            if evidence_payload.get(flag_name) is not True:
                raise ValueError(f"payload_json evidence {flag_name} must be True")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in HARD_FLAGS:
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a known evidence quality status")


def _require_canonical_string(field_name: str, value: object) -> None:
    if not _is_nonblank_string(value):
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    probability = _coerce_probability(value)
    if probability is None:
        raise ValueError(f"{field_name} must be between zero and one")
    return probability


def _quantize_probability(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=UTC,
            fold=value.fold,
        )
    return value.astimezone(UTC)


__all__ = (
    "TeamEvidenceQualityConfig",
    "TeamEvidenceQualityReport",
    "TeamEvidenceQualityRow",
    "build_team_evidence_quality_report",
)
