"""Report-only primary evidence crosscheck priority report builder.

The module is deterministic and side-effect free. Callers provide sanitized
local crosscheck metrics; the report returns a public-safe priority snapshot
without storage, network, wallet, order, sizing, recommendation, or live
trading surfaces.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_PRIMARY_EVIDENCE_CROSSCHECK_PRIORITY_REPORT_CONFIG_VERSION = (
    "research-source-primary-evidence-crosscheck-priority-report-v0"
)
RESEARCH_SOURCE_PRIMARY_EVIDENCE_CROSSCHECK_PRIORITY_STATUSES = (
    "pass",
    "watch",
    "block",
)

EMPTY_REASON = "research_source_primary_evidence_crosscheck_priority_empty"
CLEAR_REASON = "research_source_primary_evidence_crosscheck_priority_clear"
LOW_AUTHORITY_WATCH_REASON = (
    "research_source_primary_evidence_crosscheck_priority_low_authority_watch"
)
LOW_AUTHORITY_BLOCK_REASON = (
    "research_source_primary_evidence_crosscheck_priority_low_authority_block"
)
STALE_PRIMARY_WATCH_REASON = (
    "research_source_primary_evidence_crosscheck_priority_stale_primary_watch"
)
STALE_PRIMARY_BLOCK_REASON = (
    "research_source_primary_evidence_crosscheck_priority_stale_primary_block"
)
THIN_CROSSCHECK_WATCH_REASON = (
    "research_source_primary_evidence_crosscheck_priority_thin_crosscheck_watch"
)
THIN_CROSSCHECK_BLOCK_REASON = (
    "research_source_primary_evidence_crosscheck_priority_thin_crosscheck_block"
)
INDEPENDENCE_WATCH_REASON = (
    "research_source_primary_evidence_crosscheck_priority_independence_watch"
)
INDEPENDENCE_BLOCK_REASON = (
    "research_source_primary_evidence_crosscheck_priority_independence_block"
)
CONTRADICTION_WATCH_REASON = (
    "research_source_primary_evidence_crosscheck_priority_contradiction_watch"
)
CONTRADICTION_BLOCK_REASON = (
    "research_source_primary_evidence_crosscheck_priority_contradiction_block"
)
RETRIEVAL_GAP_WATCH_REASON = (
    "research_source_primary_evidence_crosscheck_priority_retrieval_gap_watch"
)
RETRIEVAL_GAP_BLOCK_REASON = (
    "research_source_primary_evidence_crosscheck_priority_retrieval_gap_block"
)
LOW_EXTRACTION_WATCH_REASON = (
    "research_source_primary_evidence_crosscheck_priority_low_extraction_watch"
)
LOW_EXTRACTION_BLOCK_REASON = (
    "research_source_primary_evidence_crosscheck_priority_low_extraction_block"
)
RESOLUTION_WINDOW_WATCH_REASON = (
    "research_source_primary_evidence_crosscheck_priority_resolution_window_watch"
)
RESOLUTION_WINDOW_BLOCK_REASON = (
    "research_source_primary_evidence_crosscheck_priority_resolution_window_block"
)

ROW_REASON_CODES = (
    CLEAR_REASON,
    LOW_AUTHORITY_BLOCK_REASON,
    STALE_PRIMARY_BLOCK_REASON,
    THIN_CROSSCHECK_BLOCK_REASON,
    INDEPENDENCE_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    RETRIEVAL_GAP_BLOCK_REASON,
    LOW_EXTRACTION_BLOCK_REASON,
    RESOLUTION_WINDOW_BLOCK_REASON,
    LOW_AUTHORITY_WATCH_REASON,
    STALE_PRIMARY_WATCH_REASON,
    THIN_CROSSCHECK_WATCH_REASON,
    INDEPENDENCE_WATCH_REASON,
    CONTRADICTION_WATCH_REASON,
    RETRIEVAL_GAP_WATCH_REASON,
    LOW_EXTRACTION_WATCH_REASON,
    RESOLUTION_WINDOW_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (EMPTY_REASON, CLEAR_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

AUTHORITY_WEIGHT = Decimal("0.150000")
FRESHNESS_WEIGHT = Decimal("0.172500")
CROSSCHECK_WEIGHT = Decimal("0.132500")
INDEPENDENCE_WEIGHT = Decimal("0.132500")
CONTRADICTION_WEIGHT = Decimal("0.112500")
RETRIEVAL_GAP_WEIGHT = Decimal("0.125000")
EXTRACTION_WEIGHT = Decimal("0.100000")
RESOLUTION_WINDOW_WEIGHT = Decimal("0.075000")

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_TOKENS = frozenset(
    (
        "auth",
        "buy",
        "candidate",
        "database",
        "dsn",
        "live",
        "market",
        "mutation",
        "network",
        "order",
        "persist",
        "question",
        "raw",
        "recommendation",
        "secret",
        "sell",
        "signing",
        "sizing",
        "slug",
        "table",
        "token",
        "trade",
        "wallet",
    ),
)
UNSAFE_TOKEN_PAIRS = (
    frozenset(("source", "text")),
    frozenset(("source", "url")),
    frozenset(("candidate", "id")),
    frozenset(("market", "id")),
    frozenset(("table", "name")),
)


@dataclass(frozen=True)
class ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_PRIMARY_EVIDENCE_CROSSCHECK_PRIORITY_REPORT_CONFIG_VERSION
    )
    authority_watch_floor: Decimal = Decimal("0.700000")
    authority_block_floor: Decimal = Decimal("0.500000")
    stale_watch_age_seconds: Decimal = Decimal("1800.000000")
    stale_block_age_seconds: Decimal = Decimal("3600.000000")
    crosscheck_watch_count: Decimal = Decimal("2.000000")
    crosscheck_block_count: Decimal = Decimal("0.000000")
    independent_evidence_watch_count: Decimal = Decimal("2.000000")
    independent_evidence_block_count: Decimal = Decimal("0.000000")
    contradiction_watch_pressure: Decimal = Decimal("0.300000")
    contradiction_block_pressure: Decimal = Decimal("0.600000")
    retrieval_gap_watch_score: Decimal = Decimal("0.300000")
    retrieval_gap_block_score: Decimal = Decimal("0.600000")
    extraction_confidence_watch_floor: Decimal = Decimal("0.800000")
    extraction_confidence_block_floor: Decimal = Decimal("0.600000")
    resolution_watch_seconds_remaining: Decimal = Decimal("1800.000000")
    resolution_block_seconds_remaining: Decimal = Decimal("600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig:
            raise TypeError(
                "ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig)
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_PRIMARY_EVIDENCE_CROSSCHECK_PRIORITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "authority_watch_floor",
            "authority_block_floor",
            "contradiction_watch_pressure",
            "contradiction_block_pressure",
            "retrieval_gap_watch_score",
            "retrieval_gap_block_score",
            "extraction_confidence_watch_floor",
            "extraction_confidence_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_watch_age_seconds",
            "stale_block_age_seconds",
            "crosscheck_watch_count",
            "independent_evidence_watch_count",
            "resolution_watch_seconds_remaining",
            "resolution_block_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "crosscheck_block_count",
            "independent_evidence_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryEvidenceCrosscheckPriorityInput:
    evidence_key: str
    primary_authority_score: Decimal
    latest_primary_age_seconds: Decimal
    crosscheck_count: Decimal
    independent_evidence_count: Decimal
    contradiction_pressure: Decimal
    retrieval_gap_score: Decimal
    extraction_confidence: Decimal
    resolution_window_seconds_remaining: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryEvidenceCrosscheckPriorityInput:
            raise TypeError(
                "ResearchSourcePrimaryEvidenceCrosscheckPriorityInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourcePrimaryEvidenceCrosscheckPriorityInput)
        object.__setattr__(
            self,
            "evidence_key",
            _require_public_identifier("evidence_key", self.evidence_key),
        )
        for field_name in (
            "primary_authority_score",
            "contradiction_pressure",
            "retrieval_gap_score",
            "extraction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latest_primary_age_seconds",
            "resolution_window_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("crosscheck_count", "independent_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_public_payload("input", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryEvidenceCrosscheckPriorityPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryEvidenceCrosscheckPriorityPublicPayloadItem:
            raise TypeError(
                "ResearchSourcePrimaryEvidenceCrosscheckPriorityPublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourcePrimaryEvidenceCrosscheckPriorityPublicPayloadItem,
        )
        object.__setattr__(self, "key", _require_public_identifier("key", self.key))
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryEvidenceCrosscheckPriorityRow:
    evidence_key: str
    primary_authority_score: Decimal
    authority_band: str
    latest_primary_age_seconds: Decimal
    freshness_band: str
    crosscheck_count: Decimal
    crosscheck_depth_score: Decimal
    independent_evidence_count: Decimal
    independent_evidence_score: Decimal
    contradiction_pressure: Decimal
    retrieval_gap_score: Decimal
    extraction_confidence: Decimal
    resolution_window_seconds_remaining: Decimal
    resolution_window_pressure_score: Decimal
    priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryEvidenceCrosscheckPriorityRow:
            raise TypeError(
                "ResearchSourcePrimaryEvidenceCrosscheckPriorityRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourcePrimaryEvidenceCrosscheckPriorityRow)
        object.__setattr__(
            self,
            "evidence_key",
            _require_public_identifier("evidence_key", self.evidence_key),
        )
        for field_name in (
            "primary_authority_score",
            "crosscheck_depth_score",
            "independent_evidence_score",
            "contradiction_pressure",
            "retrieval_gap_score",
            "extraction_confidence",
            "resolution_window_pressure_score",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latest_primary_age_seconds",
            "resolution_window_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("crosscheck_count", "independent_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "authority_band",
            _require_band("authority_band", self.authority_band, ("high", "medium", "low")),
        )
        object.__setattr__(
            self,
            "freshness_band",
            _require_band("freshness_band", self.freshness_band, ("fresh", "aging", "stale")),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryEvidenceCrosscheckPriorityReport:
    generated_at: datetime
    config_version: str
    item_count: Decimal
    pass_item_count: Decimal
    watch_item_count: Decimal
    block_item_count: Decimal
    low_authority_count: Decimal
    stale_primary_evidence_count: Decimal
    thin_crosscheck_count: Decimal
    insufficient_independent_evidence_count: Decimal
    contradiction_pressure_count: Decimal
    retrieval_gap_count: Decimal
    low_extraction_confidence_count: Decimal
    resolution_window_count: Decimal
    highest_priority_score: Decimal
    oldest_latest_primary_age_seconds: Decimal
    lowest_primary_authority_score: Decimal
    lowest_extraction_confidence: Decimal
    highest_contradiction_pressure: Decimal
    highest_retrieval_gap_score: Decimal
    nearest_resolution_window_seconds_remaining: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourcePrimaryEvidenceCrosscheckPriorityRow, ...]
    public_payload: tuple[
        ResearchSourcePrimaryEvidenceCrosscheckPriorityPublicPayloadItem,
        ...,
    ] = ()
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryEvidenceCrosscheckPriorityReport:
            raise TypeError(
                "ResearchSourcePrimaryEvidenceCrosscheckPriorityReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourcePrimaryEvidenceCrosscheckPriorityReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_PRIMARY_EVIDENCE_CROSSCHECK_PRIORITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "item_count",
            "pass_item_count",
            "watch_item_count",
            "block_item_count",
            "low_authority_count",
            "stale_primary_evidence_count",
            "thin_crosscheck_count",
            "insufficient_independent_evidence_count",
            "contradiction_pressure_count",
            "retrieval_gap_count",
            "low_extraction_confidence_count",
            "resolution_window_count",
            "oldest_latest_primary_age_seconds",
            "nearest_resolution_window_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_priority_score",
            "lowest_primary_authority_score",
            "lowest_extraction_confidence",
            "highest_contradiction_pressure",
            "highest_retrieval_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_public_payload("report", self)
        expected_digest = _report_digest_from_public_payload(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
            return
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_sha256("derived_validation_digest", self.derived_validation_digest),
        )
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match public payload")

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(self)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_public_payload("payload", payload, allow_json_containers=True)
        _verify_public_digest(payload)
        return payload


def build_research_source_primary_evidence_crosscheck_priority_report(
    inputs: list[ResearchSourcePrimaryEvidenceCrosscheckPriorityInput]
    | tuple[ResearchSourcePrimaryEvidenceCrosscheckPriorityInput, ...],
    *,
    config: ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig,
    generated_at: datetime,
    public_payload: list[ResearchSourcePrimaryEvidenceCrosscheckPriorityPublicPayloadItem]
    | tuple[ResearchSourcePrimaryEvidenceCrosscheckPriorityPublicPayloadItem, ...] = (),
) -> ResearchSourcePrimaryEvidenceCrosscheckPriorityReport:
    if type(config) is not ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig:
        raise ValueError(
            "config must be a ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig",
        )
    _require_hard_flags("config", config)
    rows = _priority_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourcePrimaryEvidenceCrosscheckPriorityReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        item_count=_count(len(rows)),
        pass_item_count=_status_count(rows, "pass"),
        watch_item_count=_status_count(rows, "watch"),
        block_item_count=_status_count(rows, "block"),
        low_authority_count=_reason_count(
            rows,
            (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON),
        ),
        stale_primary_evidence_count=_reason_count(
            rows,
            (STALE_PRIMARY_WATCH_REASON, STALE_PRIMARY_BLOCK_REASON),
        ),
        thin_crosscheck_count=_reason_count(
            rows,
            (THIN_CROSSCHECK_WATCH_REASON, THIN_CROSSCHECK_BLOCK_REASON),
        ),
        insufficient_independent_evidence_count=_reason_count(
            rows,
            (INDEPENDENCE_WATCH_REASON, INDEPENDENCE_BLOCK_REASON),
        ),
        contradiction_pressure_count=_reason_count(
            rows,
            (CONTRADICTION_WATCH_REASON, CONTRADICTION_BLOCK_REASON),
        ),
        retrieval_gap_count=_reason_count(
            rows,
            (RETRIEVAL_GAP_WATCH_REASON, RETRIEVAL_GAP_BLOCK_REASON),
        ),
        low_extraction_confidence_count=_reason_count(
            rows,
            (LOW_EXTRACTION_WATCH_REASON, LOW_EXTRACTION_BLOCK_REASON),
        ),
        resolution_window_count=_reason_count(
            rows,
            (RESOLUTION_WINDOW_WATCH_REASON, RESOLUTION_WINDOW_BLOCK_REASON),
        ),
        highest_priority_score=max(
            (row.priority_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_latest_primary_age_seconds=max(
            (row.latest_primary_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_primary_authority_score=min(
            (row.primary_authority_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_extraction_confidence=min(
            (row.extraction_confidence for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_contradiction_pressure=max(
            (row.contradiction_pressure for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_retrieval_gap_score=max(
            (row.retrieval_gap_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        nearest_resolution_window_seconds_remaining=min(
            (row.resolution_window_seconds_remaining for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
        public_payload=_normalize_public_payload(public_payload),
    )


def research_source_primary_evidence_crosscheck_priority_report_payload(
    report: ResearchSourcePrimaryEvidenceCrosscheckPriorityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourcePrimaryEvidenceCrosscheckPriorityReport:
        raise ValueError(
            "report must be a ResearchSourcePrimaryEvidenceCrosscheckPriorityReport",
        )
    validate_research_source_primary_evidence_crosscheck_priority_report_digest(report)
    _require_hard_flags("report", report)
    return report.payload


def research_source_primary_evidence_crosscheck_priority_report_digest(
    report: ResearchSourcePrimaryEvidenceCrosscheckPriorityReport,
) -> str:
    if type(report) is not ResearchSourcePrimaryEvidenceCrosscheckPriorityReport:
        raise ValueError(
            "report must be a ResearchSourcePrimaryEvidenceCrosscheckPriorityReport",
        )
    return _report_digest_from_public_payload(report)


def validate_research_source_primary_evidence_crosscheck_priority_report_digest(
    report: ResearchSourcePrimaryEvidenceCrosscheckPriorityReport,
) -> None:
    if type(report) is not ResearchSourcePrimaryEvidenceCrosscheckPriorityReport:
        raise ValueError(
            "report must be a ResearchSourcePrimaryEvidenceCrosscheckPriorityReport",
        )
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match public payload")


def _priority_rows(
    inputs: tuple[ResearchSourcePrimaryEvidenceCrosscheckPriorityInput, ...],
    *,
    config: ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig,
) -> tuple[ResearchSourcePrimaryEvidenceCrosscheckPriorityRow, ...]:
    return tuple(sorted((_priority_row(row, config=config) for row in inputs), key=_row_sort_key))


def _priority_row(
    row: ResearchSourcePrimaryEvidenceCrosscheckPriorityInput,
    *,
    config: ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig,
) -> ResearchSourcePrimaryEvidenceCrosscheckPriorityRow:
    reason_codes = _row_reason_codes(row, config=config)
    crosscheck_depth_score = _depth_score(row.crosscheck_count, config.crosscheck_watch_count)
    independent_evidence_score = _depth_score(
        row.independent_evidence_count,
        config.independent_evidence_watch_count,
    )
    resolution_window_pressure_score = _resolution_window_pressure_score(
        row.resolution_window_seconds_remaining,
        config=config,
    )
    return ResearchSourcePrimaryEvidenceCrosscheckPriorityRow(
        evidence_key=row.evidence_key,
        primary_authority_score=row.primary_authority_score,
        authority_band=_authority_band(row.primary_authority_score, config=config),
        latest_primary_age_seconds=row.latest_primary_age_seconds,
        freshness_band=_freshness_band(row.latest_primary_age_seconds, config=config),
        crosscheck_count=row.crosscheck_count,
        crosscheck_depth_score=crosscheck_depth_score,
        independent_evidence_count=row.independent_evidence_count,
        independent_evidence_score=independent_evidence_score,
        contradiction_pressure=row.contradiction_pressure,
        retrieval_gap_score=row.retrieval_gap_score,
        extraction_confidence=row.extraction_confidence,
        resolution_window_seconds_remaining=row.resolution_window_seconds_remaining,
        resolution_window_pressure_score=resolution_window_pressure_score,
        priority_score=_priority_score(
            row,
            crosscheck_depth_score=crosscheck_depth_score,
            independent_evidence_score=independent_evidence_score,
            resolution_window_pressure_score=resolution_window_pressure_score,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchSourcePrimaryEvidenceCrosscheckPriorityInput,
    *,
    config: ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.primary_authority_score <= config.authority_block_floor:
        reasons.append(LOW_AUTHORITY_BLOCK_REASON)
    elif row.primary_authority_score < config.authority_watch_floor:
        reasons.append(LOW_AUTHORITY_WATCH_REASON)
    if row.latest_primary_age_seconds >= config.stale_block_age_seconds:
        reasons.append(STALE_PRIMARY_BLOCK_REASON)
    elif row.latest_primary_age_seconds > config.stale_watch_age_seconds:
        reasons.append(STALE_PRIMARY_WATCH_REASON)
    if row.crosscheck_count <= config.crosscheck_block_count:
        reasons.append(THIN_CROSSCHECK_BLOCK_REASON)
    elif row.crosscheck_count < config.crosscheck_watch_count:
        reasons.append(THIN_CROSSCHECK_WATCH_REASON)
    if row.independent_evidence_count <= config.independent_evidence_block_count:
        reasons.append(INDEPENDENCE_BLOCK_REASON)
    elif row.independent_evidence_count < config.independent_evidence_watch_count:
        reasons.append(INDEPENDENCE_WATCH_REASON)
    if row.contradiction_pressure >= config.contradiction_block_pressure:
        reasons.append(CONTRADICTION_BLOCK_REASON)
    elif row.contradiction_pressure >= config.contradiction_watch_pressure:
        reasons.append(CONTRADICTION_WATCH_REASON)
    if row.retrieval_gap_score >= config.retrieval_gap_block_score:
        reasons.append(RETRIEVAL_GAP_BLOCK_REASON)
    elif row.retrieval_gap_score >= config.retrieval_gap_watch_score:
        reasons.append(RETRIEVAL_GAP_WATCH_REASON)
    if row.extraction_confidence <= config.extraction_confidence_block_floor:
        reasons.append(LOW_EXTRACTION_BLOCK_REASON)
    elif row.extraction_confidence < config.extraction_confidence_watch_floor:
        reasons.append(LOW_EXTRACTION_WATCH_REASON)
    if row.resolution_window_seconds_remaining <= config.resolution_block_seconds_remaining:
        reasons.append(RESOLUTION_WINDOW_BLOCK_REASON)
    elif row.resolution_window_seconds_remaining < config.resolution_watch_seconds_remaining:
        reasons.append(RESOLUTION_WINDOW_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _priority_score(
    row: ResearchSourcePrimaryEvidenceCrosscheckPriorityInput,
    *,
    crosscheck_depth_score: Decimal,
    independent_evidence_score: Decimal,
    resolution_window_pressure_score: Decimal,
    config: ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        authority_gap = ONE - row.primary_authority_score
        freshness_pressure = min(row.latest_primary_age_seconds / config.stale_block_age_seconds, ONE)
        crosscheck_gap = ONE - crosscheck_depth_score
        independence_gap = ONE - independent_evidence_score
        extraction_gap = ONE - row.extraction_confidence
        score = (
            authority_gap * AUTHORITY_WEIGHT
            + freshness_pressure * FRESHNESS_WEIGHT
            + crosscheck_gap * CROSSCHECK_WEIGHT
            + independence_gap * INDEPENDENCE_WEIGHT
            + row.contradiction_pressure * CONTRADICTION_WEIGHT
            + row.retrieval_gap_score * RETRIEVAL_GAP_WEIGHT
            + extraction_gap * EXTRACTION_WEIGHT
            + resolution_window_pressure_score * RESOLUTION_WINDOW_WEIGHT
        )
        return min(score, ONE).quantize(QUANT)


def _depth_score(value: Decimal, target: Decimal) -> Decimal:
    return min(_ratio(value, target), ONE)


def _resolution_window_pressure_score(
    value: Decimal,
    *,
    config: ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        open_fraction = min(value / config.resolution_watch_seconds_remaining, ONE)
        return (ONE - open_fraction).quantize(QUANT)


def _authority_band(
    value: Decimal,
    *,
    config: ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig,
) -> str:
    if value >= config.authority_watch_floor:
        return "high"
    if value <= config.authority_block_floor:
        return "low"
    return "medium"


def _freshness_band(
    value: Decimal,
    *,
    config: ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig,
) -> str:
    if value <= config.stale_watch_age_seconds:
        return "fresh"
    if value < config.stale_block_age_seconds:
        return "aging"
    return "stale"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourcePrimaryEvidenceCrosscheckPriorityRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourcePrimaryEvidenceCrosscheckPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason
        for reason in REPORT_TRIGGER_REASON_CODES
        if any(reason in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _row_sort_key(row: ResearchSourcePrimaryEvidenceCrosscheckPriorityRow) -> tuple[Decimal, str]:
    return (-row.priority_score, row.evidence_key)


def _status_count(
    rows: tuple[ResearchSourcePrimaryEvidenceCrosscheckPriorityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourcePrimaryEvidenceCrosscheckPriorityRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourcePrimaryEvidenceCrosscheckPriorityInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourcePrimaryEvidenceCrosscheckPriorityInput:
            raise ValueError(
                "inputs must contain ResearchSourcePrimaryEvidenceCrosscheckPriorityInput",
            )
        _require_hard_flags("input", row)
        if row.evidence_key in seen:
            raise ValueError("inputs must be unique by evidence_key")
        seen.add(row.evidence_key)
    return tuple(sorted(rows, key=lambda row: row.evidence_key))


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourcePrimaryEvidenceCrosscheckPriorityRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourcePrimaryEvidenceCrosscheckPriorityRow:
            raise ValueError("rows must contain ResearchSourcePrimaryEvidenceCrosscheckPriorityRow")
        _require_hard_flags("row", row)
        if row.evidence_key in seen:
            raise ValueError("rows must be unique by evidence_key")
        seen.add(row.evidence_key)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_public_payload(
    value: object,
) -> tuple[ResearchSourcePrimaryEvidenceCrosscheckPriorityPublicPayloadItem, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("public_payload must be a list or tuple")
    items = tuple(value)
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchSourcePrimaryEvidenceCrosscheckPriorityPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchSourcePrimaryEvidenceCrosscheckPriorityPublicPayloadItem",
            )
        _require_hard_flags("public payload item", item)
        if item.key in seen:
            raise ValueError("public_payload must be unique by key")
        seen.add(item.key)
    return tuple(sorted(items, key=lambda item: item.key))


def _validate_config(config: ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig) -> None:
    if config.authority_block_floor > config.authority_watch_floor:
        raise ValueError("authority_block_floor must not exceed authority_watch_floor")
    if config.stale_watch_age_seconds >= config.stale_block_age_seconds:
        raise ValueError("stale_watch_age_seconds must be less than stale_block_age_seconds")
    if config.crosscheck_block_count >= config.crosscheck_watch_count:
        raise ValueError("crosscheck_block_count must be less than crosscheck_watch_count")
    if config.independent_evidence_block_count >= config.independent_evidence_watch_count:
        raise ValueError(
            "independent_evidence_block_count must be less than "
            "independent_evidence_watch_count",
        )
    if config.contradiction_watch_pressure > config.contradiction_block_pressure:
        raise ValueError(
            "contradiction_watch_pressure must not exceed contradiction_block_pressure",
        )
    if config.retrieval_gap_watch_score > config.retrieval_gap_block_score:
        raise ValueError("retrieval_gap_watch_score must not exceed retrieval_gap_block_score")
    if config.extraction_confidence_block_floor > config.extraction_confidence_watch_floor:
        raise ValueError(
            "extraction_confidence_block_floor must not exceed "
            "extraction_confidence_watch_floor",
        )
    if config.resolution_block_seconds_remaining > config.resolution_watch_seconds_remaining:
        raise ValueError(
            "resolution_block_seconds_remaining must not exceed "
            "resolution_watch_seconds_remaining",
        )


def _validate_row(row: ResearchSourcePrimaryEvidenceCrosscheckPriorityRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use clear reason")


def _validate_report(report: ResearchSourcePrimaryEvidenceCrosscheckPriorityReport) -> None:
    if report.item_count != _count(len(report.rows)):
        raise ValueError("item_count must match rows")
    for status, field_name in (
        ("pass", "pass_item_count"),
        ("watch", "watch_item_count"),
        ("block", "block_item_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        ("low_authority_count", (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON)),
        (
            "stale_primary_evidence_count",
            (STALE_PRIMARY_WATCH_REASON, STALE_PRIMARY_BLOCK_REASON),
        ),
        (
            "thin_crosscheck_count",
            (THIN_CROSSCHECK_WATCH_REASON, THIN_CROSSCHECK_BLOCK_REASON),
        ),
        (
            "insufficient_independent_evidence_count",
            (INDEPENDENCE_WATCH_REASON, INDEPENDENCE_BLOCK_REASON),
        ),
        (
            "contradiction_pressure_count",
            (CONTRADICTION_WATCH_REASON, CONTRADICTION_BLOCK_REASON),
        ),
        ("retrieval_gap_count", (RETRIEVAL_GAP_WATCH_REASON, RETRIEVAL_GAP_BLOCK_REASON)),
        (
            "low_extraction_confidence_count",
            (LOW_EXTRACTION_WATCH_REASON, LOW_EXTRACTION_BLOCK_REASON),
        ),
        (
            "resolution_window_count",
            (RESOLUTION_WINDOW_WATCH_REASON, RESOLUTION_WINDOW_BLOCK_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.highest_priority_score != max(
        (row.priority_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_priority_score must match rows")
    if report.oldest_latest_primary_age_seconds != max(
        (row.latest_primary_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_latest_primary_age_seconds must match rows")
    if report.lowest_primary_authority_score != min(
        (row.primary_authority_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_primary_authority_score must match rows")
    if report.lowest_extraction_confidence != min(
        (row.extraction_confidence for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_extraction_confidence must match rows")
    if report.highest_contradiction_pressure != max(
        (row.contradiction_pressure for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_contradiction_pressure must match rows")
    if report.highest_retrieval_gap_score != max(
        (row.retrieval_gap_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_retrieval_gap_score must match rows")
    if report.nearest_resolution_window_seconds_remaining != min(
        (row.resolution_window_seconds_remaining for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("nearest_resolution_window_seconds_remaining must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic priority sort")


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _require_exact_type(value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"value must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _require_positive_decimal("ratio denominator", denominator)
    with localcontext(DECIMAL_CONTEXT):
        return (numerator_value / denominator_value).quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_band(field_name: str, value: object, supported_values: tuple[str, ...]) -> str:
    if type(value) is not str or value not in supported_values:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_SOURCE_PRIMARY_EVIDENCE_CROSSCHECK_PRIORITY_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_public_text_value(field_name, value)
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_public_text_value(field_name, value)
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    supported_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in supported_values:
            raise ValueError(f"{field_name} contains unsupported reason code")
        seen.add(reason_code)
    if not seen:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(reason for reason in supported_values if reason in seen)


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _report_digest_from_public_payload(
    report: ResearchSourcePrimaryEvidenceCrosscheckPriorityReport,
) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload("digest payload", payload, allow_json_containers=True)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    if digest != sha256(encoded).hexdigest():
        raise ValueError("derived_validation_digest must match public payload")


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
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_public_text_value(field.name, field.name)
            _reject_public_payload(
                label,
                getattr(value, field.name),
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, dict):
        if not allow_json_containers:
            raise ValueError(f"{label} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_public_text_value(key, key)
            _reject_public_payload(label, item, allow_json_containers=True)
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{label} must remain constructor-normalized")
        for item in value:
            _reject_public_payload(label, item, allow_json_containers=allow_json_containers)
        return
    if type(value) is str:
        _reject_public_text_value(label, value)
        return
    if type(value) in (bool, Decimal, datetime):
        return
    raise ValueError(f"{label} contains unsupported public payload value")


def _reject_public_text_value(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} contains unsafe text")
    if "/" in lowered or "\\" in lowered:
        raise ValueError(f"{field_name} contains unsafe text")
    tokens = set(re.findall(r"[a-z0-9]+", lowered))
    if tokens & UNSAFE_PUBLIC_TOKENS:
        raise ValueError(f"{field_name} contains unsafe text")
    for token_pair in UNSAFE_TOKEN_PAIRS:
        if token_pair.issubset(tokens):
            raise ValueError(f"{field_name} contains unsafe text")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_PRIMARY_EVIDENCE_CROSSCHECK_PRIORITY_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_PRIMARY_EVIDENCE_CROSSCHECK_PRIORITY_STATUSES",
    "ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig",
    "ResearchSourcePrimaryEvidenceCrosscheckPriorityInput",
    "ResearchSourcePrimaryEvidenceCrosscheckPriorityPublicPayloadItem",
    "ResearchSourcePrimaryEvidenceCrosscheckPriorityReport",
    "ResearchSourcePrimaryEvidenceCrosscheckPriorityRow",
    "build_research_source_primary_evidence_crosscheck_priority_report",
    "research_source_primary_evidence_crosscheck_priority_report_digest",
    "research_source_primary_evidence_crosscheck_priority_report_payload",
    "validate_research_source_primary_evidence_crosscheck_priority_report_digest",
)
