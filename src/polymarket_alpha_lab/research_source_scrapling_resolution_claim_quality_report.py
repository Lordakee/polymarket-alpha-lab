"""Pure report-only Scrapling resolution claim quality aggregation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
from typing import Any


CONFIG_VERSION = "scrapling-resolution-claim-quality-report-v1"
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
RESEARCH_SOURCE_SCRAPLING_RESOLUTION_CLAIM_QUALITY_STATUSES = (
    PASS_STATUS,
    WATCH_STATUS,
    BLOCK_STATUS,
)

DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "text",
    "url",
    "http",
    "api_key",
    "private_key",
    "credential",
    "secret",
    "auth_",
    "auth-",
    "authorization",
    "dsn",
    "table",
    "token",
    "database",
    "network",
    "persist",
    "persistence",
    "file",
    "wallet",
    "order",
    "trade",
    "live",
    "execute",
    "execution",
    "recommend",
    "recommendation",
    "position",
    "sizing",
)

__all__ = (
    "RESEARCH_SOURCE_SCRAPLING_RESOLUTION_CLAIM_QUALITY_STATUSES",
    "ResearchSourceScraplingResolutionClaimQualityConfig",
    "ResearchSourceScraplingResolutionClaimQualityInput",
    "ResearchSourceScraplingResolutionClaimQualityReport",
    "ResearchSourceScraplingResolutionClaimQualityRow",
    "build_research_source_scrapling_resolution_claim_quality_report",
    "research_source_scrapling_resolution_claim_quality_report_digest",
    "research_source_scrapling_resolution_claim_quality_report_payload",
    "validate_research_source_scrapling_resolution_claim_quality_public_payload",
)


@dataclass(frozen=True)
class ResearchSourceScraplingResolutionClaimQualityConfig:
    config_version: str = CONFIG_VERSION
    evidence_quality_weight: Decimal = Decimal("0.350000")
    resolution_alignment_weight: Decimal = Decimal("0.300000")
    authority_coverage_weight: Decimal = Decimal("0.200000")
    contradiction_pressure_weight: Decimal = Decimal("0.150000")
    watch_quality_score: Decimal = Decimal("0.700000")
    block_quality_score: Decimal = Decimal("0.400000")
    watch_staleness_hours: Decimal = Decimal("24.000000")
    block_staleness_hours: Decimal = Decimal("72.000000")
    watch_extraction_error_count: Decimal = Decimal("1")
    block_extraction_error_count: Decimal = Decimal("3")
    watch_missing_resolution_terms_count: Decimal = Decimal("1")
    block_missing_resolution_terms_count: Decimal = Decimal("2")
    watch_contradiction_pressure_score: Decimal = Decimal("0.350000")
    block_contradiction_pressure_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingResolutionClaimQualityConfig:
            raise TypeError(
                "ResearchSourceScraplingResolutionClaimQualityConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchSourceScraplingResolutionClaimQualityConfig,
        )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "evidence_quality_weight",
            "resolution_alignment_weight",
            "authority_coverage_weight",
            "contradiction_pressure_weight",
            "watch_quality_score",
            "block_quality_score",
            "watch_contradiction_pressure_score",
            "block_contradiction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_staleness_hours", "block_staleness_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_extraction_error_count",
            "block_extraction_error_count",
            "watch_missing_resolution_terms_count",
            "block_missing_resolution_terms_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingResolutionClaimQualityInput:
    case_reference: str
    capture_reference: str
    observed_at: datetime
    evidence_quality_score: Decimal
    resolution_alignment_score: Decimal
    authority_coverage_score: Decimal
    contradiction_pressure_score: Decimal
    staleness_hours: Decimal
    extraction_error_count: Decimal
    missing_resolution_terms_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingResolutionClaimQualityInput:
            raise TypeError(
                "ResearchSourceScraplingResolutionClaimQualityInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchSourceScraplingResolutionClaimQualityInput,
        )
        _require_private_reference("case_reference", self.case_reference)
        _require_private_reference("capture_reference", self.capture_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "evidence_quality_score",
            "resolution_alignment_score",
            "authority_coverage_score",
            "contradiction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "staleness_hours",
            _require_nonnegative_decimal("staleness_hours", self.staleness_hours),
        )
        for field_name in ("extraction_error_count", "missing_resolution_terms_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceScraplingResolutionClaimQualityRow:
    case_digest: str
    capture_digest: str
    observed_at: datetime
    evidence_quality_score: Decimal
    resolution_alignment_score: Decimal
    authority_coverage_score: Decimal
    contradiction_pressure_score: Decimal
    staleness_hours: Decimal
    extraction_error_count: Decimal
    missing_resolution_terms_count: Decimal
    quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingResolutionClaimQualityRow:
            raise TypeError(
                "ResearchSourceScraplingResolutionClaimQualityRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceScraplingResolutionClaimQualityRow)
        _require_sha256_digest("case_digest", self.case_digest)
        _require_sha256_digest("capture_digest", self.capture_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "evidence_quality_score",
            "resolution_alignment_score",
            "authority_coverage_score",
            "contradiction_pressure_score",
            "quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "staleness_hours",
            _require_nonnegative_decimal("staleness_hours", self.staleness_hours),
        )
        for field_name in ("extraction_error_count", "missing_resolution_terms_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScraplingResolutionClaimQualityReport:
    generated_at: datetime
    config_version: str
    status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_quality_score: Decimal
    lowest_quality_score: Decimal
    highest_contradiction_pressure_score: Decimal
    rows: tuple[ResearchSourceScraplingResolutionClaimQualityRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingResolutionClaimQualityReport:
            raise TypeError(
                "ResearchSourceScraplingResolutionClaimQualityReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchSourceScraplingResolutionClaimQualityReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_quality_score",
            "lowest_quality_score",
            "highest_contradiction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest_from_values(_report_values_without_digest(self)),
            )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        return research_source_scrapling_resolution_claim_quality_report_payload(self)


def build_research_source_scrapling_resolution_claim_quality_report(
    items: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchSourceScraplingResolutionClaimQualityConfig | None = None,
) -> ResearchSourceScraplingResolutionClaimQualityReport:
    if config is None:
        config = ResearchSourceScraplingResolutionClaimQualityConfig()
    if type(config) is not ResearchSourceScraplingResolutionClaimQualityConfig:
        raise ValueError(
            "config must be a ResearchSourceScraplingResolutionClaimQualityConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_inputs(items)
    for item in normalized_items:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_from_item(item, config) for item in normalized_items),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "item_count": _count_decimal(len(rows)),
        "pass_count": _count_decimal(_status_count(rows, PASS_STATUS)),
        "watch_count": _count_decimal(_status_count(rows, WATCH_STATUS)),
        "block_count": _count_decimal(_status_count(rows, BLOCK_STATUS)),
        "average_quality_score": _average_or_zero(row.quality_score for row in rows),
        "lowest_quality_score": _minimum_or_zero(row.quality_score for row in rows),
        "highest_contradiction_pressure_score": _maximum_or_zero(
            row.contradiction_pressure_score for row in rows
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceScraplingResolutionClaimQualityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_scrapling_resolution_claim_quality_report_payload(
    report: ResearchSourceScraplingResolutionClaimQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceScraplingResolutionClaimQualityReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a "
            "ResearchSourceScraplingResolutionClaimQualityReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_source_scrapling_resolution_claim_quality_public_payload(payload)
    return payload


def validate_research_source_scrapling_resolution_claim_quality_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_numerics(payload)
    _reject_unsafe_public_payload("public payload", payload, allow_json_containers=True)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _report_digest_from_values(unsigned_payload):
        raise ValueError("derived_validation_digest does not match public payload")
    try:
        canonical_report = _report_from_public_payload(payload)
    except ValueError as exc:
        raise ValueError("public payload does not match exact canonical schema") from exc
    if _json_ready(asdict(canonical_report)) != payload:
        raise ValueError("public payload does not match exact canonical schema")


def research_source_scrapling_resolution_claim_quality_report_digest(
    report: ResearchSourceScraplingResolutionClaimQualityReport,
) -> str:
    if type(report) is not ResearchSourceScraplingResolutionClaimQualityReport:
        raise ValueError(
            "report must be a ResearchSourceScraplingResolutionClaimQualityReport",
        )
    _require_hard_flags("report", report)
    digest = _report_digest_from_values(_report_values_without_digest(report))
    if digest != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return digest


def _row_from_item(
    item: ResearchSourceScraplingResolutionClaimQualityInput,
    config: ResearchSourceScraplingResolutionClaimQualityConfig,
) -> ResearchSourceScraplingResolutionClaimQualityRow:
    quality_score = _quality_score(item, config)
    status = _row_status(item, quality_score, config)
    return ResearchSourceScraplingResolutionClaimQualityRow(
        case_digest=_reference_digest(item.case_reference),
        capture_digest=_reference_digest(item.capture_reference),
        observed_at=item.observed_at,
        evidence_quality_score=item.evidence_quality_score,
        resolution_alignment_score=item.resolution_alignment_score,
        authority_coverage_score=item.authority_coverage_score,
        contradiction_pressure_score=item.contradiction_pressure_score,
        staleness_hours=item.staleness_hours,
        extraction_error_count=item.extraction_error_count,
        missing_resolution_terms_count=item.missing_resolution_terms_count,
        quality_score=quality_score,
        status=status,
        reason_codes=_row_reason_codes(item, quality_score, status, config),
    )


def _quality_score(
    item: ResearchSourceScraplingResolutionClaimQualityInput,
    config: ResearchSourceScraplingResolutionClaimQualityConfig,
) -> Decimal:
    return _quantize(
        item.evidence_quality_score * config.evidence_quality_weight
        + item.resolution_alignment_score * config.resolution_alignment_weight
        + item.authority_coverage_score * config.authority_coverage_weight
        + (ONE - item.contradiction_pressure_score)
        * config.contradiction_pressure_weight,
    )


def _row_status(
    item: ResearchSourceScraplingResolutionClaimQualityInput,
    quality_score: Decimal,
    config: ResearchSourceScraplingResolutionClaimQualityConfig,
) -> str:
    if (
        quality_score < config.block_quality_score
        or item.staleness_hours >= config.block_staleness_hours
        or item.extraction_error_count >= config.block_extraction_error_count
        or item.missing_resolution_terms_count
        >= config.block_missing_resolution_terms_count
        or item.contradiction_pressure_score >= config.block_contradiction_pressure_score
    ):
        return BLOCK_STATUS
    if (
        quality_score < config.watch_quality_score
        or item.staleness_hours >= config.watch_staleness_hours
        or item.extraction_error_count >= config.watch_extraction_error_count
        or item.missing_resolution_terms_count
        >= config.watch_missing_resolution_terms_count
        or item.contradiction_pressure_score >= config.watch_contradiction_pressure_score
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    item: ResearchSourceScraplingResolutionClaimQualityInput,
    quality_score: Decimal,
    status: str,
    config: ResearchSourceScraplingResolutionClaimQualityConfig,
) -> tuple[str, ...]:
    reason_codes = set(item.reason_codes)
    reason_codes.add(f"resolution_claim_quality_{status}")
    if quality_score < config.block_quality_score:
        reason_codes.add("quality_score_block")
    elif quality_score < config.watch_quality_score:
        reason_codes.add("quality_score_watch")
    if item.staleness_hours >= config.block_staleness_hours:
        reason_codes.add("stale_capture_block")
    elif item.staleness_hours >= config.watch_staleness_hours:
        reason_codes.add("stale_capture_watch")
    if item.extraction_error_count >= config.block_extraction_error_count:
        reason_codes.add("extraction_errors_block")
    elif item.extraction_error_count >= config.watch_extraction_error_count:
        reason_codes.add("extraction_errors_watch")
    if item.missing_resolution_terms_count >= config.block_missing_resolution_terms_count:
        reason_codes.add("resolution_terms_missing_block")
    elif item.missing_resolution_terms_count >= config.watch_missing_resolution_terms_count:
        reason_codes.add("resolution_terms_missing_watch")
    if item.contradiction_pressure_score >= config.watch_contradiction_pressure_score:
        reason_codes.add("contradiction_pressure_high")
    if item.authority_coverage_score < config.block_quality_score:
        reason_codes.add("authority_coverage_gap")
    if item.resolution_alignment_score < config.block_quality_score:
        reason_codes.add("resolution_alignment_gap")
    prefixed = {
        code if code.startswith("resolution_")
        or code.startswith("quality_")
        or code.startswith("stale_")
        or code.startswith("extraction_")
        or code.startswith("contradiction_")
        or code.startswith("authority_")
        else f"input_{code}"
        for code in reason_codes
    }
    return _normalize_reason_codes(tuple(prefixed), allow_empty=False)


def _row_sort_key(
    row: ResearchSourceScraplingResolutionClaimQualityRow,
) -> tuple[object, ...]:
    return (
        _status_rank(row.status),
        row.quality_score,
        -row.contradiction_pressure_score,
        row.case_digest,
        row.capture_digest,
    )


def _report_status(
    rows: tuple[ResearchSourceScraplingResolutionClaimQualityRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchSourceScraplingResolutionClaimQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_claim_quality_no_items",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _reason_code_counts(
    rows: tuple[ResearchSourceScraplingResolutionClaimQualityRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        (reason_code, _count_decimal(count))
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _normalize_inputs(
    items: Iterable[object],
) -> tuple[ResearchSourceScraplingResolutionClaimQualityInput, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable")
    try:
        values = tuple(items)
    except TypeError as exc:
        raise ValueError("items must be an iterable") from exc
    normalized: list[ResearchSourceScraplingResolutionClaimQualityInput] = []
    for value in values:
        if type(value) is not ResearchSourceScraplingResolutionClaimQualityInput:
            raise ValueError(
                "items must contain "
                "ResearchSourceScraplingResolutionClaimQualityInput values",
            )
        _require_hard_flags("input", value)
        normalized.append(value)
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourceScraplingResolutionClaimQualityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceScraplingResolutionClaimQualityRow:
            raise ValueError(
                "rows must contain ResearchSourceScraplingResolutionClaimQualityRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[tuple[str, Decimal], ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    for count in counts:
        if type(count) is not tuple or len(count) != 2:
            raise ValueError("reason_code_counts must contain two-item tuples")
        reason_code, count_value = count
        _require_reason_code("reason_code", reason_code)
        normalized.append(
            (
                reason_code,
                _require_nonnegative_decimal("reason_code_count", count_value),
            ),
        )
    sorted_counts = tuple(sorted(normalized, key=lambda item: item[0]))
    if tuple(normalized) != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason code")
    return sorted_counts


def _validate_config(
    config: ResearchSourceScraplingResolutionClaimQualityConfig,
) -> None:
    weight_total = _quantize(
        config.evidence_quality_weight
        + config.resolution_alignment_weight
        + config.authority_coverage_weight
        + config.contradiction_pressure_weight,
    )
    if weight_total != ONE:
        raise ValueError("quality weights must sum to 1")
    if config.block_quality_score >= config.watch_quality_score:
        raise ValueError("block_quality_score must be below watch_quality_score")
    _require_threshold_pair(
        "block_staleness_hours",
        config.watch_staleness_hours,
        config.block_staleness_hours,
    )
    _require_threshold_pair(
        "block_extraction_error_count",
        config.watch_extraction_error_count,
        config.block_extraction_error_count,
    )
    _require_threshold_pair(
        "block_missing_resolution_terms_count",
        config.watch_missing_resolution_terms_count,
        config.block_missing_resolution_terms_count,
    )
    _require_threshold_pair(
        "block_contradiction_pressure_score",
        config.watch_contradiction_pressure_score,
        config.block_contradiction_pressure_score,
    )


def _validate_row(row: ResearchSourceScraplingResolutionClaimQualityRow) -> None:
    if f"resolution_claim_quality_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchSourceScraplingResolutionClaimQualityReport) -> None:
    if report.item_count != _count_decimal(len(report.rows)):
        raise ValueError("item_count must match rows")
    for field_name, status in (
        ("pass_count", PASS_STATUS),
        ("watch_count", WATCH_STATUS),
        ("block_count", BLOCK_STATUS),
    ):
        if getattr(report, field_name) != _count_decimal(_status_count(report.rows, status)):
            raise ValueError(f"{field_name} must match rows")
    if report.average_quality_score != _average_or_zero(
        row.quality_score for row in report.rows
    ):
        raise ValueError("average_quality_score must match rows")
    if report.lowest_quality_score != _minimum_or_zero(
        row.quality_score for row in report.rows
    ):
        raise ValueError("lowest_quality_score must match rows")
    if report.highest_contradiction_pressure_score != _maximum_or_zero(
        row.contradiction_pressure_score for row in report.rows
    ):
        raise ValueError("highest_contradiction_pressure_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _json_ready(value: object) -> Any:
    return _payload_value(value)


def _report_values_without_digest(
    report: ResearchSourceScraplingResolutionClaimQualityReport,
) -> dict[str, Any]:
    values = _json_ready(asdict(report))
    if type(values) is not dict:
        raise ValueError("report values must be a JSON object")
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: object) -> str:
    ready_values = _json_ready(values)
    encoded = json.dumps(
        ready_values,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceScraplingResolutionClaimQualityReport:
    _require_public_payload_keys(
        "public payload",
        payload,
        ResearchSourceScraplingResolutionClaimQualityReport,
    )
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("public payload rows must be a list")
    rows = tuple(
        _row_from_public_payload(row_value, index)
        for index, row_value in enumerate(rows_value)
    )
    reason_code_counts_value = payload["reason_code_counts"]
    if type(reason_code_counts_value) is not list:
        raise ValueError("public payload reason_code_counts must be a list")
    reason_code_counts: list[tuple[str, Decimal]] = []
    for index, count_value in enumerate(reason_code_counts_value):
        if type(count_value) is not list or len(count_value) != 2:
            raise ValueError(
                "public payload reason_code_counts entries must be two-item lists",
            )
        reason_code, count = count_value
        if type(reason_code) is not str:
            raise ValueError(
                f"public payload reason_code_counts[{index}][0] must be a string",
            )
        reason_code_counts.append(
            (
                reason_code,
                _public_decimal_string(
                    f"public payload reason_code_counts[{index}][1]",
                    count,
                ),
            ),
        )
    return ResearchSourceScraplingResolutionClaimQualityReport(
        generated_at=_public_datetime_string(
            "public payload generated_at",
            payload["generated_at"],
        ),
        config_version=payload["config_version"],
        status=payload["status"],
        item_count=_public_decimal_string(
            "public payload item_count",
            payload["item_count"],
        ),
        pass_count=_public_decimal_string(
            "public payload pass_count",
            payload["pass_count"],
        ),
        watch_count=_public_decimal_string(
            "public payload watch_count",
            payload["watch_count"],
        ),
        block_count=_public_decimal_string(
            "public payload block_count",
            payload["block_count"],
        ),
        average_quality_score=_public_decimal_string(
            "public payload average_quality_score",
            payload["average_quality_score"],
        ),
        lowest_quality_score=_public_decimal_string(
            "public payload lowest_quality_score",
            payload["lowest_quality_score"],
        ),
        highest_contradiction_pressure_score=_public_decimal_string(
            "public payload highest_contradiction_pressure_score",
            payload["highest_contradiction_pressure_score"],
        ),
        rows=rows,
        reason_code_counts=tuple(reason_code_counts),
        reason_codes=_public_string_list(
            "public payload reason_codes",
            payload["reason_codes"],
        ),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    value: object,
    index: int,
) -> ResearchSourceScraplingResolutionClaimQualityRow:
    label = f"public payload rows[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{label} must be an object")
    _require_public_payload_keys(
        label,
        value,
        ResearchSourceScraplingResolutionClaimQualityRow,
    )
    return ResearchSourceScraplingResolutionClaimQualityRow(
        case_digest=value["case_digest"],
        capture_digest=value["capture_digest"],
        observed_at=_public_datetime_string(
            f"{label} observed_at",
            value["observed_at"],
        ),
        evidence_quality_score=_public_decimal_string(
            f"{label} evidence_quality_score",
            value["evidence_quality_score"],
        ),
        resolution_alignment_score=_public_decimal_string(
            f"{label} resolution_alignment_score",
            value["resolution_alignment_score"],
        ),
        authority_coverage_score=_public_decimal_string(
            f"{label} authority_coverage_score",
            value["authority_coverage_score"],
        ),
        contradiction_pressure_score=_public_decimal_string(
            f"{label} contradiction_pressure_score",
            value["contradiction_pressure_score"],
        ),
        staleness_hours=_public_decimal_string(
            f"{label} staleness_hours",
            value["staleness_hours"],
        ),
        extraction_error_count=_public_decimal_string(
            f"{label} extraction_error_count",
            value["extraction_error_count"],
        ),
        missing_resolution_terms_count=_public_decimal_string(
            f"{label} missing_resolution_terms_count",
            value["missing_resolution_terms_count"],
        ),
        quality_score=_public_decimal_string(
            f"{label} quality_score",
            value["quality_score"],
        ),
        status=value["status"],
        reason_codes=_public_string_list(
            f"{label} reason_codes",
            value["reason_codes"],
        ),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _require_public_payload_keys(
    label: str,
    value: dict[object, object],
    expected_type: type[object],
) -> None:
    if any(type(key) is not str for key in value):
        raise ValueError(f"{label} keys must be strings")
    expected_keys = {field.name for field in fields(expected_type)}
    if set(value) != expected_keys:
        raise ValueError(f"{label} must use exact public schema fields")


def _public_decimal_string(label: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{label} must be a Decimal-derived string")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a Decimal-derived string") from exc


def _public_datetime_string(label: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{label} must be an ISO datetime string")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO datetime string") from exc


def _public_string_list(label: str, value: object) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise ValueError(f"{label} must be a list of strings")
    return tuple(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        if isinstance(value, datetime):
            raise ValueError(f"{field_name} must be exactly datetime")
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be exactly Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_UP)


def _status_count(
    rows: tuple[ResearchSourceScraplingResolutionClaimQualityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_or_zero(values: Iterable[Decimal]) -> Decimal:
    materialized = tuple(values)
    if not materialized:
        return ZERO
    return _quantize(sum(materialized, ZERO) / Decimal(len(materialized)))


def _minimum_or_zero(values: Iterable[Decimal]) -> Decimal:
    materialized = tuple(values)
    if not materialized:
        return ZERO
    return min(materialized)


def _maximum_or_zero(values: Iterable[Decimal]) -> Decimal:
    materialized = tuple(values)
    if not materialized:
        return ZERO
    return max(materialized)


def _status_rank(status: str) -> int:
    if status == BLOCK_STATUS:
        return 0
    if status == WATCH_STATUS:
        return 1
    return 2


def _reference_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_private_reference(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty reference string")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_identifier(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in value:
            raise ValueError("reason_code contains unsafe text")


def _normalize_reason_codes(
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code("reason_code", value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError("reason_codes must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_SCRAPLING_RESOLUTION_CLAIM_QUALITY_STATUSES
    ):
        raise ValueError(f"{field_name} must be one of known statuses")


def _require_threshold_pair(field_name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{field_name} must be greater than watch threshold")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    allowed = "0123456789abcdef"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in FLAG_FIELDS:
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _field_value(value: object, field_name: str) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if isinstance(value, dict) and field_name in value:
        return value[field_name]
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")


def _reject_public_numerics(value: object) -> None:
    if type(value) in (float, int) or isinstance(value, Decimal):
        raise ValueError("public payload numerics must be strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        value = _json_ready(asdict(value))
        allow_json_containers = True
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = str(key).lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public field")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, list):
        if not allow_json_containers:
            raise ValueError(f"{label} contains unsafe public container")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        lowered_value = value.lower()
        if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public value")


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")
