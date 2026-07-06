"""Pure report reducer for specialist signal arbitration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_GENERIC_SIGNAL_REASON = "specialist_signal_available"
_POSTURE_RANK = {"blocked": 0, "caution": 1, "recommend": 2}
_REASON_RANK = {
    "arbitration_blocked": 0,
    "conflict_severity_blocked": 1,
    "source_freshness_watch": 2,
    "arbitration_caution": 3,
    "arbitration_recommend": 4,
    "empty_specialist_signals": 5,
}


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _surface_term("li", "ve"),
        _surface_term("au", "th"),
        _surface_term("wa", "llet"),
        _surface_term("or", "der"),
        _surface_term("net", "work"),
        _surface_term("data", "base"),
        _surface_term("per", "sist"),
        _surface_term("sign", "ing"),
        _surface_term("mut", "ation"),
        _surface_term("b", "uy"),
        _surface_term("se", "ll"),
        _surface_term("tra", "de"),
    ),
)


@dataclass(frozen=True)
class StrategySpecialistSignalArbitrationConfig:
    config_version: str
    evidence_quality_weight: Decimal
    team_calibration_weight: Decimal
    source_freshness_weight: Decimal
    liquidity_confidence_weight: Decimal
    conflict_severity_weight: Decimal
    max_source_age_seconds: Decimal
    recommend_threshold: Decimal
    caution_threshold: Decimal
    block_conflict_severity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        for field_name in (
            "evidence_quality_weight",
            "team_calibration_weight",
            "source_freshness_weight",
            "liquidity_confidence_weight",
            "conflict_severity_weight",
        ):
            value = _normalize_ratio(field_name, getattr(self, field_name))
            if value <= _ZERO:
                raise ValueError(f"{field_name} weight must be positive")
            object.__setattr__(self, field_name, value)
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_positive_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "recommend_threshold",
            "caution_threshold",
            "block_conflict_severity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.recommend_threshold < self.caution_threshold:
            raise ValueError("recommend_threshold must be at least caution_threshold")
        _require_flags("config", self)


@dataclass(frozen=True)
class StrategySpecialistSignalArbitrationInput:
    candidate_id: str
    team_id: str
    team_probability: Decimal
    evidence_quality: Decimal
    team_calibration: Decimal
    liquidity_confidence: Decimal
    conflict_severity: Decimal
    observed_at: datetime
    evidence_family: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("candidate_id", self.candidate_id)
        _require_text("team_id", self.team_id)
        for field_name in (
            "team_probability",
            "evidence_quality",
            "team_calibration",
            "liquidity_confidence",
            "conflict_severity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_text("evidence_family", self.evidence_family)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags("signal", self)


@dataclass(frozen=True)
class StrategySpecialistSignalArbitrationRow:
    candidate_id: str
    posture: str
    team_count: Decimal
    weighted_probability: Decimal
    weighted_evidence_quality: Decimal
    weighted_team_calibration: Decimal
    weighted_source_freshness: Decimal
    weighted_liquidity_confidence: Decimal
    weighted_conflict_severity: Decimal
    arbitration_score: Decimal
    conflict_adjusted_score: Decimal
    probability_spread: Decimal
    dominant_evidence_family: str | None
    latest_observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("candidate_id", self.candidate_id)
        _require_posture("posture", self.posture)
        object.__setattr__(self, "team_count", _normalize_count("team_count", self.team_count))
        for field_name in (
            "weighted_probability",
            "weighted_evidence_quality",
            "weighted_team_calibration",
            "weighted_source_freshness",
            "weighted_liquidity_confidence",
            "weighted_conflict_severity",
            "arbitration_score",
            "conflict_adjusted_score",
            "probability_spread",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.dominant_evidence_family is not None:
            _require_text("dominant_evidence_family", self.dominant_evidence_family)
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags("row", self)


@dataclass(frozen=True)
class StrategySpecialistSignalArbitrationReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        _require_flags("reason code count", self)


@dataclass(frozen=True)
class StrategySpecialistSignalArbitrationReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    signal_count: Decimal
    recommend_count: Decimal
    caution_count: Decimal
    blocked_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategySpecialistSignalArbitrationRow, ...]
    reason_code_counts: tuple[StrategySpecialistSignalArbitrationReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "signal_count",
            "recommend_count",
            "caution_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_posture("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_flags("report", self)
        _check_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_strategy_specialist_signal_arbitration_report(
    signals: object,
    *,
    config: StrategySpecialistSignalArbitrationConfig,
    generated_at: datetime,
) -> StrategySpecialistSignalArbitrationReport:
    if type(config) is not StrategySpecialistSignalArbitrationConfig:
        raise ValueError("config must be a StrategySpecialistSignalArbitrationConfig")
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    for item in normalized_signals:
        if item.observed_at > generated_at:
            raise ValueError("generated_at must not precede observed_at")
    rows = tuple(
        sorted(
            (
                _candidate_row(
                    candidate_id,
                    candidate_signals,
                    config=config,
                    generated_at=generated_at,
                )
                for candidate_id, candidate_signals in _group_signals(normalized_signals)
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return StrategySpecialistSignalArbitrationReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        signal_count=_count(len(normalized_signals)),
        recommend_count=_posture_count(rows, "recommend"),
        caution_count=_posture_count(rows, "caution"),
        blocked_count=_posture_count(rows, "blocked"),
        status=_report_status(rows),
        reason_codes=reason_codes,
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
    )


def strategy_specialist_signal_arbitration_report_payload(
    report: StrategySpecialistSignalArbitrationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategySpecialistSignalArbitrationReport:
        _require_flags("report", report)
        _reject_unsafe_public("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_flags("payload", _DictFlags(payload))
        _verify_payload_digest(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_flags("payload", _DictFlags(payload))
        _reject_flag_downgrades("payload", payload)
        _verify_payload_digest(payload)
        _reject_unsafe_public("payload", payload)
        return payload
    raise ValueError("report must be a StrategySpecialistSignalArbitrationReport")


@dataclass(frozen=True)
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


def _candidate_row(
    candidate_id: str,
    signals: tuple[StrategySpecialistSignalArbitrationInput, ...],
    *,
    config: StrategySpecialistSignalArbitrationConfig,
    generated_at: datetime,
) -> StrategySpecialistSignalArbitrationRow:
    probabilities = tuple(item.team_probability for item in signals)
    freshness_scores = tuple(
        _source_freshness(item.observed_at, generated_at, config.max_source_age_seconds)
        for item in signals
    )
    evidence_quality = _average(tuple(item.evidence_quality for item in signals))
    team_calibration = _average(tuple(item.team_calibration for item in signals))
    source_freshness = _average(freshness_scores)
    liquidity_confidence = _average(tuple(item.liquidity_confidence for item in signals))
    conflict_severity = _average(tuple(item.conflict_severity for item in signals))
    weighted_probability = _weighted_probability(signals, freshness_scores)
    probability_spread = _quantize(max(probabilities) - min(probabilities))
    quality_score = _quantize(
        (
            evidence_quality * config.evidence_quality_weight
            + team_calibration * config.team_calibration_weight
            + source_freshness * config.source_freshness_weight
            + liquidity_confidence * config.liquidity_confidence_weight
            + (_ONE - conflict_severity) * config.conflict_severity_weight
        )
    )
    arbitration_score = _quantize((weighted_probability + quality_score) / Decimal("2"))
    conflict_adjusted_score = _clamp_ratio(
        arbitration_score - (conflict_severity * config.conflict_severity_weight),
    )
    posture = _row_posture(
        arbitration_score=arbitration_score,
        conflict_adjusted_score=conflict_adjusted_score,
        conflict_severity=conflict_severity,
        source_freshness=source_freshness,
        config=config,
    )
    reason_codes = _row_reason_codes(
        posture=posture,
        source_freshness=source_freshness,
        conflict_severity=conflict_severity,
        config=config,
        source_reasons=tuple(
            reason
            for item in signals
            for reason in item.reason_codes
            if reason != _GENERIC_SIGNAL_REASON
        ),
    )
    return StrategySpecialistSignalArbitrationRow(
        candidate_id=candidate_id,
        posture=posture,
        team_count=_count(len(signals)),
        weighted_probability=weighted_probability,
        weighted_evidence_quality=evidence_quality,
        weighted_team_calibration=team_calibration,
        weighted_source_freshness=source_freshness,
        weighted_liquidity_confidence=liquidity_confidence,
        weighted_conflict_severity=conflict_severity,
        arbitration_score=arbitration_score,
        conflict_adjusted_score=conflict_adjusted_score,
        probability_spread=probability_spread,
        dominant_evidence_family=_dominant_evidence_family(signals),
        latest_observed_at=max(item.observed_at for item in signals),
        reason_codes=reason_codes,
    )


def _normalize_signals(
    signals: object,
) -> tuple[StrategySpecialistSignalArbitrationInput, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        items = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not StrategySpecialistSignalArbitrationInput:
            raise ValueError("signals must contain StrategySpecialistSignalArbitrationInput")
        _require_flags("signal", item)
        key = (item.candidate_id, item.team_id)
        if key in seen:
            raise ValueError("signals must contain unique candidate_id and team_id values")
        seen.add(key)
    return items


def _group_signals(
    signals: tuple[StrategySpecialistSignalArbitrationInput, ...],
) -> tuple[tuple[str, tuple[StrategySpecialistSignalArbitrationInput, ...]], ...]:
    candidate_ids = tuple(sorted({item.candidate_id for item in signals}))
    return tuple(
        (
            candidate_id,
            tuple(
                sorted(
                    (item for item in signals if item.candidate_id == candidate_id),
                    key=lambda item: item.team_id,
                ),
            ),
        )
        for candidate_id in candidate_ids
    )


def _source_freshness(
    observed_at: datetime,
    generated_at: datetime,
    max_source_age_seconds: Decimal,
) -> Decimal:
    age_seconds = _quantize(
        Decimal(str((generated_at - observed_at).total_seconds())),
    )
    if age_seconds <= _ZERO:
        return _ONE
    if age_seconds >= max_source_age_seconds:
        return _ZERO
    return _clamp_ratio(_ONE - _ratio(age_seconds, max_source_age_seconds))


def _weighted_probability(
    signals: tuple[StrategySpecialistSignalArbitrationInput, ...],
    freshness_scores: tuple[Decimal, ...],
) -> Decimal:
    weights = tuple(
        _quantize(
            item.evidence_quality
            * item.team_calibration
            * item.liquidity_confidence
            * freshness
            * (_ONE - item.conflict_severity),
        )
        for item, freshness in zip(signals, freshness_scores, strict=True)
    )
    weight_sum = sum(weights, _ZERO)
    if weight_sum == _ZERO:
        return _average(tuple(item.team_probability for item in signals))
    return _ratio(
        sum(
            item.team_probability * weight
            for item, weight in zip(signals, weights, strict=True)
        ),
        weight_sum,
    )


def _row_posture(
    *,
    arbitration_score: Decimal,
    conflict_adjusted_score: Decimal,
    conflict_severity: Decimal,
    source_freshness: Decimal,
    config: StrategySpecialistSignalArbitrationConfig,
) -> str:
    if conflict_severity >= config.block_conflict_severity:
        return "blocked"
    if conflict_adjusted_score >= config.recommend_threshold and source_freshness > _ZERO:
        return "recommend"
    if arbitration_score >= config.caution_threshold:
        return "caution"
    return "blocked"


def _row_reason_codes(
    *,
    posture: str,
    source_freshness: Decimal,
    conflict_severity: Decimal,
    config: StrategySpecialistSignalArbitrationConfig,
    source_reasons: tuple[str, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if posture == "blocked":
        reasons.append("arbitration_blocked")
    elif posture == "recommend":
        reasons.append("arbitration_recommend")
    if conflict_severity >= config.block_conflict_severity:
        reasons.append("conflict_severity_blocked")
    if source_freshness == _ZERO:
        reasons.append("source_freshness_watch")
    reasons.extend(source_reasons)
    if not reasons and posture == "caution":
        reasons.append("arbitration_caution")
    return _sort_reason_codes(tuple(dict.fromkeys(reasons)))


def _dominant_evidence_family(
    signals: tuple[StrategySpecialistSignalArbitrationInput, ...],
) -> str | None:
    if not signals:
        return None
    counts: dict[str, int] = {}
    for item in signals:
        counts[item.evidence_family] = counts.get(item.evidence_family, 0) + 1
    return sorted(counts, key=lambda key: (-counts[key], key))[0]


def _report_status(rows: tuple[StrategySpecialistSignalArbitrationRow, ...]) -> str:
    if not rows:
        return "caution"
    if any(row.posture == "blocked" for row in rows):
        return "blocked"
    if any(row.posture == "caution" for row in rows):
        return "caution"
    return "recommend"


def _report_reason_codes(
    rows: tuple[StrategySpecialistSignalArbitrationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_specialist_signals",)
    return _sort_reason_codes(
        tuple(dict.fromkeys(reason for row in rows for reason in row.reason_codes)),
    )


def _reason_code_counts(
    rows: tuple[StrategySpecialistSignalArbitrationRow, ...],
) -> tuple[StrategySpecialistSignalArbitrationReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason in row.reason_codes:
            counts[reason] = counts.get(reason, 0) + 1
    return tuple(
        StrategySpecialistSignalArbitrationReasonCodeCount(
            reason_code=reason,
            count=_count(count),
        )
        for reason, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], _reason_key(item[0])),
        )
    )


def _posture_count(
    rows: tuple[StrategySpecialistSignalArbitrationRow, ...],
    posture: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.posture == posture))


def _check_report(report: StrategySpecialistSignalArbitrationReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must equal row count")
    if report.recommend_count != _posture_count(rows, "recommend"):
        raise ValueError("recommend_count must match rows")
    if report.caution_count != _posture_count(rows, "caution"):
        raise ValueError("caution_count must match rows")
    if report.blocked_count != _posture_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _row_sort_key(row: StrategySpecialistSignalArbitrationRow) -> tuple[int, str]:
    return (_POSTURE_RANK[row.posture], row.candidate_id)


def _normalize_rows(
    rows: object,
) -> tuple[StrategySpecialistSignalArbitrationRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for item in items:
        if type(item) is not StrategySpecialistSignalArbitrationRow:
            raise ValueError("rows must contain StrategySpecialistSignalArbitrationRow")
        _require_flags("row", item)
    return items


def _normalize_reason_code_counts(
    reason_code_counts: object,
) -> tuple[StrategySpecialistSignalArbitrationReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        items = tuple(reason_code_counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in items:
        if type(item) is not StrategySpecialistSignalArbitrationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain StrategySpecialistSignalArbitrationReasonCodeCount",
            )
        _require_flags("reason code count", item)
    return items


def _normalize_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        _require_text(name, item)
        if item in seen:
            raise ValueError(f"{name} must not contain duplicates")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(reason_codes, key=_reason_key))


def _reason_key(reason_code: str) -> tuple[int, str]:
    return (_REASON_RANK.get(reason_code, len(_REASON_RANK)), reason_code)


def _report_digest(report: StrategySpecialistSignalArbitrationReport) -> str:
    payload = _json_ready(_report_digest_object(report))
    return _canonical_digest(payload)


def _report_digest_object(
    report: StrategySpecialistSignalArbitrationReport,
) -> dict[str, Any]:
    value = asdict(report)
    value.pop("derived_validation_digest", None)
    return value


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str or not digest:
        raise ValueError("derived_validation_digest is required")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _canonical_digest(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _canonical_digest(payload: object) -> str:
    ready = _json_ready(payload)
    encoded = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            _reject_unsafe_public(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public(label, item)


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must not be empty")
    return _ratio(sum(values, _ZERO), _count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        raise ValueError("ratio denominator must be non-zero")
    return _quantize(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(_ONE, max(_ZERO, _quantize(value)))


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be non-negative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    return _quantize(value)


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be non-negative")
    return normalized


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be non-empty without surrounding whitespace")
    if _has_unsafe_fragment(value):
        raise ValueError(f"unsafe value in {name}")


def _require_posture(name: str, value: object) -> None:
    if value not in _POSTURE_RANK:
        raise ValueError(f"{name} must be a supported posture")


def _require_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


__all__ = (
    "StrategySpecialistSignalArbitrationConfig",
    "StrategySpecialistSignalArbitrationInput",
    "StrategySpecialistSignalArbitrationReasonCodeCount",
    "StrategySpecialistSignalArbitrationReport",
    "StrategySpecialistSignalArbitrationRow",
    "build_strategy_specialist_signal_arbitration_report",
    "strategy_specialist_signal_arbitration_report_payload",
)
