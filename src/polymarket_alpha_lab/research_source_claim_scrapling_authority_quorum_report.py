"""Pure report-only Scrapling authority-quorum reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_CLAIM_SCRAPLING_AUTHORITY_QUORUM_REPORT_CONFIG_VERSION = (
    "research-source-claim-scrapling-authority-quorum-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
PUBLIC_CLAIM_REF_RE = re.compile(r"^claim-[0-9a-f]{16}$")

NO_INPUTS_REASON = "claim_scrapling_authority_quorum_no_inputs"
CLEAR_REASON = "claim_scrapling_authority_quorum_clear"
AUTHORITY_QUORUM_BLOCK_REASON = (
    "claim_scrapling_authority_quorum_insufficient_authority_block"
)
AGREEMENT_BLOCK_REASON = "claim_scrapling_authority_quorum_low_agreement_block"
PARSE_CONFIDENCE_BLOCK_REASON = (
    "claim_scrapling_authority_quorum_parse_confidence_block"
)
FIELD_COMPLETENESS_BLOCK_REASON = (
    "claim_scrapling_authority_quorum_field_completeness_block"
)
STALE_CAPTURE_BLOCK_REASON = "claim_scrapling_authority_quorum_stale_capture_block"
SCORE_BLOCK_REASON = "claim_scrapling_authority_quorum_score_block"
AUTHORITY_QUORUM_WATCH_REASON = (
    "claim_scrapling_authority_quorum_insufficient_authority_watch"
)
AGREEMENT_WATCH_REASON = "claim_scrapling_authority_quorum_low_agreement_watch"
PARSE_CONFIDENCE_WATCH_REASON = (
    "claim_scrapling_authority_quorum_parse_confidence_watch"
)
FIELD_COMPLETENESS_WATCH_REASON = (
    "claim_scrapling_authority_quorum_field_completeness_watch"
)
STALE_CAPTURE_WATCH_REASON = "claim_scrapling_authority_quorum_stale_capture_watch"
SCORE_WATCH_REASON = "claim_scrapling_authority_quorum_score_watch"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    AUTHORITY_QUORUM_BLOCK_REASON,
    AGREEMENT_BLOCK_REASON,
    PARSE_CONFIDENCE_BLOCK_REASON,
    FIELD_COMPLETENESS_BLOCK_REASON,
    STALE_CAPTURE_BLOCK_REASON,
    SCORE_BLOCK_REASON,
    AUTHORITY_QUORUM_WATCH_REASON,
    AGREEMENT_WATCH_REASON,
    PARSE_CONFIDENCE_WATCH_REASON,
    FIELD_COMPLETENESS_WATCH_REASON,
    STALE_CAPTURE_WATCH_REASON,
    SCORE_WATCH_REASON,
    CLEAR_REASON,
)
ROW_REASON_CODES = tuple(
    reason for reason in REASON_CODE_SEQUENCE if reason != NO_INPUTS_REASON
)
REASON_CODE_SET = frozenset(REASON_CODE_SEQUENCE)
PUBLIC_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "attention_count",
        "average_authority_quorum_score",
        "lowest_authority_quorum_ratio",
        "lowest_authority_agreement_ratio",
        "highest_quorum_risk_score",
        "max_collection_age_seconds",
        "status",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
        "derived_validation_digest",
    ),
)
PUBLIC_ROW_PAYLOAD_KEYS = frozenset(
    (
        "public_claim_ref",
        "authority_bucket",
        "collected_at",
        "collection_age_seconds",
        "authority_evidence_count",
        "independent_authority_count",
        "agreeing_authority_count",
        "dissenting_authority_count",
        "authority_quorum_ratio",
        "authority_agreement_ratio",
        "scrapling_parse_confidence_ratio",
        "scrapling_field_completeness_ratio",
        "freshness_score",
        "authority_quorum_score",
        "quorum_risk_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
PUBLIC_REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


def _joined_fragments() -> tuple[str, ...]:
    parts = (
        ("raw", "_", "candi", "date"),
        ("candi", "date", "_", "id"),
        ("mar", "ket", "_", "id"),
        ("mar", "ket", "_", "slug"),
        ("mar", "ket", "_", "question"),
        ("sour", "ce", "_", "url"),
        ("sour", "ce", "_", "text"),
        ("raw", "_", "url"),
        ("raw", "_", "text"),
        ("h", "t", "t", "p", ":", "/", "/"),
        ("h", "t", "t", "p", "s", ":", "/", "/"),
        ("w", "w", "w", "."),
        ("d", "s", "n"),
        ("ta", "ble"),
        ("tok", "en"),
        ("wal", "let"),
        ("private", "_", "key"),
        ("ord", "er"),
        ("tr", "ade"),
        ("li", "ve", "_", "tr", "ading"),
        ("siz", "ing"),
        ("reco", "mmendation"),
    )
    return tuple("".join(fragment_parts) for fragment_parts in parts)


UNSAFE_PUBLIC_FRAGMENTS = _joined_fragments()

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_SCRAPLING_AUTHORITY_QUORUM_REPORT_CONFIG_VERSION",
    "ResearchSourceClaimScraplingAuthorityQuorumConfig",
    "ResearchSourceClaimScraplingAuthorityQuorumInput",
    "ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount",
    "ResearchSourceClaimScraplingAuthorityQuorumReport",
    "ResearchSourceClaimScraplingAuthorityQuorumRow",
    "STATUSES",
    "build_research_source_claim_scrapling_authority_quorum_report",
    "research_source_claim_scrapling_authority_quorum_report_digest",
    "research_source_claim_scrapling_authority_quorum_report_payload",
    "validate_research_source_claim_scrapling_authority_quorum_public_payload",
    "validate_research_source_claim_scrapling_authority_quorum_report_digest",
)


@dataclass(frozen=True)
class ResearchSourceClaimScraplingAuthorityQuorumConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CLAIM_SCRAPLING_AUTHORITY_QUORUM_REPORT_CONFIG_VERSION
    )
    min_authority_quorum_count: Decimal = Decimal("3.000000")
    quorum_pass_ratio: Decimal = Decimal("1.000000")
    quorum_watch_ratio: Decimal = Decimal("0.750000")
    quorum_block_ratio: Decimal = Decimal("0.333333")
    agreement_pass_ratio: Decimal = Decimal("0.800000")
    agreement_watch_ratio: Decimal = Decimal("0.600000")
    agreement_block_ratio: Decimal = Decimal("0.400000")
    parse_confidence_pass_ratio: Decimal = Decimal("0.850000")
    parse_confidence_watch_ratio: Decimal = Decimal("0.650000")
    parse_confidence_block_ratio: Decimal = Decimal("0.450000")
    field_completeness_pass_ratio: Decimal = Decimal("0.900000")
    field_completeness_watch_ratio: Decimal = Decimal("0.600000")
    field_completeness_block_ratio: Decimal = Decimal("0.400000")
    fresh_capture_max_age_seconds: Decimal = Decimal("3600.000000")
    stale_capture_block_age_seconds: Decimal = Decimal("86400.000000")
    min_pass_quorum_score: Decimal = Decimal("0.800000")
    min_watch_quorum_score: Decimal = Decimal("0.500000")
    quorum_weight: Decimal = Decimal("0.350000")
    agreement_weight: Decimal = Decimal("0.250000")
    parse_confidence_weight: Decimal = Decimal("0.200000")
    field_completeness_weight: Decimal = Decimal("0.100000")
    freshness_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimScraplingAuthorityQuorumConfig:
            raise TypeError(
                "ResearchSourceClaimScraplingAuthorityQuorumConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceClaimScraplingAuthorityQuorumConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_SCRAPLING_AUTHORITY_QUORUM_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        object.__setattr__(
            self,
            "min_authority_quorum_count",
            _require_positive_whole_decimal(
                "min_authority_quorum_count",
                self.min_authority_quorum_count,
            ),
        )
        for field_name in (
            "quorum_pass_ratio",
            "quorum_watch_ratio",
            "quorum_block_ratio",
            "agreement_pass_ratio",
            "agreement_watch_ratio",
            "agreement_block_ratio",
            "parse_confidence_pass_ratio",
            "parse_confidence_watch_ratio",
            "parse_confidence_block_ratio",
            "field_completeness_pass_ratio",
            "field_completeness_watch_ratio",
            "field_completeness_block_ratio",
            "min_pass_quorum_score",
            "min_watch_quorum_score",
            "quorum_weight",
            "agreement_weight",
            "parse_confidence_weight",
            "field_completeness_weight",
            "freshness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fresh_capture_max_age_seconds",
            "stale_capture_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_capture_max_age_seconds >= self.stale_capture_block_age_seconds:
            raise ValueError(
                "fresh_capture_max_age_seconds must be below "
                "stale_capture_block_age_seconds",
            )
        _require_descending(
            "quorum thresholds",
            self.quorum_pass_ratio,
            self.quorum_watch_ratio,
            self.quorum_block_ratio,
        )
        _require_descending(
            "agreement thresholds",
            self.agreement_pass_ratio,
            self.agreement_watch_ratio,
            self.agreement_block_ratio,
        )
        _require_descending(
            "parse confidence thresholds",
            self.parse_confidence_pass_ratio,
            self.parse_confidence_watch_ratio,
            self.parse_confidence_block_ratio,
        )
        _require_descending(
            "field completeness thresholds",
            self.field_completeness_pass_ratio,
            self.field_completeness_watch_ratio,
            self.field_completeness_block_ratio,
        )
        if self.min_watch_quorum_score > self.min_pass_quorum_score:
            raise ValueError("score watch threshold must not exceed pass threshold")
        weight_sum = _quantize(
            self.quorum_weight
            + self.agreement_weight
            + self.parse_confidence_weight
            + self.field_completeness_weight
            + self.freshness_weight,
        )
        if weight_sum != ONE:
            raise ValueError("quorum score weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchSourceClaimScraplingAuthorityQuorumInput:
    private_claim_ref: str
    authority_bucket: str
    collected_at: datetime
    authority_evidence_count: Decimal
    independent_authority_count: Decimal
    agreeing_authority_count: Decimal
    dissenting_authority_count: Decimal
    scrapling_parse_confidence_ratio: Decimal
    scrapling_field_completeness_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimScraplingAuthorityQuorumInput:
            raise TypeError(
                "ResearchSourceClaimScraplingAuthorityQuorumInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceClaimScraplingAuthorityQuorumInput,
            "input",
        )
        _require_private_ref("private_claim_ref", self.private_claim_ref)
        object.__setattr__(
            self,
            "authority_bucket",
            _require_public_identifier("authority_bucket", self.authority_bucket),
        )
        object.__setattr__(self, "collected_at", _as_utc("collected_at", self.collected_at))
        for field_name in (
            "authority_evidence_count",
            "independent_authority_count",
            "agreeing_authority_count",
            "dissenting_authority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "scrapling_parse_confidence_ratio",
            "scrapling_field_completeness_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_authority_count > self.authority_evidence_count:
            raise ValueError(
                "independent_authority_count must not exceed authority_evidence_count",
            )
        if (
            self.agreeing_authority_count + self.dissenting_authority_count
            > self.authority_evidence_count
        ):
            raise ValueError(
                "agreeing_authority_count and dissenting_authority_count "
                "must not exceed authority_evidence_count",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceClaimScraplingAuthorityQuorumRow:
    public_claim_ref: str
    authority_bucket: str
    collected_at: datetime
    collection_age_seconds: Decimal
    authority_evidence_count: Decimal
    independent_authority_count: Decimal
    agreeing_authority_count: Decimal
    dissenting_authority_count: Decimal
    authority_quorum_ratio: Decimal
    authority_agreement_ratio: Decimal
    scrapling_parse_confidence_ratio: Decimal
    scrapling_field_completeness_ratio: Decimal
    freshness_score: Decimal
    authority_quorum_score: Decimal
    quorum_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimScraplingAuthorityQuorumRow:
            raise TypeError(
                "ResearchSourceClaimScraplingAuthorityQuorumRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimScraplingAuthorityQuorumRow, "row")
        if type(self.public_claim_ref) is not str or not PUBLIC_CLAIM_REF_RE.fullmatch(
            self.public_claim_ref,
        ):
            raise ValueError("public_claim_ref must be a redacted claim digest ref")
        object.__setattr__(
            self,
            "authority_bucket",
            _require_public_identifier("authority_bucket", self.authority_bucket),
        )
        object.__setattr__(self, "collected_at", _as_utc("collected_at", self.collected_at))
        for field_name in (
            "collection_age_seconds",
            "authority_evidence_count",
            "independent_authority_count",
            "agreeing_authority_count",
            "dissenting_authority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_quorum_ratio",
            "authority_agreement_ratio",
            "scrapling_parse_confidence_ratio",
            "scrapling_field_completeness_ratio",
            "freshness_score",
            "authority_quorum_score",
            "quorum_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if _quantize(self.authority_quorum_score + self.quorum_risk_score) != ONE:
            raise ValueError("authority_quorum_score and quorum_risk_score must sum to 1")
        if self.status == "pass" and self.reason_codes != (CLEAR_REASON,):
            raise ValueError("pass rows must carry only the clear reason")
        if self.status != "pass" and self.reason_codes == (CLEAR_REASON,):
            raise ValueError("attention rows must carry watch or block reasons")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount:
            raise TypeError(
                "ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchSourceClaimScraplingAuthorityQuorumReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    average_authority_quorum_score: Decimal
    lowest_authority_quorum_ratio: Decimal
    lowest_authority_agreement_ratio: Decimal
    highest_quorum_risk_score: Decimal
    max_collection_age_seconds: Decimal
    status: str
    rows: tuple[ResearchSourceClaimScraplingAuthorityQuorumRow, ...]
    reason_code_counts: tuple[
        ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimScraplingAuthorityQuorumReport:
            raise TypeError(
                "ResearchSourceClaimScraplingAuthorityQuorumReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimScraplingAuthorityQuorumReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "attention_count",
            "max_collection_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_authority_quorum_score",
            "lowest_authority_quorum_ratio",
            "lowest_authority_agreement_ratio",
            "highest_quorum_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REASON_CODE_SEQUENCE,
            ),
        )
        if type(self.derived_validation_digest) is not str:
            raise ValueError("derived_validation_digest must be a string")
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        unsigned_payload = _public_payload_from_report(self, include_digest=False)
        _reject_unsafe_public_payload(unsigned_payload)
        expected_digest = _digest_unsigned_payload(unsigned_payload)
        if self.derived_validation_digest:
            if not DIGEST_RE.fullmatch(self.derived_validation_digest):
                raise ValueError("derived_validation_digest must be a sha256 hex digest")
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_source_claim_scrapling_authority_quorum_report_payload(self)


def build_research_source_claim_scrapling_authority_quorum_report(
    inputs: Iterable[object],
    *,
    config: ResearchSourceClaimScraplingAuthorityQuorumConfig,
    generated_at: datetime,
) -> ResearchSourceClaimScraplingAuthorityQuorumReport:
    if type(config) is not ResearchSourceClaimScraplingAuthorityQuorumConfig:
        raise ValueError(
            "config must be a ResearchSourceClaimScraplingAuthorityQuorumConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _score_input(item, config=config, generated_at=generated_at_utc)
                for item in normalized_inputs
            ),
            key=lambda row: (
                STATUS_RANK[row.status],
                row.public_claim_ref,
                row.authority_bucket,
            ),
        ),
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchSourceClaimScraplingAuthorityQuorumReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(normalized_inputs)),
        row_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        attention_count=_decimal_count(
            _status_count(rows, "watch") + _status_count(rows, "block"),
        ),
        average_authority_quorum_score=_average(
            tuple(row.authority_quorum_score for row in rows),
        ),
        lowest_authority_quorum_ratio=_minimum(
            tuple(row.authority_quorum_ratio for row in rows),
        ),
        lowest_authority_agreement_ratio=_minimum(
            tuple(row.authority_agreement_ratio for row in rows),
        ),
        highest_quorum_risk_score=_maximum(
            tuple(row.quorum_risk_score for row in rows),
        ),
        max_collection_age_seconds=_maximum(
            tuple(row.collection_age_seconds for row in rows),
        ),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_source_claim_scrapling_authority_quorum_report_payload(
    report: ResearchSourceClaimScraplingAuthorityQuorumReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourceClaimScraplingAuthorityQuorumReport:
        raise ValueError(
            "report must be a ResearchSourceClaimScraplingAuthorityQuorumReport",
        )
    payload = _public_payload_from_report(report, include_digest=True)
    _reject_unsafe_public_payload(payload)
    validate_research_source_claim_scrapling_authority_quorum_public_payload(payload)
    return payload


def research_source_claim_scrapling_authority_quorum_report_digest(
    report: ResearchSourceClaimScraplingAuthorityQuorumReport,
) -> str:
    if type(report) is not ResearchSourceClaimScraplingAuthorityQuorumReport:
        raise ValueError(
            "report must be a ResearchSourceClaimScraplingAuthorityQuorumReport",
        )
    return _digest_unsigned_payload(_public_payload_from_report(report, include_digest=False))


def validate_research_source_claim_scrapling_authority_quorum_report_digest(
    report: ResearchSourceClaimScraplingAuthorityQuorumReport,
) -> bool:
    expected = research_source_claim_scrapling_authority_quorum_report_digest(report)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match report payload")
    return True


def validate_research_source_claim_scrapling_authority_quorum_public_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(payload)
    _reject_raw_public_numbers(payload)
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str or not DIGEST_RE.fullmatch(digest):
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    _require_public_payload_keys(
        "payload",
        payload,
        PUBLIC_REPORT_PAYLOAD_KEYS,
    )
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    if digest != _digest_unsigned_payload(unsigned):
        raise ValueError("derived_validation_digest does not match public payload")
    _report_from_public_payload(payload)
    return True


def _report_from_public_payload(
    payload: dict[object, object],
) -> ResearchSourceClaimScraplingAuthorityQuorumReport:
    rows_value = _require_public_list("payload rows", payload["rows"])
    reason_counts_value = _require_public_list(
        "payload reason_code_counts",
        payload["reason_code_counts"],
    )
    rows = tuple(_row_from_public_payload(row) for row in rows_value)
    row_sort_keys = tuple(
        (STATUS_RANK[row.status], row.public_claim_ref, row.authority_bucket)
        for row in rows
    )
    if row_sort_keys != tuple(sorted(row_sort_keys)):
        raise ValueError("rows must be in canonical order")
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(item) for item in reason_counts_value
    )
    reason_count_codes = tuple(item.reason_code for item in reason_code_counts)
    if len(frozenset(reason_count_codes)) != len(reason_count_codes):
        raise ValueError("reason_code_counts must not contain duplicates")
    reason_rank = {reason: index for index, reason in enumerate(REASON_CODE_SEQUENCE)}
    if reason_count_codes != tuple(
        sorted(reason_count_codes, key=lambda reason: reason_rank[reason]),
    ):
        raise ValueError("reason_code_counts must be in canonical order")
    return ResearchSourceClaimScraplingAuthorityQuorumReport(
        generated_at=_require_public_datetime_string(
            "generated_at",
            payload["generated_at"],
        ),
        config_version=_require_public_identifier(
            "config_version",
            payload["config_version"],
        ),
        input_count=_require_public_nonnegative_whole_decimal_string(
            "input_count",
            payload["input_count"],
        ),
        row_count=_require_public_nonnegative_whole_decimal_string(
            "row_count",
            payload["row_count"],
        ),
        pass_count=_require_public_nonnegative_whole_decimal_string(
            "pass_count",
            payload["pass_count"],
        ),
        watch_count=_require_public_nonnegative_whole_decimal_string(
            "watch_count",
            payload["watch_count"],
        ),
        block_count=_require_public_nonnegative_whole_decimal_string(
            "block_count",
            payload["block_count"],
        ),
        attention_count=_require_public_nonnegative_whole_decimal_string(
            "attention_count",
            payload["attention_count"],
        ),
        average_authority_quorum_score=_require_public_probability_decimal_string(
            "average_authority_quorum_score",
            payload["average_authority_quorum_score"],
        ),
        lowest_authority_quorum_ratio=_require_public_probability_decimal_string(
            "lowest_authority_quorum_ratio",
            payload["lowest_authority_quorum_ratio"],
        ),
        lowest_authority_agreement_ratio=_require_public_probability_decimal_string(
            "lowest_authority_agreement_ratio",
            payload["lowest_authority_agreement_ratio"],
        ),
        highest_quorum_risk_score=_require_public_probability_decimal_string(
            "highest_quorum_risk_score",
            payload["highest_quorum_risk_score"],
        ),
        max_collection_age_seconds=_require_public_nonnegative_whole_decimal_string(
            "max_collection_age_seconds",
            payload["max_collection_age_seconds"],
        ),
        status=_require_public_member("status", payload["status"], STATUSES),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_require_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            REASON_CODE_SEQUENCE,
        ),
        derived_validation_digest=_require_public_digest_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_require_public_true("payload paper_only", payload["paper_only"]),
        report_only=_require_public_true("payload report_only", payload["report_only"]),
        readonly=_require_public_true("payload readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    value: object,
) -> ResearchSourceClaimScraplingAuthorityQuorumRow:
    _require_public_payload_keys("row schema", value, PUBLIC_ROW_PAYLOAD_KEYS)
    if type(value) is not dict:
        raise ValueError("row schema must be a dict")
    return ResearchSourceClaimScraplingAuthorityQuorumRow(
        public_claim_ref=_require_public_claim_ref_string(
            "public_claim_ref",
            value["public_claim_ref"],
        ),
        authority_bucket=_require_public_identifier(
            "authority_bucket",
            value["authority_bucket"],
        ),
        collected_at=_require_public_datetime_string(
            "collected_at",
            value["collected_at"],
        ),
        collection_age_seconds=_require_public_nonnegative_whole_decimal_string(
            "collection_age_seconds",
            value["collection_age_seconds"],
        ),
        authority_evidence_count=_require_public_nonnegative_whole_decimal_string(
            "authority_evidence_count",
            value["authority_evidence_count"],
        ),
        independent_authority_count=_require_public_nonnegative_whole_decimal_string(
            "independent_authority_count",
            value["independent_authority_count"],
        ),
        agreeing_authority_count=_require_public_nonnegative_whole_decimal_string(
            "agreeing_authority_count",
            value["agreeing_authority_count"],
        ),
        dissenting_authority_count=_require_public_nonnegative_whole_decimal_string(
            "dissenting_authority_count",
            value["dissenting_authority_count"],
        ),
        authority_quorum_ratio=_require_public_probability_decimal_string(
            "authority_quorum_ratio",
            value["authority_quorum_ratio"],
        ),
        authority_agreement_ratio=_require_public_probability_decimal_string(
            "authority_agreement_ratio",
            value["authority_agreement_ratio"],
        ),
        scrapling_parse_confidence_ratio=_require_public_probability_decimal_string(
            "scrapling_parse_confidence_ratio",
            value["scrapling_parse_confidence_ratio"],
        ),
        scrapling_field_completeness_ratio=_require_public_probability_decimal_string(
            "scrapling_field_completeness_ratio",
            value["scrapling_field_completeness_ratio"],
        ),
        freshness_score=_require_public_probability_decimal_string(
            "freshness_score",
            value["freshness_score"],
        ),
        authority_quorum_score=_require_public_probability_decimal_string(
            "authority_quorum_score",
            value["authority_quorum_score"],
        ),
        quorum_risk_score=_require_public_probability_decimal_string(
            "quorum_risk_score",
            value["quorum_risk_score"],
        ),
        status=_require_public_member("status", value["status"], STATUSES),
        reason_codes=_require_public_reason_codes(
            "reason_codes",
            value["reason_codes"],
            ROW_REASON_CODES,
        ),
        paper_only=_require_public_true("row paper_only", value["paper_only"]),
        report_only=_require_public_true("row report_only", value["report_only"]),
        readonly=_require_public_true("row readonly", value["readonly"]),
    )


def _reason_code_count_from_public_payload(
    value: object,
) -> ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount:
    _require_public_payload_keys(
        "reason_code_count schema",
        value,
        PUBLIC_REASON_CODE_COUNT_PAYLOAD_KEYS,
    )
    if type(value) is not dict:
        raise ValueError("reason_code_count schema must be a dict")
    return ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount(
        reason_code=_require_public_member(
            "reason_code",
            value["reason_code"],
            REASON_CODE_SEQUENCE,
        ),
        count=_require_public_positive_whole_decimal_string(
            "count",
            value["count"],
        ),
        paper_only=_require_public_true(
            "reason_code_count paper_only",
            value["paper_only"],
        ),
        report_only=_require_public_true(
            "reason_code_count report_only",
            value["report_only"],
        ),
        readonly=_require_public_true("reason_code_count readonly", value["readonly"]),
    )


def _score_input(
    item: ResearchSourceClaimScraplingAuthorityQuorumInput,
    *,
    config: ResearchSourceClaimScraplingAuthorityQuorumConfig,
    generated_at: datetime,
) -> ResearchSourceClaimScraplingAuthorityQuorumRow:
    collection_age_seconds = _datetime_delta_seconds(generated_at, item.collected_at)
    authority_quorum_ratio = _bounded_ratio(
        item.independent_authority_count,
        config.min_authority_quorum_count,
    )
    authority_agreement_ratio = _bounded_ratio(
        item.agreeing_authority_count,
        item.agreeing_authority_count + item.dissenting_authority_count,
    )
    freshness_score = _freshness_score(collection_age_seconds, config)
    authority_quorum_score = _quantize(
        authority_quorum_ratio * config.quorum_weight
        + authority_agreement_ratio * config.agreement_weight
        + item.scrapling_parse_confidence_ratio * config.parse_confidence_weight
        + item.scrapling_field_completeness_ratio * config.field_completeness_weight
        + freshness_score * config.freshness_weight,
    )
    quorum_risk_score = _quantize(ONE - authority_quorum_score)
    reason_codes = _row_reason_codes(
        authority_quorum_ratio=authority_quorum_ratio,
        authority_agreement_ratio=authority_agreement_ratio,
        parse_confidence_ratio=item.scrapling_parse_confidence_ratio,
        field_completeness_ratio=item.scrapling_field_completeness_ratio,
        collection_age_seconds=collection_age_seconds,
        authority_quorum_score=authority_quorum_score,
        config=config,
    )
    return ResearchSourceClaimScraplingAuthorityQuorumRow(
        public_claim_ref=_public_claim_ref(item.private_claim_ref),
        authority_bucket=item.authority_bucket,
        collected_at=item.collected_at,
        collection_age_seconds=collection_age_seconds,
        authority_evidence_count=item.authority_evidence_count,
        independent_authority_count=item.independent_authority_count,
        agreeing_authority_count=item.agreeing_authority_count,
        dissenting_authority_count=item.dissenting_authority_count,
        authority_quorum_ratio=authority_quorum_ratio,
        authority_agreement_ratio=authority_agreement_ratio,
        scrapling_parse_confidence_ratio=item.scrapling_parse_confidence_ratio,
        scrapling_field_completeness_ratio=item.scrapling_field_completeness_ratio,
        freshness_score=freshness_score,
        authority_quorum_score=authority_quorum_score,
        quorum_risk_score=quorum_risk_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    authority_quorum_ratio: Decimal,
    authority_agreement_ratio: Decimal,
    parse_confidence_ratio: Decimal,
    field_completeness_ratio: Decimal,
    collection_age_seconds: Decimal,
    authority_quorum_score: Decimal,
    config: ResearchSourceClaimScraplingAuthorityQuorumConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_threshold_reason(
        reasons,
        value=authority_quorum_ratio,
        block_threshold=config.quorum_block_ratio,
        pass_threshold=config.quorum_pass_ratio,
        block_reason=AUTHORITY_QUORUM_BLOCK_REASON,
        watch_reason=AUTHORITY_QUORUM_WATCH_REASON,
    )
    _append_threshold_reason(
        reasons,
        value=authority_agreement_ratio,
        block_threshold=config.agreement_block_ratio,
        pass_threshold=config.agreement_pass_ratio,
        block_reason=AGREEMENT_BLOCK_REASON,
        watch_reason=AGREEMENT_WATCH_REASON,
    )
    _append_threshold_reason(
        reasons,
        value=parse_confidence_ratio,
        block_threshold=config.parse_confidence_block_ratio,
        pass_threshold=config.parse_confidence_pass_ratio,
        block_reason=PARSE_CONFIDENCE_BLOCK_REASON,
        watch_reason=PARSE_CONFIDENCE_WATCH_REASON,
    )
    _append_threshold_reason(
        reasons,
        value=field_completeness_ratio,
        block_threshold=config.field_completeness_block_ratio,
        pass_threshold=config.field_completeness_pass_ratio,
        block_reason=FIELD_COMPLETENESS_BLOCK_REASON,
        watch_reason=FIELD_COMPLETENESS_WATCH_REASON,
    )
    if collection_age_seconds >= config.stale_capture_block_age_seconds:
        reasons.append(STALE_CAPTURE_BLOCK_REASON)
    elif collection_age_seconds > config.fresh_capture_max_age_seconds:
        reasons.append(STALE_CAPTURE_WATCH_REASON)
    _append_threshold_reason(
        reasons,
        value=authority_quorum_score,
        block_threshold=config.min_watch_quorum_score,
        pass_threshold=config.min_pass_quorum_score,
        block_reason=SCORE_BLOCK_REASON,
        watch_reason=SCORE_WATCH_REASON,
    )
    if not reasons:
        return (CLEAR_REASON,)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in reasons)


def _append_threshold_reason(
    reasons: list[str],
    *,
    value: Decimal,
    block_threshold: Decimal,
    pass_threshold: Decimal,
    block_reason: str,
    watch_reason: str,
) -> None:
    if value < block_threshold:
        reasons.append(block_reason)
    elif value < pass_threshold:
        reasons.append(watch_reason)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _public_claim_ref(private_claim_ref: str) -> str:
    return f"claim-{sha256(private_claim_ref.encode()).hexdigest()[:16]}"


def _public_payload_from_report(
    report: ResearchSourceClaimScraplingAuthorityQuorumReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "generated_at": _json_ready(report.generated_at),
        "config_version": report.config_version,
        "input_count": _json_ready(report.input_count),
        "row_count": _json_ready(report.row_count),
        "pass_count": _json_ready(report.pass_count),
        "watch_count": _json_ready(report.watch_count),
        "block_count": _json_ready(report.block_count),
        "attention_count": _json_ready(report.attention_count),
        "average_authority_quorum_score": _json_ready(
            report.average_authority_quorum_score,
        ),
        "lowest_authority_quorum_ratio": _json_ready(
            report.lowest_authority_quorum_ratio,
        ),
        "lowest_authority_agreement_ratio": _json_ready(
            report.lowest_authority_agreement_ratio,
        ),
        "highest_quorum_risk_score": _json_ready(report.highest_quorum_risk_score),
        "max_collection_age_seconds": _json_ready(report.max_collection_age_seconds),
        "status": report.status,
        "rows": [_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            _reason_count_payload(item) for item in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(row: ResearchSourceClaimScraplingAuthorityQuorumRow) -> dict[str, object]:
    return {
        "public_claim_ref": row.public_claim_ref,
        "authority_bucket": row.authority_bucket,
        "collected_at": _json_ready(row.collected_at),
        "collection_age_seconds": _json_ready(row.collection_age_seconds),
        "authority_evidence_count": _json_ready(row.authority_evidence_count),
        "independent_authority_count": _json_ready(row.independent_authority_count),
        "agreeing_authority_count": _json_ready(row.agreeing_authority_count),
        "dissenting_authority_count": _json_ready(row.dissenting_authority_count),
        "authority_quorum_ratio": _json_ready(row.authority_quorum_ratio),
        "authority_agreement_ratio": _json_ready(row.authority_agreement_ratio),
        "scrapling_parse_confidence_ratio": _json_ready(
            row.scrapling_parse_confidence_ratio,
        ),
        "scrapling_field_completeness_ratio": _json_ready(
            row.scrapling_field_completeness_ratio,
        ),
        "freshness_score": _json_ready(row.freshness_score),
        "authority_quorum_score": _json_ready(row.authority_quorum_score),
        "quorum_risk_score": _json_ready(row.quorum_risk_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_count_payload(
    item: ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount,
) -> dict[str, object]:
    return {
        "reason_code": item.reason_code,
        "count": _json_ready(item.count),
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _digest_unsigned_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {
            str(_json_ready(key)): _json_ready(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {value!r}")


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchSourceClaimScraplingAuthorityQuorumInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable of quorum inputs")
    normalized: list[ResearchSourceClaimScraplingAuthorityQuorumInput] = []
    for item in inputs:
        if type(item) is not ResearchSourceClaimScraplingAuthorityQuorumInput:
            raise ValueError(
                "inputs must contain ResearchSourceClaimScraplingAuthorityQuorumInput",
            )
        _require_hard_flags("input", item)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: Iterable[object],
) -> tuple[ResearchSourceClaimScraplingAuthorityQuorumRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable of quorum rows")
    normalized: list[ResearchSourceClaimScraplingAuthorityQuorumRow] = []
    for row in rows:
        if type(row) is not ResearchSourceClaimScraplingAuthorityQuorumRow:
            raise ValueError(
                "rows must contain ResearchSourceClaimScraplingAuthorityQuorumRow",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                STATUS_RANK[row.status],
                row.public_claim_ref,
                row.authority_bucket,
            ),
        ),
    )


def _normalize_reason_code_counts(
    counts: Iterable[object],
) -> tuple[ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized: list[ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount] = []
    for item in counts:
        if type(item) is not ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        normalized.append(item)
    rank = {reason: index for index, reason in enumerate(REASON_CODE_SEQUENCE)}
    return tuple(sorted(normalized, key=lambda item: rank[item.reason_code]))


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    allowed_set = frozenset(allowed)
    for reason in reason_codes:
        if type(reason) is not str or reason not in allowed_set:
            raise ValueError(f"{field_name} contains an unsupported reason code")
    rank = {reason: index for index, reason in enumerate(REASON_CODE_SEQUENCE)}
    return tuple(sorted(reason_codes, key=lambda reason: rank[reason]))


def _summary_reason_codes(
    rows: tuple[ResearchSourceClaimScraplingAuthorityQuorumRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    present = {reason for row in rows for reason in row.reason_codes}
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in present)


def _reason_code_counts(
    rows: tuple[ResearchSourceClaimScraplingAuthorityQuorumRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
            ),
        )
    counts = Counter(reason for row in rows for reason in row.reason_codes)
    return tuple(
        ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount(
            reason_code=reason,
            count=_decimal_count(counts[reason]),
        )
        for reason in reason_codes
        if counts[reason] > 0
    )


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if NO_INPUTS_REASON in reason_codes:
        return "block"
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _validate_report_consistency(
    report: ResearchSourceClaimScraplingAuthorityQuorumReport,
) -> None:
    rows = report.rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must equal row count for report rows")
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must equal report rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count does not match rows")
    if report.attention_count != _quantize(report.watch_count + report.block_count):
        raise ValueError("attention_count must equal watch_count plus block_count")
    if report.average_authority_quorum_score != _average(
        tuple(row.authority_quorum_score for row in rows),
    ):
        raise ValueError("average_authority_quorum_score does not match rows")
    if report.lowest_authority_quorum_ratio != _minimum(
        tuple(row.authority_quorum_ratio for row in rows),
    ):
        raise ValueError("lowest_authority_quorum_ratio does not match rows")
    if report.lowest_authority_agreement_ratio != _minimum(
        tuple(row.authority_agreement_ratio for row in rows),
    ):
        raise ValueError("lowest_authority_agreement_ratio does not match rows")
    if report.highest_quorum_risk_score != _maximum(
        tuple(row.quorum_risk_score for row in rows),
    ):
        raise ValueError("highest_quorum_risk_score does not match rows")
    if report.max_collection_age_seconds != _maximum(
        tuple(row.collection_age_seconds for row in rows),
    ):
        raise ValueError("max_collection_age_seconds does not match rows")
    expected_reasons = _summary_reason_codes(rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes do not match rows")
    if report.reason_code_counts != _reason_code_counts(rows, expected_reasons):
        raise ValueError("reason_code_counts do not match rows")
    if report.status != _summary_status(expected_reasons):
        raise ValueError("status does not match reason codes")


def _status_count(
    rows: tuple[ResearchSourceClaimScraplingAuthorityQuorumRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _decimal_count(len(values)))


def _minimum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _maximum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    ratio = _quantize(numerator / denominator)
    if ratio < ZERO:
        return ZERO
    if ratio > ONE:
        return ONE
    return ratio


def _freshness_score(
    age_seconds: Decimal,
    config: ResearchSourceClaimScraplingAuthorityQuorumConfig,
) -> Decimal:
    if age_seconds <= config.fresh_capture_max_age_seconds:
        return ONE
    if age_seconds >= config.stale_capture_block_age_seconds:
        return ZERO
    stale_window = _quantize(
        config.stale_capture_block_age_seconds - config.fresh_capture_max_age_seconds,
    )
    remaining = _quantize(config.stale_capture_block_age_seconds - age_seconds)
    return _bounded_ratio(remaining, stale_window)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.total_seconds() < 0:
        raise ValueError("collected_at must not be after generated_at")
    whole_seconds = Decimal(delta.days) * SECONDS_PER_DAY + Decimal(delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(whole_seconds + fractional_seconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or len(value) > 512 or any(ord(char) < 32 for char in value):
        raise ValueError(f"{field_name} must be a non-empty private reference")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_payload({field_name: value})
    return value


def _require_public_payload_keys(
    label: str,
    value: object,
    expected_keys: frozenset[str],
) -> None:
    schema_label = label if label.endswith("schema") else f"{label} schema"
    if type(value) is not dict:
        raise ValueError(f"{schema_label} must be a dict")
    if frozenset(value) != expected_keys:
        raise ValueError(f"{schema_label} keys must match expected public schema")


def _require_public_list(field_name: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _require_public_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _require_public_member(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_public_digest_string(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_public_claim_ref_string(field_name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_CLAIM_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a redacted claim digest ref")
    return value


def _require_public_datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)


def _require_public_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    normalized = _require_decimal(field_name, parsed)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_public_nonnegative_whole_decimal_string(
    field_name: str,
    value: object,
) -> Decimal:
    normalized = _require_public_decimal_string(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_public_positive_whole_decimal_string(
    field_name: str,
    value: object,
) -> Decimal:
    normalized = _require_public_nonnegative_whole_decimal_string(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_public_probability_decimal_string(
    field_name: str,
    value: object,
) -> Decimal:
    normalized = _require_public_decimal_string(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_public_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list of reason codes")
    normalized = _normalize_reason_codes(field_name, tuple(value), allowed)
    if tuple(value) != normalized:
        raise ValueError(f"{field_name} must be in canonical order")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be an exact {expected_type.__name__}")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name, None)
        if type(flag) is not bool or flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_descending(
    label: str,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if pass_threshold < watch_threshold or watch_threshold < block_threshold:
        raise ValueError(f"{label} must be pass >= watch >= block")


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _reject_raw_public_numbers(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numerics must be rendered as strings")
    if type(value) is dict:
        for item in value.values():
            _reject_raw_public_numbers(item)
    elif type(value) is list:
        for item in value:
            _reject_raw_public_numbers(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_string(key)
            _reject_unsafe_public_payload(item)
        return
    if type(value) is list or type(value) is tuple:
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(value)
        return
    if type(value) in (bool, Decimal, datetime) or value is None:
        return
    raise ValueError(f"unsupported public payload value: {value!r}")


def _reject_unsafe_public_string(value: str) -> None:
    normalized = value.casefold()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("public payload contains unsafe private surface")
