"""Readonly source-quorum report for memory-backed research claims."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_MEMORY_CLAIM_SOURCE_QUORUM_REPORT_VERSION = (
    "research-strategy-memory-claim-source-quorum-report"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SIX = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

ROW_REASON_CODES = (
    "source_quorum_pass",
    "source_quorum_watch",
    "source_quorum_block",
    "thin_source_count",
    "thin_independent_sources",
    "high_contradiction_ratio",
    "low_confidence_score",
)
REPORT_REASON_CODES = (
    "source_quorum_report_pass",
    "source_quorum_report_watch",
    "source_quorum_report_block",
    "source_quorum_report_empty",
)

PUBLIC_REPORT_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "claim_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_source_quorum_score",
        "rows",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
)
PUBLIC_ROW_KEYS = frozenset(
    (
        "claim_digest",
        "source_bundle_digest",
        "observed_at",
        "source_count",
        "independent_source_count",
        "contradicting_source_count",
        "support_ratio",
        "confidence_score",
        "source_quorum_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
)
RAW_LEAK_MARKERS = (
    "http://",
    "https://",
    "://",
    "dsn",
    "table",
    "token",
    "secret",
    "private_",
    "candidate-",
    "market-",
    "claim text",
    "source text",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MEMORY_CLAIM_SOURCE_QUORUM_REPORT_VERSION",
    "ResearchStrategyMemoryClaimSourceQuorumReportConfig",
    "ResearchStrategyMemoryClaimSourceQuorumClaim",
    "ResearchStrategyMemoryClaimSourceQuorumRow",
    "ResearchStrategyMemoryClaimSourceQuorumReport",
    "build_research_strategy_memory_claim_source_quorum_report",
    "research_strategy_memory_claim_source_quorum_report_payload",
    "validate_research_strategy_memory_claim_source_quorum_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__bases__ != (_FinalPublicDataclass,):
            raise TypeError("public dataclasses do not support subclassing")
        if not cls.__name__.startswith("ResearchStrategyMemoryClaimSourceQuorum"):
            raise TypeError("public dataclasses do not support subclassing")


@dataclass(frozen=True)
class ResearchStrategyMemoryClaimSourceQuorumReportConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MEMORY_CLAIM_SOURCE_QUORUM_REPORT_VERSION
    )
    minimum_source_count: Decimal = Decimal("3.000000")
    minimum_independent_source_count: Decimal = Decimal("2.000000")
    minimum_support_ratio: Decimal = Decimal("0.800000")
    minimum_confidence_score: Decimal = Decimal("0.700000")
    watch_confidence_floor: Decimal = Decimal("0.500000")
    maximum_contradiction_ratio: Decimal = Decimal("0.250000")
    source_count_weight: Decimal = Decimal("0.250000")
    independent_source_weight: Decimal = Decimal("0.250000")
    support_ratio_weight: Decimal = Decimal("0.250000")
    confidence_score_weight: Decimal = Decimal("0.250000")
    source_shortfall_penalty_weight: Decimal = Decimal("0.150000")
    independent_shortfall_penalty_weight: Decimal = Decimal("0.250000")
    contradiction_penalty_weight: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMemoryClaimSourceQuorumReportConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in ("minimum_source_count", "minimum_independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_support_ratio",
            "minimum_confidence_score",
            "watch_confidence_floor",
            "maximum_contradiction_ratio",
            "source_count_weight",
            "independent_source_weight",
            "support_ratio_weight",
            "confidence_score_weight",
            "source_shortfall_penalty_weight",
            "independent_shortfall_penalty_weight",
            "contradiction_penalty_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_decimal_equal(
            "source quorum score weights",
            self.source_count_weight
            + self.independent_source_weight
            + self.support_ratio_weight
            + self.confidence_score_weight,
            ONE,
        )
        if self.minimum_confidence_score < self.watch_confidence_floor:
            raise ValueError("minimum_confidence_score must be at least watch_confidence_floor")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyMemoryClaimSourceQuorumClaim(_FinalPublicDataclass):
    raw_candidate: str
    raw_market: str
    raw_claim: str
    raw_source_refs: tuple[str, ...]
    source_family_refs: tuple[str, ...]
    observed_at: datetime
    source_count: Decimal
    independent_source_count: Decimal
    contradicting_source_count: Decimal
    confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMemoryClaimSourceQuorumClaim, "claim")
        for field_name in ("raw_candidate", "raw_market", "raw_claim"):
            object.__setattr__(
                self,
                field_name,
                _require_private_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "raw_source_refs",
            _require_private_strings("raw_source_refs", self.raw_source_refs),
        )
        object.__setattr__(
            self,
            "source_family_refs",
            _require_private_strings("source_family_refs", self.source_family_refs),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_count",
            "independent_source_count",
            "contradicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        if self.contradicting_source_count > self.source_count:
            raise ValueError("contradicting_source_count must not exceed source_count")
        _require_hard_flags("claim", self)


@dataclass(frozen=True)
class ResearchStrategyMemoryClaimSourceQuorumRow(_FinalPublicDataclass):
    claim_digest: str
    source_bundle_digest: str
    observed_at: datetime
    source_count: Decimal
    independent_source_count: Decimal
    contradicting_source_count: Decimal
    support_ratio: Decimal
    confidence_score: Decimal
    source_quorum_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMemoryClaimSourceQuorumRow, "row")
        object.__setattr__(
            self,
            "claim_digest",
            _require_digest_reference("claim_digest", self.claim_digest),
        )
        object.__setattr__(
            self,
            "source_bundle_digest",
            _require_digest_reference("source_bundle_digest", self.source_bundle_digest),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_count",
            "independent_source_count",
            "contradicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("support_ratio", "confidence_score", "source_quorum_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        if self.contradicting_source_count > self.source_count:
            raise ValueError("contradicting_source_count must not exceed source_count")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyMemoryClaimSourceQuorumReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_source_quorum_score: Decimal
    rows: tuple[ResearchStrategyMemoryClaimSourceQuorumRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMemoryClaimSourceQuorumReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_status("status", self.status)
        for field_name in ("claim_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_source_quorum_score",
            _require_ratio_decimal(
                "average_source_quorum_score",
                self.average_source_quorum_score,
            ),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _validate_report(self)
        _require_matching_digest(_payload_value(self))


def build_research_strategy_memory_claim_source_quorum_report(
    claims: Iterable[ResearchStrategyMemoryClaimSourceQuorumClaim],
    *,
    config: ResearchStrategyMemoryClaimSourceQuorumReportConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategyMemoryClaimSourceQuorumReport:
    cfg = config or ResearchStrategyMemoryClaimSourceQuorumReportConfig()
    if type(cfg) is not ResearchStrategyMemoryClaimSourceQuorumReportConfig:
        raise ValueError(
            "config must be exactly ResearchStrategyMemoryClaimSourceQuorumReportConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_claims = _normalize_claims(claims)
    for item in normalized_claims:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(sorted((_row_for_claim(item, cfg) for item in normalized_claims), key=_row_key))
    status = _report_status(rows)
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "status": status,
        "claim_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "average_source_quorum_score": _average(row.source_quorum_score for row in rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return ResearchStrategyMemoryClaimSourceQuorumReport(**values)


def research_strategy_memory_claim_source_quorum_report_payload(
    report: ResearchStrategyMemoryClaimSourceQuorumReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyMemoryClaimSourceQuorumReport:
        raise ValueError(
            "report must be exactly ResearchStrategyMemoryClaimSourceQuorumReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_public_payload_shape(payload)
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    return payload


def validate_research_strategy_memory_claim_source_quorum_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _require_public_payload_shape(payload)
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    return True


def _row_for_claim(
    claim: ResearchStrategyMemoryClaimSourceQuorumClaim,
    config: ResearchStrategyMemoryClaimSourceQuorumReportConfig,
) -> ResearchStrategyMemoryClaimSourceQuorumRow:
    source_count_score = _coverage_score(claim.source_count, config.minimum_source_count)
    independent_source_score = _coverage_score(
        claim.independent_source_count,
        config.minimum_independent_source_count,
    )
    contradiction_ratio = _safe_ratio(claim.contradicting_source_count, claim.source_count)
    support_ratio = _clamp_ratio(ONE - contradiction_ratio)
    source_quorum_score = _source_quorum_score(
        source_count_score=source_count_score,
        independent_source_score=independent_source_score,
        support_ratio=support_ratio,
        confidence_score=claim.confidence_score,
        contradiction_ratio=contradiction_ratio,
        config=config,
    )
    status = _row_status(
        source_count=claim.source_count,
        independent_source_count=claim.independent_source_count,
        support_ratio=support_ratio,
        confidence_score=claim.confidence_score,
        contradiction_ratio=contradiction_ratio,
        config=config,
    )
    return ResearchStrategyMemoryClaimSourceQuorumRow(
        claim_digest=_digest_reference(
            (
                ("candidate", claim.raw_candidate),
                ("market", claim.raw_market),
                ("claim", claim.raw_claim),
            )
        ),
        source_bundle_digest=_digest_reference(
            (
                ("sources", claim.raw_source_refs),
                ("families", claim.source_family_refs),
            )
        ),
        observed_at=claim.observed_at,
        source_count=claim.source_count,
        independent_source_count=claim.independent_source_count,
        contradicting_source_count=claim.contradicting_source_count,
        support_ratio=support_ratio,
        confidence_score=claim.confidence_score,
        source_quorum_score=source_quorum_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            source_count=claim.source_count,
            independent_source_count=claim.independent_source_count,
            contradiction_ratio=contradiction_ratio,
            confidence_score=claim.confidence_score,
            config=config,
        ),
    )


def _source_quorum_score(
    *,
    source_count_score: Decimal,
    independent_source_score: Decimal,
    support_ratio: Decimal,
    confidence_score: Decimal,
    contradiction_ratio: Decimal,
    config: ResearchStrategyMemoryClaimSourceQuorumReportConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        weighted_score = _six(
            source_count_score * config.source_count_weight
            + independent_source_score * config.independent_source_weight
            + support_ratio * config.support_ratio_weight
            + confidence_score * config.confidence_score_weight
        )
        source_shortfall_penalty = _six(
            (ONE - source_count_score) * config.source_shortfall_penalty_weight,
        )
        independent_shortfall_penalty = _six(
            (ONE - independent_source_score)
            * config.independent_shortfall_penalty_weight,
        )
        contradiction_penalty = _six(
            max(ZERO, contradiction_ratio - config.maximum_contradiction_ratio)
            * config.contradiction_penalty_weight,
        )
        return _clamp_ratio(
            weighted_score
            - source_shortfall_penalty
            - independent_shortfall_penalty
            - contradiction_penalty,
        )


def _row_status(
    *,
    source_count: Decimal,
    independent_source_count: Decimal,
    support_ratio: Decimal,
    confidence_score: Decimal,
    contradiction_ratio: Decimal,
    config: ResearchStrategyMemoryClaimSourceQuorumReportConfig,
) -> str:
    if (
        independent_source_count < config.minimum_independent_source_count
        or support_ratio < config.minimum_support_ratio
        or confidence_score < config.watch_confidence_floor
        or contradiction_ratio > config.maximum_contradiction_ratio
    ):
        return STATUS_BLOCK
    if (
        source_count < config.minimum_source_count
        or confidence_score < config.minimum_confidence_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    status: str,
    source_count: Decimal,
    independent_source_count: Decimal,
    contradiction_ratio: Decimal,
    confidence_score: Decimal,
    config: ResearchStrategyMemoryClaimSourceQuorumReportConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if status == STATUS_BLOCK:
        codes.append("source_quorum_block")
    elif status == STATUS_WATCH:
        codes.append("source_quorum_watch")
    else:
        codes.append("source_quorum_pass")
    if source_count < config.minimum_source_count:
        codes.append("thin_source_count")
    if independent_source_count < config.minimum_independent_source_count:
        codes.append("thin_independent_sources")
    if contradiction_ratio > config.maximum_contradiction_ratio:
        codes.append("high_contradiction_ratio")
    if confidence_score < config.minimum_confidence_score:
        codes.append("low_confidence_score")
    return _require_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _normalize_claims(
    claims: Iterable[ResearchStrategyMemoryClaimSourceQuorumClaim],
) -> tuple[ResearchStrategyMemoryClaimSourceQuorumClaim, ...]:
    if isinstance(claims, (str, bytes)):
        raise ValueError("claims must be an iterable of claims")
    try:
        normalized = tuple(claims)
    except TypeError as exc:
        raise ValueError("claims must be an iterable of claims") from exc
    for item in normalized:
        if type(item) is not ResearchStrategyMemoryClaimSourceQuorumClaim:
            raise ValueError(
                "claims must contain ResearchStrategyMemoryClaimSourceQuorumClaim",
            )
    digests = tuple(
        _digest_reference(
            (
                ("candidate", item.raw_candidate),
                ("market", item.raw_market),
                ("claim", item.raw_claim),
            )
        )
        for item in normalized
    )
    if len(set(digests)) != len(digests):
        raise ValueError("claims must not contain duplicate claim material")
    return normalized


def _row_key(row: ResearchStrategyMemoryClaimSourceQuorumRow) -> tuple[str, str]:
    return (row.claim_digest, row.source_bundle_digest)


def _status_count(
    rows: tuple[ResearchStrategyMemoryClaimSourceQuorumRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _report_status(rows: tuple[ResearchStrategyMemoryClaimSourceQuorumRow, ...]) -> str:
    if not rows:
        return STATUS_WATCH
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategyMemoryClaimSourceQuorumRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("source_quorum_report_empty",)
    if status == STATUS_BLOCK:
        return ("source_quorum_report_block",)
    if status == STATUS_WATCH:
        return ("source_quorum_report_watch",)
    return ("source_quorum_report_pass",)


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _six(sum(items, ZERO) / Decimal(len(items)))


def _coverage_score(value: Decimal, target: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(value / target)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _validate_report(report: ResearchStrategyMemoryClaimSourceQuorumReport) -> None:
    rows = report.rows
    _require_decimal_equal("claim_count", report.claim_count, _count_decimal(len(rows)))
    _require_decimal_equal("pass_count", report.pass_count, _status_count(rows, STATUS_PASS))
    _require_decimal_equal("watch_count", report.watch_count, _status_count(rows, STATUS_WATCH))
    _require_decimal_equal("block_count", report.block_count, _status_count(rows, STATUS_BLOCK))
    _require_decimal_equal(
        "average_source_quorum_score",
        report.average_source_quorum_score,
        _average(row.source_quorum_score for row in rows),
    )
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.status):
        raise ValueError("reason_codes must match rows")
    if tuple(sorted(rows, key=_row_key)) != rows:
        raise ValueError("rows must be canonical")


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(
            {field.name: getattr(value, field.name) for field in fields(value)}
        )
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is str:
        _require_safe_public_text("public payload value", value)
        return value
    if type(value) is bool or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must use Decimal strings")
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_safe_public_text("public payload key", key)
            payload[key] = _payload_value(item)
        return payload
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_payload(name: str, value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_safe_public_text(f"{name} key", key)
            _reject_unsafe_public_payload(f"{name}.{key}", item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(name, item)
        return
    if type(value) is str:
        _require_safe_public_text(name, value)
        return
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must use Decimal strings")
    if type(value) is bool or value is None:
        return
    raise ValueError("public payload contains unsupported value")


def _require_public_payload_shape(payload: dict[str, Any]) -> None:
    keys = set(payload)
    extra_keys = keys - PUBLIC_REPORT_KEYS
    if extra_keys:
        raise ValueError("unexpected public payload key")
    missing_keys = PUBLIC_REPORT_KEYS - keys
    if missing_keys:
        raise ValueError("missing public payload key")
    if type(payload["rows"]) is not list:
        raise ValueError("payload rows must be a list")
    for row in payload["rows"]:
        if type(row) is not dict:
            raise ValueError("payload rows must be dicts")
        row_keys = set(row)
        if row_keys - PUBLIC_ROW_KEYS:
            raise ValueError("unexpected public payload row key")
        if PUBLIC_ROW_KEYS - row_keys:
            raise ValueError("missing public payload row key")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"payload {flag_name} must be True")
    for row in payload.get("rows", []):
        if type(row) is not dict:
            raise ValueError("payload rows must be dicts")
        for flag_name in ("paper_only", "report_only", "readonly"):
            if row.get(flag_name) is not True:
                raise ValueError(f"payload row {flag_name} must be True")


def _require_hard_flags(name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{name} {flag_name} must be True")


def _require_safe_public_text(name: str, value: str) -> None:
    if value.strip() != value or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{name} must be canonical")
    lower = value.lower()
    if any(marker in lower for marker in RAW_LEAK_MARKERS):
        raise ValueError(f"{name} contains unsafe public surface")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    material = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    return sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _require_matching_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    if payload["derived_validation_digest"] != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")


def _digest_reference(value: object) -> str:
    return f"sha256:{_digest_private_value(value)}"


def _digest_private_value(value: object) -> str:
    return sha256(
        json.dumps(
            _private_json_value(value),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _private_json_value(value: object) -> object:
    if type(value) is str:
        return value
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("private datetime", value).isoformat()
    if type(value) is tuple or type(value) is list:
        return [_private_json_value(item) for item in value]
    return value


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must be non-empty")
    _require_safe_public_text(name, value)
    return value


def _require_private_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must be non-empty")
    if value.strip() != value or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{name} must be canonical")
    return value


def _require_private_strings(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not value:
        raise ValueError(f"{name} must be non-empty")
    return tuple(
        _require_private_string(f"{name} item", item)
        for item in value
    )


def _require_digest_reference(name: str, value: object) -> str:
    digest_reference = _require_private_string(name, value)
    if not digest_reference.startswith("sha256:"):
        raise ValueError(f"{name} must be a sha256 reference")
    _require_digest(name, digest_reference.removeprefix("sha256:"))
    return digest_reference


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 digest")
    return value


def _require_status(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_reason_codes(
    name: str,
    value: object,
    allowed_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not value:
        raise ValueError(f"{name} must be non-empty")
    for code in value:
        if type(code) is not str:
            raise ValueError(f"{name} must contain strings")
        if code not in allowed_codes:
            raise ValueError(f"{name} contains unknown code")
        _require_safe_public_text(name, code)
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must not contain duplicates")
    return value


def _require_rows(
    value: object,
) -> tuple[ResearchStrategyMemoryClaimSourceQuorumRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchStrategyMemoryClaimSourceQuorumRow:
            raise ValueError("rows must contain ResearchStrategyMemoryClaimSourceQuorumRow")
    if tuple(sorted(value, key=_row_key)) != value:
        raise ValueError("rows must be canonical")
    return value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _six(value)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_decimal_equal(name: str, actual: Decimal, expected: Decimal) -> None:
    if actual != _six(expected):
        raise ValueError(f"{name} must equal derived value")


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(SIX)


def _six(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SIX)


def _clamp_ratio(value: Decimal) -> Decimal:
    return _six(min(max(value, ZERO), ONE))


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)
