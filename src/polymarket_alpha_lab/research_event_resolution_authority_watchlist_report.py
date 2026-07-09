"""Report-only event resolution authority watchlist scorer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_WATCHLIST_CONFIG_VERSION = (
    "research-event-resolution-authority-watchlist-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_EVENT_RESOLUTION_AUTHORITY_WATCHLIST_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)
STATUSES = frozenset(RESEARCH_EVENT_RESOLUTION_AUTHORITY_WATCHLIST_STATUSES)
STATUS_RANK = {
    STATUS_BLOCK: Decimal("0"),
    STATUS_WATCH: Decimal("1"),
    STATUS_PASS: Decimal("2"),
}

AUTHORITY_RELIABILITY_SCORES = {
    "official": Decimal("1.000000"),
    "primary": Decimal("0.850000"),
    "proxy": Decimal("0.600000"),
    "unknown": Decimal("0.000000"),
}

REASON_CODE_SEQUENCE = (
    "authority_check_missing",
    "authority_stale_block",
    "authority_stale_watch",
    "low_authority_block",
    "low_authority_watch",
    "unresolved_dependency_block",
    "unresolved_dependency_watch",
    "conflict_signal_block",
    "conflict_signal_watch",
    "coverage_gap_block",
    "coverage_gap_watch",
    "deadline_pressure_block",
    "deadline_pressure_watch",
    "authority_recent",
    "coverage_sufficient",
    "authority_watchlist_pass",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "http",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    ),
)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityWatchlistConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_WATCHLIST_CONFIG_VERSION
    watch_age_to_cadence_ratio: Decimal = Decimal("1.000000")
    block_age_to_cadence_ratio: Decimal = Decimal("2.000000")
    watch_dependency_count: Decimal = Decimal("1.000000")
    block_dependency_count: Decimal = Decimal("3.000000")
    watch_conflict_count: Decimal = Decimal("1.000000")
    block_conflict_count: Decimal = Decimal("3.000000")
    minimum_pass_verification_coverage: Decimal = Decimal("0.800000")
    block_verification_coverage: Decimal = Decimal("0.250000")
    minimum_pass_authority_score: Decimal = Decimal("0.800000")
    block_authority_score: Decimal = Decimal("0.250000")
    watch_deadline_proximity_seconds: Decimal = Decimal("86400.000000")
    block_deadline_proximity_seconds: Decimal = Decimal("3600.000000")
    stale_weight: Decimal = Decimal("0.300000")
    authority_weight: Decimal = Decimal("0.150000")
    dependency_weight: Decimal = Decimal("0.190000")
    conflict_weight: Decimal = Decimal("0.082500")
    coverage_weight: Decimal = Decimal("0.150000")
    deadline_weight: Decimal = Decimal("0.090000")
    watch_score_threshold: Decimal = Decimal("0.250000")
    block_score_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityWatchlistConfig:
            raise TypeError(
                "ResearchEventResolutionAuthorityWatchlistConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionAuthorityWatchlistConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_WATCHLIST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_age_to_cadence_ratio",
            "block_age_to_cadence_ratio",
            "watch_dependency_count",
            "block_dependency_count",
            "watch_conflict_count",
            "block_conflict_count",
            "watch_deadline_proximity_seconds",
            "block_deadline_proximity_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_verification_coverage",
            "block_verification_coverage",
            "minimum_pass_authority_score",
            "block_authority_score",
            "stale_weight",
            "authority_weight",
            "dependency_weight",
            "conflict_weight",
            "coverage_weight",
            "deadline_weight",
            "watch_score_threshold",
            "block_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityWatchlistInput:
    event_reference: str
    authority_reference: str
    authority_tier: str
    last_checked_at: datetime | None
    expected_check_cadence_seconds: Decimal
    unresolved_dependency_count: Decimal
    conflict_signal_count: Decimal
    verification_coverage: Decimal
    deadline_at: datetime | None
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityWatchlistInput:
            raise TypeError(
                "ResearchEventResolutionAuthorityWatchlistInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_private_reference("event_reference", self.event_reference)
        _require_private_reference("authority_reference", self.authority_reference)
        _require_authority_tier("authority_tier", self.authority_tier)
        object.__setattr__(
            self,
            "last_checked_at",
            _as_optional_utc("last_checked_at", self.last_checked_at),
        )
        object.__setattr__(
            self,
            "expected_check_cadence_seconds",
            _require_positive_decimal(
                "expected_check_cadence_seconds",
                self.expected_check_cadence_seconds,
            ),
        )
        for field_name in ("unresolved_dependency_count", "conflict_signal_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "verification_coverage",
            _require_ratio_decimal("verification_coverage", self.verification_coverage),
        )
        object.__setattr__(
            self,
            "deadline_at",
            _as_optional_utc("deadline_at", self.deadline_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityWatchlistRow:
    event_digest: str
    authority_digest: str
    authority_tier: str
    authority_reliability_score: Decimal
    last_checked_at: datetime | None
    check_age_seconds: Decimal | None
    expected_check_cadence_seconds: Decimal
    age_to_cadence_ratio: Decimal | None
    unresolved_dependency_count: Decimal
    conflict_signal_count: Decimal
    verification_coverage: Decimal
    deadline_at: datetime | None
    deadline_proximity_seconds: Decimal | None
    watchlist_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityWatchlistRow:
            raise TypeError(
                "ResearchEventResolutionAuthorityWatchlistRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_sha256_digest("event_digest", self.event_digest)
        _require_sha256_digest("authority_digest", self.authority_digest)
        _require_authority_tier("authority_tier", self.authority_tier)
        object.__setattr__(
            self,
            "authority_reliability_score",
            _require_ratio_decimal(
                "authority_reliability_score",
                self.authority_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "last_checked_at",
            _as_optional_utc("last_checked_at", self.last_checked_at),
        )
        object.__setattr__(
            self,
            "check_age_seconds",
            _require_optional_nonnegative_decimal(
                "check_age_seconds",
                self.check_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "expected_check_cadence_seconds",
            _require_positive_decimal(
                "expected_check_cadence_seconds",
                self.expected_check_cadence_seconds,
            ),
        )
        object.__setattr__(
            self,
            "age_to_cadence_ratio",
            _require_optional_nonnegative_decimal(
                "age_to_cadence_ratio",
                self.age_to_cadence_ratio,
            ),
        )
        for field_name in ("unresolved_dependency_count", "conflict_signal_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "verification_coverage",
            _require_ratio_decimal("verification_coverage", self.verification_coverage),
        )
        object.__setattr__(
            self,
            "deadline_at",
            _as_optional_utc("deadline_at", self.deadline_at),
        )
        object.__setattr__(
            self,
            "deadline_proximity_seconds",
            _require_optional_nonnegative_decimal(
                "deadline_proximity_seconds",
                self.deadline_proximity_seconds,
            ),
        )
        object.__setattr__(
            self,
            "watchlist_score",
            _require_ratio_decimal("watchlist_score", self.watchlist_score),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityWatchlistReport:
    generated_at: datetime
    config_version: str
    status: str
    authority_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_or_missing_count: Decimal
    low_coverage_count: Decimal
    average_watchlist_score: Decimal
    highest_watchlist_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventResolutionAuthorityWatchlistRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityWatchlistReport:
            raise TypeError(
                "ResearchEventResolutionAuthorityWatchlistReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionAuthorityWatchlistReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_WATCHLIST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "authority_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_or_missing_count",
            "low_coverage_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_watchlist_score", "highest_watchlist_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _derived_validation_digest(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_event_resolution_authority_watchlist_report(
    watch_items: Sequence[ResearchEventResolutionAuthorityWatchlistInput],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionAuthorityWatchlistConfig | None = None,
) -> ResearchEventResolutionAuthorityWatchlistReport:
    if config is None:
        config = ResearchEventResolutionAuthorityWatchlistConfig()
    if type(config) is not ResearchEventResolutionAuthorityWatchlistConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionAuthorityWatchlistConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(watch_items)
    rows = tuple(
        sorted(
            (_row_from_input(item, generated_at=generated_at, config=config) for item in normalized),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "authority_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "stale_or_missing_count": _stale_or_missing_count(rows, config),
        "low_coverage_count": _low_coverage_count(rows, config),
        "average_watchlist_score": _average(tuple(row.watchlist_score for row in rows)),
        "highest_watchlist_score": _highest_watchlist_score(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionAuthorityWatchlistReport(
        **values,
        derived_validation_digest=_derived_validation_digest(values),
    )


def research_event_resolution_authority_watchlist_report_payload(
    report: ResearchEventResolutionAuthorityWatchlistReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionAuthorityWatchlistReport:
        raise ValueError(
            "report must be a ResearchEventResolutionAuthorityWatchlistReport",
        )
    _require_hard_flags("report", report)
    validate_research_event_resolution_authority_watchlist_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def research_event_resolution_authority_watchlist_report_json(
    report: ResearchEventResolutionAuthorityWatchlistReport,
) -> str:
    payload = research_event_resolution_authority_watchlist_report_payload(report)
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def research_event_resolution_authority_watchlist_report_digest(
    report: ResearchEventResolutionAuthorityWatchlistReport,
) -> str:
    if type(report) is not ResearchEventResolutionAuthorityWatchlistReport:
        raise ValueError(
            "report must be a ResearchEventResolutionAuthorityWatchlistReport",
        )
    _validate_public_report_contract(report)
    return _derived_validation_digest(_report_values_without_digest(report))


def validate_research_event_resolution_authority_watchlist_digest(
    report: ResearchEventResolutionAuthorityWatchlistReport,
) -> None:
    expected = research_event_resolution_authority_watchlist_report_digest(report)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match report payload")


def _row_from_input(
    item: ResearchEventResolutionAuthorityWatchlistInput,
    *,
    generated_at: datetime,
    config: ResearchEventResolutionAuthorityWatchlistConfig,
) -> ResearchEventResolutionAuthorityWatchlistRow:
    if item.last_checked_at is not None and item.last_checked_at > generated_at:
        raise ValueError("last_checked_at must not be after generated_at")
    if item.deadline_at is not None and item.deadline_at < generated_at:
        raise ValueError("deadline_at must not be before generated_at")
    check_age_seconds = (
        None if item.last_checked_at is None else _seconds_between(generated_at, item.last_checked_at)
    )
    age_to_cadence_ratio = (
        None
        if check_age_seconds is None
        else _ratio(check_age_seconds, item.expected_check_cadence_seconds)
    )
    deadline_proximity_seconds = (
        None if item.deadline_at is None else _seconds_between(item.deadline_at, generated_at)
    )
    authority_reliability_score = AUTHORITY_RELIABILITY_SCORES[item.authority_tier]
    watchlist_score = _watchlist_score(
        authority_reliability_score=authority_reliability_score,
        age_to_cadence_ratio=age_to_cadence_ratio,
        unresolved_dependency_count=item.unresolved_dependency_count,
        conflict_signal_count=item.conflict_signal_count,
        verification_coverage=item.verification_coverage,
        deadline_proximity_seconds=deadline_proximity_seconds,
        config=config,
    )
    status = _row_status(
        authority_reliability_score=authority_reliability_score,
        age_to_cadence_ratio=age_to_cadence_ratio,
        unresolved_dependency_count=item.unresolved_dependency_count,
        conflict_signal_count=item.conflict_signal_count,
        verification_coverage=item.verification_coverage,
        deadline_proximity_seconds=deadline_proximity_seconds,
        watchlist_score=watchlist_score,
        config=config,
    )
    return ResearchEventResolutionAuthorityWatchlistRow(
        event_digest=_digest_private_reference(item.event_reference),
        authority_digest=_digest_private_reference(item.authority_reference),
        authority_tier=item.authority_tier,
        authority_reliability_score=authority_reliability_score,
        last_checked_at=item.last_checked_at,
        check_age_seconds=check_age_seconds,
        expected_check_cadence_seconds=item.expected_check_cadence_seconds,
        age_to_cadence_ratio=age_to_cadence_ratio,
        unresolved_dependency_count=item.unresolved_dependency_count,
        conflict_signal_count=item.conflict_signal_count,
        verification_coverage=item.verification_coverage,
        deadline_at=item.deadline_at,
        deadline_proximity_seconds=deadline_proximity_seconds,
        watchlist_score=watchlist_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            authority_reliability_score=authority_reliability_score,
            age_to_cadence_ratio=age_to_cadence_ratio,
            unresolved_dependency_count=item.unresolved_dependency_count,
            conflict_signal_count=item.conflict_signal_count,
            verification_coverage=item.verification_coverage,
            deadline_proximity_seconds=deadline_proximity_seconds,
            input_reason_codes=item.reason_codes,
            config=config,
        ),
    )


def _watchlist_score(
    *,
    authority_reliability_score: Decimal,
    age_to_cadence_ratio: Decimal | None,
    unresolved_dependency_count: Decimal,
    conflict_signal_count: Decimal,
    verification_coverage: Decimal,
    deadline_proximity_seconds: Decimal | None,
    config: ResearchEventResolutionAuthorityWatchlistConfig,
) -> Decimal:
    stale_risk = ONE if age_to_cadence_ratio is None else min(
        _ratio(age_to_cadence_ratio, config.block_age_to_cadence_ratio),
        ONE,
    )
    authority_risk = ONE - authority_reliability_score
    dependency_risk = min(_ratio(unresolved_dependency_count, config.block_dependency_count), ONE)
    conflict_risk = min(_ratio(conflict_signal_count, config.block_conflict_count), ONE)
    coverage_risk = ONE - verification_coverage
    deadline_risk = _deadline_risk(deadline_proximity_seconds, config)
    score = (
        stale_risk * config.stale_weight
        + authority_risk * config.authority_weight
        + dependency_risk * config.dependency_weight
        + conflict_risk * config.conflict_weight
        + coverage_risk * config.coverage_weight
        + deadline_risk * config.deadline_weight
    )
    return _clamp_ratio(score)


def _deadline_risk(
    deadline_proximity_seconds: Decimal | None,
    config: ResearchEventResolutionAuthorityWatchlistConfig,
) -> Decimal:
    if deadline_proximity_seconds is None:
        return ZERO
    if deadline_proximity_seconds <= config.block_deadline_proximity_seconds:
        return ONE
    if deadline_proximity_seconds <= config.watch_deadline_proximity_seconds:
        return Decimal("0.500000")
    return ZERO


def _row_status(
    *,
    authority_reliability_score: Decimal,
    age_to_cadence_ratio: Decimal | None,
    unresolved_dependency_count: Decimal,
    conflict_signal_count: Decimal,
    verification_coverage: Decimal,
    deadline_proximity_seconds: Decimal | None,
    watchlist_score: Decimal,
    config: ResearchEventResolutionAuthorityWatchlistConfig,
) -> str:
    if (
        age_to_cadence_ratio is None
        or age_to_cadence_ratio >= config.block_age_to_cadence_ratio
        or authority_reliability_score <= config.block_authority_score
        or unresolved_dependency_count >= config.block_dependency_count
        or conflict_signal_count >= config.block_conflict_count
        or verification_coverage <= config.block_verification_coverage
        or (
            deadline_proximity_seconds is not None
            and deadline_proximity_seconds <= config.block_deadline_proximity_seconds
        )
        or watchlist_score >= config.block_score_threshold
    ):
        return STATUS_BLOCK
    if (
        age_to_cadence_ratio >= config.watch_age_to_cadence_ratio
        or authority_reliability_score < config.minimum_pass_authority_score
        or unresolved_dependency_count >= config.watch_dependency_count
        or conflict_signal_count >= config.watch_conflict_count
        or verification_coverage < config.minimum_pass_verification_coverage
        or (
            deadline_proximity_seconds is not None
            and deadline_proximity_seconds <= config.watch_deadline_proximity_seconds
        )
        or watchlist_score >= config.watch_score_threshold
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    status: str,
    authority_reliability_score: Decimal,
    age_to_cadence_ratio: Decimal | None,
    unresolved_dependency_count: Decimal,
    conflict_signal_count: Decimal,
    verification_coverage: Decimal,
    deadline_proximity_seconds: Decimal | None,
    input_reason_codes: tuple[str, ...],
    config: ResearchEventResolutionAuthorityWatchlistConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = list(input_reason_codes)
    if age_to_cadence_ratio is None:
        reason_codes.append("authority_check_missing")
    elif age_to_cadence_ratio >= config.block_age_to_cadence_ratio:
        reason_codes.append("authority_stale_block")
    elif age_to_cadence_ratio >= config.watch_age_to_cadence_ratio:
        reason_codes.append("authority_stale_watch")
    elif status == STATUS_PASS:
        reason_codes.append("authority_recent")
    if authority_reliability_score <= config.block_authority_score:
        reason_codes.append("low_authority_block")
    elif authority_reliability_score < config.minimum_pass_authority_score:
        reason_codes.append("low_authority_watch")
    if unresolved_dependency_count >= config.block_dependency_count:
        reason_codes.append("unresolved_dependency_block")
    elif unresolved_dependency_count >= config.watch_dependency_count:
        reason_codes.append("unresolved_dependency_watch")
    if conflict_signal_count >= config.block_conflict_count:
        reason_codes.append("conflict_signal_block")
    elif conflict_signal_count >= config.watch_conflict_count:
        reason_codes.append("conflict_signal_watch")
    if verification_coverage <= config.block_verification_coverage:
        reason_codes.append("coverage_gap_block")
    elif verification_coverage < config.minimum_pass_verification_coverage:
        reason_codes.append("coverage_gap_watch")
    elif status == STATUS_PASS:
        reason_codes.append("coverage_sufficient")
    if deadline_proximity_seconds is not None:
        if deadline_proximity_seconds <= config.block_deadline_proximity_seconds:
            reason_codes.append("deadline_pressure_block")
        elif deadline_proximity_seconds <= config.watch_deadline_proximity_seconds:
            reason_codes.append("deadline_pressure_watch")
    if status == STATUS_PASS:
        reason_codes.append("authority_watchlist_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_config(config: ResearchEventResolutionAuthorityWatchlistConfig) -> None:
    if config.block_age_to_cadence_ratio <= config.watch_age_to_cadence_ratio:
        raise ValueError("block_age_to_cadence_ratio must exceed watch threshold")
    if config.block_dependency_count < config.watch_dependency_count:
        raise ValueError("block_dependency_count must meet watch threshold")
    if config.block_conflict_count < config.watch_conflict_count:
        raise ValueError("block_conflict_count must meet watch threshold")
    if config.block_verification_coverage >= config.minimum_pass_verification_coverage:
        raise ValueError("block_verification_coverage must be below pass threshold")
    if config.block_authority_score >= config.minimum_pass_authority_score:
        raise ValueError("block_authority_score must be below pass threshold")
    if config.block_deadline_proximity_seconds > config.watch_deadline_proximity_seconds:
        raise ValueError("block deadline threshold must not exceed watch threshold")
    if config.block_score_threshold <= config.watch_score_threshold:
        raise ValueError("block_score_threshold must exceed watch threshold")


def _validate_row_consistency(row: ResearchEventResolutionAuthorityWatchlistRow) -> None:
    if row.status == STATUS_PASS and "authority_watchlist_pass" not in row.reason_codes:
        raise ValueError("pass rows must include authority_watchlist_pass")
    if row.status == STATUS_BLOCK:
        block_reasons = {
            "authority_check_missing",
            "authority_stale_block",
            "low_authority_block",
            "unresolved_dependency_block",
            "conflict_signal_block",
            "coverage_gap_block",
            "deadline_pressure_block",
        }
        if not any(reason_code in row.reason_codes for reason_code in block_reasons):
            raise ValueError("block rows must include a block reason")


def _validate_report_consistency(report: ResearchEventResolutionAuthorityWatchlistReport) -> None:
    if report.authority_count != _count_decimal(len(report.rows)):
        raise ValueError("authority_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.authority_count:
        raise ValueError("status counts must match authority_count")
    if report.average_watchlist_score != _average(
        tuple(row.watchlist_score for row in report.rows),
    ):
        raise ValueError("average_watchlist_score must match rows")
    if report.highest_watchlist_score != _highest_watchlist_score(report.rows):
        raise ValueError("highest_watchlist_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _validate_public_report_contract(
    report: ResearchEventResolutionAuthorityWatchlistReport,
) -> None:
    _require_hard_flags("report", report)
    _require_status("status", report.status)
    if report.reason_codes != _normalize_reason_codes(report.reason_codes):
        raise ValueError("reason_codes must use canonical order")
    if report.rows != _normalize_rows(report.rows):
        raise ValueError("rows must use canonical order")
    _validate_report_consistency(report)
    _reject_unsafe_public_payload("report", report)


def _normalize_inputs(
    value: Sequence[ResearchEventResolutionAuthorityWatchlistInput],
) -> tuple[ResearchEventResolutionAuthorityWatchlistInput, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("watch_items must be a sequence")
    normalized: list[ResearchEventResolutionAuthorityWatchlistInput] = []
    for item in value:
        if type(item) is not ResearchEventResolutionAuthorityWatchlistInput:
            raise ValueError(
                "watch_items must contain ResearchEventResolutionAuthorityWatchlistInput",
            )
        _require_hard_flags("input", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                _digest_private_reference(item.event_reference),
                _digest_private_reference(item.authority_reference),
            ),
        ),
    )


def _normalize_rows(
    value: Sequence[ResearchEventResolutionAuthorityWatchlistRow],
) -> tuple[ResearchEventResolutionAuthorityWatchlistRow, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchEventResolutionAuthorityWatchlistRow] = []
    for row in value:
        if type(row) is not ResearchEventResolutionAuthorityWatchlistRow:
            raise ValueError("rows must contain ResearchEventResolutionAuthorityWatchlistRow")
        _require_hard_flags("row", row)
        if row.reason_codes != _normalize_reason_codes(row.reason_codes):
            raise ValueError("row reason_codes must use canonical order")
        _validate_row_consistency(row)
        _reject_unsafe_public_payload("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(row: ResearchEventResolutionAuthorityWatchlistRow) -> tuple[Decimal, Decimal, str]:
    return (STATUS_RANK[row.status], -row.watchlist_score, row.event_digest)


def _status_count(
    rows: tuple[ResearchEventResolutionAuthorityWatchlistRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _stale_or_missing_count(
    rows: tuple[ResearchEventResolutionAuthorityWatchlistRow, ...],
    config: ResearchEventResolutionAuthorityWatchlistConfig,
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if row.age_to_cadence_ratio is None
            or row.age_to_cadence_ratio >= config.watch_age_to_cadence_ratio
        ),
    )


def _low_coverage_count(
    rows: tuple[ResearchEventResolutionAuthorityWatchlistRow, ...],
    config: ResearchEventResolutionAuthorityWatchlistConfig,
) -> Decimal:
    return _count_decimal(
        sum(row.verification_coverage < config.minimum_pass_verification_coverage for row in rows),
    )


def _report_status(rows: tuple[ResearchEventResolutionAuthorityWatchlistRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionAuthorityWatchlistRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("authority_watchlist_pass",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _quantize_decimal(ZERO)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(sum(values, ZERO) / Decimal(len(values)))


def _highest_watchlist_score(
    rows: tuple[ResearchEventResolutionAuthorityWatchlistRow, ...],
) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    return max(row.watchlist_score for row in rows)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    later = _as_utc("later", later)
    earlier = _as_utc("earlier", earlier)
    if earlier > later:
        raise ValueError("earlier datetime must not be after later datetime")
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return _quantize_decimal(seconds)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return _quantize_decimal(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize_decimal(value)
    if normalized < ZERO:
        return _quantize_decimal(ZERO)
    if normalized > ONE:
        return _quantize_decimal(ONE)
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        if normalized != normalized.to_integral_value(rounding=ROUND_HALF_UP):
            raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain a canonical string")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_authority_tier(field_name: str, value: object) -> str:
    if type(value) is not str or value not in AUTHORITY_RELIABILITY_SCORES:
        raise ValueError(f"{field_name} must be a supported authority tier")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    *,
    allow_any_safe: bool = False,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    unique: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if not allow_any_safe and reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in unique:
            unique.append(reason_code)
    ordered = [
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in unique
    ]
    ordered.extend(sorted(reason_code for reason_code in unique if reason_code not in ordered))
    return tuple(ordered)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _digest_private_reference(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchEventResolutionAuthorityWatchlistReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _derived_validation_digest(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


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
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
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
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    normalized = key.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload key at {path}: {key}")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    normalized = value.lower()
    if "://" in normalized or any(
        fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS
    ):
        if path == "reason_code":
            raise ValueError("reason_code contains unsafe text")
        raise ValueError(f"unsafe public payload value at {path}")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_WATCHLIST_CONFIG_VERSION",
    "RESEARCH_EVENT_RESOLUTION_AUTHORITY_WATCHLIST_STATUSES",
    "ResearchEventResolutionAuthorityWatchlistConfig",
    "ResearchEventResolutionAuthorityWatchlistInput",
    "ResearchEventResolutionAuthorityWatchlistReport",
    "ResearchEventResolutionAuthorityWatchlistRow",
    "build_research_event_resolution_authority_watchlist_report",
    "research_event_resolution_authority_watchlist_report_digest",
    "research_event_resolution_authority_watchlist_report_json",
    "research_event_resolution_authority_watchlist_report_payload",
    "validate_research_event_resolution_authority_watchlist_digest",
)
