"""Report-only resolution-claim quorum decay monitor."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_QUORUM_DECAY_REPORT_CONFIG_VERSION = (
    "research-event-resolution-claim-quorum-decay-report-v0"
)

DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_RANK = {
    STATUS_BLOCK: 0,
    STATUS_WATCH: 1,
    STATUS_PASS: 2,
}

PASS_REASON = "resolution_claim_quorum_decay_pass"
WATCH_REASON = "resolution_claim_quorum_decay_watch"
BLOCK_REASON = "resolution_claim_quorum_decay_block"
EMPTY_REASON = "resolution_claim_quorum_decay_empty"
MISSING_VERIFICATION_REASON = "missing_claim_verification_timestamp"
STALE_VERIFICATION_REASON = "claim_verification_timestamp_stale"
BELOW_QUORUM_REASON = "active_independent_source_quorum_below_required"
AT_FLOOR_REASON = "active_independent_source_quorum_at_floor"
HIGH_DECAY_REASON = "high_resolution_claim_quorum_decay"
MEDIUM_DECAY_REASON = "medium_resolution_claim_quorum_decay"
CONTRADICTION_REASON = "contradicted_resolution_claim_sources_present"

STATUS_REASON_CODES = (PASS_REASON, WATCH_REASON, BLOCK_REASON)
REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    EMPTY_REASON,
    MISSING_VERIFICATION_REASON,
    STALE_VERIFICATION_REASON,
    BELOW_QUORUM_REASON,
    AT_FLOOR_REASON,
    HIGH_DECAY_REASON,
    MEDIUM_DECAY_REASON,
    CONTRADICTION_REASON,
)
REASON_CODE_SET = frozenset(REASON_CODES)

PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "account",
        "balance",
        "broker",
        "trade",
        "trading",
        "order",
        "auth",
        "position",
        "sizing",
    ),
)
PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        "candidate",
        "market-alpha",
        "will-this-resolve",
        "http://",
        "https://",
        "postgresql://",
        "mysql://",
        "raw source text",
        "source text",
        "dsn=",
        "table_name",
        "wallet",
        "order",
        "trade",
        "position-sizing",
        "recommendation",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_QUORUM_DECAY_REPORT_CONFIG_VERSION",
    "ResearchEventResolutionClaimQuorumDecayConfig",
    "ResearchEventResolutionClaimQuorumDecayInput",
    "ResearchEventResolutionClaimQuorumDecayRow",
    "ResearchEventResolutionClaimQuorumDecayReasonCodeCount",
    "ResearchEventResolutionClaimQuorumDecayReport",
    "build_research_event_resolution_claim_quorum_decay_report",
    "research_event_resolution_claim_quorum_decay_report_payload",
    "validate_research_event_resolution_claim_quorum_decay_public_payload",
)


@dataclass(frozen=True)
class ResearchEventResolutionClaimQuorumDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_QUORUM_DECAY_REPORT_CONFIG_VERSION
    )
    required_active_independent_source_count: Decimal = Decimal("3.000000")
    watch_quorum_decay_score: Decimal = Decimal("0.250000")
    block_quorum_decay_score: Decimal = Decimal("0.500000")
    max_claim_verification_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionClaimQuorumDecayConfig, "config")
        _require_plain_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_QUORUM_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "required_active_independent_source_count",
            _count_decimal(
                "required_active_independent_source_count",
                self.required_active_independent_source_count,
            ),
        )
        if self.required_active_independent_source_count <= ZERO:
            raise ValueError("required_active_independent_source_count must be positive")
        object.__setattr__(
            self,
            "watch_quorum_decay_score",
            _probability_decimal("watch_quorum_decay_score", self.watch_quorum_decay_score),
        )
        object.__setattr__(
            self,
            "block_quorum_decay_score",
            _probability_decimal("block_quorum_decay_score", self.block_quorum_decay_score),
        )
        object.__setattr__(
            self,
            "max_claim_verification_age_seconds",
            _nonnegative_decimal(
                "max_claim_verification_age_seconds",
                self.max_claim_verification_age_seconds,
            ),
        )
        if self.block_quorum_decay_score <= self.watch_quorum_decay_score:
            raise ValueError("block_quorum_decay_score must exceed watch_quorum_decay_score")
        require_paper_only_flags("config", self)
        reject_unsafe_surface_fields("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionClaimQuorumDecayInput:
    event_ref_digest: str
    claim_ref_digest: str
    event_category: str
    claim_observed_at: datetime
    last_verified_at: datetime | None
    active_independent_source_count: Decimal
    stale_independent_source_count: Decimal
    contradicted_independent_source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionClaimQuorumDecayInput, "input")
        _require_digest_ref("event_ref_digest", self.event_ref_digest)
        _require_digest_ref("claim_ref_digest", self.claim_ref_digest)
        _require_plain_text("event_category", self.event_category)
        object.__setattr__(
            self,
            "claim_observed_at",
            _as_utc("claim_observed_at", self.claim_observed_at),
        )
        object.__setattr__(
            self,
            "last_verified_at",
            _optional_utc("last_verified_at", self.last_verified_at),
        )
        for field_name in (
            "active_independent_source_count",
            "stale_independent_source_count",
            "contradicted_independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("input", self)
        reject_unsafe_surface_fields("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionClaimQuorumDecayRow:
    event_ref_digest: str
    claim_ref_digest: str
    event_category: str
    claim_observed_at: datetime
    last_verified_at: datetime | None
    active_independent_source_count: Decimal
    stale_independent_source_count: Decimal
    contradicted_independent_source_count: Decimal
    required_active_independent_source_count: Decimal
    claim_age_seconds: Decimal
    last_verified_age_seconds: Decimal | None
    active_quorum_ratio: Decimal
    quorum_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionClaimQuorumDecayRow, "row")
        _require_digest_ref("event_ref_digest", self.event_ref_digest)
        _require_digest_ref("claim_ref_digest", self.claim_ref_digest)
        _require_plain_text("event_category", self.event_category)
        object.__setattr__(
            self,
            "claim_observed_at",
            _as_utc("claim_observed_at", self.claim_observed_at),
        )
        object.__setattr__(
            self,
            "last_verified_at",
            _optional_utc("last_verified_at", self.last_verified_at),
        )
        for field_name in (
            "active_independent_source_count",
            "stale_independent_source_count",
            "contradicted_independent_source_count",
            "required_active_independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_active_independent_source_count <= ZERO:
            raise ValueError("required_active_independent_source_count must be positive")
        object.__setattr__(
            self,
            "claim_age_seconds",
            _nonnegative_decimal("claim_age_seconds", self.claim_age_seconds),
        )
        object.__setattr__(
            self,
            "last_verified_age_seconds",
            _optional_nonnegative_decimal(
                "last_verified_age_seconds",
                self.last_verified_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "active_quorum_ratio",
            _probability_decimal("active_quorum_ratio", self.active_quorum_ratio),
        )
        object.__setattr__(
            self,
            "quorum_decay_score",
            _probability_decimal("quorum_decay_score", self.quorum_decay_score),
        )
        _require_choice("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        require_paper_only_flags("row", self)
        reject_unsafe_surface_fields("row", self)
        _validate_row_consistency(self)
        _set_or_validate_digest(self, "row")


@dataclass(frozen=True)
class ResearchEventResolutionClaimQuorumDecayReasonCodeCount:
    reason_code: str
    row_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionClaimQuorumDecayReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "row_count",
            _count_decimal("row_count", self.row_count),
        )
        require_paper_only_flags("reason code count", self)
        reject_unsafe_surface_fields("reason code count", self)


@dataclass(frozen=True)
class ResearchEventResolutionClaimQuorumDecayReport:
    generated_at: datetime
    config_version: str
    report_status: str
    claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_verification_count: Decimal
    below_quorum_count: Decimal
    contradicted_claim_count: Decimal
    stale_verification_count: Decimal
    max_quorum_decay_score: Decimal
    total_active_independent_source_count: Decimal
    total_stale_independent_source_count: Decimal
    total_contradicted_independent_source_count: Decimal
    rows: tuple[ResearchEventResolutionClaimQuorumDecayRow, ...]
    reason_code_counts: tuple[
        ResearchEventResolutionClaimQuorumDecayReasonCodeCount,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionClaimQuorumDecayReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_plain_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_QUORUM_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_choice("report_status", self.report_status, STATUSES)
        for field_name in (
            "claim_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_verification_count",
            "below_quorum_count",
            "contradicted_claim_count",
            "stale_verification_count",
            "total_active_independent_source_count",
            "total_stale_independent_source_count",
            "total_contradicted_independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_quorum_decay_score",
            _probability_decimal("max_quorum_decay_score", self.max_quorum_decay_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        require_paper_only_flags("report", self)
        reject_unsafe_surface_fields("report", self)
        _validate_report_consistency(self)
        _set_or_validate_digest(self, "report")


def build_research_event_resolution_claim_quorum_decay_report(
    rows: Iterable[ResearchEventResolutionClaimQuorumDecayInput],
    *,
    config: ResearchEventResolutionClaimQuorumDecayConfig,
    generated_at: datetime,
) -> ResearchEventResolutionClaimQuorumDecayReport:
    if type(config) is not ResearchEventResolutionClaimQuorumDecayConfig:
        raise ValueError("config must be ResearchEventResolutionClaimQuorumDecayConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_inputs(rows)
    report_rows = tuple(
        sorted(
            (
                _row_from_input(row, config=config, generated_at=generated_at_utc)
                for row in normalized_rows
            ),
            key=_row_sort_key,
        ),
    )
    claim_count = _decimal_from_int(len(report_rows))
    return ResearchEventResolutionClaimQuorumDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(report_rows),
        claim_count=claim_count,
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        missing_verification_count=_reason_count(report_rows, MISSING_VERIFICATION_REASON),
        below_quorum_count=_reason_count(report_rows, BELOW_QUORUM_REASON),
        contradicted_claim_count=_positive_count(
            row.contradicted_independent_source_count for row in report_rows
        ),
        stale_verification_count=_reason_count(report_rows, STALE_VERIFICATION_REASON),
        max_quorum_decay_score=max(
            (row.quorum_decay_score for row in report_rows),
            default=ZERO,
        ),
        total_active_independent_source_count=sum(
            (row.active_independent_source_count for row in report_rows),
            ZERO,
        ),
        total_stale_independent_source_count=sum(
            (row.stale_independent_source_count for row in report_rows),
            ZERO,
        ),
        total_contradicted_independent_source_count=sum(
            (row.contradicted_independent_source_count for row in report_rows),
            ZERO,
        ),
        rows=report_rows,
        reason_code_counts=_reason_code_counts(report_rows),
    )


def research_event_resolution_claim_quorum_decay_report_payload(
    report: ResearchEventResolutionClaimQuorumDecayReport,
) -> "FrozenJsonObject":
    if type(report) is not ResearchEventResolutionClaimQuorumDecayReport:
        raise ValueError(
            "report must be exactly ResearchEventResolutionClaimQuorumDecayReport",
        )
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    validate_research_event_resolution_claim_quorum_decay_public_payload(payload)
    return _freeze_json_object(payload)


def validate_research_event_resolution_claim_quorum_decay_public_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload("public payload", payload)
    current_digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", current_digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    canonical_payload = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected_digest = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    if current_digest != expected_digest:
        raise ValueError("derived_validation_digest must match public payload")
    return True


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _row_from_input(
    row: ResearchEventResolutionClaimQuorumDecayInput,
    *,
    config: ResearchEventResolutionClaimQuorumDecayConfig,
    generated_at: datetime,
) -> ResearchEventResolutionClaimQuorumDecayRow:
    if row.claim_observed_at > generated_at:
        raise ValueError("claim_observed_at must not be after generated_at")
    if row.last_verified_at is not None:
        if row.last_verified_at > generated_at:
            raise ValueError("last_verified_at must not be after generated_at")
        if row.last_verified_at < row.claim_observed_at:
            raise ValueError("last_verified_at must not be before claim_observed_at")
    active_quorum_ratio = _active_quorum_ratio(
        row.active_independent_source_count,
        config.required_active_independent_source_count,
    )
    quorum_decay_score = _quorum_decay_score(row)
    last_verified_age_seconds = (
        None
        if row.last_verified_at is None
        else _duration_seconds(row.last_verified_at, generated_at)
    )
    reason_codes = _row_reason_codes(
        row,
        config=config,
        last_verified_age_seconds=last_verified_age_seconds,
        quorum_decay_score=quorum_decay_score,
    )
    return ResearchEventResolutionClaimQuorumDecayRow(
        event_ref_digest=row.event_ref_digest,
        claim_ref_digest=row.claim_ref_digest,
        event_category=row.event_category,
        claim_observed_at=row.claim_observed_at,
        last_verified_at=row.last_verified_at,
        active_independent_source_count=row.active_independent_source_count,
        stale_independent_source_count=row.stale_independent_source_count,
        contradicted_independent_source_count=row.contradicted_independent_source_count,
        required_active_independent_source_count=(
            config.required_active_independent_source_count
        ),
        claim_age_seconds=_duration_seconds(row.claim_observed_at, generated_at),
        last_verified_age_seconds=last_verified_age_seconds,
        active_quorum_ratio=active_quorum_ratio,
        quorum_decay_score=quorum_decay_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchEventResolutionClaimQuorumDecayInput,
    *,
    config: ResearchEventResolutionClaimQuorumDecayConfig,
    last_verified_age_seconds: Decimal | None,
    quorum_decay_score: Decimal,
) -> tuple[str, ...]:
    detail_reasons: list[str] = []
    has_block_reason = False
    if row.last_verified_at is None:
        detail_reasons.append(MISSING_VERIFICATION_REASON)
        has_block_reason = True
    elif last_verified_age_seconds is not None:
        if last_verified_age_seconds > config.max_claim_verification_age_seconds:
            detail_reasons.append(STALE_VERIFICATION_REASON)
            has_block_reason = True
    if row.active_independent_source_count < config.required_active_independent_source_count:
        detail_reasons.append(BELOW_QUORUM_REASON)
        has_block_reason = True
    if quorum_decay_score >= config.block_quorum_decay_score:
        detail_reasons.append(HIGH_DECAY_REASON)
        has_block_reason = True
    elif quorum_decay_score >= config.watch_quorum_decay_score:
        detail_reasons.append(MEDIUM_DECAY_REASON)
    if row.active_independent_source_count == config.required_active_independent_source_count:
        detail_reasons.append(AT_FLOOR_REASON)
    if row.contradicted_independent_source_count > ZERO:
        detail_reasons.append(CONTRADICTION_REASON)
        has_block_reason = True
    if has_block_reason:
        return (BLOCK_REASON, *detail_reasons)
    if detail_reasons:
        return (WATCH_REASON, *detail_reasons)
    return (PASS_REASON,)


def _active_quorum_ratio(active_count: Decimal, required_count: Decimal) -> Decimal:
    return min(_ratio(active_count, required_count), ONE)


def _quorum_decay_score(row: ResearchEventResolutionClaimQuorumDecayInput) -> Decimal:
    decayed_count = (
        row.stale_independent_source_count + row.contradicted_independent_source_count
    )
    total_count = decayed_count + row.active_independent_source_count
    if total_count == ZERO:
        return ONE
    return _ratio(decayed_count, total_count)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == BLOCK_REASON:
        return STATUS_BLOCK
    if reason_codes[0] == WATCH_REASON:
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[ResearchEventResolutionClaimQuorumDecayRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _normalize_inputs(
    rows: Iterable[ResearchEventResolutionClaimQuorumDecayInput],
) -> tuple[ResearchEventResolutionClaimQuorumDecayInput, ...]:
    if isinstance(rows, (str, bytes, dict)):
        raise ValueError("rows must be an iterable of inputs")
    normalized = tuple(rows)
    seen_claim_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventResolutionClaimQuorumDecayInput:
            raise ValueError("rows must contain ResearchEventResolutionClaimQuorumDecayInput")
        require_paper_only_flags("input", row)
        if row.claim_ref_digest in seen_claim_refs:
            raise ValueError("claim_ref_digest values must be unique")
        seen_claim_refs.add(row.claim_ref_digest)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchEventResolutionClaimQuorumDecayRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_claim_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventResolutionClaimQuorumDecayRow:
            raise ValueError("rows must contain ResearchEventResolutionClaimQuorumDecayRow")
        require_paper_only_flags("row", row)
        if row.claim_ref_digest in seen_claim_refs:
            raise ValueError("rows claim_ref_digest values must be unique")
        seen_claim_refs.add(row.claim_ref_digest)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchEventResolutionClaimQuorumDecayReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    seen_reason_codes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventResolutionClaimQuorumDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventResolutionClaimQuorumDecayReasonCodeCount",
            )
        require_paper_only_flags("reason code count", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _row_sort_key(
    row: ResearchEventResolutionClaimQuorumDecayRow,
) -> tuple[int, Decimal, str, str, str]:
    return (
        STATUS_SORT_RANK[row.status],
        -row.quorum_decay_score,
        row.event_category,
        row.event_ref_digest,
        row.claim_ref_digest,
    )


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionClaimQuorumDecayRow, ...],
) -> tuple[ResearchEventResolutionClaimQuorumDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventResolutionClaimQuorumDecayReasonCodeCount(
                reason_code=EMPTY_REASON,
                row_count=ONE,
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchEventResolutionClaimQuorumDecayReasonCodeCount(
            reason_code=reason_code,
            row_count=count,
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[ResearchEventResolutionClaimQuorumDecayRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchEventResolutionClaimQuorumDecayRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_from_int(
        sum(1 for row in rows if reason_code in row.reason_codes),
    )


def _positive_count(values: Iterable[Decimal]) -> Decimal:
    return _decimal_from_int(sum(1 for value in values if value > ZERO))


def _validate_row_consistency(row: ResearchEventResolutionClaimQuorumDecayRow) -> None:
    if (row.last_verified_at is None) != (row.last_verified_age_seconds is None):
        raise ValueError("last_verified_age_seconds must match last_verified_at")
    if row.last_verified_at is not None and row.last_verified_at < row.claim_observed_at:
        raise ValueError("last_verified_at must not be before claim_observed_at")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.active_quorum_ratio != _active_quorum_ratio(
        row.active_independent_source_count,
        row.required_active_independent_source_count,
    ):
        raise ValueError("active_quorum_ratio must match source counts")
    input_row = ResearchEventResolutionClaimQuorumDecayInput(
        event_ref_digest=row.event_ref_digest,
        claim_ref_digest=row.claim_ref_digest,
        event_category=row.event_category,
        claim_observed_at=row.claim_observed_at,
        last_verified_at=row.last_verified_at,
        active_independent_source_count=row.active_independent_source_count,
        stale_independent_source_count=row.stale_independent_source_count,
        contradicted_independent_source_count=row.contradicted_independent_source_count,
    )
    if row.quorum_decay_score != _quorum_decay_score(input_row):
        raise ValueError("quorum_decay_score must match source counts")


def _validate_report_consistency(
    report: ResearchEventResolutionClaimQuorumDecayReport,
) -> None:
    expected_claim_count = _decimal_from_int(len(report.rows))
    expected_values = {
        "claim_count": expected_claim_count,
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
        "missing_verification_count": _reason_count(
            report.rows,
            MISSING_VERIFICATION_REASON,
        ),
        "below_quorum_count": _reason_count(report.rows, BELOW_QUORUM_REASON),
        "contradicted_claim_count": _positive_count(
            row.contradicted_independent_source_count for row in report.rows
        ),
        "stale_verification_count": _reason_count(report.rows, STALE_VERIFICATION_REASON),
        "max_quorum_decay_score": max(
            (row.quorum_decay_score for row in report.rows),
            default=ZERO,
        ),
        "total_active_independent_source_count": sum(
            (row.active_independent_source_count for row in report.rows),
            ZERO,
        ),
        "total_stale_independent_source_count": sum(
            (row.stale_independent_source_count for row in report.rows),
            ZERO,
        ),
        "total_contradicted_independent_source_count": sum(
            (row.contradicted_independent_source_count for row in report.rows),
            ZERO,
        ),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_reason_codes(value: object, *, allow_empty: bool) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        if allow_empty:
            return ()
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    if reason_codes[0] not in STATUS_REASON_CODES:
        raise ValueError("reason_codes must begin with a status reason")
    if reason_codes[0] == PASS_REASON and len(reason_codes) != 1:
        raise ValueError("pass reason_codes must stand alone")
    if reason_codes[0] != PASS_REASON and len(reason_codes) == 1:
        raise ValueError("watch or block reason_codes require detail reasons")
    return reason_codes


def _set_or_validate_digest(value: object, label: str) -> None:
    current_digest = getattr(value, "derived_validation_digest")
    if current_digest == "":
        object.__setattr__(
            value,
            "derived_validation_digest",
            _derived_validation_digest(value, label),
        )
        return
    _require_digest("derived_validation_digest", current_digest)
    if current_digest != _derived_validation_digest(value, label):
        raise ValueError("derived_validation_digest does not match payload")


def _derived_validation_digest(value: object, label: str) -> str:
    ready_value = _json_ready_without_digest(value)
    reject_unsafe_surface_fields(f"{label} digest payload", ready_value)
    _reject_public_payload(f"{label} digest payload", ready_value)
    canonical_payload = json.dumps(
        ready_value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready_without_digest(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass instance")
    ready = json_ready_no_floats(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    ready.pop("derived_validation_digest", None)
    return ready


def _reject_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in PUBLIC_KEY_FRAGMENTS):
                raise ValueError(f"unsafe public payload field in {label}: {key}")
            _reject_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(label, item)
        return
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, (int, float)):
        raise ValueError("unsafe public payload numeric values must be strings")
    if isinstance(value, str):
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in PUBLIC_VALUE_FRAGMENTS):
            raise ValueError(f"unsafe public payload value in {label}")


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    start = _as_utc("started_at", started_at)
    finish = _as_utc("finished_at", finished_at)
    if finish < start:
        raise ValueError("duration seconds must be nonnegative")
    delta = finish - start
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize(seconds)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    return _quantize(numerator / denominator)


def _decimal_from_int(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _count_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _optional_nonnegative_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _nonnegative_decimal(name, value)


def _probability_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be quantizable") from exc


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(name, value)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_plain_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a plain str")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_digest_ref(name: str, value: object) -> None:
    _require_plain_text(name, value)
    if not value.startswith("sha256:"):
        raise ValueError(f"{name} must be a sha256 digest reference")
    digest = value.removeprefix("sha256:")
    _require_digest(name, digest)


def _require_choice(name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        joined_choices = ", ".join(choices)
        raise ValueError(f"{name} must be one of: {joined_choices}")


def _require_reason_code(name: str, value: object) -> None:
    _require_plain_text(name, value)
    if value not in REASON_CODE_SET:
        raise ValueError(f"{name} must be a known reason code")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a 64-character hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be lowercase hex")
