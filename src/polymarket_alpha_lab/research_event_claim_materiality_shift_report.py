"""Deterministic report-only aggregation for event claim materiality shifts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_EVENT_CLAIM_MATERIALITY_SHIFT_CONFIG_VERSION = (
    "research-event-claim-materiality-shift-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
CLAIM_MATERIALITY_SHIFT_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

NO_INPUTS_REASON = "materiality_shift_no_inputs"
SHIFT_PASS_REASON = "materiality_shift_pass"
SHIFT_WATCH_REASON = "materiality_shift_watch"
SHIFT_BLOCK_REASON = "materiality_shift_block"
SOURCE_CURRENT_REASON = "source_recency_current"
SOURCE_AGING_REASON = "source_recency_aging"
SOURCE_STALE_REASON = "source_recency_stale"
CORROBORATION_SUFFICIENT_REASON = "corroboration_sufficient"
CORROBORATION_THIN_REASON = "corroboration_thin"
CORROBORATION_MISSING_REASON = "corroboration_missing"
CONTRADICTION_LOW_REASON = "contradiction_pressure_low"
CONTRADICTION_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_BLOCK_REASON = "contradiction_pressure_block"
MANUAL_URGENCY_LOW_REASON = "manual_review_urgency_low"
MANUAL_URGENCY_WATCH_REASON = "manual_review_urgency_watch"
MANUAL_URGENCY_BLOCK_REASON = "manual_review_urgency_block"

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")

_DERIVED_DIGEST_FIELD = "derived_validation_digest"

_PUBLIC_NEXT_STEPS = {
    STATUS_PASS: "continue_report_only_materiality_review",
    STATUS_WATCH: "watch_report_only_materiality_review",
    STATUS_BLOCK: "pause_report_only_materiality_review",
}

_ROW_REASON_CODE_SEQUENCE = (
    SHIFT_BLOCK_REASON,
    SHIFT_WATCH_REASON,
    SHIFT_PASS_REASON,
    SOURCE_CURRENT_REASON,
    SOURCE_AGING_REASON,
    SOURCE_STALE_REASON,
    CORROBORATION_SUFFICIENT_REASON,
    CORROBORATION_THIN_REASON,
    CORROBORATION_MISSING_REASON,
    CONTRADICTION_LOW_REASON,
    CONTRADICTION_WATCH_REASON,
    CONTRADICTION_BLOCK_REASON,
    MANUAL_URGENCY_LOW_REASON,
    MANUAL_URGENCY_WATCH_REASON,
    MANUAL_URGENCY_BLOCK_REASON,
)

_REPORT_REASON_CODE_SEQUENCE = (
    SHIFT_BLOCK_REASON,
    SHIFT_WATCH_REASON,
    SHIFT_PASS_REASON,
    SOURCE_STALE_REASON,
    SOURCE_AGING_REASON,
    SOURCE_CURRENT_REASON,
    CORROBORATION_MISSING_REASON,
    CORROBORATION_THIN_REASON,
    CORROBORATION_SUFFICIENT_REASON,
    CONTRADICTION_BLOCK_REASON,
    CONTRADICTION_WATCH_REASON,
    CONTRADICTION_LOW_REASON,
    MANUAL_URGENCY_BLOCK_REASON,
    MANUAL_URGENCY_WATCH_REASON,
    MANUAL_URGENCY_LOW_REASON,
    NO_INPUTS_REASON,
)

_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "raw_market",
        "raw_candidate",
        "raw_source",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_identifier",
        "source_ref",
        "source_url",
        "source_text",
        "://",
        "www.",
        "api_key",
        "api-key",
        "dsn",
        "postgres",
        "private_key",
        "private-key",
        "secret",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "position",
        "sizing",
        "buy",
        "sell",
        "recommend",
    ),
)

__all__ = (
    "CLAIM_MATERIALITY_SHIFT_STATUSES",
    "DEFAULT_RESEARCH_EVENT_CLAIM_MATERIALITY_SHIFT_CONFIG_VERSION",
    "ResearchEventClaimMaterialityShiftConfig",
    "ResearchEventClaimMaterialityShiftInput",
    "ResearchEventClaimMaterialityShiftReasonCodeCount",
    "ResearchEventClaimMaterialityShiftReport",
    "ResearchEventClaimMaterialityShiftRow",
    "build_research_event_claim_materiality_shift_report",
    "research_event_claim_materiality_shift_report_digest",
    "research_event_claim_materiality_shift_report_payload",
)


@dataclass(frozen=True)
class ResearchEventClaimMaterialityShiftConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_CLAIM_MATERIALITY_SHIFT_CONFIG_VERSION
    )
    fresh_source_age_seconds: Decimal = Decimal("21600.000000")
    stale_source_age_seconds: Decimal = Decimal("172800.000000")
    min_pass_corroboration_count: Decimal = Decimal("2.000000")
    watch_materiality_score: Decimal = Decimal("0.400000")
    block_materiality_score: Decimal = Decimal("0.700000")
    watch_contradiction_pressure: Decimal = Decimal("0.300000")
    block_contradiction_pressure: Decimal = Decimal("0.650000")
    watch_manual_review_urgency: Decimal = Decimal("0.400000")
    block_manual_review_urgency: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClaimMaterialityShiftConfig:
            raise TypeError(
                "ResearchEventClaimMaterialityShiftConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimMaterialityShiftConfig:
            raise TypeError(
                "config must be exactly ResearchEventClaimMaterialityShiftConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_CLAIM_MATERIALITY_SHIFT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("fresh_source_age_seconds", "stale_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_source_age_seconds <= self.fresh_source_age_seconds:
            raise ValueError(
                "stale_source_age_seconds must exceed fresh_source_age_seconds",
            )
        object.__setattr__(
            self,
            "min_pass_corroboration_count",
            _require_positive_whole_decimal(
                "min_pass_corroboration_count",
                self.min_pass_corroboration_count,
            ),
        )
        for field_name in (
            "watch_materiality_score",
            "block_materiality_score",
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
            "watch_manual_review_urgency",
            "block_manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_materiality_score <= self.watch_materiality_score:
            raise ValueError(
                "block_materiality_score must exceed watch_materiality_score",
            )
        if self.block_contradiction_pressure <= self.watch_contradiction_pressure:
            raise ValueError(
                "block_contradiction_pressure must exceed "
                "watch_contradiction_pressure",
            )
        if self.block_manual_review_urgency <= self.watch_manual_review_urgency:
            raise ValueError(
                "block_manual_review_urgency must exceed "
                "watch_manual_review_urgency",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventClaimMaterialityShiftInput:
    public_event_key: str
    event_family: str
    claim_cluster_label: str
    changed_claim_count: Decimal
    materiality_score: Decimal
    source_age_seconds: Decimal
    corroboration_count: Decimal
    contradiction_pressure: Decimal
    manual_review_urgency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClaimMaterialityShiftInput:
            raise TypeError(
                "ResearchEventClaimMaterialityShiftInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimMaterialityShiftInput:
            raise TypeError(
                "input must be exactly ResearchEventClaimMaterialityShiftInput",
            )
        _require_public_string("public_event_key", self.public_event_key)
        _require_public_string("event_family", self.event_family)
        _require_public_string("claim_cluster_label", self.claim_cluster_label)
        object.__setattr__(
            self,
            "changed_claim_count",
            _require_positive_whole_decimal(
                "changed_claim_count",
                self.changed_claim_count,
            ),
        )
        for field_name in (
            "materiality_score",
            "contradiction_pressure",
            "manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "corroboration_count",
            _require_nonnegative_whole_decimal(
                "corroboration_count",
                self.corroboration_count,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventClaimMaterialityShiftRow:
    public_event_key: str
    event_family: str
    claim_cluster_label: str
    changed_claim_count: Decimal
    materiality_score: Decimal
    source_age_seconds: Decimal
    source_recency_score: Decimal
    corroboration_count: Decimal
    corroboration_score: Decimal
    contradiction_pressure: Decimal
    manual_review_urgency: Decimal
    status: str
    public_next_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClaimMaterialityShiftRow:
            raise TypeError(
                "ResearchEventClaimMaterialityShiftRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimMaterialityShiftRow:
            raise TypeError("row must be exactly ResearchEventClaimMaterialityShiftRow")
        _require_public_string("public_event_key", self.public_event_key)
        _require_public_string("event_family", self.event_family)
        _require_public_string("claim_cluster_label", self.claim_cluster_label)
        object.__setattr__(
            self,
            "changed_claim_count",
            _require_positive_whole_decimal(
                "changed_claim_count",
                self.changed_claim_count,
            ),
        )
        for field_name in (
            "materiality_score",
            "source_recency_score",
            "corroboration_score",
            "contradiction_pressure",
            "manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "corroboration_count",
            _require_nonnegative_whole_decimal(
                "corroboration_count",
                self.corroboration_count,
            ),
        )
        _require_status("status", self.status)
        if self.public_next_step != _PUBLIC_NEXT_STEPS[self.status]:
            raise ValueError("public_next_step must match status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchEventClaimMaterialityShiftReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClaimMaterialityShiftReasonCodeCount:
            raise TypeError(
                "ResearchEventClaimMaterialityShiftReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimMaterialityShiftReasonCodeCount:
            raise TypeError(
                "reason code count must be exactly "
                "ResearchEventClaimMaterialityShiftReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventClaimMaterialityShiftReport:
    generated_at: datetime
    config_version: str
    status: str
    public_next_step: str
    event_count: Decimal
    changed_claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_materiality_score: Decimal
    average_source_recency_score: Decimal
    total_corroboration_count: Decimal
    max_contradiction_pressure: Decimal
    max_manual_review_urgency: Decimal
    rows: tuple[ResearchEventClaimMaterialityShiftRow, ...]
    reason_code_counts: tuple[ResearchEventClaimMaterialityShiftReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClaimMaterialityShiftReport:
            raise TypeError(
                "ResearchEventClaimMaterialityShiftReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimMaterialityShiftReport:
            raise TypeError(
                "report must be exactly ResearchEventClaimMaterialityShiftReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_CLAIM_MATERIALITY_SHIFT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_status("status", self.status)
        if self.public_next_step != _PUBLIC_NEXT_STEPS[self.status]:
            raise ValueError("public_next_step must match status")
        for field_name in (
            "event_count",
            "changed_claim_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_corroboration_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_materiality_score",
            "average_source_recency_score",
            "max_contradiction_pressure",
            "max_manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _require_row_tuple("rows", self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_count_tuple("reason_code_counts", self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        if self.reason_codes != tuple(item.reason_code for item in self.reason_code_counts):
            raise ValueError("reason_codes must match reason_code_counts")
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest_from_values(_report_values_without_digest(self)),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_digest_from_values(
                _report_values_without_digest(self),
            ):
                raise ValueError("derived_validation_digest mismatch")
        _reject_unsafe_public_payload(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_claim_materiality_shift_report_payload(self)

    @property
    def digest(self) -> str:
        return research_event_claim_materiality_shift_report_digest(self)


def build_research_event_claim_materiality_shift_report(
    rows: tuple[ResearchEventClaimMaterialityShiftInput, ...],
    *,
    generated_at: datetime,
    config: ResearchEventClaimMaterialityShiftConfig | None = None,
) -> ResearchEventClaimMaterialityShiftReport:
    cfg = config or ResearchEventClaimMaterialityShiftConfig()
    if type(cfg) is not ResearchEventClaimMaterialityShiftConfig:
        raise TypeError(
            "config must be exactly ResearchEventClaimMaterialityShiftConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _require_input_tuple("rows", rows)

    if not input_rows:
        reason_counts = (
            ResearchEventClaimMaterialityShiftReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ZERO,
            ),
        )
        return ResearchEventClaimMaterialityShiftReport(
            generated_at=generated_at_utc,
            config_version=cfg.config_version,
            status=STATUS_BLOCK,
            public_next_step=_PUBLIC_NEXT_STEPS[STATUS_BLOCK],
            event_count=ZERO,
            changed_claim_count=ZERO,
            pass_count=ZERO,
            watch_count=ZERO,
            block_count=ZERO,
            average_materiality_score=ZERO,
            average_source_recency_score=ZERO,
            total_corroboration_count=ZERO,
            max_contradiction_pressure=ZERO,
            max_manual_review_urgency=ZERO,
            rows=(),
            reason_code_counts=reason_counts,
            reason_codes=(NO_INPUTS_REASON,),
        )

    report_rows = tuple(_build_report_row(row, config=cfg) for row in input_rows)
    sorted_rows = tuple(
        sorted(
            report_rows,
            key=lambda row: (
                _status_rank(row.status),
                row.public_event_key,
                row.event_family,
                row.claim_cluster_label,
            ),
        ),
    )
    reason_counts = _reason_code_counts(sorted_rows)
    reason_codes = tuple(item.reason_code for item in reason_counts)
    status = _report_status(sorted_rows)

    return ResearchEventClaimMaterialityShiftReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=status,
        public_next_step=_PUBLIC_NEXT_STEPS[status],
        event_count=_count_decimal(len(sorted_rows)),
        changed_claim_count=_sum_decimal(
            tuple(row.changed_claim_count for row in sorted_rows),
        ),
        pass_count=_sum_if(sorted_rows, lambda row: row.status == STATUS_PASS),
        watch_count=_sum_if(sorted_rows, lambda row: row.status == STATUS_WATCH),
        block_count=_sum_if(sorted_rows, lambda row: row.status == STATUS_BLOCK),
        average_materiality_score=_average_decimal(
            tuple(row.materiality_score for row in sorted_rows),
        ),
        average_source_recency_score=_average_decimal(
            tuple(row.source_recency_score for row in sorted_rows),
        ),
        total_corroboration_count=_sum_decimal(
            tuple(row.corroboration_count for row in sorted_rows),
        ),
        max_contradiction_pressure=max(
            (row.contradiction_pressure for row in sorted_rows),
            default=ZERO,
        ),
        max_manual_review_urgency=max(
            (row.manual_review_urgency for row in sorted_rows),
            default=ZERO,
        ),
        rows=sorted_rows,
        reason_code_counts=reason_counts,
        reason_codes=reason_codes,
    )


def research_event_claim_materiality_shift_report_payload(
    value: ResearchEventClaimMaterialityShiftReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchEventClaimMaterialityShiftReport:
        _require_hard_flags("report", value)
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise TypeError(
            "value must be exactly ResearchEventClaimMaterialityShiftReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _validate_public_payload_digest(payload)
    return payload


def research_event_claim_materiality_shift_report_digest(
    report: ResearchEventClaimMaterialityShiftReport,
) -> str:
    if type(report) is not ResearchEventClaimMaterialityShiftReport:
        raise TypeError("report must be exactly ResearchEventClaimMaterialityShiftReport")
    _require_hard_flags("report", report)
    return _report_digest_from_values(_report_values_without_digest(report))


def _build_report_row(
    row: ResearchEventClaimMaterialityShiftInput,
    *,
    config: ResearchEventClaimMaterialityShiftConfig,
) -> ResearchEventClaimMaterialityShiftRow:
    source_recency_score = _source_recency_score(
        row.source_age_seconds,
        fresh_source_age_seconds=config.fresh_source_age_seconds,
        stale_source_age_seconds=config.stale_source_age_seconds,
    )
    corroboration_score = _corroboration_score(
        row.corroboration_count,
        min_pass_corroboration_count=config.min_pass_corroboration_count,
    )
    status = _row_status(
        materiality_score=row.materiality_score,
        source_recency_score=source_recency_score,
        corroboration_count=row.corroboration_count,
        contradiction_pressure=row.contradiction_pressure,
        manual_review_urgency=row.manual_review_urgency,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        source_recency_score=source_recency_score,
        corroboration_count=row.corroboration_count,
        contradiction_pressure=row.contradiction_pressure,
        manual_review_urgency=row.manual_review_urgency,
        config=config,
    )
    return ResearchEventClaimMaterialityShiftRow(
        public_event_key=row.public_event_key,
        event_family=row.event_family,
        claim_cluster_label=row.claim_cluster_label,
        changed_claim_count=row.changed_claim_count,
        materiality_score=row.materiality_score,
        source_age_seconds=row.source_age_seconds,
        source_recency_score=source_recency_score,
        corroboration_count=row.corroboration_count,
        corroboration_score=corroboration_score,
        contradiction_pressure=row.contradiction_pressure,
        manual_review_urgency=row.manual_review_urgency,
        status=status,
        public_next_step=_PUBLIC_NEXT_STEPS[status],
        reason_codes=reason_codes,
    )


def _source_recency_score(
    source_age_seconds: Decimal,
    *,
    fresh_source_age_seconds: Decimal,
    stale_source_age_seconds: Decimal,
) -> Decimal:
    if source_age_seconds <= fresh_source_age_seconds:
        return ONE
    if source_age_seconds >= stale_source_age_seconds:
        return ZERO
    return _bounded_ratio(
        ONE
        - (
            (source_age_seconds - fresh_source_age_seconds)
            / (stale_source_age_seconds - fresh_source_age_seconds)
        ),
    )


def _corroboration_score(
    corroboration_count: Decimal,
    *,
    min_pass_corroboration_count: Decimal,
) -> Decimal:
    return _bounded_ratio(corroboration_count / min_pass_corroboration_count)


def _row_status(
    *,
    materiality_score: Decimal,
    source_recency_score: Decimal,
    corroboration_count: Decimal,
    contradiction_pressure: Decimal,
    manual_review_urgency: Decimal,
    config: ResearchEventClaimMaterialityShiftConfig,
) -> str:
    if (
        materiality_score >= config.block_materiality_score
        or source_recency_score == ZERO
        or corroboration_count == ZERO
        or contradiction_pressure >= config.block_contradiction_pressure
        or manual_review_urgency >= config.block_manual_review_urgency
    ):
        return STATUS_BLOCK
    if (
        materiality_score >= config.watch_materiality_score
        or source_recency_score < ONE
        or corroboration_count < config.min_pass_corroboration_count
        or contradiction_pressure >= config.watch_contradiction_pressure
        or manual_review_urgency >= config.watch_manual_review_urgency
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    status: str,
    source_recency_score: Decimal,
    corroboration_count: Decimal,
    contradiction_pressure: Decimal,
    manual_review_urgency: Decimal,
    config: ResearchEventClaimMaterialityShiftConfig,
) -> tuple[str, ...]:
    reason_codes = [_shift_reason(status)]
    if source_recency_score == ZERO:
        reason_codes.append(SOURCE_STALE_REASON)
    elif source_recency_score < ONE:
        reason_codes.append(SOURCE_AGING_REASON)
    else:
        reason_codes.append(SOURCE_CURRENT_REASON)

    if corroboration_count == ZERO:
        reason_codes.append(CORROBORATION_MISSING_REASON)
    elif corroboration_count < config.min_pass_corroboration_count:
        reason_codes.append(CORROBORATION_THIN_REASON)
    else:
        reason_codes.append(CORROBORATION_SUFFICIENT_REASON)

    if contradiction_pressure >= config.block_contradiction_pressure:
        reason_codes.append(CONTRADICTION_BLOCK_REASON)
    elif contradiction_pressure >= config.watch_contradiction_pressure:
        reason_codes.append(CONTRADICTION_WATCH_REASON)
    else:
        reason_codes.append(CONTRADICTION_LOW_REASON)

    if manual_review_urgency >= config.block_manual_review_urgency:
        reason_codes.append(MANUAL_URGENCY_BLOCK_REASON)
    elif manual_review_urgency >= config.watch_manual_review_urgency:
        reason_codes.append(MANUAL_URGENCY_WATCH_REASON)
    else:
        reason_codes.append(MANUAL_URGENCY_LOW_REASON)

    return _normalize_row_reason_codes("reason_codes", tuple(reason_codes))


def _shift_reason(status: str) -> str:
    if status == STATUS_BLOCK:
        return SHIFT_BLOCK_REASON
    if status == STATUS_WATCH:
        return SHIFT_WATCH_REASON
    return SHIFT_PASS_REASON


def _report_status(rows: tuple[ResearchEventClaimMaterialityShiftRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchEventClaimMaterialityShiftRow, ...],
) -> tuple[ResearchEventClaimMaterialityShiftReasonCodeCount, ...]:
    event_count = _count_decimal(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchEventClaimMaterialityShiftReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            event_ratio=_safe_ratio(counts[reason_code], event_count),
        )
        for reason_code in _REPORT_REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _require_input_tuple(
    field_name: str,
    value: tuple[ResearchEventClaimMaterialityShiftInput, ...],
) -> tuple[ResearchEventClaimMaterialityShiftInput, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    for row in value:
        if type(row) is not ResearchEventClaimMaterialityShiftInput:
            raise TypeError(
                f"{field_name} must contain ResearchEventClaimMaterialityShiftInput",
            )
        _require_hard_flags("input", row)
    return value


def _require_row_tuple(
    field_name: str,
    value: tuple[ResearchEventClaimMaterialityShiftRow, ...],
) -> tuple[ResearchEventClaimMaterialityShiftRow, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    for row in value:
        if type(row) is not ResearchEventClaimMaterialityShiftRow:
            raise TypeError(
                f"{field_name} must contain ResearchEventClaimMaterialityShiftRow",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(
        sorted(
            value,
            key=lambda row: (
                _status_rank(row.status),
                row.public_event_key,
                row.event_family,
                row.claim_cluster_label,
            ),
        ),
    )
    if value != sorted_rows:
        raise ValueError("rows must be sorted by status and public_event_key")
    return value


def _require_reason_count_tuple(
    field_name: str,
    value: tuple[ResearchEventClaimMaterialityShiftReasonCodeCount, ...],
) -> tuple[ResearchEventClaimMaterialityShiftReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    for item in value:
        if type(item) is not ResearchEventClaimMaterialityShiftReasonCodeCount:
            raise TypeError(
                f"{field_name} must contain "
                "ResearchEventClaimMaterialityShiftReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
    sorted_values = tuple(
        sorted(value, key=lambda item: _REPORT_REASON_CODE_SEQUENCE.index(item.reason_code)),
    )
    if value != sorted_values:
        raise ValueError("reason_code_counts must follow known reason sequence")
    return value


def _validate_row_consistency(row: ResearchEventClaimMaterialityShiftRow) -> None:
    if row.status not in CLAIM_MATERIALITY_SHIFT_STATUSES:
        raise ValueError("status must be pass, watch, or block")
    if row.reason_codes[0] != _shift_reason(row.status):
        raise ValueError("reason_codes must match status")


def _validate_report_consistency(report: ResearchEventClaimMaterialityShiftReport) -> None:
    if report.event_count != _count_decimal(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.changed_claim_count != _sum_decimal(
        tuple(row.changed_claim_count for row in report.rows),
    ):
        raise ValueError("changed_claim_count must match rows")
    if report.pass_count != _sum_if(report.rows, lambda row: row.status == STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _sum_if(report.rows, lambda row: row.status == STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _sum_if(report.rows, lambda row: row.status == STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_materiality_score != _average_decimal(
        tuple(row.materiality_score for row in report.rows),
    ):
        raise ValueError("average_materiality_score must match rows")
    if report.average_source_recency_score != _average_decimal(
        tuple(row.source_recency_score for row in report.rows),
    ):
        raise ValueError("average_source_recency_score must match rows")
    if report.total_corroboration_count != _sum_decimal(
        tuple(row.corroboration_count for row in report.rows),
    ):
        raise ValueError("total_corroboration_count must match rows")
    if report.max_contradiction_pressure != max(
        (row.contradiction_pressure for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.max_manual_review_urgency != max(
        (row.manual_review_urgency for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_manual_review_urgency must match rows")
    expected_status = STATUS_BLOCK if not report.rows else _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")


def _normalize_row_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    unique_values = frozenset(value)
    if len(unique_values) != len(value):
        raise ValueError(f"{field_name} contains duplicate reason_code values")
    for reason_code in unique_values:
        _require_reason_code(field_name, reason_code)
    return tuple(
        reason_code for reason_code in _ROW_REASON_CODE_SEQUENCE if reason_code in unique_values
    )


def _normalize_report_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    unique_values = frozenset(value)
    if len(unique_values) != len(value):
        raise ValueError(f"{field_name} contains duplicate reason_code values")
    for reason_code in unique_values:
        _require_reason_code(field_name, reason_code)
    return tuple(
        reason_code
        for reason_code in _REPORT_REASON_CODE_SEQUENCE
        if reason_code in unique_values
    )


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    if value not in _REPORT_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} contains unknown reason_code")


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if value not in CLAIM_MATERIALITY_SHIFT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _status_rank(status: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[status]


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _require_bool(field_name: str, value: bool) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be exactly bool")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        flag_value = getattr(value, flag_name, None)
        _require_bool(flag_name, flag_value)
        if flag_value is not True:
            raise ValueError(f"{field_name}.{flag_name} must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.microsecond:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    result = _require_decimal(field_name, value)
    if result < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return result


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    result = _require_decimal(field_name, value)
    if result <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return result


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    result = _require_decimal(field_name, value)
    if result < ZERO or result > ONE:
        raise ValueError(f"{field_name} must be a ratio")
    return result


def _require_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    result = _require_positive_decimal(field_name, value)
    if result != result.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return result


def _require_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    result = _require_nonnegative_decimal(field_name, value)
    if result != result.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return result


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT)


def _bounded_ratio(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return _require_ratio_decimal("ratio", value)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _sum_if(
    rows: tuple[ResearchEventClaimMaterialityShiftRow, ...],
    predicate: Any,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if predicate(row)))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(_sum_decimal(values) / _count_decimal(len(values)))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _bounded_ratio(numerator / denominator)


def _report_values_without_digest(
    report: ResearchEventClaimMaterialityShiftReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != _DERIVED_DIGEST_FIELD
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(payload)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_public_payload_digest(payload: dict[str, Any]) -> None:
    digest_value = payload.get(_DERIVED_DIGEST_FIELD)
    if digest_value is None:
        return
    _require_sha256_digest(_DERIVED_DIGEST_FIELD, digest_value)
    values = {key: item for key, item in payload.items() if key != _DERIVED_DIGEST_FIELD}
    if digest_value != _report_digest_from_values(values):
        raise ValueError("derived_validation_digest mismatch")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a SHA-256 digest") from exc
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    return value


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if type(value) is str:
        _reject_unsafe_public_string("JSON string", value)
        return value
    if isinstance(value, Mapping):
        return {
            _json_ready_key(key): _json_ready(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError(f"unsupported JSON value type: {type(value).__name__}")


def _json_ready_key(value: object) -> str:
    if type(value) is not str:
        raise ValueError("JSON object keys must be strings")
    _reject_unsafe_public_string("JSON key", value)
    return value


def _copy_json_object(value: dict[str, Any]) -> dict[str, Any]:
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _copy_json_value(value: object) -> object:
    if value is None:
        return None
    if type(value) is str:
        _reject_unsafe_public_string("payload string", value)
        return value
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("payload numeric values must use Decimal strings")
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if type(value) is dict:
        return {
            _json_ready_key(key): _copy_json_value(item)
            for key, item in value.items()
        }
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _reject_unsafe_public_payload(value: object) -> None:
    if value is None:
        return
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(asdict(value))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_unsafe_public_string("payload key", str(key))
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_public_string("payload string", value)
