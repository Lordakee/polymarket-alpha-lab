"""Phase 1 read-only team/domain source latency penalty digest."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_TEAM_SPECIALIST_SOURCE_LATENCY_PENALTY_DIGEST_V2_CONFIG_VERSION = (
    "team-specialist-source-latency-penalty-digest-v2"
)
ROW_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("empty", "pass", "watch", "block")

_COUNT_QUANTUM = Decimal("1")
_SIX_PLACE_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_SCORE = Decimal("0.000000")
_ONE_SCORE = Decimal("1.000000")
_TWO = Decimal("2")
_HIGH_LATENCY_SCORE = Decimal("0.500000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_DIGEST_FIELD = "derived_validation_digest"
_UNSAFE_PUBLIC_TERMS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "or" "der",
    "net" "work",
    "data" "base",
    "per" "sist",
    "sig" "ning",
    "mu" "tation",
    "b" "uy",
    "se" "ll",
    "tra" "de",
    "tra" "ding",
)
_REASON_SEQUENCE = (
    "latency_penalty_digest_empty",
    "median_latency_watch",
    "median_latency_block",
    "p95_latency_watch",
    "p95_latency_block",
    "latency_penalty_high",
    "stale_source_ratio_watch",
    "stale_source_ratio_block",
    "refresh_age_watch",
    "refresh_age_block",
    "latency_penalty_pass",
)


@dataclass(frozen=True)
class TeamSpecialistSourceLatencyPenaltyDigestV2Config:
    config_version: str = DEFAULT_TEAM_SPECIALIST_SOURCE_LATENCY_PENALTY_DIGEST_V2_CONFIG_VERSION
    median_watch_latency_seconds: Decimal = Decimal("900.000000")
    median_block_latency_seconds: Decimal = Decimal("1800.000000")
    p95_watch_latency_seconds: Decimal = Decimal("1800.000000")
    p95_block_latency_seconds: Decimal = Decimal("3600.000000")
    stale_source_watch_ratio: Decimal = Decimal("0.200000")
    stale_source_block_ratio: Decimal = Decimal("0.500000")
    refresh_watch_age_seconds: Decimal = Decimal("1200.000000")
    refresh_block_age_seconds: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, TeamSpecialistSourceLatencyPenaltyDigestV2Config)
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_SOURCE_LATENCY_PENALTY_DIGEST_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "median_watch_latency_seconds",
            "median_block_latency_seconds",
            "p95_watch_latency_seconds",
            "p95_block_latency_seconds",
            "refresh_watch_age_seconds",
            "refresh_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_six_place_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("stale_source_watch_ratio", "stale_source_block_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_score(field_name, getattr(self, field_name)),
            )
        if self.median_block_latency_seconds < self.median_watch_latency_seconds:
            raise ValueError(
                "median_block_latency_seconds must be at least median_watch_latency_seconds",
            )
        if self.p95_block_latency_seconds < self.p95_watch_latency_seconds:
            raise ValueError("p95_block_latency_seconds must be at least p95_watch_latency_seconds")
        if self.stale_source_block_ratio < self.stale_source_watch_ratio:
            raise ValueError("stale_source_block_ratio must be at least stale_source_watch_ratio")
        if self.refresh_block_age_seconds < self.refresh_watch_age_seconds:
            raise ValueError("refresh_block_age_seconds must be at least refresh_watch_age_seconds")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class TeamSpecialistSourceLatencyPenaltyInputV2:
    team_id: str
    domain: str
    median_source_latency_seconds: Decimal
    p95_source_latency_seconds: Decimal
    stale_source_count: Decimal
    source_count: Decimal
    latest_refresh_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("input", self, TeamSpecialistSourceLatencyPenaltyInputV2)
        for field_name in ("team_id", "domain"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("median_source_latency_seconds", "p95_source_latency_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_six_place_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "stale_source_count",
            _normalize_nonnegative_count("stale_source_count", self.stale_source_count),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_positive_count("source_count", self.source_count),
        )
        if self.stale_source_count > self.source_count:
            raise ValueError("source_count must be at least stale_source_count")
        object.__setattr__(
            self,
            "latest_refresh_at",
            _as_utc("latest_refresh_at", self.latest_refresh_at),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", _payload_value(self))


@dataclass(frozen=True)
class TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason code count",
            self,
            TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2,
        )
        _require_member("reason_code", self.reason_code, _REASON_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", _payload_value(self))


@dataclass(frozen=True)
class TeamSpecialistSourceLatencyPenaltyRowV2:
    team_id: str
    domain: str
    median_source_latency_seconds: Decimal
    p95_source_latency_seconds: Decimal
    stale_source_count: Decimal
    source_count: Decimal
    latest_refresh_at: datetime
    latency_penalty_score: Decimal
    stale_source_ratio: Decimal
    refresh_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, TeamSpecialistSourceLatencyPenaltyRowV2)
        for field_name in ("team_id", "domain"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("median_source_latency_seconds", "p95_source_latency_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_six_place_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("stale_source_count", "source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.source_count <= _ZERO_COUNT:
            raise ValueError("source_count must be positive")
        if self.stale_source_count > self.source_count:
            raise ValueError("stale_source_count must not exceed source_count")
        object.__setattr__(
            self,
            "latest_refresh_at",
            _as_utc("latest_refresh_at", self.latest_refresh_at),
        )
        for field_name in (
            "latency_penalty_score",
            "stale_source_ratio",
            "refresh_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_six_place_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.latency_penalty_score > _ONE_SCORE:
            raise ValueError("latency_penalty_score must be at most one")
        if self.stale_source_ratio > _ONE_SCORE:
            raise ValueError("stale_source_ratio must be at most one")
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_metrics(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match row fields")


@dataclass(frozen=True)
class TeamSpecialistSourceLatencyPenaltyReportV2:
    generated_at: datetime
    config_version: str
    report_status: str
    team_domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    high_latency_count: Decimal
    stale_source_count: Decimal
    stale_refresh_count: Decimal
    max_latency_penalty_score: Decimal
    rows: tuple[TeamSpecialistSourceLatencyPenaltyRowV2, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, TeamSpecialistSourceLatencyPenaltyReportV2)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        for field_name in (
            "team_domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "high_latency_count",
            "stale_source_count",
            "stale_refresh_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_latency_penalty_score",
            _normalize_unit_score(
                "max_latency_penalty_score",
                self.max_latency_penalty_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_metrics(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")


def build_team_specialist_source_latency_penalty_digest_v2(
    inputs: object,
    *,
    config: TeamSpecialistSourceLatencyPenaltyDigestV2Config,
    generated_at: datetime,
) -> TeamSpecialistSourceLatencyPenaltyReportV2:
    if type(config) is not TeamSpecialistSourceLatencyPenaltyDigestV2Config:
        raise ValueError("config must be a TeamSpecialistSourceLatencyPenaltyDigestV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in normalized_inputs
            ),
            key=lambda row: (row.team_id, row.domain),
        ),
    )
    pass_count = _count(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count(sum(1 for row in rows if row.status == "watch"))
    block_count = _count(sum(1 for row in rows if row.status == "block"))
    high_latency_count = _count(
        sum(1 for row in rows if "latency_penalty_high" in row.reason_codes),
    )
    stale_source_count = _count(
        sum(
            1
            for row in rows
            if (
                "stale_source_ratio_watch" in row.reason_codes
                or "stale_source_ratio_block" in row.reason_codes
            )
        ),
    )
    stale_refresh_count = _count(
        sum(
            1
            for row in rows
            if (
                "refresh_age_watch" in row.reason_codes
                or "refresh_age_block" in row.reason_codes
            )
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return TeamSpecialistSourceLatencyPenaltyReportV2(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        team_domain_count=_count(len(rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        high_latency_count=high_latency_count,
        stale_source_count=stale_source_count,
        stale_refresh_count=stale_refresh_count,
        max_latency_penalty_score=_max_latency_penalty_score(rows),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
    )


def team_specialist_source_latency_penalty_digest_v2_payload(
    report: object,
) -> dict[str, Any]:
    if type(report) is TeamSpecialistSourceLatencyPenaltyReportV2:
        _validate_report_digest(report)
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is dict:
        _reject_non_string_numeric(report)
        _reject_unsafe_public_payload("payload", report)
        _require_payload_hard_flags(report)
        if _DIGEST_FIELD in report:
            _validate_payload_digest(report)
        return report
    raise ValueError("report must be a latency penalty report or payload dict")


def _row_from_input(
    item: TeamSpecialistSourceLatencyPenaltyInputV2,
    *,
    config: TeamSpecialistSourceLatencyPenaltyDigestV2Config,
    generated_at: datetime,
) -> TeamSpecialistSourceLatencyPenaltyRowV2:
    stale_source_ratio = _six(_ratio(item.stale_source_count, item.source_count))
    refresh_age_seconds = _refresh_age_seconds(item, generated_at)
    latency_penalty_score = _latency_penalty_score(item, config)
    reason_codes = _row_reason_codes(
        item,
        config=config,
        latency_penalty_score=latency_penalty_score,
        stale_source_ratio=stale_source_ratio,
        refresh_age_seconds=refresh_age_seconds,
    )
    return TeamSpecialistSourceLatencyPenaltyRowV2(
        team_id=item.team_id,
        domain=item.domain,
        median_source_latency_seconds=item.median_source_latency_seconds,
        p95_source_latency_seconds=item.p95_source_latency_seconds,
        stale_source_count=item.stale_source_count,
        source_count=item.source_count,
        latest_refresh_at=item.latest_refresh_at,
        latency_penalty_score=latency_penalty_score,
        stale_source_ratio=stale_source_ratio,
        refresh_age_seconds=refresh_age_seconds,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _latency_penalty_score(
    item: TeamSpecialistSourceLatencyPenaltyInputV2,
    config: TeamSpecialistSourceLatencyPenaltyDigestV2Config,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        median_score = _capped_ratio(
            item.median_source_latency_seconds,
            config.median_block_latency_seconds,
        )
        p95_score = _capped_ratio(
            item.p95_source_latency_seconds,
            config.p95_block_latency_seconds,
        )
        return _six((median_score + p95_score) / _TWO)


def _row_reason_codes(
    item: TeamSpecialistSourceLatencyPenaltyInputV2,
    *,
    config: TeamSpecialistSourceLatencyPenaltyDigestV2Config,
    latency_penalty_score: Decimal,
    stale_source_ratio: Decimal,
    refresh_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.median_source_latency_seconds >= config.median_block_latency_seconds:
        reason_codes.append("median_latency_block")
    elif item.median_source_latency_seconds >= config.median_watch_latency_seconds:
        reason_codes.append("median_latency_watch")
    if item.p95_source_latency_seconds >= config.p95_block_latency_seconds:
        reason_codes.append("p95_latency_block")
    elif item.p95_source_latency_seconds >= config.p95_watch_latency_seconds:
        reason_codes.append("p95_latency_watch")
    if latency_penalty_score >= _HIGH_LATENCY_SCORE:
        reason_codes.append("latency_penalty_high")
    if stale_source_ratio >= config.stale_source_block_ratio:
        reason_codes.append("stale_source_ratio_block")
    elif stale_source_ratio >= config.stale_source_watch_ratio:
        reason_codes.append("stale_source_ratio_watch")
    if refresh_age_seconds >= config.refresh_block_age_seconds:
        reason_codes.append("refresh_age_block")
    elif refresh_age_seconds >= config.refresh_watch_age_seconds:
        reason_codes.append("refresh_age_watch")
    if not reason_codes:
        reason_codes.append("latency_penalty_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes == ("latency_penalty_pass",):
        return "pass"
    return "watch"


def _report_status(rows: tuple[TeamSpecialistSourceLatencyPenaltyRowV2, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[TeamSpecialistSourceLatencyPenaltyRowV2, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("latency_penalty_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in (
                "latency_penalty_pass",
                "median_latency_watch",
                "median_latency_block",
                "p95_latency_watch",
                "p95_latency_block",
            ):
                reason_codes.append(reason_code)
    if not reason_codes:
        return ("latency_penalty_pass",)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[TeamSpecialistSourceLatencyPenaltyRowV2, ...],
    reason_codes: tuple[str, ...],
) -> tuple[TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2, ...]:
    if not rows:
        return tuple(
            TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2(
                reason_code=reason_code,
                count=_count(1),
            )
            for reason_code in reason_codes
        )
    return tuple(
        TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2(
            reason_code=reason_code,
            count=_count(sum(1 for row in rows if reason_code in row.reason_codes)),
        )
        for reason_code in reason_codes
    )


def _max_latency_penalty_score(
    rows: tuple[TeamSpecialistSourceLatencyPenaltyRowV2, ...],
) -> Decimal:
    if not rows:
        return _ZERO_SCORE
    return max(row.latency_penalty_score for row in rows)


def _normalize_inputs(
    value: object,
    generated_at: datetime,
) -> tuple[TeamSpecialistSourceLatencyPenaltyInputV2, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    items = tuple(value)
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not TeamSpecialistSourceLatencyPenaltyInputV2:
            raise ValueError("inputs must contain exact latency penalty inputs")
        _require_hard_flags("input", item)
        if item.latest_refresh_at > generated_at:
            raise ValueError("latest_refresh_at must not be in the future")
        key = (item.team_id, item.domain)
        if key in seen:
            raise ValueError("inputs must not repeat team/domain")
        seen.add(key)
    return tuple(sorted(items, key=lambda item: (item.team_id, item.domain)))


def _normalize_rows(value: object) -> tuple[TeamSpecialistSourceLatencyPenaltyRowV2, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not TeamSpecialistSourceLatencyPenaltyRowV2:
            raise ValueError("rows must contain exact latency penalty rows")
        _require_hard_flags("row", row)
        key = (row.team_id, row.domain)
        if key in seen:
            raise ValueError("rows must not repeat team/domain")
        seen.add(key)
        _validate_row_digest(row)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.team_id, row.domain)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by team_id and domain")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2:
            raise ValueError("reason_code_counts must contain exact reason code counts")
        _require_hard_flags("reason code count", row)
    return rows


def _validate_row_metrics(row: TeamSpecialistSourceLatencyPenaltyRowV2) -> None:
    if row.stale_source_ratio != _six(_ratio(row.stale_source_count, row.source_count)):
        raise ValueError("stale_source_ratio must match source counts")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_metrics(report: TeamSpecialistSourceLatencyPenaltyReportV2) -> None:
    if report.team_domain_count != _count(len(report.rows)):
        raise ValueError("team_domain_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.high_latency_count != _count(
        sum(1 for row in report.rows if "latency_penalty_high" in row.reason_codes),
    ):
        raise ValueError("high_latency_count must match rows")
    if report.stale_source_count != _count(
        sum(
            1
            for row in report.rows
            if (
                "stale_source_ratio_watch" in row.reason_codes
                or "stale_source_ratio_block" in row.reason_codes
            )
        ),
    ):
        raise ValueError("stale_source_count must match rows")
    if report.stale_refresh_count != _count(
        sum(
            1
            for row in report.rows
            if (
                "refresh_age_watch" in row.reason_codes
                or "refresh_age_block" in row.reason_codes
            )
        ),
    ):
        raise ValueError("stale_refresh_count must match rows")
    if report.max_latency_penalty_score != _max_latency_penalty_score(report.rows):
        raise ValueError("max_latency_penalty_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _refresh_age_seconds(
    item: TeamSpecialistSourceLatencyPenaltyInputV2,
    generated_at: datetime,
) -> Decimal:
    seconds = Decimal(str((generated_at - item.latest_refresh_at).total_seconds()))
    if seconds < _ZERO_SCORE:
        raise ValueError("latest_refresh_at must not be in the future")
    return _six(seconds)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO_SCORE:
        raise ValueError("denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        value = numerator / denominator
    if value < _ZERO_SCORE:
        return _ZERO_SCORE
    if value > _ONE_SCORE:
        return _ONE_SCORE
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO_COUNT:
        raise ValueError("denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        return numerator / denominator


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _six(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_SIX_PLACE_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    count = _normalize_nonnegative_count(field_name, value)
    if count <= _ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return count


def _normalize_nonnegative_six_place_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _six(value)
    if quantized < _ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_six_place_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_six_place_decimal(field_name, value)
    if normalized <= _ZERO_SCORE:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_unit_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_six_place_decimal(field_name, value)
    if normalized > _ONE_SCORE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in _REASON_SEQUENCE:
            raise ValueError("reason_codes must be known")
    seen = set(reason_codes)
    return tuple(reason_code for reason_code in _REASON_SEQUENCE if reason_code in seen)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(field_name: str, value: object, expected: type[object]) -> None:
    if type(value) is not expected:
        raise ValueError(f"{field_name} must be exact {expected.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, object]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("payload paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError("payload report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError("payload readonly must be True")


def _validate_row_digest(row: TeamSpecialistSourceLatencyPenaltyRowV2) -> None:
    if row.derived_validation_digest != _digest_value(row):
        raise ValueError("derived_validation_digest tamper detected in row")


def _validate_report_digest(report: TeamSpecialistSourceLatencyPenaltyReportV2) -> None:
    for row in report.rows:
        _validate_row_digest(row)
    if report.derived_validation_digest != _digest_value(report):
        raise ValueError("derived_validation_digest tamper detected in report")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    expected = _payload_digest(payload)
    if payload.get(_DIGEST_FIELD) != expected:
        raise ValueError("derived_validation_digest must match payload")
    rows = payload.get("rows")
    if type(rows) is list:
        for row in rows:
            if type(row) is dict and _DIGEST_FIELD in row:
                expected_row_digest = _payload_digest(row)
                if row.get(_DIGEST_FIELD) != expected_row_digest:
                    raise ValueError("derived_validation_digest must match payload row")


def _payload_digest(payload: dict[str, Any]) -> str:
    payload_without_digest = dict(payload)
    payload_without_digest[_DIGEST_FIELD] = ""
    encoded = json.dumps(payload_without_digest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    payload[_DIGEST_FIELD] = ""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _reject_non_string_numeric(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is float:
        raise ValueError("float values are not supported in public payloads")
    if type(value) is int:
        raise ValueError("public numeric values must be Decimal strings")
    if type(value) is Decimal:
        raise ValueError("public Decimal values must be strings")
    if type(value) is dict:
        for item in value.values():
            _reject_non_string_numeric(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_non_string_numeric(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload key in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_SOURCE_LATENCY_PENALTY_DIGEST_V2_CONFIG_VERSION",
    "REPORT_STATUSES",
    "ROW_STATUSES",
    "TeamSpecialistSourceLatencyPenaltyDigestV2Config",
    "TeamSpecialistSourceLatencyPenaltyInputV2",
    "TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2",
    "TeamSpecialistSourceLatencyPenaltyRowV2",
    "TeamSpecialistSourceLatencyPenaltyReportV2",
    "build_team_specialist_source_latency_penalty_digest_v2",
    "team_specialist_source_latency_penalty_digest_v2_payload",
)
