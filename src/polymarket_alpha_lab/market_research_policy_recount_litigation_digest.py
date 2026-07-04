"""Pure Phase 1 policy recount litigation digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_RECOUNT_LITIGATION_DIGEST_CONFIG_VERSION = (
    "market-research-policy-recount-litigation-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_policy_recount_litigation_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
UNRESOLVED_FILINGS_REASON = f"{REASON_PREFIX}unresolved_filings"
UNCERTIFIED_RESULT_REASON = f"{REASON_PREFIX}uncertified_result"
RECOUNT_MARGIN_REASON = f"{REASON_PREFIX}recount_margin"
LITIGATION_ACTIVITY_REASON = f"{REASON_PREFIX}litigation_activity"
STALE_EVIDENCE_REASON = f"{REASON_PREFIX}stale_evidence"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

ROW_REASON_CODE_SEQUENCE = (
    UNRESOLVED_FILINGS_REASON,
    UNCERTIFIED_RESULT_REASON,
    RECOUNT_MARGIN_REASON,
    LITIGATION_ACTIVITY_REASON,
    STALE_EVIDENCE_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    UNRESOLVED_FILINGS_REASON,
    UNCERTIFIED_RESULT_REASON,
    RECOUNT_MARGIN_REASON,
    LITIGATION_ACTIVITY_REASON,
    STALE_EVIDENCE_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_policy_recount_litigation_digest",
    STATUS_WATCH: "watch_report_only_market_research_policy_recount_litigation_digest",
    STATUS_BLOCKED: "block_report_only_market_research_policy_recount_litigation_digest",
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_RECOUNT_LITIGATION_DIGEST_CONFIG_VERSION",
    "MarketResearchPolicyRecountLitigationDigestConfig",
    "MarketResearchPolicyRecountLitigationDigestInputRow",
    "MarketResearchPolicyRecountLitigationDigestReasonCodeCount",
    "MarketResearchPolicyRecountLitigationDigestReport",
    "MarketResearchPolicyRecountLitigationDigestRow",
    "build_market_research_policy_recount_litigation_digest",
    "market_research_policy_recount_litigation_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPolicyRecountLitigationDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_RECOUNT_LITIGATION_DIGEST_CONFIG_VERSION
    )
    max_evidence_age_seconds: Decimal = Decimal("21600.000000")
    min_source_count: Decimal = Decimal("2.000000")
    recount_margin_watch_ratio: Decimal = Decimal("0.001000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyRecountLitigationDigestConfig:
            raise TypeError(
                "MarketResearchPolicyRecountLitigationDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyRecountLitigationDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchPolicyRecountLitigationDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_RECOUNT_LITIGATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in (
            "max_evidence_age_seconds",
            "min_source_count",
            "recount_margin_watch_ratio",
        ):
            object.__setattr__(self, name, _require_nonnegative_decimal(name, getattr(self, name)))
        if self.max_evidence_age_seconds == ZERO:
            raise ValueError("max_evidence_age_seconds must be positive")
        if self.min_source_count == ZERO:
            raise ValueError("min_source_count must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPolicyRecountLitigationDigestInputRow:
    research_key: str
    condition_id: str
    jurisdiction: str
    public_evidence_reference: str
    observed_at: datetime
    source_count: Decimal
    recount_margin_ratio: Decimal
    litigation_event_count: Decimal
    unresolved_filing_count: Decimal
    certified_result: bool
    official_update: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyRecountLitigationDigestInputRow:
            raise TypeError(
                "MarketResearchPolicyRecountLitigationDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyRecountLitigationDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchPolicyRecountLitigationDigestInputRow",
            )
        for name in ("research_key", "condition_id", "jurisdiction"):
            _require_public_string(name, getattr(self, name))
        _require_reference("public_evidence_reference", self.public_evidence_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in (
            "source_count",
            "litigation_event_count",
            "unresolved_filing_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_count_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "recount_margin_ratio",
            _require_ratio_decimal("recount_margin_ratio", self.recount_margin_ratio),
        )
        _require_bool("certified_result", self.certified_result)
        _require_bool("official_update", self.official_update)
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchPolicyRecountLitigationDigestRow:
    research_key: str
    condition_id: str
    jurisdiction: str
    digest_status: str
    observed_at: datetime
    evidence_age_seconds: Decimal
    source_count: Decimal
    recount_margin_ratio: Decimal
    litigation_event_count: Decimal
    unresolved_filing_count: Decimal
    certified_result: bool
    official_update: bool
    redacted_public_evidence_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyRecountLitigationDigestRow:
            raise TypeError(
                "MarketResearchPolicyRecountLitigationDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyRecountLitigationDigestRow:
            raise ValueError("row must be exactly MarketResearchPolicyRecountLitigationDigestRow")
        for name in (
            "research_key",
            "condition_id",
            "jurisdiction",
            "redacted_public_evidence_reference",
        ):
            _require_public_string(name, getattr(self, name))
        _require_digest_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _require_nonnegative_decimal("evidence_age_seconds", self.evidence_age_seconds),
        )
        for name in (
            "source_count",
            "litigation_event_count",
            "unresolved_filing_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_count_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "recount_margin_ratio",
            _require_ratio_decimal("recount_margin_ratio", self.recount_margin_ratio),
        )
        _require_bool("certified_result", self.certified_result)
        _require_bool("official_update", self.official_update)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        if self.digest_status != _row_status(self.reason_codes):
            raise ValueError("digest_status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPolicyRecountLitigationDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyRecountLitigationDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPolicyRecountLitigationDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyRecountLitigationDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchPolicyRecountLitigationDigestReasonCodeCount",
            )
        _require_digest_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchPolicyRecountLitigationDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    row_count: Decimal
    ready_row_count: Decimal
    watch_row_count: Decimal
    blocked_row_count: Decimal
    recount_watch_count: Decimal
    litigation_watch_count: Decimal
    unresolved_filing_count: Decimal
    uncertified_result_count: Decimal
    stale_evidence_count: Decimal
    thin_source_count: Decimal
    average_recount_margin_ratio: Decimal
    max_evidence_age_seconds: Decimal
    rows: tuple[MarketResearchPolicyRecountLitigationDigestRow, ...]
    reason_code_counts: tuple[MarketResearchPolicyRecountLitigationDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyRecountLitigationDigestReport:
            raise TypeError(
                "MarketResearchPolicyRecountLitigationDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyRecountLitigationDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchPolicyRecountLitigationDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_RECOUNT_LITIGATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_digest_status("digest_status", self.digest_status)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for name in (
            "row_count",
            "ready_row_count",
            "watch_row_count",
            "blocked_row_count",
            "recount_watch_count",
            "litigation_watch_count",
            "unresolved_filing_count",
            "uncertified_result_count",
            "stale_evidence_count",
            "thin_source_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_count_decimal(name, getattr(self, name)),
            )
        for name in ("average_recount_margin_ratio", "max_evidence_age_seconds"):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODE_SEQUENCE),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_market_research_policy_recount_litigation_digest(
    rows: tuple[object, ...],
    *,
    config: MarketResearchPolicyRecountLitigationDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyRecountLitigationDigestReport:
    if type(config) is not MarketResearchPolicyRecountLitigationDigestConfig:
        raise ValueError("config must be exactly MarketResearchPolicyRecountLitigationDigestConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(rows)
    digest_rows = tuple(
        sorted(
            (
                _build_row(source, config=config, generated_at=generated_at_utc)
                for source in source_rows
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _decimal_count(len(digest_rows))
    ready_count = _status_count(digest_rows, STATUS_READY)
    watch_count = _status_count(digest_rows, STATUS_WATCH)
    blocked_count = _status_count(digest_rows, STATUS_BLOCKED)
    reason_code_counts = _reason_code_counts(digest_rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not digest_rows:
        reason_codes = (NO_INPUTS_REASON,)
    digest_status = _report_status(
        row_count=row_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
    )
    return MarketResearchPolicyRecountLitigationDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        row_count=row_count,
        ready_row_count=ready_count,
        watch_row_count=watch_count,
        blocked_row_count=blocked_count,
        recount_watch_count=_reason_row_count(digest_rows, RECOUNT_MARGIN_REASON),
        litigation_watch_count=_reason_row_count(digest_rows, LITIGATION_ACTIVITY_REASON),
        unresolved_filing_count=_reason_row_count(digest_rows, UNRESOLVED_FILINGS_REASON),
        uncertified_result_count=_reason_row_count(digest_rows, UNCERTIFIED_RESULT_REASON),
        stale_evidence_count=_reason_row_count(digest_rows, STALE_EVIDENCE_REASON),
        thin_source_count=_reason_row_count(digest_rows, THIN_SOURCES_REASON),
        average_recount_margin_ratio=_ratio(
            _sum_decimal(row.recount_margin_ratio for row in digest_rows),
            row_count,
        ),
        max_evidence_age_seconds=_max_decimal(row.evidence_age_seconds for row in digest_rows),
        rows=digest_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_policy_recount_litigation_digest_payload(
    report: MarketResearchPolicyRecountLitigationDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPolicyRecountLitigationDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchPolicyRecountLitigationDigestReport",
        )
    _require_hard_flags("report", report)
    return _payload_value(asdict(report))


def _build_row(
    source: MarketResearchPolicyRecountLitigationDigestInputRow,
    *,
    config: MarketResearchPolicyRecountLitigationDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyRecountLitigationDigestRow:
    evidence_age_seconds = _age_seconds(generated_at, source.observed_at)
    reason_codes = _row_reason_codes(source, config=config, age_seconds=evidence_age_seconds)
    return MarketResearchPolicyRecountLitigationDigestRow(
        research_key=source.research_key,
        condition_id=source.condition_id,
        jurisdiction=source.jurisdiction,
        digest_status=_row_status(reason_codes),
        observed_at=source.observed_at,
        evidence_age_seconds=evidence_age_seconds,
        source_count=source.source_count,
        recount_margin_ratio=source.recount_margin_ratio,
        litigation_event_count=source.litigation_event_count,
        unresolved_filing_count=source.unresolved_filing_count,
        certified_result=source.certified_result,
        official_update=source.official_update,
        redacted_public_evidence_reference=_redacted_reference(source.public_evidence_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    source: MarketResearchPolicyRecountLitigationDigestInputRow,
    *,
    config: MarketResearchPolicyRecountLitigationDigestConfig,
    age_seconds: Decimal,
) -> tuple[str, ...]:
    reasons = []
    if source.unresolved_filing_count > ZERO:
        reasons.append(UNRESOLVED_FILINGS_REASON)
    if not source.certified_result:
        reasons.append(UNCERTIFIED_RESULT_REASON)
    if source.recount_margin_ratio <= config.recount_margin_watch_ratio:
        reasons.append(RECOUNT_MARGIN_REASON)
    if source.litigation_event_count > ZERO:
        reasons.append(LITIGATION_ACTIVITY_REASON)
    if age_seconds > config.max_evidence_age_seconds or not source.official_update:
        reasons.append(STALE_EVIDENCE_REASON)
    if source.source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if not reasons:
        return (READY_REASON,)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if (
        UNRESOLVED_FILINGS_REASON in reason_codes
        or UNCERTIFIED_RESULT_REASON in reason_codes
        or STALE_EVIDENCE_REASON in reason_codes
        or THIN_SOURCES_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(*, row_count: Decimal, watch_count: Decimal, blocked_count: Decimal) -> str:
    if row_count == ZERO:
        return STATUS_READY
    if blocked_count > ZERO:
        return STATUS_BLOCKED
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _row_sort_key(row: MarketResearchPolicyRecountLitigationDigestRow) -> tuple[int, str, str]:
    return (_status_rank(row.digest_status), row.research_key, row.condition_id)


def _normalize_input_rows(
    rows: tuple[object, ...],
) -> tuple[MarketResearchPolicyRecountLitigationDigestInputRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = []
    seen_research_keys: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchPolicyRecountLitigationDigestInputRow:
            raise ValueError(
                "rows must contain MarketResearchPolicyRecountLitigationDigestInputRow",
            )
        _require_hard_flags("input row", row)
        if row.research_key in seen_research_keys:
            raise ValueError("research_key values must be unique")
        seen_research_keys.add(row.research_key)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[MarketResearchPolicyRecountLitigationDigestRow, ...],
) -> tuple[MarketResearchPolicyRecountLitigationDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_research_keys: set[str] = set()
    normalized = []
    for row in rows:
        if type(row) is not MarketResearchPolicyRecountLitigationDigestRow:
            raise ValueError("rows must contain MarketResearchPolicyRecountLitigationDigestRow")
        _require_hard_flags("row", row)
        if row.research_key in seen_research_keys:
            raise ValueError("row research_key values must be unique")
        seen_research_keys.add(row.research_key)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchPolicyRecountLitigationDigestReasonCodeCount, ...],
) -> tuple[MarketResearchPolicyRecountLitigationDigestReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_reason_codes: set[str] = set()
    normalized = []
    for count in counts:
        if type(count) is not MarketResearchPolicyRecountLitigationDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchPolicyRecountLitigationDigestReasonCodeCount",
            )
        _require_hard_flags("reason count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen_reason_codes.add(count.reason_code)
        normalized.append(count)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                REPORT_REASON_CODE_SEQUENCE.index(item.reason_code),
                item.reason_code,
            ),
        ),
    )


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen_reason_codes: set[str] = set()
    for reason_code in reason_codes:
        _require_digest_reason_code("reason_code", reason_code)
        if reason_code in seen_reason_codes:
            raise ValueError("reason_codes must be unique")
        if reason_code not in sequence:
            raise ValueError("reason_code is not valid for this scope")
        seen_reason_codes.add(reason_code)
    normalized = tuple(reason_code for reason_code in sequence if reason_code in seen_reason_codes)
    if normalized != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _validate_report_consistency(
    report: MarketResearchPolicyRecountLitigationDigestReport,
) -> None:
    row_count = _decimal_count(len(report.rows))
    if report.row_count != row_count:
        raise ValueError("row_count must match rows")
    expected_ready = _status_count(report.rows, STATUS_READY)
    expected_watch = _status_count(report.rows, STATUS_WATCH)
    expected_blocked = _status_count(report.rows, STATUS_BLOCKED)
    expected_counts = (
        ("ready_row_count", expected_ready),
        ("watch_row_count", expected_watch),
        ("blocked_row_count", expected_blocked),
        ("recount_watch_count", _reason_row_count(report.rows, RECOUNT_MARGIN_REASON)),
        (
            "litigation_watch_count",
            _reason_row_count(report.rows, LITIGATION_ACTIVITY_REASON),
        ),
        (
            "unresolved_filing_count",
            _reason_row_count(report.rows, UNRESOLVED_FILINGS_REASON),
        ),
        (
            "uncertified_result_count",
            _reason_row_count(report.rows, UNCERTIFIED_RESULT_REASON),
        ),
        ("stale_evidence_count", _reason_row_count(report.rows, STALE_EVIDENCE_REASON)),
        ("thin_source_count", _reason_row_count(report.rows, THIN_SOURCES_REASON)),
    )
    for name, expected in expected_counts:
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    if report.average_recount_margin_ratio != _ratio(
        _sum_decimal(row.recount_margin_ratio for row in report.rows),
        row_count,
    ):
        raise ValueError("average_recount_margin_ratio must match rows")
    if report.max_evidence_age_seconds != _max_decimal(
        (row.evidence_age_seconds for row in report.rows),
    ):
        raise ValueError("max_evidence_age_seconds must match rows")
    if report.digest_status != _report_status(
        row_count=row_count,
        watch_count=expected_watch,
        blocked_count=expected_blocked,
    ):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        if report.rows or report.reason_codes != (NO_INPUTS_REASON,):
            raise ValueError("reason_codes must match reason_code_counts")


def _reason_code_counts(
    rows: tuple[MarketResearchPolicyRecountLitigationDigestRow, ...],
) -> tuple[MarketResearchPolicyRecountLitigationDigestReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    if total == ZERO:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    include_ready = set(counts) == {READY_REASON}
    return tuple(
        MarketResearchPolicyRecountLitigationDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code != NO_INPUTS_REASON
        and (reason_code != READY_REASON or include_ready)
        and (count := counts.get(reason_code, 0)) > 0
    )


def _status_count(
    rows: tuple[MarketResearchPolicyRecountLitigationDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_row_count(
    rows: tuple[MarketResearchPolicyRecountLitigationDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _require_public_string(name: str, value: str) -> None:
    _require_canonical_string(name, value)
    _reject_sensitive_text(name, value)


def _require_reference(name: str, value: str) -> None:
    _require_canonical_string(name, value)


def _require_canonical_string(name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a plain string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be non-empty canonical text")


def _reject_sensitive_text(name: str, value: str) -> None:
    lowered = value.lower()
    forbidden = (
        _join_parts("wal", "let"),
        _join_parts("pri", "vate", "_", "key"),
        _join_parts("mar", "ket", "_", "slug"),
        _join_parts("quest", "ion"),
        _join_parts("adv", "ice"),
    )
    if any(fragment in lowered for fragment in forbidden):
        raise ValueError(f"{name} contains forbidden text")


def _require_digest_status(name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a plain string")
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{name} must be one of {DIGEST_STATUSES}")


def _require_digest_reason_code(name: str, value: str) -> None:
    _require_canonical_string(name, value)
    if value not in REPORT_REASON_CODE_SEQUENCE:
        raise ValueError(f"{name} must be a supported reason code")


def _require_bool(name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    if (
        getattr(value, "paper_only", None) is not True
        or getattr(value, "report_only", None) is not True
        or getattr(value, "readonly", None) is not True
    ):
        raise ValueError(f"{label} paper_only/report_only/readonly must be True")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _six(value)


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_nonnegative_count_decimal(name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole-count Decimal")
    return decimal_value


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value > ONE:
        raise ValueError(f"{name} must be in the 0..1 range")
    return decimal_value


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    total = (
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _require_nonnegative_decimal("evidence_age_seconds", total)


def _redacted_reference(value: str) -> str:
    if value.startswith("public-"):
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _status_rank(status: str) -> int:
    return {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[status]


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _six(Decimal(value))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _six(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _six(numerator / denominator)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return max(tuple(values), default=ZERO)


def _six(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _payload_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    return value


def _join_parts(*parts: str) -> str:
    return "".join(parts)
