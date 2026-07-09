"""Pure public scorecard for memory authority quorum review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping


DEFAULT_RESEARCH_STRATEGY_MEMORY_AUTHORITY_QUORUM_SCORECARD_CONFIG_VERSION = (
    "research-strategy-memory-quorum-scorecard-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_MEMORY_SNAPSHOT_READY = "memory_snapshot_ready"
REASON_MANUAL_REVIEW_REQUESTED = "manual_review_requested"
REASON_MISSING_MEMORY_EVIDENCE = "missing_memory_evidence"
REASON_MEMORY_MATCH_BLOCK = "memory_match_block"
REASON_SOURCE_RANK_BLOCK = "source_rank_block"
REASON_QUORUM_BLOCK = "quorum_block"
REASON_CONTRADICTION_RISK_BLOCK = "contradiction_risk_block"
REASON_AGGREGATE_SCORE_BLOCK = "aggregate_score_block"
REASON_MEMORY_MATCH_WATCH = "memory_match_watch"
REASON_SOURCE_RANK_WATCH = "source_rank_watch"
REASON_QUORUM_WATCH = "quorum_watch"
REASON_CONTRADICTION_RISK_WATCH = "contradiction_risk_watch"
REASON_AGGREGATE_SCORE_WATCH = "aggregate_score_watch"
REASON_MEMORY_QUORUM_PASS = "memory_quorum_pass"

_UPSTREAM_REASON_CODE_SEQUENCE = (
    REASON_MEMORY_SNAPSHOT_READY,
    REASON_MANUAL_REVIEW_REQUESTED,
    REASON_MISSING_MEMORY_EVIDENCE,
)
_GENERATED_REASON_CODE_SEQUENCE = (
    REASON_MEMORY_MATCH_BLOCK,
    REASON_SOURCE_RANK_BLOCK,
    REASON_QUORUM_BLOCK,
    REASON_CONTRADICTION_RISK_BLOCK,
    REASON_AGGREGATE_SCORE_BLOCK,
    REASON_MEMORY_MATCH_WATCH,
    REASON_SOURCE_RANK_WATCH,
    REASON_QUORUM_WATCH,
    REASON_CONTRADICTION_RISK_WATCH,
    REASON_AGGREGATE_SCORE_WATCH,
    REASON_MEMORY_QUORUM_PASS,
)
_REASON_CODE_SEQUENCE = (
    REASON_EMPTY_INPUT,
    *_UPSTREAM_REASON_CODE_SEQUENCE,
    *_GENERATED_REASON_CODE_SEQUENCE,
)

_Q = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_VALUES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _term(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_FRAGMENTS = (
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
    _term("wa", "llet"),
    _term("au", "th"),
    _term("or", "der"),
    _term("li", "ve"),
    _term("tra", "ding"),
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
class ResearchStrategyMemoryAuthorityQuorumScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MEMORY_AUTHORITY_QUORUM_SCORECARD_CONFIG_VERSION
    )
    pass_min_score: Decimal = Decimal("0.800000")
    watch_min_score: Decimal = Decimal("0.600000")
    min_pass_memory_match_score: Decimal = Decimal("0.800000")
    min_watch_memory_match_score: Decimal = Decimal("0.600000")
    min_pass_source_rank_score: Decimal = Decimal("0.750000")
    min_watch_source_rank_score: Decimal = Decimal("0.550000")
    required_quorum_count: Decimal = Decimal("3.000000")
    min_pass_independent_count: Decimal = Decimal("3.000000")
    min_watch_independent_count: Decimal = Decimal("2.000000")
    max_pass_contradiction_risk_score: Decimal = Decimal("0.200000")
    max_watch_contradiction_risk_score: Decimal = Decimal("0.450000")
    memory_match_weight: Decimal = Decimal("0.350000")
    source_rank_weight: Decimal = Decimal("0.250000")
    quorum_weight: Decimal = Decimal("0.250000")
    contradiction_safety_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMemoryAuthorityQuorumScorecardConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MEMORY_AUTHORITY_QUORUM_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_score",
            "watch_min_score",
            "min_pass_memory_match_score",
            "min_watch_memory_match_score",
            "min_pass_source_rank_score",
            "min_watch_source_rank_score",
            "max_pass_contradiction_risk_score",
            "max_watch_contradiction_risk_score",
            "memory_match_weight",
            "source_rank_weight",
            "quorum_weight",
            "contradiction_safety_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "required_quorum_count",
            "min_pass_independent_count",
            "min_watch_independent_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_score < self.watch_min_score:
            raise ValueError("pass_min_score must be at least watch_min_score")
        if self.min_pass_memory_match_score < self.min_watch_memory_match_score:
            raise ValueError(
                "min_pass_memory_match_score must be at least "
                "min_watch_memory_match_score",
            )
        if self.min_pass_source_rank_score < self.min_watch_source_rank_score:
            raise ValueError(
                "min_pass_source_rank_score must be at least min_watch_source_rank_score",
            )
        if self.min_pass_independent_count < self.min_watch_independent_count:
            raise ValueError(
                "min_pass_independent_count must be at least min_watch_independent_count",
            )
        if self.required_quorum_count <= _ZERO:
            raise ValueError("required_quorum_count must be positive")
        if self.min_pass_independent_count > self.required_quorum_count:
            raise ValueError(
                "min_pass_independent_count must not exceed required_quorum_count",
            )
        if (
            self.max_pass_contradiction_risk_score
            > self.max_watch_contradiction_risk_score
        ):
            raise ValueError(
                "max_pass_contradiction_risk_score must not exceed "
                "max_watch_contradiction_risk_score",
            )
        weight_sum = _quantize(
            self.memory_match_weight
            + self.source_rank_weight
            + self.quorum_weight
            + self.contradiction_safety_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("scorecard weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyMemoryAuthorityQuorumInput:
    item_ref: str
    memory_match_score: Decimal
    source_rank_score: Decimal
    independent_source_count: Decimal
    contradiction_risk_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMemoryAuthorityQuorumInput, "input")
        object.__setattr__(
            self,
            "item_ref",
            _require_private_ref("item_ref", self.item_ref),
        )
        for field_name in (
            "memory_match_score",
            "source_rank_score",
            "contradiction_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "independent_source_count",
            _require_nonnegative_decimal(
                "independent_source_count",
                self.independent_source_count,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyMemoryAuthorityQuorumPublicNote:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMemoryAuthorityQuorumPublicNote, "note")
        object.__setattr__(
            self,
            "key",
            _require_public_identifier("key", self.key),
        )
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("note", self)
        _reject_unsafe_public_payload("note", self)


@dataclass(frozen=True)
class ResearchStrategyMemoryAuthorityQuorumScorecardRow:
    item_digest: str
    status: str
    memory_match_score: Decimal
    memory_gap_score: Decimal
    source_rank_score: Decimal
    source_rank_gap_score: Decimal
    independent_source_count: Decimal
    required_quorum_count: Decimal
    quorum_score: Decimal
    contradiction_risk_score: Decimal
    contradiction_safety_score: Decimal
    score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMemoryAuthorityQuorumScorecardRow, "row")
        object.__setattr__(
            self,
            "item_digest",
            _require_private_digest("item_digest", self.item_digest),
        )
        _require_status("status", self.status)
        for field_name in (
            "memory_match_score",
            "memory_gap_score",
            "source_rank_score",
            "source_rank_gap_score",
            "quorum_score",
            "contradiction_risk_score",
            "contradiction_safety_score",
            "score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("independent_source_count", "required_quorum_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_quorum_count <= _ZERO:
            raise ValueError("required_quorum_count must be positive")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyMemoryAuthorityQuorumScorecardReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_score: Decimal
    min_score: Decimal
    max_contradiction_risk_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyMemoryAuthorityQuorumScorecardRow, ...]
    public_notes: tuple[ResearchStrategyMemoryAuthorityQuorumPublicNote, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMemoryAuthorityQuorumScorecardReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_score",
            "min_score",
            "max_contradiction_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "public_notes", _normalize_public_notes(self.public_notes))
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
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match public payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_strategy_memory_authority_quorum_scorecard_report_public_payload(
            self,
        )


def build_research_strategy_memory_authority_quorum_scorecard_report(
    *,
    items: object,
    generated_at: datetime,
    config: ResearchStrategyMemoryAuthorityQuorumScorecardConfig
    | None = None,
    public_notes: object = (),
) -> ResearchStrategyMemoryAuthorityQuorumScorecardReport:
    generated_at = _as_utc("generated_at", generated_at)
    resolved_config = config or ResearchStrategyMemoryAuthorityQuorumScorecardConfig()
    if type(resolved_config) is not ResearchStrategyMemoryAuthorityQuorumScorecardConfig:
        raise ValueError("config must be a ResearchStrategyMemoryAuthorityQuorumScorecardConfig")
    _require_hard_flags("config", resolved_config)
    normalized_items = _normalize_inputs(items)
    notes = _normalize_public_notes(public_notes)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=resolved_config)
                for item in normalized_items
            ),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": resolved_config.config_version,
        "status": _report_status(rows),
        "row_count": _count(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "average_score": _average_score(rows),
        "min_score": _min_score(rows),
        "max_contradiction_risk_score": _max_contradiction_risk_score(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "public_notes": notes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyMemoryAuthorityQuorumScorecardReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_strategy_memory_authority_quorum_scorecard_report_public_payload(
    report: ResearchStrategyMemoryAuthorityQuorumScorecardReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyMemoryAuthorityQuorumScorecardReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("public payload must be a JSON object")
        return validate_research_strategy_memory_authority_quorum_scorecard_report_public_payload(
            payload,
        )
    return validate_research_strategy_memory_authority_quorum_scorecard_report_public_payload(
        report,
    )


def research_strategy_memory_authority_quorum_scorecard_report_digest(
    report: ResearchStrategyMemoryAuthorityQuorumScorecardReport | Mapping[str, Any],
) -> str:
    payload = research_strategy_memory_authority_quorum_scorecard_report_public_payload(
        report,
    )
    return _require_sha256_digest(_DIGEST_FIELD, payload[_DIGEST_FIELD])


def validate_research_strategy_memory_authority_quorum_scorecard_report_public_payload(
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
    digest = _require_sha256_digest(_DIGEST_FIELD, ready.get(_DIGEST_FIELD))
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
    item: ResearchStrategyMemoryAuthorityQuorumInput,
    *,
    config: ResearchStrategyMemoryAuthorityQuorumScorecardConfig,
) -> ResearchStrategyMemoryAuthorityQuorumScorecardRow:
    quorum_score = _ratio_capped(item.independent_source_count, config.required_quorum_count)
    contradiction_safety_score = _quantize(_ONE - item.contradiction_risk_score)
    score = _quantize(
        item.memory_match_score * config.memory_match_weight
        + item.source_rank_score * config.source_rank_weight
        + quorum_score * config.quorum_weight
        + contradiction_safety_score * config.contradiction_safety_weight,
    )
    reason_codes = _row_reason_codes(
        item,
        score=score,
        config=config,
    )
    return ResearchStrategyMemoryAuthorityQuorumScorecardRow(
        item_digest=_private_digest(item.item_ref),
        status=_row_status(reason_codes),
        memory_match_score=item.memory_match_score,
        memory_gap_score=_quantize(_ONE - item.memory_match_score),
        source_rank_score=item.source_rank_score,
        source_rank_gap_score=_quantize(_ONE - item.source_rank_score),
        independent_source_count=item.independent_source_count,
        required_quorum_count=config.required_quorum_count,
        quorum_score=quorum_score,
        contradiction_risk_score=item.contradiction_risk_score,
        contradiction_safety_score=contradiction_safety_score,
        score=score,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchStrategyMemoryAuthorityQuorumInput,
    *,
    score: Decimal,
    config: ResearchStrategyMemoryAuthorityQuorumScorecardConfig,
) -> tuple[str, ...]:
    reasons = list(item.reason_codes)
    if item.memory_match_score < config.min_watch_memory_match_score:
        reasons.append(REASON_MEMORY_MATCH_BLOCK)
    elif item.memory_match_score < config.min_pass_memory_match_score:
        reasons.append(REASON_MEMORY_MATCH_WATCH)
    if item.source_rank_score < config.min_watch_source_rank_score:
        reasons.append(REASON_SOURCE_RANK_BLOCK)
    elif item.source_rank_score < config.min_pass_source_rank_score:
        reasons.append(REASON_SOURCE_RANK_WATCH)
    if item.independent_source_count < config.min_watch_independent_count:
        reasons.append(REASON_QUORUM_BLOCK)
    elif item.independent_source_count < config.min_pass_independent_count:
        reasons.append(REASON_QUORUM_WATCH)
    if item.contradiction_risk_score > config.max_watch_contradiction_risk_score:
        reasons.append(REASON_CONTRADICTION_RISK_BLOCK)
    elif item.contradiction_risk_score > config.max_pass_contradiction_risk_score:
        reasons.append(REASON_CONTRADICTION_RISK_WATCH)
    if score < config.watch_min_score:
        reasons.append(REASON_AGGREGATE_SCORE_BLOCK)
    elif score < config.pass_min_score:
        reasons.append(REASON_AGGREGATE_SCORE_WATCH)
    if len(reasons) == len(item.reason_codes):
        reasons.append(REASON_MEMORY_QUORUM_PASS)
    return _normalize_reason_codes(tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return STATUS_BLOCK
    if any(reason.endswith("_watch") for reason in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[ResearchStrategyMemoryAuthorityQuorumScorecardRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategyMemoryAuthorityQuorumScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_EMPTY_INPUT,)
    return _normalize_reason_codes(
        tuple(dict.fromkeys(reason for row in rows for reason in row.reason_codes)),
    )


def _normalize_inputs(
    items: object,
) -> tuple[ResearchStrategyMemoryAuthorityQuorumInput, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("items must be an iterable") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchStrategyMemoryAuthorityQuorumInput:
            raise ValueError("items must contain ResearchStrategyMemoryAuthorityQuorumInput")
        _require_hard_flags("input", item)
        item_digest = _private_digest(item.item_ref)
        if item_digest in seen:
            raise ValueError("items must contain unique item_ref values")
        seen.add(item_digest)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyMemoryAuthorityQuorumScorecardRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchStrategyMemoryAuthorityQuorumScorecardRow:
            raise ValueError("rows must contain ResearchStrategyMemoryAuthorityQuorumScorecardRow")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_public_notes(
    public_notes: object,
) -> tuple[ResearchStrategyMemoryAuthorityQuorumPublicNote, ...]:
    if isinstance(public_notes, (str, bytes)):
        raise ValueError("public_notes must be an iterable")
    try:
        normalized = tuple(public_notes)
    except TypeError as exc:
        raise ValueError("public_notes must be an iterable") from exc
    seen: set[str] = set()
    for note in normalized:
        if type(note) is not ResearchStrategyMemoryAuthorityQuorumPublicNote:
            raise ValueError(
                "public_notes must contain ResearchStrategyMemoryAuthorityQuorumPublicNote",
            )
        _require_hard_flags("note", note)
        _reject_unsafe_public_payload("note", note)
        if note.key in seen:
            raise ValueError("public_notes must contain unique keys")
        seen.add(note.key)
    return tuple(sorted(normalized, key=lambda note: (note.key, note.value)))


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason in normalized:
        _require_public_identifier("reason_codes", reason)
        _reject_unsafe_public_text("reason_codes", reason)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(sorted(normalized, key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    try:
        return (_REASON_CODE_SEQUENCE.index(reason_code), reason_code)
    except ValueError:
        return (len(_REASON_CODE_SEQUENCE), reason_code)


def _row_sort_key(
    row: ResearchStrategyMemoryAuthorityQuorumScorecardRow,
) -> tuple[int, Decimal, str]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[row.status],
        row.score,
        row.item_digest,
    )


def _status_count(
    rows: tuple[ResearchStrategyMemoryAuthorityQuorumScorecardRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_score(
    rows: tuple[ResearchStrategyMemoryAuthorityQuorumScorecardRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return _quantize(sum((row.score for row in rows), _ZERO) / _count(len(rows)))


def _min_score(
    rows: tuple[ResearchStrategyMemoryAuthorityQuorumScorecardRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return min(row.score for row in rows)


def _max_contradiction_risk_score(
    rows: tuple[ResearchStrategyMemoryAuthorityQuorumScorecardRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return max(row.contradiction_risk_score for row in rows)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio_capped(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    value = _quantize(numerator / denominator)
    if value > _ONE:
        return _ONE
    return value


def _private_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _report_values_without_digest(
    report: ResearchStrategyMemoryAuthorityQuorumScorecardReport,
) -> dict[str, object]:
    return _without_digest(asdict(report))


def _without_digest(value: Mapping[str, object]) -> dict[str, object]:
    unsigned = dict(value)
    unsigned.pop(_DIGEST_FIELD, None)
    return unsigned


def _digest_from_values(values: Mapping[str, object]) -> str:
    ready = _json_ready(dict(values))
    _reject_unsafe_public_payload("digest payload", ready, allow_json_containers=True)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric values must be Decimal-derived strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=True,
        )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers and type(value) is not dict:
            raise ValueError(f"{label} must use standard JSON containers")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            if key == _DIGEST_FIELD:
                _require_sha256_digest(key, item)
                continue
            if key.endswith("_digest"):
                _require_private_digest(key, item)
                continue
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers and type(value) not in (list, tuple):
            raise ValueError(f"{label} must use standard JSON containers")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


def _require_nested_hard_flags(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for field_name in _FLAG_FIELDS:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True for {label}")
        for item in value.values():
            _require_nested_hard_flags(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _require_nested_hard_flags(label, item)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _PRIVATE_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a private SHA-256 digest")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_Q, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise TypeError(f"{label} must be {expected_type.__name__}")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MEMORY_AUTHORITY_QUORUM_SCORECARD_CONFIG_VERSION",
    "ResearchStrategyMemoryAuthorityQuorumScorecardConfig",
    "ResearchStrategyMemoryAuthorityQuorumInput",
    "ResearchStrategyMemoryAuthorityQuorumPublicNote",
    "ResearchStrategyMemoryAuthorityQuorumScorecardRow",
    "ResearchStrategyMemoryAuthorityQuorumScorecardReport",
    "build_research_strategy_memory_authority_quorum_scorecard_report",
    "research_strategy_memory_authority_quorum_scorecard_report_public_payload",
    "research_strategy_memory_authority_quorum_scorecard_report_digest",
    "validate_research_strategy_memory_authority_quorum_scorecard_report_public_payload",
)
