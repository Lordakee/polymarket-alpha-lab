"""Pure report reducer for local research memory retention policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256


DEFAULT_RESEARCH_LOCAL_SUPABASE_RETENTION_POLICY_CONFIG_VERSION = (
    "research-local-supabase-retention-policy-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

NO_INPUTS_REASON = "research_local_supabase_retention_policy_no_inputs"
PASS_REASON = "research_local_supabase_retention_policy_pass"
RETENTION_LIMIT_REASON = (
    "research_local_supabase_retention_policy_retention_period_exceeds_limit"
)
DEIDENTIFICATION_GAP_REASON = (
    "research_local_supabase_retention_policy_deidentification_gap"
)
REVIEW_RETENTION_SHORT_REASON = (
    "research_local_supabase_retention_policy_review_retention_shortfall"
)
REVIEW_RETENTION_OVER_REASON = (
    "research_local_supabase_retention_policy_review_retention_exceeds_limit"
)
REVIEW_WINDOW_EXPIRED_REASON = (
    "research_local_supabase_retention_policy_review_window_expired"
)
SOURCE_SUMMARY_MISSING_REASON = (
    "research_local_supabase_retention_policy_source_summary_missing"
)
SOURCE_SUMMARY_SHORT_REASON = (
    "research_local_supabase_retention_policy_source_summary_retention_shortfall"
)
SOURCE_SUMMARY_OVER_REASON = (
    "research_local_supabase_retention_policy_source_summary_retention_exceeds_limit"
)
AUDIT_LOG_MISSING_REASON = "research_local_supabase_retention_policy_audit_log_missing"
AUDIT_LOG_SHORT_REASON = (
    "research_local_supabase_retention_policy_audit_log_retention_shortfall"
)
AUDIT_LOG_OVER_REASON = (
    "research_local_supabase_retention_policy_audit_log_retention_exceeds_limit"
)

REASON_CODE_SEQUENCE = (
    AUDIT_LOG_MISSING_REASON,
    AUDIT_LOG_OVER_REASON,
    AUDIT_LOG_SHORT_REASON,
    DEIDENTIFICATION_GAP_REASON,
    NO_INPUTS_REASON,
    PASS_REASON,
    RETENTION_LIMIT_REASON,
    REVIEW_RETENTION_OVER_REASON,
    REVIEW_RETENTION_SHORT_REASON,
    REVIEW_WINDOW_EXPIRED_REASON,
    SOURCE_SUMMARY_MISSING_REASON,
    SOURCE_SUMMARY_OVER_REASON,
    SOURCE_SUMMARY_SHORT_REASON,
)
ROW_REASON_CODE_SEQUENCE = tuple(
    reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code != NO_INPUTS_REASON
)
BLOCK_REASON_CODES = frozenset(
    (
        AUDIT_LOG_MISSING_REASON,
        AUDIT_LOG_SHORT_REASON,
        DEIDENTIFICATION_GAP_REASON,
        RETENTION_LIMIT_REASON,
        REVIEW_RETENTION_SHORT_REASON,
        REVIEW_WINDOW_EXPIRED_REASON,
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        AUDIT_LOG_OVER_REASON,
        REVIEW_RETENTION_OVER_REASON,
        SOURCE_SUMMARY_MISSING_REASON,
        SOURCE_SUMMARY_OVER_REASON,
        SOURCE_SUMMARY_SHORT_REASON,
    ),
)

RECORD_CLASSES = frozenset(
    (
        "research_memory",
        "review_snapshot",
        "source_summary",
        "audit_log",
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

_STATUS_NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_research_local_supabase_retention_policy",
    STATUS_WATCH: "watch_report_only_research_local_supabase_retention_policy",
    STATUS_BLOCK: "block_report_only_research_local_supabase_retention_policy",
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("ds", "n"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("raw", "_source"),
        _join_parts("raw", "source"),
        _join_parts("mar", "ket"),
        _join_parts("con", "dition"),
        _join_parts("data", "base"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        _join_parts("wal", "let"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_LOCAL_SUPABASE_RETENTION_POLICY_CONFIG_VERSION",
    "ResearchLocalSupabaseRetentionPolicyConfig",
    "ResearchLocalSupabaseRetentionPolicyInputRow",
    "ResearchLocalSupabaseRetentionPolicyReasonCodeCount",
    "ResearchLocalSupabaseRetentionPolicyReport",
    "ResearchLocalSupabaseRetentionPolicyRow",
    "build_research_local_supabase_retention_policy_report",
    "research_local_supabase_retention_policy_payload",
)


@dataclass(frozen=True)
class ResearchLocalSupabaseRetentionPolicyConfig:
    config_version: str = DEFAULT_RESEARCH_LOCAL_SUPABASE_RETENTION_POLICY_CONFIG_VERSION
    max_memory_retention_days: Decimal = Decimal("365.000000")
    max_deidentification_lag_days: Decimal = Decimal("30.000000")
    min_review_retention_days: Decimal = Decimal("90.000000")
    max_review_retention_days: Decimal = Decimal("730.000000")
    min_source_summary_retention_days: Decimal = Decimal("90.000000")
    max_source_summary_retention_days: Decimal = Decimal("730.000000")
    min_audit_log_retention_days: Decimal = Decimal("180.000000")
    max_audit_log_retention_days: Decimal = Decimal("730.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchLocalSupabaseRetentionPolicyConfig:
            raise TypeError(
                "ResearchLocalSupabaseRetentionPolicyConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchLocalSupabaseRetentionPolicyConfig:
            raise ValueError(
                "config must be exactly ResearchLocalSupabaseRetentionPolicyConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "max_memory_retention_days",
            "max_deidentification_lag_days",
            "min_review_retention_days",
            "max_review_retention_days",
            "min_source_summary_retention_days",
            "max_source_summary_retention_days",
            "min_audit_log_retention_days",
            "max_audit_log_retention_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_review_retention_days > self.max_review_retention_days:
            raise ValueError(
                "min_review_retention_days must not exceed max_review_retention_days",
            )
        if (
            self.min_source_summary_retention_days
            > self.max_source_summary_retention_days
        ):
            raise ValueError(
                "min_source_summary_retention_days must not exceed "
                "max_source_summary_retention_days",
            )
        if self.min_audit_log_retention_days > self.max_audit_log_retention_days:
            raise ValueError(
                "min_audit_log_retention_days must not exceed "
                "max_audit_log_retention_days",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchLocalSupabaseRetentionPolicyInputRow:
    record_class: str
    retention_days: Decimal
    deidentify_after_days: Decimal
    review_retention_days: Decimal
    source_summary_retention_days: Decimal
    audit_log_retention_days: Decimal
    unredacted_reference_present: bool
    direct_identifier_present: bool
    source_summary_present: bool
    audit_log_present: bool
    review_required: bool
    review_age_days: Decimal
    reference_locator: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchLocalSupabaseRetentionPolicyInputRow:
            raise TypeError(
                "ResearchLocalSupabaseRetentionPolicyInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchLocalSupabaseRetentionPolicyInputRow:
            raise ValueError(
                "input row must be exactly ResearchLocalSupabaseRetentionPolicyInputRow",
            )
        _require_record_class("record_class", self.record_class)
        for field_name in (
            "retention_days",
            "deidentify_after_days",
            "review_retention_days",
            "source_summary_retention_days",
            "audit_log_retention_days",
            "review_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unredacted_reference_present",
            "direct_identifier_present",
            "source_summary_present",
            "audit_log_present",
            "review_required",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reference_locator",
            _normalize_optional_reference("reference_locator", self.reference_locator),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchLocalSupabaseRetentionPolicyRow:
    record_class: str
    policy_status: str
    retention_days: Decimal
    deidentify_after_days: Decimal
    review_retention_days: Decimal
    source_summary_retention_days: Decimal
    audit_log_retention_days: Decimal
    unredacted_reference_present: bool
    direct_identifier_present: bool
    source_summary_present: bool
    audit_log_present: bool
    review_required: bool
    review_age_days: Decimal
    reference_fingerprint: str | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchLocalSupabaseRetentionPolicyRow:
            raise TypeError(
                "ResearchLocalSupabaseRetentionPolicyRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchLocalSupabaseRetentionPolicyRow:
            raise ValueError("row must be exactly ResearchLocalSupabaseRetentionPolicyRow")
        _require_record_class("record_class", self.record_class)
        _require_status("policy_status", self.policy_status)
        for field_name in (
            "retention_days",
            "deidentify_after_days",
            "review_retention_days",
            "source_summary_retention_days",
            "audit_log_retention_days",
            "review_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unredacted_reference_present",
            "direct_identifier_present",
            "source_summary_present",
            "audit_log_present",
            "review_required",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reference_fingerprint",
            _normalize_optional_fingerprint(
                "reference_fingerprint",
                self.reference_fingerprint,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.policy_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("policy_status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchLocalSupabaseRetentionPolicyReasonCodeCount:
    reason_code: str
    count: Decimal
    subject_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchLocalSupabaseRetentionPolicyReasonCodeCount:
            raise TypeError(
                "ResearchLocalSupabaseRetentionPolicyReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchLocalSupabaseRetentionPolicyReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchLocalSupabaseRetentionPolicyReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "subject_ratio",
            _require_ratio_decimal("subject_ratio", self.subject_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchLocalSupabaseRetentionPolicyReport:
    generated_at: datetime
    config_version: str
    policy_status: str
    recommended_next_step: str
    policy_subject_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    retention_gap_count: Decimal
    deidentification_gap_count: Decimal
    review_retention_gap_count: Decimal
    source_summary_gap_count: Decimal
    audit_log_gap_count: Decimal
    reference_fingerprint_count: Decimal
    source_summary_coverage_ratio: Decimal
    audit_log_coverage_ratio: Decimal
    average_retention_days: Decimal
    max_retention_days: Decimal
    rows: tuple[ResearchLocalSupabaseRetentionPolicyRow, ...]
    reason_code_counts: tuple[ResearchLocalSupabaseRetentionPolicyReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchLocalSupabaseRetentionPolicyReport:
            raise TypeError(
                "ResearchLocalSupabaseRetentionPolicyReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchLocalSupabaseRetentionPolicyReport:
            raise ValueError(
                "report must be exactly ResearchLocalSupabaseRetentionPolicyReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("policy_status", self.policy_status)
        if self.recommended_next_step != _STATUS_NEXT_STEPS[self.policy_status]:
            raise ValueError("recommended_next_step must match policy_status")
        for field_name in (
            "policy_subject_count",
            "pass_count",
            "watch_count",
            "block_count",
            "retention_gap_count",
            "deidentification_gap_count",
            "review_retention_gap_count",
            "source_summary_gap_count",
            "audit_log_gap_count",
            "reference_fingerprint_count",
            "average_retention_days",
            "max_retention_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_summary_coverage_ratio", "audit_log_coverage_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_row_tuple("rows", self.rows)
        _require_reason_count_tuple("reason_code_counts", self.reason_code_counts)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_research_local_supabase_retention_policy_report(
    rows: tuple[ResearchLocalSupabaseRetentionPolicyInputRow, ...],
    *,
    config: ResearchLocalSupabaseRetentionPolicyConfig | None = None,
    generated_at: datetime,
) -> ResearchLocalSupabaseRetentionPolicyReport:
    cfg = config or ResearchLocalSupabaseRetentionPolicyConfig()
    if type(cfg) is not ResearchLocalSupabaseRetentionPolicyConfig:
        raise TypeError(
            "config must be exactly ResearchLocalSupabaseRetentionPolicyConfig",
        )
    _require_hard_flags("config", cfg)
    observed_at = _as_utc("generated_at", generated_at)
    input_rows = _require_input_row_tuple("rows", rows)

    if not input_rows:
        reason_counts = (
            ResearchLocalSupabaseRetentionPolicyReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                subject_ratio=ZERO,
            ),
        )
        return ResearchLocalSupabaseRetentionPolicyReport(
            generated_at=observed_at,
            config_version=cfg.config_version,
            policy_status=STATUS_BLOCK,
            recommended_next_step=_STATUS_NEXT_STEPS[STATUS_BLOCK],
            policy_subject_count=ZERO,
            pass_count=ZERO,
            watch_count=ZERO,
            block_count=ZERO,
            retention_gap_count=ZERO,
            deidentification_gap_count=ZERO,
            review_retention_gap_count=ZERO,
            source_summary_gap_count=ZERO,
            audit_log_gap_count=ZERO,
            reference_fingerprint_count=ZERO,
            source_summary_coverage_ratio=ZERO,
            audit_log_coverage_ratio=ZERO,
            average_retention_days=ZERO,
            max_retention_days=ZERO,
            rows=(),
            reason_code_counts=reason_counts,
            reason_codes=(NO_INPUTS_REASON,),
        )

    report_rows = tuple(_build_row(row, config=cfg) for row in input_rows)
    sorted_rows = tuple(
        sorted(
            report_rows,
            key=lambda row: (
                _status_rank(row.policy_status),
                row.record_class,
                row.retention_days,
            ),
        ),
    )
    reason_counts = _reason_code_counts(sorted_rows)
    reason_codes = tuple(item.reason_code for item in reason_counts)
    subject_count = _count_decimal(sorted_rows)
    policy_status = _report_status(sorted_rows)

    return ResearchLocalSupabaseRetentionPolicyReport(
        generated_at=observed_at,
        config_version=cfg.config_version,
        policy_status=policy_status,
        recommended_next_step=_STATUS_NEXT_STEPS[policy_status],
        policy_subject_count=subject_count,
        pass_count=_sum_if(sorted_rows, lambda row: row.policy_status == STATUS_PASS),
        watch_count=_sum_if(sorted_rows, lambda row: row.policy_status == STATUS_WATCH),
        block_count=_sum_if(sorted_rows, lambda row: row.policy_status == STATUS_BLOCK),
        retention_gap_count=_sum_if(
            sorted_rows,
            lambda row: RETENTION_LIMIT_REASON in row.reason_codes,
        ),
        deidentification_gap_count=_sum_if(
            sorted_rows,
            lambda row: DEIDENTIFICATION_GAP_REASON in row.reason_codes,
        ),
        review_retention_gap_count=_sum_if(
            sorted_rows,
            lambda row: any(
                reason_code in row.reason_codes
                for reason_code in (
                    REVIEW_RETENTION_OVER_REASON,
                    REVIEW_RETENTION_SHORT_REASON,
                    REVIEW_WINDOW_EXPIRED_REASON,
                )
            ),
        ),
        source_summary_gap_count=_sum_if(
            sorted_rows,
            lambda row: any(
                reason_code in row.reason_codes
                for reason_code in (
                    SOURCE_SUMMARY_MISSING_REASON,
                    SOURCE_SUMMARY_OVER_REASON,
                    SOURCE_SUMMARY_SHORT_REASON,
                )
            ),
        ),
        audit_log_gap_count=_sum_if(
            sorted_rows,
            lambda row: any(
                reason_code in row.reason_codes
                for reason_code in (
                    AUDIT_LOG_MISSING_REASON,
                    AUDIT_LOG_OVER_REASON,
                    AUDIT_LOG_SHORT_REASON,
                )
            ),
        ),
        reference_fingerprint_count=_sum_if(
            sorted_rows,
            lambda row: row.reference_fingerprint is not None,
        ),
        source_summary_coverage_ratio=_ratio(
            _sum_if(sorted_rows, lambda row: row.source_summary_present),
            subject_count,
        ),
        audit_log_coverage_ratio=_ratio(
            _sum_if(sorted_rows, lambda row: row.audit_log_present),
            subject_count,
        ),
        average_retention_days=_average(row.retention_days for row in sorted_rows),
        max_retention_days=max(row.retention_days for row in sorted_rows),
        rows=sorted_rows,
        reason_code_counts=reason_counts,
        reason_codes=reason_codes,
    )


def research_local_supabase_retention_policy_payload(
    report: ResearchLocalSupabaseRetentionPolicyReport,
) -> dict[str, object]:
    if type(report) is not ResearchLocalSupabaseRetentionPolicyReport:
        raise TypeError(
            "report must be exactly ResearchLocalSupabaseRetentionPolicyReport",
        )
    _require_hard_flags("report", report)
    payload: dict[str, object] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "policy_status": report.policy_status,
        "recommended_next_step": report.recommended_next_step,
        "policy_subject_count": _decimal_payload(report.policy_subject_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "retention_gap_count": _decimal_payload(report.retention_gap_count),
        "deidentification_gap_count": _decimal_payload(
            report.deidentification_gap_count,
        ),
        "review_retention_gap_count": _decimal_payload(
            report.review_retention_gap_count,
        ),
        "source_summary_gap_count": _decimal_payload(report.source_summary_gap_count),
        "audit_log_gap_count": _decimal_payload(report.audit_log_gap_count),
        "reference_fingerprint_count": _decimal_payload(
            report.reference_fingerprint_count,
        ),
        "source_summary_coverage_ratio": _decimal_payload(
            report.source_summary_coverage_ratio,
        ),
        "audit_log_coverage_ratio": _decimal_payload(report.audit_log_coverage_ratio),
        "average_retention_days": _decimal_payload(report.average_retention_days),
        "max_retention_days": _decimal_payload(report.max_retention_days),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            _reason_code_count_payload(item) for item in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _build_row(
    row: ResearchLocalSupabaseRetentionPolicyInputRow,
    *,
    config: ResearchLocalSupabaseRetentionPolicyConfig,
) -> ResearchLocalSupabaseRetentionPolicyRow:
    reason_codes = _row_reason_codes(row, config=config)
    return ResearchLocalSupabaseRetentionPolicyRow(
        record_class=row.record_class,
        policy_status=_status_from_reason_codes(reason_codes),
        retention_days=row.retention_days,
        deidentify_after_days=row.deidentify_after_days,
        review_retention_days=row.review_retention_days,
        source_summary_retention_days=row.source_summary_retention_days,
        audit_log_retention_days=row.audit_log_retention_days,
        unredacted_reference_present=row.unredacted_reference_present,
        direct_identifier_present=row.direct_identifier_present,
        source_summary_present=row.source_summary_present,
        audit_log_present=row.audit_log_present,
        review_required=row.review_required,
        review_age_days=row.review_age_days,
        reference_fingerprint=_fingerprint_reference(row.reference_locator),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchLocalSupabaseRetentionPolicyInputRow,
    *,
    config: ResearchLocalSupabaseRetentionPolicyConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.retention_days > config.max_memory_retention_days:
        reasons.append(RETENTION_LIMIT_REASON)
    if (
        row.unredacted_reference_present or row.direct_identifier_present
    ) and row.deidentify_after_days > config.max_deidentification_lag_days:
        reasons.append(DEIDENTIFICATION_GAP_REASON)
    if row.review_required:
        if row.review_retention_days < config.min_review_retention_days:
            reasons.append(REVIEW_RETENTION_SHORT_REASON)
        if row.review_age_days > row.review_retention_days:
            reasons.append(REVIEW_WINDOW_EXPIRED_REASON)
    if row.review_retention_days > config.max_review_retention_days:
        reasons.append(REVIEW_RETENTION_OVER_REASON)
    if not row.source_summary_present:
        reasons.append(SOURCE_SUMMARY_MISSING_REASON)
    if row.source_summary_retention_days < config.min_source_summary_retention_days:
        reasons.append(SOURCE_SUMMARY_SHORT_REASON)
    if row.source_summary_retention_days > config.max_source_summary_retention_days:
        reasons.append(SOURCE_SUMMARY_OVER_REASON)
    if not row.audit_log_present:
        reasons.append(AUDIT_LOG_MISSING_REASON)
    if row.audit_log_retention_days < config.min_audit_log_retention_days:
        reasons.append(AUDIT_LOG_SHORT_REASON)
    if row.audit_log_retention_days > config.max_audit_log_retention_days:
        reasons.append(AUDIT_LOG_OVER_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _row_payload(row: ResearchLocalSupabaseRetentionPolicyRow) -> dict[str, object]:
    _require_hard_flags("row", row)
    return {
        "record_class": row.record_class,
        "policy_status": row.policy_status,
        "retention_days": _decimal_payload(row.retention_days),
        "deidentify_after_days": _decimal_payload(row.deidentify_after_days),
        "review_retention_days": _decimal_payload(row.review_retention_days),
        "source_summary_retention_days": _decimal_payload(
            row.source_summary_retention_days,
        ),
        "audit_log_retention_days": _decimal_payload(row.audit_log_retention_days),
        "unredacted_reference_present": row.unredacted_reference_present,
        "direct_identifier_present": row.direct_identifier_present,
        "source_summary_present": row.source_summary_present,
        "audit_log_present": row.audit_log_present,
        "review_required": row.review_required,
        "review_age_days": _decimal_payload(row.review_age_days),
        "reference_fingerprint": row.reference_fingerprint,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    item: ResearchLocalSupabaseRetentionPolicyReasonCodeCount,
) -> dict[str, object]:
    _require_hard_flags("reason code count", item)
    return {
        "reason_code": item.reason_code,
        "count": _decimal_payload(item.count),
        "subject_ratio": _decimal_payload(item.subject_ratio),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_status(rows: tuple[ResearchLocalSupabaseRetentionPolicyRow, ...]) -> str:
    if any(row.policy_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.policy_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if NO_INPUTS_REASON in reason_codes:
        return STATUS_BLOCK
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return STATUS_WATCH
    raise ValueError("reason_codes do not map to a policy_status")


def _reason_code_counts(
    rows: tuple[ResearchLocalSupabaseRetentionPolicyRow, ...],
) -> tuple[ResearchLocalSupabaseRetentionPolicyReasonCodeCount, ...]:
    row_count = _count_decimal(rows)
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchLocalSupabaseRetentionPolicyReasonCodeCount(
            reason_code=reason_code,
            count=count,
            subject_ratio=_ratio(count, row_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REASON_CODE_SEQUENCE.index(item[0]),
        )
    )


def _validate_report_consistency(
    report: ResearchLocalSupabaseRetentionPolicyReport,
) -> None:
    rows = report.rows
    if report.policy_subject_count != _count_decimal(rows):
        raise ValueError("policy_subject_count must match rows")
    if report.pass_count != _sum_if(rows, lambda row: row.policy_status == STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _sum_if(rows, lambda row: row.policy_status == STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _sum_if(rows, lambda row: row.policy_status == STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.policy_status != _report_status(rows) and rows:
        raise ValueError("policy_status must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.policy_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("policy_status must match reason_codes")


def _status_rank(status: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[status]


def _require_input_row_tuple(
    field_name: str,
    value: tuple[ResearchLocalSupabaseRetentionPolicyInputRow, ...],
) -> tuple[ResearchLocalSupabaseRetentionPolicyInputRow, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    for row in value:
        if type(row) is not ResearchLocalSupabaseRetentionPolicyInputRow:
            raise ValueError(
                f"{field_name} must contain ResearchLocalSupabaseRetentionPolicyInputRow",
            )
    return value


def _require_row_tuple(
    field_name: str,
    value: tuple[ResearchLocalSupabaseRetentionPolicyRow, ...],
) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    for row in value:
        if type(row) is not ResearchLocalSupabaseRetentionPolicyRow:
            raise ValueError(
                f"{field_name} must contain ResearchLocalSupabaseRetentionPolicyRow",
            )


def _require_reason_count_tuple(
    field_name: str,
    value: tuple[ResearchLocalSupabaseRetentionPolicyReasonCodeCount, ...],
) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    for item in value:
        if type(item) is not ResearchLocalSupabaseRetentionPolicyReasonCodeCount:
            raise ValueError(
                f"{field_name} must contain "
                "ResearchLocalSupabaseRetentionPolicyReasonCodeCount",
            )


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_record_class(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if value not in RECORD_CLASSES:
        raise ValueError(f"{field_name} must be a known record class")
    return value


def _require_status(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if value not in _STATUS_NEXT_STEPS:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason_code")
    return value


def _normalize_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    unique_values = frozenset(value)
    if len(unique_values) != len(value):
        raise ValueError(f"{field_name} contains duplicate reason_code values")
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
    reason_sequence = (
        REASON_CODE_SEQUENCE if NO_INPUTS_REASON in value else ROW_REASON_CODE_SEQUENCE
    )
    return tuple(reason_code for reason_code in reason_sequence if reason_code in unique_values)


def _normalize_optional_reference(field_name: str, value: str | None) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str when present")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be canonical when present")
    return value


def _normalize_optional_fingerprint(field_name: str, value: str | None) -> str | None:
    if value is None:
        return None
    _require_public_string(field_name, value)
    if not (value.startswith("sha256:") and len(value) == 19):
        raise ValueError(f"{field_name} must be a short sha256 fingerprint")
    _reject_unsafe_public_text(field_name, value)
    return value


def _fingerprint_reference(value: str | None) -> str | None:
    if value is None:
        return None
    return f"sha256:{sha256(value.encode()).hexdigest()[:12]}"


def _require_bool(field_name: str, value: bool) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be exactly bool")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must keep {flag_name}=True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be exactly Decimal")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the unit interval")
    return decimal_value


def _count_decimal(values: tuple[object, ...]) -> Decimal:
    return _quantize(Decimal(len(values)))


def _sum_if(
    rows: tuple[ResearchLocalSupabaseRetentionPolicyRow, ...],
    predicate: object,
) -> Decimal:
    return _quantize(sum((ONE for row in rows if predicate(row)), ZERO))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _average(values: object) -> Decimal:
    collected = tuple(values)
    if not collected:
        return ZERO
    return _ratio(_sum_decimal(collected), Decimal(len(collected)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise TypeError("payload value must be exactly Decimal")
    return str(value)


def _reject_unsafe_public_payload(field_name: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError(f"{field_name} payload keys must be exactly str")
            _reject_unsafe_public_text(f"{field_name} key", key)
            _reject_unsafe_public_payload(f"{field_name}.{key}", item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(field_name, item)
    elif isinstance(value, str):
        _reject_unsafe_public_text(field_name, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
