"""Pure paper candidate portfolio exposure throttle diagnostics."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "BOUNDARY_STATEMENT",
    "CandidatePortfolioExposureBucket",
    "CandidatePortfolioExposureCandidate",
    "CandidatePortfolioExposureSnapshot",
    "CandidatePortfolioExposureThrottleConfig",
    "CandidatePortfolioExposureThrottleReport",
    "CandidatePortfolioExposureThrottleRow",
    "build_candidate_portfolio_exposure_throttle_report",
    "candidate_portfolio_exposure_throttle_payload",
)


BOUNDARY_STATEMENT = (
    "Phase 1 paper-only candidate portfolio exposure decision support; report-only readonly scope."
)
DEFAULT_CONFIG_VERSION = "candidate-portfolio-exposure-throttle-v0"
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
BUCKET_TYPES = ("event", "side", "team")
SIDES = ("yes", "no")
STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
UNSAFE_PUBLIC_FRAGMENTS = tuple(
    "".join(parts)
    for parts in (
        ("au", "th"),
        ("private", "_", "key"),
        ("sec", "ret"),
        ("tok", "en"),
        ("wa", "llet"),
        ("acc", "ount"),
        ("bal", "ance"),
        ("or", "der"),
        ("can", "cel"),
        ("si", "gn"),
        ("tr", "ade"),
        ("exchange", "_", "mutation"),
        ("buy",),
        ("sell",),
        ("rec", "ommend"),
    )
)
UNSAFE_PUBLIC_PAYLOAD_VALUE_FRAGMENTS = UNSAFE_PUBLIC_FRAGMENTS + tuple(
    "".join(parts)
    for parts in (
        ("ht", "tp"),
        (":", "/", "/"),
        ("www", "."),
        ("so", "urce"),
        ("mar", "ket"),
        ("slug",),
        ("quest", "ion"),
        ("dsn",),
        ("data", "base"),
        ("table",),
    )
)
UNSAFE_PUBLIC_FIELD_FRAGMENTS = tuple(
    "".join(parts)
    for parts in (
        ("so", "urce"),
        ("url",),
        ("mar", "ket"),
        ("slug",),
        ("quest", "ion"),
        ("dsn",),
        ("data", "base"),
        ("table",),
    )
)
POSITION_SIZING_FIELD_FRAGMENTS = tuple(
    "".join(parts)
    for parts in (
        ("not", "ional"),
        ("expo", "sure"),
        ("cash", "_", "buffer"),
        ("cash", "buffer"),
        ("lock", "up"),
        ("ratio",),
        ("stake",),
        ("allocation",),
        ("amount",),
    )
)
POSITION_SIZING_VALUE_FRAGMENTS = tuple(
    "".join(parts)
    for parts in (
        ("not", "ional"),
        ("position", "_", "size"),
        ("position", "_", "sizing"),
        ("position", "-", "size"),
        ("position", "-", "sizing"),
        ("position", " ", "size"),
        ("position", " ", "sizing"),
        ("cash", "_", "buffer"),
        ("cash", " ", "buffer"),
        ("cash", "buffer"),
        ("cash", "_", "lockup"),
        ("cash", " ", "lockup"),
        ("cash", "lockup"),
        ("lock", "_", "up"),
        ("lock", " ", "up"),
        ("lock", "up"),
        ("ratio",),
        ("stake",),
        ("allocation",),
        ("amount",),
    )
)
REPORT_REASON_SEQUENCE = (
    "candidate_exposure_block",
    "candidate_exposure_watch",
    "candidate_exposure_pass",
    "hard_safety_flag_present",
    "team_exposure_block",
    "event_exposure_block",
    "side_exposure_block",
    "cash_buffer_below_minimum",
    "cash_lockup_horizon_block",
    "team_exposure_watch",
    "event_exposure_watch",
    "side_exposure_watch",
    "long_cash_lockup_horizon",
    "candidate_exposure_empty",
)
REDACTED_CANDIDATE_PREFIX = "candidate_ref_"
REDACTED_EVENT_PREFIX = "event_ref_"
REDACTED_DIGEST_LENGTH = 32
RAW_REFERENCE_FIELDS = ("candidate_reference", "event_reference")
PUBLIC_REPORT_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "hard_flag_count",
        "status",
        "reason_codes",
        "rows",
        "boundary_statement",
        "paper_only",
        "report_only",
        "readonly",
    )
)
PUBLIC_ROW_FIELDS = frozenset(
    (
        "redacted_candidate_reference",
        "redacted_event_reference",
        "status",
        "reason_codes",
        "hard_safety_flags",
        "boundary_statement",
        "paper_only",
        "report_only",
        "readonly",
    )
)
PUBLIC_REASON_CODES = frozenset(
    (
        "candidate_exposure_block",
        "candidate_exposure_watch",
        "candidate_exposure_pass",
        "hard_safety_flag_present",
        "candidate_exposure_empty",
    )
)


@dataclass(frozen=True)
class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class CandidatePortfolioExposureThrottleConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_CONFIG_VERSION
    team_watch_ratio: Decimal = Decimal("0.300000")
    team_block_ratio: Decimal = Decimal("0.500000")
    event_watch_ratio: Decimal = Decimal("0.200000")
    event_block_ratio: Decimal = Decimal("0.350000")
    side_watch_ratio: Decimal = Decimal("0.600000")
    side_block_ratio: Decimal = Decimal("0.800000")
    minimum_cash_buffer_ratio: Decimal = Decimal("0.100000")
    long_cash_lockup_days: Decimal = Decimal("14.000000")
    block_cash_lockup_days: Decimal = Decimal("45.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "team_watch_ratio",
            "team_block_ratio",
            "event_watch_ratio",
            "event_block_ratio",
            "side_watch_ratio",
            "side_block_ratio",
            "minimum_cash_buffer_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("long_cash_lockup_days", "block_cash_lockup_days"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.team_watch_ratio > self.team_block_ratio:
            raise ValueError("team_watch_ratio must not exceed team_block_ratio")
        if self.event_watch_ratio > self.event_block_ratio:
            raise ValueError("event_watch_ratio must not exceed event_block_ratio")
        if self.side_watch_ratio > self.side_block_ratio:
            raise ValueError("side_watch_ratio must not exceed side_block_ratio")
        if self.long_cash_lockup_days > self.block_cash_lockup_days:
            raise ValueError("long_cash_lockup_days must not exceed block_cash_lockup_days")
        _require_flags("config", self)


@dataclass(frozen=True)
class CandidatePortfolioExposureBucket(_FinalPublicDataclass):
    bucket_type: str
    bucket_value: str
    current_notional: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "bucket_type",
            _require_member("bucket_type", self.bucket_type, BUCKET_TYPES),
        )
        object.__setattr__(
            self,
            "bucket_value",
            _require_public_text("bucket_value", self.bucket_value),
        )
        object.__setattr__(
            self,
            "current_notional",
            _require_nonnegative_decimal("current_notional", self.current_notional),
        )
        if self.bucket_type == "side":
            _require_member("bucket_value", self.bucket_value, SIDES)
        _require_flags("bucket", self)


@dataclass(frozen=True)
class CandidatePortfolioExposureSnapshot(_FinalPublicDataclass):
    total_paper_equity: Decimal
    available_cash: Decimal
    exposures: tuple[CandidatePortfolioExposureBucket, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "total_paper_equity",
            _require_positive_decimal("total_paper_equity", self.total_paper_equity),
        )
        object.__setattr__(
            self,
            "available_cash",
            _require_nonnegative_decimal("available_cash", self.available_cash),
        )
        object.__setattr__(
            self,
            "exposures",
            _normalize_buckets(self.exposures),
        )
        _require_flags("snapshot", self)


@dataclass(frozen=True)
class CandidatePortfolioExposureCandidate(_FinalPublicDataclass):
    candidate_reference: str
    event_reference: str
    team_id: str
    side: str
    candidate_notional: Decimal
    cash_lockup_days: Decimal
    hard_safety_flags: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "candidate_reference",
            _require_public_text("candidate_reference", self.candidate_reference),
        )
        object.__setattr__(
            self,
            "event_reference",
            _require_public_text("event_reference", self.event_reference),
        )
        object.__setattr__(
            self,
            "team_id",
            _require_public_text("team_id", self.team_id),
        )
        object.__setattr__(self, "side", _require_member("side", self.side, SIDES))
        object.__setattr__(
            self,
            "candidate_notional",
            _require_positive_decimal("candidate_notional", self.candidate_notional),
        )
        object.__setattr__(
            self,
            "cash_lockup_days",
            _require_nonnegative_decimal("cash_lockup_days", self.cash_lockup_days),
        )
        object.__setattr__(
            self,
            "hard_safety_flags",
            _normalize_flags(self.hard_safety_flags),
        )
        _require_flags("candidate", self)


@dataclass(frozen=True)
class CandidatePortfolioExposureThrottleRow(_FinalPublicDataclass):
    redacted_candidate_reference: str
    redacted_event_reference: str
    team_id: str
    side: str
    candidate_notional: Decimal
    cash_lockup_days: Decimal
    current_team_exposure: Decimal
    current_event_exposure: Decimal
    current_side_exposure: Decimal
    projected_team_exposure: Decimal
    projected_event_exposure: Decimal
    projected_side_exposure: Decimal
    projected_team_exposure_ratio: Decimal
    projected_event_exposure_ratio: Decimal
    projected_side_exposure_ratio: Decimal
    projected_cash_buffer: Decimal
    projected_cash_buffer_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    hard_safety_flags: tuple[str, ...]
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "team_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_public_text(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "redacted_candidate_reference",
            _require_redacted_reference(
                "redacted_candidate_reference",
                self.redacted_candidate_reference,
                REDACTED_CANDIDATE_PREFIX,
            ),
        )
        object.__setattr__(
            self,
            "redacted_event_reference",
            _require_redacted_reference(
                "redacted_event_reference",
                self.redacted_event_reference,
                REDACTED_EVENT_PREFIX,
            ),
        )
        object.__setattr__(self, "side", _require_member("side", self.side, SIDES))
        for field_name in (
            "candidate_notional",
            "cash_lockup_days",
            "current_team_exposure",
            "current_event_exposure",
            "current_side_exposure",
            "projected_team_exposure",
            "projected_event_exposure",
            "projected_side_exposure",
            "projected_team_exposure_ratio",
            "projected_event_exposure_ratio",
            "projected_side_exposure_ratio",
            "projected_cash_buffer",
            "projected_cash_buffer_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_member("status", self.status, STATUSES))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "hard_safety_flags",
            _normalize_flags(self.hard_safety_flags),
        )
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match paper-only scope")
        _validate_row_consistency(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class CandidatePortfolioExposureThrottleReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    hard_flag_count: Decimal
    total_candidate_notional: Decimal
    aggregate_candidate_notional_to_equity_ratio: Decimal
    max_projected_team_exposure_ratio: Decimal
    max_projected_event_exposure_ratio: Decimal
    max_projected_side_exposure_ratio: Decimal
    min_projected_cash_buffer_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[CandidatePortfolioExposureThrottleRow, ...]
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "hard_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_candidate_notional",
            "aggregate_candidate_notional_to_equity_ratio",
            "max_projected_team_exposure_ratio",
            "max_projected_event_exposure_ratio",
            "max_projected_side_exposure_ratio",
            "min_projected_cash_buffer_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_member("status", self.status, STATUSES))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match paper-only scope")
        _validate_report_consistency(self)
        _require_flags("report", self)


def build_candidate_portfolio_exposure_throttle_report(
    candidates: Iterable[CandidatePortfolioExposureCandidate],
    *,
    snapshot: CandidatePortfolioExposureSnapshot,
    config: CandidatePortfolioExposureThrottleConfig,
    generated_at: datetime,
) -> CandidatePortfolioExposureThrottleReport:
    if type(snapshot) is not CandidatePortfolioExposureSnapshot:
        raise ValueError("snapshot must be CandidatePortfolioExposureSnapshot")
    if type(config) is not CandidatePortfolioExposureThrottleConfig:
        raise ValueError("config must be CandidatePortfolioExposureThrottleConfig")
    _require_flags("snapshot", snapshot)
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    exposure_index = _exposure_index(snapshot.exposures)
    candidate_tuple = tuple(candidates)
    seen: set[str] = set()
    rows: list[CandidatePortfolioExposureThrottleRow] = []

    for candidate in candidate_tuple:
        if type(candidate) is not CandidatePortfolioExposureCandidate:
            raise ValueError("candidates must contain CandidatePortfolioExposureCandidate")
        _require_flags("candidate", candidate)
        if candidate.candidate_reference in seen:
            raise ValueError("duplicate candidate_reference")
        seen.add(candidate.candidate_reference)
        rows.append(_build_row(candidate, snapshot, config, exposure_index))

    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if not sorted_rows:
        return CandidatePortfolioExposureThrottleReport(
            generated_at=generated_at,
            config_version=config.config_version,
            candidate_count=_count_decimal(0),
            pass_count=_count_decimal(0),
            watch_count=_count_decimal(0),
            block_count=_count_decimal(0),
            hard_flag_count=_count_decimal(0),
            total_candidate_notional=ZERO,
            aggregate_candidate_notional_to_equity_ratio=ZERO,
            max_projected_team_exposure_ratio=ZERO,
            max_projected_event_exposure_ratio=ZERO,
            max_projected_side_exposure_ratio=ZERO,
            min_projected_cash_buffer_ratio=ZERO,
            status="watch",
            reason_codes=("candidate_exposure_empty",),
            rows=(),
        )

    total_candidate_notional = _sum_decimal(row.candidate_notional for row in sorted_rows)
    return CandidatePortfolioExposureThrottleReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(sorted_rows)),
        pass_count=_status_count(sorted_rows, "pass"),
        watch_count=_status_count(sorted_rows, "watch"),
        block_count=_status_count(sorted_rows, "block"),
        hard_flag_count=_count_decimal(
            sum(1 for row in sorted_rows if row.hard_safety_flags),
        ),
        total_candidate_notional=total_candidate_notional,
        aggregate_candidate_notional_to_equity_ratio=_ratio(
            total_candidate_notional,
            snapshot.total_paper_equity,
        ),
        max_projected_team_exposure_ratio=max(
            row.projected_team_exposure_ratio for row in sorted_rows
        ),
        max_projected_event_exposure_ratio=max(
            row.projected_event_exposure_ratio for row in sorted_rows
        ),
        max_projected_side_exposure_ratio=max(
            row.projected_side_exposure_ratio for row in sorted_rows
        ),
        min_projected_cash_buffer_ratio=min(
            row.projected_cash_buffer_ratio for row in sorted_rows
        ),
        status=_report_status(sorted_rows),
        reason_codes=_report_reasons(sorted_rows),
        rows=sorted_rows,
    )


def candidate_portfolio_exposure_throttle_payload(
    report: CandidatePortfolioExposureThrottleReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is CandidatePortfolioExposureThrottleReport:
        _require_flags("report", report)
        payload = _public_report_payload(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be CandidatePortfolioExposureThrottleReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload_schema(payload)
    _require_payload_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _public_report_payload(report: CandidatePortfolioExposureThrottleReport) -> dict[str, Any]:
    payload = {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "candidate_count": report.candidate_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "hard_flag_count": report.hard_flag_count,
        "status": report.status,
        "reason_codes": _public_reason_codes(report.reason_codes),
        "rows": tuple(_public_row_payload(row) for row in report.rows),
        "boundary_statement": report.boundary_statement,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    _reject_unsafe_public_payload("report", payload)
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    return ready


def _public_row_payload(row: CandidatePortfolioExposureThrottleRow) -> dict[str, Any]:
    _require_flags("row", row)
    return {
        "redacted_candidate_reference": row.redacted_candidate_reference,
        "redacted_event_reference": row.redacted_event_reference,
        "status": row.status,
        "reason_codes": _public_reason_codes(row.reason_codes),
        "hard_safety_flags": row.hard_safety_flags,
        "boundary_statement": row.boundary_statement,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _build_row(
    candidate: CandidatePortfolioExposureCandidate,
    snapshot: CandidatePortfolioExposureSnapshot,
    config: CandidatePortfolioExposureThrottleConfig,
    exposure_index: dict[tuple[str, str], Decimal],
) -> CandidatePortfolioExposureThrottleRow:
    current_team_exposure = exposure_index.get(("team", candidate.team_id), ZERO)
    current_event_exposure = exposure_index.get(("event", candidate.event_reference), ZERO)
    current_side_exposure = exposure_index.get(("side", candidate.side), ZERO)
    projected_team_exposure = _q(current_team_exposure + candidate.candidate_notional)
    projected_event_exposure = _q(current_event_exposure + candidate.candidate_notional)
    projected_side_exposure = _q(current_side_exposure + candidate.candidate_notional)
    projected_cash_buffer = max(
        _q(snapshot.available_cash - candidate.candidate_notional),
        ZERO,
    )
    team_ratio = _ratio(projected_team_exposure, snapshot.total_paper_equity)
    event_ratio = _ratio(projected_event_exposure, snapshot.total_paper_equity)
    side_ratio = _ratio(projected_side_exposure, snapshot.total_paper_equity)
    cash_buffer_ratio = _ratio(projected_cash_buffer, snapshot.total_paper_equity)
    status, reason_codes = _row_status_and_reasons(
        candidate,
        config,
        team_ratio=team_ratio,
        event_ratio=event_ratio,
        side_ratio=side_ratio,
        cash_buffer_ratio=cash_buffer_ratio,
    )
    return CandidatePortfolioExposureThrottleRow(
        redacted_candidate_reference=_redacted(
            candidate.candidate_reference,
            REDACTED_CANDIDATE_PREFIX,
        ),
        redacted_event_reference=_redacted(
            candidate.event_reference,
            REDACTED_EVENT_PREFIX,
        ),
        team_id=candidate.team_id,
        side=candidate.side,
        candidate_notional=candidate.candidate_notional,
        cash_lockup_days=candidate.cash_lockup_days,
        current_team_exposure=current_team_exposure,
        current_event_exposure=current_event_exposure,
        current_side_exposure=current_side_exposure,
        projected_team_exposure=projected_team_exposure,
        projected_event_exposure=projected_event_exposure,
        projected_side_exposure=projected_side_exposure,
        projected_team_exposure_ratio=team_ratio,
        projected_event_exposure_ratio=event_ratio,
        projected_side_exposure_ratio=side_ratio,
        projected_cash_buffer=projected_cash_buffer,
        projected_cash_buffer_ratio=cash_buffer_ratio,
        status=status,
        reason_codes=reason_codes,
        hard_safety_flags=candidate.hard_safety_flags,
    )


def _row_status_and_reasons(
    candidate: CandidatePortfolioExposureCandidate,
    config: CandidatePortfolioExposureThrottleConfig,
    *,
    team_ratio: Decimal,
    event_ratio: Decimal,
    side_ratio: Decimal,
    cash_buffer_ratio: Decimal,
) -> tuple[str, tuple[str, ...]]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []

    if candidate.hard_safety_flags:
        block_reasons.append("hard_safety_flag_present")
        block_reasons.extend(
            f"hard_safety_flag_{flag}" for flag in candidate.hard_safety_flags
        )
    if team_ratio >= config.team_block_ratio:
        block_reasons.append("team_exposure_block")
    elif team_ratio >= config.team_watch_ratio:
        watch_reasons.append("team_exposure_watch")
    if event_ratio >= config.event_block_ratio:
        block_reasons.append("event_exposure_block")
    elif event_ratio >= config.event_watch_ratio:
        watch_reasons.append("event_exposure_watch")
    if side_ratio >= config.side_block_ratio:
        block_reasons.append("side_exposure_block")
    elif side_ratio >= config.side_watch_ratio:
        watch_reasons.append("side_exposure_watch")
    if cash_buffer_ratio < config.minimum_cash_buffer_ratio:
        block_reasons.append("cash_buffer_below_minimum")
    if candidate.cash_lockup_days >= config.block_cash_lockup_days:
        block_reasons.append("cash_lockup_horizon_block")
    elif candidate.cash_lockup_days >= config.long_cash_lockup_days:
        watch_reasons.append("long_cash_lockup_horizon")

    if block_reasons:
        return "block", _normalize_reasons(
            ("candidate_exposure_block", *block_reasons),
            allow_empty=False,
        )
    if watch_reasons:
        return "watch", _normalize_reasons(
            ("candidate_exposure_watch", *watch_reasons),
            allow_empty=False,
        )
    return "pass", ("candidate_exposure_pass",)


def _report_status(rows: tuple[CandidatePortfolioExposureThrottleRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reasons(
    rows: tuple[CandidatePortfolioExposureThrottleRow, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    dynamic_flags = sorted(
        reason for reason in seen if reason.startswith("hard_safety_flag_")
    )
    sequenced = [reason for reason in REPORT_REASON_SEQUENCE if reason in seen]
    for reason in dynamic_flags:
        if reason not in sequenced:
            sequenced.append(reason)
    return tuple(sequenced)


def _public_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    public_codes: list[str] = []
    for reason_code in reason_codes:
        if reason_code.startswith("hard_safety_flag_"):
            _reject_position_sizing_text("reason_code", reason_code)
            public_codes.append(reason_code)
        elif reason_code in PUBLIC_REASON_CODES:
            public_codes.append(reason_code)
    return tuple(public_codes)


def _row_sort_key(
    row: CandidatePortfolioExposureThrottleRow,
) -> tuple[int, Decimal, str, str, str, str]:
    return (
        STATUS_RANK[row.status],
        -row.candidate_notional,
        row.redacted_candidate_reference,
        row.redacted_event_reference,
        row.team_id,
        row.side,
    )


def _status_count(
    rows: tuple[CandidatePortfolioExposureThrottleRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _exposure_index(
    exposures: tuple[CandidatePortfolioExposureBucket, ...],
) -> dict[tuple[str, str], Decimal]:
    index: dict[tuple[str, str], Decimal] = {}
    for exposure in exposures:
        key = (exposure.bucket_type, exposure.bucket_value)
        index[key] = _q(index.get(key, ZERO) + exposure.current_notional)
    return index


def _validate_row_consistency(row: CandidatePortfolioExposureThrottleRow) -> None:
    if row.projected_team_exposure != _q(
        row.current_team_exposure + row.candidate_notional
    ):
        raise ValueError("projected_team_exposure must match candidate notional")
    if row.projected_event_exposure != _q(
        row.current_event_exposure + row.candidate_notional
    ):
        raise ValueError("projected_event_exposure must match candidate notional")
    if row.projected_side_exposure != _q(
        row.current_side_exposure + row.candidate_notional
    ):
        raise ValueError("projected_side_exposure must match candidate notional")
    if row.status == "pass" and row.reason_codes != ("candidate_exposure_pass",):
        raise ValueError("pass rows must use pass reason")
    if row.status == "watch" and row.reason_codes[0] != "candidate_exposure_watch":
        raise ValueError("watch rows must use watch reason")
    if row.status == "block" and row.reason_codes[0] != "candidate_exposure_block":
        raise ValueError("block rows must use block reason")


def _validate_report_consistency(report: CandidatePortfolioExposureThrottleReport) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count does not match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count does not match rows")
    if report.hard_flag_count != _count_decimal(
        sum(1 for row in report.rows if row.hard_safety_flags)
    ):
        raise ValueError("hard_flag_count does not match rows")
    if report.total_candidate_notional != _sum_decimal(
        row.candidate_notional for row in report.rows
    ):
        raise ValueError("total_candidate_notional does not match rows")
    expected_status = "watch" if not report.rows else _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status does not match rows")
    expected_reasons = (
        ("candidate_exposure_empty",) if not report.rows else _report_reasons(report.rows)
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes do not match rows")


def _normalize_buckets(value: object) -> tuple[CandidatePortfolioExposureBucket, ...]:
    if type(value) is not tuple:
        raise ValueError("exposures must be a tuple")
    for item in value:
        if type(item) is not CandidatePortfolioExposureBucket:
            raise ValueError("exposures must contain CandidatePortfolioExposureBucket")
        _require_flags("exposure", item)
    return tuple(sorted(value, key=lambda item: (item.bucket_type, item.bucket_value)))


def _normalize_rows(value: object) -> tuple[CandidatePortfolioExposureThrottleRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for item in value:
        if type(item) is not CandidatePortfolioExposureThrottleRow:
            raise ValueError("rows must contain CandidatePortfolioExposureThrottleRow")
        _require_flags("row", item)
    rows = tuple(value)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _normalize_reasons(value: object, *, allow_empty: bool) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason in value:
        reason = _require_code("reason_code", reason)
        if reason not in normalized:
            normalized.append(reason)
    return tuple(normalized)


def _normalize_flags(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("hard_safety_flags must be a tuple")
    normalized: list[str] = []
    for flag in value:
        flag = _require_code("hard_safety_flag", flag)
        _reject_position_sizing_text("hard_safety_flag", flag)
        if flag not in normalized:
            normalized.append(flag)
    return tuple(sorted(normalized))


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonempty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {field_name}")
    return value


def _require_code(field_name: str, value: object) -> str:
    value = _require_public_text(field_name, value)
    if not all(character.islower() or character.isdigit() or character == "_" for character in value):
        raise ValueError(f"{field_name} must be a lowercase code")
    return value


def _require_member(field_name: str, value: object, choices: tuple[str, ...]) -> str:
    value = _require_public_text(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")
    return value


def _require_redacted_reference(field_name: str, value: object, prefix: str) -> str:
    value = _require_public_text(field_name, value)
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be redacted")
    suffix = value.removeprefix(prefix)
    if (
        len(suffix) != REDACTED_DIGEST_LENGTH
        or not suffix
        or not all(character in "0123456789abcdef" for character in suffix)
    ):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _q(_require_decimal(field_name, value))
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_ratio(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _require_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload {field_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _q(numerator / denominator)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _q(total + _require_decimal("value", value))
    return total


def _count_decimal(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _redacted(value: str, prefix: str) -> str:
    return prefix + hashlib.sha256(value.encode("utf-8")).hexdigest()[:REDACTED_DIGEST_LENGTH]


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is bool or type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_PAYLOAD_VALUE_FRAGMENTS):
            raise ValueError(f"unsafe public value in {path or label}")
        _reject_position_sizing_text(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError(f"{path or label} must be a finite Decimal")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if key in RAW_REFERENCE_FIELDS:
                raise ValueError(f"unredacted reference field in {label}: {key}")
            nested_path = key if not path else f"{path}.{key}"
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in POSITION_SIZING_FIELD_FRAGMENTS):
                raise ValueError(f"position sizing field in {label}: {key}")
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key == "redacted_candidate_reference":
                _require_redacted_reference(key, item, REDACTED_CANDIDATE_PREFIX)
            if key == "redacted_event_reference":
                _require_redacted_reference(key, item, REDACTED_EVENT_PREFIX)
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if type(value) is list or type(value) is tuple:
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_exact_public_fields("payload", payload, PUBLIC_REPORT_FIELDS)
    _validate_public_status("payload.status", payload.get("status"))
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload rows must contain JSON objects")
        _require_exact_public_fields(
            f"payload.rows[{index}]",
            row,
            PUBLIC_ROW_FIELDS,
        )
        _validate_public_status(
            f"payload.rows[{index}].status",
            row.get("status"),
        )
        _validate_public_reason_codes(
            f"payload.rows[{index}].reason_codes",
            row.get("reason_codes"),
        )
        _validate_public_code_list(
            f"payload.rows[{index}].hard_safety_flags",
            row.get("hard_safety_flags"),
        )
    _validate_public_reason_codes("payload.reason_codes", payload.get("reason_codes"))


def _require_exact_public_fields(
    label: str,
    payload: dict[str, Any],
    allowed_fields: frozenset[str],
) -> None:
    for key in payload:
        if key not in allowed_fields:
            raise ValueError(f"unexpected public field in {label}: {key}")
    for key in allowed_fields:
        if key not in payload:
            raise ValueError(f"missing public field in {label}: {key}")


def _validate_public_reason_codes(label: str, value: object) -> None:
    for reason_code in _require_public_string_list(label, value):
        _reject_position_sizing_text(label, reason_code)
        if (
            reason_code not in PUBLIC_REASON_CODES
            and not reason_code.startswith("hard_safety_flag_")
        ):
            raise ValueError(f"unexpected public reason code in {label}: {reason_code}")


def _validate_public_status(label: str, value: object) -> None:
    _require_member(label, value, STATUSES)


def _validate_public_code_list(label: str, value: object) -> None:
    for code in _require_public_string_list(label, value):
        _reject_position_sizing_text(label, code)


def _require_public_string_list(label: str, value: object) -> list[str]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a list")
    for item in value:
        if type(item) is not str:
            raise ValueError(f"{label} must contain strings")
    return value


def _reject_position_sizing_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in POSITION_SIZING_VALUE_FRAGMENTS):
        raise ValueError(f"position sizing value in {field_name}")
