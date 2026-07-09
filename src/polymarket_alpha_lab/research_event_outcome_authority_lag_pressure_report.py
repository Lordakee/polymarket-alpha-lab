"""Pure report-only event outcome authority lag pressure reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_CONFIG_VERSION = "research-event-outcome-authority-lag-pressure-report-v0"

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

EMPTY_REASON = "outcome_authority_lag_pressure_empty"
PASS_REASON = "outcome_authority_lag_pressure_pass"
WATCH_REASON = "outcome_authority_lag_pressure_watch"
BLOCK_REASON = "outcome_authority_lag_pressure_block"
AUTHORITY_CONFIRMATION_MISSING_REASON = "authority_confirmation_missing"
AUTHORITY_LAG_WATCH_REASON = "authority_lag_watch"
AUTHORITY_LAG_BLOCK_REASON = "authority_lag_block"
AUTHORITY_CHECK_STALENESS_WATCH_REASON = "authority_check_staleness_watch"
AUTHORITY_CHECK_STALENESS_BLOCK_REASON = "authority_check_staleness_block"
AUTHORITY_QUORUM_WATCH_REASON = "authority_quorum_watch"
AUTHORITY_QUORUM_BLOCK_REASON = "authority_quorum_block"
CONTRADICTION_PRESSURE_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_PRESSURE_BLOCK_REASON = "contradiction_pressure_block"

REASON_CODE_PRIORITY = (
    EMPTY_REASON,
    AUTHORITY_CONFIRMATION_MISSING_REASON,
    AUTHORITY_LAG_BLOCK_REASON,
    AUTHORITY_CHECK_STALENESS_BLOCK_REASON,
    AUTHORITY_QUORUM_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    BLOCK_REASON,
    AUTHORITY_LAG_WATCH_REASON,
    AUTHORITY_CHECK_STALENESS_WATCH_REASON,
    AUTHORITY_QUORUM_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    WATCH_REASON,
    PASS_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)
BLOCK_REASONS = frozenset(
    (
        EMPTY_REASON,
        AUTHORITY_CONFIRMATION_MISSING_REASON,
        AUTHORITY_LAG_BLOCK_REASON,
        AUTHORITY_CHECK_STALENESS_BLOCK_REASON,
        AUTHORITY_QUORUM_BLOCK_REASON,
        CONTRADICTION_PRESSURE_BLOCK_REASON,
        BLOCK_REASON,
    ),
)
WATCH_REASONS = frozenset(
    (
        AUTHORITY_LAG_WATCH_REASON,
        AUTHORITY_CHECK_STALENESS_WATCH_REASON,
        AUTHORITY_QUORUM_WATCH_REASON,
        CONTRADICTION_PRESSURE_WATCH_REASON,
        WATCH_REASON,
    ),
)

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "raw_id",
    "raw-",
    "raw_",
    "slug",
    "question",
    "source_url",
    "source-url",
    "source_text",
    "source-text",
    "source_ref",
    "source-ref",
    "://",
    "http://",
    "https://",
    "www.",
    "dsn",
    "table",
    "token",
    "wal" + "let",
    "author" + "ization",
    "credential",
    "or" + "der",
    "tr" + "ade",
    "buy",
    "sell",
    "position",
    "siz" + "ing",
    "recomm" + "endation",
    "net" + "work",
    "live",
)


@dataclass(frozen=True)
class ResearchEventOutcomeAuthorityLagPressureReportConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    max_pass_authority_lag_seconds: Decimal = Decimal("3600.000000")
    max_watch_authority_lag_seconds: Decimal = Decimal("14400.000000")
    max_pass_authority_check_age_seconds: Decimal = Decimal("1800.000000")
    max_watch_authority_check_age_seconds: Decimal = Decimal("7200.000000")
    min_pass_authority_quorum_score: Decimal = Decimal("1.000000")
    min_watch_authority_quorum_score: Decimal = Decimal("0.500000")
    watch_contradiction_pressure: Decimal = Decimal("0.150000")
    block_contradiction_pressure: Decimal = Decimal("0.600000")
    authority_lag_pressure_weight: Decimal = Decimal("0.300000")
    authority_check_staleness_pressure_weight: Decimal = Decimal("0.237500")
    authority_quorum_gap_pressure_weight: Decimal = Decimal("0.262500")
    contradiction_pressure_weight: Decimal = Decimal("0.200000")
    watch_lag_pressure_score: Decimal = Decimal("0.250000")
    block_lag_pressure_score: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventOutcomeAuthorityLagPressureReportConfig:
            raise TypeError(
                "ResearchEventOutcomeAuthorityLagPressureReportConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeAuthorityLagPressureReportConfig:
            raise ValueError(
                "config must be a ResearchEventOutcomeAuthorityLagPressureReportConfig",
            )
        _require_public_label("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "max_pass_authority_lag_seconds",
            "max_watch_authority_lag_seconds",
            "max_pass_authority_check_age_seconds",
            "max_watch_authority_check_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_authority_quorum_score",
            "min_watch_authority_quorum_score",
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
            "authority_lag_pressure_weight",
            "authority_check_staleness_pressure_weight",
            "authority_quorum_gap_pressure_weight",
            "contradiction_pressure_weight",
            "watch_lag_pressure_score",
            "block_lag_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventOutcomeAuthorityLagPressureReportInput:
    event_private_label: str
    outcome_observed_at: datetime
    authority_confirmed_at: datetime | None
    authority_checked_at: datetime
    authority_evidence_count: Decimal
    required_authority_evidence_count: Decimal
    contradiction_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventOutcomeAuthorityLagPressureReportInput:
            raise TypeError(
                "ResearchEventOutcomeAuthorityLagPressureReportInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeAuthorityLagPressureReportInput:
            raise ValueError(
                "input must be a ResearchEventOutcomeAuthorityLagPressureReportInput",
            )
        _require_private_label("event_private_label", self.event_private_label)
        object.__setattr__(
            self,
            "outcome_observed_at",
            _as_utc("outcome_observed_at", self.outcome_observed_at),
        )
        if self.authority_confirmed_at is not None:
            object.__setattr__(
                self,
                "authority_confirmed_at",
                _as_utc("authority_confirmed_at", self.authority_confirmed_at),
            )
        object.__setattr__(
            self,
            "authority_checked_at",
            _as_utc("authority_checked_at", self.authority_checked_at),
        )
        if (
            self.authority_confirmed_at is not None
            and self.authority_confirmed_at < self.outcome_observed_at
        ):
            raise ValueError("authority_confirmed_at must not be before outcome_observed_at")
        object.__setattr__(
            self,
            "authority_evidence_count",
            _normalize_nonnegative_count(
                "authority_evidence_count",
                self.authority_evidence_count,
            ),
        )
        object.__setattr__(
            self,
            "required_authority_evidence_count",
            _normalize_positive_count(
                "required_authority_evidence_count",
                self.required_authority_evidence_count,
            ),
        )
        if self.authority_evidence_count > self.required_authority_evidence_count:
            raise ValueError(
                "authority_evidence_count must not exceed "
                "required_authority_evidence_count",
            )
        object.__setattr__(
            self,
            "contradiction_pressure",
            _normalize_probability("contradiction_pressure", self.contradiction_pressure),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventOutcomeAuthorityLagPressureReportRow:
    event_public_label: str
    outcome_observed_at: datetime
    authority_confirmed_at: datetime | None
    authority_checked_at: datetime
    authority_lag_seconds: Decimal
    authority_check_age_seconds: Decimal
    authority_lag_pressure: Decimal
    authority_check_staleness_pressure: Decimal
    authority_evidence_count: Decimal
    required_authority_evidence_count: Decimal
    authority_quorum_score: Decimal
    authority_quorum_gap_pressure: Decimal
    contradiction_pressure: Decimal
    lag_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventOutcomeAuthorityLagPressureReportRow:
            raise TypeError(
                "ResearchEventOutcomeAuthorityLagPressureReportRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeAuthorityLagPressureReportRow:
            raise ValueError("row must be a ResearchEventOutcomeAuthorityLagPressureReportRow")
        _require_public_label("event_public_label", self.event_public_label)
        object.__setattr__(
            self,
            "outcome_observed_at",
            _as_utc("outcome_observed_at", self.outcome_observed_at),
        )
        if self.authority_confirmed_at is not None:
            object.__setattr__(
                self,
                "authority_confirmed_at",
                _as_utc("authority_confirmed_at", self.authority_confirmed_at),
            )
        object.__setattr__(
            self,
            "authority_checked_at",
            _as_utc("authority_checked_at", self.authority_checked_at),
        )
        for field_name in (
            "authority_lag_seconds",
            "authority_check_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_evidence_count",
            "required_authority_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_lag_pressure",
            "authority_check_staleness_pressure",
            "authority_quorum_score",
            "authority_quorum_gap_pressure",
            "contradiction_pressure",
            "lag_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventOutcomeAuthorityLagPressureReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_authority_lag_seconds: Decimal
    max_authority_check_age_seconds: Decimal
    min_authority_quorum_score: Decimal
    max_contradiction_pressure: Decimal
    average_lag_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventOutcomeAuthorityLagPressureReportRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventOutcomeAuthorityLagPressureReport:
            raise TypeError(
                "ResearchEventOutcomeAuthorityLagPressureReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeAuthorityLagPressureReport:
            raise ValueError("report must be a ResearchEventOutcomeAuthorityLagPressureReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_authority_lag_seconds",
            "max_authority_check_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_authority_quorum_score",
            "max_contradiction_pressure",
            "average_lag_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if self.public_digest == "":
            object.__setattr__(self, "public_digest", _report_public_digest(self))
        else:
            _require_sha256_digest("public_digest", self.public_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload(
            "report",
            _public_payload_value(asdict(self)),
        )


def build_research_event_outcome_authority_lag_pressure_report(
    items: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchEventOutcomeAuthorityLagPressureReportConfig,
) -> ResearchEventOutcomeAuthorityLagPressureReport:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable of report inputs")
    if type(config) is not ResearchEventOutcomeAuthorityLagPressureReportConfig:
        raise ValueError("config must be a ResearchEventOutcomeAuthorityLagPressureReportConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_inputs(items)
    scored_rows = tuple(
        _scored_row(item=item, generated_at=generated_at_utc, config=config)
        for item in normalized_items
    )
    sorted_scored_rows = tuple(
        sorted(
            scored_rows,
            key=lambda item: (
                STATUS_RANK[item[0].status],
                -item[0].lag_pressure_score,
                item[1],
            ),
        ),
    )
    rows = tuple(
        _with_public_label(row, index=index)
        for index, (row, _private_label) in enumerate(sorted_scored_rows, start=1)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchEventOutcomeAuthorityLagPressureReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        max_authority_lag_seconds=_max_decimal(row.authority_lag_seconds for row in rows),
        max_authority_check_age_seconds=_max_decimal(
            row.authority_check_age_seconds for row in rows
        ),
        min_authority_quorum_score=_min_probability(
            row.authority_quorum_score for row in rows
        ),
        max_contradiction_pressure=_max_probability(
            row.contradiction_pressure for row in rows
        ),
        average_lag_pressure_score=_average_probability(
            row.lag_pressure_score for row in rows
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
    )


def research_event_outcome_authority_lag_pressure_report_public_payload(
    report: ResearchEventOutcomeAuthorityLagPressureReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventOutcomeAuthorityLagPressureReport:
        raise ValueError("report must be a ResearchEventOutcomeAuthorityLagPressureReport")
    _require_hard_flags("report", report)
    if report.public_digest != _report_public_digest(report):
        raise ValueError("public_digest must match report fields")
    payload = _public_payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_event_outcome_authority_lag_pressure_public_payload(payload)
    return payload


def validate_research_event_outcome_authority_lag_pressure_public_payload(
    payload: Mapping[str, Any],
) -> bool:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    normalized_payload = dict(payload)
    _reject_unsafe_public_payload("payload", normalized_payload)
    public_digest = normalized_payload.get("public_digest")
    if type(public_digest) is not str:
        raise ValueError("public_digest must be a sha256 digest")
    _require_sha256_digest("public_digest", public_digest)
    if public_digest != _payload_public_digest(normalized_payload):
        raise ValueError("public_digest must match payload fields")
    return True


def research_event_outcome_authority_lag_pressure_report_public_digest(
    report: ResearchEventOutcomeAuthorityLagPressureReport,
) -> str:
    if type(report) is not ResearchEventOutcomeAuthorityLagPressureReport:
        raise ValueError("report must be a ResearchEventOutcomeAuthorityLagPressureReport")
    return _report_public_digest(report)


def _scored_row(
    *,
    item: ResearchEventOutcomeAuthorityLagPressureReportInput,
    generated_at: datetime,
    config: ResearchEventOutcomeAuthorityLagPressureReportConfig,
) -> tuple[ResearchEventOutcomeAuthorityLagPressureReportRow, str]:
    if type(item) is not ResearchEventOutcomeAuthorityLagPressureReportInput:
        raise ValueError(
            "items must contain ResearchEventOutcomeAuthorityLagPressureReportInput",
        )
    _require_hard_flags("input", item)
    if item.outcome_observed_at > generated_at:
        raise ValueError("outcome_observed_at must not be after generated_at")
    if item.authority_confirmed_at is not None and item.authority_confirmed_at > generated_at:
        raise ValueError("authority_confirmed_at must not be after generated_at")
    if item.authority_checked_at > generated_at:
        raise ValueError("authority_checked_at must not be after generated_at")

    authority_lag_seconds = (
        _duration_seconds(item.outcome_observed_at, generated_at)
        if item.authority_confirmed_at is None
        else _duration_seconds(item.outcome_observed_at, item.authority_confirmed_at)
    )
    authority_check_age_seconds = _duration_seconds(item.authority_checked_at, generated_at)
    authority_lag_pressure = _capped_ratio(
        authority_lag_seconds,
        config.max_watch_authority_lag_seconds,
    )
    authority_check_staleness_pressure = _capped_ratio(
        authority_check_age_seconds,
        config.max_watch_authority_check_age_seconds,
    )
    authority_quorum_score = _capped_ratio(
        item.authority_evidence_count,
        item.required_authority_evidence_count,
    )
    authority_quorum_gap_pressure = _q(ONE - authority_quorum_score)
    lag_pressure_score = _lag_pressure_score(
        authority_lag_pressure=authority_lag_pressure,
        authority_check_staleness_pressure=authority_check_staleness_pressure,
        authority_quorum_gap_pressure=authority_quorum_gap_pressure,
        contradiction_pressure=item.contradiction_pressure,
        config=config,
    )
    reason_codes = _row_reason_codes(
        authority_confirmed_at=item.authority_confirmed_at,
        authority_lag_seconds=authority_lag_seconds,
        authority_check_age_seconds=authority_check_age_seconds,
        authority_quorum_score=authority_quorum_score,
        contradiction_pressure=item.contradiction_pressure,
        lag_pressure_score=lag_pressure_score,
        config=config,
    )
    row = ResearchEventOutcomeAuthorityLagPressureReportRow(
        event_public_label="event-000",
        outcome_observed_at=item.outcome_observed_at,
        authority_confirmed_at=item.authority_confirmed_at,
        authority_checked_at=item.authority_checked_at,
        authority_lag_seconds=authority_lag_seconds,
        authority_check_age_seconds=authority_check_age_seconds,
        authority_lag_pressure=authority_lag_pressure,
        authority_check_staleness_pressure=authority_check_staleness_pressure,
        authority_evidence_count=item.authority_evidence_count,
        required_authority_evidence_count=item.required_authority_evidence_count,
        authority_quorum_score=authority_quorum_score,
        authority_quorum_gap_pressure=authority_quorum_gap_pressure,
        contradiction_pressure=item.contradiction_pressure,
        lag_pressure_score=lag_pressure_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )
    return row, item.event_private_label


def _with_public_label(
    row: ResearchEventOutcomeAuthorityLagPressureReportRow,
    *,
    index: int,
) -> ResearchEventOutcomeAuthorityLagPressureReportRow:
    return ResearchEventOutcomeAuthorityLagPressureReportRow(
        event_public_label=f"event-{index:03d}",
        outcome_observed_at=row.outcome_observed_at,
        authority_confirmed_at=row.authority_confirmed_at,
        authority_checked_at=row.authority_checked_at,
        authority_lag_seconds=row.authority_lag_seconds,
        authority_check_age_seconds=row.authority_check_age_seconds,
        authority_lag_pressure=row.authority_lag_pressure,
        authority_check_staleness_pressure=row.authority_check_staleness_pressure,
        authority_evidence_count=row.authority_evidence_count,
        required_authority_evidence_count=row.required_authority_evidence_count,
        authority_quorum_score=row.authority_quorum_score,
        authority_quorum_gap_pressure=row.authority_quorum_gap_pressure,
        contradiction_pressure=row.contradiction_pressure,
        lag_pressure_score=row.lag_pressure_score,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    authority_confirmed_at: datetime | None,
    authority_lag_seconds: Decimal,
    authority_check_age_seconds: Decimal,
    authority_quorum_score: Decimal,
    contradiction_pressure: Decimal,
    lag_pressure_score: Decimal,
    config: ResearchEventOutcomeAuthorityLagPressureReportConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if authority_confirmed_at is None:
        codes.append(AUTHORITY_CONFIRMATION_MISSING_REASON)
    if (
        authority_lag_seconds > config.max_watch_authority_lag_seconds
        or authority_confirmed_at is None
    ):
        codes.append(AUTHORITY_LAG_BLOCK_REASON)
    elif authority_lag_seconds > config.max_pass_authority_lag_seconds:
        codes.append(AUTHORITY_LAG_WATCH_REASON)
    if authority_check_age_seconds > config.max_watch_authority_check_age_seconds:
        codes.append(AUTHORITY_CHECK_STALENESS_BLOCK_REASON)
    elif authority_check_age_seconds > config.max_pass_authority_check_age_seconds:
        codes.append(AUTHORITY_CHECK_STALENESS_WATCH_REASON)
    if authority_quorum_score < config.min_watch_authority_quorum_score:
        codes.append(AUTHORITY_QUORUM_BLOCK_REASON)
    elif authority_quorum_score < config.min_pass_authority_quorum_score:
        codes.append(AUTHORITY_QUORUM_WATCH_REASON)
    if contradiction_pressure >= config.block_contradiction_pressure:
        codes.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif contradiction_pressure >= config.watch_contradiction_pressure:
        codes.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if lag_pressure_score >= config.block_lag_pressure_score:
        codes.append(BLOCK_REASON)
    elif any(code in BLOCK_REASONS for code in codes):
        codes.append(BLOCK_REASON)
    elif lag_pressure_score >= config.watch_lag_pressure_score:
        codes.append(WATCH_REASON)
    elif any(code in WATCH_REASONS for code in codes):
        codes.append(WATCH_REASON)
    else:
        codes.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _lag_pressure_score(
    *,
    authority_lag_pressure: Decimal,
    authority_check_staleness_pressure: Decimal,
    authority_quorum_gap_pressure: Decimal,
    contradiction_pressure: Decimal,
    config: ResearchEventOutcomeAuthorityLagPressureReportConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _q(
            authority_lag_pressure * config.authority_lag_pressure_weight
            + authority_check_staleness_pressure
            * config.authority_check_staleness_pressure_weight
            + authority_quorum_gap_pressure * config.authority_quorum_gap_pressure_weight
            + contradiction_pressure * config.contradiction_pressure_weight,
        )


def _report_reason_codes(
    rows: tuple[ResearchEventOutcomeAuthorityLagPressureReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON, BLOCK_REASON)
    present = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in present)


def _reason_code_counts(
    rows: tuple[ResearchEventOutcomeAuthorityLagPressureReportRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        (reason_code, _decimal_count(count))
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (REASON_CODE_PRIORITY.index(item[0]), item[0]),
        )
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchEventOutcomeAuthorityLagPressureReportRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    if finished_at < started_at:
        raise ValueError("finished_at must not be before started_at")
    delta = finished_at - started_at
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(delta.days) * Decimal("86400") + Decimal(delta.seconds)
        seconds += Decimal(delta.microseconds) / Decimal("1000000")
    return _q(seconds)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return _q(value)


def _average_probability(values: Iterable[Decimal]) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _q(sum(normalized_values, ZERO) / Decimal(len(normalized_values)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ZERO
    return max(normalized_values)


def _max_probability(values: Iterable[Decimal]) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ZERO
    return max(normalized_values)


def _min_probability(values: Iterable[Decimal]) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ONE
    return min(normalized_values)


def _report_public_digest(report: ResearchEventOutcomeAuthorityLagPressureReport) -> str:
    payload = _public_payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _payload_public_digest(payload)


def _payload_public_digest(payload: Mapping[str, Any]) -> str:
    digest_payload = {
        key: value for key, value in payload.items() if key != "public_digest"
    }
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _public_payload_value(value: Any, *, field_name: str = "") -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _public_payload_value(asdict(value), field_name=field_name)
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _public_payload_value(item, field_name=key)
        return ready
    if isinstance(value, tuple):
        return [_public_payload_value(item, field_name=field_name) for item in value]
    if isinstance(value, list):
        return [_public_payload_value(item, field_name=field_name) for item in value]
    if type(value) is Decimal:
        return _format_decimal(value, field_name=field_name)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload type: {type(value).__name__}")


def _format_decimal(value: Decimal, *, field_name: str) -> str:
    if field_name.endswith("_count") or field_name == "reason_code_counts":
        return format(value.quantize(COUNT_QUANTUM), "f")
    return format(value.quantize(VALUE_QUANTUM), "f")


def _validate_config(config: ResearchEventOutcomeAuthorityLagPressureReportConfig) -> None:
    if config.max_pass_authority_lag_seconds > config.max_watch_authority_lag_seconds:
        raise ValueError("max_pass_authority_lag_seconds must not exceed watch threshold")
    if (
        config.max_pass_authority_check_age_seconds
        > config.max_watch_authority_check_age_seconds
    ):
        raise ValueError(
            "max_pass_authority_check_age_seconds must not exceed watch threshold",
        )
    if config.min_pass_authority_quorum_score < config.min_watch_authority_quorum_score:
        raise ValueError("min_pass_authority_quorum_score must be at least watch threshold")
    if config.block_contradiction_pressure < config.watch_contradiction_pressure:
        raise ValueError("block_contradiction_pressure must be at least watch threshold")
    if config.block_lag_pressure_score <= config.watch_lag_pressure_score:
        raise ValueError("block_lag_pressure_score must exceed watch threshold")
    weights = (
        config.authority_lag_pressure_weight
        + config.authority_check_staleness_pressure_weight
        + config.authority_quorum_gap_pressure_weight
        + config.contradiction_pressure_weight
    )
    if weights != ONE:
        raise ValueError("pressure weights must sum to 1.000000")


def _validate_row(row: ResearchEventOutcomeAuthorityLagPressureReportRow) -> None:
    if row.authority_confirmed_at is not None and row.authority_confirmed_at < row.outcome_observed_at:
        raise ValueError("authority_confirmed_at must not be before outcome_observed_at")
    if row.authority_evidence_count > row.required_authority_evidence_count:
        raise ValueError(
            "authority_evidence_count must not exceed required_authority_evidence_count",
        )
    if row.authority_quorum_gap_pressure != _q(ONE - row.authority_quorum_score):
        raise ValueError("authority_quorum_gap_pressure must match authority_quorum_score")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchEventOutcomeAuthorityLagPressureReport) -> None:
    rows = report.rows
    if report.event_count != _decimal_count(len(rows)):
        raise ValueError("event_count must match rows")
    for status, expected_count in (
        ("pass", report.pass_count),
        ("watch", report.watch_count),
        ("block", report.block_count),
    ):
        if expected_count != _status_count(rows, status):
            raise ValueError(f"{status}_count must match rows")
    if report.max_authority_lag_seconds != _max_decimal(
        row.authority_lag_seconds for row in rows
    ):
        raise ValueError("max_authority_lag_seconds must match rows")
    if report.max_authority_check_age_seconds != _max_decimal(
        row.authority_check_age_seconds for row in rows
    ):
        raise ValueError("max_authority_check_age_seconds must match rows")
    if report.min_authority_quorum_score != _min_probability(
        row.authority_quorum_score for row in rows
    ):
        raise ValueError("min_authority_quorum_score must match rows")
    if report.max_contradiction_pressure != _max_probability(
        row.contradiction_pressure for row in rows
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.average_lag_pressure_score != _average_probability(
        row.lag_pressure_score for row in rows
    ):
        raise ValueError("average_lag_pressure_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.public_digest != _report_public_digest(report):
        raise ValueError("public_digest must match report fields")


def _normalize_inputs(
    values: Iterable[object],
) -> tuple[ResearchEventOutcomeAuthorityLagPressureReportInput, ...]:
    try:
        normalized_values = tuple(values)
    except TypeError as exc:
        raise ValueError("items must be an iterable of report inputs") from exc
    for value in normalized_values:
        if type(value) is not ResearchEventOutcomeAuthorityLagPressureReportInput:
            raise ValueError(
                "items must contain ResearchEventOutcomeAuthorityLagPressureReportInput",
            )
    labels = [value.event_private_label for value in normalized_values]
    if len(set(labels)) != len(labels):
        raise ValueError("event_private_label values must be unique")
    return normalized_values


def _normalize_rows(
    rows: object,
) -> tuple[ResearchEventOutcomeAuthorityLagPressureReportRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventOutcomeAuthorityLagPressureReportRow:
            raise ValueError(
                "rows must contain ResearchEventOutcomeAuthorityLagPressureReportRow",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(values: object) -> tuple[tuple[str, Decimal], ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for value in values:
        if type(value) is not tuple or len(value) != 2:
            raise ValueError("reason_code_counts entries must be pairs")
        reason_code, count = value
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(reason_code)
        normalized.append(
            (
                reason_code,
                _normalize_nonnegative_count("reason_code_count", count),
            ),
        )
    return tuple(normalized)


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in values:
        _require_reason_code(field_name, value)
    return tuple(
        sorted(values, key=lambda value: (REASON_CODE_PRIORITY.index(value), value)),
    )


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES!r}")


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal")
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


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be an exact Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_private_label(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or value == "":
        raise ValueError(f"{field_name} must be canonical")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_text(field_name, value)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text(f"{label}.{key}", key)
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload text in {label}")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "STATUSES",
    "ResearchEventOutcomeAuthorityLagPressureReportConfig",
    "ResearchEventOutcomeAuthorityLagPressureReportInput",
    "ResearchEventOutcomeAuthorityLagPressureReportRow",
    "ResearchEventOutcomeAuthorityLagPressureReport",
    "build_research_event_outcome_authority_lag_pressure_report",
    "research_event_outcome_authority_lag_pressure_report_public_payload",
    "research_event_outcome_authority_lag_pressure_report_public_digest",
    "validate_research_event_outcome_authority_lag_pressure_public_payload",
)
