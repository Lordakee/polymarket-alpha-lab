"""Read-only report for specialist claim edge decay."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any, final


DEFAULT_RESEARCH_STRATEGY_SPECIALIST_CLAIM_EDGE_DECAY_REPORT_CONFIG_VERSION = (
    "research-strategy-specialist-claim-edge-decay-report-v0"
)

STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "claim_edge_survives",
    "claim_edge_decayed",
    "claim_age_stale_watch",
    "evidence_refresh_stale_watch",
    "specialist_confidence_watch",
    "source_quorum_watch",
    "contradiction_watch",
    "contradiction_block",
)
REPORT_REASON_CODES = (
    "claim_edge_decay_clear",
    "claim_edge_decay_watch",
    "claim_edge_decay_block",
    "claim_age_stale_watch",
    "evidence_refresh_stale_watch",
    "specialist_confidence_watch",
    "source_quorum_watch",
    "contradiction_watch",
    "contradiction_block",
)
REPORT_ROW_REASON_CODES = (
    "claim_age_stale_watch",
    "evidence_refresh_stale_watch",
    "specialist_confidence_watch",
    "source_quorum_watch",
    "contradiction_watch",
    "contradiction_block",
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
REDACTED_CLAIM_REF_PREFIX = "claim_ref_"
REDACTED_DIGEST_LENGTH = 16

UNSAFE_PUBLIC_FIELD_FRAGMENTS = (
    "candidate",
    "condition",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "url",
    "text",
    "d" + "sn",
    "table",
    "token",
    "auth",
    "api_key",
    "secret",
    "net" + "work",
    "requ" + "ests",
    "sock" + "et",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "li" + "ve",
    "position",
    "siz" + "ing",
    "size",
    "rec" + "ommend",
    "exec" + "ute",
    "exec" + "ution",
    "buy",
    "sell",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "candidate",
    "condition",
    "market_id",
    "market_slug",
    "question",
    "url",
    "raw-",
    "token",
    "secret",
    "private",
    "d" + "sn",
    "auth",
    "api_key",
    "net" + "work",
    "requ" + "ests",
    "sock" + "et",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "li" + "ve",
    "position",
    "siz" + "ing",
    "size",
    "rec" + "ommend",
    "exec" + "ute",
    "exec" + "ution",
    "buy",
    "sell",
)
PUBLIC_REASON_CODES = tuple(dict.fromkeys(REPORT_REASON_CODES + ROW_REASON_CODES))
PUBLIC_REPORT_FIELDS = (
    "generated_at",
    "config_version",
    "source_row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "surviving_edge_count",
    "mean_decayed_edge_probability",
    "min_decayed_edge_probability",
    "status",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "payload_sha256",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_ROW_FIELDS = (
    "redacted_claim_ref",
    "observed_at",
    "specialist_probability",
    "market_probability",
    "raw_edge_probability",
    "claim_age_hours",
    "claim_age_decay_probability",
    "evidence_refresh_age_hours",
    "evidence_refresh_decay_probability",
    "specialist_confidence_score",
    "confidence_decay_probability",
    "source_quorum_score",
    "source_quorum_decay_probability",
    "contradiction_score",
    "contradiction_decay_probability",
    "decayed_edge_probability",
    "claim_edge_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_COUNT_FIELDS = (
    "source_row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "surviving_edge_count",
)
PUBLIC_REPORT_RATIO_FIELDS = (
    "mean_decayed_edge_probability",
    "min_decayed_edge_probability",
)
PUBLIC_ROW_PROBABILITY_FIELDS = (
    "specialist_probability",
    "market_probability",
    "claim_age_decay_probability",
    "evidence_refresh_decay_probability",
    "specialist_confidence_score",
    "confidence_decay_probability",
    "source_quorum_score",
    "source_quorum_decay_probability",
    "contradiction_score",
    "contradiction_decay_probability",
)
PUBLIC_ROW_VALUE_FIELDS = (
    "raw_edge_probability",
    "decayed_edge_probability",
)
PUBLIC_ROW_AGE_FIELDS = (
    "claim_age_hours",
    "evidence_refresh_age_hours",
)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySpecialistClaimEdgeDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_SPECIALIST_CLAIM_EDGE_DECAY_REPORT_CONFIG_VERSION
    )
    pass_edge_floor: Decimal = Decimal("0.050000")
    watch_edge_floor: Decimal = Decimal("0.015000")
    max_claim_age_hours: Decimal = Decimal("36.000000")
    max_evidence_refresh_age_hours: Decimal = Decimal("12.000000")
    claim_age_decay_cap: Decimal = Decimal("0.030000")
    evidence_refresh_decay_cap: Decimal = Decimal("0.020000")
    confidence_decay_cap: Decimal = Decimal("0.020000")
    source_quorum_decay_cap: Decimal = Decimal("0.020000")
    contradiction_decay_cap: Decimal = Decimal("0.040000")
    specialist_confidence_watch_floor: Decimal = Decimal("0.500000")
    source_quorum_watch_floor: Decimal = Decimal("0.500000")
    contradiction_watch_score: Decimal = Decimal("0.350000")
    contradiction_block_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySpecialistClaimEdgeDecayConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SPECIALIST_CLAIM_EDGE_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_edge_floor",
            "watch_edge_floor",
            "claim_age_decay_cap",
            "evidence_refresh_decay_cap",
            "confidence_decay_cap",
            "source_quorum_decay_cap",
            "contradiction_decay_cap",
            "specialist_confidence_watch_floor",
            "source_quorum_watch_floor",
            "contradiction_watch_score",
            "contradiction_block_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_claim_age_hours", "max_evidence_refresh_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
            if getattr(self, field_name) == ZERO_RATIO:
                raise ValueError(f"{field_name} must be positive")
        if self.watch_edge_floor > self.pass_edge_floor:
            raise ValueError("watch_edge_floor must not exceed pass_edge_floor")
        if self.contradiction_watch_score > self.contradiction_block_score:
            raise ValueError(
                "contradiction_watch_score must not exceed contradiction_block_score",
            )
        _require_hard_flags("config", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySpecialistClaimEdgeDecayObservation:
    claim_ref: str
    observed_at: datetime
    specialist_probability: Decimal
    market_probability: Decimal
    claim_age_hours: Decimal
    evidence_refresh_age_hours: Decimal
    specialist_confidence_score: Decimal
    source_quorum_score: Decimal
    contradiction_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySpecialistClaimEdgeDecayObservation,
            "observation",
        )
        _require_canonical_string("claim_ref", self.claim_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("specialist_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("claim_age_hours", "evidence_refresh_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "specialist_confidence_score",
            "source_quorum_score",
            "contradiction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySpecialistClaimEdgeDecayRow:
    redacted_claim_ref: str
    observed_at: datetime
    specialist_probability: Decimal
    market_probability: Decimal
    raw_edge_probability: Decimal
    claim_age_hours: Decimal
    claim_age_decay_probability: Decimal
    evidence_refresh_age_hours: Decimal
    evidence_refresh_decay_probability: Decimal
    specialist_confidence_score: Decimal
    confidence_decay_probability: Decimal
    source_quorum_score: Decimal
    source_quorum_decay_probability: Decimal
    contradiction_score: Decimal
    contradiction_decay_probability: Decimal
    decayed_edge_probability: Decimal
    claim_edge_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySpecialistClaimEdgeDecayRow, "row")
        _require_redacted_claim_ref(self.redacted_claim_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "specialist_probability",
            "market_probability",
            "raw_edge_probability",
            "claim_age_hours",
            "claim_age_decay_probability",
            "evidence_refresh_age_hours",
            "evidence_refresh_decay_probability",
            "specialist_confidence_score",
            "confidence_decay_probability",
            "source_quorum_score",
            "source_quorum_decay_probability",
            "contradiction_score",
            "contradiction_decay_probability",
            "decayed_edge_probability",
        ):
            if field_name in ("claim_age_hours", "evidence_refresh_age_hours"):
                normalized = _normalize_nonnegative_value(
                    field_name,
                    getattr(self, field_name),
                )
            elif field_name in (
                "raw_edge_probability",
                "decayed_edge_probability",
            ):
                normalized = _normalize_value(field_name, getattr(self, field_name))
            else:
                normalized = _normalize_probability(field_name, getattr(self, field_name))
            object.__setattr__(self, field_name, normalized)
        _require_member("claim_edge_status", self.claim_edge_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySpecialistClaimEdgeDecayReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    surviving_edge_count: Decimal
    mean_decayed_edge_probability: Decimal
    min_decayed_edge_probability: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchStrategySpecialistClaimEdgeDecayRow, ...]
    payload_sha256: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySpecialistClaimEdgeDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SPECIALIST_CLAIM_EDGE_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "surviving_edge_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_decayed_edge_probability",
            "min_decayed_edge_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_value(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _payload_digest_without_digest(_json_ready(self))
        if self.payload_sha256:
            _require_sha256("payload_sha256", self.payload_sha256)
            if self.payload_sha256 != expected_digest:
                raise ValueError("payload_sha256 does not match report payload")
        else:
            object.__setattr__(self, "payload_sha256", expected_digest)


def build_research_strategy_specialist_claim_edge_decay_report(
    observations: list[ResearchStrategySpecialistClaimEdgeDecayObservation]
    | tuple[ResearchStrategySpecialistClaimEdgeDecayObservation, ...],
    *,
    config: ResearchStrategySpecialistClaimEdgeDecayConfig,
    generated_at: datetime,
) -> ResearchStrategySpecialistClaimEdgeDecayReport:
    if type(config) is not ResearchStrategySpecialistClaimEdgeDecayConfig:
        raise ValueError(
            "config must be a ResearchStrategySpecialistClaimEdgeDecayConfig",
        )
    _require_hard_flags("config", config)
    source_rows = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (_row_from_observation(row, config) for row in source_rows),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategySpecialistClaimEdgeDecayReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        source_row_count=_count(len(source_rows)),
        pass_count=_count(sum(1 for row in rows if row.claim_edge_status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.claim_edge_status == "watch")),
        block_count=_count(sum(1 for row in rows if row.claim_edge_status == "block")),
        surviving_edge_count=_count(
            sum(
                1
                for row in rows
                if row.decayed_edge_probability >= config.pass_edge_floor
            ),
        ),
        mean_decayed_edge_probability=_mean(
            tuple(row.decayed_edge_probability for row in rows),
        ),
        min_decayed_edge_probability=_min_or_zero(
            tuple(row.decayed_edge_probability for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_specialist_claim_edge_decay_report_payload(
    report: ResearchStrategySpecialistClaimEdgeDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategySpecialistClaimEdgeDecayReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_keys("payload", report)
        _reject_unsafe_public_values("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategySpecialistClaimEdgeDecayReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_keys("payload", payload)
    _reject_unsafe_public_values("payload", payload)
    validate_research_strategy_specialist_claim_edge_decay_report_payload(payload)
    return payload


def research_strategy_specialist_claim_edge_decay_report_json(
    report: ResearchStrategySpecialistClaimEdgeDecayReport | dict[str, Any],
) -> str:
    payload = research_strategy_specialist_claim_edge_decay_report_payload(report)
    return _canonical_json(payload)


def validate_research_strategy_specialist_claim_edge_decay_report_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_keys("payload", payload)
    _reject_unsafe_public_values("payload", payload)
    _validate_public_payload_schema(payload)
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    digest = ready.get("payload_sha256")
    _require_sha256("payload_sha256", digest)
    expected_digest = _payload_digest_without_digest(ready)
    if digest != expected_digest:
        raise ValueError("payload_sha256 does not match report payload")
    _report_from_public_payload(ready)


@final
@dataclass(frozen=True, slots=True)
class _DictFlags:
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


def _normalize_observations(
    observations: list[ResearchStrategySpecialistClaimEdgeDecayObservation]
    | tuple[ResearchStrategySpecialistClaimEdgeDecayObservation, ...],
) -> tuple[ResearchStrategySpecialistClaimEdgeDecayObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    rows = tuple(observations)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategySpecialistClaimEdgeDecayObservation:
            raise ValueError(
                "observations must contain "
                "ResearchStrategySpecialistClaimEdgeDecayObservation values",
            )
        _require_hard_flags("observation", row)
        if row.claim_ref in seen:
            raise ValueError("observations must not contain duplicate claim_ref values")
        seen.add(row.claim_ref)
    return rows


def _row_from_observation(
    row: ResearchStrategySpecialistClaimEdgeDecayObservation,
    config: ResearchStrategySpecialistClaimEdgeDecayConfig,
) -> ResearchStrategySpecialistClaimEdgeDecayRow:
    raw_edge = _quantize_ratio(row.specialist_probability - row.market_probability)
    claim_decay = _claim_age_decay(row.claim_age_hours, config)
    refresh_decay = _evidence_refresh_decay(row.evidence_refresh_age_hours, config)
    confidence_decay = _confidence_decay(row.specialist_confidence_score, config)
    quorum_decay = _source_quorum_decay(row.source_quorum_score, config)
    contradiction_decay = _contradiction_decay(row.contradiction_score, config)
    decayed_edge = _quantize_ratio(
        raw_edge
        - claim_decay
        - refresh_decay
        - confidence_decay
        - quorum_decay
        - contradiction_decay,
    )
    return ResearchStrategySpecialistClaimEdgeDecayRow(
        redacted_claim_ref=_redacted_claim_ref(row.claim_ref),
        observed_at=row.observed_at,
        specialist_probability=row.specialist_probability,
        market_probability=row.market_probability,
        raw_edge_probability=raw_edge,
        claim_age_hours=row.claim_age_hours,
        claim_age_decay_probability=claim_decay,
        evidence_refresh_age_hours=row.evidence_refresh_age_hours,
        evidence_refresh_decay_probability=refresh_decay,
        specialist_confidence_score=row.specialist_confidence_score,
        confidence_decay_probability=confidence_decay,
        source_quorum_score=row.source_quorum_score,
        source_quorum_decay_probability=quorum_decay,
        contradiction_score=row.contradiction_score,
        contradiction_decay_probability=contradiction_decay,
        decayed_edge_probability=decayed_edge,
        claim_edge_status=_row_status(decayed_edge, row, config),
        reason_codes=_row_reason_codes(decayed_edge, row, config),
    )


def _row_status(
    decayed_edge: Decimal,
    row: ResearchStrategySpecialistClaimEdgeDecayObservation,
    config: ResearchStrategySpecialistClaimEdgeDecayConfig,
) -> str:
    if decayed_edge < config.watch_edge_floor:
        return "block"
    if row.contradiction_score >= config.contradiction_block_score:
        return "block"
    if decayed_edge < config.pass_edge_floor:
        return "watch"
    if row.claim_age_hours > config.max_claim_age_hours:
        return "watch"
    if row.evidence_refresh_age_hours > config.max_evidence_refresh_age_hours:
        return "watch"
    if row.specialist_confidence_score < config.specialist_confidence_watch_floor:
        return "watch"
    if row.source_quorum_score < config.source_quorum_watch_floor:
        return "watch"
    if row.contradiction_score >= config.contradiction_watch_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    decayed_edge: Decimal,
    row: ResearchStrategySpecialistClaimEdgeDecayObservation,
    config: ResearchStrategySpecialistClaimEdgeDecayConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if decayed_edge >= config.pass_edge_floor:
        codes.append("claim_edge_survives")
    else:
        codes.append("claim_edge_decayed")
    if row.claim_age_hours > config.max_claim_age_hours:
        codes.append("claim_age_stale_watch")
    if row.evidence_refresh_age_hours > config.max_evidence_refresh_age_hours:
        codes.append("evidence_refresh_stale_watch")
    if row.specialist_confidence_score < config.specialist_confidence_watch_floor:
        codes.append("specialist_confidence_watch")
    if row.source_quorum_score < config.source_quorum_watch_floor:
        codes.append("source_quorum_watch")
    if row.contradiction_score >= config.contradiction_block_score:
        codes.append("contradiction_block")
    elif row.contradiction_score >= config.contradiction_watch_score:
        codes.append("contradiction_watch")
    return tuple(codes)


def _report_status(
    rows: tuple[ResearchStrategySpecialistClaimEdgeDecayRow, ...],
) -> str:
    if any(row.claim_edge_status == "block" for row in rows):
        return "block"
    if any(row.claim_edge_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategySpecialistClaimEdgeDecayRow, ...],
) -> tuple[str, ...]:
    if not rows or all(row.claim_edge_status == "pass" for row in rows):
        return ("claim_edge_decay_clear",)
    codes: list[str] = []
    if any(row.claim_edge_status == "block" for row in rows):
        codes.append("claim_edge_decay_block")
    if any(row.claim_edge_status == "watch" for row in rows):
        codes.append("claim_edge_decay_watch")
    for code in REPORT_ROW_REASON_CODES:
        if any(code in row.reason_codes for row in rows):
            codes.append(code)
    return tuple(codes)


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategySpecialistClaimEdgeDecayRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        (reason_code, _count(count))
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _claim_age_decay(
    claim_age_hours: Decimal,
    config: ResearchStrategySpecialistClaimEdgeDecayConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        age_ratio = claim_age_hours / config.max_claim_age_hours
        if age_ratio > ONE_RATIO:
            age_ratio = ONE_RATIO
        return _quantize_ratio(config.claim_age_decay_cap * age_ratio)


def _evidence_refresh_decay(
    evidence_refresh_age_hours: Decimal,
    config: ResearchStrategySpecialistClaimEdgeDecayConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        age_ratio = evidence_refresh_age_hours / config.max_evidence_refresh_age_hours
        if age_ratio > ONE_RATIO:
            age_ratio = ONE_RATIO
        return _quantize_ratio(config.evidence_refresh_decay_cap * age_ratio)


def _confidence_decay(
    specialist_confidence_score: Decimal,
    config: ResearchStrategySpecialistClaimEdgeDecayConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(
            config.confidence_decay_cap * (ONE_RATIO - specialist_confidence_score),
        )


def _source_quorum_decay(
    source_quorum_score: Decimal,
    config: ResearchStrategySpecialistClaimEdgeDecayConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(
            config.source_quorum_decay_cap * (ONE_RATIO - source_quorum_score),
        )


def _contradiction_decay(
    contradiction_score: Decimal,
    config: ResearchStrategySpecialistClaimEdgeDecayConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(config.contradiction_decay_cap * contradiction_score)


def _row_sort_key(
    row: ResearchStrategySpecialistClaimEdgeDecayRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        _status_rank(row.claim_edge_status),
        row.decayed_edge_probability,
        row.redacted_claim_ref,
    )


def _status_rank(status: str) -> Decimal:
    if status == "block":
        return Decimal("0")
    if status == "watch":
        return Decimal("1")
    return Decimal("2")


def _validate_row(row: ResearchStrategySpecialistClaimEdgeDecayRow) -> None:
    expected_raw_edge = _quantize_ratio(
        row.specialist_probability - row.market_probability,
    )
    if row.raw_edge_probability != expected_raw_edge:
        raise ValueError("raw_edge_probability must match specialist market gap")
    expected_decayed_edge = _quantize_ratio(
        row.raw_edge_probability
        - row.claim_age_decay_probability
        - row.evidence_refresh_decay_probability
        - row.confidence_decay_probability
        - row.source_quorum_decay_probability
        - row.contradiction_decay_probability,
    )
    if row.decayed_edge_probability != expected_decayed_edge:
        raise ValueError("decayed_edge_probability must match decay reducer")
    if row.claim_edge_status == "pass" and row.reason_codes != (
        "claim_edge_survives",
    ):
        raise ValueError("pass row reason_codes must describe a surviving edge")
    if row.claim_edge_status == "watch" and row.reason_codes == (
        "claim_edge_survives",
    ):
        raise ValueError("watch row reason_codes must describe a watch condition")
    if row.claim_edge_status == "block" and not any(
        code in row.reason_codes
        for code in ("claim_edge_decayed", "contradiction_block")
    ):
        raise ValueError("block row reason_codes must describe a blocking condition")


def _validate_report(report: ResearchStrategySpecialistClaimEdgeDecayReport) -> None:
    rows = report.rows
    if report.source_row_count != _count(len(rows)):
        raise ValueError("source_row_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.claim_edge_status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(
        sum(1 for row in rows if row.claim_edge_status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(
        sum(1 for row in rows if row.claim_edge_status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.surviving_edge_count != _count(
        sum(1 for row in rows if "claim_edge_survives" in row.reason_codes),
    ):
        raise ValueError("surviving_edge_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(rows):
        raise ValueError("reason_code_counts must match rows")
    decayed_edges = tuple(row.decayed_edge_probability for row in rows)
    if report.mean_decayed_edge_probability != _mean(decayed_edges):
        raise ValueError("mean_decayed_edge_probability must match rows")
    if report.min_decayed_edge_probability != _min_or_zero(decayed_edges):
        raise ValueError("min_decayed_edge_probability must match rows")


def _normalize_rows(
    rows: list[ResearchStrategySpecialistClaimEdgeDecayRow]
    | tuple[ResearchStrategySpecialistClaimEdgeDecayRow, ...],
) -> tuple[ResearchStrategySpecialistClaimEdgeDecayRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategySpecialistClaimEdgeDecayRow:
            raise ValueError(
                "rows must contain ResearchStrategySpecialistClaimEdgeDecayRow values",
            )
        _require_hard_flags("row", row)
        if row.redacted_claim_ref in seen:
            raise ValueError("rows must not contain duplicate redacted_claim_ref values")
        seen.add(row.redacted_claim_ref)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    reason_code_counts: tuple[tuple[str, Decimal], ...],
) -> tuple[tuple[str, Decimal], ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for item in reason_code_counts:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("reason_code_counts must contain pairs")
        reason_code, count = item
        if type(reason_code) is not str:
            raise ValueError("reason_code_counts reason code must be a string")
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code_counts reason code is not supported")
        if reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(reason_code)
        normalized.append(
            (
                reason_code,
                _normalize_nonnegative_count("reason_code_counts count", count),
            ),
        )
    expected = tuple(sorted(normalized, key=lambda item: (-item[1], item[0])))
    if tuple(normalized) != expected:
        raise ValueError("reason_code_counts must be sorted")
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in normalized:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} values must be strings")
        if reason_code not in supported:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    return normalized


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _payload_digest_without_digest(payload: dict[str, Any]) -> str:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "payload_sha256"
    }
    return sha256(_canonical_json(payload_without_digest).encode("utf-8")).hexdigest()


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _reject_unsafe_public_keys(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_keys(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key, UNSAFE_PUBLIC_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_keys(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_keys(label, item)


def _reject_unsafe_public_values(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_values(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value, UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_values(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_values(label, item)


def _has_unsafe_fragment(value: str, fragments: tuple[str, ...]) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in fragments)


def _validate_public_payload_schema(value: object) -> None:
    _require_exact_payload_fields("payload", value, PUBLIC_REPORT_FIELDS)
    if type(value) is not dict:
        return
    if type(value["generated_at"]) is not str:
        raise ValueError("generated_at must be a canonical UTC string")
    if type(value["config_version"]) is not str:
        raise ValueError("config_version must be a string")
    if type(value["payload_sha256"]) is not str:
        raise ValueError("payload_sha256 must be present")
    _require_member("status", value["status"], STATUSES)
    _require_public_reason_codes("reason_codes", value["reason_codes"], REPORT_REASON_CODES)
    _require_public_flags(value)
    for field_name in PUBLIC_REPORT_COUNT_FIELDS + PUBLIC_REPORT_RATIO_FIELDS:
        _require_public_decimal_string(field_name, value[field_name])
    if type(value["reason_code_counts"]) is not list:
        raise ValueError("reason_code_counts must be a list")
    for item in value["reason_code_counts"]:
        if type(item) is not list or len(item) != 2:
            raise ValueError("reason_code_counts must contain pairs")
        if type(item[0]) is not str:
            raise ValueError("reason_code_counts reason code must be a string")
        _require_public_decimal_string("reason_code_counts count", item[1])
    if type(value["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row in value["rows"]:
        _validate_public_row_schema(row)


def _validate_public_row_schema(value: object) -> None:
    _require_exact_payload_fields("row", value, PUBLIC_ROW_FIELDS)
    if type(value) is not dict:
        return
    if type(value["redacted_claim_ref"]) is not str:
        raise ValueError("redacted_claim_ref must be a string")
    _require_redacted_claim_ref(value["redacted_claim_ref"])
    if type(value["observed_at"]) is not str:
        raise ValueError("observed_at must be a canonical UTC string")
    for field_name in PUBLIC_ROW_PROBABILITY_FIELDS:
        _require_public_decimal_string(field_name, value[field_name])
    for field_name in PUBLIC_ROW_VALUE_FIELDS + PUBLIC_ROW_AGE_FIELDS:
        _require_public_decimal_string(field_name, value[field_name])
    _require_member("claim_edge_status", value["claim_edge_status"], STATUSES)
    _require_public_reason_codes(
        "reason_codes",
        value["reason_codes"],
        ROW_REASON_CODES,
    )
    _require_public_flags(value)


def _require_exact_payload_fields(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> None:
    if type(value) is not dict:
        raise ValueError(f"{label} must be an object")
    actual_fields = set(value)
    expected = set(expected_fields)
    missing = sorted(expected - actual_fields)
    unexpected = sorted(actual_fields - expected)
    if missing or unexpected:
        raise ValueError(
            f"{label} fields must match exact schema; "
            f"missing={missing}, unexpected={unexpected}",
        )


def _require_public_decimal_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")


def _require_public_reason_codes(
    field_name: str,
    value: object,
    supported: tuple[str, ...],
) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    _normalize_reason_codes(field_name, value, supported)


def _require_public_flags(value: dict[str, Any]) -> None:
    _require_hard_flags("payload", _DictFlags(value))


def _public_decimal(
    field_name: str,
    value: object,
    normalizer: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = normalizer(field_name, parsed)
    if value != str(normalized):
        raise ValueError(f"{field_name} must use canonical Decimal encoding")
    return normalized


def _public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC string") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must use canonical UTC encoding")
    return normalized


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategySpecialistClaimEdgeDecayReport:
    rows = tuple(_row_from_public_payload(row) for row in payload["rows"])
    return ResearchStrategySpecialistClaimEdgeDecayReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        source_row_count=_public_decimal(
            "source_row_count",
            payload["source_row_count"],
            _normalize_nonnegative_count,
        ),
        pass_count=_public_decimal(
            "pass_count",
            payload["pass_count"],
            _normalize_nonnegative_count,
        ),
        watch_count=_public_decimal(
            "watch_count",
            payload["watch_count"],
            _normalize_nonnegative_count,
        ),
        block_count=_public_decimal(
            "block_count",
            payload["block_count"],
            _normalize_nonnegative_count,
        ),
        surviving_edge_count=_public_decimal(
            "surviving_edge_count",
            payload["surviving_edge_count"],
            _normalize_nonnegative_count,
        ),
        mean_decayed_edge_probability=_public_decimal(
            "mean_decayed_edge_probability",
            payload["mean_decayed_edge_probability"],
            _normalize_value,
        ),
        min_decayed_edge_probability=_public_decimal(
            "min_decayed_edge_probability",
            payload["min_decayed_edge_probability"],
            _normalize_value,
        ),
        status=payload["status"],
        reason_codes=tuple(payload["reason_codes"]),
        reason_code_counts=tuple(
            (
                item[0],
                _public_decimal(
                    "reason_code_counts count",
                    item[1],
                    _normalize_nonnegative_count,
                ),
            )
            for item in payload["reason_code_counts"]
        ),
        rows=rows,
        payload_sha256=payload["payload_sha256"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategySpecialistClaimEdgeDecayRow:
    return ResearchStrategySpecialistClaimEdgeDecayRow(
        redacted_claim_ref=payload["redacted_claim_ref"],
        observed_at=_public_datetime("observed_at", payload["observed_at"]),
        specialist_probability=_public_decimal(
            "specialist_probability",
            payload["specialist_probability"],
            _normalize_probability,
        ),
        market_probability=_public_decimal(
            "market_probability",
            payload["market_probability"],
            _normalize_probability,
        ),
        raw_edge_probability=_public_decimal(
            "raw_edge_probability",
            payload["raw_edge_probability"],
            _normalize_value,
        ),
        claim_age_hours=_public_decimal(
            "claim_age_hours",
            payload["claim_age_hours"],
            _normalize_nonnegative_value,
        ),
        claim_age_decay_probability=_public_decimal(
            "claim_age_decay_probability",
            payload["claim_age_decay_probability"],
            _normalize_probability,
        ),
        evidence_refresh_age_hours=_public_decimal(
            "evidence_refresh_age_hours",
            payload["evidence_refresh_age_hours"],
            _normalize_nonnegative_value,
        ),
        evidence_refresh_decay_probability=_public_decimal(
            "evidence_refresh_decay_probability",
            payload["evidence_refresh_decay_probability"],
            _normalize_probability,
        ),
        specialist_confidence_score=_public_decimal(
            "specialist_confidence_score",
            payload["specialist_confidence_score"],
            _normalize_probability,
        ),
        confidence_decay_probability=_public_decimal(
            "confidence_decay_probability",
            payload["confidence_decay_probability"],
            _normalize_probability,
        ),
        source_quorum_score=_public_decimal(
            "source_quorum_score",
            payload["source_quorum_score"],
            _normalize_probability,
        ),
        source_quorum_decay_probability=_public_decimal(
            "source_quorum_decay_probability",
            payload["source_quorum_decay_probability"],
            _normalize_probability,
        ),
        contradiction_score=_public_decimal(
            "contradiction_score",
            payload["contradiction_score"],
            _normalize_probability,
        ),
        contradiction_decay_probability=_public_decimal(
            "contradiction_decay_probability",
            payload["contradiction_decay_probability"],
            _normalize_probability,
        ),
        decayed_edge_probability=_public_decimal(
            "decayed_edge_probability",
            payload["decayed_edge_probability"],
            _normalize_value,
        ),
        claim_edge_status=payload["claim_edge_status"],
        reason_codes=tuple(payload["reason_codes"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_member(field_name: str, value: str, members: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have surrounding whitespace")


def _require_redacted_claim_ref(value: object) -> None:
    if type(value) is not str:
        raise ValueError("redacted_claim_ref must be a string")
    if not value.startswith(REDACTED_CLAIM_REF_PREFIX):
        raise ValueError("redacted_claim_ref must be redacted")
    suffix = value.removeprefix(REDACTED_CLAIM_REF_PREFIX)
    if len(suffix) != REDACTED_DIGEST_LENGTH:
        raise ValueError("redacted_claim_ref must have a digest suffix")
    if any(character not in "0123456789abcdef" for character in suffix):
        raise ValueError("redacted_claim_ref digest suffix must be hex")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_ratio(decimal_value)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        if decimal_value != decimal_value.to_integral_value():
            raise ValueError(f"{field_name} must be integral")
        normalized = decimal_value.quantize(COUNT_QUANTUM)
        return ZERO_COUNT if normalized == ZERO_COUNT else normalized


def _normalize_value(field_name: str, value: object) -> Decimal:
    return _quantize_ratio(_require_decimal(field_name, value))


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(RATIO_QUANTUM)
        return ZERO_RATIO if normalized == ZERO_RATIO else normalized


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = Decimal(value).quantize(COUNT_QUANTUM)
        return ZERO_COUNT if normalized == ZERO_COUNT else normalized


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(sum(values, ZERO_RATIO) / Decimal(len(values)))


def _min_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return _quantize_ratio(min(values))


def _redacted_claim_ref(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:REDACTED_DIGEST_LENGTH]
    return f"{REDACTED_CLAIM_REF_PREFIX}{digest}"


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SPECIALIST_CLAIM_EDGE_DECAY_REPORT_CONFIG_VERSION",
    "ResearchStrategySpecialistClaimEdgeDecayConfig",
    "ResearchStrategySpecialistClaimEdgeDecayObservation",
    "ResearchStrategySpecialistClaimEdgeDecayRow",
    "ResearchStrategySpecialistClaimEdgeDecayReport",
    "build_research_strategy_specialist_claim_edge_decay_report",
    "research_strategy_specialist_claim_edge_decay_report_payload",
    "research_strategy_specialist_claim_edge_decay_report_json",
    "validate_research_strategy_specialist_claim_edge_decay_report_payload",
)
