"""Report-only authority-lag scoring for resolved research event claims."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


CONFIG_VERSION = "research_event_claim_resolution_authority_lag_report"
DECIMAL_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PASS = "authority_lag_pass"
REASON_WATCH = "authority_lag_watch"
REASON_BLOCK = "authority_lag_block"
REASON_MISSING_AUTHORITY_REPORT = "missing_authority_report"
REASON_INSUFFICIENT_RESOLVER_CONFIRMATION = "insufficient_resolver_confirmation"
REASON_CONFLICTING_RESOLVER_CONFIRMATION = "conflicting_resolver_confirmation"


@dataclass(frozen=True)
class ResearchEventClaimResolutionAuthorityLagConfig:
    config_version: str = CONFIG_VERSION
    watch_lag_hours: Decimal = Decimal("24")
    block_lag_hours: Decimal = Decimal("72")
    min_resolver_confirmation_count: Decimal = Decimal("1")
    max_conflicting_resolver_count: Decimal = Decimal("0")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClaimResolutionAuthorityLagConfig:
            raise TypeError(
                "ResearchEventClaimResolutionAuthorityLagConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimResolutionAuthorityLagConfig:
            raise ValueError(
                "config must be exactly ResearchEventClaimResolutionAuthorityLagConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_lag_hours",
            "block_lag_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_resolver_confirmation_count",
            "max_conflicting_resolver_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_lag_hours <= self.watch_lag_hours:
            raise ValueError("block_lag_hours must exceed watch_lag_hours")
        require_paper_only_flags("authority lag config", self)


@dataclass(frozen=True)
class ResearchEventClaimResolutionAuthorityLagCandidate:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    resolution_authority_id: str
    claim_category: str
    resolution_at: datetime
    authority_reported_at: datetime | None
    observed_at: datetime
    resolver_confirmation_count: Decimal
    conflicting_resolver_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClaimResolutionAuthorityLagCandidate:
            raise TypeError(
                "ResearchEventClaimResolutionAuthorityLagCandidate does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimResolutionAuthorityLagCandidate:
            raise ValueError(
                "candidate must be exactly ResearchEventClaimResolutionAuthorityLagCandidate",
            )
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "resolution_authority_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_public_label_string("claim_category", self.claim_category)
        object.__setattr__(self, "resolution_at", _as_utc("resolution_at", self.resolution_at))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.authority_reported_at is not None:
            object.__setattr__(
                self,
                "authority_reported_at",
                _as_utc("authority_reported_at", self.authority_reported_at),
            )
        if self.observed_at < self.resolution_at:
            raise ValueError("observed_at must be at or after resolution_at")
        if self.authority_reported_at is not None:
            if self.authority_reported_at < self.resolution_at:
                raise ValueError("authority_reported_at must be at or after resolution_at")
            if self.authority_reported_at > self.observed_at:
                raise ValueError("authority_reported_at must be at or before observed_at")
        for field_name in (
            "resolver_confirmation_count",
            "conflicting_resolver_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        require_paper_only_flags("authority lag candidate", self)


@dataclass(frozen=True)
class ResearchEventClaimResolutionAuthorityLagRow:
    claim_fingerprint: str
    resolver_fingerprint: str
    claim_category: str
    resolution_at: datetime
    authority_reported_at: datetime | None
    observed_at: datetime
    authority_lag_hours: Decimal | None
    resolution_age_hours: Decimal
    resolver_confirmation_count: Decimal
    conflicting_resolver_count: Decimal
    lag_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClaimResolutionAuthorityLagRow:
            raise TypeError(
                "ResearchEventClaimResolutionAuthorityLagRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimResolutionAuthorityLagRow:
            raise ValueError("row must be exactly ResearchEventClaimResolutionAuthorityLagRow")
        _require_fingerprint("claim_fingerprint", self.claim_fingerprint)
        _require_fingerprint("resolver_fingerprint", self.resolver_fingerprint)
        _require_public_label_string("claim_category", self.claim_category)
        object.__setattr__(self, "resolution_at", _as_utc("resolution_at", self.resolution_at))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.authority_reported_at is not None:
            object.__setattr__(
                self,
                "authority_reported_at",
                _as_utc("authority_reported_at", self.authority_reported_at),
            )
        if self.observed_at < self.resolution_at:
            raise ValueError("observed_at must be at or after resolution_at")
        if self.authority_reported_at is not None:
            if self.authority_reported_at < self.resolution_at:
                raise ValueError("authority_reported_at must be at or after resolution_at")
            if self.authority_reported_at > self.observed_at:
                raise ValueError("authority_reported_at must be at or before observed_at")
        if self.authority_lag_hours is not None:
            object.__setattr__(
                self,
                "authority_lag_hours",
                _normalize_nonnegative_decimal("authority_lag_hours", self.authority_lag_hours),
            )
        object.__setattr__(
            self,
            "resolution_age_hours",
            _normalize_nonnegative_decimal("resolution_age_hours", self.resolution_age_hours),
        )
        for field_name in (
            "resolver_confirmation_count",
            "conflicting_resolver_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("lag_status", self.lag_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        require_paper_only_flags("authority lag row", self)


@dataclass(frozen=True)
class ResearchEventClaimResolutionAuthorityLagReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_authority_lag_hours: Decimal
    maximum_authority_lag_hours: Decimal
    status: str
    rows: tuple[ResearchEventClaimResolutionAuthorityLagRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClaimResolutionAuthorityLagReport:
            raise TypeError(
                "ResearchEventClaimResolutionAuthorityLagReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimResolutionAuthorityLagReport:
            raise ValueError("report must be exactly ResearchEventClaimResolutionAuthorityLagReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_authority_lag_hours",
            "maximum_authority_lag_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", _report_validation_digest(self))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        require_paper_only_flags("authority lag report", self)
        _require_report_validation_digest(self)
        _reject_unsafe_public_payload("authority lag report", _payload_value(asdict(self)))


def build_research_event_claim_resolution_authority_lag_report(
    candidates: tuple[ResearchEventClaimResolutionAuthorityLagCandidate, ...],
    *,
    generated_at: datetime,
    config: ResearchEventClaimResolutionAuthorityLagConfig,
) -> ResearchEventClaimResolutionAuthorityLagReport:
    if type(candidates) is not tuple:
        raise ValueError("candidates must be a tuple")
    if type(config) is not ResearchEventClaimResolutionAuthorityLagConfig:
        raise ValueError("config must be a ResearchEventClaimResolutionAuthorityLagConfig")
    require_paper_only_flags("authority lag config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(sorted((_build_row(candidate, config) for candidate in candidates), key=_row_sort_key))
    reason_code_counts = _reason_code_counts(rows)
    return ResearchEventClaimResolutionAuthorityLagReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        row_count=Decimal(len(rows)),
        pass_count=_count_status(rows, STATUS_PASS),
        watch_count=_count_status(rows, STATUS_WATCH),
        block_count=_count_status(rows, STATUS_BLOCK),
        average_authority_lag_hours=_average(
            row.authority_lag_hours for row in rows if row.authority_lag_hours is not None
        ),
        maximum_authority_lag_hours=_maximum_lag(rows),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
    )


def research_event_claim_resolution_authority_lag_report_payload(
    report: ResearchEventClaimResolutionAuthorityLagReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventClaimResolutionAuthorityLagReport:
        require_paper_only_flags("authority lag report", report)
        _validate_report_consistency(report)
        _require_report_validation_digest(report)
        payload = _payload_value(asdict(report))
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError("report must be a ResearchEventClaimResolutionAuthorityLagReport or object")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def _build_row(
    candidate: ResearchEventClaimResolutionAuthorityLagCandidate,
    config: ResearchEventClaimResolutionAuthorityLagConfig,
) -> ResearchEventClaimResolutionAuthorityLagRow:
    if type(candidate) is not ResearchEventClaimResolutionAuthorityLagCandidate:
        raise ValueError(
            "candidates must contain ResearchEventClaimResolutionAuthorityLagCandidate values",
        )
    require_paper_only_flags("authority lag candidate", candidate)
    resolution_age_hours = _hours_between(candidate.resolution_at, candidate.observed_at)
    authority_lag_hours = (
        None
        if candidate.authority_reported_at is None
        else _hours_between(candidate.resolution_at, candidate.authority_reported_at)
    )
    lag_status = _lag_status(
        authority_lag_hours=authority_lag_hours,
        resolution_age_hours=resolution_age_hours,
        resolver_confirmation_count=candidate.resolver_confirmation_count,
        conflicting_resolver_count=candidate.conflicting_resolver_count,
        config=config,
    )
    return ResearchEventClaimResolutionAuthorityLagRow(
        claim_fingerprint=_claim_fingerprint(candidate),
        resolver_fingerprint=_resolver_fingerprint(candidate),
        claim_category=candidate.claim_category,
        resolution_at=candidate.resolution_at,
        authority_reported_at=candidate.authority_reported_at,
        observed_at=candidate.observed_at,
        authority_lag_hours=authority_lag_hours,
        resolution_age_hours=resolution_age_hours,
        resolver_confirmation_count=candidate.resolver_confirmation_count,
        conflicting_resolver_count=candidate.conflicting_resolver_count,
        lag_status=lag_status,
        reason_codes=_row_reason_codes(candidate, lag_status=lag_status, config=config),
    )


def _lag_status(
    *,
    authority_lag_hours: Decimal | None,
    resolution_age_hours: Decimal,
    resolver_confirmation_count: Decimal,
    conflicting_resolver_count: Decimal,
    config: ResearchEventClaimResolutionAuthorityLagConfig,
) -> str:
    if (
        resolver_confirmation_count < config.min_resolver_confirmation_count
        or conflicting_resolver_count > config.max_conflicting_resolver_count
    ):
        return STATUS_BLOCK
    if authority_lag_hours is None:
        if resolution_age_hours >= config.block_lag_hours:
            return STATUS_BLOCK
        return STATUS_WATCH
    if authority_lag_hours >= config.block_lag_hours:
        return STATUS_BLOCK
    if authority_lag_hours >= config.watch_lag_hours:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    candidate: ResearchEventClaimResolutionAuthorityLagCandidate,
    *,
    lag_status: str,
    config: ResearchEventClaimResolutionAuthorityLagConfig,
) -> tuple[str, ...]:
    codes = set(candidate.reason_codes)
    if lag_status == STATUS_PASS:
        codes.add(REASON_PASS)
    elif lag_status == STATUS_WATCH:
        codes.add(REASON_WATCH)
    elif lag_status == STATUS_BLOCK:
        codes.add(REASON_BLOCK)
    else:
        raise ValueError("lag_status must be known")
    if candidate.authority_reported_at is None:
        codes.add(REASON_MISSING_AUTHORITY_REPORT)
    if candidate.resolver_confirmation_count < config.min_resolver_confirmation_count:
        codes.add(REASON_INSUFFICIENT_RESOLVER_CONFIRMATION)
    if candidate.conflicting_resolver_count > config.max_conflicting_resolver_count:
        codes.add(REASON_CONFLICTING_RESOLVER_CONFIRMATION)
    return _normalize_reason_codes(tuple(codes), allow_empty=False)


def _claim_fingerprint(candidate: ResearchEventClaimResolutionAuthorityLagCandidate) -> str:
    return _fingerprint(
        (
            "claim",
            candidate.candidate_id,
            candidate.market_id,
            candidate.market_slug,
            candidate.market_question,
        ),
    )


def _resolver_fingerprint(candidate: ResearchEventClaimResolutionAuthorityLagCandidate) -> str:
    return _fingerprint(
        (
            "resolver",
            candidate.resolution_authority_id,
            candidate.claim_category,
        ),
    )


def _fingerprint(parts: tuple[str, ...]) -> str:
    canonical = json.dumps(list(parts), sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _row_sort_key(row: ResearchEventClaimResolutionAuthorityLagRow) -> tuple[str, str, str, datetime]:
    return (row.lag_status, row.claim_category, row.claim_fingerprint, row.observed_at)


def _reason_code_counts(
    rows: tuple[ResearchEventClaimResolutionAuthorityLagRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple((code, Decimal(counter[code])) for code in sorted(counter))


def _count_status(rows: tuple[ResearchEventClaimResolutionAuthorityLagRow, ...], status: str) -> Decimal:
    return Decimal(sum(1 for row in rows if row.lag_status == status))


def _summary_status(rows: tuple[ResearchEventClaimResolutionAuthorityLagRow, ...]) -> str:
    if _count_status(rows, STATUS_BLOCK) > ZERO:
        return STATUS_BLOCK
    if _count_status(rows, STATUS_WATCH) > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _average(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _maximum_lag(rows: tuple[ResearchEventClaimResolutionAuthorityLagRow, ...]) -> Decimal:
    values = tuple(row.authority_lag_hours for row in rows if row.authority_lag_hours is not None)
    if not values:
        return ZERO
    return _quantize(max(values))


def _hours_between(started_at: datetime, finished_at: datetime) -> Decimal:
    if finished_at < started_at:
        raise ValueError("finished_at must be at or after started_at")
    delta = finished_at - started_at
    seconds = (
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    return _quantize(seconds / Decimal("3600"))


def _normalize_rows(
    value: object,
) -> tuple[ResearchEventClaimResolutionAuthorityLagRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    if not all(type(row) is ResearchEventClaimResolutionAuthorityLagRow for row in rows):
        raise ValueError("rows must contain ResearchEventClaimResolutionAuthorityLagRow values")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return rows


def _normalize_reason_code_counts(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    previous: str | None = None
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts values must be pairs")
        code, count = item
        _require_public_label_string("reason_code_counts", code)
        if previous is not None and previous > code:
            raise ValueError("reason_code_counts must be sorted")
        normalized.append((code, _normalize_count_decimal("reason_code_counts", count)))
        previous = code
    return tuple(normalized)


def _normalize_reason_codes(value: object, *, allow_empty: bool = False) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    codes = tuple(value)
    if not codes and not allow_empty:
        raise ValueError("reason_codes is required")
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    for code in codes:
        _require_public_label_string("reason_codes", code)
    return tuple(sorted(codes))


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")


def _require_public_label_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    if any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789_-"
        for character in value
    ):
        raise ValueError(f"{field_name} must be a lowercase public label")
    _reject_unsafe_string(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_fingerprint(field_name: str, value: object) -> None:
    if type(value) is not str or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 fingerprint")
    _require_sha256_digest(field_name, value.removeprefix("sha256:"))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _validate_row_consistency(row: ResearchEventClaimResolutionAuthorityLagRow) -> None:
    expected_age = _hours_between(row.resolution_at, row.observed_at)
    if row.resolution_age_hours != expected_age:
        raise ValueError("resolution_age_hours must match resolution_at and observed_at")
    if row.authority_reported_at is None:
        if row.authority_lag_hours is not None:
            raise ValueError("authority_lag_hours must be empty without authority_reported_at")
    elif row.authority_lag_hours != _hours_between(row.resolution_at, row.authority_reported_at):
        raise ValueError("authority_lag_hours must match resolution_at and authority_reported_at")
    expected_reason = {
        STATUS_PASS: REASON_PASS,
        STATUS_WATCH: REASON_WATCH,
        STATUS_BLOCK: REASON_BLOCK,
    }[row.lag_status]
    if expected_reason not in row.reason_codes:
        raise ValueError("reason_codes must include lag_status reason")


def _validate_report_consistency(report: ResearchEventClaimResolutionAuthorityLagReport) -> None:
    if report.row_count != Decimal(len(report.rows)):
        raise ValueError("row_count must equal rows length")
    if report.pass_count != _count_status(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_status(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_status(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_authority_lag_hours != _average(
        row.authority_lag_hours for row in report.rows if row.authority_lag_hours is not None
    ):
        raise ValueError("average_authority_lag_hours must match rows")
    if report.maximum_authority_lag_hours != _maximum_lag(report.rows):
        raise ValueError("maximum_authority_lag_hours must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_validation_digest(report: ResearchEventClaimResolutionAuthorityLagReport) -> str:
    return _derived_validation_digest(asdict(report))


def _require_report_validation_digest(report: ResearchEventClaimResolutionAuthorityLagReport) -> None:
    if report.derived_validation_digest != _report_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(values: dict[str, object]) -> str:
    payload = {
        key: _payload_value(value)
        for key, value in values.items()
        if key != "derived_validation_digest"
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _payload_value(value: object) -> object:
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is Decimal:
        return format(_quantize(value), "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is dict:
        ready: dict[str, object] = {}
        for key, item in value.items():
            _require_canonical_string("payload key", key)
            ready[key] = _payload_value(item)
        return ready
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type) and type(value).__module__ == __name__:
        return _payload_value(asdict(value))
    raise ValueError("public payload contains unsupported value")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("authority lag payload", payload)
    _require_public_payload_flags("authority lag payload", payload)
    _require_public_payload_statuses("authority lag payload", payload)
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _require_public_payload_statuses(label: str, value: object) -> None:
    if type(value) is dict:
        for key, child in value.items():
            if key in ("status", "lag_status"):
                _require_status(key, child)
            _require_public_payload_statuses(label, child)
        return
    if type(value) is list:
        for child in value:
            _require_public_payload_statuses(label, child)
        return
    if value is None or type(value) in (str, bool):
        return
    raise ValueError(f"{label} must use safe serialized scalars")


def _require_public_payload_flags(label: str, value: object) -> None:
    if type(value) is dict:
        for field_name in ("paper_only", "report_only", "readonly"):
            if field_name in value and value.get(field_name) is not True:
                raise ValueError(f"{label} {field_name} must be True")
        for child in value.values():
            _require_public_payload_flags(label, child)
        return
    if type(value) is list:
        for child in value:
            _require_public_payload_flags(label, child)
        return
    if value is None or type(value) in (str, bool):
        return
    raise ValueError(f"{label} must use safe serialized scalars")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload key in {label}")
            _reject_unsafe_key(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_string(label, value)


def _reject_unsafe_key(label: str, key: str) -> None:
    normalized = key.lower()
    forbidden_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "source_reference",
        "source_ref",
        "url",
        "dsn",
        "table",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "token",
        "private_key",
        "api_key",
        "secret",
        "bearer",
        "authorization",
        "oauth",
        "database",
    )
    if any(fragment in normalized for fragment in forbidden_fragments):
        raise ValueError(f"unsafe public payload field in {label}: {key}")


def _reject_unsafe_string(label: str, value: str) -> None:
    normalized = value.lower()
    forbidden_fragments = (
        "candidate_id",
        "candidate-",
        "candidate_",
        "market_id",
        "market_slug",
        "market_question",
        "market-",
        "market_",
        "slug",
        "question",
        "source_url",
        "source_text",
        "source_reference",
        "source_ref",
        "http://",
        "https://",
        "postgres://",
        "postgresql://",
        "mysql://",
        "sqlite://",
        "mongodb://",
        "dsn",
        "table",
        "database",
        "private_key",
        "api_key",
        "token",
        "bearer ",
        "wallet:",
        "wallet",
        "submit_order",
        "cancel_order",
        "replace_order",
        "order_",
        "_order",
        "trade",
        "sizing",
        "recommendation",
    )
    if any(fragment in normalized for fragment in forbidden_fragments):
        raise ValueError(f"unsafe public payload value in {label}")


__all__ = (
    "ResearchEventClaimResolutionAuthorityLagCandidate",
    "ResearchEventClaimResolutionAuthorityLagConfig",
    "ResearchEventClaimResolutionAuthorityLagReport",
    "ResearchEventClaimResolutionAuthorityLagRow",
    "build_research_event_claim_resolution_authority_lag_report",
    "research_event_claim_resolution_authority_lag_report_payload",
)
