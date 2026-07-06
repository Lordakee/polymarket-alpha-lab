"""Readonly Decimal gate for probability event research readiness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_PROBABILITY_EVENT_RESEARCH_READINESS_GATE_V2_CONFIG_VERSION = (
    "strategy-probability-event-research-readiness-gate-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SEVEN = Decimal("7")

READINESS_STATUSES = ("pass", "watch", "blocked")
ROW_STATUS_RANK = {
    "blocked": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}
SCORE_FIELD_NAMES = (
    "official_source_anchor_score",
    "information_quality_score",
    "source_crosscheck_score",
    "rule_clarity_score",
    "probability_movement_context_score",
    "source_freshness_exception_score",
    "specialist_confidence_score",
)
ROW_REASON_CODES = (
    "research_readiness_pass",
    "research_readiness_watch",
    "research_readiness_blocked",
    "official_source_anchor_strong",
    "official_source_anchor_watch",
    "official_source_anchor_weak",
    "information_quality_strong",
    "information_quality_watch",
    "information_quality_weak",
    "source_crosscheck_strong",
    "source_crosscheck_watch",
    "source_crosscheck_weak",
    "rule_clarity_strong",
    "rule_clarity_watch",
    "rule_clarity_weak",
    "probability_movement_context_strong",
    "probability_movement_context_watch",
    "probability_movement_context_weak",
    "source_freshness_exception_strong",
    "source_freshness_exception_watch",
    "source_freshness_exception_weak",
    "specialist_confidence_strong",
    "specialist_confidence_watch",
    "specialist_confidence_weak",
)
REPORT_REASON_CODES = (
    "research_readiness_gate_passed",
    "research_readiness_gate_watch_rows",
    "research_readiness_gate_blocked_rows",
    "research_readiness_gate_empty",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = tuple(
    "".join(parts)
    for parts in (
        ("li", "ve"),
        ("au", "th"),
        ("wal", "let"),
        ("or", "der"),
        ("net", "work"),
        ("data", "base"),
        ("per", "sist"),
        ("sig", "ning"),
        ("muta", "tion"),
        ("b", "uy"),
        ("se", "ll"),
        ("tra", "de"),
    )
)

__all__ = (
    "DEFAULT_STRATEGY_PROBABILITY_EVENT_RESEARCH_READINESS_GATE_V2_CONFIG_VERSION",
    "StrategyProbabilityEventResearchReadinessGateV2Config",
    "StrategyProbabilityEventResearchReadinessEvidenceV2",
    "StrategyProbabilityEventResearchReadinessGateV2Row",
    "StrategyProbabilityEventResearchReadinessGateV2Report",
    "build_strategy_probability_event_research_readiness_gate_v2",
)


@dataclass(frozen=True)
class StrategyProbabilityEventResearchReadinessGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_PROBABILITY_EVENT_RESEARCH_READINESS_GATE_V2_CONFIG_VERSION
    )
    pass_score_floor: Decimal = Decimal("0.850000")
    watch_score_floor: Decimal = Decimal("0.700000")
    critical_dimension_floor: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "pass_score_floor",
            "watch_score_floor",
            "critical_dimension_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags(
            "StrategyProbabilityEventResearchReadinessGateV2Config",
            self,
        )
        _reject_unsafe_public_payload(
            "StrategyProbabilityEventResearchReadinessGateV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyProbabilityEventResearchReadinessEvidenceV2:
    candidate_id: str
    event_id: str
    official_source_anchor_score: Decimal
    information_quality_score: Decimal
    source_crosscheck_score: Decimal
    rule_clarity_score: Decimal
    probability_movement_context_score: Decimal
    source_freshness_exception_score: Decimal
    specialist_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "candidate_id",
            _require_non_empty_string("candidate_id", self.candidate_id),
        )
        object.__setattr__(
            self,
            "event_id",
            _require_non_empty_string("event_id", self.event_id),
        )
        for field_name in SCORE_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(
            "StrategyProbabilityEventResearchReadinessEvidenceV2",
            self,
        )
        _reject_unsafe_public_payload(
            "StrategyProbabilityEventResearchReadinessEvidenceV2",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyProbabilityEventResearchReadinessGateV2Row:
    candidate_id: str
    event_id: str
    official_source_anchor_score: Decimal
    information_quality_score: Decimal
    source_crosscheck_score: Decimal
    rule_clarity_score: Decimal
    probability_movement_context_score: Decimal
    source_freshness_exception_score: Decimal
    specialist_confidence_score: Decimal
    research_readiness_score: Decimal
    readiness_status: str
    strategy_promotion_blocked: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _reject_unsafe_public_payload(
            "StrategyProbabilityEventResearchReadinessGateV2Row.raw",
            {"reason_codes": self.reason_codes},
        )
        object.__setattr__(
            self,
            "candidate_id",
            _require_non_empty_string("candidate_id", self.candidate_id),
        )
        object.__setattr__(
            self,
            "event_id",
            _require_non_empty_string("event_id", self.event_id),
        )
        for field_name in (*SCORE_FIELD_NAMES, "research_readiness_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("readiness_status", self.readiness_status)
        _require_bool("strategy_promotion_blocked", self.strategy_promotion_blocked)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags(
            "StrategyProbabilityEventResearchReadinessGateV2Row",
            self,
        )
        _reject_unsafe_public_payload(
            "StrategyProbabilityEventResearchReadinessGateV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class StrategyProbabilityEventResearchReadinessGateV2Report:
    generated_at: datetime
    config_version: str
    gate_status: str
    strategy_promotion_blocked: bool
    candidate_count: Decimal
    pass_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    average_research_readiness_score: Decimal
    top_research_readiness_score: Decimal
    bottom_research_readiness_score: Decimal
    rows: tuple[StrategyProbabilityEventResearchReadinessGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_status("gate_status", self.gate_status)
        _require_bool("strategy_promotion_blocked", self.strategy_promotion_blocked)
        for field_name in (
            "candidate_count",
            "pass_candidate_count",
            "watch_candidate_count",
            "blocked_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_research_readiness_score",
            "top_research_readiness_score",
            "bottom_research_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags(
            "StrategyProbabilityEventResearchReadinessGateV2Report",
            self,
        )
        _reject_unsafe_public_payload(
            "StrategyProbabilityEventResearchReadinessGateV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_shape(self)
        _validate_report_digest(self)
        _validate_report_summary(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "StrategyProbabilityEventResearchReadinessGateV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_strategy_probability_event_research_readiness_gate_v2(
    readiness_evidence: object,
    *,
    config: StrategyProbabilityEventResearchReadinessGateV2Config | None = None,
    generated_at: datetime,
) -> StrategyProbabilityEventResearchReadinessGateV2Report:
    if config is None:
        config = StrategyProbabilityEventResearchReadinessGateV2Config()
    if type(config) is not StrategyProbabilityEventResearchReadinessGateV2Config:
        raise ValueError(
            "config must be a StrategyProbabilityEventResearchReadinessGateV2Config",
        )
    _require_hard_flags(
        "StrategyProbabilityEventResearchReadinessGateV2Config",
        config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_evidence_items(readiness_evidence)
    rows = tuple(
        sorted(
            (_row_for_evidence(item, config) for item in evidence_items),
            key=_row_sort_key,
        ),
    )
    status = _gate_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "gate_status": status,
        "strategy_promotion_blocked": status != "pass",
        "candidate_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "pass_candidate_count": _status_count(rows, "pass"),
        "watch_candidate_count": _status_count(rows, "watch"),
        "blocked_candidate_count": _status_count(rows, "blocked"),
        "average_research_readiness_score": _average_score(rows),
        "top_research_readiness_score": _top_score(rows),
        "bottom_research_readiness_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return StrategyProbabilityEventResearchReadinessGateV2Report(**values)


def _row_for_evidence(
    item: StrategyProbabilityEventResearchReadinessEvidenceV2,
    config: StrategyProbabilityEventResearchReadinessGateV2Config,
) -> StrategyProbabilityEventResearchReadinessGateV2Row:
    score = _readiness_score(item)
    status = _readiness_status(item, score, config)
    return StrategyProbabilityEventResearchReadinessGateV2Row(
        candidate_id=item.candidate_id,
        event_id=item.event_id,
        official_source_anchor_score=item.official_source_anchor_score,
        information_quality_score=item.information_quality_score,
        source_crosscheck_score=item.source_crosscheck_score,
        rule_clarity_score=item.rule_clarity_score,
        probability_movement_context_score=item.probability_movement_context_score,
        source_freshness_exception_score=item.source_freshness_exception_score,
        specialist_confidence_score=item.specialist_confidence_score,
        research_readiness_score=score,
        readiness_status=status,
        strategy_promotion_blocked=status != "pass",
        reason_codes=_row_reason_codes(item, status, config),
    )


def _readiness_score(item: StrategyProbabilityEventResearchReadinessEvidenceV2) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = sum((getattr(item, field_name) for field_name in SCORE_FIELD_NAMES), ZERO)
        return _clamp_ratio(score / SEVEN)


def _readiness_status(
    item: StrategyProbabilityEventResearchReadinessEvidenceV2,
    score: Decimal,
    config: StrategyProbabilityEventResearchReadinessGateV2Config,
) -> str:
    values = tuple(getattr(item, field_name) for field_name in SCORE_FIELD_NAMES)
    if min(values) < config.critical_dimension_floor:
        return "blocked"
    if score >= config.pass_score_floor and min(values) >= config.pass_score_floor:
        return "pass"
    if score >= config.watch_score_floor:
        return "watch"
    return "blocked"


def _row_reason_codes(
    item: StrategyProbabilityEventResearchReadinessEvidenceV2,
    status: str,
    config: StrategyProbabilityEventResearchReadinessGateV2Config,
) -> tuple[str, ...]:
    return (
        f"research_readiness_{status}",
        _tier_reason(
            item.official_source_anchor_score,
            "official_source_anchor",
            config,
        ),
        _tier_reason(item.information_quality_score, "information_quality", config),
        _tier_reason(item.source_crosscheck_score, "source_crosscheck", config),
        _tier_reason(item.rule_clarity_score, "rule_clarity", config),
        _tier_reason(
            item.probability_movement_context_score,
            "probability_movement_context",
            config,
        ),
        _tier_reason(
            item.source_freshness_exception_score,
            "source_freshness_exception",
            config,
        ),
        _tier_reason(item.specialist_confidence_score, "specialist_confidence", config),
    )


def _tier_reason(
    value: Decimal,
    prefix: str,
    config: StrategyProbabilityEventResearchReadinessGateV2Config,
) -> str:
    if value >= config.pass_score_floor:
        return f"{prefix}_strong"
    if value >= config.critical_dimension_floor:
        return f"{prefix}_watch"
    return f"{prefix}_weak"


def _gate_status(
    rows: tuple[StrategyProbabilityEventResearchReadinessGateV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.readiness_status == "blocked" for row in rows):
        return "blocked"
    if any(row.readiness_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyProbabilityEventResearchReadinessGateV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("research_readiness_gate_empty",)
    if status == "pass":
        return ("research_readiness_gate_passed",)
    reasons: list[str] = []
    if any(row.readiness_status == "watch" for row in rows):
        reasons.append("research_readiness_gate_watch_rows")
    if any(row.readiness_status == "blocked" for row in rows):
        reasons.append("research_readiness_gate_blocked_rows")
    return tuple(reasons)


def _status_count(
    rows: tuple[StrategyProbabilityEventResearchReadinessGateV2Row, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.readiness_status == status)).quantize(
        COUNT_QUANT,
    )


def _average_score(
    rows: tuple[StrategyProbabilityEventResearchReadinessGateV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.research_readiness_score for row in rows), ZERO)
            / Decimal(len(rows)),
        )


def _top_score(
    rows: tuple[StrategyProbabilityEventResearchReadinessGateV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.research_readiness_score for row in rows)


def _bottom_score(
    rows: tuple[StrategyProbabilityEventResearchReadinessGateV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.research_readiness_score for row in rows)


def _row_sort_key(row: StrategyProbabilityEventResearchReadinessGateV2Row) -> tuple[Decimal, str, str]:
    return (ROW_STATUS_RANK[row.readiness_status], row.candidate_id, row.event_id)


def _normalize_evidence_items(
    readiness_evidence: object,
) -> tuple[StrategyProbabilityEventResearchReadinessEvidenceV2, ...]:
    if isinstance(readiness_evidence, (str, bytes)):
        raise ValueError("readiness evidence must be an iterable")
    try:
        items = tuple(readiness_evidence)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("readiness evidence must be an iterable") from exc
    for item in items:
        if type(item) is not StrategyProbabilityEventResearchReadinessEvidenceV2:
            raise ValueError(
                "readiness evidence items must be "
                "StrategyProbabilityEventResearchReadinessEvidenceV2",
            )
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item.candidate_id, item.event_id)
        if key in seen:
            raise ValueError("duplicate candidate_id and event_id")
        seen.add(key)
    return items


def _normalize_rows(rows: object) -> tuple[StrategyProbabilityEventResearchReadinessGateV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyProbabilityEventResearchReadinessGateV2Row:
            raise ValueError(
                "rows must contain StrategyProbabilityEventResearchReadinessGateV2Row",
            )
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and candidate_id")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for value in normalized:
        _require_non_empty_string(field_name, value)
    _reject_unsafe_public_payload(field_name, normalized)
    for value in normalized:
        if value not in allowed:
            raise ValueError(f"{field_name} contains an unsupported reason code")
    return normalized


def _validate_config(
    config: StrategyProbabilityEventResearchReadinessGateV2Config,
) -> None:
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must not exceed pass_score_floor")
    if config.critical_dimension_floor > config.watch_score_floor:
        raise ValueError("critical_dimension_floor must not exceed watch_score_floor")


def _validate_row_consistency(
    row: StrategyProbabilityEventResearchReadinessGateV2Row,
) -> None:
    expected_score = _clamp_ratio(
        sum((getattr(row, field_name) for field_name in SCORE_FIELD_NAMES), ZERO)
        / SEVEN,
    )
    if row.research_readiness_score != expected_score:
        raise ValueError("research_readiness_score must match component scores")
    if row.strategy_promotion_blocked is not (row.readiness_status != "pass"):
        raise ValueError("strategy_promotion_blocked must match readiness_status")
    if not row.reason_codes or row.reason_codes[0] != f"research_readiness_{row.readiness_status}":
        raise ValueError("reason_codes must match readiness_status")


def _validate_report_shape(
    report: StrategyProbabilityEventResearchReadinessGateV2Report,
) -> None:
    if report.candidate_count != Decimal(len(report.rows)).quantize(COUNT_QUANT):
        raise ValueError("candidate_count must match rows")
    if (
        report.pass_candidate_count != _status_count(report.rows, "pass")
        or report.watch_candidate_count != _status_count(report.rows, "watch")
        or report.blocked_candidate_count != _status_count(report.rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    expected_status = _gate_status(report.rows)
    if report.gate_status != expected_status:
        raise ValueError("gate_status must match rows")
    if report.strategy_promotion_blocked is not (report.gate_status != "pass"):
        raise ValueError("strategy_promotion_blocked must match gate_status")
    if report.reason_codes != _report_reason_codes(report.rows, report.gate_status):
        raise ValueError("reason_codes must match gate_status")


def _validate_report_summary(
    report: StrategyProbabilityEventResearchReadinessGateV2Report,
) -> None:
    if report.average_research_readiness_score != _average_score(report.rows):
        raise ValueError("average_research_readiness_score must match rows")
    if report.top_research_readiness_score != _top_score(report.rows):
        raise ValueError("top_research_readiness_score must match rows")
    if report.bottom_research_readiness_score != _bottom_score(report.rows):
        raise ValueError("bottom_research_readiness_score must match rows")


def _validate_report_digest(
    report: StrategyProbabilityEventResearchReadinessGateV2Report,
) -> None:
    if report.derived_validation_digest != _derived_validation_digest(_report_digest_fields(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _report_digest_fields(
    report: StrategyProbabilityEventResearchReadinessGateV2Report,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "gate_status": report.gate_status,
        "strategy_promotion_blocked": report.strategy_promotion_blocked,
        "candidate_count": report.candidate_count,
        "pass_candidate_count": report.pass_candidate_count,
        "watch_candidate_count": report.watch_candidate_count,
        "blocked_candidate_count": report.blocked_candidate_count,
        "average_research_readiness_score": report.average_research_readiness_score,
        "top_research_readiness_score": report.top_research_readiness_score,
        "bottom_research_readiness_score": report.bottom_research_readiness_score,
        "rows": report.rows,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_values = dict(values)
    digest_values.pop("derived_validation_digest", None)
    ready = _payload_value(digest_values)
    _reject_unsafe_public_payload("derived validation digest fields", ready)
    encoded = json.dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is float:
        raise ValueError("payload values must not be floats")
    if type(value) in (str, int, bool):
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for text in _iter_public_text(payload):
        lowered = text.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"unsafe public payload in {label}: {text}")


def _iter_public_text(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_text(asdict(value))
    if type(value) is dict:
        text_values: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            text_values.append(key)
            text_values.extend(_iter_public_text(item))
        return tuple(text_values)
    if type(value) in (list, tuple):
        text_values = []
        for item in value:
            text_values.extend(_iter_public_text(item))
        return tuple(text_values)
    if type(value) is str:
        return (value,)
    return ()


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if value != quantized:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_integral_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(COUNT_QUANT)
    if value != quantized:
        raise ValueError(f"{field_name} must be an integral Decimal")
    return quantized


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value < ZERO:
            value = ZERO
        if value > ONE:
            value = ONE
        return value.quantize(SCORE_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in READINESS_STATUSES:
        raise ValueError(f"{field_name} must be one of {READINESS_STATUSES!r}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
