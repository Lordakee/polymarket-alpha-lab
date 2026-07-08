"""Report-only event-memory similarity matching."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Iterable, Mapping


DEFAULT_RESEARCH_EVENT_SIMILARITY_MEMORY_MATCH_CONFIG_VERSION = (
    "research-event-similarity-memory-match-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_REPORT_STATUSES = frozenset(("pass", "watch", "block", "empty"))
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate",
    "market",
    "source",
    "url",
    "text",
    "dsn",
    "table",
    "token",
)
_REASON_CODE_SEQUENCE = (
    "low_domain_similarity",
    "low_settlement_rule_similarity",
    "low_info_channel_similarity",
    "low_composite_similarity",
    "high_historical_error",
    "review_required",
    "memory_similarity_pass",
)
_RETRIEVAL_NEED_SEQUENCE = (
    "local_supabase_similarity_lookup",
    "local_postgres_similarity_lookup",
)


@dataclass(frozen=True)
class ResearchEventSimilarityMemoryMatchConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_SIMILARITY_MEMORY_MATCH_CONFIG_VERSION
    min_domain_similarity_score: Decimal = Decimal("0.666667")
    min_settlement_rule_similarity_score: Decimal = Decimal("0.666667")
    min_info_channel_similarity_score: Decimal = Decimal("0.666667")
    min_composite_similarity_score: Decimal = Decimal("0.666667")
    max_historical_error_score: Decimal = Decimal("0.666667")
    max_review_need_score: Decimal = Decimal("0.666667")
    high_risk_pair_penalty: Decimal = Decimal("0.040000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSimilarityMemoryMatchConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSimilarityMemoryMatchConfig:
            raise ValueError(
                "config must be exactly ResearchEventSimilarityMemoryMatchConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SIMILARITY_MEMORY_MATCH_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_domain_similarity_score",
            "min_settlement_rule_similarity_score",
            "min_info_channel_similarity_score",
            "min_composite_similarity_score",
            "max_historical_error_score",
            "max_review_need_score",
            "high_risk_pair_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventSimilarityMemoryMatchInput:
    event_ref: str
    memory_ref: str
    domain_similarity_score: Decimal
    settlement_rule_similarity_score: Decimal
    info_channel_similarity_score: Decimal
    historical_error_score: Decimal
    review_need_score: Decimal
    memory_age_days: Decimal
    local_supabase_retrieval_needed: bool = False
    local_postgres_retrieval_needed: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSimilarityMemoryMatchInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSimilarityMemoryMatchInput:
            raise ValueError(
                "input must be exactly ResearchEventSimilarityMemoryMatchInput",
            )
        for field_name in ("event_ref", "memory_ref"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "domain_similarity_score",
            "settlement_rule_similarity_score",
            "info_channel_similarity_score",
            "historical_error_score",
            "review_need_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_days",
            _require_nonnegative_count_decimal("memory_age_days", self.memory_age_days),
        )
        for field_name in (
            "local_supabase_retrieval_needed",
            "local_postgres_retrieval_needed",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchEventSimilarityMemoryMatchRow:
    event_ref: str
    memory_ref: str
    domain_similarity_score: Decimal
    settlement_rule_similarity_score: Decimal
    info_channel_similarity_score: Decimal
    historical_error_score: Decimal
    review_need_score: Decimal
    memory_age_days: Decimal
    composite_similarity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    retrieval_need_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSimilarityMemoryMatchRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSimilarityMemoryMatchRow:
            raise ValueError("row must be exactly ResearchEventSimilarityMemoryMatchRow")
        for field_name in ("event_ref", "memory_ref"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "domain_similarity_score",
            "settlement_rule_similarity_score",
            "info_channel_similarity_score",
            "historical_error_score",
            "review_need_score",
            "composite_similarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_days",
            _require_nonnegative_count_decimal("memory_age_days", self.memory_age_days),
        )
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "retrieval_need_codes",
            _normalize_retrieval_need_codes(self.retrieval_need_codes),
        )
        _validate_row_reason_status(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventSimilarityMemoryMatchReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSimilarityMemoryMatchReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSimilarityMemoryMatchReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchEventSimilarityMemoryMatchReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchEventSimilarityMemoryMatchRetrievalNeedCount:
    retrieval_need_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSimilarityMemoryMatchRetrievalNeedCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSimilarityMemoryMatchRetrievalNeedCount:
            raise ValueError(
                "retrieval need count must be exactly "
                "ResearchEventSimilarityMemoryMatchRetrievalNeedCount",
            )
        _require_retrieval_need_code("retrieval_need_code", self.retrieval_need_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        _require_hard_flags("retrieval need count", self)
        _reject_unsafe_public_payload("retrieval need count", self)


@dataclass(frozen=True)
class ResearchEventSimilarityMemoryMatchReport:
    generated_at: datetime
    config_version: str
    report_status: str
    pair_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    review_required_count: Decimal
    high_historical_error_count: Decimal
    local_supabase_retrieval_count: Decimal
    local_postgres_retrieval_count: Decimal
    min_composite_similarity_score: Decimal
    max_historical_error_score: Decimal
    max_review_need_score: Decimal
    rows: tuple[ResearchEventSimilarityMemoryMatchRow, ...]
    reason_code_counts: tuple[ResearchEventSimilarityMemoryMatchReasonCodeCount, ...]
    retrieval_need_counts: tuple[
        ResearchEventSimilarityMemoryMatchRetrievalNeedCount,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSimilarityMemoryMatchReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSimilarityMemoryMatchReport:
            raise ValueError(
                "report must be exactly ResearchEventSimilarityMemoryMatchReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SIMILARITY_MEMORY_MATCH_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("report_status", self.report_status, _REPORT_STATUSES)
        for field_name in (
            "pair_count",
            "pass_count",
            "watch_count",
            "block_count",
            "review_required_count",
            "high_historical_error_count",
            "local_supabase_retrieval_count",
            "local_postgres_retrieval_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_composite_similarity_score",
            "max_historical_error_score",
            "max_review_need_score",
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
            "retrieval_need_counts",
            _normalize_retrieval_need_counts(self.retrieval_need_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
            return
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchEventSimilarityMemoryMatchReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        return payload


def build_research_event_similarity_memory_match_report(
    rows: Iterable[ResearchEventSimilarityMemoryMatchInput],
    *,
    generated_at: datetime,
    config: ResearchEventSimilarityMemoryMatchConfig | None = None,
) -> ResearchEventSimilarityMemoryMatchReport:
    """Build a deterministic report-only event-memory similarity snapshot."""

    if config is None:
        config = ResearchEventSimilarityMemoryMatchConfig()
    if type(config) is not ResearchEventSimilarityMemoryMatchConfig:
        raise ValueError("config must be a ResearchEventSimilarityMemoryMatchConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(rows)
    match_rows = tuple(_row_for_input(item, config) for item in normalized_inputs)
    reason_code_counts = _reason_code_counts(match_rows)
    retrieval_need_counts = _retrieval_need_counts(match_rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(match_rows),
        "pair_count": _decimal_count(len(match_rows)),
        "pass_count": _status_count(match_rows, "pass"),
        "watch_count": _status_count(match_rows, "watch"),
        "block_count": _status_count(match_rows, "block"),
        "review_required_count": _reason_count(match_rows, "review_required"),
        "high_historical_error_count": _reason_count(
            match_rows,
            "high_historical_error",
        ),
        "local_supabase_retrieval_count": _retrieval_count(
            match_rows,
            "local_supabase_similarity_lookup",
        ),
        "local_postgres_retrieval_count": _retrieval_count(
            match_rows,
            "local_postgres_similarity_lookup",
        ),
        "min_composite_similarity_score": min(
            (row.composite_similarity_score for row in match_rows),
            default=_ZERO,
        ),
        "max_historical_error_score": max(
            (row.historical_error_score for row in match_rows),
            default=_ZERO,
        ),
        "max_review_need_score": max(
            (row.review_need_score for row in match_rows),
            default=_ZERO,
        ),
        "rows": match_rows,
        "reason_code_counts": reason_code_counts,
        "retrieval_need_counts": retrieval_need_counts,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventSimilarityMemoryMatchReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _row_for_input(
    item: ResearchEventSimilarityMemoryMatchInput,
    config: ResearchEventSimilarityMemoryMatchConfig,
) -> ResearchEventSimilarityMemoryMatchRow:
    composite_similarity_score = _composite_similarity_score(item, config)
    reason_codes = _row_reason_codes(
        item,
        composite_similarity_score=composite_similarity_score,
        config=config,
    )
    return ResearchEventSimilarityMemoryMatchRow(
        event_ref=item.event_ref,
        memory_ref=item.memory_ref,
        domain_similarity_score=item.domain_similarity_score,
        settlement_rule_similarity_score=item.settlement_rule_similarity_score,
        info_channel_similarity_score=item.info_channel_similarity_score,
        historical_error_score=item.historical_error_score,
        review_need_score=item.review_need_score,
        memory_age_days=item.memory_age_days,
        composite_similarity_score=composite_similarity_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        retrieval_need_codes=_retrieval_need_codes_for_input(item),
    )


def _row_reason_codes(
    item: ResearchEventSimilarityMemoryMatchInput,
    *,
    composite_similarity_score: Decimal,
    config: ResearchEventSimilarityMemoryMatchConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    has_high_historical_error = (
        item.historical_error_score > config.max_historical_error_score
    )
    needs_review = item.review_need_score > config.max_review_need_score
    if item.domain_similarity_score < config.min_domain_similarity_score:
        reason_codes.append("low_domain_similarity")
    if (
        item.settlement_rule_similarity_score
        < config.min_settlement_rule_similarity_score
    ):
        reason_codes.append("low_settlement_rule_similarity")
    if item.info_channel_similarity_score < config.min_info_channel_similarity_score:
        reason_codes.append("low_info_channel_similarity")
    if (
        composite_similarity_score < config.min_composite_similarity_score
        and not has_high_historical_error
        and not needs_review
    ):
        reason_codes.append("low_composite_similarity")
    if has_high_historical_error:
        reason_codes.append("high_historical_error")
    if needs_review:
        reason_codes.append("review_required")
    if not reason_codes:
        return ("memory_similarity_pass",)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "high_historical_error" in reason_codes or "review_required" in reason_codes:
        return "block"
    if reason_codes == ("memory_similarity_pass",):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchEventSimilarityMemoryMatchRow, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _composite_similarity_score(
    item: ResearchEventSimilarityMemoryMatchInput,
    config: ResearchEventSimilarityMemoryMatchConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        value = (
            item.domain_similarity_score * Decimal("0.300000")
            + item.settlement_rule_similarity_score * Decimal("0.300000")
            + item.info_channel_similarity_score * Decimal("0.200000")
            + (_ONE - item.historical_error_score) * Decimal("0.100000")
            + (_ONE - item.review_need_score) * Decimal("0.100000")
        )
        if (
            item.historical_error_score > config.max_historical_error_score
            and item.review_need_score > config.max_review_need_score
        ):
            value -= config.high_risk_pair_penalty
        return _clamp_ratio(value)


def _retrieval_need_codes_for_input(
    item: ResearchEventSimilarityMemoryMatchInput,
) -> tuple[str, ...]:
    codes: list[str] = []
    if item.local_supabase_retrieval_needed:
        codes.append("local_supabase_similarity_lookup")
    if item.local_postgres_retrieval_needed:
        codes.append("local_postgres_similarity_lookup")
    return _normalize_retrieval_need_codes(tuple(codes))


def _validate_row_reason_status(row: ResearchEventSimilarityMemoryMatchRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchEventSimilarityMemoryMatchReport,
) -> None:
    rows = report.rows
    if report.pair_count != _decimal_count(len(rows)):
        raise ValueError("pair_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.review_required_count != _reason_count(rows, "review_required"):
        raise ValueError("review_required_count must match rows")
    if report.high_historical_error_count != _reason_count(
        rows,
        "high_historical_error",
    ):
        raise ValueError("high_historical_error_count must match rows")
    if report.local_supabase_retrieval_count != _retrieval_count(
        rows,
        "local_supabase_similarity_lookup",
    ):
        raise ValueError("local_supabase_retrieval_count must match rows")
    if report.local_postgres_retrieval_count != _retrieval_count(
        rows,
        "local_postgres_similarity_lookup",
    ):
        raise ValueError("local_postgres_retrieval_count must match rows")
    if report.min_composite_similarity_score != min(
        (row.composite_similarity_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_composite_similarity_score must match rows")
    if report.max_historical_error_score != max(
        (row.historical_error_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_historical_error_score must match rows")
    if report.max_review_need_score != max(
        (row.review_need_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_review_need_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.retrieval_need_counts != _retrieval_need_counts(rows):
        raise ValueError("retrieval_need_counts must match rows")


def _normalize_inputs(
    value: Iterable[ResearchEventSimilarityMemoryMatchInput],
) -> tuple[ResearchEventSimilarityMemoryMatchInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of similarity inputs")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of similarity inputs") from exc
    seen_pairs: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchEventSimilarityMemoryMatchInput:
            raise ValueError(
                "rows must contain ResearchEventSimilarityMemoryMatchInput",
            )
        _require_hard_flags("input", row)
        pair_key = (row.event_ref, row.memory_ref)
        if pair_key in seen_pairs:
            raise ValueError("event_ref and memory_ref pairs must be unique")
        seen_pairs.add(pair_key)
    return tuple(sorted(rows, key=lambda row: (row.event_ref, row.memory_ref)))


def _normalize_rows(
    value: Iterable[ResearchEventSimilarityMemoryMatchRow],
) -> tuple[ResearchEventSimilarityMemoryMatchRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of similarity rows")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of similarity rows") from exc
    seen_pairs: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchEventSimilarityMemoryMatchRow:
            raise ValueError("rows must contain ResearchEventSimilarityMemoryMatchRow")
        _require_hard_flags("row", row)
        pair_key = (row.event_ref, row.memory_ref)
        if pair_key in seen_pairs:
            raise ValueError("rows event_ref and memory_ref pairs must be unique")
        seen_pairs.add(pair_key)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.event_ref, row.memory_ref)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[ResearchEventSimilarityMemoryMatchReasonCodeCount],
) -> tuple[ResearchEventSimilarityMemoryMatchReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventSimilarityMemoryMatchReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventSimilarityMemoryMatchReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_codes.add(row.reason_code)
    sorted_rows = tuple(
        sorted(rows, key=lambda row: _REASON_CODE_SEQUENCE.index(row.reason_code)),
    )
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return rows


def _normalize_retrieval_need_counts(
    value: Iterable[ResearchEventSimilarityMemoryMatchRetrievalNeedCount],
) -> tuple[ResearchEventSimilarityMemoryMatchRetrievalNeedCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("retrieval_need_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("retrieval_need_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventSimilarityMemoryMatchRetrievalNeedCount:
            raise ValueError(
                "retrieval_need_counts must contain "
                "ResearchEventSimilarityMemoryMatchRetrievalNeedCount",
            )
        _require_hard_flags("retrieval need count", row)
        if row.retrieval_need_code in seen_codes:
            raise ValueError(
                "retrieval_need_counts retrieval_need_code values must be unique",
            )
        seen_codes.add(row.retrieval_need_code)
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: _RETRIEVAL_NEED_SEQUENCE.index(row.retrieval_need_code),
        ),
    )
    if rows != sorted_rows:
        raise ValueError("retrieval_need_counts must be sorted deterministically")
    return rows


def _reason_code_counts(
    rows: tuple[ResearchEventSimilarityMemoryMatchRow, ...],
) -> tuple[ResearchEventSimilarityMemoryMatchReasonCodeCount, ...]:
    counts: list[ResearchEventSimilarityMemoryMatchReasonCodeCount] = []
    for reason_code in _REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count > _ZERO:
            counts.append(
                ResearchEventSimilarityMemoryMatchReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                ),
            )
    return tuple(counts)


def _retrieval_need_counts(
    rows: tuple[ResearchEventSimilarityMemoryMatchRow, ...],
) -> tuple[ResearchEventSimilarityMemoryMatchRetrievalNeedCount, ...]:
    counts: list[ResearchEventSimilarityMemoryMatchRetrievalNeedCount] = []
    for retrieval_need_code in _RETRIEVAL_NEED_SEQUENCE:
        count = _retrieval_count(rows, retrieval_need_code)
        if count > _ZERO:
            counts.append(
                ResearchEventSimilarityMemoryMatchRetrievalNeedCount(
                    retrieval_need_code=retrieval_need_code,
                    count=count,
                ),
            )
    return tuple(counts)


def _status_count(
    rows: tuple[ResearchEventSimilarityMemoryMatchRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchEventSimilarityMemoryMatchRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _retrieval_count(
    rows: tuple[ResearchEventSimilarityMemoryMatchRow, ...],
    retrieval_need_code: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if retrieval_need_code in row.retrieval_need_codes),
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_member(field_name: str, value: object, members: frozenset[str]) -> str:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be a known value")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_retrieval_need_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _RETRIEVAL_NEED_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of reason codes")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of reason codes") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if "memory_similarity_pass" in normalized and len(normalized) > 1:
        raise ValueError("pass reason must stand alone")
    return tuple(
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _normalize_retrieval_need_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("retrieval_need_codes must be an iterable")
    try:
        retrieval_need_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("retrieval_need_codes must be an iterable") from exc
    normalized: list[str] = []
    for retrieval_need_code in retrieval_need_codes:
        _require_retrieval_need_code("retrieval_need_code", retrieval_need_code)
        if retrieval_need_code not in normalized:
            normalized.append(retrieval_need_code)
    return tuple(
        retrieval_need_code
        for retrieval_need_code in _RETRIEVAL_NEED_SEQUENCE
        if retrieval_need_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchEventSimilarityMemoryMatchReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return format(value, "f")
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


__all__ = (
    "DEFAULT_RESEARCH_EVENT_SIMILARITY_MEMORY_MATCH_CONFIG_VERSION",
    "ResearchEventSimilarityMemoryMatchConfig",
    "ResearchEventSimilarityMemoryMatchInput",
    "ResearchEventSimilarityMemoryMatchReasonCodeCount",
    "ResearchEventSimilarityMemoryMatchReport",
    "ResearchEventSimilarityMemoryMatchRetrievalNeedCount",
    "ResearchEventSimilarityMemoryMatchRow",
    "build_research_event_similarity_memory_match_report",
)
