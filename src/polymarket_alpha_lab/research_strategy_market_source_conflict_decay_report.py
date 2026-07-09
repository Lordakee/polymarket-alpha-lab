"""Pure report-only market source conflict decay snapshot.

Callers supply in-memory observations. The module returns deterministic,
read-only report objects and public JSON payloads with raw market/source
surfaces represented only by stable SHA-256 digests.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_MARKET_SOURCE_CONFLICT_DECAY_CONFIG_VERSION = (
    "research-strategy-market-source-conflict-decay-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_HEX = frozenset("0123456789abcdef")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_INPUT_REASON_CODES = ("manual_reviewed",)
_REASON_CODE_SEQUENCE = (
    "no_source_observations",
    "input_manual_reviewed",
    "market_source_conflict_pass",
    "source_conflict_watch",
    "source_conflict_block",
)
_PUBLIC_UNSAFE_FRAGMENTS = (
    "://" ,
    "?" ,
    "@" ,
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tr" + "ade",
    "siz" + "ing",
    "reco" + "mmend",
    "private" + "_key",
    "secret",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MARKET_SOURCE_CONFLICT_DECAY_CONFIG_VERSION",
    "STATUSES",
    "ResearchStrategyMarketSourceConflictDecayConfig",
    "ResearchStrategyMarketSourceConflictDecayObservation",
    "ResearchStrategyMarketSourceConflictDecayReasonCodeCount",
    "ResearchStrategyMarketSourceConflictDecayReport",
    "ResearchStrategyMarketSourceConflictDecayRow",
    "build_research_strategy_market_source_conflict_decay_report",
    "research_strategy_market_source_conflict_decay_report_digest",
    "research_strategy_market_source_conflict_decay_report_payload",
    "validate_research_strategy_market_source_conflict_decay_report_payload",
)


@dataclass(frozen=True)
class ResearchStrategyMarketSourceConflictDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MARKET_SOURCE_CONFLICT_DECAY_CONFIG_VERSION
    )
    fresh_age_seconds: Decimal = Decimal("3600.000000")
    stale_age_seconds: Decimal = Decimal("86400.000000")
    watch_decayed_conflict_score: Decimal = Decimal("0.100000")
    block_decayed_conflict_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMarketSourceConflictDecayConfig, "config")
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MARKET_SOURCE_CONFLICT_DECAY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_age_seconds", "stale_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must exceed fresh_age_seconds")
        for field_name in (
            "watch_decayed_conflict_score",
            "block_decayed_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_decayed_conflict_score <= self.watch_decayed_conflict_score:
            raise ValueError(
                "block_decayed_conflict_score must exceed watch_decayed_conflict_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyMarketSourceConflictDecayObservation:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_id: str
    source_family: str
    source_probability: Decimal
    reference_probability: Decimal
    confidence_score: Decimal
    observed_at: datetime
    source_url: str | None = None
    source_text: str | None = None
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketSourceConflictDecayObservation,
            "observation",
        )
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "source_id",
            "source_family",
        ):
            _require_private_text(field_name, getattr(self, field_name))
        for field_name in (
            "source_probability",
            "reference_probability",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_url",
            _require_optional_private_text("source_url", self.source_url),
        )
        object.__setattr__(
            self,
            "source_text",
            _require_optional_private_text("source_text", self.source_text),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchStrategyMarketSourceConflictDecayRow:
    market_group_digest: str
    source_count: Decimal
    source_family_count: Decimal
    conflict_observation_count: Decimal
    average_conflict_delta: Decimal
    max_conflict_delta: Decimal
    average_recency_score: Decimal
    decayed_conflict_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMarketSourceConflictDecayRow, "row")
        _require_sha256_digest("market_group_digest", self.market_group_digest)
        for field_name in (
            "source_count",
            "source_family_count",
            "conflict_observation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_conflict_delta",
            "max_conflict_delta",
            "average_recency_score",
            "decayed_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyMarketSourceConflictDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketSourceConflictDecayReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyMarketSourceConflictDecayReport:
    generated_at: datetime
    config_version: str
    status: str
    group_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_decayed_conflict_score: Decimal
    max_conflict_delta: Decimal
    rows: tuple[ResearchStrategyMarketSourceConflictDecayRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyMarketSourceConflictDecayReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMarketSourceConflictDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MARKET_SOURCE_CONFLICT_DECAY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "group_count",
            "observation_count",
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
            "average_decayed_conflict_score",
            "max_conflict_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_strategy_market_source_conflict_decay_report(
    observations: Iterable[object],
    *,
    config: ResearchStrategyMarketSourceConflictDecayConfig,
    generated_at: datetime,
) -> ResearchStrategyMarketSourceConflictDecayReport:
    if type(config) is not ResearchStrategyMarketSourceConflictDecayConfig:
        raise ValueError("config must be ResearchStrategyMarketSourceConflictDecayConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    rows = _build_rows(items, generated_at=generated_at_utc, config=config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "group_count": _decimal_count(len(rows)),
        "observation_count": _decimal_count(len(items)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_decayed_conflict_score": _average(
            tuple(row.decayed_conflict_score for row in rows),
        ),
        "max_conflict_delta": max(
            (row.max_conflict_delta for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyMarketSourceConflictDecayReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_market_source_conflict_decay_report_payload(
    report: ResearchStrategyMarketSourceConflictDecayReport,
) -> "FrozenJsonObject":
    if type(report) is not ResearchStrategyMarketSourceConflictDecayReport:
        raise ValueError("report must be ResearchStrategyMarketSourceConflictDecayReport")
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    validate_research_strategy_market_source_conflict_decay_report_payload(payload)
    return _freeze_json_object(payload)


def research_strategy_market_source_conflict_decay_report_digest(
    report: ResearchStrategyMarketSourceConflictDecayReport,
) -> str:
    if type(report) is not ResearchStrategyMarketSourceConflictDecayReport:
        raise ValueError("report must be ResearchStrategyMarketSourceConflictDecayReport")
    return report.derived_validation_digest


def validate_research_strategy_market_source_conflict_decay_report_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_payload_value(payload)
    _require_payload_flags(payload)
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    expected_digest = _payload_digest(without_digest)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match payload")


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _build_rows(
    observations: tuple[ResearchStrategyMarketSourceConflictDecayObservation, ...],
    *,
    generated_at: datetime,
    config: ResearchStrategyMarketSourceConflictDecayConfig,
) -> tuple[ResearchStrategyMarketSourceConflictDecayRow, ...]:
    grouped: dict[
        tuple[str, str, str, str],
        list[ResearchStrategyMarketSourceConflictDecayObservation],
    ] = {}
    for item in observations:
        grouped.setdefault(
            (item.candidate_id, item.market_id, item.market_slug, item.market_question),
            [],
        ).append(item)
    return tuple(
        _row_for_group(
            group_key,
            tuple(grouped[group_key]),
            generated_at=generated_at,
            config=config,
        )
        for group_key in sorted(grouped)
    )


def _row_for_group(
    group_key: tuple[str, str, str, str],
    observations: tuple[ResearchStrategyMarketSourceConflictDecayObservation, ...],
    *,
    generated_at: datetime,
    config: ResearchStrategyMarketSourceConflictDecayConfig,
) -> ResearchStrategyMarketSourceConflictDecayRow:
    sorted_observations = tuple(
        sorted(
            observations,
            key=lambda item: (item.observed_at, item.source_family, item.source_id),
        ),
    )
    source_count = len(sorted_observations)
    source_family_count = len({item.source_family for item in sorted_observations})
    conflict_deltas = tuple(
        _quantize(abs(item.source_probability - item.reference_probability))
        for item in sorted_observations
    )
    recency_scores = tuple(
        _recency_score(
            _age_seconds(generated_at, item.observed_at),
            fresh_age_seconds=config.fresh_age_seconds,
            stale_age_seconds=config.stale_age_seconds,
        )
        for item in sorted_observations
    )
    decayed_scores = tuple(
        _quantize(delta * recency * item.confidence_score)
        for delta, recency, item in zip(
            conflict_deltas,
            recency_scores,
            sorted_observations,
            strict=True,
        )
    )
    decayed_conflict_score = _average(decayed_scores)
    status = _status_for_score(decayed_conflict_score, config)
    input_reasons = tuple(
        f"input_{reason_code}"
        for item in sorted_observations
        for reason_code in item.reason_codes
    )
    reason_codes = _row_reason_codes(status=status, input_reason_codes=input_reasons)
    return ResearchStrategyMarketSourceConflictDecayRow(
        market_group_digest=_group_digest(group_key),
        source_count=_decimal_count(source_count),
        source_family_count=_decimal_count(source_family_count),
        conflict_observation_count=_decimal_count(
            sum(1 for delta in conflict_deltas if delta > _ZERO),
        ),
        average_conflict_delta=_average(conflict_deltas),
        max_conflict_delta=max(conflict_deltas, default=_ZERO),
        average_recency_score=_average(recency_scores),
        decayed_conflict_score=decayed_conflict_score,
        status=status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    status: str,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reasons = list(input_reason_codes)
    if status == STATUS_BLOCK:
        reasons.append("source_conflict_block")
    elif status == STATUS_WATCH:
        reasons.append("source_conflict_watch")
    else:
        reasons.append("market_source_conflict_pass")
    return _normalize_report_reason_codes(tuple(reasons), allow_empty=False)


def _status_for_score(
    score: Decimal,
    config: ResearchStrategyMarketSourceConflictDecayConfig,
) -> str:
    if score >= config.block_decayed_conflict_score:
        return STATUS_BLOCK
    if score >= config.watch_decayed_conflict_score:
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[ResearchStrategyMarketSourceConflictDecayRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategyMarketSourceConflictDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_source_observations",)
    return _normalize_report_reason_codes(
        tuple(reason for row in rows for reason in row.reason_codes),
        allow_empty=False,
    )


def _reason_code_counts(
    rows: tuple[ResearchStrategyMarketSourceConflictDecayRow, ...],
) -> tuple[ResearchStrategyMarketSourceConflictDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyMarketSourceConflictDecayReasonCodeCount(
                reason_code="no_source_observations",
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyMarketSourceConflictDecayReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if counts[reason_code]
    )


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchStrategyMarketSourceConflictDecayObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized: list[ResearchStrategyMarketSourceConflictDecayObservation] = []
    for item in observations:
        if type(item) is not ResearchStrategyMarketSourceConflictDecayObservation:
            raise ValueError(
                "observations must contain "
                "ResearchStrategyMarketSourceConflictDecayObservation",
            )
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.candidate_id,
                item.market_id,
                item.market_slug,
                item.market_question,
                item.observed_at,
                item.source_family,
                item.source_id,
            ),
        ),
    )


def _normalize_rows(
    rows: tuple[ResearchStrategyMarketSourceConflictDecayRow, ...],
) -> tuple[ResearchStrategyMarketSourceConflictDecayRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchStrategyMarketSourceConflictDecayRow] = []
    for row in rows:
        if type(row) is not ResearchStrategyMarketSourceConflictDecayRow:
            raise ValueError(
                "rows must contain ResearchStrategyMarketSourceConflictDecayRow",
            )
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.market_group_digest))


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyMarketSourceConflictDecayReasonCodeCount, ...],
) -> tuple[ResearchStrategyMarketSourceConflictDecayReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchStrategyMarketSourceConflictDecayReasonCodeCount] = []
    seen: set[str] = set()
    for count in counts:
        if type(count) is not ResearchStrategyMarketSourceConflictDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyMarketSourceConflictDecayReasonCodeCount",
            )
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(count.reason_code)
        normalized.append(count)
    return tuple(
        sorted(
            normalized,
            key=lambda count: _REASON_CODE_SEQUENCE.index(count.reason_code),
        ),
    )


def _normalize_input_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_code must be a string")
        if reason_code not in _INPUT_REASON_CODES:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _normalize_report_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not allow_empty and not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _validate_row_consistency(
    row: ResearchStrategyMarketSourceConflictDecayRow,
) -> None:
    if row.source_family_count > row.source_count:
        raise ValueError("source_family_count must not exceed source_count")
    if row.conflict_observation_count > row.source_count:
        raise ValueError("conflict_observation_count must not exceed source_count")
    if row.average_conflict_delta > row.max_conflict_delta:
        raise ValueError("average_conflict_delta must not exceed max_conflict_delta")
    expected_status_reason = {
        STATUS_PASS: "market_source_conflict_pass",
        STATUS_WATCH: "source_conflict_watch",
        STATUS_BLOCK: "source_conflict_block",
    }[row.status]
    if expected_status_reason not in row.reason_codes:
        raise ValueError("reason_codes must match status")


def _validate_report_consistency(
    report: ResearchStrategyMarketSourceConflictDecayReport,
) -> None:
    if report.group_count != _decimal_count(len(report.rows)):
        raise ValueError("group_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_decayed_conflict_score != _average(
        tuple(row.decayed_conflict_score for row in report.rows),
    ):
        raise ValueError("average_decayed_conflict_score must match rows")
    expected_max_delta = max(
        (row.max_conflict_delta for row in report.rows),
        default=_ZERO,
    )
    if report.max_conflict_delta != expected_max_delta:
        raise ValueError("max_conflict_delta must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchStrategyMarketSourceConflictDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _recency_score(
    age_seconds: Decimal,
    *,
    fresh_age_seconds: Decimal,
    stale_age_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_age_seconds:
        return _ONE
    if age_seconds >= stale_age_seconds:
        return _ZERO
    stale_window = stale_age_seconds - fresh_age_seconds
    return _bounded_probability(_ONE - ((age_seconds - fresh_age_seconds) / stale_window))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    return _quantize(Decimal(str((generated_at - observed_at).total_seconds())))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _group_digest(group_key: tuple[str, str, str, str]) -> str:
    payload = json.dumps(group_key, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchStrategyMarketSourceConflictDecayReport,
) -> dict[str, object]:
    values = _json_ready(report, skip_derived_validation_digest=True)
    if type(values) is not dict:
        raise ValueError("report values must be a JSON object")
    return values


def _report_digest_from_values(values: dict[str, object]) -> str:
    return _payload_digest(_json_ready(values))


def _payload_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any, *, skip_derived_validation_digest: bool = False) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            if skip_derived_validation_digest and field.name == "derived_validation_digest":
                continue
            ready[field.name] = _json_ready(
                getattr(value, field.name),
                skip_derived_validation_digest=skip_derived_validation_digest,
            )
        return ready
    if isinstance(value, dict):
        return {
            str(key): _json_ready(
                item,
                skip_derived_validation_digest=skip_derived_validation_digest,
            )
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [
            _json_ready(item, skip_derived_validation_digest=skip_derived_validation_digest)
            for item in value
        ]
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _validate_public_payload_value(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _require_public_text("payload key", str(key))
            _validate_public_payload_value(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_public_payload_value(item)
        return
    if type(value) is str:
        _reject_unsafe_public_text("payload value", value)
        return
    if type(value) is bool or value is None:
        return
    raise ValueError("payload must contain only JSON-ready string and bool values")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in payload")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_private_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty text")
    if len(value) > 1024:
        raise ValueError(f"{field_name} must not exceed 1024 characters")
    return value


def _require_optional_private_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_private_text(field_name, value)


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 256:
        raise ValueError(f"{field_name} must not exceed 256 characters")
    _reject_unsafe_public_text(field_name, value)
    return value


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _PUBLIC_UNSAFE_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64 or set(value) - _DIGEST_HEX:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _bounded_probability(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized
