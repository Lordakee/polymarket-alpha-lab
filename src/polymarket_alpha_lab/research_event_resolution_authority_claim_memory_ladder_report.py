"""Report-only authority claim memory ladder reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


CONFIG_VERSION = "research_event_resolution_authority_claim_memory_ladder_v1"
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_MEMORY_LADDER_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

__all__ = (
    "CONFIG_VERSION",
    "RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_MEMORY_LADDER_STATUSES",
    "ResearchEventResolutionAuthorityClaimMemoryLadderConfig",
    "ResearchEventResolutionAuthorityClaimMemoryLadderInput",
    "ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem",
    "ResearchEventResolutionAuthorityClaimMemoryLadderReport",
    "ResearchEventResolutionAuthorityClaimMemoryLadderRow",
    "build_research_event_resolution_authority_claim_memory_ladder_report",
    "research_event_resolution_authority_claim_memory_ladder_digest",
    "research_event_resolution_authority_claim_memory_ladder_public_payload",
    "validate_research_event_resolution_authority_claim_memory_ladder_digest",
)

REASON_EMPTY = "authority_claim_memory_ladder_empty"
REASON_PASS = "authority_claim_memory_ladder_pass"
REASON_SCORE_BLOCK = "authority_claim_ladder_score_block"
REASON_SCORE_WATCH = "authority_claim_ladder_score_watch"
REASON_AUTHORITY_GAP = "authority_claim_quorum_gap"
REASON_CLAIM_STALE = "claim_age_stale"
REASON_EVIDENCE_GAP = "evidence_family_gap"
REASON_MEMORY_RECALL_GAP = "memory_recall_gap"
REASON_MEMORY_CONFLICT = "memory_conflict_pressure"
REASON_LADDER_DEPTH_GAP = "memory_ladder_depth_gap"
REASON_CONTRADICTION = "contradiction_pressure"
REASON_RULE_CLARITY_GAP = "resolution_rule_clarity_gap"
REASON_SPECIFICITY_GAP = "claim_specificity_gap"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_UNSAFE_PUBLIC_KEY_TOKENS = frozenset(
    (
        "candidate",
        "market",
        "source_url",
        "source_text",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommendation",
    ),
)
_UNSAFE_PUBLIC_VALUE_PATTERNS = (
    "://",
    "candidate",
    "credential",
    "dsn",
    "market",
    "order",
    "password",
    "postgres",
    "recommendation",
    "sizing",
    "source text",
    "source_text",
    "source url",
    "source_url",
    "table",
    "token",
    "trade",
    "wallet",
)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityClaimMemoryLadderConfig:
    config_version: str = CONFIG_VERSION
    pass_authority_count: Decimal = Decimal("3.000000")
    pass_evidence_family_count: Decimal = Decimal("3.000000")
    pass_ladder_depth_count: Decimal = Decimal("3.000000")
    max_claim_age_hours: Decimal = Decimal("72.000000")
    watch_ladder_threshold: Decimal = Decimal("0.700000")
    block_ladder_threshold: Decimal = Decimal("0.350000")
    watch_claim_freshness_score: Decimal = Decimal("0.750000")
    watch_memory_recall_score: Decimal = Decimal("0.700000")
    watch_memory_conflict_pressure: Decimal = Decimal("0.250000")
    watch_contradiction_pressure: Decimal = Decimal("0.300000")
    watch_resolution_rule_clarity_score: Decimal = Decimal("0.700000")
    watch_claim_specificity_score: Decimal = Decimal("0.700000")
    authority_quorum_weight: Decimal = Decimal("0.150000")
    claim_freshness_weight: Decimal = Decimal("0.100000")
    evidence_family_weight: Decimal = Decimal("0.150000")
    memory_recall_weight: Decimal = Decimal("0.150000")
    memory_conflict_weight: Decimal = Decimal("0.150000")
    ladder_depth_weight: Decimal = Decimal("0.100000")
    contradiction_weight: Decimal = Decimal("0.100000")
    resolution_rule_clarity_weight: Decimal = Decimal("0.050000")
    claim_specificity_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityClaimMemoryLadderConfig:
            raise TypeError(
                "ResearchEventResolutionAuthorityClaimMemoryLadderConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionAuthorityClaimMemoryLadderConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchEventResolutionAuthorityClaimMemoryLadderConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_authority_count",
            "pass_evidence_family_count",
            "pass_ladder_depth_count",
            "max_claim_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_ladder_threshold",
            "block_ladder_threshold",
            "watch_claim_freshness_score",
            "watch_memory_recall_score",
            "watch_memory_conflict_pressure",
            "watch_contradiction_pressure",
            "watch_resolution_rule_clarity_score",
            "watch_claim_specificity_score",
            "authority_quorum_weight",
            "claim_freshness_weight",
            "evidence_family_weight",
            "memory_recall_weight",
            "memory_conflict_weight",
            "ladder_depth_weight",
            "contradiction_weight",
            "resolution_rule_clarity_weight",
            "claim_specificity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("authority claim memory ladder config", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityClaimMemoryLadderInput:
    event_digest: str
    authority_digest: str
    claim_digest: str
    observed_at: datetime
    claim_age_hours: Decimal
    authority_count: Decimal
    evidence_family_count: Decimal
    memory_match_count: Decimal
    memory_conflict_count: Decimal
    memory_recall_score: Decimal
    ladder_depth_count: Decimal
    contradiction_pressure: Decimal
    resolution_rule_clarity_score: Decimal
    claim_specificity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityClaimMemoryLadderInput:
            raise TypeError(
                "ResearchEventResolutionAuthorityClaimMemoryLadderInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionAuthorityClaimMemoryLadderInput:
            raise ValueError(
                "input must be exactly "
                "ResearchEventResolutionAuthorityClaimMemoryLadderInput",
            )
        for field_name in ("event_digest", "authority_digest", "claim_digest"):
            _require_sha256_digest(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "claim_age_hours",
            "authority_count",
            "evidence_family_count",
            "memory_match_count",
            "memory_conflict_count",
            "ladder_depth_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_recall_score",
            "contradiction_pressure",
            "resolution_rule_clarity_score",
            "claim_specificity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("authority claim memory ladder input", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem:
            raise TypeError(
                "ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        require_paper_only_flags("authority claim memory ladder public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityClaimMemoryLadderRow:
    event_digest: str
    authority_digest: str
    claim_digest: str
    observed_at: datetime
    claim_age_hours: Decimal
    authority_count: Decimal
    evidence_family_count: Decimal
    memory_match_count: Decimal
    memory_conflict_count: Decimal
    memory_conflict_pressure: Decimal
    memory_recall_score: Decimal
    ladder_depth_count: Decimal
    contradiction_pressure: Decimal
    resolution_rule_clarity_score: Decimal
    claim_specificity_score: Decimal
    authority_quorum_score: Decimal
    claim_freshness_score: Decimal
    evidence_family_score: Decimal
    ladder_depth_score: Decimal
    ladder_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityClaimMemoryLadderRow:
            raise TypeError(
                "ResearchEventResolutionAuthorityClaimMemoryLadderRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionAuthorityClaimMemoryLadderRow:
            raise ValueError(
                "row must be exactly ResearchEventResolutionAuthorityClaimMemoryLadderRow",
            )
        for field_name in ("event_digest", "authority_digest", "claim_digest"):
            _require_sha256_digest(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "claim_age_hours",
            "authority_count",
            "evidence_family_count",
            "memory_match_count",
            "memory_conflict_count",
            "ladder_depth_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_conflict_pressure",
            "memory_recall_score",
            "contradiction_pressure",
            "resolution_rule_clarity_score",
            "claim_specificity_score",
            "authority_quorum_score",
            "claim_freshness_score",
            "evidence_family_score",
            "ladder_depth_score",
            "ladder_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.status not in self.reason_codes:
            raise ValueError("status must be included in reason_codes")
        require_paper_only_flags("authority claim memory ladder row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityClaimMemoryLadderReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_ladder_score: Decimal
    weakest_ladder_score: Decimal
    authority_gap_count: Decimal
    stale_claim_count: Decimal
    evidence_gap_count: Decimal
    memory_conflict_count: Decimal
    contradiction_count: Decimal
    rows: tuple[ResearchEventResolutionAuthorityClaimMemoryLadderRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    public_payload: tuple[
        ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityClaimMemoryLadderReport:
            raise TypeError(
                "ResearchEventResolutionAuthorityClaimMemoryLadderReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionAuthorityClaimMemoryLadderReport:
            raise ValueError(
                "report must be exactly ResearchEventResolutionAuthorityClaimMemoryLadderReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "authority_gap_count",
            "stale_claim_count",
            "evidence_gap_count",
            "memory_conflict_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_ladder_score", "weakest_ladder_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        require_paper_only_flags("authority claim memory ladder report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        return research_event_resolution_authority_claim_memory_ladder_public_payload(self)


def build_research_event_resolution_authority_claim_memory_ladder_report(
    inputs: Sequence[ResearchEventResolutionAuthorityClaimMemoryLadderInput],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionAuthorityClaimMemoryLadderConfig | None = None,
    public_payload: Sequence[
        ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem
    ] = (),
) -> ResearchEventResolutionAuthorityClaimMemoryLadderReport:
    """Build a deterministic report-only authority claim memory ladder snapshot."""

    if config is None:
        config = ResearchEventResolutionAuthorityClaimMemoryLadderConfig()
    if type(config) is not ResearchEventResolutionAuthorityClaimMemoryLadderConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionAuthorityClaimMemoryLadderConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    payload_items = _normalize_public_payload(public_payload)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "average_ladder_score": _average(tuple(row.ladder_score for row in rows)),
        "weakest_ladder_score": _minimum_or_zero(tuple(row.ladder_score for row in rows)),
        "authority_gap_count": _reason_count(rows, REASON_AUTHORITY_GAP),
        "stale_claim_count": _reason_count(rows, REASON_CLAIM_STALE),
        "evidence_gap_count": _reason_count(rows, REASON_EVIDENCE_GAP),
        "memory_conflict_count": _reason_count(rows, REASON_MEMORY_CONFLICT),
        "contradiction_count": _reason_count(rows, REASON_CONTRADICTION),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionAuthorityClaimMemoryLadderReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_resolution_authority_claim_memory_ladder_public_payload(
    report: ResearchEventResolutionAuthorityClaimMemoryLadderReport | dict[str, Any],
) -> dict[str, object]:
    if type(report) is ResearchEventResolutionAuthorityClaimMemoryLadderReport:
        _rebuild_report_for_payload(report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError(
            "report must be a ResearchEventResolutionAuthorityClaimMemoryLadderReport "
            "or dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(
        "ResearchEventResolutionAuthorityClaimMemoryLadderReport.payload",
        payload,
        allow_json_containers=True,
    )
    _require_hard_flags("payload", _DictFlags(payload))
    _require_nested_hard_flags("payload", payload)
    digest_value = payload.get("derived_validation_digest")
    if type(digest_value) is not str:
        raise ValueError("derived_validation_digest must be a sha256 digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def validate_research_event_resolution_authority_claim_memory_ladder_digest(
    report: ResearchEventResolutionAuthorityClaimMemoryLadderReport,
) -> None:
    if type(report) is not ResearchEventResolutionAuthorityClaimMemoryLadderReport:
        raise ValueError(
            "report must be a ResearchEventResolutionAuthorityClaimMemoryLadderReport",
        )
    _rebuild_report_for_payload(report)


def research_event_resolution_authority_claim_memory_ladder_digest(
    report: ResearchEventResolutionAuthorityClaimMemoryLadderReport,
) -> str:
    if type(report) is not ResearchEventResolutionAuthorityClaimMemoryLadderReport:
        raise ValueError(
            "report must be a ResearchEventResolutionAuthorityClaimMemoryLadderReport",
        )
    return _report_digest_from_values(_report_values_without_digest(report))


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_input(
    item: ResearchEventResolutionAuthorityClaimMemoryLadderInput,
    *,
    config: ResearchEventResolutionAuthorityClaimMemoryLadderConfig,
) -> ResearchEventResolutionAuthorityClaimMemoryLadderRow:
    authority_score = _capped_ratio(item.authority_count, config.pass_authority_count)
    claim_freshness_score = _claim_freshness_score(item.claim_age_hours, config)
    evidence_score = _capped_ratio(
        item.evidence_family_count,
        config.pass_evidence_family_count,
    )
    memory_conflict_pressure = _memory_conflict_pressure(item)
    ladder_depth_score = _capped_ratio(
        item.ladder_depth_count,
        config.pass_ladder_depth_count,
    )
    ladder_score = _ladder_score(
        authority_quorum_score=authority_score,
        claim_freshness_score=claim_freshness_score,
        evidence_family_score=evidence_score,
        memory_recall_score=item.memory_recall_score,
        memory_conflict_pressure=memory_conflict_pressure,
        ladder_depth_score=ladder_depth_score,
        contradiction_pressure=item.contradiction_pressure,
        resolution_rule_clarity_score=item.resolution_rule_clarity_score,
        claim_specificity_score=item.claim_specificity_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        item=item,
        authority_quorum_score=authority_score,
        claim_freshness_score=claim_freshness_score,
        evidence_family_score=evidence_score,
        memory_conflict_pressure=memory_conflict_pressure,
        ladder_depth_score=ladder_depth_score,
        ladder_score=ladder_score,
        config=config,
    )
    return ResearchEventResolutionAuthorityClaimMemoryLadderRow(
        event_digest=item.event_digest,
        authority_digest=item.authority_digest,
        claim_digest=item.claim_digest,
        observed_at=item.observed_at,
        claim_age_hours=item.claim_age_hours,
        authority_count=item.authority_count,
        evidence_family_count=item.evidence_family_count,
        memory_match_count=item.memory_match_count,
        memory_conflict_count=item.memory_conflict_count,
        memory_conflict_pressure=memory_conflict_pressure,
        memory_recall_score=item.memory_recall_score,
        ladder_depth_count=item.ladder_depth_count,
        contradiction_pressure=item.contradiction_pressure,
        resolution_rule_clarity_score=item.resolution_rule_clarity_score,
        claim_specificity_score=item.claim_specificity_score,
        authority_quorum_score=authority_score,
        claim_freshness_score=claim_freshness_score,
        evidence_family_score=evidence_score,
        ladder_depth_score=ladder_depth_score,
        ladder_score=ladder_score,
        status=_row_status(ladder_score, config=config),
        reason_codes=reason_codes,
    )


def _claim_freshness_score(
    claim_age_hours: Decimal,
    config: ResearchEventResolutionAuthorityClaimMemoryLadderConfig,
) -> Decimal:
    if claim_age_hours >= config.max_claim_age_hours:
        return ZERO
    return _quantize(ONE - (claim_age_hours / config.max_claim_age_hours))


def _memory_conflict_pressure(
    item: ResearchEventResolutionAuthorityClaimMemoryLadderInput,
) -> Decimal:
    total_memory_count = item.memory_match_count + item.memory_conflict_count
    if total_memory_count == ZERO:
        return ZERO
    return _capped_ratio(item.memory_conflict_count, total_memory_count)


def _ladder_score(
    *,
    authority_quorum_score: Decimal,
    claim_freshness_score: Decimal,
    evidence_family_score: Decimal,
    memory_recall_score: Decimal,
    memory_conflict_pressure: Decimal,
    ladder_depth_score: Decimal,
    contradiction_pressure: Decimal,
    resolution_rule_clarity_score: Decimal,
    claim_specificity_score: Decimal,
    config: ResearchEventResolutionAuthorityClaimMemoryLadderConfig,
) -> Decimal:
    return _quantize(
        authority_quorum_score * config.authority_quorum_weight
        + claim_freshness_score * config.claim_freshness_weight
        + evidence_family_score * config.evidence_family_weight
        + memory_recall_score * config.memory_recall_weight
        + (ONE - memory_conflict_pressure) * config.memory_conflict_weight
        + ladder_depth_score * config.ladder_depth_weight
        + (ONE - contradiction_pressure) * config.contradiction_weight
        + resolution_rule_clarity_score * config.resolution_rule_clarity_weight
        + claim_specificity_score * config.claim_specificity_weight,
    )


def _row_status(
    ladder_score: Decimal,
    *,
    config: ResearchEventResolutionAuthorityClaimMemoryLadderConfig,
) -> str:
    if ladder_score <= config.block_ladder_threshold:
        return STATUS_BLOCK
    if ladder_score < config.watch_ladder_threshold:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    item: ResearchEventResolutionAuthorityClaimMemoryLadderInput,
    authority_quorum_score: Decimal,
    claim_freshness_score: Decimal,
    evidence_family_score: Decimal,
    memory_conflict_pressure: Decimal,
    ladder_depth_score: Decimal,
    ladder_score: Decimal,
    config: ResearchEventResolutionAuthorityClaimMemoryLadderConfig,
) -> tuple[str, ...]:
    status = _row_status(ladder_score, config=config)
    reason_codes = {status}
    if status == STATUS_PASS:
        reason_codes.add(REASON_PASS)
    elif status == STATUS_BLOCK:
        reason_codes.add(REASON_SCORE_BLOCK)
    else:
        reason_codes.add(REASON_SCORE_WATCH)
    if authority_quorum_score < ONE:
        reason_codes.add(REASON_AUTHORITY_GAP)
    if claim_freshness_score < config.watch_claim_freshness_score:
        reason_codes.add(REASON_CLAIM_STALE)
    if evidence_family_score < ONE:
        reason_codes.add(REASON_EVIDENCE_GAP)
    if item.memory_recall_score < config.watch_memory_recall_score:
        reason_codes.add(REASON_MEMORY_RECALL_GAP)
    if memory_conflict_pressure >= config.watch_memory_conflict_pressure:
        reason_codes.add(REASON_MEMORY_CONFLICT)
    if ladder_depth_score < ONE:
        reason_codes.add(REASON_LADDER_DEPTH_GAP)
    if item.contradiction_pressure >= config.watch_contradiction_pressure:
        reason_codes.add(REASON_CONTRADICTION)
    if item.resolution_rule_clarity_score < config.watch_resolution_rule_clarity_score:
        reason_codes.add(REASON_RULE_CLARITY_GAP)
    if item.claim_specificity_score < config.watch_claim_specificity_score:
        reason_codes.add(REASON_SPECIFICITY_GAP)
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchEventResolutionAuthorityClaimMemoryLadderRow, ...],
) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionAuthorityClaimMemoryLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_EMPTY,)
    reason_codes: set[str] = set()
    for row in rows:
        reason_codes.update(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionAuthorityClaimMemoryLadderRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    if not rows:
        return ((REASON_EMPTY, ONE),)
    counter: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counter[reason_code] = counter.get(reason_code, 0) + 1
    return tuple(
        (reason_code, _decimal_count(count))
        for reason_code, count in sorted(counter.items())
    )


def _reason_count(
    rows: tuple[ResearchEventResolutionAuthorityClaimMemoryLadderRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if reason_code in row.reason_codes),
    )


def _status_count(
    rows: tuple[ResearchEventResolutionAuthorityClaimMemoryLadderRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _minimum_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values).quantize(DECIMAL_QUANTUM)


def _row_sort_key(
    row: ResearchEventResolutionAuthorityClaimMemoryLadderRow,
) -> tuple[str, str, str]:
    return (row.claim_digest, row.event_digest, row.authority_digest)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return min(ONE, _quantize(numerator / denominator))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(DECIMAL_QUANTUM)


def _report_values_without_digest(
    report: ResearchEventResolutionAuthorityClaimMemoryLadderReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _json_ready(values),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_validation_digest(payload: Mapping[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _rebuild_report_for_payload(
    report: ResearchEventResolutionAuthorityClaimMemoryLadderReport,
) -> None:
    expected_digest = _report_digest_from_values(_report_values_without_digest(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value.quantize(DECIMAL_QUANTUM), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _validate_config(
    config: ResearchEventResolutionAuthorityClaimMemoryLadderConfig,
) -> None:
    if config.block_ladder_threshold >= config.watch_ladder_threshold:
        raise ValueError("block_ladder_threshold must be below watch_ladder_threshold")
    weights = (
        config.authority_quorum_weight
        + config.claim_freshness_weight
        + config.evidence_family_weight
        + config.memory_recall_weight
        + config.memory_conflict_weight
        + config.ladder_depth_weight
        + config.contradiction_weight
        + config.resolution_rule_clarity_weight
        + config.claim_specificity_weight
    )
    if weights != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_report(
    report: ResearchEventResolutionAuthorityClaimMemoryLadderReport,
) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must equal rows length")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must equal row status count")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must equal row status count")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must equal row status count")
    if report.status != _report_status(rows):
        raise ValueError("status must reflect row statuses")
    if report.average_ladder_score != _average(tuple(row.ladder_score for row in rows)):
        raise ValueError("average_ladder_score must equal row average")
    if report.weakest_ladder_score != _minimum_or_zero(
        tuple(row.ladder_score for row in rows),
    ):
        raise ValueError("weakest_ladder_score must equal row minimum")
    for field_name, reason_code in (
        ("authority_gap_count", REASON_AUTHORITY_GAP),
        ("stale_claim_count", REASON_CLAIM_STALE),
        ("evidence_gap_count", REASON_EVIDENCE_GAP),
        ("memory_conflict_count", REASON_MEMORY_CONFLICT),
        ("contradiction_count", REASON_CONTRADICTION),
    ):
        if getattr(report, field_name) != _reason_count(rows, reason_code):
            raise ValueError(f"{field_name} must equal row reason count")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must equal row reason codes")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must equal row reason code counts")


def _normalize_inputs(
    inputs: Sequence[ResearchEventResolutionAuthorityClaimMemoryLadderInput],
) -> tuple[ResearchEventResolutionAuthorityClaimMemoryLadderInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be a sequence of input values")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not ResearchEventResolutionAuthorityClaimMemoryLadderInput:
            raise ValueError(
                "inputs must contain ResearchEventResolutionAuthorityClaimMemoryLadderInput values",
            )
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchEventResolutionAuthorityClaimMemoryLadderRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventResolutionAuthorityClaimMemoryLadderRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionAuthorityClaimMemoryLadderRow values",
            )
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_public_payload(
    items: Sequence[ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem],
) -> tuple[ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("public_payload must be a sequence of payload items")
    normalized = tuple(items)
    for item in normalized:
        if type(item) is not ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem values",
            )
    return tuple(sorted(normalized, key=lambda item: (item.key, item.value)))


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for code in reason_codes:
        _require_public_identifier("reason_code", code)
        if code not in seen:
            seen.add(code)
            normalized.append(code)
    return tuple(sorted(normalized))


def _normalize_reason_code_counts(
    reason_code_counts: object,
) -> tuple[tuple[str, Decimal], ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    for item in reason_code_counts:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts must contain two-item tuples")
        reason_code, count = item
        _require_public_identifier("reason_code", reason_code)
        normalized.append(
            (
                reason_code,
                _require_nonnegative_decimal("reason_code_count", count),
            ),
        )
    return tuple(sorted(normalized, key=lambda item: item[0]))


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (
        STATUS_PASS,
        STATUS_WATCH,
        STATUS_BLOCK,
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    if _unsafe_public_string(value):
        raise ValueError(f"{field_name} contains unsafe public payload text")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if not value or len(value) > 256:
        raise ValueError(f"{field_name} must be non-empty and at most 256 characters")
    if _unsafe_public_string(value):
        raise ValueError(f"{field_name} contains unsafe public payload text")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be exactly Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(DECIMAL_QUANTUM)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    require_paper_only_flags(field_name, value)


def _require_nested_hard_flags(field_name: str, value: object) -> None:
    flag_names = ("paper_only", "report_only", "readonly")
    if isinstance(value, Mapping):
        if any(flag_name in value for flag_name in flag_names):
            for flag_name in flag_names:
                if value.get(flag_name) is not True:
                    raise ValueError(f"{field_name} {flag_name} must be True")
        for key, item in value.items():
            _require_nested_hard_flags(f"{field_name}.{key}", item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _require_nested_hard_flags(field_name, item)


def _unsafe_public_string(value: str) -> bool:
    normalized = value.lower()
    tokens = tuple(token for token in re.split(r"[^a-z0-9]+", normalized) if token)
    if any(token in _UNSAFE_PUBLIC_KEY_TOKENS for token in tokens):
        return True
    return any(pattern in normalized for pattern in _UNSAFE_PUBLIC_VALUE_PATTERNS)


def _reject_unsafe_public_payload(
    field_name: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(field_name, asdict(value), allow_json_containers=True)
        return
    if isinstance(value, Mapping):
        if not allow_json_containers and type(value) is not dict:
            raise ValueError(f"{field_name} must use plain public payload containers")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{field_name} contains non-string public payload key")
            if _unsafe_public_string(key):
                raise ValueError(f"{field_name} contains unsafe public payload key")
            _reject_unsafe_public_payload(
                f"{field_name}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (tuple, list)):
        if not allow_json_containers and type(value) is not tuple:
            raise ValueError(f"{field_name} must use tuple public payload containers")
        for item in value:
            _reject_unsafe_public_payload(
                field_name,
                item,
                allow_json_containers=True,
            )
        return
    if type(value) is str and _unsafe_public_string(value):
        raise ValueError(f"{field_name} contains unsafe public payload value")
    if (
        type(value) in (str, bool, Decimal, datetime)
        or value is None
    ):
        return
    raise ValueError(f"{field_name} contains unsupported public payload value")
