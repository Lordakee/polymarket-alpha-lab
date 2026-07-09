"""Report-only claim memory quorum router reducer."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_CLAIM_MEMORY_QUORUM_ROUTER_REPORT_CONFIG_VERSION = (
    "research-strategy-claim-memory-quorum-router-report-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
RESEARCH_STRATEGY_CLAIM_MEMORY_QUORUM_ROUTER_REPORT_STATUSES = (
    PASS_STATUS,
    WATCH_STATUS,
    BLOCK_STATUS,
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
HEX_CHARS = frozenset("0123456789abcdef")

CLAIM_CONFIDENCE_BLOCK_REASON = "claim_confidence_block"
CLAIM_CONFIDENCE_WATCH_REASON = "claim_confidence_watch"
MEMORY_MATCH_BLOCK_REASON = "memory_match_block"
MEMORY_MATCH_WATCH_REASON = "memory_match_watch"
QUORUM_AGREEMENT_BLOCK_REASON = "quorum_agreement_block"
QUORUM_AGREEMENT_WATCH_REASON = "quorum_agreement_watch"
CONTRADICTION_PRESSURE_BLOCK_REASON = "contradiction_pressure_block"
CONTRADICTION_PRESSURE_WATCH_REASON = "contradiction_pressure_watch"
EVIDENCE_AGE_BLOCK_REASON = "evidence_age_block"
EVIDENCE_AGE_WATCH_REASON = "evidence_age_watch"
CORROBORATION_BLOCK_REASON = "corroboration_block"
CORROBORATION_WATCH_REASON = "corroboration_watch"
PASS_REASON = "claim_memory_quorum_pass"
EMPTY_REASON = "claim_memory_quorum_empty"
REPORT_BLOCK_REASON = "claim_memory_quorum_report_block"
REPORT_WATCH_REASON = "claim_memory_quorum_report_watch"
REPORT_PASS_REASON = "claim_memory_quorum_report_pass"

STATUS_RANK = {
    BLOCK_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("cand", "idate"),
    _join_parts("mar", "ket"),
    _join_parts("sou", "rce_url"),
    _join_parts("sou", "rce url"),
    _join_parts("sou", "rce_text"),
    _join_parts("sou", "rce text"),
    _join_parts("raw ", "sou", "rce"),
    _join_parts("raw ", "te", "xt"),
    _join_parts("ur", "l"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("au", "th"),
    _join_parts("li", "ve"),
    _join_parts("siz", "ing"),
    _join_parts("recomm", "end"),
    _join_parts("exec", "ute"),
    _join_parts("exec", "ution"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    "://",
    _join_parts("ht", "tp"),
    "www.",
    _join_parts("jd", "bc:"),
    _join_parts("post", "gres:"),
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CLAIM_MEMORY_QUORUM_ROUTER_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_CLAIM_MEMORY_QUORUM_ROUTER_REPORT_STATUSES",
    "ResearchStrategyClaimMemoryQuorumRouterConfig",
    "ResearchStrategyClaimMemoryQuorumRouterInput",
    "ResearchStrategyClaimMemoryQuorumRouterPublicPayloadItem",
    "ResearchStrategyClaimMemoryQuorumRouterReport",
    "ResearchStrategyClaimMemoryQuorumRouterRow",
    "build_research_strategy_claim_memory_quorum_router_report",
    "research_strategy_claim_memory_quorum_router_report_digest",
    "research_strategy_claim_memory_quorum_router_report_payload",
    "validate_research_strategy_claim_memory_quorum_router_report_digest",
    "validate_research_strategy_claim_memory_quorum_router_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyClaimMemoryQuorumRouterConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CLAIM_MEMORY_QUORUM_ROUTER_REPORT_CONFIG_VERSION
    )
    claim_confidence_watch_threshold: Decimal = Decimal("0.700000")
    claim_confidence_block_threshold: Decimal = Decimal("0.550000")
    memory_match_watch_threshold: Decimal = Decimal("0.700000")
    memory_match_block_threshold: Decimal = Decimal("0.500000")
    quorum_agreement_watch_threshold: Decimal = Decimal("0.700000")
    quorum_agreement_block_threshold: Decimal = Decimal("0.500000")
    contradiction_pressure_watch_threshold: Decimal = Decimal("0.150000")
    contradiction_pressure_block_threshold: Decimal = Decimal("0.500000")
    evidence_age_watch_seconds: Decimal = Decimal("86400.000000")
    evidence_age_block_seconds: Decimal = Decimal("172800.000000")
    corroborating_watch_count: Decimal = Decimal("2.000000")
    corroborating_block_count: Decimal = Decimal("1.000000")
    claim_confidence_pass_threshold: Decimal = Decimal("0.800000")
    memory_match_pass_threshold: Decimal = Decimal("0.800000")
    quorum_agreement_pass_threshold: Decimal = Decimal("0.750000")
    corroborating_pass_count: Decimal = Decimal("3.000000")
    contradiction_penalty_weight: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimMemoryQuorumRouterConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CLAIM_MEMORY_QUORUM_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "claim_confidence_watch_threshold",
            "claim_confidence_block_threshold",
            "memory_match_watch_threshold",
            "memory_match_block_threshold",
            "quorum_agreement_watch_threshold",
            "quorum_agreement_block_threshold",
            "contradiction_pressure_watch_threshold",
            "contradiction_pressure_block_threshold",
            "claim_confidence_pass_threshold",
            "memory_match_pass_threshold",
            "quorum_agreement_pass_threshold",
            "contradiction_penalty_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_age_watch_seconds",
            "evidence_age_block_seconds",
            "corroborating_watch_count",
            "corroborating_block_count",
            "corroborating_pass_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_descending_threshold(
            "claim_confidence_threshold",
            self.claim_confidence_watch_threshold,
            self.claim_confidence_block_threshold,
        )
        _require_descending_threshold(
            "memory_match_threshold",
            self.memory_match_watch_threshold,
            self.memory_match_block_threshold,
        )
        _require_descending_threshold(
            "quorum_agreement_threshold",
            self.quorum_agreement_watch_threshold,
            self.quorum_agreement_block_threshold,
        )
        _require_ascending_threshold(
            "contradiction_pressure_threshold",
            self.contradiction_pressure_watch_threshold,
            self.contradiction_pressure_block_threshold,
        )
        _require_ascending_threshold(
            "evidence_age_threshold",
            self.evidence_age_watch_seconds,
            self.evidence_age_block_seconds,
        )
        _require_descending_threshold(
            "corroborating_count_threshold",
            self.corroborating_watch_count,
            self.corroborating_block_count,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyClaimMemoryQuorumRouterInput(_FinalPublicDataclass):
    claim_digest: str
    memory_digest: str
    quorum_digest: str
    observed_at: datetime
    claim_confidence_score: Decimal
    memory_match_score: Decimal
    quorum_agreement_ratio: Decimal
    contradiction_pressure: Decimal
    evidence_age_seconds: Decimal
    corroborating_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimMemoryQuorumRouterInput, "input")
        _require_sha256("claim_digest", self.claim_digest)
        _require_sha256("memory_digest", self.memory_digest)
        _require_sha256("quorum_digest", self.quorum_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "claim_confidence_score",
            "memory_match_score",
            "quorum_agreement_ratio",
            "contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _require_nonnegative_decimal(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "corroborating_count",
            _require_nonnegative_decimal(
                "corroborating_count",
                self.corroborating_count,
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyClaimMemoryQuorumRouterPublicPayloadItem(_FinalPublicDataclass):
    key: str
    value: str

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyClaimMemoryQuorumRouterPublicPayloadItem,
            "public_payload_item",
        )
        object.__setattr__(self, "key", _require_public_string("key", self.key))
        object.__setattr__(self, "value", _require_public_string("value", self.value))
        _reject_unsafe_public_payload("public_payload_item", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyClaimMemoryQuorumRouterRow(_FinalPublicDataclass):
    rank: Decimal
    claim_digest: str
    memory_digest: str
    quorum_digest: str
    status: str
    observed_at: datetime
    claim_confidence_score: Decimal
    memory_match_score: Decimal
    quorum_agreement_ratio: Decimal
    contradiction_pressure: Decimal
    evidence_age_seconds: Decimal
    corroborating_count: Decimal
    readiness_score: Decimal
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimMemoryQuorumRouterRow, "row")
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        _require_sha256("claim_digest", self.claim_digest)
        _require_sha256("memory_digest", self.memory_digest)
        _require_sha256("quorum_digest", self.quorum_digest)
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "claim_confidence_score",
            "memory_match_score",
            "quorum_agreement_ratio",
            "contradiction_pressure",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _require_nonnegative_decimal(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "corroborating_count",
            _require_nonnegative_decimal(
                "corroborating_count",
                self.corroborating_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyClaimMemoryQuorumRouterReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal
    max_contradiction_pressure: Decimal
    stale_evidence_count: Decimal
    rows: tuple[ResearchStrategyClaimMemoryQuorumRouterRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchStrategyClaimMemoryQuorumRouterPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimMemoryQuorumRouterReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CLAIM_MEMORY_QUORUM_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(self, "status", _require_status("status", self.status))
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_score",
            "max_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "rows",
            _require_tuple_of("rows", self.rows, ResearchStrategyClaimMemoryQuorumRouterRow),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "public_payload",
            _require_tuple_of(
                "public_payload",
                self.public_payload,
                ResearchStrategyClaimMemoryQuorumRouterPublicPayloadItem,
            ),
        )
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        expected_digest = research_strategy_claim_memory_quorum_router_report_digest(self)
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _reject_unsafe_public_payload("report", self.payload)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_claim_memory_quorum_router_report_payload(self)


def build_research_strategy_claim_memory_quorum_router_report(
    inputs: Iterable[ResearchStrategyClaimMemoryQuorumRouterInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyClaimMemoryQuorumRouterConfig | None = None,
    public_payload: Iterable[
        ResearchStrategyClaimMemoryQuorumRouterPublicPayloadItem
    ] = (),
) -> ResearchStrategyClaimMemoryQuorumRouterReport:
    active_config = config or ResearchStrategyClaimMemoryQuorumRouterConfig()
    _require_exact_type(
        active_config,
        ResearchStrategyClaimMemoryQuorumRouterConfig,
        "config",
    )
    generated_at = _as_utc("generated_at", generated_at)
    input_rows = _require_tuple_of(
        "inputs",
        tuple(inputs),
        ResearchStrategyClaimMemoryQuorumRouterInput,
    )
    payload_items = _require_tuple_of(
        "public_payload",
        tuple(public_payload),
        ResearchStrategyClaimMemoryQuorumRouterPublicPayloadItem,
    )
    rows = _build_rows(input_rows, active_config)
    row_count = _decimal_count(rows)
    pass_count = _decimal_count(row for row in rows if row.status == PASS_STATUS)
    watch_count = _decimal_count(row for row in rows if row.status == WATCH_STATUS)
    block_count = _decimal_count(row for row in rows if row.status == BLOCK_STATUS)
    if block_count > ZERO:
        status = BLOCK_STATUS
        report_reason = REPORT_BLOCK_REASON
    elif watch_count > ZERO:
        status = WATCH_STATUS
        report_reason = REPORT_WATCH_REASON
    else:
        status = PASS_STATUS
        report_reason = EMPTY_REASON if row_count == ZERO else REPORT_PASS_REASON
    average_readiness_score = _average(
        tuple(row.readiness_score for row in rows),
    )
    max_contradiction_pressure = max(
        (row.contradiction_pressure for row in rows),
        default=ZERO,
    )
    stale_evidence_count = _decimal_count(
        row
        for row in rows
        if row.evidence_age_seconds >= active_config.evidence_age_watch_seconds
    )
    reason_codes = _dedupe_reason_codes(
        (report_reason,)
        + tuple(reason for row in rows for reason in row.reason_codes),
    )
    report_without_digest = ResearchStrategyClaimMemoryQuorumRouterReport.__new__(
        ResearchStrategyClaimMemoryQuorumRouterReport,
    )
    object.__setattr__(report_without_digest, "generated_at", generated_at)
    object.__setattr__(report_without_digest, "config_version", active_config.config_version)
    object.__setattr__(report_without_digest, "status", status)
    object.__setattr__(report_without_digest, "row_count", row_count)
    object.__setattr__(report_without_digest, "pass_count", pass_count)
    object.__setattr__(report_without_digest, "watch_count", watch_count)
    object.__setattr__(report_without_digest, "block_count", block_count)
    object.__setattr__(
        report_without_digest,
        "average_readiness_score",
        average_readiness_score,
    )
    object.__setattr__(
        report_without_digest,
        "max_contradiction_pressure",
        max_contradiction_pressure,
    )
    object.__setattr__(report_without_digest, "stale_evidence_count", stale_evidence_count)
    object.__setattr__(report_without_digest, "rows", rows)
    object.__setattr__(report_without_digest, "reason_codes", reason_codes)
    object.__setattr__(report_without_digest, "public_payload", payload_items)
    object.__setattr__(report_without_digest, "paper_only", True)
    object.__setattr__(report_without_digest, "report_only", True)
    object.__setattr__(report_without_digest, "readonly", True)
    digest = research_strategy_claim_memory_quorum_router_report_digest(
        report_without_digest,
    )
    return ResearchStrategyClaimMemoryQuorumRouterReport(
        generated_at=generated_at,
        config_version=active_config.config_version,
        status=status,
        row_count=row_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_readiness_score=average_readiness_score,
        max_contradiction_pressure=max_contradiction_pressure,
        stale_evidence_count=stale_evidence_count,
        rows=rows,
        reason_codes=reason_codes,
        public_payload=payload_items,
        derived_validation_digest=digest,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_strategy_claim_memory_quorum_router_report_payload(
    report: ResearchStrategyClaimMemoryQuorumRouterReport,
) -> dict[str, object]:
    payload = _report_payload(report, include_digest=True)
    _reject_unsafe_public_payload("report_payload", payload)
    return payload


def research_strategy_claim_memory_quorum_router_report_digest(
    report: ResearchStrategyClaimMemoryQuorumRouterReport,
) -> str:
    return _digest_payload(_report_payload(report, include_digest=False))


def validate_research_strategy_claim_memory_quorum_router_report_digest(
    report: ResearchStrategyClaimMemoryQuorumRouterReport,
) -> bool:
    expected_digest = research_strategy_claim_memory_quorum_router_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return True


def validate_research_strategy_claim_memory_quorum_router_report_payload(
    payload: Mapping[str, object],
) -> bool:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    digest_value = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest_value)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    expected_digest = _digest_payload(unsigned)
    if digest_value != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    _validate_public_payload_contract(payload)
    _reject_unsafe_public_payload("payload", payload)
    return True


def _validate_public_payload_contract(payload: Mapping[str, object]) -> None:
    _require_payload_true_flag(payload, "paper_only")
    _require_payload_true_flag(payload, "report_only")
    _require_payload_true_flag(payload, "readonly")
    _require_status("payload.status", payload.get("status"))
    rows = payload.get("rows")
    if type(rows) not in (tuple, list):
        raise ValueError("payload.rows must be a list or tuple")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("payload.rows entries must be mappings")
        _require_status("payload.rows.status", row.get("status"))


def _require_payload_true_flag(
    payload: Mapping[str, object],
    flag_name: str,
) -> None:
    if payload.get(flag_name) is not True:
        raise ValueError(f"payload.{flag_name} must be True")


def _build_rows(
    inputs: tuple[ResearchStrategyClaimMemoryQuorumRouterInput, ...],
    config: ResearchStrategyClaimMemoryQuorumRouterConfig,
) -> tuple[ResearchStrategyClaimMemoryQuorumRouterRow, ...]:
    scored: list[tuple[str, Decimal, ResearchStrategyClaimMemoryQuorumRouterInput, tuple[str, ...]]] = []
    for row in inputs:
        reason_codes = _row_reason_codes(row, config)
        status = _status_from_reasons(reason_codes)
        readiness_score = _readiness_score(row, config)
        scored.append((status, readiness_score, row, reason_codes))
    scored.sort(
        key=lambda item: (
            STATUS_RANK[item[0]],
            item[1],
            item[2].claim_digest,
            item[2].memory_digest,
            item[2].quorum_digest,
        ),
    )
    rows: list[ResearchStrategyClaimMemoryQuorumRouterRow] = []
    for index, (status, readiness_score, row, reason_codes) in enumerate(scored, start=1):
        rows.append(
            ResearchStrategyClaimMemoryQuorumRouterRow(
                rank=_decimal_from_index(index),
                claim_digest=row.claim_digest,
                memory_digest=row.memory_digest,
                quorum_digest=row.quorum_digest,
                status=status,
                observed_at=row.observed_at,
                claim_confidence_score=row.claim_confidence_score,
                memory_match_score=row.memory_match_score,
                quorum_agreement_ratio=row.quorum_agreement_ratio,
                contradiction_pressure=row.contradiction_pressure,
                evidence_age_seconds=row.evidence_age_seconds,
                corroborating_count=row.corroborating_count,
                readiness_score=readiness_score,
                reason_codes=reason_codes,
            ),
        )
    return tuple(rows)


def _row_reason_codes(
    row: ResearchStrategyClaimMemoryQuorumRouterInput,
    config: ResearchStrategyClaimMemoryQuorumRouterConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_low_score_reason(
        reasons,
        row.claim_confidence_score,
        config.claim_confidence_watch_threshold,
        config.claim_confidence_block_threshold,
        CLAIM_CONFIDENCE_WATCH_REASON,
        CLAIM_CONFIDENCE_BLOCK_REASON,
    )
    _append_low_score_reason(
        reasons,
        row.memory_match_score,
        config.memory_match_watch_threshold,
        config.memory_match_block_threshold,
        MEMORY_MATCH_WATCH_REASON,
        MEMORY_MATCH_BLOCK_REASON,
    )
    _append_low_score_reason(
        reasons,
        row.quorum_agreement_ratio,
        config.quorum_agreement_watch_threshold,
        config.quorum_agreement_block_threshold,
        QUORUM_AGREEMENT_WATCH_REASON,
        QUORUM_AGREEMENT_BLOCK_REASON,
    )
    _append_high_score_reason(
        reasons,
        row.contradiction_pressure,
        config.contradiction_pressure_watch_threshold,
        config.contradiction_pressure_block_threshold,
        CONTRADICTION_PRESSURE_WATCH_REASON,
        CONTRADICTION_PRESSURE_BLOCK_REASON,
    )
    _append_high_score_reason(
        reasons,
        row.evidence_age_seconds,
        config.evidence_age_watch_seconds,
        config.evidence_age_block_seconds,
        EVIDENCE_AGE_WATCH_REASON,
        EVIDENCE_AGE_BLOCK_REASON,
    )
    _append_low_score_reason(
        reasons,
        row.corroborating_count,
        config.corroborating_watch_count,
        config.corroborating_block_count,
        CORROBORATION_WATCH_REASON,
        CORROBORATION_BLOCK_REASON,
    )
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(reasons)


def _append_low_score_reason(
    reasons: list[str],
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value <= block_threshold:
        reasons.append(block_reason)
    elif value <= watch_threshold:
        reasons.append(watch_reason)


def _append_high_score_reason(
    reasons: list[str],
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value >= block_threshold:
        reasons.append(block_reason)
    elif value >= watch_threshold:
        reasons.append(watch_reason)


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return BLOCK_STATUS
    if any(reason.endswith("_watch") for reason in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _readiness_score(
    row: ResearchStrategyClaimMemoryQuorumRouterInput,
    config: ResearchStrategyClaimMemoryQuorumRouterConfig,
) -> Decimal:
    positive_base = min(
        ONE,
        _capped_ratio(row.claim_confidence_score, config.claim_confidence_pass_threshold),
        _capped_ratio(row.memory_match_score, config.memory_match_pass_threshold),
        _capped_ratio(row.quorum_agreement_ratio, config.quorum_agreement_pass_threshold),
        _capped_ratio(row.corroborating_count, config.corroborating_pass_count),
        _freshness_score(row.evidence_age_seconds, config),
    )
    with localcontext(DECIMAL_CONTEXT):
        penalty = row.contradiction_pressure * config.contradiction_penalty_weight
        return _quantize(min(ONE, max(ZERO, positive_base - penalty)))


def _freshness_score(
    evidence_age_seconds: Decimal,
    config: ResearchStrategyClaimMemoryQuorumRouterConfig,
) -> Decimal:
    if evidence_age_seconds <= config.evidence_age_watch_seconds:
        return ONE
    if evidence_age_seconds >= config.evidence_age_block_seconds:
        return ZERO
    span = config.evidence_age_block_seconds - config.evidence_age_watch_seconds
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(ONE - ((evidence_age_seconds - config.evidence_age_watch_seconds) / span))


def _capped_ratio(value: Decimal, target: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(min(ONE, max(ZERO, value / target)))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / _decimal_from_index(len(values)))


def _report_payload(
    report: ResearchStrategyClaimMemoryQuorumRouterReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "generated_at": _payload_value(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "row_count": _payload_value(report.row_count),
        "pass_count": _payload_value(report.pass_count),
        "watch_count": _payload_value(report.watch_count),
        "block_count": _payload_value(report.block_count),
        "average_readiness_score": _payload_value(report.average_readiness_score),
        "max_contradiction_pressure": _payload_value(report.max_contradiction_pressure),
        "stale_evidence_count": _payload_value(report.stale_evidence_count),
        "rows": _payload_value(report.rows),
        "reason_codes": report.reason_codes,
        "public_payload": _payload_value(report.public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _digest_payload(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return _format_decimal(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return tuple(_payload_value(item) for item in value)
    if isinstance(value, list):
        return tuple(_payload_value(item) for item in value)
    if isinstance(value, dict):
        return {
            str(key): _payload_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    return value


def _as_utc(label: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise TypeError(f"{label} must be {expected_type.__name__}")


def _require_public_string(label: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{label} must be a non-empty canonical string")
    return value


def _require_sha256(label: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a sha256 hex digest")
    if len(value) != SHA256_HEX_LENGTH or any(char not in HEX_CHARS for char in value):
        raise ValueError(f"{label} must be a sha256 hex digest")


def _require_status(label: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_STRATEGY_CLAIM_MEMORY_QUORUM_ROUTER_REPORT_STATUSES:
        raise ValueError(f"{label} must be pass, watch, or block")
    return value


def _require_reason_codes(label: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{label} must be a tuple")
    if not value:
        raise ValueError(f"{label} must not be empty")
    normalized: list[str] = []
    for reason in value:
        normalized.append(_require_public_string(label, reason))
    return tuple(normalized)


def _require_tuple_of(label: str, value: object, expected_type: type[Any]) -> tuple[Any, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{label} must be a tuple")
    for item in value:
        if type(item) is not expected_type:
            raise TypeError(f"{label} entries must be {expected_type.__name__}")
    return value


def _require_decimal(label: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(label: str, value: object) -> Decimal:
    normalized = _require_decimal(label, value)
    if normalized < ZERO:
        raise ValueError(f"{label} must be nonnegative")
    return normalized


def _require_positive_decimal(label: str, value: object) -> Decimal:
    normalized = _require_decimal(label, value)
    if normalized <= ZERO:
        raise ValueError(f"{label} must be positive")
    return normalized


def _require_ratio_decimal(label: str, value: object) -> Decimal:
    normalized = _require_decimal(label, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{label} must be between 0 and 1")
    return normalized


def _require_descending_threshold(label: str, high_value: Decimal, low_value: Decimal) -> None:
    if high_value <= low_value:
        raise ValueError(f"{label} watch threshold must exceed block threshold")


def _require_ascending_threshold(label: str, low_value: Decimal, high_value: Decimal) -> None:
    if low_value >= high_value:
        raise ValueError(f"{label} watch threshold must be below block threshold")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{label}.{flag_name} must be True")


def _decimal_count(values: Iterable[object]) -> Decimal:
    return _decimal_from_index(sum(1 for _ in values))


def _decimal_from_index(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _format_decimal(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _dedupe_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for reason in reason_codes:
        if reason not in seen:
            seen.add(reason)
            deduped.append(reason)
    return tuple(deduped)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_unsafe_text(f"{label}.key", str(key))
            _reject_unsafe_public_payload(f"{label}.{key}", item)
    elif isinstance(value, tuple | list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, str):
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{label} contains unsafe public payload content")
