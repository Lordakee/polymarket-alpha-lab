"""Report-only claim authority memory scorecard reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CLAIM_AUTHORITY_MEMORY_SCORECARD_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_CLAIM_AUTHORITY_MEMORY_SCORECARD_STATUSES",
    "ResearchStrategyClaimAuthorityMemoryScorecardConfig",
    "ResearchStrategyClaimAuthorityMemoryScorecardInput",
    "ResearchStrategyClaimAuthorityMemoryScorecardReasonCodeCount",
    "ResearchStrategyClaimAuthorityMemoryScorecardReport",
    "ResearchStrategyClaimAuthorityMemoryScorecardRow",
    "build_research_strategy_claim_authority_memory_scorecard_report",
    "research_strategy_claim_authority_memory_scorecard_report_digest",
    "research_strategy_claim_authority_memory_scorecard_report_public_payload",
    "validate_research_strategy_claim_authority_memory_scorecard_report_public_payload",
)


DEFAULT_RESEARCH_STRATEGY_CLAIM_AUTHORITY_MEMORY_SCORECARD_REPORT_CONFIG_VERSION = (
    "research-strategy-claim-authority-memory-scorecard-report-v0"
)
RESEARCH_STRATEGY_CLAIM_AUTHORITY_MEMORY_SCORECARD_STATUSES = (
    "pass",
    "watch",
    "block",
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
DIGEST_FIELD = "derived_validation_digest"
Q = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUS_SEQUENCE = {
    BLOCK_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

EMPTY_REPORT_REASON = "empty_claim_authority_memory_inputs"
INPUT_REASON_CODES = (
    "memory_trace_ready",
    "human_review_flagged",
    "missing_memory_trace",
)
GENERATED_REASON_CODES = (
    "claim_authority_block",
    "memory_recall_block",
    "evidence_alignment_block",
    "conflict_pressure_block",
    "aggregate_score_block",
    "claim_authority_watch",
    "memory_recall_watch",
    "evidence_alignment_watch",
    "conflict_pressure_watch",
    "aggregate_score_watch",
    "claim_authority_memory_pass",
)
REASON_CODES = (
    EMPTY_REPORT_REASON,
    *INPUT_REASON_CODES,
    *GENERATED_REASON_CODES,
)
REASON_SEQUENCE = {
    reason: Decimal(index)
    for index, reason in enumerate(REASON_CODES)
}

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DIGEST_REFERENCE_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _term(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "raw_text",
    "raw text",
    "dsn",
    "table",
    _term("to", "ken"),
    _term("wal", "let"),
    _term("ord", "er"),
    _term("tra", "de"),
    _term("li", "ve"),
    _term("siz", "ing"),
    _term("recom", "mend"),
    _term("d", "b"),
    _term("data", "base"),
    _term("net", "work"),
    "http://",
    "https://",
    "://",
)


@dataclass(frozen=True)
class ResearchStrategyClaimAuthorityMemoryScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CLAIM_AUTHORITY_MEMORY_SCORECARD_REPORT_CONFIG_VERSION
    )
    pass_min_score: Decimal = Decimal("0.800000")
    watch_min_score: Decimal = Decimal("0.600000")
    min_pass_claim_authority_score: Decimal = Decimal("0.800000")
    min_watch_claim_authority_score: Decimal = Decimal("0.600000")
    min_pass_memory_recall_score: Decimal = Decimal("0.750000")
    min_watch_memory_recall_score: Decimal = Decimal("0.550000")
    min_pass_evidence_alignment_score: Decimal = Decimal("0.700000")
    min_watch_evidence_alignment_score: Decimal = Decimal("0.550000")
    max_pass_conflict_score: Decimal = Decimal("0.200000")
    max_watch_conflict_score: Decimal = Decimal("0.450000")
    claim_authority_weight: Decimal = Decimal("0.350000")
    memory_recall_weight: Decimal = Decimal("0.300000")
    evidence_alignment_weight: Decimal = Decimal("0.200000")
    conflict_safety_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyClaimAuthorityMemoryScorecardConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimAuthorityMemoryScorecardConfig)
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CLAIM_AUTHORITY_MEMORY_SCORECARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "pass_min_score",
            "watch_min_score",
            "min_pass_claim_authority_score",
            "min_watch_claim_authority_score",
            "min_pass_memory_recall_score",
            "min_watch_memory_recall_score",
            "min_pass_evidence_alignment_score",
            "min_watch_evidence_alignment_score",
            "max_pass_conflict_score",
            "max_watch_conflict_score",
            "claim_authority_weight",
            "memory_recall_weight",
            "evidence_alignment_weight",
            "conflict_safety_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_descending_pair("score threshold", self.pass_min_score, self.watch_min_score)
        _require_descending_pair(
            "claim_authority_score",
            self.min_pass_claim_authority_score,
            self.min_watch_claim_authority_score,
        )
        _require_descending_pair(
            "memory_recall_score",
            self.min_pass_memory_recall_score,
            self.min_watch_memory_recall_score,
        )
        _require_descending_pair(
            "evidence_alignment_score",
            self.min_pass_evidence_alignment_score,
            self.min_watch_evidence_alignment_score,
        )
        if self.max_watch_conflict_score < self.max_pass_conflict_score:
            raise ValueError("max_watch_conflict_score must be at least max_pass_conflict_score")
        weight_sum = _quantize_ratio(
            self.claim_authority_weight
            + self.memory_recall_weight
            + self.evidence_alignment_weight
            + self.conflict_safety_weight,
        )
        if weight_sum != ONE:
            raise ValueError("score weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyClaimAuthorityMemoryScorecardInput:
    claim_group: str
    private_candidate_reference: str
    private_market_reference: str
    private_source_reference: str
    observed_at: datetime
    claim_authority_score: Decimal
    memory_recall_score: Decimal
    evidence_alignment_score: Decimal
    conflict_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyClaimAuthorityMemoryScorecardInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimAuthorityMemoryScorecardInput)
        object.__setattr__(
            self,
            "claim_group",
            _require_public_identifier("claim_group", self.claim_group),
        )
        for field_name in (
            "private_candidate_reference",
            "private_market_reference",
            "private_source_reference",
        ):
            _require_private_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "claim_authority_score",
            "memory_recall_score",
            "evidence_alignment_score",
            "conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, INPUT_REASON_CODES),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyClaimAuthorityMemoryScorecardRow:
    rank: Decimal
    claim_group: str
    claim_digest: str
    context_digest: str
    evidence_digest: str
    observed_at: datetime
    claim_authority_score: Decimal
    memory_recall_score: Decimal
    evidence_alignment_score: Decimal
    conflict_score: Decimal
    conflict_safety_score: Decimal
    score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyClaimAuthorityMemoryScorecardRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimAuthorityMemoryScorecardRow)
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        object.__setattr__(
            self,
            "claim_group",
            _require_public_identifier("claim_group", self.claim_group),
        )
        for field_name in ("claim_digest", "context_digest", "evidence_digest"):
            _require_digest_reference(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "claim_authority_score",
            "memory_recall_score",
            "evidence_alignment_score",
            "conflict_score",
            "conflict_safety_score",
            "score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REASON_CODES),
        )
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyClaimAuthorityMemoryScorecardReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyClaimAuthorityMemoryScorecardReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimAuthorityMemoryScorecardReasonCodeCount)
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(self, "count", _require_positive_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyClaimAuthorityMemoryScorecardReport:
    generated_at: datetime
    config_version: str
    status: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_score: Decimal
    weakest_score: Decimal
    highest_conflict_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyClaimAuthorityMemoryScorecardReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyClaimAuthorityMemoryScorecardRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyClaimAuthorityMemoryScorecardReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimAuthorityMemoryScorecardReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CLAIM_AUTHORITY_MEMORY_SCORECARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_status("status", self.status)
        for field_name in ("signal_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_score", "weakest_score", "highest_conflict_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_sha256_digest(DIGEST_FIELD, self.derived_validation_digest),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match public payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_strategy_claim_authority_memory_scorecard_report_public_payload(self)


def build_research_strategy_claim_authority_memory_scorecard_report(
    *,
    signals: object,
    generated_at: datetime,
    config: ResearchStrategyClaimAuthorityMemoryScorecardConfig | None = None,
) -> ResearchStrategyClaimAuthorityMemoryScorecardReport:
    generated_at = _as_utc("generated_at", generated_at)
    resolved_config = config or ResearchStrategyClaimAuthorityMemoryScorecardConfig()
    if type(resolved_config) is not ResearchStrategyClaimAuthorityMemoryScorecardConfig:
        raise ValueError(
            "config must be a ResearchStrategyClaimAuthorityMemoryScorecardConfig",
        )
    _require_hard_flags("config", resolved_config)
    normalized_signals = _normalize_inputs(signals)
    for item in normalized_signals:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = _rank_rows(
        tuple(
            _row_from_input(item, config=resolved_config)
            for item in normalized_signals
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": resolved_config.config_version,
        "status": _report_status(rows),
        "signal_count": _count(len(rows)),
        "pass_count": _count(_status_count(rows, PASS_STATUS)),
        "watch_count": _count(_status_count(rows, WATCH_STATUS)),
        "block_count": _count(_status_count(rows, BLOCK_STATUS)),
        "average_score": _average_score(rows),
        "weakest_score": min((row.score for row in rows), default=ZERO),
        "highest_conflict_score": max((row.conflict_score for row in rows), default=ZERO),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyClaimAuthorityMemoryScorecardReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_strategy_claim_authority_memory_scorecard_report_public_payload(
    report: ResearchStrategyClaimAuthorityMemoryScorecardReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyClaimAuthorityMemoryScorecardReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping) and not isinstance(report, (str, bytes)):
        payload = _json_ready(dict(report))
    else:
        raise ValueError(
            "report must be a ResearchStrategyClaimAuthorityMemoryScorecardReport",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    return validate_research_strategy_claim_authority_memory_scorecard_report_public_payload(
        payload,
    )


def research_strategy_claim_authority_memory_scorecard_report_digest(
    report: ResearchStrategyClaimAuthorityMemoryScorecardReport | Mapping[str, Any],
) -> str:
    public_payload = research_strategy_claim_authority_memory_scorecard_report_public_payload(
        report,
    )
    return _require_sha256_digest(DIGEST_FIELD, public_payload[DIGEST_FIELD])


def validate_research_strategy_claim_authority_memory_scorecard_report_public_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or isinstance(payload, (str, bytes)):
        raise ValueError("public payload must be a JSON object")
    ready = _json_ready(dict(payload))
    if type(ready) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", ready, allow_json_containers=True)
    _require_hard_flags("public payload", _DictFlags(ready))
    _require_nested_hard_flags("public payload", ready)
    digest = _require_sha256_digest(DIGEST_FIELD, ready.get(DIGEST_FIELD))
    expected_digest = _digest_from_values(_without_digest(ready))
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    return ready


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, Any]

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
    item: ResearchStrategyClaimAuthorityMemoryScorecardInput,
    *,
    config: ResearchStrategyClaimAuthorityMemoryScorecardConfig,
) -> ResearchStrategyClaimAuthorityMemoryScorecardRow:
    conflict_safety_score = _quantize_ratio(ONE - item.conflict_score)
    score = _quantize_ratio(
        (item.claim_authority_score * config.claim_authority_weight)
        + (item.memory_recall_score * config.memory_recall_weight)
        + (item.evidence_alignment_score * config.evidence_alignment_weight)
        + (conflict_safety_score * config.conflict_safety_weight),
    )
    reason_codes = _row_reason_codes(item, score=score, config=config)
    return ResearchStrategyClaimAuthorityMemoryScorecardRow(
        rank=ONE,
        claim_group=item.claim_group,
        claim_digest=_digest_reference(
            "claim",
            item.claim_group,
            item.private_candidate_reference,
        ),
        context_digest=_digest_reference(
            "context",
            item.claim_group,
            item.private_market_reference,
        ),
        evidence_digest=_digest_reference(
            "evidence",
            item.claim_group,
            item.private_source_reference,
        ),
        observed_at=item.observed_at,
        claim_authority_score=item.claim_authority_score,
        memory_recall_score=item.memory_recall_score,
        evidence_alignment_score=item.evidence_alignment_score,
        conflict_score=item.conflict_score,
        conflict_safety_score=conflict_safety_score,
        score=score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchStrategyClaimAuthorityMemoryScorecardInput,
    *,
    score: Decimal,
    config: ResearchStrategyClaimAuthorityMemoryScorecardConfig,
) -> tuple[str, ...]:
    reason_codes = list(item.reason_codes)
    if item.claim_authority_score < config.min_watch_claim_authority_score:
        reason_codes.append("claim_authority_block")
    elif item.claim_authority_score < config.min_pass_claim_authority_score:
        reason_codes.append("claim_authority_watch")
    if item.memory_recall_score < config.min_watch_memory_recall_score:
        reason_codes.append("memory_recall_block")
    elif item.memory_recall_score < config.min_pass_memory_recall_score:
        reason_codes.append("memory_recall_watch")
    if item.evidence_alignment_score < config.min_watch_evidence_alignment_score:
        reason_codes.append("evidence_alignment_block")
    elif item.evidence_alignment_score < config.min_pass_evidence_alignment_score:
        reason_codes.append("evidence_alignment_watch")
    if item.conflict_score > config.max_watch_conflict_score:
        reason_codes.append("conflict_pressure_block")
    elif item.conflict_score > config.max_pass_conflict_score:
        reason_codes.append("conflict_pressure_watch")
    if score < config.watch_min_score:
        reason_codes.append("aggregate_score_block")
    elif score < config.pass_min_score:
        reason_codes.append("aggregate_score_watch")
    if len(reason_codes) == len(item.reason_codes):
        reason_codes.append("claim_authority_memory_pass")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), REASON_CODES)


def _rank_rows(
    rows: tuple[ResearchStrategyClaimAuthorityMemoryScorecardRow, ...],
) -> tuple[ResearchStrategyClaimAuthorityMemoryScorecardRow, ...]:
    ranked: list[ResearchStrategyClaimAuthorityMemoryScorecardRow] = []
    for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1):
        ranked.append(
            ResearchStrategyClaimAuthorityMemoryScorecardRow(
                rank=_count(index),
                claim_group=row.claim_group,
                claim_digest=row.claim_digest,
                context_digest=row.context_digest,
                evidence_digest=row.evidence_digest,
                observed_at=row.observed_at,
                claim_authority_score=row.claim_authority_score,
                memory_recall_score=row.memory_recall_score,
                evidence_alignment_score=row.evidence_alignment_score,
                conflict_score=row.conflict_score,
                conflict_safety_score=row.conflict_safety_score,
                score=row.score,
                status=row.status,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked)


def _row_sort_key(row: ResearchStrategyClaimAuthorityMemoryScorecardRow) -> tuple[object, ...]:
    return (
        STATUS_SEQUENCE[row.status],
        row.score,
        row.claim_group,
        row.claim_digest,
        row.context_digest,
        row.evidence_digest,
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return BLOCK_STATUS
    if any(reason.endswith("_watch") for reason in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _report_status(
    rows: tuple[ResearchStrategyClaimAuthorityMemoryScorecardRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchStrategyClaimAuthorityMemoryScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON,)
    return tuple(
        reason
        for reason in REASON_CODES
        if reason != EMPTY_REPORT_REASON
        and any(reason in row.reason_codes for row in rows)
    )


def _reason_code_counts(
    rows: tuple[ResearchStrategyClaimAuthorityMemoryScorecardRow, ...],
) -> tuple[ResearchStrategyClaimAuthorityMemoryScorecardReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyClaimAuthorityMemoryScorecardReasonCodeCount(
            reason_code=reason,
            count=_count(counter[reason]),
        )
        for reason in REASON_CODES
        if counter[reason] > 0
    )


def _average_score(
    rows: tuple[ResearchStrategyClaimAuthorityMemoryScorecardRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize_ratio(sum((row.score for row in rows), ZERO) / _count(len(rows)))


def _status_count(
    rows: tuple[ResearchStrategyClaimAuthorityMemoryScorecardRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_inputs(
    signals: object,
) -> tuple[ResearchStrategyClaimAuthorityMemoryScorecardInput, ...]:
    if type(signals) not in (tuple, list):
        raise ValueError("signals must be a tuple or list")
    normalized = tuple(signals)
    for item in normalized:
        if type(item) is not ResearchStrategyClaimAuthorityMemoryScorecardInput:
            raise ValueError(
                "signals must contain ResearchStrategyClaimAuthorityMemoryScorecardInput",
            )
        _require_hard_flags("input", item)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyClaimAuthorityMemoryScorecardRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for index, row in enumerate(rows, start=1):
        if type(row) is not ResearchStrategyClaimAuthorityMemoryScorecardRow:
            raise ValueError(
                "rows must contain ResearchStrategyClaimAuthorityMemoryScorecardRow",
            )
        if row.rank != _count(index):
            raise ValueError("rows must use deterministic sequence")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: object,
) -> tuple[ResearchStrategyClaimAuthorityMemoryScorecardReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in reason_code_counts:
        if type(item) is not ResearchStrategyClaimAuthorityMemoryScorecardReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyClaimAuthorityMemoryScorecardReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
    expected = tuple(sorted(reason_code_counts, key=lambda item: REASON_SEQUENCE[item.reason_code]))
    if reason_code_counts != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return reason_code_counts


def _validate_report(report: ResearchStrategyClaimAuthorityMemoryScorecardReport) -> None:
    rows = report.rows
    if report.signal_count != _count(len(rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _count(_status_count(rows, PASS_STATUS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(rows, WATCH_STATUS)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(rows, BLOCK_STATUS)):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.average_score != _average_score(rows):
        raise ValueError("average_score must match rows")
    if report.weakest_score != min((row.score for row in rows), default=ZERO):
        raise ValueError("weakest_score must match rows")
    if report.highest_conflict_score != max((row.conflict_score for row in rows), default=ZERO):
        raise ValueError("highest_conflict_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _report_values_without_digest(
    report: ResearchStrategyClaimAuthorityMemoryScorecardReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop(DIGEST_FIELD)
    return values


def _without_digest(payload: Mapping[str, Any]) -> dict[str, Any]:
    if DIGEST_FIELD not in payload:
        raise ValueError("derived_validation_digest is required")
    return {key: value for key, value in payload.items() if key != DIGEST_FIELD}


def _digest_from_values(values: Mapping[str, Any]) -> str:
    ready = _json_ready(dict(values))
    _reject_unsafe_public_payload("public payload", ready, allow_json_containers=True)
    encoded = json.dumps(ready, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _digest_reference(*parts: str) -> str:
    encoded = "\x1f".join(parts).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is tuple or type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _reject_unsafe_public_payload(
    context: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(fragment in key_text for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"{context} contains unsafe public payload key")
            _reject_unsafe_public_payload(
                context,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if allow_json_containers and isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(
                context,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        if DIGEST_REFERENCE_RE.fullmatch(value) or SHA256_RE.fullmatch(value):
            return
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{context} contains unsafe public payload value")


def _require_nested_hard_flags(context: str, value: object) -> None:
    if isinstance(value, Mapping):
        if {"paper_only", "report_only", "readonly"} & set(value):
            _require_hard_flags(context, _DictFlags(value))
        for item in value.values():
            _require_nested_hard_flags(context, item)
    elif isinstance(value, list):
        for item in value:
            _require_nested_hard_flags(context, item)


def _require_exact_type(value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"value must be exactly {expected_type.__name__}")


def _require_hard_flags(context: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{context} {field_name} must be True")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_STRATEGY_CLAIM_AUTHORITY_MEMORY_SCORECARD_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_private_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    quantized = _quantize_ratio(value)
    if quantized < ZERO or quantized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return quantized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    quantized = _quantize_ratio(value)
    if quantized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    quantized = _quantize_ratio(value)
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_digest_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_REFERENCE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 reference")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason in values:
        if type(reason) is not str or not REASON_CODE_RE.fullmatch(reason):
            raise ValueError(f"{field_name} must contain reason codes")
        _require_member(field_name, reason, allowed)
        if reason not in normalized:
            normalized.append(reason)
    return tuple(sorted(normalized, key=lambda reason: REASON_SEQUENCE[reason]))


def _require_descending_pair(field_name: str, pass_value: Decimal, watch_value: Decimal) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{field_name} pass value must be at least watch value")


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(Q, rounding=ROUND_HALF_UP)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(Q, rounding=ROUND_HALF_UP)
