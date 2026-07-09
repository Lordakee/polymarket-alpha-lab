"""Report-only source ranking for event resolution evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping


DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_SOURCE_RANK_CONFIG_VERSION = (
    "research-event-resolution-evidence-source-rank-report"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
SECONDS_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PRIVATE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,255}$")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

STATUSES = ("pass", "watch", "block")
SOURCE_KINDS = ("official", "primary", "secondary")
ROW_REASON_CODES = (
    "source_rank_pass",
    "source_rank_watch",
    "source_rank_block",
    "official_source_kind",
    "primary_source_kind",
    "secondary_source_kind",
    "fresh_evidence",
    "stale_evidence",
    "strong_corroboration",
    "limited_corroboration",
    "missing_corroboration",
    "independent_source_family_support",
    "limited_source_family_support",
    "missing_source_family_support",
    "contradiction_penalty_none",
    "contradiction_penalty_present",
    "contradiction_penalty_high",
)
REPORT_REASON_CODES = (
    "source_rank_report_passed",
    "source_rank_report_watch_rows",
    "source_rank_report_block_rows",
    "source_rank_report_empty",
    "contradiction_penalty_present",
    "stale_evidence_present",
)
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PRIVATE_TEXT_FRAGMENTS = (
    "authorization",
    "authentication",
    "private_key",
    "wallet",
    "order",
    "trade",
    "sizing",
    "recommendation",
    "token",
    "api_key",
    "access_key",
    "dsn",
)
UNSAFE_PUBLIC_FIELD_FRAGMENTS = (
    "candidate_key",
    "candidate_id",
    "market_id",
    "market_slug",
    "question",
    "source_key",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "sizing",
    "recommendation",
    "authorization",
    "authentication",
    "private_key",
    "api_key",
    "access_key",
    "balance",
    "network",
    "database",
    "persist",
    "live",
    "buy",
    "sell",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "://",
    "authorization",
    "authentication",
    "private key",
    "wallet",
    "order",
    "trade",
    "sizing",
    "recommendation",
    "token",
    "api key",
    "access key",
    "dsn",
)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_SOURCE_RANK_CONFIG_VERSION",
    "ResearchEventResolutionEvidenceSourceRankConfig",
    "ResearchEventResolutionEvidenceSourceRankInput",
    "ResearchEventResolutionEvidenceSourceRankRow",
    "ResearchEventResolutionEvidenceSourceRankReport",
    "build_research_event_resolution_evidence_source_rank_report",
    "research_event_resolution_evidence_source_rank_report_payload",
)


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceSourceRankConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_SOURCE_RANK_CONFIG_VERSION
    )
    authority_weight: Decimal = Decimal("0.350000")
    recency_weight: Decimal = Decimal("0.250000")
    corroboration_weight: Decimal = Decimal("0.200000")
    independence_weight: Decimal = Decimal("0.200000")
    contradiction_penalty_weight: Decimal = Decimal("0.300000")
    max_source_age_seconds: Decimal = Decimal("864000.000000")
    target_corroborating_evidence_count: Decimal = Decimal("4")
    target_independent_source_family_count: Decimal = Decimal("3")
    max_contradiction_count: Decimal = Decimal("2")
    pass_score_floor: Decimal = Decimal("0.750000")
    watch_score_floor: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceSourceRankConfig:
            raise TypeError(
                "ResearchEventResolutionEvidenceSourceRankConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionEvidenceSourceRankConfig:
            raise ValueError(
                "config must be exactly ResearchEventResolutionEvidenceSourceRankConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_SOURCE_RANK_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "authority_weight",
            "recency_weight",
            "corroboration_weight",
            "independence_weight",
            "contradiction_penalty_weight",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_source_age_seconds",
            "target_corroborating_evidence_count",
            "target_independent_source_family_count",
            "max_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceSourceRankInput:
    candidate_key: str
    source_key: str
    source_family: str
    source_kind: str
    authority_score: Decimal
    observed_at: datetime
    corroborating_evidence_count: Decimal
    independent_source_family_count: Decimal
    contradiction_count: Decimal = Decimal("0")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceSourceRankInput:
            raise TypeError(
                "ResearchEventResolutionEvidenceSourceRankInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionEvidenceSourceRankInput:
            raise ValueError(
                "input must be exactly ResearchEventResolutionEvidenceSourceRankInput",
            )
        for field_name in ("candidate_key", "source_key"):
            object.__setattr__(
                self,
                field_name,
                _require_private_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_family",
            _require_public_identifier("source_family", self.source_family),
        )
        object.__setattr__(
            self,
            "source_kind",
            _require_source_kind("source_kind", self.source_kind),
        )
        object.__setattr__(
            self,
            "authority_score",
            _require_ratio_decimal("authority_score", self.authority_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "corroborating_evidence_count",
            "independent_source_family_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceSourceRankRow:
    rank: Decimal
    candidate_digest: str
    source_digest: str
    source_family: str
    source_kind: str
    authority_score: Decimal
    recency_score: Decimal
    source_age_seconds: Decimal
    corroborating_evidence_count: Decimal
    corroboration_score: Decimal
    independent_source_family_count: Decimal
    independence_score: Decimal
    contradiction_count: Decimal
    contradiction_penalty: Decimal
    source_rank_score: Decimal
    pass_score_floor: Decimal
    watch_score_floor: Decimal
    status: str
    reason_codes: tuple[str, ...]
    row_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceSourceRankRow:
            raise TypeError(
                "ResearchEventResolutionEvidenceSourceRankRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionEvidenceSourceRankRow:
            raise ValueError("row must be exactly ResearchEventResolutionEvidenceSourceRankRow")
        object.__setattr__(
            self,
            "rank",
            _require_positive_integral_decimal("rank", self.rank),
        )
        for field_name in ("candidate_digest", "source_digest", "row_digest"):
            object.__setattr__(
                self,
                field_name,
                _require_sha256_digest(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_family",
            _require_public_identifier("source_family", self.source_family),
        )
        object.__setattr__(
            self,
            "source_kind",
            _require_source_kind("source_kind", self.source_kind),
        )
        for field_name in (
            "authority_score",
            "recency_score",
            "corroboration_score",
            "independence_score",
            "contradiction_penalty",
            "source_rank_score",
            "pass_score_floor",
            "watch_score_floor",
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
        for field_name in (
            "corroborating_evidence_count",
            "independent_source_family_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if self.watch_score_floor > self.pass_score_floor:
            raise ValueError("watch_score_floor must not exceed pass_score_floor")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row_consistency(self)
        if self.row_digest != _row_digest_from_values(asdict(self)):
            raise ValueError("row_digest must match row fields")


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceSourceRankReport:
    generated_at: datetime
    config_version: str
    report_status: str
    candidate_count: Decimal
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    contradiction_penalty_count: Decimal
    stale_evidence_count: Decimal
    average_source_rank_score: Decimal
    top_source_rank_score: Decimal
    bottom_source_rank_score: Decimal
    rows: tuple[ResearchEventResolutionEvidenceSourceRankRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceSourceRankReport:
            raise TypeError(
                "ResearchEventResolutionEvidenceSourceRankReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionEvidenceSourceRankReport:
            raise ValueError(
                "report must be exactly ResearchEventResolutionEvidenceSourceRankReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_SOURCE_RANK_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "report_status",
            _require_status("report_status", self.report_status),
        )
        for field_name in (
            "candidate_count",
            "source_count",
            "pass_count",
            "watch_count",
            "block_count",
            "contradiction_penalty_count",
            "stale_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_source_rank_score",
            "top_source_rank_score",
            "bottom_source_rank_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self)
        if self.derived_validation_digest != _derived_validation_digest(asdict(self)):
            raise ValueError("derived_validation_digest must match report fields")

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_event_resolution_evidence_source_rank_report(
    evidence_rows: object,
    *,
    generated_at: datetime,
    config: ResearchEventResolutionEvidenceSourceRankConfig | None = None,
) -> ResearchEventResolutionEvidenceSourceRankReport:
    if config is None:
        config = ResearchEventResolutionEvidenceSourceRankConfig()
    if type(config) is not ResearchEventResolutionEvidenceSourceRankConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionEvidenceSourceRankConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_evidence_rows = _normalize_evidence_rows(evidence_rows)
    for item in normalized_evidence_rows:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        _ranked_row(index, item, config=config, generated_at=generated_at_utc)
        for index, item in enumerate(
            _sorted_evidence_rows(normalized_evidence_rows, config, generated_at_utc),
            start=1,
        )
    )
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "candidate_count": _decimal_count(
            len({_candidate_digest(item.candidate_key) for item in normalized_evidence_rows}),
        ),
        "source_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "contradiction_penalty_count": _penalty_count(rows),
        "stale_evidence_count": _stale_count(rows),
        "average_source_rank_score": _average_score(rows),
        "top_source_rank_score": _top_score(rows),
        "bottom_source_rank_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return ResearchEventResolutionEvidenceSourceRankReport(**values)


def research_event_resolution_evidence_source_rank_report_payload(
    value: object,
) -> dict[str, object]:
    if type(value) is ResearchEventResolutionEvidenceSourceRankReport:
        return value.payload
    if type(value) is not dict:
        raise ValueError("payload source must be a report or dict")
    _require_payload_hard_flags(value)
    _reject_unsafe_public_payload("payload", value, allow_json_containers=True)
    digest = value.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(value):
        raise ValueError("derived_validation_digest must match payload fields")
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _sorted_evidence_rows(
    rows: tuple[ResearchEventResolutionEvidenceSourceRankInput, ...],
    config: ResearchEventResolutionEvidenceSourceRankConfig,
    generated_at: datetime,
) -> tuple[ResearchEventResolutionEvidenceSourceRankInput, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                -_source_rank_score(row, config, generated_at),
                _candidate_digest(row.candidate_key),
                _source_digest(row.source_key),
                row.source_family,
                row.source_kind,
            ),
        ),
    )


def _ranked_row(
    rank: int,
    item: ResearchEventResolutionEvidenceSourceRankInput,
    *,
    config: ResearchEventResolutionEvidenceSourceRankConfig,
    generated_at: datetime,
) -> ResearchEventResolutionEvidenceSourceRankRow:
    age_seconds = _seconds_between(item.observed_at, generated_at)
    recency_score = _recency_score(age_seconds, config.max_source_age_seconds)
    corroboration_score = _bounded_count_score(
        item.corroborating_evidence_count,
        config.target_corroborating_evidence_count,
    )
    independence_score = _bounded_count_score(
        item.independent_source_family_count,
        config.target_independent_source_family_count,
    )
    contradiction_penalty = _contradiction_penalty(item.contradiction_count, config)
    source_rank_score = _source_rank_score(item, config, generated_at)
    status = _row_status(source_rank_score, config)
    values = {
        "rank": Decimal(rank).quantize(COUNT_QUANT),
        "candidate_digest": _candidate_digest(item.candidate_key),
        "source_digest": _source_digest(item.source_key),
        "source_family": item.source_family,
        "source_kind": item.source_kind,
        "authority_score": item.authority_score,
        "recency_score": recency_score,
        "source_age_seconds": age_seconds,
        "corroborating_evidence_count": item.corroborating_evidence_count,
        "corroboration_score": corroboration_score,
        "independent_source_family_count": item.independent_source_family_count,
        "independence_score": independence_score,
        "contradiction_count": item.contradiction_count,
        "contradiction_penalty": contradiction_penalty,
        "source_rank_score": source_rank_score,
        "pass_score_floor": config.pass_score_floor,
        "watch_score_floor": config.watch_score_floor,
        "status": status,
        "reason_codes": _row_reason_codes(
            status=status,
            source_kind=item.source_kind,
            recency_score=recency_score,
            corroboration_score=corroboration_score,
            independence_score=independence_score,
            contradiction_penalty=contradiction_penalty,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["row_digest"] = _row_digest_from_values(values)
    return ResearchEventResolutionEvidenceSourceRankRow(**values)


def _source_rank_score(
    item: ResearchEventResolutionEvidenceSourceRankInput,
    config: ResearchEventResolutionEvidenceSourceRankConfig,
    generated_at: datetime,
) -> Decimal:
    age_seconds = _seconds_between(item.observed_at, generated_at)
    with localcontext(DECIMAL_CONTEXT):
        score = (
            item.authority_score * config.authority_weight
            + _recency_score(age_seconds, config.max_source_age_seconds)
            * config.recency_weight
            + _bounded_count_score(
                item.corroborating_evidence_count,
                config.target_corroborating_evidence_count,
            )
            * config.corroboration_weight
            + _bounded_count_score(
                item.independent_source_family_count,
                config.target_independent_source_family_count,
            )
            * config.independence_weight
            - _contradiction_penalty(item.contradiction_count, config)
        )
        return _clamp_ratio(score)


def _recency_score(source_age_seconds: Decimal, max_source_age_seconds: Decimal) -> Decimal:
    if source_age_seconds >= max_source_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - source_age_seconds / max_source_age_seconds)


def _bounded_count_score(count: Decimal, target_count: Decimal) -> Decimal:
    if target_count <= ZERO:
        raise ValueError("target_count must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(count / target_count)


def _contradiction_penalty(
    contradiction_count: Decimal,
    config: ResearchEventResolutionEvidenceSourceRankConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        contradiction_rate = _clamp_ratio(
            contradiction_count / config.max_contradiction_count,
        )
        return _clamp_ratio(contradiction_rate * config.contradiction_penalty_weight)


def _row_status(
    source_rank_score: Decimal,
    config: ResearchEventResolutionEvidenceSourceRankConfig,
) -> str:
    if source_rank_score >= config.pass_score_floor:
        return "pass"
    if source_rank_score >= config.watch_score_floor:
        return "watch"
    return "block"


def _report_status(rows: tuple[ResearchEventResolutionEvidenceSourceRankRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    source_kind: str,
    recency_score: Decimal,
    corroboration_score: Decimal,
    independence_score: Decimal,
    contradiction_penalty: Decimal,
) -> tuple[str, ...]:
    reason_codes = [
        f"source_rank_{status}",
        f"{source_kind}_source_kind",
    ]
    if recency_score == ZERO:
        reason_codes.append("stale_evidence")
    else:
        reason_codes.append("fresh_evidence")
    if corroboration_score == ZERO:
        reason_codes.append("missing_corroboration")
    elif corroboration_score < ONE:
        reason_codes.append("limited_corroboration")
    else:
        reason_codes.append("strong_corroboration")
    if independence_score == ZERO:
        reason_codes.append("missing_source_family_support")
    elif independence_score < ONE:
        reason_codes.append("limited_source_family_support")
    else:
        reason_codes.append("independent_source_family_support")
    if contradiction_penalty == ZERO:
        reason_codes.append("contradiction_penalty_none")
    elif contradiction_penalty >= Decimal("0.150000"):
        reason_codes.append("contradiction_penalty_high")
    else:
        reason_codes.append("contradiction_penalty_present")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionEvidenceSourceRankRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_rank_report_empty",)
    reason_codes: list[str] = []
    if all(row.status == "pass" for row in rows):
        reason_codes.append("source_rank_report_passed")
    if any(row.status == "watch" for row in rows):
        reason_codes.append("source_rank_report_watch_rows")
    if any(row.status == "block" for row in rows):
        reason_codes.append("source_rank_report_block_rows")
    if any(row.contradiction_penalty > ZERO for row in rows):
        reason_codes.append("contradiction_penalty_present")
    if any(row.recency_score == ZERO for row in rows):
        reason_codes.append("stale_evidence_present")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), REPORT_REASON_CODES)


def _status_count(
    rows: tuple[ResearchEventResolutionEvidenceSourceRankRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _penalty_count(rows: tuple[ResearchEventResolutionEvidenceSourceRankRow, ...]) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.contradiction_penalty > ZERO))


def _stale_count(rows: tuple[ResearchEventResolutionEvidenceSourceRankRow, ...]) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.recency_score == ZERO))


def _average_score(rows: tuple[ResearchEventResolutionEvidenceSourceRankRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(sum(row.source_rank_score for row in rows) / Decimal(len(rows)))


def _top_score(rows: tuple[ResearchEventResolutionEvidenceSourceRankRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.source_rank_score for row in rows)


def _bottom_score(rows: tuple[ResearchEventResolutionEvidenceSourceRankRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.source_rank_score for row in rows)


def _normalize_evidence_rows(
    value: object,
) -> tuple[ResearchEventResolutionEvidenceSourceRankInput, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("evidence_rows must be an iterable")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchEventResolutionEvidenceSourceRankInput:
            raise ValueError(
                "evidence_rows must contain ResearchEventResolutionEvidenceSourceRankInput",
            )
        _require_hard_flags("input", row)
    keys = tuple((row.candidate_key, row.source_key) for row in rows)
    if len(set(keys)) != len(keys):
        raise ValueError("evidence_rows must not contain duplicate candidate source keys")
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchEventResolutionEvidenceSourceRankRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchEventResolutionEvidenceSourceRankRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionEvidenceSourceRankRow",
            )
    return value


def _validate_config(config: ResearchEventResolutionEvidenceSourceRankConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        positive_weights = (
            config.authority_weight
            + config.recency_weight
            + config.corroboration_weight
            + config.independence_weight
        ).quantize(SCORE_QUANT)
    if positive_weights > ONE:
        raise ValueError("positive score weights must not exceed 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must not exceed pass_score_floor")


def _validate_row_consistency(row: ResearchEventResolutionEvidenceSourceRankRow) -> None:
    if row.status == "pass" and row.source_rank_score < row.pass_score_floor:
        raise ValueError("pass status requires a passing source_rank_score")
    if row.status == "watch" and not (
        row.watch_score_floor <= row.source_rank_score < row.pass_score_floor
    ):
        raise ValueError("watch status requires a watch source_rank_score")
    if row.status == "block" and row.source_rank_score >= row.watch_score_floor:
        raise ValueError("block status requires a blocking source_rank_score")
    if row.contradiction_count == ZERO and row.contradiction_penalty != ZERO:
        raise ValueError("contradiction_penalty must be zero without contradictions")
    if row.reason_codes != _row_reason_codes(
        status=row.status,
        source_kind=row.source_kind,
        recency_score=row.recency_score,
        corroboration_score=row.corroboration_score,
        independence_score=row.independence_score,
        contradiction_penalty=row.contradiction_penalty,
    ):
        raise ValueError("reason_codes must match row fields")


def _validate_report_consistency(report: ResearchEventResolutionEvidenceSourceRankReport) -> None:
    rows = report.rows
    if report.candidate_count > report.source_count:
        raise ValueError("candidate_count must not exceed source_count")
    if report.source_count != _decimal_count(len(rows)):
        raise ValueError("source_count must match rows")
    if (
        report.pass_count != _status_count(rows, "pass")
        or report.watch_count != _status_count(rows, "watch")
        or report.block_count != _status_count(rows, "block")
    ):
        raise ValueError("status counts must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.source_count:
        raise ValueError("status counts must sum to source_count")
    if report.contradiction_penalty_count != _penalty_count(rows):
        raise ValueError("contradiction_penalty_count must match rows")
    if report.stale_evidence_count != _stale_count(rows):
        raise ValueError("stale_evidence_count must match rows")
    if report.average_source_rank_score != _average_score(rows):
        raise ValueError("average_source_rank_score must match rows")
    if report.top_source_rank_score != _top_score(rows):
        raise ValueError("top_source_rank_score must match rows")
    if report.bottom_source_rank_score != _bottom_score(rows):
        raise ValueError("bottom_source_rank_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    _validate_rows_sorted(rows)


def _validate_rows_sorted(
    rows: tuple[ResearchEventResolutionEvidenceSourceRankRow, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.source_rank_score,
                row.candidate_digest,
                row.source_digest,
                row.source_family,
                row.source_kind,
            ),
        ),
    )
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    if rows != expected or tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must be sorted by source_rank_score and rank")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    seconds = Decimal(str((end - start).total_seconds()))
    with localcontext(DECIMAL_CONTEXT):
        return seconds.quantize(SECONDS_QUANT)


def _require_private_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a private identifier")
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe private value")
    if any(fragment in lowered for fragment in UNSAFE_PRIVATE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe private value")
    if not PRIVATE_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a private identifier")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_source_kind(field_name: str, value: object) -> str:
    value = _require_public_identifier(field_name, value)
    if value not in SOURCE_KINDS:
        raise ValueError(f"{field_name} must be a supported source kind")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_public_identifier(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain supported reason codes")
    return tuple(reason_code for reason_code in allowed if reason_code in normalized)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(value: Mapping[str, object]) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SECONDS_QUANT)


def _require_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative integral Decimal")
    return value.quantize(COUNT_QUANT)


def _require_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SECONDS_QUANT)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANT)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized < ZERO:
        return ZERO
    if quantized > ONE:
        return ONE
    return quantized


def _candidate_digest(candidate_key: str) -> str:
    return _digest_parts(("candidate", candidate_key))


def _source_digest(source_key: str) -> str:
    return _digest_parts(("source", source_key))


def _row_digest_from_values(values: Mapping[str, object]) -> str:
    digest_values = dict(values)
    digest_values.pop("row_digest", None)
    return _canonical_digest(digest_values)


def _derived_validation_digest(values: Mapping[str, object]) -> str:
    digest_values = dict(values)
    digest_values.pop("derived_validation_digest", None)
    return _canonical_digest(digest_values)


def _canonical_digest(values: Mapping[str, object]) -> str:
    payload = _payload_value(values)
    _reject_unsafe_public_payload("digest payload", payload, allow_json_containers=True)
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _digest_parts(parts: tuple[str, str]) -> str:
    digest = sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\x1f")
    return digest.hexdigest()


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
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
            ready[key] = _payload_value(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
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
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FIELD_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")
