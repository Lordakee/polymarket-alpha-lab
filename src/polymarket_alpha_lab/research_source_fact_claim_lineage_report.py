"""Report-only fact-claim lineage quality snapshot."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_FACT_CLAIM_LINEAGE_CONFIG_VERSION = (
    "research-source-fact-claim-lineage-report"
)

LINEAGE_STATUSES = ("pass", "watch", "block")
PASS_REASON_CODE = "fact_claim_lineage_pass"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400.000000")
_MICROSECOND = Decimal("1000000.000000")
_DECIMAL_CONTEXT_PRECISION = 28
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_DOMAIN_LIKE_RE = re.compile(
    r"(?i)(?:^|[^A-Za-z0-9])(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,63}(?:$|[^A-Za-z0-9])",
)
_UUID_LIKE_RE = re.compile(
    r"(?i)^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
)
_HEX_ID_LIKE_RE = re.compile(r"(?i)^0x[0-9a-f]{32,}$")
_JWT_LIKE_RE = re.compile(
    r"^[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}$",
)
_STATUSES = frozenset(LINEAGE_STATUSES)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
)
_REASON_CODE_SEQUENCE = (
    "empty_evidence",
    "source_authority_watch",
    "freshness_watch",
    "corroboration_hops_watch",
    "contradiction_severity_watch",
    "contradiction_severity_block",
    "extraction_confidence_watch",
    "manual_verification_coverage_watch",
    "lineage_score_watch",
    "lineage_score_block",
    PASS_REASON_CODE,
)

PUBLIC_CONFIG_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "max_fresh_age_seconds",
    "min_source_authority_score",
    "min_freshness_score",
    "min_corroboration_hops",
    "full_corroboration_hops",
    "watch_contradiction_severity",
    "block_contradiction_severity",
    "min_extraction_confidence",
    "min_manual_verification_coverage",
    "min_lineage_score",
    "block_lineage_score",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_CONFIG_PAYLOAD_FIELDS = (
    *PUBLIC_CONFIG_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "lineage_key",
    "claim_key",
    "source_count",
    "average_source_authority_score",
    "freshness_score",
    "max_corroboration_hops",
    "corroboration_hop_score",
    "max_contradiction_severity",
    "average_extraction_confidence",
    "manual_verification_coverage",
    "lineage_score",
    "lineage_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_ROW_PAYLOAD_FIELDS = (
    *PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
PUBLIC_REASON_CODE_COUNT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "reason_code",
    "row_count",
    "row_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REASON_CODE_COUNT_PAYLOAD_FIELDS = (
    *PUBLIC_REASON_CODE_COUNT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "config",
    "generated_at",
    "report_status",
    "claim_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_lineage_score",
    "max_contradiction_severity",
    "min_manual_verification_coverage",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_PAYLOAD_FIELDS = (
    *PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)


@dataclass(frozen=True)
class ResearchSourceFactClaimLineageConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_FACT_CLAIM_LINEAGE_CONFIG_VERSION
    max_fresh_age_seconds: Decimal = _SECONDS_PER_DAY
    min_source_authority_score: Decimal = Decimal("0.600000")
    min_freshness_score: Decimal = Decimal("0.500000")
    min_corroboration_hops: Decimal = Decimal("1.000000")
    full_corroboration_hops: Decimal = Decimal("2.000000")
    watch_contradiction_severity: Decimal = Decimal("0.400000")
    block_contradiction_severity: Decimal = Decimal("0.750000")
    min_extraction_confidence: Decimal = Decimal("0.600000")
    min_manual_verification_coverage: Decimal = Decimal("0.500000")
    min_lineage_score: Decimal = Decimal("0.700000")
    block_lineage_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    derived_validation_digest: str = ""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceFactClaimLineageConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchSourceFactClaimLineageConfig)
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOURCE_FACT_CLAIM_LINEAGE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_fresh_age_seconds",
            _require_positive_decimal("max_fresh_age_seconds", self.max_fresh_age_seconds),
        )
        for field_name in (
            "min_source_authority_score",
            "min_freshness_score",
            "watch_contradiction_severity",
            "block_contradiction_severity",
            "min_extraction_confidence",
            "min_manual_verification_coverage",
            "min_lineage_score",
            "block_lineage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_corroboration_hops", "full_corroboration_hops"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.full_corroboration_hops <= _ZERO:
            raise ValueError("full_corroboration_hops must be positive")
        if self.full_corroboration_hops < self.min_corroboration_hops:
            raise ValueError(
                "full_corroboration_hops must be at least min_corroboration_hops",
            )
        if self.block_contradiction_severity < self.watch_contradiction_severity:
            raise ValueError(
                "block_contradiction_severity must be at least "
                "watch_contradiction_severity",
            )
        if self.min_lineage_score < self.block_lineage_score:
            raise ValueError("min_lineage_score must be at least block_lineage_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _config_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _require_sha256_digest(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_config_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        return _config_public_payload(self)


@dataclass(frozen=True)
class ResearchSourceFactClaimLineageEvidence:
    lineage_key: str
    claim_key: str
    observed_at: datetime
    source_authority_score: Decimal
    corroboration_hops: Decimal
    contradiction_severity: Decimal
    extraction_confidence: Decimal
    manual_verification_coverage: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceFactClaimLineageEvidence does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("evidence", self, ResearchSourceFactClaimLineageEvidence)
        for field_name in ("lineage_key", "claim_key"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_authority_score",
            "contradiction_severity",
            "extraction_confidence",
            "manual_verification_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_hops",
            _require_nonnegative_decimal("corroboration_hops", self.corroboration_hops),
        )
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", self)


@dataclass(frozen=True)
class ResearchSourceFactClaimLineageRow:
    lineage_key: str
    claim_key: str
    source_count: Decimal
    average_source_authority_score: Decimal
    freshness_score: Decimal
    max_corroboration_hops: Decimal
    corroboration_hop_score: Decimal
    max_contradiction_severity: Decimal
    average_extraction_confidence: Decimal
    manual_verification_coverage: Decimal
    lineage_score: Decimal
    lineage_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    derived_validation_digest: str = ""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceFactClaimLineageRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceFactClaimLineageRow)
        for field_name in ("lineage_key", "claim_key"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_count",
            _require_positive_whole_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "max_corroboration_hops",
            _require_nonnegative_decimal(
                "max_corroboration_hops",
                self.max_corroboration_hops,
            ),
        )
        for field_name in (
            "average_source_authority_score",
            "freshness_score",
            "corroboration_hop_score",
            "max_contradiction_severity",
            "average_extraction_confidence",
            "manual_verification_coverage",
            "lineage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("lineage_status", self.lineage_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _require_sha256_digest(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_row_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        return _row_public_payload(self)


@dataclass(frozen=True)
class ResearchSourceFactClaimLineageReasonCodeCount:
    reason_code: str
    row_count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    derived_validation_digest: str = ""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceFactClaimLineageReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchSourceFactClaimLineageReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "row_count",
            _require_nonnegative_whole_decimal("row_count", self.row_count),
        )
        object.__setattr__(self, "row_ratio", _require_ratio_decimal("row_ratio", self.row_ratio))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _reason_code_count_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _require_sha256_digest(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_reason_code_count_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        return _reason_code_count_public_payload(self)


@dataclass(frozen=True)
class ResearchSourceFactClaimLineageReport:
    config_version: str
    config: ResearchSourceFactClaimLineageConfig
    generated_at: datetime
    report_status: str
    claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_lineage_score: Decimal
    max_contradiction_severity: Decimal
    min_manual_verification_coverage: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceFactClaimLineageReasonCodeCount, ...]
    rows: tuple[ResearchSourceFactClaimLineageRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    derived_validation_digest: str = ""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceFactClaimLineageReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourceFactClaimLineageReport)
        object.__setattr__(self, "config", _normalize_config(self.config))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_status("report_status", self.report_status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        for field_name in ("claim_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_lineage_score",
            "max_contradiction_severity",
            "min_manual_verification_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _require_sha256_digest(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        return research_source_fact_claim_lineage_report_payload(self)


def build_research_source_fact_claim_lineage_report(
    evidence: Sequence[ResearchSourceFactClaimLineageEvidence],
    *,
    generated_at: datetime,
    config: ResearchSourceFactClaimLineageConfig | None = None,
) -> ResearchSourceFactClaimLineageReport:
    """Build a local, read-only fact-claim lineage report."""

    if config is None:
        config = ResearchSourceFactClaimLineageConfig()
    _require_exact_type("config", config, ResearchSourceFactClaimLineageConfig)
    _require_hard_flags("config", config)
    _validate_config_derived_validation_digest(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_evidence = _normalize_evidence(evidence)
    for item in normalized_evidence:
        if item.observed_at > generated_at:
            raise ValueError("evidence observed_at must not be after generated_at")
    rows = _build_rows(normalized_evidence, config, generated_at)
    reason_codes = _report_reason_codes(rows)
    return ResearchSourceFactClaimLineageReport(
        config_version=config.config_version,
        config=config,
        generated_at=generated_at,
        report_status=_report_status(rows),
        claim_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_lineage_score=_average(tuple(row.lineage_score for row in rows)),
        max_contradiction_severity=_max_decimal(
            tuple(row.max_contradiction_severity for row in rows),
        ),
        min_manual_verification_coverage=_min_decimal(
            tuple(row.manual_verification_coverage for row in rows),
        ),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        rows=rows,
    )


def research_source_fact_claim_lineage_report_payload(
    report: ResearchSourceFactClaimLineageReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchSourceFactClaimLineageReport:
        _validate_report_current(report)
        payload = _report_public_payload_without_digest(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload(
            "ResearchSourceFactClaimLineageReport.payload",
            report,
            allow_json_containers=True,
        )
        _validate_public_report_payload(report)
        return dict(report)
    raise ValueError("report must be a ResearchSourceFactClaimLineageReport")


def research_source_fact_claim_lineage_report_digest(
    report: ResearchSourceFactClaimLineageReport,
) -> str:
    _validate_report_current(report)
    return report.derived_validation_digest


def validate_research_source_fact_claim_lineage_public_payload(payload: object) -> bool:
    try:
        if type(payload) is not dict:
            return False
        _reject_unsafe_public_payload(
            "ResearchSourceFactClaimLineageReport.payload",
            payload,
            allow_json_containers=True,
        )
        _validate_public_report_payload(payload)
        return True
    except (TypeError, ValueError):
        return False


def _build_rows(
    evidence: tuple[ResearchSourceFactClaimLineageEvidence, ...],
    config: ResearchSourceFactClaimLineageConfig,
    generated_at: datetime,
) -> tuple[ResearchSourceFactClaimLineageRow, ...]:
    grouped: dict[tuple[str, str], list[ResearchSourceFactClaimLineageEvidence]] = {}
    for item in evidence:
        grouped.setdefault((item.lineage_key, item.claim_key), []).append(item)
    return tuple(
        _row_for_group(lineage_key, claim_key, tuple(items), config, generated_at)
        for (lineage_key, claim_key), items in sorted(grouped.items())
    )


def _row_for_group(
    lineage_key: str,
    claim_key: str,
    evidence: tuple[ResearchSourceFactClaimLineageEvidence, ...],
    config: ResearchSourceFactClaimLineageConfig,
    generated_at: datetime,
) -> ResearchSourceFactClaimLineageRow:
    average_authority = _average(tuple(item.source_authority_score for item in evidence))
    freshness_score = _average(
        tuple(_freshness_score(item, generated_at, config) for item in evidence),
    )
    max_hops = _max_decimal(tuple(item.corroboration_hops for item in evidence))
    hop_score = _clamp_ratio(_ratio_raw(max_hops, config.full_corroboration_hops))
    max_contradiction = _max_decimal(
        tuple(item.contradiction_severity for item in evidence),
    )
    average_extraction = _average(tuple(item.extraction_confidence for item in evidence))
    manual_coverage = _average(
        tuple(item.manual_verification_coverage for item in evidence),
    )
    lineage_score = _lineage_score(
        average_authority=average_authority,
        freshness_score=freshness_score,
        hop_score=hop_score,
        max_contradiction=max_contradiction,
        average_extraction=average_extraction,
        manual_coverage=manual_coverage,
    )
    status = _row_status(
        average_authority=average_authority,
        freshness_score=freshness_score,
        max_hops=max_hops,
        max_contradiction=max_contradiction,
        average_extraction=average_extraction,
        manual_coverage=manual_coverage,
        lineage_score=lineage_score,
        config=config,
    )
    return ResearchSourceFactClaimLineageRow(
        lineage_key=lineage_key,
        claim_key=claim_key,
        source_count=_decimal_count(len(evidence)),
        average_source_authority_score=average_authority,
        freshness_score=freshness_score,
        max_corroboration_hops=max_hops,
        corroboration_hop_score=hop_score,
        max_contradiction_severity=max_contradiction,
        average_extraction_confidence=average_extraction,
        manual_verification_coverage=manual_coverage,
        lineage_score=lineage_score,
        lineage_status=status,
        reason_codes=_row_reason_codes(
            average_authority=average_authority,
            freshness_score=freshness_score,
            max_hops=max_hops,
            max_contradiction=max_contradiction,
            average_extraction=average_extraction,
            manual_coverage=manual_coverage,
            lineage_score=lineage_score,
            status=status,
            config=config,
        ),
    )


def _freshness_score(
    item: ResearchSourceFactClaimLineageEvidence,
    generated_at: datetime,
    config: ResearchSourceFactClaimLineageConfig,
) -> Decimal:
    age_seconds = _seconds_between(generated_at, item.observed_at)
    with localcontext() as context:
        context.prec = _DECIMAL_CONTEXT_PRECISION
        return _clamp_ratio(_ONE - (age_seconds / config.max_fresh_age_seconds))


def _lineage_score(
    *,
    average_authority: Decimal,
    freshness_score: Decimal,
    hop_score: Decimal,
    max_contradiction: Decimal,
    average_extraction: Decimal,
    manual_coverage: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = _DECIMAL_CONTEXT_PRECISION
        return _clamp_ratio(
            (
                average_authority
                + freshness_score
                + hop_score
                + (_ONE - max_contradiction)
                + average_extraction
                + manual_coverage
            )
            / Decimal("6.000000"),
        )


def _row_status(
    *,
    average_authority: Decimal,
    freshness_score: Decimal,
    max_hops: Decimal,
    max_contradiction: Decimal,
    average_extraction: Decimal,
    manual_coverage: Decimal,
    lineage_score: Decimal,
    config: ResearchSourceFactClaimLineageConfig,
) -> str:
    if (
        max_contradiction >= config.block_contradiction_severity
        or lineage_score < config.block_lineage_score
    ):
        return "block"
    if (
        average_authority >= config.min_source_authority_score
        and freshness_score >= config.min_freshness_score
        and max_hops >= config.min_corroboration_hops
        and max_contradiction < config.watch_contradiction_severity
        and average_extraction >= config.min_extraction_confidence
        and manual_coverage >= config.min_manual_verification_coverage
        and lineage_score >= config.min_lineage_score
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    average_authority: Decimal,
    freshness_score: Decimal,
    max_hops: Decimal,
    max_contradiction: Decimal,
    average_extraction: Decimal,
    manual_coverage: Decimal,
    lineage_score: Decimal,
    status: str,
    config: ResearchSourceFactClaimLineageConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if average_authority < config.min_source_authority_score:
        reason_codes.append("source_authority_watch")
    if freshness_score < config.min_freshness_score:
        reason_codes.append("freshness_watch")
    if max_hops < config.min_corroboration_hops:
        reason_codes.append("corroboration_hops_watch")
    if max_contradiction >= config.block_contradiction_severity:
        reason_codes.append("contradiction_severity_block")
    elif max_contradiction >= config.watch_contradiction_severity:
        reason_codes.append("contradiction_severity_watch")
    if average_extraction < config.min_extraction_confidence:
        reason_codes.append("extraction_confidence_watch")
    if manual_coverage < config.min_manual_verification_coverage:
        reason_codes.append("manual_verification_coverage_watch")
    if lineage_score < config.block_lineage_score:
        reason_codes.append("lineage_score_block")
    elif status == "watch" and lineage_score < config.min_lineage_score:
        reason_codes.append("lineage_score_watch")
    if status == "pass":
        reason_codes.append(PASS_REASON_CODE)
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchSourceFactClaimLineageRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.lineage_status == "block" for row in rows):
        return "block"
    if any(row.lineage_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceFactClaimLineageRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_evidence",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchSourceFactClaimLineageRow, ...],
) -> tuple[ResearchSourceFactClaimLineageReasonCodeCount, ...]:
    if reason_codes == ("empty_evidence",):
        return (
            ResearchSourceFactClaimLineageReasonCodeCount(
                reason_code="empty_evidence",
                row_count=_ONE,
                row_ratio=_ZERO,
            ),
        )
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchSourceFactClaimLineageReasonCodeCount(
            reason_code=reason_code,
            row_count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[ResearchSourceFactClaimLineageRow, ...],
) -> Decimal:
    _require_reason_code("reason_code", reason_code)
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_count(
    rows: tuple[ResearchSourceFactClaimLineageRow, ...],
    status: str,
) -> int:
    _require_status("status", status)
    return sum(1 for row in rows if row.lineage_status == status)


def _validate_row_consistency(row: ResearchSourceFactClaimLineageRow) -> None:
    if row.source_count <= _ZERO:
        raise ValueError("source_count must be positive")
    if row.lineage_score != _lineage_score(
        average_authority=row.average_source_authority_score,
        freshness_score=row.freshness_score,
        hop_score=row.corroboration_hop_score,
        max_contradiction=row.max_contradiction_severity,
        average_extraction=row.average_extraction_confidence,
        manual_coverage=row.manual_verification_coverage,
    ):
        raise ValueError("lineage_score must match row dimensions")
    if row.lineage_status == "pass" and row.reason_codes != (PASS_REASON_CODE,):
        raise ValueError("pass rows must only include fact_claim_lineage_pass")
    if row.lineage_status != "pass" and PASS_REASON_CODE in row.reason_codes:
        raise ValueError("non-pass rows must not include fact_claim_lineage_pass")
    has_block_reason = (
        "contradiction_severity_block" in row.reason_codes
        or "lineage_score_block" in row.reason_codes
    )
    if row.lineage_status == "block" and not has_block_reason:
        raise ValueError("block rows must include a block reason")
    if row.lineage_status != "block" and has_block_reason:
        raise ValueError("non-block rows must not include block reasons")


def _validate_row_with_config(
    row: ResearchSourceFactClaimLineageRow,
    config: ResearchSourceFactClaimLineageConfig,
) -> None:
    expected_hop_score = _clamp_ratio(
        _ratio_raw(row.max_corroboration_hops, config.full_corroboration_hops),
    )
    if row.corroboration_hop_score != expected_hop_score:
        raise ValueError("corroboration_hop_score must match config")
    expected_score = _lineage_score(
        average_authority=row.average_source_authority_score,
        freshness_score=row.freshness_score,
        hop_score=row.corroboration_hop_score,
        max_contradiction=row.max_contradiction_severity,
        average_extraction=row.average_extraction_confidence,
        manual_coverage=row.manual_verification_coverage,
    )
    if row.lineage_score != expected_score:
        raise ValueError("lineage_score must match row dimensions")
    expected_status = _row_status(
        average_authority=row.average_source_authority_score,
        freshness_score=row.freshness_score,
        max_hops=row.max_corroboration_hops,
        max_contradiction=row.max_contradiction_severity,
        average_extraction=row.average_extraction_confidence,
        manual_coverage=row.manual_verification_coverage,
        lineage_score=row.lineage_score,
        config=config,
    )
    if row.lineage_status != expected_status:
        raise ValueError("lineage_status must match row dimensions and config")
    expected_reasons = _row_reason_codes(
        average_authority=row.average_source_authority_score,
        freshness_score=row.freshness_score,
        max_hops=row.max_corroboration_hops,
        max_contradiction=row.max_contradiction_severity,
        average_extraction=row.average_extraction_confidence,
        manual_coverage=row.manual_verification_coverage,
        lineage_score=row.lineage_score,
        status=row.lineage_status,
        config=config,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row dimensions and config")


def _validate_report_current(report: ResearchSourceFactClaimLineageReport) -> None:
    _require_exact_type("report", report, ResearchSourceFactClaimLineageReport)
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    _validate_report_consistency(report)
    _validate_report_derived_validation_digest(report)


def _validate_report_consistency(report: ResearchSourceFactClaimLineageReport) -> None:
    _require_exact_type("config", report.config, ResearchSourceFactClaimLineageConfig)
    _validate_config_derived_validation_digest(report.config)
    if report.config_version != report.config.config_version:
        raise ValueError("config_version must match config")
    _require_rows_tuple(report.rows)
    for row in report.rows:
        _validate_row_derived_validation_digest(row)
        _validate_row_with_config(row, report.config)
    _require_reason_code_counts_tuple(report.reason_code_counts)
    for reason_code_count in report.reason_code_counts:
        _validate_reason_code_count_derived_validation_digest(reason_code_count)
    if report.claim_count != _decimal_count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_lineage_score != _average(
        tuple(row.lineage_score for row in report.rows),
    ):
        raise ValueError("average_lineage_score must match rows")
    if report.max_contradiction_severity != _max_decimal(
        tuple(row.max_contradiction_severity for row in report.rows),
    ):
        raise ValueError("max_contradiction_severity must match rows")
    if report.min_manual_verification_coverage != _min_decimal(
        tuple(row.manual_verification_coverage for row in report.rows),
    ):
        raise ValueError("min_manual_verification_coverage must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes and rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")


def _normalize_evidence(
    evidence: Sequence[ResearchSourceFactClaimLineageEvidence],
) -> tuple[ResearchSourceFactClaimLineageEvidence, ...]:
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
        raise ValueError("evidence must be a sequence")
    normalized: list[ResearchSourceFactClaimLineageEvidence] = []
    for item in evidence:
        _require_exact_type("evidence", item, ResearchSourceFactClaimLineageEvidence)
        _require_hard_flags("evidence", item)
        _reject_unsafe_public_payload("evidence", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.lineage_key,
                item.claim_key,
                item.observed_at,
                item.source_authority_score,
                item.corroboration_hops,
                item.contradiction_severity,
                item.extraction_confidence,
                item.manual_verification_coverage,
            ),
        ),
    )


def _normalize_config(value: object) -> ResearchSourceFactClaimLineageConfig:
    _require_exact_type("config", value, ResearchSourceFactClaimLineageConfig)
    config = value
    _require_hard_flags("config", config)
    _validate_config_derived_validation_digest(config)
    return config


def _normalize_rows(value: object) -> tuple[ResearchSourceFactClaimLineageRow, ...]:
    rows = _require_rows_tuple(value)
    return tuple(sorted(rows, key=_row_sort_key))


def _require_rows_tuple(value: object) -> tuple[ResearchSourceFactClaimLineageRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows: list[ResearchSourceFactClaimLineageRow] = []
    for row in value:
        _require_exact_type("row", row, ResearchSourceFactClaimLineageRow)
        _require_hard_flags("row", row)
        _validate_row_derived_validation_digest(row)
        rows.append(row)
    return tuple(rows)


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourceFactClaimLineageReasonCodeCount, ...]:
    return _require_reason_code_counts_tuple(value)


def _require_reason_code_counts_tuple(
    value: object,
) -> tuple[ResearchSourceFactClaimLineageReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    counts: list[ResearchSourceFactClaimLineageReasonCodeCount] = []
    for reason_code_count in value:
        _require_exact_type(
            "reason_code_count",
            reason_code_count,
            ResearchSourceFactClaimLineageReasonCodeCount,
        )
        _require_hard_flags("reason_code_count", reason_code_count)
        _validate_reason_code_count_derived_validation_digest(reason_code_count)
        counts.append(reason_code_count)
    return tuple(counts)


def _row_sort_key(
    row: ResearchSourceFactClaimLineageRow,
) -> tuple[str, str]:
    return (row.lineage_key, row.claim_key)


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_flags(label: str, payload: Mapping[str, object]) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal_raw(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    return _quantize(_require_decimal_raw(field_name, value))


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal_raw(field_name, value)
    if raw < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal_raw(field_name, value)
    if raw <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(raw)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal_raw(field_name, value)
    if raw < _ZERO or raw > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(raw)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal_raw(field_name, value)
    if raw < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(raw)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal_raw(field_name, value)
    if raw <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(raw)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext() as context:
        context.prec = _DECIMAL_CONTEXT_PRECISION
        return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return max(values)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return min(values)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _clamp_ratio(_ratio_raw(numerator, denominator))


def _ratio_raw(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    with localcontext() as context:
        context.prec = _DECIMAL_CONTEXT_PRECISION
        return numerator / denominator


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = _DECIMAL_CONTEXT_PRECISION
        normalized = value.quantize(_QUANT, rounding=ROUND_HALF_UP)
    if normalized == _ZERO:
        return _ZERO
    return normalized


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("earlier datetime must not be after later datetime")
    with localcontext() as context:
        context.prec = _DECIMAL_CONTEXT_PRECISION
        whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
        microseconds = Decimal(delta.microseconds) / _MICROSECOND
        return _require_nonnegative_decimal("age_seconds", whole_seconds + microseconds)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _normalize_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    codes = tuple(value)
    normalized = _normalize_reason_codes(codes)
    if codes != normalized:
        raise ValueError(f"{field_name} must use canonical order")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _config_public_payload(
    config: ResearchSourceFactClaimLineageConfig,
) -> dict[str, object]:
    _validate_config_derived_validation_digest(config)
    payload = _config_public_payload_without_digest(config)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = config.derived_validation_digest
    return payload


def _config_public_payload_without_digest(
    config: ResearchSourceFactClaimLineageConfig,
) -> dict[str, object]:
    return {
        "config_version": config.config_version,
        "max_fresh_age_seconds": _decimal_payload(config.max_fresh_age_seconds),
        "min_source_authority_score": _decimal_payload(config.min_source_authority_score),
        "min_freshness_score": _decimal_payload(config.min_freshness_score),
        "min_corroboration_hops": _decimal_payload(config.min_corroboration_hops),
        "full_corroboration_hops": _decimal_payload(config.full_corroboration_hops),
        "watch_contradiction_severity": _decimal_payload(
            config.watch_contradiction_severity,
        ),
        "block_contradiction_severity": _decimal_payload(
            config.block_contradiction_severity,
        ),
        "min_extraction_confidence": _decimal_payload(config.min_extraction_confidence),
        "min_manual_verification_coverage": _decimal_payload(
            config.min_manual_verification_coverage,
        ),
        "min_lineage_score": _decimal_payload(config.min_lineage_score),
        "block_lineage_score": _decimal_payload(config.block_lineage_score),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(row: ResearchSourceFactClaimLineageRow) -> dict[str, object]:
    _validate_row_derived_validation_digest(row)
    payload = _row_public_payload_without_digest(row)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _row_public_payload_without_digest(
    row: ResearchSourceFactClaimLineageRow,
) -> dict[str, object]:
    return {
        "lineage_key": row.lineage_key,
        "claim_key": row.claim_key,
        "source_count": _decimal_payload(row.source_count),
        "average_source_authority_score": _decimal_payload(
            row.average_source_authority_score,
        ),
        "freshness_score": _decimal_payload(row.freshness_score),
        "max_corroboration_hops": _decimal_payload(row.max_corroboration_hops),
        "corroboration_hop_score": _decimal_payload(row.corroboration_hop_score),
        "max_contradiction_severity": _decimal_payload(row.max_contradiction_severity),
        "average_extraction_confidence": _decimal_payload(
            row.average_extraction_confidence,
        ),
        "manual_verification_coverage": _decimal_payload(row.manual_verification_coverage),
        "lineage_score": _decimal_payload(row.lineage_score),
        "lineage_status": row.lineage_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_public_payload(
    reason_code_count: ResearchSourceFactClaimLineageReasonCodeCount,
) -> dict[str, object]:
    _validate_reason_code_count_derived_validation_digest(reason_code_count)
    payload = _reason_code_count_public_payload_without_digest(reason_code_count)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = (
        reason_code_count.derived_validation_digest
    )
    return payload


def _reason_code_count_public_payload_without_digest(
    reason_code_count: ResearchSourceFactClaimLineageReasonCodeCount,
) -> dict[str, object]:
    return {
        "reason_code": reason_code_count.reason_code,
        "row_count": _decimal_payload(reason_code_count.row_count),
        "row_ratio": _decimal_payload(reason_code_count.row_ratio),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_public_payload_without_digest(
    report: ResearchSourceFactClaimLineageReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "config": _config_public_payload(report.config),
        "generated_at": _datetime_payload(report.generated_at),
        "report_status": report.report_status,
        "claim_count": _decimal_payload(report.claim_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "average_lineage_score": _decimal_payload(report.average_lineage_score),
        "max_contradiction_severity": _decimal_payload(
            report.max_contradiction_severity,
        ),
        "min_manual_verification_coverage": _decimal_payload(
            report.min_manual_verification_coverage,
        ),
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_public_payload(reason_code_count)
            for reason_code_count in report.reason_code_counts
        ],
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _config_derived_validation_digest(
    config: ResearchSourceFactClaimLineageConfig,
) -> str:
    return _derived_validation_digest(
        "research_source_fact_claim_lineage_config",
        _config_public_payload_without_digest(config),
        PUBLIC_CONFIG_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _row_derived_validation_digest(row: ResearchSourceFactClaimLineageRow) -> str:
    return _derived_validation_digest(
        "research_source_fact_claim_lineage_row",
        _row_public_payload_without_digest(row),
        PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _reason_code_count_derived_validation_digest(
    reason_code_count: ResearchSourceFactClaimLineageReasonCodeCount,
) -> str:
    return _derived_validation_digest(
        "research_source_fact_claim_lineage_reason_code_count",
        _reason_code_count_public_payload_without_digest(reason_code_count),
        PUBLIC_REASON_CODE_COUNT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _report_derived_validation_digest(
    report: ResearchSourceFactClaimLineageReport,
) -> str:
    return _derived_validation_digest(
        "research_source_fact_claim_lineage_report",
        _report_public_payload_without_digest(report),
        PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _derived_validation_digest(
    label: str,
    payload: dict[str, object],
    field_names: tuple[str, ...],
) -> str:
    canonical = json.dumps(
        {field_name: payload[field_name] for field_name in field_names},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(f"{label}|{canonical}".encode("utf-8")).hexdigest()


def _validate_config_derived_validation_digest(
    config: ResearchSourceFactClaimLineageConfig,
) -> None:
    if config.derived_validation_digest != _config_derived_validation_digest(config):
        raise ValueError("derived_validation_digest must match config fields")


def _validate_row_derived_validation_digest(
    row: ResearchSourceFactClaimLineageRow,
) -> None:
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_reason_code_count_derived_validation_digest(
    reason_code_count: ResearchSourceFactClaimLineageReasonCodeCount,
) -> None:
    if reason_code_count.derived_validation_digest != (
        _reason_code_count_derived_validation_digest(reason_code_count)
    ):
        raise ValueError("derived_validation_digest must match reason_code_count fields")


def _validate_report_derived_validation_digest(
    report: ResearchSourceFactClaimLineageReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_public_report_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_REPORT_PAYLOAD_FIELDS, "report")
    _require_public_identifier("config_version", payload["config_version"])
    if type(payload["config"]) is not dict:
        raise ValueError("config must be a config payload dictionary")
    config = _config_from_public_payload(payload["config"])
    generated_at = _require_datetime_payload_string("generated_at", payload["generated_at"])
    _require_status("report_status", payload["report_status"])
    claim_count = _require_decimal_payload_string("claim_count", payload["claim_count"], whole=True)
    pass_count = _require_decimal_payload_string("pass_count", payload["pass_count"], whole=True)
    watch_count = _require_decimal_payload_string("watch_count", payload["watch_count"], whole=True)
    block_count = _require_decimal_payload_string("block_count", payload["block_count"], whole=True)
    average_lineage_score = _require_decimal_payload_string(
        "average_lineage_score",
        payload["average_lineage_score"],
        probability=True,
    )
    max_contradiction_severity = _require_decimal_payload_string(
        "max_contradiction_severity",
        payload["max_contradiction_severity"],
        probability=True,
    )
    min_manual_verification_coverage = _require_decimal_payload_string(
        "min_manual_verification_coverage",
        payload["min_manual_verification_coverage"],
        probability=True,
    )
    reason_codes = _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    reason_code_counts_payload = payload["reason_code_counts"]
    if type(reason_code_counts_payload) is not list:
        raise ValueError("reason_code_counts must be a list")
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(reason_code_count_payload)
        for reason_code_count_payload in reason_code_counts_payload
    )
    rows_payload = payload["rows"]
    if type(rows_payload) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(_row_from_public_payload(row_payload) for row_payload in rows_payload)
    _require_payload_flags("payload", payload)
    _require_sha256_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != _derived_validation_digest(
        "research_source_fact_claim_lineage_report",
        payload,
        PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    ):
        raise ValueError("derived_validation_digest must match report payload")
    ResearchSourceFactClaimLineageReport(
        config_version=payload["config_version"],
        config=config,
        generated_at=generated_at,
        report_status=payload["report_status"],
        claim_count=claim_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_lineage_score=average_lineage_score,
        max_contradiction_severity=max_contradiction_severity,
        min_manual_verification_coverage=min_manual_verification_coverage,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        rows=rows,
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
        derived_validation_digest=payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )


def _config_from_public_payload(
    payload: dict[str, object],
) -> ResearchSourceFactClaimLineageConfig:
    _require_exact_payload_fields(payload, PUBLIC_CONFIG_PAYLOAD_FIELDS, "config")
    _require_public_identifier("config_version", payload["config_version"])
    _require_payload_flags("config payload", payload)
    _require_sha256_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    return ResearchSourceFactClaimLineageConfig(
        config_version=payload["config_version"],
        max_fresh_age_seconds=_require_decimal_payload_string(
            "max_fresh_age_seconds",
            payload["max_fresh_age_seconds"],
            positive=True,
        ),
        min_source_authority_score=_require_decimal_payload_string(
            "min_source_authority_score",
            payload["min_source_authority_score"],
            probability=True,
        ),
        min_freshness_score=_require_decimal_payload_string(
            "min_freshness_score",
            payload["min_freshness_score"],
            probability=True,
        ),
        min_corroboration_hops=_require_decimal_payload_string(
            "min_corroboration_hops",
            payload["min_corroboration_hops"],
        ),
        full_corroboration_hops=_require_decimal_payload_string(
            "full_corroboration_hops",
            payload["full_corroboration_hops"],
            positive=True,
        ),
        watch_contradiction_severity=_require_decimal_payload_string(
            "watch_contradiction_severity",
            payload["watch_contradiction_severity"],
            probability=True,
        ),
        block_contradiction_severity=_require_decimal_payload_string(
            "block_contradiction_severity",
            payload["block_contradiction_severity"],
            probability=True,
        ),
        min_extraction_confidence=_require_decimal_payload_string(
            "min_extraction_confidence",
            payload["min_extraction_confidence"],
            probability=True,
        ),
        min_manual_verification_coverage=_require_decimal_payload_string(
            "min_manual_verification_coverage",
            payload["min_manual_verification_coverage"],
            probability=True,
        ),
        min_lineage_score=_require_decimal_payload_string(
            "min_lineage_score",
            payload["min_lineage_score"],
            probability=True,
        ),
        block_lineage_score=_require_decimal_payload_string(
            "block_lineage_score",
            payload["block_lineage_score"],
            probability=True,
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
        derived_validation_digest=payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )


def _row_from_public_payload(payload: object) -> ResearchSourceFactClaimLineageRow:
    if type(payload) is not dict:
        raise ValueError("rows must contain row payload dictionaries")
    _require_exact_payload_fields(payload, PUBLIC_ROW_PAYLOAD_FIELDS, "row")
    for field_name in ("lineage_key", "claim_key"):
        _require_public_identifier(field_name, payload[field_name])
    reason_codes = _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    _require_payload_flags("row payload", payload)
    _require_sha256_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    return ResearchSourceFactClaimLineageRow(
        lineage_key=payload["lineage_key"],
        claim_key=payload["claim_key"],
        source_count=_require_decimal_payload_string(
            "source_count",
            payload["source_count"],
            whole=True,
            positive=True,
        ),
        average_source_authority_score=_require_decimal_payload_string(
            "average_source_authority_score",
            payload["average_source_authority_score"],
            probability=True,
        ),
        freshness_score=_require_decimal_payload_string(
            "freshness_score",
            payload["freshness_score"],
            probability=True,
        ),
        max_corroboration_hops=_require_decimal_payload_string(
            "max_corroboration_hops",
            payload["max_corroboration_hops"],
        ),
        corroboration_hop_score=_require_decimal_payload_string(
            "corroboration_hop_score",
            payload["corroboration_hop_score"],
            probability=True,
        ),
        max_contradiction_severity=_require_decimal_payload_string(
            "max_contradiction_severity",
            payload["max_contradiction_severity"],
            probability=True,
        ),
        average_extraction_confidence=_require_decimal_payload_string(
            "average_extraction_confidence",
            payload["average_extraction_confidence"],
            probability=True,
        ),
        manual_verification_coverage=_require_decimal_payload_string(
            "manual_verification_coverage",
            payload["manual_verification_coverage"],
            probability=True,
        ),
        lineage_score=_require_decimal_payload_string(
            "lineage_score",
            payload["lineage_score"],
            probability=True,
        ),
        lineage_status=_require_status("lineage_status", payload["lineage_status"]),
        reason_codes=reason_codes,
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
        derived_validation_digest=payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )


def _reason_code_count_from_public_payload(
    payload: object,
) -> ResearchSourceFactClaimLineageReasonCodeCount:
    if type(payload) is not dict:
        raise ValueError("reason_code_counts must contain payload dictionaries")
    _require_exact_payload_fields(
        payload,
        PUBLIC_REASON_CODE_COUNT_PAYLOAD_FIELDS,
        "reason_code_count",
    )
    _require_reason_code("reason_code", payload["reason_code"])
    _require_payload_flags("reason_code_count payload", payload)
    _require_sha256_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    return ResearchSourceFactClaimLineageReasonCodeCount(
        reason_code=payload["reason_code"],
        row_count=_require_decimal_payload_string(
            "row_count",
            payload["row_count"],
            whole=True,
        ),
        row_ratio=_require_decimal_payload_string(
            "row_ratio",
            payload["row_ratio"],
            probability=True,
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
        derived_validation_digest=payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )


def _require_exact_payload_fields(
    payload: Mapping[str, object],
    field_names: tuple[str, ...],
    label: str,
) -> None:
    if tuple(payload) != field_names:
        missing = [field_name for field_name in field_names if field_name not in payload]
        if missing:
            raise ValueError(f"{missing[0]} is required")
        extra = sorted(set(payload) - set(field_names))
        if extra:
            raise ValueError(f"unexpected {label} payload field: {extra[0]}")
        raise ValueError(f"{label} payload field order must be canonical")


def _decimal_payload(value: Decimal) -> str:
    return str(_require_decimal("payload numeric", value))


def _datetime_payload(value: datetime) -> str:
    return _as_utc("payload datetime", value).isoformat()


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    whole: bool = False,
    positive: bool = False,
    probability: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal payload string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal payload string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if positive and decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    if probability and decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    if whole and decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    normalized = _quantize(decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must use six decimal places")
    return normalized


def _require_datetime_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime payload string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime payload string") from exc
    return _as_utc(field_name, parsed)


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
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if _DOMAIN_LIKE_RE.search(value):
        raise ValueError(f"{field_name} has unsafe public value")
    if (
        _UUID_LIKE_RE.fullmatch(value)
        or _HEX_ID_LIKE_RE.fullmatch(value)
        or _JWT_LIKE_RE.fullmatch(value)
    ):
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_FACT_CLAIM_LINEAGE_CONFIG_VERSION",
    "DERIVED_VALIDATION_DIGEST_FIELD",
    "LINEAGE_STATUSES",
    "PASS_REASON_CODE",
    "PUBLIC_CONFIG_PAYLOAD_FIELDS",
    "PUBLIC_CONFIG_PAYLOAD_FIELDS_WITHOUT_DIGEST",
    "PUBLIC_REASON_CODE_COUNT_PAYLOAD_FIELDS",
    "PUBLIC_REASON_CODE_COUNT_PAYLOAD_FIELDS_WITHOUT_DIGEST",
    "PUBLIC_REPORT_PAYLOAD_FIELDS",
    "PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST",
    "PUBLIC_ROW_PAYLOAD_FIELDS",
    "PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST",
    "ResearchSourceFactClaimLineageConfig",
    "ResearchSourceFactClaimLineageEvidence",
    "ResearchSourceFactClaimLineageReasonCodeCount",
    "ResearchSourceFactClaimLineageReport",
    "ResearchSourceFactClaimLineageRow",
    "build_research_source_fact_claim_lineage_report",
    "research_source_fact_claim_lineage_report_digest",
    "research_source_fact_claim_lineage_report_payload",
    "validate_research_source_fact_claim_lineage_public_payload",
)
