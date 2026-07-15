"""Pure report-only research claim resolution authority decay scorecard."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DEFAULT_CONFIG_VERSION = "rscrad-scorecard-v0"

STATUSES = ("pass", "watch", "block")
ISSUER_KINDS = ("official", "archive", "independent")

PASS_REASON = "scorecard_pass"
NO_EVIDENCE_REASON = "no_evidence"
AGE_DECAY_WATCH_REASON = "age_decay_watch"
DECAY_SCORE_WATCH_REASON = "decay_score_watch"
ISSUER_FLOOR_WATCH_REASON = "issuer_floor_watch"
ALIGNMENT_FLOOR_WATCH_REASON = "alignment_floor_watch"
PARSE_FLOOR_WATCH_REASON = "parse_floor_watch"
LOW_DECAY_SCORE_REASON = "low_decay_score"

REASON_CODE_PRIORITY = (
    PASS_REASON,
    NO_EVIDENCE_REASON,
    AGE_DECAY_WATCH_REASON,
    DECAY_SCORE_WATCH_REASON,
    ISSUER_FLOOR_WATCH_REASON,
    ALIGNMENT_FLOOR_WATCH_REASON,
    PARSE_FLOOR_WATCH_REASON,
    LOW_DECAY_SCORE_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)

UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "source",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "db",
    "database",
    "network",
    "wallet",
    "auth",
    "order",
    "live",
    "trading",
    "sizing",
    "recommendation",
)

PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "evidence_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_decay_score",
        "status",
        "reason_codes",
        "score_rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "item_ref",
        "kind_class",
        "observed_at",
        "age_seconds",
        "issuer_score",
        "resolution_alignment",
        "parse_confidence",
        "recency_factor",
        "decay_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchSourceClaimResolutionAuthorityDecayScorecardConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("3600.000000")
    stale_age_seconds: Decimal = Decimal("86400.000000")
    pass_decay_score: Decimal = Decimal("0.800000")
    watch_decay_score: Decimal = Decimal("0.500000")
    issuer_weight: Decimal = Decimal("0.300000")
    resolution_alignment_weight: Decimal = Decimal("0.350000")
    parse_confidence_weight: Decimal = Decimal("0.350000")
    min_issuer_score: Decimal = Decimal("0.500000")
    min_resolution_alignment: Decimal = Decimal("0.500000")
    min_parse_confidence: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceClaimResolutionAuthorityDecayScorecardConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_age_seconds", "stale_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_age_seconds >= self.stale_age_seconds:
            raise ValueError("stale_age_seconds must be greater than fresh_age_seconds")
        for field_name in (
            "pass_decay_score",
            "watch_decay_score",
            "issuer_weight",
            "resolution_alignment_weight",
            "parse_confidence_weight",
            "min_issuer_score",
            "min_resolution_alignment",
            "min_parse_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.pass_decay_score <= self.watch_decay_score:
            raise ValueError("pass_decay_score must be greater than watch_decay_score")
        with localcontext(DECIMAL_CONTEXT):
            weight_sum = (
                self.issuer_weight
                + self.resolution_alignment_weight
                + self.parse_confidence_weight
            )
        if _normalize_probability("weight_sum", weight_sum) != ONE:
            raise ValueError("score weights must sum to 1")
        _require_hard_flags("config", self)
        _require_supported_config(self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence(_FinalPublicDataclass):
    claim_id: str
    evidence_id: str
    issuer_id: str
    resolution_id: str
    issuer_kind: str
    observed_at: datetime
    issuer_score: Decimal = ZERO
    resolution_alignment: Decimal = ZERO
    parse_confidence: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence,
            "evidence",
        )
        for field_name in (
            "claim_id",
            "evidence_id",
            "issuer_id",
            "resolution_id",
            "issuer_kind",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("issuer_kind", self.issuer_kind, ISSUER_KINDS)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "issuer_score",
            "resolution_alignment",
            "parse_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchSourceClaimResolutionAuthorityDecayScorecardRow(_FinalPublicDataclass):
    item_ref: str
    kind_class: str
    observed_at: datetime
    age_seconds: Decimal
    issuer_score: Decimal
    resolution_alignment: Decimal
    parse_confidence: Decimal
    recency_factor: Decimal
    decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceClaimResolutionAuthorityDecayScorecardRow,
            "row",
        )
        _require_public_string("item_ref", self.item_ref)
        _require_member("kind_class", self.kind_class, ISSUER_KINDS)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "age_seconds",
            _normalize_nonnegative_decimal("age_seconds", self.age_seconds),
        )
        for field_name in (
            "issuer_score",
            "resolution_alignment",
            "parse_confidence",
            "recency_factor",
            "decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchSourceClaimResolutionAuthorityDecayScorecardReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_decay_score: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    score_rows: tuple[ResearchSourceClaimResolutionAuthorityDecayScorecardRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceClaimResolutionAuthorityDecayScorecardReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "evidence_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_decay_score",
            _normalize_optional_probability(
                "average_decay_score",
                self.average_decay_score,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "score_rows", _normalize_rows(self.score_rows))
        _require_hard_flags("report", self)
        _validate_report(self)
        _set_or_validate_derived_validation_digest(self)
        _reject_unsafe_public_payload("report", _payload_value(self))

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
            self,
        )


def build_research_source_claim_resolution_authority_decay_scorecard_report(
    evidence_rows: Iterable[ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence],
    *,
    config: ResearchSourceClaimResolutionAuthorityDecayScorecardConfig,
    generated_at: datetime,
) -> ResearchSourceClaimResolutionAuthorityDecayScorecardReport:
    if type(config) is not ResearchSourceClaimResolutionAuthorityDecayScorecardConfig:
        raise ValueError(
            "config must be a ResearchSourceClaimResolutionAuthorityDecayScorecardConfig",
        )
    _validate_config_state(config)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_evidence = _normalize_evidence_rows(
        evidence_rows,
        generated_at=generated_at_utc,
    )
    unreferenced_rows = tuple(
        _row_for_evidence(
            evidence,
            item_ref="item-000000",
            config=config,
            generated_at=generated_at_utc,
        )
        for evidence in normalized_evidence
    )
    score_rows = tuple(
        replace(row, item_ref=f"item-{index:06d}")
        for index, row in enumerate(
            sorted(unreferenced_rows, key=_row_content_sort_key),
            start=1,
        )
    )
    reason_codes = _report_reason_codes(score_rows)
    return ResearchSourceClaimResolutionAuthorityDecayScorecardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        evidence_count=_count(len(score_rows)),
        pass_count=_count(sum(1 for row in score_rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in score_rows if row.status == "watch")),
        block_count=_count(sum(1 for row in score_rows if row.status == "block")),
        average_decay_score=_average_decay_score(score_rows),
        status=_report_status(reason_codes),
        reason_codes=reason_codes,
        score_rows=score_rows,
    )


def research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
    value: ResearchSourceClaimResolutionAuthorityDecayScorecardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchSourceClaimResolutionAuthorityDecayScorecardReport:
        _validate_report(value)
        _validate_derived_validation_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError(
            "value must be a ResearchSourceClaimResolutionAuthorityDecayScorecardReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    validate_research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
        payload,
    )
    return dict(payload)


def validate_research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _validate_public_payload_shape(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    parsed_report = _report_from_public_payload(payload)
    if _payload_value(parsed_report) != payload:
        raise ValueError("public payload must use canonical scorecard serialization")
    return True


def _row_for_evidence(
    evidence: ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence,
    *,
    item_ref: str,
    config: ResearchSourceClaimResolutionAuthorityDecayScorecardConfig,
    generated_at: datetime,
) -> ResearchSourceClaimResolutionAuthorityDecayScorecardRow:
    age_seconds = _seconds_between(evidence.observed_at, generated_at)
    recency_factor = _recency_factor(age_seconds, config=config)
    base_score = _weighted_score(evidence, config=config)
    with localcontext(DECIMAL_CONTEXT):
        decay_score = _normalize_probability("decay_score", base_score * recency_factor)
    reason_codes = _row_reason_codes(
        evidence,
        age_seconds=age_seconds,
        decay_score=decay_score,
        config=config,
    )
    return ResearchSourceClaimResolutionAuthorityDecayScorecardRow(
        item_ref=item_ref,
        kind_class=evidence.issuer_kind,
        observed_at=evidence.observed_at,
        age_seconds=age_seconds,
        issuer_score=evidence.issuer_score,
        resolution_alignment=evidence.resolution_alignment,
        parse_confidence=evidence.parse_confidence,
        recency_factor=recency_factor,
        decay_score=decay_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    evidence: ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence,
    *,
    age_seconds: Decimal,
    decay_score: Decimal,
    config: ResearchSourceClaimResolutionAuthorityDecayScorecardConfig,
) -> tuple[str, ...]:
    return _row_reason_codes_for_values(
        issuer_score=evidence.issuer_score,
        resolution_alignment=evidence.resolution_alignment,
        parse_confidence=evidence.parse_confidence,
        age_seconds=age_seconds,
        decay_score=decay_score,
        config=config,
    )


def _row_reason_codes_for_values(
    *,
    issuer_score: Decimal,
    resolution_alignment: Decimal,
    parse_confidence: Decimal,
    age_seconds: Decimal,
    decay_score: Decimal,
    config: ResearchSourceClaimResolutionAuthorityDecayScorecardConfig,
) -> tuple[str, ...]:
    if decay_score < config.watch_decay_score:
        return (LOW_DECAY_SCORE_REASON,)
    reasons: list[str] = []
    if age_seconds > config.fresh_age_seconds:
        reasons.append(AGE_DECAY_WATCH_REASON)
    if decay_score < config.pass_decay_score:
        reasons.append(DECAY_SCORE_WATCH_REASON)
    if issuer_score < config.min_issuer_score:
        reasons.append(ISSUER_FLOOR_WATCH_REASON)
    if resolution_alignment < config.min_resolution_alignment:
        reasons.append(ALIGNMENT_FLOOR_WATCH_REASON)
    if parse_confidence < config.min_parse_confidence:
        reasons.append(PARSE_FLOOR_WATCH_REASON)
    if not reasons:
        return (PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimResolutionAuthorityDecayScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_EVIDENCE_REASON,)
    if all(row.reason_codes == (PASS_REASON,) for row in rows):
        return (PASS_REASON,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(
            code
            for row in rows
            for code in row.reason_codes
            if code != PASS_REASON
        ),
    )


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if NO_EVIDENCE_REASON in reason_codes or LOW_DECAY_SCORE_REASON in reason_codes:
        return "block"
    return "watch"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if LOW_DECAY_SCORE_REASON in reason_codes:
        return "block"
    return "watch"


def _validate_row(
    row: ResearchSourceClaimResolutionAuthorityDecayScorecardRow,
) -> None:
    config = ResearchSourceClaimResolutionAuthorityDecayScorecardConfig()
    normalized_observed_at = _as_utc("observed_at", row.observed_at)
    if row.observed_at != normalized_observed_at or row.observed_at.tzinfo is not UTC:
        raise ValueError("observed_at must be canonical UTC")
    expected_recency_factor = _recency_factor(row.age_seconds, config=config)
    if row.recency_factor != expected_recency_factor:
        raise ValueError("recency_factor must match age_seconds")
    base_score = _weighted_score_values(
        issuer_score=row.issuer_score,
        resolution_alignment=row.resolution_alignment,
        parse_confidence=row.parse_confidence,
        config=config,
    )
    with localcontext(DECIMAL_CONTEXT):
        expected_decay_score = _normalize_probability(
            "decay_score",
            base_score * expected_recency_factor,
        )
    if row.decay_score != expected_decay_score:
        raise ValueError("decay_score must match score inputs")
    expected_reason_codes = _row_reason_codes_for_values(
        issuer_score=row.issuer_score,
        resolution_alignment=row.resolution_alignment,
        parse_confidence=row.parse_confidence,
        age_seconds=row.age_seconds,
        decay_score=row.decay_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match score inputs")
    if row.status != _status_from_reason_codes(expected_reason_codes):
        raise ValueError("status must match score inputs")


def _normalize_evidence_rows(
    value: Iterable[ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence],
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("evidence_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("evidence_rows must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence:
            raise ValueError(
                "evidence_rows must contain "
                "ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence values",
            )
        _validate_evidence_state(row)
        if row.evidence_id in seen_ids:
            raise ValueError("evidence_id values must be unique")
        seen_ids.add(row.evidence_id)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return tuple(sorted(rows, key=_evidence_sort_key))


def _normalize_rows(
    value: Iterable[ResearchSourceClaimResolutionAuthorityDecayScorecardRow],
) -> tuple[ResearchSourceClaimResolutionAuthorityDecayScorecardRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("score_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("score_rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceClaimResolutionAuthorityDecayScorecardRow:
            raise ValueError(
                "score_rows must contain "
                "ResearchSourceClaimResolutionAuthorityDecayScorecardRow values",
            )
        _require_hard_flags("row", row)
        _validate_row(row)
        if row.item_ref in seen_refs:
            raise ValueError("item_ref values must be unique")
        seen_refs.add(row.item_ref)
    expected_refs = tuple(f"item-{index:06d}" for index in range(1, len(rows) + 1))
    if tuple(row.item_ref for row in rows) != expected_refs:
        raise ValueError("item_ref values must use canonical sequence")
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("score_rows must be sorted deterministically")
    return rows


def _validate_report(
    report: ResearchSourceClaimResolutionAuthorityDecayScorecardReport,
) -> None:
    normalized_generated_at = _as_utc("generated_at", report.generated_at)
    if report.generated_at != normalized_generated_at or report.generated_at.tzinfo is not UTC:
        raise ValueError("generated_at must be canonical UTC")
    rows = report.score_rows
    for row in rows:
        _validate_row(row)
        if row.observed_at > report.generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if row.age_seconds != _seconds_between(row.observed_at, report.generated_at):
            raise ValueError("age_seconds must match generated_at and observed_at")
    if report.evidence_count != _count(len(rows)):
        raise ValueError("evidence_count must match score_rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match score_rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match score_rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match score_rows")
    if report.average_decay_score != _average_decay_score(rows):
        raise ValueError("average_decay_score must match score_rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match score_rows")
    if report.status != _report_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_evidence_state(
    evidence: ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence,
) -> None:
    _require_exact_type(
        evidence,
        ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence,
        "evidence",
    )
    for field_name in (
        "claim_id",
        "evidence_id",
        "issuer_id",
        "resolution_id",
        "issuer_kind",
    ):
        _require_public_string(field_name, getattr(evidence, field_name))
    _require_member("issuer_kind", evidence.issuer_kind, ISSUER_KINDS)
    normalized_observed_at = _as_utc("observed_at", evidence.observed_at)
    if (
        evidence.observed_at != normalized_observed_at
        or evidence.observed_at.tzinfo is not UTC
    ):
        raise ValueError("evidence observed_at must be canonical UTC")
    for field_name in (
        "issuer_score",
        "resolution_alignment",
        "parse_confidence",
    ):
        normalized = _normalize_probability(field_name, getattr(evidence, field_name))
        if getattr(evidence, field_name) != normalized:
            raise ValueError(f"evidence {field_name} must be canonical")
    _require_hard_flags("evidence", evidence)


def _validate_config_state(
    config: ResearchSourceClaimResolutionAuthorityDecayScorecardConfig,
) -> None:
    if type(config) is not ResearchSourceClaimResolutionAuthorityDecayScorecardConfig:
        raise ValueError(
            "config must be a ResearchSourceClaimResolutionAuthorityDecayScorecardConfig",
        )
    ResearchSourceClaimResolutionAuthorityDecayScorecardConfig(
        config_version=config.config_version,
        fresh_age_seconds=config.fresh_age_seconds,
        stale_age_seconds=config.stale_age_seconds,
        pass_decay_score=config.pass_decay_score,
        watch_decay_score=config.watch_decay_score,
        issuer_weight=config.issuer_weight,
        resolution_alignment_weight=config.resolution_alignment_weight,
        parse_confidence_weight=config.parse_confidence_weight,
        min_issuer_score=config.min_issuer_score,
        min_resolution_alignment=config.min_resolution_alignment,
        min_parse_confidence=config.min_parse_confidence,
        paper_only=config.paper_only,
        report_only=config.report_only,
        readonly=config.readonly,
    )


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    if frozenset(payload) != PAYLOAD_KEYS:
        raise ValueError("public payload keys must match scorecard schema")
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _payload_datetime_string(payload, "generated_at")
    config_version = _payload_required_string(payload, "config_version")
    _require_public_string("config_version", config_version)
    if config_version != DEFAULT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    for field_name in ("status", "derived_validation_digest"):
        _payload_required_string(payload, field_name)
    _require_member("status", payload["status"], STATUSES)
    for field_name in (
        "evidence_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _payload_decimal_string(
            payload,
            field_name,
            whole=True,
            optional=False,
            minimum=ZERO,
            maximum=None,
        )
    _payload_decimal_string(
        payload,
        "average_decay_score",
        whole=False,
        optional=True,
        minimum=ZERO,
        maximum=ONE,
    )
    _payload_reason_codes(payload["reason_codes"])
    rows = payload["score_rows"]
    if type(rows) is not list:
        raise ValueError("score_rows must be a list")
    item_refs: list[str] = []
    for row in rows:
        if type(row) is not dict:
            raise ValueError("score_rows must contain dict values")
        _validate_public_row_payload(row)
        item_refs.append(row["item_ref"])
    expected_refs = [f"item-{index:06d}" for index in range(1, len(rows) + 1)]
    if item_refs != expected_refs:
        raise ValueError("item_ref values must use canonical sequence")


def _validate_public_row_payload(row: dict[str, Any]) -> None:
    if frozenset(row) != ROW_PAYLOAD_KEYS:
        raise ValueError("public row keys must match scorecard schema")
    for field_name in ("paper_only", "report_only", "readonly"):
        if row[field_name] is not True:
            raise ValueError(f"score row {field_name} must be True")
    for field_name in ("item_ref", "kind_class", "status"):
        _payload_required_string(row, field_name)
    _require_public_string("item_ref", row["item_ref"])
    _payload_datetime_string(row, "observed_at")
    _require_member("kind_class", row["kind_class"], ISSUER_KINDS)
    _require_member("status", row["status"], STATUSES)
    _payload_decimal_string(
        row,
        "age_seconds",
        whole=False,
        optional=False,
        minimum=ZERO,
        maximum=None,
    )
    for field_name in (
        "issuer_score",
        "resolution_alignment",
        "parse_confidence",
        "recency_factor",
        "decay_score",
    ):
        _payload_decimal_string(
            row,
            field_name,
            whole=False,
            optional=False,
            minimum=ZERO,
            maximum=ONE,
        )
    reason_codes = _payload_reason_codes(row["reason_codes"])
    if row["status"] != _status_from_reason_codes(reason_codes):
        raise ValueError("score row status must match reason_codes")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceClaimResolutionAuthorityDecayScorecardReport:
    return ResearchSourceClaimResolutionAuthorityDecayScorecardReport(
        generated_at=_payload_datetime_string(payload, "generated_at"),
        config_version=_payload_required_string(payload, "config_version"),
        evidence_count=_required_payload_decimal(
            payload,
            "evidence_count",
            whole=True,
            minimum=ZERO,
            maximum=None,
        ),
        pass_count=_required_payload_decimal(
            payload,
            "pass_count",
            whole=True,
            minimum=ZERO,
            maximum=None,
        ),
        watch_count=_required_payload_decimal(
            payload,
            "watch_count",
            whole=True,
            minimum=ZERO,
            maximum=None,
        ),
        block_count=_required_payload_decimal(
            payload,
            "block_count",
            whole=True,
            minimum=ZERO,
            maximum=None,
        ),
        average_decay_score=_payload_decimal_string(
            payload,
            "average_decay_score",
            whole=False,
            optional=True,
            minimum=ZERO,
            maximum=ONE,
        ),
        status=_payload_required_string(payload, "status"),
        reason_codes=_payload_reason_codes(payload["reason_codes"]),
        score_rows=tuple(_row_from_public_payload(row) for row in payload["score_rows"]),
        derived_validation_digest=_payload_required_string(
            payload,
            "derived_validation_digest",
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceClaimResolutionAuthorityDecayScorecardRow:
    return ResearchSourceClaimResolutionAuthorityDecayScorecardRow(
        item_ref=_payload_required_string(payload, "item_ref"),
        kind_class=_payload_required_string(payload, "kind_class"),
        observed_at=_payload_datetime_string(payload, "observed_at"),
        age_seconds=_required_payload_decimal(
            payload,
            "age_seconds",
            whole=False,
            minimum=ZERO,
            maximum=None,
        ),
        issuer_score=_required_payload_decimal(
            payload,
            "issuer_score",
            whole=False,
            minimum=ZERO,
            maximum=ONE,
        ),
        resolution_alignment=_required_payload_decimal(
            payload,
            "resolution_alignment",
            whole=False,
            minimum=ZERO,
            maximum=ONE,
        ),
        parse_confidence=_required_payload_decimal(
            payload,
            "parse_confidence",
            whole=False,
            minimum=ZERO,
            maximum=ONE,
        ),
        recency_factor=_required_payload_decimal(
            payload,
            "recency_factor",
            whole=False,
            minimum=ZERO,
            maximum=ONE,
        ),
        decay_score=_required_payload_decimal(
            payload,
            "decay_score",
            whole=False,
            minimum=ZERO,
            maximum=ONE,
        ),
        status=_payload_required_string(payload, "status"),
        reason_codes=_payload_reason_codes(payload["reason_codes"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _set_or_validate_derived_validation_digest(
    report: ResearchSourceClaimResolutionAuthorityDecayScorecardReport,
) -> None:
    current = report.derived_validation_digest
    expected = _derived_validation_digest(report)
    if current == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256_digest("derived_validation_digest", current)
    if current != expected:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_derived_validation_digest(
    report: ResearchSourceClaimResolutionAuthorityDecayScorecardReport,
) -> None:
    current = _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if current != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(value: object) -> str:
    payload = _without_derived_validation_digest(_payload_value(value))
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _without_derived_validation_digest(value: object) -> object:
    if type(value) is dict:
        return {
            key: _without_derived_validation_digest(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if type(value) is list:
        return [_without_derived_validation_digest(item) for item in value]
    return value


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if path.endswith("derived_validation_digest"):
            return
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public payload value in {path or label}")
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(f"{path or label} must use Decimal strings, not numeric values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not public JSON serializable")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_decimal_string(
    payload: dict[str, Any],
    field_name: str,
    *,
    whole: bool,
    optional: bool,
    minimum: Decimal | None,
    maximum: Decimal | None,
) -> Decimal | None:
    value = payload.get(field_name)
    if value is None and optional:
        return None
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if decimal_value.is_zero() and decimal_value.is_signed():
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    if minimum is not None and decimal_value < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    if maximum is not None and decimal_value > maximum:
        raise ValueError(f"{field_name} must be at most {maximum}")
    if whole and decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal string")
    quantum = COUNT_QUANTUM if whole else VALUE_QUANTUM
    normalized = _quantize_decimal(field_name, decimal_value, quantum)
    if decimal_value != normalized or value != format(normalized, "f"):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _required_payload_decimal(
    payload: dict[str, Any],
    field_name: str,
    *,
    whole: bool,
    minimum: Decimal | None,
    maximum: Decimal | None,
) -> Decimal:
    value = _payload_decimal_string(
        payload,
        field_name,
        whole=whole,
        optional=False,
        minimum=minimum,
        maximum=maximum,
    )
    if value is None:
        raise ValueError(f"{field_name} must be a Decimal string")
    return value


def _payload_datetime_string(payload: dict[str, Any], field_name: str) -> datetime:
    value = _payload_required_string(payload, field_name)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _payload_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    normalized = _normalize_reason_codes("reason_codes", tuple(value))
    if value != list(normalized):
        raise ValueError("reason_codes must use canonical sequence")
    return normalized


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _weighted_score(
    evidence: ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence,
    *,
    config: ResearchSourceClaimResolutionAuthorityDecayScorecardConfig,
) -> Decimal:
    return _weighted_score_values(
        issuer_score=evidence.issuer_score,
        resolution_alignment=evidence.resolution_alignment,
        parse_confidence=evidence.parse_confidence,
        config=config,
    )


def _weighted_score_values(
    *,
    issuer_score: Decimal,
    resolution_alignment: Decimal,
    parse_confidence: Decimal,
    config: ResearchSourceClaimResolutionAuthorityDecayScorecardConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            issuer_score * config.issuer_weight
            + resolution_alignment * config.resolution_alignment_weight
            + parse_confidence * config.parse_confidence_weight
        )
    return _normalize_probability("weighted_score", value)


def _recency_factor(
    age_seconds: Decimal,
    *,
    config: ResearchSourceClaimResolutionAuthorityDecayScorecardConfig,
) -> Decimal:
    if age_seconds <= config.fresh_age_seconds:
        return ONE
    if age_seconds >= config.stale_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        decay_window = config.stale_age_seconds - config.fresh_age_seconds
        decayed_age = age_seconds - config.fresh_age_seconds
        value = ONE - (decayed_age / decay_window)
    return _normalize_probability("recency_factor", value)


def _average_decay_score(
    rows: tuple[ResearchSourceClaimResolutionAuthorityDecayScorecardRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        value = sum((row.decay_score for row in rows), ZERO) / Decimal(len(rows))
    return _normalize_probability("average_decay_score", value)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * Decimal("86400")
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / Decimal("1000000"))
        )
    return _normalize_nonnegative_decimal("age_seconds", seconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return _quantize_decimal(field_name, decimal_value, VALUE_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(field_name, decimal_value, VALUE_QUANTUM)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return _quantize_decimal(field_name, decimal_value, VALUE_QUANTUM)


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        integral_value = decimal_value.to_integral_value()
    if decimal_value != integral_value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(field_name, decimal_value, COUNT_QUANTUM)


def _count(value: int) -> Decimal:
    return _quantize_decimal("count", Decimal(value), COUNT_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _quantize_decimal(
    field_name: str,
    value: Decimal,
    quantum: Decimal,
) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(quantum)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} cannot be quantized") from exc


def _normalize_reason_codes(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        if type(code) is not str or not code:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if code not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unknown reason code")
    active_codes = [code for code in codes if code != PASS_REASON]
    if PASS_REASON in codes and active_codes:
        raise ValueError(f"{field_name} pass reason must stand alone")
    if NO_EVIDENCE_REASON in codes and len(codes) != 1:
        raise ValueError(f"{field_name} no evidence reason must stand alone")
    return tuple(sorted(set(codes), key=REASON_CODE_PRIORITY.index))


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical string")
    if "://" in value or "?" in value or _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public content")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(value: object, expected_type: type[Any], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_supported_config(
    config: ResearchSourceClaimResolutionAuthorityDecayScorecardConfig,
) -> None:
    expected_values = {
        "fresh_age_seconds": Decimal("3600.000000"),
        "stale_age_seconds": Decimal("86400.000000"),
        "pass_decay_score": Decimal("0.800000"),
        "watch_decay_score": Decimal("0.500000"),
        "issuer_weight": Decimal("0.300000"),
        "resolution_alignment_weight": Decimal("0.350000"),
        "parse_confidence_weight": Decimal("0.350000"),
        "min_issuer_score": Decimal("0.500000"),
        "min_resolution_alignment": Decimal("0.500000"),
        "min_parse_confidence": Decimal("0.500000"),
    }
    if any(
        getattr(config, field_name) != expected_value
        for field_name, expected_value in expected_values.items()
    ):
        raise ValueError("config must use the supported configuration")


def _evidence_sort_key(
    evidence: ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence,
) -> tuple[object, ...]:
    return (
        evidence.claim_id,
        evidence.evidence_id,
        evidence.issuer_id,
        evidence.resolution_id,
        evidence.issuer_kind,
        evidence.observed_at,
        evidence.issuer_score,
        evidence.resolution_alignment,
        evidence.parse_confidence,
        evidence.paper_only,
        evidence.report_only,
        evidence.readonly,
    )


def _row_content_sort_key(
    row: ResearchSourceClaimResolutionAuthorityDecayScorecardRow,
) -> tuple[object, ...]:
    return (
        row.kind_class,
        row.observed_at,
        row.age_seconds,
        row.issuer_score,
        row.resolution_alignment,
        row.parse_confidence,
        row.recency_factor,
        row.decay_score,
        row.status,
        row.reason_codes,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def _row_sort_key(
    row: ResearchSourceClaimResolutionAuthorityDecayScorecardRow,
) -> tuple[object, ...]:
    return (*_row_content_sort_key(row), row.item_ref)


__all__ = (
    "ResearchSourceClaimResolutionAuthorityDecayScorecardConfig",
    "ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence",
    "ResearchSourceClaimResolutionAuthorityDecayScorecardReport",
    "ResearchSourceClaimResolutionAuthorityDecayScorecardRow",
    "build_research_source_claim_resolution_authority_decay_scorecard_report",
    "research_source_claim_resolution_authority_decay_scorecard_report_public_payload",
    "validate_research_source_claim_resolution_authority_decay_scorecard_report_public_payload",
)
