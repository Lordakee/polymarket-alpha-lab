"""Pure public rollup for sanitized research-source retrieval integrity."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_RETRIEVAL_INTEGRITY_ROLLUP_REPORT_CONFIG_VERSION = (
    "research-source-retrieval-integrity-rollup-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
RETRIEVAL_CHANNELS = ("scraping", "web")

REASON_PREFIX = "research_source_retrieval_integrity_rollup_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
RETRIEVAL_FRESHNESS_WATCH_REASON = f"{REASON_PREFIX}retrieval_freshness_watch"
RETRIEVAL_FRESHNESS_BLOCK_REASON = f"{REASON_PREFIX}retrieval_freshness_block"
PARSE_CONFIDENCE_WATCH_REASON = f"{REASON_PREFIX}parse_confidence_watch"
PARSE_CONFIDENCE_BLOCK_REASON = f"{REASON_PREFIX}parse_confidence_block"
FAMILY_QUORUM_WATCH_REASON = f"{REASON_PREFIX}family_quorum_watch"
FAMILY_QUORUM_BLOCK_REASON = f"{REASON_PREFIX}family_quorum_block"
CONTRADICTION_PRESSURE_WATCH_REASON = f"{REASON_PREFIX}contradiction_pressure_watch"
CONTRADICTION_PRESSURE_BLOCK_REASON = f"{REASON_PREFIX}contradiction_pressure_block"
INTEGRITY_SCORE_WATCH_REASON = f"{REASON_PREFIX}integrity_score_watch"
INTEGRITY_SCORE_BLOCK_REASON = f"{REASON_PREFIX}integrity_score_block"

REASON_CODES = (
    NO_INPUTS_REASON,
    PASS_REASON,
    RETRIEVAL_FRESHNESS_WATCH_REASON,
    RETRIEVAL_FRESHNESS_BLOCK_REASON,
    PARSE_CONFIDENCE_WATCH_REASON,
    PARSE_CONFIDENCE_BLOCK_REASON,
    FAMILY_QUORUM_WATCH_REASON,
    FAMILY_QUORUM_BLOCK_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    INTEGRITY_SCORE_WATCH_REASON,
    INTEGRITY_SCORE_BLOCK_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

HARD_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
PUBLIC_DIGEST_FIELD = "public_digest"

UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "candidate_id",
    "candidate_slug",
    "candidate_identifier",
    "market_id",
    "market_slug",
    "market_identifier",
    "slug",
    "question",
    "source_id",
    "source_url",
    "raw_id",
    "raw_url",
    "raw_text",
    "source_text",
    "url",
    "dsn",
    "table_name",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "live_trading",
    "sizing",
    "recommendation",
    "private",
    "secret",
    "buy",
    "sell",
    "position",
)

PUBLIC_DECIMAL_STRING_KEYS = frozenset(
    (
        "average_family_quorum_ratio",
        "average_parse_confidence",
        "average_retrieval_freshness_score",
        "block_count",
        "channel_count",
        "contradiction_pressure",
        "count",
        "family_quorum_count",
        "family_quorum_ratio",
        "input_count",
        "integrity_score",
        "latest_retrieval_age_seconds",
        "max_contradiction_pressure",
        "observation_count",
        "parse_confidence",
        "pass_count",
        "retrieval_freshness_score",
        "row_ratio",
        "watch_count",
    ),
)


class _Missing:
    pass


_MISSING = _Missing()


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_RETRIEVAL_INTEGRITY_ROLLUP_REPORT_CONFIG_VERSION",
    "RETRIEVAL_CHANNELS",
    "STATUSES",
    "ResearchSourceRetrievalIntegrityEvidence",
    "ResearchSourceRetrievalIntegrityRollupConfig",
    "ResearchSourceRetrievalIntegrityRollupReasonCodeCount",
    "ResearchSourceRetrievalIntegrityRollupReport",
    "ResearchSourceRetrievalIntegrityRollupRow",
    "build_research_source_retrieval_integrity_rollup_report",
    "research_source_retrieval_integrity_rollup_report_public_digest",
    "research_source_retrieval_integrity_rollup_report_public_payload",
    "validate_research_source_retrieval_integrity_rollup_report_public_payload",
)


@dataclass(frozen=True)
class ResearchSourceRetrievalIntegrityRollupConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_RETRIEVAL_INTEGRITY_ROLLUP_REPORT_CONFIG_VERSION
    )
    fresh_retrieval_age_seconds: Decimal = Decimal("3600.000000")
    stale_retrieval_age_seconds: Decimal = Decimal("86400.000000")
    minimum_family_quorum_count: Decimal = Decimal("2.000000")
    pass_integrity_score: Decimal = Decimal("0.700000")
    watch_integrity_score: Decimal = Decimal("0.400000")
    watch_freshness_score: Decimal = Decimal("0.500000")
    block_freshness_score: Decimal = Decimal("0.250000")
    watch_parse_confidence: Decimal = Decimal("0.700000")
    block_parse_confidence: Decimal = Decimal("0.400000")
    watch_contradiction_pressure: Decimal = Decimal("0.350000")
    block_contradiction_pressure: Decimal = Decimal("0.650000")
    freshness_weight: Decimal = Decimal("0.300000")
    parse_confidence_weight: Decimal = Decimal("0.300000")
    family_quorum_weight: Decimal = Decimal("0.250000")
    contradiction_pressure_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRetrievalIntegrityRollupConfig:
            raise ValueError(
                "config must be exactly ResearchSourceRetrievalIntegrityRollupConfig",
            )
        _require_public_text("config_version", self.config_version)
        _reject_unsafe_public_text("config_version", self.config_version)
        for field_name in (
            "fresh_retrieval_age_seconds",
            "stale_retrieval_age_seconds",
            "minimum_family_quorum_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_retrieval_age_seconds <= self.fresh_retrieval_age_seconds:
            raise ValueError(
                "stale_retrieval_age_seconds must exceed fresh_retrieval_age_seconds",
            )
        for field_name in (
            "pass_integrity_score",
            "watch_integrity_score",
            "watch_freshness_score",
            "block_freshness_score",
            "watch_parse_confidence",
            "block_parse_confidence",
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
            "freshness_weight",
            "parse_confidence_weight",
            "family_quorum_weight",
            "contradiction_pressure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_integrity_score <= self.watch_integrity_score:
            raise ValueError("pass_integrity_score must exceed watch_integrity_score")
        if self.block_freshness_score > self.watch_freshness_score:
            raise ValueError("block_freshness_score must not exceed watch_freshness_score")
        if self.block_parse_confidence > self.watch_parse_confidence:
            raise ValueError(
                "block_parse_confidence must not exceed watch_parse_confidence",
            )
        if self.block_contradiction_pressure < self.watch_contradiction_pressure:
            raise ValueError(
                "block_contradiction_pressure must not be below "
                "watch_contradiction_pressure",
            )
        weight_sum = _quantize(
            self.freshness_weight
            + self.parse_confidence_weight
            + self.family_quorum_weight
            + self.contradiction_pressure_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "freshness_weight, parse_confidence_weight, family_quorum_weight, "
                "and contradiction_pressure_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceRetrievalIntegrityEvidence:
    retrieval_channel: str
    retrieved_at: datetime
    parse_confidence: Decimal
    family_quorum_count: Decimal
    contradiction_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRetrievalIntegrityEvidence:
            raise ValueError(
                "evidence must be exactly ResearchSourceRetrievalIntegrityEvidence",
            )
        object.__setattr__(
            self,
            "retrieval_channel",
            _require_retrieval_channel("retrieval_channel", self.retrieval_channel),
        )
        object.__setattr__(self, "retrieved_at", _as_utc("retrieved_at", self.retrieved_at))
        object.__setattr__(
            self,
            "parse_confidence",
            _require_ratio_decimal("parse_confidence", self.parse_confidence),
        )
        object.__setattr__(
            self,
            "family_quorum_count",
            _require_nonnegative_decimal("family_quorum_count", self.family_quorum_count),
        )
        object.__setattr__(
            self,
            "contradiction_pressure",
            _require_ratio_decimal(
                "contradiction_pressure",
                self.contradiction_pressure,
            ),
        )
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchSourceRetrievalIntegrityRollupRow:
    retrieval_channel: str
    observation_count: Decimal
    latest_retrieved_at: datetime
    latest_retrieval_age_seconds: Decimal
    retrieval_freshness_score: Decimal
    parse_confidence: Decimal
    family_quorum_count: Decimal
    family_quorum_ratio: Decimal
    contradiction_pressure: Decimal
    integrity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRetrievalIntegrityRollupRow:
            raise ValueError(
                "row must be exactly ResearchSourceRetrievalIntegrityRollupRow",
            )
        object.__setattr__(
            self,
            "retrieval_channel",
            _require_retrieval_channel("retrieval_channel", self.retrieval_channel),
        )
        object.__setattr__(
            self,
            "observation_count",
            _require_positive_decimal("observation_count", self.observation_count),
        )
        object.__setattr__(
            self,
            "latest_retrieved_at",
            _as_utc("latest_retrieved_at", self.latest_retrieved_at),
        )
        object.__setattr__(
            self,
            "latest_retrieval_age_seconds",
            _require_nonnegative_decimal(
                "latest_retrieval_age_seconds",
                self.latest_retrieval_age_seconds,
            ),
        )
        for field_name in (
            "retrieval_freshness_score",
            "parse_confidence",
            "family_quorum_ratio",
            "contradiction_pressure",
            "integrity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "family_quorum_count",
            _require_nonnegative_decimal("family_quorum_count", self.family_quorum_count),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchSourceRetrievalIntegrityRollupReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRetrievalIntegrityRollupReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchSourceRetrievalIntegrityRollupReasonCodeCount",
            )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(self, "count", _require_positive_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceRetrievalIntegrityRollupReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    channel_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_retrieval_freshness_score: Decimal
    average_parse_confidence: Decimal
    average_family_quorum_ratio: Decimal
    max_contradiction_pressure: Decimal
    integrity_score: Decimal
    status: str
    rows: tuple[ResearchSourceRetrievalIntegrityRollupRow, ...]
    reason_code_counts: tuple[ResearchSourceRetrievalIntegrityRollupReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRetrievalIntegrityRollupReport:
            raise ValueError(
                "report must be exactly ResearchSourceRetrievalIntegrityRollupReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        _reject_unsafe_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RETRIEVAL_INTEGRITY_ROLLUP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "channel_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_retrieval_freshness_score",
            "average_parse_confidence",
            "average_family_quorum_ratio",
            "max_contradiction_pressure",
            "integrity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _finalize_public_digest(self)
        _reject_unsafe_public_payload("report", _json_ready(self))


def build_research_source_retrieval_integrity_rollup_report(
    evidence_rows: Iterable[object],
    *,
    config: ResearchSourceRetrievalIntegrityRollupConfig,
    generated_at: datetime,
) -> ResearchSourceRetrievalIntegrityRollupReport:
    if type(config) is not ResearchSourceRetrievalIntegrityRollupConfig:
        raise ValueError(
            "config must be exactly ResearchSourceRetrievalIntegrityRollupConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_evidence_rows(evidence_rows)
    for item in evidence_items:
        if item.retrieved_at > generated_at_utc:
            raise ValueError("retrieved_at must not be after generated_at")

    grouped: dict[str, list[ResearchSourceRetrievalIntegrityEvidence]] = {}
    for item in evidence_items:
        grouped.setdefault(item.retrieval_channel, []).append(item)

    rows = tuple(
        _rollup_row_for_channel(
            retrieval_channel=retrieval_channel,
            evidence_rows=tuple(grouped[retrieval_channel]),
            config=config,
            generated_at=generated_at_utc,
        )
        for retrieval_channel in sorted(grouped)
    )
    reason_codes = _report_reason_codes(rows)

    return ResearchSourceRetrievalIntegrityRollupReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(evidence_items)),
        channel_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, STATUS_PASS)),
        watch_count=_decimal_count(_status_count(rows, STATUS_WATCH)),
        block_count=_decimal_count(_status_count(rows, STATUS_BLOCK)),
        average_retrieval_freshness_score=_average_or_zero(
            tuple(row.retrieval_freshness_score for row in rows),
        ),
        average_parse_confidence=_average_or_zero(
            tuple(row.parse_confidence for row in rows),
        ),
        average_family_quorum_ratio=_average_or_zero(
            tuple(row.family_quorum_ratio for row in rows),
        ),
        max_contradiction_pressure=max(
            (row.contradiction_pressure for row in rows),
            default=ZERO,
        ),
        integrity_score=_average_or_zero(tuple(row.integrity_score for row in rows)),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_source_retrieval_integrity_rollup_report_public_payload(
    report: ResearchSourceRetrievalIntegrityRollupReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceRetrievalIntegrityRollupReport:
        raise ValueError(
            "report must be exactly ResearchSourceRetrievalIntegrityRollupReport",
        )
    _validate_public_digest_for_report(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    validate_research_source_retrieval_integrity_rollup_report_public_payload(payload)
    return payload


def research_source_retrieval_integrity_rollup_report_public_digest(
    value: ResearchSourceRetrievalIntegrityRollupReport | dict[str, Any],
) -> str:
    if type(value) is ResearchSourceRetrievalIntegrityRollupReport:
        return _public_digest_from_report(value)
    if type(value) is dict:
        return _public_digest_from_payload(value)
    raise ValueError("value must be a report or public payload")


def validate_research_source_retrieval_integrity_rollup_report_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _validate_public_payload_values(payload)
    _require_public_payload_flags(payload)
    digest = _payload_required_string(payload, PUBLIC_DIGEST_FIELD)
    _require_sha256_digest(PUBLIC_DIGEST_FIELD, digest)
    if digest != _public_digest_from_payload(payload):
        raise ValueError("public_digest must match public payload")


def _rollup_row_for_channel(
    *,
    retrieval_channel: str,
    evidence_rows: tuple[ResearchSourceRetrievalIntegrityEvidence, ...],
    config: ResearchSourceRetrievalIntegrityRollupConfig,
    generated_at: datetime,
) -> ResearchSourceRetrievalIntegrityRollupRow:
    if not evidence_rows:
        raise ValueError("evidence_rows must be nonempty")
    latest_retrieved_at = max(item.retrieved_at for item in evidence_rows)
    latest_retrieval_age_seconds = _age_seconds(generated_at, latest_retrieved_at)
    retrieval_freshness_score = _retrieval_freshness_score(
        latest_retrieval_age_seconds,
        config=config,
    )
    parse_confidence = _average_or_zero(tuple(item.parse_confidence for item in evidence_rows))
    family_quorum_count = _average_or_zero(
        tuple(item.family_quorum_count for item in evidence_rows),
    )
    family_quorum_ratio = _bounded_ratio(
        family_quorum_count / config.minimum_family_quorum_count,
    )
    contradiction_pressure = max(item.contradiction_pressure for item in evidence_rows)
    integrity_score = _integrity_score(
        retrieval_freshness_score=retrieval_freshness_score,
        parse_confidence=parse_confidence,
        family_quorum_ratio=family_quorum_ratio,
        contradiction_pressure=contradiction_pressure,
        config=config,
    )
    status = _row_status(
        retrieval_freshness_score=retrieval_freshness_score,
        parse_confidence=parse_confidence,
        family_quorum_ratio=family_quorum_ratio,
        contradiction_pressure=contradiction_pressure,
        integrity_score=integrity_score,
        config=config,
    )
    return ResearchSourceRetrievalIntegrityRollupRow(
        retrieval_channel=retrieval_channel,
        observation_count=_decimal_count(len(evidence_rows)),
        latest_retrieved_at=latest_retrieved_at,
        latest_retrieval_age_seconds=latest_retrieval_age_seconds,
        retrieval_freshness_score=retrieval_freshness_score,
        parse_confidence=parse_confidence,
        family_quorum_count=family_quorum_count,
        family_quorum_ratio=family_quorum_ratio,
        contradiction_pressure=contradiction_pressure,
        integrity_score=integrity_score,
        status=status,
        reason_codes=_row_reason_codes(
            retrieval_freshness_score=retrieval_freshness_score,
            parse_confidence=parse_confidence,
            family_quorum_ratio=family_quorum_ratio,
            contradiction_pressure=contradiction_pressure,
            integrity_score=integrity_score,
            status=status,
            config=config,
        ),
    )


def _normalize_evidence_rows(
    evidence_rows: Iterable[object],
) -> tuple[ResearchSourceRetrievalIntegrityEvidence, ...]:
    if isinstance(evidence_rows, (str, bytes)):
        raise ValueError("evidence_rows must be an iterable")
    try:
        values = tuple(evidence_rows)
    except TypeError as exc:
        raise ValueError("evidence_rows must be an iterable") from exc
    return tuple(_coerce_evidence_row(value) for value in values)


def _coerce_evidence_row(value: object) -> ResearchSourceRetrievalIntegrityEvidence:
    if type(value) is ResearchSourceRetrievalIntegrityEvidence:
        _require_hard_flags("evidence", value)
        return value
    _require_hard_flags("evidence", value)
    return ResearchSourceRetrievalIntegrityEvidence(
        retrieval_channel=_field_value(value, "retrieval_channel"),
        retrieved_at=_field_value(value, "retrieved_at"),
        parse_confidence=_field_value(value, "parse_confidence"),
        family_quorum_count=_field_value(value, "family_quorum_count"),
        contradiction_pressure=_field_value(value, "contradiction_pressure"),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _retrieval_freshness_score(
    latest_retrieval_age_seconds: Decimal,
    *,
    config: ResearchSourceRetrievalIntegrityRollupConfig,
) -> Decimal:
    if latest_retrieval_age_seconds <= config.fresh_retrieval_age_seconds:
        return ONE
    if latest_retrieval_age_seconds >= config.stale_retrieval_age_seconds:
        return ZERO
    return _bounded_ratio(ONE - (latest_retrieval_age_seconds / config.stale_retrieval_age_seconds))


def _integrity_score(
    *,
    retrieval_freshness_score: Decimal,
    parse_confidence: Decimal,
    family_quorum_ratio: Decimal,
    contradiction_pressure: Decimal,
    config: ResearchSourceRetrievalIntegrityRollupConfig,
) -> Decimal:
    return _bounded_ratio(
        (retrieval_freshness_score * config.freshness_weight)
        + (parse_confidence * config.parse_confidence_weight)
        + (family_quorum_ratio * config.family_quorum_weight)
        + ((ONE - contradiction_pressure) * config.contradiction_pressure_weight),
    )


def _row_status(
    *,
    retrieval_freshness_score: Decimal,
    parse_confidence: Decimal,
    family_quorum_ratio: Decimal,
    contradiction_pressure: Decimal,
    integrity_score: Decimal,
    config: ResearchSourceRetrievalIntegrityRollupConfig,
) -> str:
    if retrieval_freshness_score <= config.block_freshness_score:
        return STATUS_BLOCK
    if parse_confidence <= config.block_parse_confidence:
        return STATUS_BLOCK
    if family_quorum_ratio == ZERO:
        return STATUS_BLOCK
    if contradiction_pressure >= config.block_contradiction_pressure:
        return STATUS_BLOCK
    if integrity_score < config.watch_integrity_score:
        return STATUS_BLOCK
    if retrieval_freshness_score <= config.watch_freshness_score:
        return STATUS_WATCH
    if parse_confidence <= config.watch_parse_confidence:
        return STATUS_WATCH
    if family_quorum_ratio < ONE:
        return STATUS_WATCH
    if contradiction_pressure >= config.watch_contradiction_pressure:
        return STATUS_WATCH
    if integrity_score < config.pass_integrity_score:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    retrieval_freshness_score: Decimal,
    parse_confidence: Decimal,
    family_quorum_ratio: Decimal,
    contradiction_pressure: Decimal,
    integrity_score: Decimal,
    status: str,
    config: ResearchSourceRetrievalIntegrityRollupConfig,
) -> tuple[str, ...]:
    if status == STATUS_PASS:
        return (PASS_REASON,)

    reason_codes: list[str] = []
    if retrieval_freshness_score <= config.block_freshness_score:
        reason_codes.append(RETRIEVAL_FRESHNESS_BLOCK_REASON)
    elif retrieval_freshness_score <= config.watch_freshness_score:
        reason_codes.append(RETRIEVAL_FRESHNESS_WATCH_REASON)

    if parse_confidence <= config.block_parse_confidence:
        reason_codes.append(PARSE_CONFIDENCE_BLOCK_REASON)
    elif parse_confidence <= config.watch_parse_confidence:
        reason_codes.append(PARSE_CONFIDENCE_WATCH_REASON)

    if family_quorum_ratio == ZERO:
        reason_codes.append(FAMILY_QUORUM_BLOCK_REASON)
    elif family_quorum_ratio < ONE:
        reason_codes.append(FAMILY_QUORUM_WATCH_REASON)

    if contradiction_pressure >= config.block_contradiction_pressure:
        reason_codes.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif contradiction_pressure >= config.watch_contradiction_pressure:
        reason_codes.append(CONTRADICTION_PRESSURE_WATCH_REASON)

    if integrity_score < config.watch_integrity_score:
        reason_codes.append(INTEGRITY_SCORE_BLOCK_REASON)
    elif integrity_score < config.pass_integrity_score:
        reason_codes.append(INTEGRITY_SCORE_WATCH_REASON)

    if not reason_codes:
        reason_codes.append(INTEGRITY_SCORE_WATCH_REASON)
    return tuple(sorted(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchSourceRetrievalIntegrityRollupRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    if all(row.status == STATUS_PASS for row in rows):
        return (PASS_REASON,)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _report_status(rows: tuple[ResearchSourceRetrievalIntegrityRollupRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchSourceRetrievalIntegrityRollupRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceRetrievalIntegrityRollupReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceRetrievalIntegrityRollupReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchSourceRetrievalIntegrityRollupReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            row_ratio=_bounded_ratio(_decimal_count(counts[reason_code]) / row_count),
        )
        for reason_code in sorted(counts)
        if reason_code in reason_codes
    )


def _validate_row_consistency(row: ResearchSourceRetrievalIntegrityRollupRow) -> None:
    if row.integrity_score < ZERO or row.integrity_score > ONE:
        raise ValueError("integrity_score must be between 0 and 1")
    if row.status == STATUS_PASS and row.integrity_score < Decimal("0.700000"):
        raise ValueError("integrity_score must support pass status")
    if row.status == STATUS_WATCH and (
        row.integrity_score < Decimal("0.400000")
        or row.integrity_score >= Decimal("0.700000")
    ):
        raise ValueError("integrity_score must support watch status")
    if row.status == STATUS_BLOCK and row.integrity_score >= Decimal("0.400000"):
        raise ValueError("integrity_score must support block status")
    if row.status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("reason_codes must support pass status")
    if row.status != STATUS_PASS and PASS_REASON in row.reason_codes:
        raise ValueError("reason_codes must not mix pass with non-pass status")


def _validate_report_consistency(
    report: ResearchSourceRetrievalIntegrityRollupReport,
) -> None:
    rows = report.rows
    if report.input_count < report.channel_count:
        raise ValueError("input_count must not be below channel_count")
    if report.channel_count != _decimal_count(len(rows)):
        raise ValueError("channel_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_retrieval_freshness_score != _average_or_zero(
        tuple(row.retrieval_freshness_score for row in rows),
    ):
        raise ValueError("average_retrieval_freshness_score must match rows")
    if report.average_parse_confidence != _average_or_zero(
        tuple(row.parse_confidence for row in rows),
    ):
        raise ValueError("average_parse_confidence must match rows")
    if report.average_family_quorum_ratio != _average_or_zero(
        tuple(row.family_quorum_ratio for row in rows),
    ):
        raise ValueError("average_family_quorum_ratio must match rows")
    if report.max_contradiction_pressure != max(
        (row.contradiction_pressure for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.integrity_score != _average_or_zero(tuple(row.integrity_score for row in rows)):
        raise ValueError("integrity_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _normalize_rows(
    rows: tuple[ResearchSourceRetrievalIntegrityRollupRow, ...],
) -> tuple[ResearchSourceRetrievalIntegrityRollupRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceRetrievalIntegrityRollupRow:
            raise ValueError(
                "rows must contain ResearchSourceRetrievalIntegrityRollupRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.retrieval_channel))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by retrieval_channel")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceRetrievalIntegrityRollupReasonCodeCount, ...],
) -> tuple[ResearchSourceRetrievalIntegrityRollupReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchSourceRetrievalIntegrityRollupReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceRetrievalIntegrityRollupReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _status_count(
    rows: tuple[ResearchSourceRetrievalIntegrityRollupRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _bounded_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_public_text(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if normalized != value:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _require_retrieval_channel(field_name: str, value: str) -> str:
    normalized = _require_public_text(field_name, value)
    if normalized not in RETRIEVAL_CHANNELS:
        raise ValueError(f"{field_name} must be one of scraping/web")
    return normalized


def _require_status(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_reason_code(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} contains an unknown reason code")
    return value


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(sorted({_require_reason_code(field_name, value) for value in values}))
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return normalized


def _require_sha256_digest(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be lowercase hex")
    return value


def _require_decimal_string(field_name: str, value: str) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal strings")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must use Decimal strings") from exc
    normalized = _require_decimal(field_name, parsed)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must use Decimal strings")
    return normalized


def _require_hard_flags(label: str, value: Any) -> None:
    for field_name in HARD_FLAG_FIELDS:
        flag_value = getattr(value, field_name, None)
        if type(flag_value) is not bool:
            raise ValueError(f"{label}.{field_name} must be a bool")
        if flag_value is not True:
            raise ValueError(f"{label}.{field_name} must be true")


def _json_ready(value: Any, *, skip_public_digest: bool = False) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        result: dict[str, Any] = {}
        for field in fields(value):
            if skip_public_digest and field.name == PUBLIC_DIGEST_FIELD:
                continue
            result[field.name] = _json_ready(
                getattr(value, field.name),
                skip_public_digest=skip_public_digest,
            )
        return result
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(_require_decimal("payload Decimal", value), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item, skip_public_digest=skip_public_digest) for item in value]
    if isinstance(value, list):
        return [_json_ready(item, skip_public_digest=skip_public_digest) for item in value]
    if isinstance(value, dict):
        return {
            _json_ready(key, skip_public_digest=skip_public_digest): _json_ready(
                item,
                skip_public_digest=skip_public_digest,
            )
            for key, item in value.items()
        }
    if type(value) in (str, bool):
        return value
    raise ValueError("public payload values must use Decimal strings")


def _public_digest_from_report(
    report: ResearchSourceRetrievalIntegrityRollupReport,
) -> str:
    payload = _json_ready(report, skip_public_digest=True)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _public_digest_from_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != PUBLIC_DIGEST_FIELD
    }
    encoded = json.dumps(payload_without_digest, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _finalize_public_digest(report: ResearchSourceRetrievalIntegrityRollupReport) -> None:
    current = report.public_digest
    expected = _public_digest_from_report(report)
    if current == "":
        object.__setattr__(report, PUBLIC_DIGEST_FIELD, expected)
        return
    _require_sha256_digest(PUBLIC_DIGEST_FIELD, current)
    if current != expected:
        raise ValueError("public_digest must match report fields")


def _validate_public_digest_for_report(
    report: ResearchSourceRetrievalIntegrityRollupReport,
) -> None:
    _require_sha256_digest(PUBLIC_DIGEST_FIELD, report.public_digest)
    if report.public_digest != _public_digest_from_report(report):
        raise ValueError("public_digest must match report fields")


def _validate_public_payload_values(value: Any, *, key_name: str | None = None) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _validate_public_payload_values(item, key_name=key)
        return
    if isinstance(value, list):
        for item in value:
            _validate_public_payload_values(item, key_name=key_name)
        return
    if type(value) in (int, float, Decimal) or type(value) is datetime:
        raise ValueError("public payload numeric values must be Decimal strings")
    if key_name in PUBLIC_DECIMAL_STRING_KEYS:
        _require_decimal_string(key_name, value)
        return
    if key_name == "status":
        _require_status("status", value)
        return
    if value is not None and type(value) not in (str, bool):
        raise ValueError("public payload values must be public JSON values")


def _require_public_payload_flags(value: Any) -> None:
    if isinstance(value, dict):
        present_flags = HARD_FLAG_FIELDS.intersection(value)
        if present_flags:
            if present_flags != HARD_FLAG_FIELDS:
                raise ValueError("public payload hard flags are incomplete")
            for field_name in HARD_FLAG_FIELDS:
                if value[field_name] is not True:
                    raise ValueError(f"{field_name} must be true")
        for item in value.values():
            _require_public_payload_flags(item)
    elif isinstance(value, list):
        for item in value:
            _require_public_payload_flags(item)


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        value = _json_ready(value)
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_public_text("public payload key", key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload text in {field_name}")


def _payload_required_string(payload: dict[str, Any], key: str) -> str:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is not str:
        raise ValueError(f"{key} must be a string")
    return value
