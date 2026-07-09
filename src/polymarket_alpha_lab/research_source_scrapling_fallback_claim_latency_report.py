"""Pure report-only Scrapling fallback claim latency reducer.

Callers provide already-sanitized timing telemetry from local collection flows.
This module performs no external access and returns a deterministic public
report with redacted row labels, Decimal-only numerics, and SHA-256 digest
validation.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_SCRAPLING_FALLBACK_CLAIM_LATENCY_REPORT_CONFIG_VERSION = (
    "research-source-scrapling-fallback-claim-latency-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECOND_DIVISOR = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
COLLECTOR_FAMILIES = ("generic", "scrapling")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

NO_INPUTS_REASON = "scrapling_fallback_claim_latency_no_inputs"
PASS_REASON = "scrapling_fallback_claim_latency_pass"
WATCH_REASON = "scrapling_fallback_claim_latency_watch"
BLOCK_REASON = "scrapling_fallback_claim_latency_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    "claim_latency_block",
    "claim_latency_watch",
    "fallback_ratio_block",
    "fallback_ratio_watch",
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
DECIMAL_STRING_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
ROW_LABEL_RE = re.compile(r"^redacted-claim-latency-[0-9]{6}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "raw candidate",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "slug",
    "question",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "url",
    "http://",
    "https://",
    "www.",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "network",
    "auth",
    "sizing",
    "recommendation",
    "execution",
)
TOP_LEVEL_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "attention_count",
        "max_claim_latency_seconds",
        "average_claim_latency_seconds",
        "average_fallback_ratio",
        "average_latency_pressure_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "row_label",
        "collector_family",
        "claim_latency_seconds",
        "claim_latency_score",
        "fallback_ratio",
        "latency_pressure_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPLING_FALLBACK_CLAIM_LATENCY_REPORT_CONFIG_VERSION",
    "ResearchSourceScraplingFallbackClaimLatencyConfig",
    "ResearchSourceScraplingFallbackClaimLatencyInput",
    "ResearchSourceScraplingFallbackClaimLatencyReasonCodeCount",
    "ResearchSourceScraplingFallbackClaimLatencyReport",
    "ResearchSourceScraplingFallbackClaimLatencyRow",
    "STATUSES",
    "build_research_source_scrapling_fallback_claim_latency_report",
    "research_source_scrapling_fallback_claim_latency_report_digest",
    "research_source_scrapling_fallback_claim_latency_report_payload",
    "validate_research_source_scrapling_fallback_claim_latency_public_payload",
)


@dataclass(frozen=True)
class ResearchSourceScraplingFallbackClaimLatencyConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPLING_FALLBACK_CLAIM_LATENCY_REPORT_CONFIG_VERSION
    )
    fresh_claim_max_age_seconds: Decimal = Decimal("1800.000000")
    watch_claim_max_age_seconds: Decimal = Decimal("7200.000000")
    block_claim_max_age_seconds: Decimal = Decimal("21600.000000")
    fallback_watch_ratio: Decimal = Decimal("0.250000")
    fallback_block_ratio: Decimal = Decimal("0.500000")
    claim_latency_weight: Decimal = Decimal("0.600000")
    fallback_pressure_weight: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingFallbackClaimLatencyConfig:
            raise TypeError(
                "ResearchSourceScraplingFallbackClaimLatencyConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingFallbackClaimLatencyConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_FALLBACK_CLAIM_LATENCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_claim_max_age_seconds",
            "watch_claim_max_age_seconds",
            "block_claim_max_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_claim_max_age_seconds >= self.watch_claim_max_age_seconds:
            raise ValueError(
                "fresh_claim_max_age_seconds must be below watch_claim_max_age_seconds",
            )
        if self.watch_claim_max_age_seconds >= self.block_claim_max_age_seconds:
            raise ValueError(
                "watch_claim_max_age_seconds must be below block_claim_max_age_seconds",
            )
        for field_name in (
            "fallback_watch_ratio",
            "fallback_block_ratio",
            "claim_latency_weight",
            "fallback_pressure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.fallback_watch_ratio > self.fallback_block_ratio:
            raise ValueError("fallback watch threshold must not exceed block threshold")
        weight_sum = _quantize(self.claim_latency_weight + self.fallback_pressure_weight)
        if weight_sum != ONE:
            raise ValueError("latency pressure weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingFallbackClaimLatencyInput:
    private_candidate_ref: str
    collector_family: str
    claim_observed_at: datetime
    fallback_attempt_count: Decimal
    primary_attempt_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingFallbackClaimLatencyInput:
            raise TypeError(
                "ResearchSourceScraplingFallbackClaimLatencyInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingFallbackClaimLatencyInput,
            "input",
        )
        _require_private_string("private_candidate_ref", self.private_candidate_ref)
        _require_member("collector_family", self.collector_family, COLLECTOR_FAMILIES)
        object.__setattr__(
            self,
            "claim_observed_at",
            _as_utc("claim_observed_at", self.claim_observed_at),
        )
        object.__setattr__(
            self,
            "fallback_attempt_count",
            _normalize_nonnegative_count(
                "fallback_attempt_count",
                self.fallback_attempt_count,
            ),
        )
        object.__setattr__(
            self,
            "primary_attempt_count",
            _normalize_positive_count("primary_attempt_count", self.primary_attempt_count),
        )
        if self.fallback_attempt_count > self.primary_attempt_count:
            raise ValueError(
                "fallback_attempt_count must not exceed primary_attempt_count",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceScraplingFallbackClaimLatencyRow:
    row_label: str
    collector_family: str
    claim_latency_seconds: Decimal
    claim_latency_score: Decimal
    fallback_ratio: Decimal
    latency_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingFallbackClaimLatencyRow:
            raise TypeError(
                "ResearchSourceScraplingFallbackClaimLatencyRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraplingFallbackClaimLatencyRow, "row")
        _require_public_identifier("row_label", self.row_label)
        _require_member("collector_family", self.collector_family, COLLECTOR_FAMILIES)
        object.__setattr__(
            self,
            "claim_latency_seconds",
            _normalize_nonnegative_decimal(
                "claim_latency_seconds",
                self.claim_latency_seconds,
            ),
        )
        for field_name in (
            "claim_latency_score",
            "fallback_ratio",
            "latency_pressure_score",
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
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScraplingFallbackClaimLatencyReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingFallbackClaimLatencyReasonCodeCount:
            raise TypeError(
                "ResearchSourceScraplingFallbackClaimLatencyReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingFallbackClaimLatencyReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchSourceScraplingFallbackClaimLatencyReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    max_claim_latency_seconds: Decimal
    average_claim_latency_seconds: Decimal
    average_fallback_ratio: Decimal
    average_latency_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceScraplingFallbackClaimLatencyReasonCodeCount, ...]
    rows: tuple[ResearchSourceScraplingFallbackClaimLatencyRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingFallbackClaimLatencyReport:
            raise TypeError(
                "ResearchSourceScraplingFallbackClaimLatencyReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraplingFallbackClaimLatencyReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_FALLBACK_CLAIM_LATENCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "attention_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_claim_latency_seconds",
            "average_claim_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_fallback_ratio",
            "average_latency_pressure_score",
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
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_scrapling_fallback_claim_latency_report_payload(self)


def build_research_source_scrapling_fallback_claim_latency_report(
    inputs: Iterable[ResearchSourceScraplingFallbackClaimLatencyInput],
    *,
    config: ResearchSourceScraplingFallbackClaimLatencyConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingFallbackClaimLatencyReport:
    if type(config) is not ResearchSourceScraplingFallbackClaimLatencyConfig:
        raise ValueError(
            "config must be exactly ResearchSourceScraplingFallbackClaimLatencyConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.claim_observed_at > generated_at:
            raise ValueError("claim_observed_at cannot be after generated_at")

    rows = tuple(
        _row_from_input(
            item,
            row_number=index,
            config=config,
            generated_at=generated_at,
        )
        for index, item in enumerate(normalized_inputs, start=1)
    )
    input_count = _count_decimal(len(normalized_inputs))
    pass_count = _count_decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count_decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _count_decimal(sum(1 for row in rows if row.status == "block"))
    attention_count = watch_count + block_count
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows, status)

    return ResearchSourceScraplingFallbackClaimLatencyReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=input_count,
        row_count=_count_decimal(len(rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        attention_count=attention_count,
        max_claim_latency_seconds=max(
            (row.claim_latency_seconds for row in rows),
            default=ZERO,
        ),
        average_claim_latency_seconds=_average_decimal(
            row.claim_latency_seconds for row in rows
        ),
        average_fallback_ratio=_average_decimal(row.fallback_ratio for row in rows),
        average_latency_pressure_score=_average_decimal(
            row.latency_pressure_score for row in rows
        ),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_scrapling_fallback_claim_latency_report_payload(
    report: ResearchSourceScraplingFallbackClaimLatencyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceScraplingFallbackClaimLatencyReport:
        raise ValueError(
            "report must be exactly ResearchSourceScraplingFallbackClaimLatencyReport",
        )
    _validate_report_consistency(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def research_source_scrapling_fallback_claim_latency_report_digest(
    report: ResearchSourceScraplingFallbackClaimLatencyReport,
) -> str:
    payload = research_source_scrapling_fallback_claim_latency_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_source_scrapling_fallback_claim_latency_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        return False
    try:
        _validate_public_payload(payload)
        digest = payload.get("derived_validation_digest")
        if type(digest) is not str or not DIGEST_RE.fullmatch(digest):
            return False
        unsigned = dict(payload)
        unsigned.pop("derived_validation_digest")
        encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        return sha256(encoded).hexdigest() == digest
    except (TypeError, ValueError):
        return False


def _normalize_inputs(
    inputs: Iterable[ResearchSourceScraplingFallbackClaimLatencyInput],
) -> tuple[ResearchSourceScraplingFallbackClaimLatencyInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchSourceScraplingFallbackClaimLatencyInput:
            raise ValueError(
                "inputs must contain ResearchSourceScraplingFallbackClaimLatencyInput",
            )
        _require_hard_flags("input", item)
    return tuple(sorted(normalized, key=_input_sort_key))


def _input_sort_key(
    item: ResearchSourceScraplingFallbackClaimLatencyInput,
) -> tuple[str, str, Decimal, Decimal]:
    return (
        item.collector_family,
        item.claim_observed_at.isoformat(),
        item.fallback_attempt_count,
        item.primary_attempt_count,
    )


def _row_from_input(
    item: ResearchSourceScraplingFallbackClaimLatencyInput,
    *,
    row_number: int,
    config: ResearchSourceScraplingFallbackClaimLatencyConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingFallbackClaimLatencyRow:
    claim_latency_seconds = _age_seconds(generated_at, item.claim_observed_at)
    fallback_ratio = _safe_ratio(
        item.fallback_attempt_count,
        item.fallback_attempt_count + item.primary_attempt_count,
    )
    claim_latency_score = _claim_latency_score(claim_latency_seconds, config)
    latency_pressure_score = _quantize(
        claim_latency_score * config.claim_latency_weight
        + fallback_ratio * config.fallback_pressure_weight,
    )
    reason_codes = _row_reason_codes(
        claim_latency_seconds=claim_latency_seconds,
        fallback_ratio=fallback_ratio,
        config=config,
    )
    status = _row_status(reason_codes)
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        (*reason_codes, _status_reason(status)),
    )
    return ResearchSourceScraplingFallbackClaimLatencyRow(
        row_label=f"redacted-claim-latency-{row_number:06d}",
        collector_family=item.collector_family,
        claim_latency_seconds=claim_latency_seconds,
        claim_latency_score=claim_latency_score,
        fallback_ratio=fallback_ratio,
        latency_pressure_score=latency_pressure_score,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _claim_latency_score(
    claim_latency_seconds: Decimal,
    config: ResearchSourceScraplingFallbackClaimLatencyConfig,
) -> Decimal:
    if claim_latency_seconds <= config.fresh_claim_max_age_seconds:
        return ZERO
    return min(ONE, _safe_ratio(claim_latency_seconds, config.watch_claim_max_age_seconds))


def _row_reason_codes(
    *,
    claim_latency_seconds: Decimal,
    fallback_ratio: Decimal,
    config: ResearchSourceScraplingFallbackClaimLatencyConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if claim_latency_seconds >= config.block_claim_max_age_seconds:
        reason_codes.append("claim_latency_block")
    elif claim_latency_seconds > config.fresh_claim_max_age_seconds:
        reason_codes.append("claim_latency_watch")

    if fallback_ratio >= config.fallback_block_ratio:
        reason_codes.append("fallback_ratio_block")
    elif fallback_ratio >= config.fallback_watch_ratio:
        reason_codes.append("fallback_ratio_watch")

    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_reason(status: str) -> str:
    if status == "pass":
        return PASS_REASON
    if status == "watch":
        return WATCH_REASON
    if status == "block":
        return BLOCK_REASON
    raise ValueError("status must be pass, watch, or block")


def _report_status(rows: tuple[ResearchSourceScraplingFallbackClaimLatencyRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScraplingFallbackClaimLatencyRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON, BLOCK_REASON)
    reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    reason_codes.add(_status_reason(status))
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceScraplingFallbackClaimLatencyReasonCodeCount, ...]:
    counts = Counter(reason_codes)
    return tuple(
        ResearchSourceScraplingFallbackClaimLatencyReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counts[reason_code]),
            paper_only=True,
            report_only=True,
            readonly=True,
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: tuple[ResearchSourceScraplingFallbackClaimLatencyRow, ...],
) -> tuple[ResearchSourceScraplingFallbackClaimLatencyRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchSourceScraplingFallbackClaimLatencyRow:
            raise ValueError(
                "rows must contain ResearchSourceScraplingFallbackClaimLatencyRow",
            )
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(row: ResearchSourceScraplingFallbackClaimLatencyRow) -> tuple[int, str, str]:
    return (STATUS_WEIGHT[row.status], row.row_label, row.collector_family)


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceScraplingFallbackClaimLatencyReasonCodeCount, ...],
) -> tuple[ResearchSourceScraplingFallbackClaimLatencyReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        if type(count) is not ResearchSourceScraplingFallbackClaimLatencyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceScraplingFallbackClaimLatencyReasonCodeCount",
            )
    return tuple(
        sorted(
            normalized,
            key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _validate_report_consistency(
    report: ResearchSourceScraplingFallbackClaimLatencyReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _count_decimal(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.attention_count != report.watch_count + report.block_count:
        raise ValueError("attention_count must match watch and block counts")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows, report.status):
        raise ValueError("reason_codes must match rows and status")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.max_claim_latency_seconds != max(
        (row.claim_latency_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_claim_latency_seconds must match rows")
    expected_averages = {
        "average_claim_latency_seconds": _average_decimal(
            row.claim_latency_seconds for row in report.rows
        ),
        "average_fallback_ratio": _average_decimal(row.fallback_ratio for row in report.rows),
        "average_latency_pressure_score": _average_decimal(
            row.latency_pressure_score for row in report.rows
        ),
    }
    for field_name, expected_value in expected_averages.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_status(field_name: str, value: object) -> str:
    return _require_member(field_name, value, STATUSES)


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_private_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty private text")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if value != normalized:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECOND_DIVISOR),
    )


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _report_digest(report: ResearchSourceScraplingFallbackClaimLatencyReport) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _validate_public_payload(payload, require_digest=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


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


def _validate_public_payload(value: object, *, require_digest: bool = True) -> None:
    _reject_unsafe_public_payload("payload", value, allow_json_containers=True)
    _reject_raw_numeric_payload(value)
    _validate_public_payload_schema(value, require_digest=require_digest)


def _reject_raw_numeric_payload(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_raw_numeric_payload(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_raw_numeric_payload(item)


def _validate_public_payload_schema(
    value: object,
    *,
    require_digest: bool,
) -> None:
    if type(value) is not dict:
        raise ValueError("public payload must be a JSON object")
    expected_keys = set(TOP_LEVEL_PAYLOAD_KEYS)
    if not require_digest:
        expected_keys.remove("derived_validation_digest")
    _require_exact_payload_keys("payload", value, expected_keys)

    _require_canonical_utc_datetime_string("generated_at", value["generated_at"])
    _require_public_identifier("config_version", value["config_version"])
    if (
        value["config_version"]
        != DEFAULT_RESEARCH_SOURCE_SCRAPLING_FALLBACK_CLAIM_LATENCY_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")

    input_count = _require_public_count_string("input_count", value["input_count"])
    row_count = _require_public_count_string("row_count", value["row_count"])
    pass_count = _require_public_count_string("pass_count", value["pass_count"])
    watch_count = _require_public_count_string("watch_count", value["watch_count"])
    block_count = _require_public_count_string("block_count", value["block_count"])
    attention_count = _require_public_count_string(
        "attention_count",
        value["attention_count"],
    )
    max_claim_latency_seconds = _require_public_nonnegative_decimal_string(
        "max_claim_latency_seconds",
        value["max_claim_latency_seconds"],
    )
    average_claim_latency_seconds = _require_public_nonnegative_decimal_string(
        "average_claim_latency_seconds",
        value["average_claim_latency_seconds"],
    )
    average_fallback_ratio = _require_public_probability_string(
        "average_fallback_ratio",
        value["average_fallback_ratio"],
    )
    average_latency_pressure_score = _require_public_probability_string(
        "average_latency_pressure_score",
        value["average_latency_pressure_score"],
    )
    status = _require_status("status", value["status"])
    reason_codes = _require_public_reason_codes("reason_codes", value["reason_codes"])
    reason_code_counts = _require_public_reason_code_counts(
        "reason_code_counts",
        value["reason_code_counts"],
    )
    rows = _require_public_rows("rows", value["rows"])
    if require_digest:
        _require_digest("derived_validation_digest", value["derived_validation_digest"])
    _require_public_true("paper_only", value["paper_only"])
    _require_public_true("report_only", value["report_only"])
    _require_public_true("readonly", value["readonly"])

    if input_count != row_count:
        raise ValueError("input_count must match row_count")
    if row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if pass_count != _count_decimal(sum(1 for row in rows if row["status"] == "pass")):
        raise ValueError("pass_count must match rows")
    if watch_count != _count_decimal(sum(1 for row in rows if row["status"] == "watch")):
        raise ValueError("watch_count must match rows")
    if block_count != _count_decimal(sum(1 for row in rows if row["status"] == "block")):
        raise ValueError("block_count must match rows")
    if attention_count != watch_count + block_count:
        raise ValueError("attention_count must match watch and block counts")
    expected_status = _public_report_status(rows)
    if status != expected_status:
        raise ValueError("status must match row statuses")
    expected_reason_codes = _public_report_reason_codes(rows, status)
    if reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows and status")
    if reason_code_counts != _public_reason_code_counts(reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if max_claim_latency_seconds != max(
        (row["claim_latency_seconds"] for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_claim_latency_seconds must match rows")
    if average_claim_latency_seconds != _average_decimal(
        row["claim_latency_seconds"] for row in rows
    ):
        raise ValueError("average_claim_latency_seconds must match rows")
    if average_fallback_ratio != _average_decimal(row["fallback_ratio"] for row in rows):
        raise ValueError("average_fallback_ratio must match rows")
    if average_latency_pressure_score != _average_decimal(
        row["latency_pressure_score"] for row in rows
    ):
        raise ValueError("average_latency_pressure_score must match rows")


def _require_exact_payload_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: set[str],
) -> None:
    if set(value) != expected_keys:
        raise ValueError(f"{label} must use the supported public schema")


def _require_public_true(field_name: str, value: object) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must be True")


def _require_canonical_utc_datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be canonical UTC")
    return normalized


def _parse_public_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    if not DECIMAL_STRING_RE.fullmatch(value):
        raise ValueError(f"{field_name} must use six decimal places")
    try:
        parsed = Decimal(value)
        normalized = _quantize(parsed)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must be canonical") from exc
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _require_public_nonnegative_decimal_string(
    field_name: str,
    value: object,
) -> Decimal:
    parsed = _parse_public_decimal_string(field_name, value)
    if parsed < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return parsed


def _require_public_count_string(field_name: str, value: object) -> Decimal:
    parsed = _require_public_nonnegative_decimal_string(field_name, value)
    if parsed != parsed.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return parsed


def _require_public_probability_string(field_name: str, value: object) -> Decimal:
    parsed = _parse_public_decimal_string(field_name, value)
    if parsed < ZERO or parsed > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return parsed


def _require_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    reason_codes = tuple(value)
    normalized = _normalize_reason_codes(field_name, reason_codes)
    if reason_codes != normalized:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _require_public_reason_code_counts(
    field_name: str,
    value: object,
) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized: list[tuple[str, Decimal]] = []
    for index, item in enumerate(value):
        label = f"{field_name}[{index}]"
        if type(item) is not dict:
            raise ValueError(f"{label} must be a JSON object")
        _require_exact_payload_keys(label, item, set(REASON_CODE_COUNT_PAYLOAD_KEYS))
        reason_code = _require_reason_code("reason_code", item["reason_code"])
        count = _require_public_count_string("count", item["count"])
        if count <= ZERO:
            raise ValueError("count must be positive")
        _require_public_true("paper_only", item["paper_only"])
        _require_public_true("report_only", item["report_only"])
        _require_public_true("readonly", item["readonly"])
        normalized.append((reason_code, count))
    expected_order = tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in {reason_code for reason_code, _count in normalized}
    )
    if tuple(reason_code for reason_code, _count in normalized) != expected_order:
        raise ValueError(f"{field_name} must be canonical")
    return tuple(normalized)


def _require_public_rows(
    field_name: str,
    value: object,
) -> tuple[dict[str, object], ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    rows: list[dict[str, object]] = []
    seen_labels: set[str] = set()
    for index, item in enumerate(value):
        label = f"{field_name}[{index}]"
        if type(item) is not dict:
            raise ValueError(f"{label} must be a JSON object")
        _require_exact_payload_keys(label, item, set(ROW_PAYLOAD_KEYS))
        row_label = item["row_label"]
        _require_public_identifier("row_label", row_label)
        if not ROW_LABEL_RE.fullmatch(row_label):
            raise ValueError("row_label must be redacted")
        if row_label in seen_labels:
            raise ValueError("row_label must be unique")
        seen_labels.add(row_label)
        collector_family = _require_member(
            "collector_family",
            item["collector_family"],
            COLLECTOR_FAMILIES,
        )
        claim_latency_seconds = _require_public_nonnegative_decimal_string(
            "claim_latency_seconds",
            item["claim_latency_seconds"],
        )
        claim_latency_score = _require_public_probability_string(
            "claim_latency_score",
            item["claim_latency_score"],
        )
        fallback_ratio = _require_public_probability_string(
            "fallback_ratio",
            item["fallback_ratio"],
        )
        latency_pressure_score = _require_public_probability_string(
            "latency_pressure_score",
            item["latency_pressure_score"],
        )
        status = _require_status("status", item["status"])
        reason_codes = _require_public_reason_codes("reason_codes", item["reason_codes"])
        if _status_reason(status) not in reason_codes:
            raise ValueError("row reason_codes must include status reason")
        non_status_reason_codes = tuple(
            reason_code
            for reason_code in reason_codes
            if reason_code != _status_reason(status)
        )
        if status == "pass" and non_status_reason_codes:
            raise ValueError("pass row reason_codes must only include pass reason")
        if status == "watch" and not any(
            reason_code.endswith("_watch") for reason_code in non_status_reason_codes
        ):
            raise ValueError("watch row reason_codes must include watch reason")
        if status == "block" and not any(
            reason_code.endswith("_block") for reason_code in non_status_reason_codes
        ):
            raise ValueError("block row reason_codes must include block reason")
        if status != _row_status(reason_codes):
            raise ValueError("row status must match reason_codes")
        _require_public_true("paper_only", item["paper_only"])
        _require_public_true("report_only", item["report_only"])
        _require_public_true("readonly", item["readonly"])
        rows.append(
            {
                "row_label": row_label,
                "collector_family": collector_family,
                "claim_latency_seconds": claim_latency_seconds,
                "claim_latency_score": claim_latency_score,
                "fallback_ratio": fallback_ratio,
                "latency_pressure_score": latency_pressure_score,
                "status": status,
                "reason_codes": reason_codes,
            },
        )
    expected_rows = tuple(sorted(rows, key=_public_row_sort_key))
    if tuple(rows) != expected_rows:
        raise ValueError(f"{field_name} must be canonical")
    return tuple(rows)


def _public_row_sort_key(row: dict[str, object]) -> tuple[int, object, object]:
    return (
        STATUS_WEIGHT[str(row["status"])],
        row["row_label"],
        row["collector_family"],
    )


def _public_report_status(rows: tuple[dict[str, object], ...]) -> str:
    if not rows:
        return "block"
    if any(row["status"] == "block" for row in rows):
        return "block"
    if any(row["status"] == "watch" for row in rows):
        return "watch"
    return "pass"


def _public_report_reason_codes(
    rows: tuple[dict[str, object], ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON, BLOCK_REASON)
    reason_codes = {
        reason_code
        for row in rows
        for reason_code in row["reason_codes"]  # type: ignore[union-attr]
    }
    reason_codes.add(_status_reason(status))
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _public_reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts = Counter(reason_codes)
    return tuple(
        (reason_code, _count_decimal(counts[reason_code]))
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


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
    lowered = key.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")
