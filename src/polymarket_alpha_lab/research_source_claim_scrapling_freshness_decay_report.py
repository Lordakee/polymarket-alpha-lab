"""Pure report-only Scrapling claim freshness decay reducer.

Callers provide already-sanitized claim freshness telemetry. This module performs
no database, network, wallet, order, sizing, auth, or trading work and exposes
only a deterministic public report with redacted row labels, Decimal-only
numerics, and SHA-256 digest validation.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_CLAIM_SCRAPLING_FRESHNESS_DECAY_REPORT_CONFIG_VERSION = (
    "research-source-claim-scrapling-freshness-decay-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECOND_DIVISOR = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

RESEARCH_SOURCE_CLAIM_SCRAPLING_FRESHNESS_DECAY_STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

NO_INPUTS_REASON = "scrapling_claim_freshness_decay_no_inputs"
PASS_REASON = "scrapling_claim_freshness_decay_pass"
WATCH_REASON = "scrapling_claim_freshness_decay_watch"
BLOCK_REASON = "scrapling_claim_freshness_decay_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    "claim_age_block",
    "claim_age_watch",
    "scrapling_confidence_block",
    "scrapling_confidence_watch",
    "claim_support_block",
    "claim_support_watch",
    "authority_alignment_block",
    "authority_alignment_watch",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "raw candidate",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "market_question",
    "market question",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "http://",
    "https://",
    "www.",
    "dsn",
    "table_name",
    "table name",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "sizing",
    "recommend",
)

REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "attention_count",
        "max_claim_age_seconds",
        "average_claim_freshness_score",
        "average_scrapling_confidence_score",
        "average_claim_support_ratio",
        "average_authority_alignment_score",
        "average_contradiction_pressure_score",
        "average_freshness_decay_score",
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
REPORT_PAYLOAD_UNSIGNED_KEYS = REPORT_PAYLOAD_KEYS - frozenset(
    ("derived_validation_digest",),
)
REPORT_COUNT_PAYLOAD_FIELDS = (
    "input_count",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "attention_count",
)
REPORT_AVERAGE_PAYLOAD_FIELDS = (
    "average_claim_freshness_score",
    "average_scrapling_confidence_score",
    "average_claim_support_ratio",
    "average_authority_alignment_score",
    "average_contradiction_pressure_score",
    "average_freshness_decay_score",
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "row_label",
        "claim_age_seconds",
        "claim_freshness_score",
        "scrapling_confidence_score",
        "claim_support_ratio",
        "authority_alignment_score",
        "contradiction_pressure_score",
        "freshness_decay_score",
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
STATUS_REASON_CODES = frozenset((PASS_REASON, WATCH_REASON, BLOCK_REASON))

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_SCRAPLING_FRESHNESS_DECAY_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_CLAIM_SCRAPLING_FRESHNESS_DECAY_STATUSES",
    "ResearchSourceClaimScraplingFreshnessDecayConfig",
    "ResearchSourceClaimScraplingFreshnessDecayInput",
    "ResearchSourceClaimScraplingFreshnessDecayReasonCodeCount",
    "ResearchSourceClaimScraplingFreshnessDecayReport",
    "ResearchSourceClaimScraplingFreshnessDecayRow",
    "build_research_source_claim_scrapling_freshness_decay_report",
    "research_source_claim_scrapling_freshness_decay_report_digest",
    "research_source_claim_scrapling_freshness_decay_report_payload",
    "validate_research_source_claim_scrapling_freshness_decay_report_digest",
    "validate_research_source_claim_scrapling_freshness_decay_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceClaimScraplingFreshnessDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CLAIM_SCRAPLING_FRESHNESS_DECAY_REPORT_CONFIG_VERSION
    )
    fresh_claim_max_age_seconds: Decimal = Decimal("3600.000000")
    decayed_claim_watch_age_seconds: Decimal = Decimal("21600.000000")
    decayed_claim_block_age_seconds: Decimal = Decimal("86400.000000")
    min_scrapling_confidence_pass_ratio: Decimal = Decimal("0.850000")
    min_scrapling_confidence_watch_ratio: Decimal = Decimal("0.600000")
    min_claim_support_pass_ratio: Decimal = Decimal("0.800000")
    min_claim_support_watch_ratio: Decimal = Decimal("0.500000")
    min_authority_alignment_pass_ratio: Decimal = Decimal("0.750000")
    min_authority_alignment_watch_ratio: Decimal = Decimal("0.500000")
    max_contradiction_watch_pressure: Decimal = Decimal("0.150000")
    max_contradiction_block_pressure: Decimal = Decimal("0.400000")
    min_freshness_decay_pass_score: Decimal = Decimal("0.800000")
    min_freshness_decay_watch_score: Decimal = Decimal("0.500000")
    freshness_weight: Decimal = Decimal("0.300000")
    scrapling_confidence_weight: Decimal = Decimal("0.250000")
    claim_support_weight: Decimal = Decimal("0.200000")
    authority_alignment_weight: Decimal = Decimal("0.150000")
    contradiction_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimScraplingFreshnessDecayConfig:
            raise TypeError(
                "ResearchSourceClaimScraplingFreshnessDecayConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimScraplingFreshnessDecayConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_SCRAPLING_FRESHNESS_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_claim_max_age_seconds",
            "decayed_claim_watch_age_seconds",
            "decayed_claim_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if not (
            self.fresh_claim_max_age_seconds
            < self.decayed_claim_watch_age_seconds
            < self.decayed_claim_block_age_seconds
        ):
            raise ValueError(
                "fresh_claim_max_age_seconds must be below watch and block ages",
            )
        for field_name in (
            "min_scrapling_confidence_pass_ratio",
            "min_scrapling_confidence_watch_ratio",
            "min_claim_support_pass_ratio",
            "min_claim_support_watch_ratio",
            "min_authority_alignment_pass_ratio",
            "min_authority_alignment_watch_ratio",
            "max_contradiction_watch_pressure",
            "max_contradiction_block_pressure",
            "min_freshness_decay_pass_score",
            "min_freshness_decay_watch_score",
            "freshness_weight",
            "scrapling_confidence_weight",
            "claim_support_weight",
            "authority_alignment_weight",
            "contradiction_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_watch_not_above_pass(
            "scrapling confidence",
            self.min_scrapling_confidence_watch_ratio,
            self.min_scrapling_confidence_pass_ratio,
        )
        _require_watch_not_above_pass(
            "claim support",
            self.min_claim_support_watch_ratio,
            self.min_claim_support_pass_ratio,
        )
        _require_watch_not_above_pass(
            "authority alignment",
            self.min_authority_alignment_watch_ratio,
            self.min_authority_alignment_pass_ratio,
        )
        _require_watch_not_above_pass(
            "freshness decay",
            self.min_freshness_decay_watch_score,
            self.min_freshness_decay_pass_score,
        )
        if self.max_contradiction_watch_pressure > self.max_contradiction_block_pressure:
            raise ValueError(
                "contradiction watch pressure must not exceed block pressure",
            )
        weight_sum = _quantize(
            self.freshness_weight
            + self.scrapling_confidence_weight
            + self.claim_support_weight
            + self.authority_alignment_weight
            + self.contradiction_weight,
        )
        if weight_sum != ONE:
            raise ValueError("freshness decay weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimScraplingFreshnessDecayInput:
    private_candidate_ref: str
    observed_at: datetime
    scrapling_confidence_ratio: Decimal
    supporting_source_count: Decimal
    independent_source_count: Decimal
    authority_alignment_ratio: Decimal
    contradiction_flag_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimScraplingFreshnessDecayInput:
            raise TypeError(
                "ResearchSourceClaimScraplingFreshnessDecayInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimScraplingFreshnessDecayInput, "input")
        _require_private_string("private_candidate_ref", self.private_candidate_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("scrapling_confidence_ratio", "authority_alignment_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "supporting_source_count",
            _normalize_positive_count("supporting_source_count", self.supporting_source_count),
        )
        for field_name in ("independent_source_count", "contradiction_flag_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.supporting_source_count:
            raise ValueError(
                "independent_source_count must not exceed supporting_source_count",
            )
        if self.contradiction_flag_count > self.supporting_source_count:
            raise ValueError(
                "contradiction_flag_count must not exceed supporting_source_count",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceClaimScraplingFreshnessDecayRow:
    row_label: str
    claim_age_seconds: Decimal
    claim_freshness_score: Decimal
    scrapling_confidence_score: Decimal
    claim_support_ratio: Decimal
    authority_alignment_score: Decimal
    contradiction_pressure_score: Decimal
    freshness_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimScraplingFreshnessDecayRow:
            raise TypeError(
                "ResearchSourceClaimScraplingFreshnessDecayRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimScraplingFreshnessDecayRow, "row")
        _require_public_identifier("row_label", self.row_label)
        object.__setattr__(
            self,
            "claim_age_seconds",
            _normalize_nonnegative_decimal("claim_age_seconds", self.claim_age_seconds),
        )
        for field_name in (
            "claim_freshness_score",
            "scrapling_confidence_score",
            "claim_support_ratio",
            "authority_alignment_score",
            "contradiction_pressure_score",
            "freshness_decay_score",
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
class ResearchSourceClaimScraplingFreshnessDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimScraplingFreshnessDecayReasonCodeCount:
            raise TypeError(
                "ResearchSourceClaimScraplingFreshnessDecayReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceClaimScraplingFreshnessDecayReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchSourceClaimScraplingFreshnessDecayReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    max_claim_age_seconds: Decimal
    average_claim_freshness_score: Decimal
    average_scrapling_confidence_score: Decimal
    average_claim_support_ratio: Decimal
    average_authority_alignment_score: Decimal
    average_contradiction_pressure_score: Decimal
    average_freshness_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceClaimScraplingFreshnessDecayReasonCodeCount, ...]
    rows: tuple[ResearchSourceClaimScraplingFreshnessDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimScraplingFreshnessDecayReport:
            raise TypeError(
                "ResearchSourceClaimScraplingFreshnessDecayReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimScraplingFreshnessDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_SCRAPLING_FRESHNESS_DECAY_REPORT_CONFIG_VERSION
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
        object.__setattr__(
            self,
            "max_claim_age_seconds",
            _normalize_nonnegative_decimal(
                "max_claim_age_seconds",
                self.max_claim_age_seconds,
            ),
        )
        for field_name in (
            "average_claim_freshness_score",
            "average_scrapling_confidence_score",
            "average_claim_support_ratio",
            "average_authority_alignment_score",
            "average_contradiction_pressure_score",
            "average_freshness_decay_score",
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
        return research_source_claim_scrapling_freshness_decay_report_payload(self)


def build_research_source_claim_scrapling_freshness_decay_report(
    inputs: Iterable[ResearchSourceClaimScraplingFreshnessDecayInput],
    *,
    config: ResearchSourceClaimScraplingFreshnessDecayConfig,
    generated_at: datetime,
) -> ResearchSourceClaimScraplingFreshnessDecayReport:
    if type(config) is not ResearchSourceClaimScraplingFreshnessDecayConfig:
        raise ValueError(
            "config must be exactly ResearchSourceClaimScraplingFreshnessDecayConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at:
            raise ValueError("observed_at cannot be after generated_at")
    rows = tuple(
        _row_from_input(
            item,
            row_number=index,
            config=config,
            generated_at=generated_at,
        )
        for index, item in enumerate(normalized_inputs, start=1)
    )
    pass_count = _count_decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count_decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _count_decimal(sum(1 for row in rows if row.status == "block"))
    attention_count = watch_count + block_count
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows, status)
    return ResearchSourceClaimScraplingFreshnessDecayReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized_inputs)),
        row_count=_count_decimal(len(rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        attention_count=attention_count,
        max_claim_age_seconds=max(
            (row.claim_age_seconds for row in rows),
            default=ZERO,
        ),
        average_claim_freshness_score=_average(
            row.claim_freshness_score for row in rows
        ),
        average_scrapling_confidence_score=_average(
            row.scrapling_confidence_score for row in rows
        ),
        average_claim_support_ratio=_average(row.claim_support_ratio for row in rows),
        average_authority_alignment_score=_average(
            row.authority_alignment_score for row in rows
        ),
        average_contradiction_pressure_score=_average(
            row.contradiction_pressure_score for row in rows
        ),
        average_freshness_decay_score=_average(
            row.freshness_decay_score for row in rows
        ),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_claim_scrapling_freshness_decay_report_payload(
    report: ResearchSourceClaimScraplingFreshnessDecayReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceClaimScraplingFreshnessDecayReport:
        raise ValueError(
            "report must be exactly ResearchSourceClaimScraplingFreshnessDecayReport",
        )
    _validate_report_consistency(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    _validate_report_payload_schema(payload, require_digest=True)
    return payload


def research_source_claim_scrapling_freshness_decay_report_digest(
    report: ResearchSourceClaimScraplingFreshnessDecayReport,
) -> str:
    payload = research_source_claim_scrapling_freshness_decay_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_source_claim_scrapling_freshness_decay_report_digest(
    report: ResearchSourceClaimScraplingFreshnessDecayReport,
) -> None:
    if type(report) is not ResearchSourceClaimScraplingFreshnessDecayReport:
        raise ValueError(
            "report must be exactly ResearchSourceClaimScraplingFreshnessDecayReport",
        )
    expected_digest = _report_digest(report)
    _require_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")


def validate_research_source_claim_scrapling_freshness_decay_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        return False
    try:
        _validate_public_payload(payload)
        _validate_report_payload_schema(payload, require_digest=True)
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
    inputs: Iterable[ResearchSourceClaimScraplingFreshnessDecayInput],
) -> tuple[ResearchSourceClaimScraplingFreshnessDecayInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchSourceClaimScraplingFreshnessDecayInput:
            raise ValueError(
                "inputs must contain ResearchSourceClaimScraplingFreshnessDecayInput",
            )
        _require_hard_flags("input", item)
    return tuple(sorted(normalized, key=_input_sort_key))


def _input_sort_key(
    item: ResearchSourceClaimScraplingFreshnessDecayInput,
) -> tuple[str, str, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        item.private_candidate_ref,
        item.observed_at.isoformat(),
        item.scrapling_confidence_ratio,
        item.supporting_source_count,
        item.independent_source_count,
        item.authority_alignment_ratio,
        item.contradiction_flag_count,
        item.paper_only,
    )


def _row_from_input(
    item: ResearchSourceClaimScraplingFreshnessDecayInput,
    *,
    row_number: int,
    config: ResearchSourceClaimScraplingFreshnessDecayConfig,
    generated_at: datetime,
) -> ResearchSourceClaimScraplingFreshnessDecayRow:
    claim_age_seconds = _age_seconds(generated_at, item.observed_at)
    claim_freshness_score = _freshness_score(claim_age_seconds, config)
    claim_support_ratio = _safe_ratio(
        item.independent_source_count,
        item.supporting_source_count,
    )
    contradiction_pressure_score = min(
        ONE,
        _safe_ratio(item.contradiction_flag_count, item.supporting_source_count),
    )
    freshness_decay_score = _quantize(
        claim_freshness_score * config.freshness_weight
        + item.scrapling_confidence_ratio * config.scrapling_confidence_weight
        + claim_support_ratio * config.claim_support_weight
        + item.authority_alignment_ratio * config.authority_alignment_weight
        + (ONE - contradiction_pressure_score) * config.contradiction_weight,
    )
    reason_codes = _row_reason_codes(
        claim_freshness_score=claim_freshness_score,
        claim_age_seconds=claim_age_seconds,
        scrapling_confidence_score=item.scrapling_confidence_ratio,
        claim_support_ratio=claim_support_ratio,
        authority_alignment_score=item.authority_alignment_ratio,
        contradiction_pressure_score=contradiction_pressure_score,
        config=config,
    )
    status = _row_status(reason_codes, freshness_decay_score, config)
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        (*reason_codes, _status_reason(status)),
    )
    return ResearchSourceClaimScraplingFreshnessDecayRow(
        row_label=f"redacted-scrapling-claim-freshness-{row_number:06d}",
        claim_age_seconds=claim_age_seconds,
        claim_freshness_score=claim_freshness_score,
        scrapling_confidence_score=item.scrapling_confidence_ratio,
        claim_support_ratio=claim_support_ratio,
        authority_alignment_score=item.authority_alignment_ratio,
        contradiction_pressure_score=contradiction_pressure_score,
        freshness_decay_score=freshness_decay_score,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _freshness_score(
    claim_age_seconds: Decimal,
    config: ResearchSourceClaimScraplingFreshnessDecayConfig,
) -> Decimal:
    if claim_age_seconds <= config.fresh_claim_max_age_seconds:
        return ONE
    if claim_age_seconds >= config.decayed_claim_block_age_seconds:
        return ZERO
    decay_window = config.decayed_claim_block_age_seconds - config.fresh_claim_max_age_seconds
    decay_progress = _safe_ratio(
        claim_age_seconds - config.fresh_claim_max_age_seconds,
        decay_window,
    )
    return _quantize(ONE - decay_progress)


def _row_reason_codes(
    *,
    claim_freshness_score: Decimal,
    claim_age_seconds: Decimal,
    scrapling_confidence_score: Decimal,
    claim_support_ratio: Decimal,
    authority_alignment_score: Decimal,
    contradiction_pressure_score: Decimal,
    config: ResearchSourceClaimScraplingFreshnessDecayConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if claim_age_seconds >= config.decayed_claim_block_age_seconds:
        reason_codes.append("claim_age_block")
    elif claim_freshness_score < ONE:
        reason_codes.append("claim_age_watch")
    if scrapling_confidence_score < config.min_scrapling_confidence_watch_ratio:
        reason_codes.append("scrapling_confidence_block")
    elif scrapling_confidence_score < config.min_scrapling_confidence_pass_ratio:
        reason_codes.append("scrapling_confidence_watch")
    if claim_support_ratio < config.min_claim_support_watch_ratio:
        reason_codes.append("claim_support_block")
    elif claim_support_ratio < config.min_claim_support_pass_ratio:
        reason_codes.append("claim_support_watch")
    if authority_alignment_score < config.min_authority_alignment_watch_ratio:
        reason_codes.append("authority_alignment_block")
    elif authority_alignment_score < config.min_authority_alignment_pass_ratio:
        reason_codes.append("authority_alignment_watch")
    if contradiction_pressure_score >= config.max_contradiction_block_pressure:
        reason_codes.append("contradiction_pressure_block")
    elif contradiction_pressure_score >= config.max_contradiction_watch_pressure:
        reason_codes.append("contradiction_pressure_watch")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _row_status(
    reason_codes: tuple[str, ...],
    freshness_decay_score: Decimal,
    config: ResearchSourceClaimScraplingFreshnessDecayConfig,
) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if freshness_decay_score < config.min_freshness_decay_watch_score:
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    if freshness_decay_score < config.min_freshness_decay_pass_score:
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


def _report_status(rows: tuple[ResearchSourceClaimScraplingFreshnessDecayRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimScraplingFreshnessDecayRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON, BLOCK_REASON)
    reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    reason_codes.add(_status_reason(status))
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchSourceClaimScraplingFreshnessDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceClaimScraplingFreshnessDecayReasonCodeCount, ...]:
    if rows:
        counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    else:
        counts = Counter(reason_codes)
    return tuple(
        ResearchSourceClaimScraplingFreshnessDecayReasonCodeCount(
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
    rows: tuple[ResearchSourceClaimScraplingFreshnessDecayRow, ...],
) -> tuple[ResearchSourceClaimScraplingFreshnessDecayRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchSourceClaimScraplingFreshnessDecayRow:
            raise ValueError(
                "rows must contain ResearchSourceClaimScraplingFreshnessDecayRow",
            )
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(row: ResearchSourceClaimScraplingFreshnessDecayRow) -> tuple[int, str]:
    return (STATUS_WEIGHT[row.status], row.row_label)


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceClaimScraplingFreshnessDecayReasonCodeCount, ...],
) -> tuple[ResearchSourceClaimScraplingFreshnessDecayReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        if type(count) is not ResearchSourceClaimScraplingFreshnessDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceClaimScraplingFreshnessDecayReasonCodeCount",
            )
    return tuple(
        sorted(
            normalized,
            key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _validate_report_consistency(
    report: ResearchSourceClaimScraplingFreshnessDecayReport,
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
    if report.status != _report_status(report.rows):
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows, report.status):
        raise ValueError("reason_codes must match rows and status")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.max_claim_age_seconds != max(
        (row.claim_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_claim_age_seconds must match rows")
    expected_averages = {
        "average_claim_freshness_score": _average(
            row.claim_freshness_score for row in report.rows
        ),
        "average_scrapling_confidence_score": _average(
            row.scrapling_confidence_score for row in report.rows
        ),
        "average_claim_support_ratio": _average(
            row.claim_support_ratio for row in report.rows
        ),
        "average_authority_alignment_score": _average(
            row.authority_alignment_score for row in report.rows
        ),
        "average_contradiction_pressure_score": _average(
            row.contradiction_pressure_score for row in report.rows
        ),
        "average_freshness_decay_score": _average(
            row.freshness_decay_score for row in report.rows
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
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in normalized)


def _average(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _safe_ratio(sum(normalized, ZERO), _count_decimal(len(normalized)))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            Decimal(delta.days * 86400 + delta.seconds)
            + Decimal(delta.microseconds) / MICROSECOND_DIVISOR,
        )


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized == ZERO:
        return ZERO
    return normalized


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_private_string(field_name: str, value: str) -> None:
    if type(value) is not str or value == "":
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_public_identifier(field_name: str, value: str) -> None:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_text(field_name, value)


def _require_watch_not_above_pass(
    label: str,
    watch_value: Decimal,
    pass_value: Decimal,
) -> None:
    if watch_value > pass_value:
        raise ValueError(f"{label} watch threshold must not exceed pass threshold")


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in RESEARCH_SOURCE_CLAIM_SCRAPLING_FRESHNESS_DECAY_STATUSES:
        raise ValueError(
            f"{field_name} must be one of "
            f"{RESEARCH_SOURCE_CLAIM_SCRAPLING_FRESHNESS_DECAY_STATUSES}",
        )
    _reject_unsafe_public_text(field_name, value)


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    _reject_unsafe_public_text(field_name, value)


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _report_digest(report: ResearchSourceClaimScraplingFreshnessDecayReport) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _validate_public_payload(payload)
    _validate_report_payload_schema(payload, require_digest=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) in (int, float):
        raise ValueError("JSON value must not contain raw numeric values")
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    ready = _json_ready(
        asdict(value) if is_dataclass(value) and not isinstance(value, type) else value,
    )
    _validate_public_payload(ready, label=label)


def _validate_public_payload(value: Any, *, label: str = "payload") -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text(label, key)
            _validate_public_payload(item, label=key)
        return
    if type(value) is list:
        for item in value:
            _validate_public_payload(item, label=label)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) in (int, float, Decimal):
        raise ValueError(f"{label} must not expose raw numeric values")


def _validate_report_payload_schema(
    payload: dict[str, Any],
    *,
    require_digest: bool,
) -> None:
    expected_keys = REPORT_PAYLOAD_KEYS if require_digest else REPORT_PAYLOAD_UNSIGNED_KEYS
    _require_payload_keys("payload", payload, expected_keys)
    if require_digest:
        _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    _payload_datetime("generated_at", payload["generated_at"])
    config_version = payload["config_version"]
    _require_public_identifier("config_version", config_version)
    if (
        config_version
        != DEFAULT_RESEARCH_SOURCE_CLAIM_SCRAPLING_FRESHNESS_DECAY_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")

    count_values = {
        field_name: _payload_nonnegative_count(field_name, payload[field_name])
        for field_name in REPORT_COUNT_PAYLOAD_FIELDS
    }
    max_claim_age_seconds = _payload_nonnegative_decimal(
        "max_claim_age_seconds",
        payload["max_claim_age_seconds"],
    )
    average_values = {
        field_name: _payload_probability(field_name, payload[field_name])
        for field_name in REPORT_AVERAGE_PAYLOAD_FIELDS
    }
    status = payload["status"]
    _require_status("status", status)
    reason_codes = _payload_reason_codes("reason_codes", payload["reason_codes"])
    reason_code_counts = tuple(
        _payload_reason_code_count(item)
        for item in _payload_list("reason_code_counts", payload["reason_code_counts"])
    )
    rows = tuple(_payload_row(item) for item in _payload_list("rows", payload["rows"]))
    _require_payload_hard_flags("payload", payload)

    if count_values["input_count"] != count_values["row_count"]:
        raise ValueError("input_count must match row_count")
    if count_values["row_count"] != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if count_values["pass_count"] != _count_decimal(
        sum(1 for row in rows if row.status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if count_values["watch_count"] != _count_decimal(
        sum(1 for row in rows if row.status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if count_values["block_count"] != _count_decimal(
        sum(1 for row in rows if row.status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if (
        count_values["attention_count"]
        != count_values["watch_count"] + count_values["block_count"]
    ):
        raise ValueError("attention_count must match watch and block counts")
    if status != _report_status(rows):
        raise ValueError("status must match row statuses")
    if reason_codes != _report_reason_codes(rows, status):
        raise ValueError("reason_codes must match rows and status")
    if reason_code_counts != _reason_code_counts(rows, reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if max_claim_age_seconds != max((row.claim_age_seconds for row in rows), default=ZERO):
        raise ValueError("max_claim_age_seconds must match rows")

    expected_averages = {
        "average_claim_freshness_score": _average(
            row.claim_freshness_score for row in rows
        ),
        "average_scrapling_confidence_score": _average(
            row.scrapling_confidence_score for row in rows
        ),
        "average_claim_support_ratio": _average(row.claim_support_ratio for row in rows),
        "average_authority_alignment_score": _average(
            row.authority_alignment_score for row in rows
        ),
        "average_contradiction_pressure_score": _average(
            row.contradiction_pressure_score for row in rows
        ),
        "average_freshness_decay_score": _average(
            row.freshness_decay_score for row in rows
        ),
    }
    for field_name, expected_value in expected_averages.items():
        if average_values[field_name] != expected_value:
            raise ValueError(f"{field_name} must match rows")


def _payload_row(payload: Any) -> ResearchSourceClaimScraplingFreshnessDecayRow:
    _require_payload_keys("row", payload, ROW_PAYLOAD_KEYS)
    _require_public_identifier("row_label", payload["row_label"])
    status = payload["status"]
    _require_status("status", status)
    reason_codes = _payload_reason_codes("reason_codes", payload["reason_codes"])
    expected_status_reason = _status_reason(status)
    unexpected_status_reasons = STATUS_REASON_CODES - frozenset((expected_status_reason,))
    if expected_status_reason not in reason_codes or any(
        reason_code in reason_codes for reason_code in unexpected_status_reasons
    ):
        raise ValueError("row reason_codes must match status")
    _require_payload_hard_flags("row", payload)
    return ResearchSourceClaimScraplingFreshnessDecayRow(
        row_label=payload["row_label"],
        claim_age_seconds=_payload_nonnegative_decimal(
            "claim_age_seconds",
            payload["claim_age_seconds"],
        ),
        claim_freshness_score=_payload_probability(
            "claim_freshness_score",
            payload["claim_freshness_score"],
        ),
        scrapling_confidence_score=_payload_probability(
            "scrapling_confidence_score",
            payload["scrapling_confidence_score"],
        ),
        claim_support_ratio=_payload_probability(
            "claim_support_ratio",
            payload["claim_support_ratio"],
        ),
        authority_alignment_score=_payload_probability(
            "authority_alignment_score",
            payload["authority_alignment_score"],
        ),
        contradiction_pressure_score=_payload_probability(
            "contradiction_pressure_score",
            payload["contradiction_pressure_score"],
        ),
        freshness_decay_score=_payload_probability(
            "freshness_decay_score",
            payload["freshness_decay_score"],
        ),
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _payload_reason_code_count(
    payload: Any,
) -> ResearchSourceClaimScraplingFreshnessDecayReasonCodeCount:
    _require_payload_keys("reason_code_count", payload, REASON_CODE_COUNT_PAYLOAD_KEYS)
    _require_reason_code("reason_code", payload["reason_code"])
    _require_payload_hard_flags("reason_code_count", payload)
    return ResearchSourceClaimScraplingFreshnessDecayReasonCodeCount(
        reason_code=payload["reason_code"],
        count=_payload_positive_count("count", payload["count"]),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _require_payload_keys(
    label: str,
    value: Any,
    expected_keys: frozenset[str],
) -> None:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    if frozenset(value) != expected_keys:
        raise ValueError(f"{label} schema keys must match")


def _payload_list(field_name: str, value: Any) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _require_payload_hard_flags(label: str, payload: dict[str, Any]) -> None:
    if payload["paper_only"] is not True:
        raise ValueError(f"{label} paper_only must be True")
    if payload["report_only"] is not True:
        raise ValueError(f"{label} report_only must be True")
    if payload["readonly"] is not True:
        raise ValueError(f"{label} readonly must be True")


def _payload_reason_codes(field_name: str, value: Any) -> tuple[str, ...]:
    reason_codes = tuple(_payload_list(field_name, value))
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    if reason_codes != _normalize_reason_codes(field_name, reason_codes):
        raise ValueError(f"{field_name} must be canonical")
    return reason_codes


def _payload_datetime(field_name: str, value: Any) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC ISO datetime string")
    return normalized


def _payload_positive_count(field_name: str, value: Any) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_positive_count)


def _payload_nonnegative_count(field_name: str, value: Any) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_nonnegative_count)


def _payload_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_nonnegative_decimal)


def _payload_probability(field_name: str, value: Any) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_probability)


def _payload_decimal(
    field_name: str,
    value: Any,
    normalizer: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except (ArithmeticError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = normalizer(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} has unsafe public surface")
