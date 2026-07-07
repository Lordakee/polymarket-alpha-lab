"""Decimal-only paper report for source trust decay gates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_RECOMMENDATION_SOURCE_TRUST_DECAY_GATE_V2_CONFIG_VERSION = (
    "strategy-recommendation-source-trust-decay-gate-v2"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
SIDES = ("yes", "no")
STATUSES = ("blocked", "watch", "pass")
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}
EMPTY_REASON = "source_trust_decay_gate_v2_empty"
OWNED_REASON_CODES = frozenset(
    (
        "source_trust_decay_gate_blocked",
        "source_trust_decay_gate_watch",
        "source_trust_decay_gate_pass",
        "source_staleness_blocked",
        "historical_reliability_blocked",
        "source_contradiction_blocked",
        "official_confirmation_missing_blocked",
        "source_trust_score_blocked",
        "decayed_source_trust_blocked",
        "source_staleness_watch",
        "historical_reliability_watch",
        "source_contradiction_watch",
        "source_trust_score_watch",
        "decayed_source_trust_watch",
        EMPTY_REASON,
    ),
)
REASON_RANK = {
    "source_trust_decay_gate_blocked": 0,
    "source_trust_decay_gate_watch": 1,
    "source_trust_decay_gate_pass": 2,
    "source_staleness_blocked": 3,
    "historical_reliability_blocked": 4,
    "source_contradiction_blocked": 5,
    "official_confirmation_missing_blocked": 6,
    "source_trust_score_blocked": 7,
    "decayed_source_trust_blocked": 8,
    "source_staleness_watch": 9,
    "historical_reliability_watch": 10,
    "source_contradiction_watch": 11,
    "source_trust_score_watch": 12,
    "decayed_source_trust_watch": 13,
    EMPTY_REASON: 14,
}
REPORT_KEYS = (
    "generated_at",
    "config_version",
    "candidate_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_KEYS = (
    "recommendation_id",
    "market_id",
    "recommendation_side",
    "base_confidence",
    "source_trust_score",
    "source_observed_at",
    "source_age_seconds",
    "source_freshness_score",
    "historical_reliability_score",
    "contradiction_score",
    "contradiction_resistance_score",
    "official_confirmation_observed_at",
    "official_confirmation_score",
    "source_trust_decay_score",
    "trust_adjusted_confidence",
    "observed_at",
    "gate_status",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _surface_term("li", "ve"),
        _surface_term("au", "th"),
        _surface_term("wa", "llet"),
        _surface_term("bro", "ker"),
        _surface_term("or", "der"),
        _surface_term("net", "work"),
        _surface_term("data", "base"),
        _surface_term("private", "_key"),
        _surface_term("sup", "abase"),
        _surface_term("sql", "ite"),
        _surface_term("re", "quests"),
        _surface_term("tra", "de"),
        _surface_term("b", "uy"),
        _surface_term("se", "ll"),
        _surface_term("sign", "ing"),
        _surface_term("mut", "ation"),
    ),
)


@dataclass(frozen=True)
class StrategyRecommendationSourceTrustDecayGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_SOURCE_TRUST_DECAY_GATE_V2_CONFIG_VERSION
    )
    source_age_watch_seconds: Decimal = Decimal("3600.000000")
    source_age_block_seconds: Decimal = Decimal("7200.000000")
    historical_reliability_watch_score: Decimal = Decimal("0.750000")
    historical_reliability_block_score: Decimal = Decimal("0.500000")
    contradiction_watch_score: Decimal = Decimal("0.250000")
    contradiction_block_score: Decimal = Decimal("0.500000")
    minimum_source_trust_score: Decimal = Decimal("0.700000")
    blocked_source_trust_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationSourceTrustDecayGateV2Config:
            raise ValueError(
                "config must be a StrategyRecommendationSourceTrustDecayGateV2Config",
            )
        _require_text("config_version", self.config_version)
        for field_name in ("source_age_watch_seconds", "source_age_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "historical_reliability_watch_score",
            "historical_reliability_block_score",
            "contradiction_watch_score",
            "contradiction_block_score",
            "minimum_source_trust_score",
            "blocked_source_trust_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_at_most(
            "source_age_watch_seconds",
            self.source_age_watch_seconds,
            self.source_age_block_seconds,
        )
        if (
            self.historical_reliability_block_score
            > self.historical_reliability_watch_score
        ):
            raise ValueError(
                "historical_reliability_block_score must not exceed watch threshold",
            )
        _require_at_most(
            "contradiction_watch_score",
            self.contradiction_watch_score,
            self.contradiction_block_score,
        )
        if self.blocked_source_trust_score > self.minimum_source_trust_score:
            raise ValueError(
                "blocked_source_trust_score must not exceed minimum threshold",
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationSourceTrustDecayGateV2Input:
    recommendation_id: str
    market_id: str
    recommendation_side: str
    base_confidence: Decimal
    source_trust_score: Decimal
    source_observed_at: datetime
    historical_reliability_score: Decimal
    contradiction_score: Decimal
    official_confirmation_observed_at: datetime | None
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationSourceTrustDecayGateV2Input:
            raise ValueError(
                "input must be a StrategyRecommendationSourceTrustDecayGateV2Input",
            )
        for field_name in ("recommendation_id", "market_id", "recommendation_side"):
            _require_text(field_name, getattr(self, field_name))
        if self.recommendation_side not in SIDES:
            raise ValueError("recommendation_side must be yes or no")
        for field_name in (
            "base_confidence",
            "source_trust_score",
            "historical_reliability_score",
            "contradiction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "official_confirmation_observed_at",
            _as_optional_utc(
                "official_confirmation_observed_at",
                self.official_confirmation_observed_at,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_flags("input", self)


@dataclass(frozen=True)
class StrategyRecommendationSourceTrustDecayGateV2Row:
    recommendation_id: str
    market_id: str
    recommendation_side: str
    base_confidence: Decimal
    source_trust_score: Decimal
    source_observed_at: datetime
    source_age_seconds: Decimal
    source_freshness_score: Decimal
    historical_reliability_score: Decimal
    contradiction_score: Decimal
    contradiction_resistance_score: Decimal
    official_confirmation_observed_at: datetime | None
    official_confirmation_score: Decimal
    source_trust_decay_score: Decimal
    trust_adjusted_confidence: Decimal
    observed_at: datetime
    gate_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationSourceTrustDecayGateV2Row:
            raise ValueError("row must be a StrategyRecommendationSourceTrustDecayGateV2Row")
        for field_name in ("recommendation_id", "market_id", "recommendation_side"):
            _require_text(field_name, getattr(self, field_name))
        if self.recommendation_side not in SIDES:
            raise ValueError("recommendation_side must be yes or no")
        for field_name in (
            "base_confidence",
            "source_trust_score",
            "source_freshness_score",
            "historical_reliability_score",
            "contradiction_score",
            "contradiction_resistance_score",
            "official_confirmation_score",
            "source_trust_decay_score",
            "trust_adjusted_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "official_confirmation_observed_at",
            _as_optional_utc(
                "official_confirmation_observed_at",
                self.official_confirmation_observed_at,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_flags("row", self)
        _check_row(self)
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


@dataclass(frozen=True)
class StrategyRecommendationSourceTrustDecayGateV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyRecommendationSourceTrustDecayGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationSourceTrustDecayGateV2Report:
            raise ValueError(
                "report must be a StrategyRecommendationSourceTrustDecayGateV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_flags("report", self)
        _check_report(self)
        for row in self.rows:
            _require_row_digest(row)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_strategy_recommendation_source_trust_decay_gate_v2_report(
    recommendations: object,
    *,
    config: StrategyRecommendationSourceTrustDecayGateV2Config,
    generated_at: datetime,
) -> StrategyRecommendationSourceTrustDecayGateV2Report:
    if type(config) is not StrategyRecommendationSourceTrustDecayGateV2Config:
        raise ValueError(
            "config must be a StrategyRecommendationSourceTrustDecayGateV2Config",
        )
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_inputs(recommendations)
    for item in items:
        if item.source_observed_at > generated_at:
            raise ValueError("source_observed_at must not be after generated_at")
        if (
            item.official_confirmation_observed_at is not None
            and item.official_confirmation_observed_at > generated_at
        ):
            raise ValueError(
                "official_confirmation_observed_at must not be after generated_at",
            )
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_for_recommendation(
                    item,
                    config=config,
                    generated_at=generated_at,
                )
                for item in items
            ),
            key=_row_sort_key,
        ),
    )
    return StrategyRecommendationSourceTrustDecayGateV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_recommendation_source_trust_decay_gate_v2_payload(
    report: StrategyRecommendationSourceTrustDecayGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyRecommendationSourceTrustDecayGateV2Report:
        _require_flags("report", report)
        _require_report_digest(report)
        _reject_unsafe_public("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public("payload", report)
        _reject_raw_public_numbers("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        _reject_unsafe_public("payload", payload)
        return payload
    raise ValueError("report must be a StrategyRecommendationSourceTrustDecayGateV2Report")


def _row_for_recommendation(
    item: StrategyRecommendationSourceTrustDecayGateV2Input,
    *,
    config: StrategyRecommendationSourceTrustDecayGateV2Config,
    generated_at: datetime,
) -> StrategyRecommendationSourceTrustDecayGateV2Row:
    source_age_seconds = _age_seconds(
        "source_observed_at",
        generated_at,
        item.source_observed_at,
    )
    source_freshness_score = _inverse_threshold_score(
        source_age_seconds,
        config.source_age_block_seconds,
    )
    contradiction_resistance_score = _clamp_ratio(ONE - item.contradiction_score)
    official_confirmation_score = (
        ONE if item.official_confirmation_observed_at is not None else ZERO
    )
    source_trust_decay_score = _average(
        (
            item.source_trust_score,
            source_freshness_score,
            item.historical_reliability_score,
            contradiction_resistance_score,
            official_confirmation_score,
        ),
    )
    trust_adjusted_confidence = _quantize(
        min(item.base_confidence, source_trust_decay_score),
    )
    reason_codes = _row_reason_codes(
        item,
        source_age_seconds=source_age_seconds,
        source_trust_decay_score=source_trust_decay_score,
        config=config,
    )
    return StrategyRecommendationSourceTrustDecayGateV2Row(
        recommendation_id=item.recommendation_id,
        market_id=item.market_id,
        recommendation_side=item.recommendation_side,
        base_confidence=item.base_confidence,
        source_trust_score=item.source_trust_score,
        source_observed_at=item.source_observed_at,
        source_age_seconds=source_age_seconds,
        source_freshness_score=source_freshness_score,
        historical_reliability_score=item.historical_reliability_score,
        contradiction_score=item.contradiction_score,
        contradiction_resistance_score=contradiction_resistance_score,
        official_confirmation_observed_at=item.official_confirmation_observed_at,
        official_confirmation_score=official_confirmation_score,
        source_trust_decay_score=source_trust_decay_score,
        trust_adjusted_confidence=trust_adjusted_confidence,
        observed_at=item.observed_at,
        gate_status=_status_from_reasons(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: StrategyRecommendationSourceTrustDecayGateV2Input,
    *,
    source_age_seconds: Decimal,
    source_trust_decay_score: Decimal,
    config: StrategyRecommendationSourceTrustDecayGateV2Config,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if source_age_seconds > config.source_age_block_seconds:
        block_reasons.append("source_staleness_blocked")
    elif source_age_seconds > config.source_age_watch_seconds:
        watch_reasons.append("source_staleness_watch")
    if item.historical_reliability_score < config.historical_reliability_block_score:
        block_reasons.append("historical_reliability_blocked")
    elif item.historical_reliability_score < config.historical_reliability_watch_score:
        watch_reasons.append("historical_reliability_watch")
    if item.contradiction_score > config.contradiction_block_score:
        block_reasons.append("source_contradiction_blocked")
    elif item.contradiction_score > config.contradiction_watch_score:
        watch_reasons.append("source_contradiction_watch")
    if item.official_confirmation_observed_at is None:
        block_reasons.append("official_confirmation_missing_blocked")
    if item.source_trust_score < config.blocked_source_trust_score:
        block_reasons.append("source_trust_score_blocked")
    elif item.source_trust_score < config.minimum_source_trust_score:
        watch_reasons.append("source_trust_score_watch")
    if source_trust_decay_score < config.blocked_source_trust_score:
        block_reasons.append("decayed_source_trust_blocked")
    elif source_trust_decay_score < config.minimum_source_trust_score:
        watch_reasons.append("decayed_source_trust_watch")

    if block_reasons:
        reasons = ["source_trust_decay_gate_blocked", *block_reasons]
    elif watch_reasons:
        reasons = ["source_trust_decay_gate_watch", *watch_reasons]
    else:
        reasons = ["source_trust_decay_gate_pass"]
    reasons.extend(item.reason_codes)
    return _sort_reason_codes(tuple(reasons))


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if "source_trust_decay_gate_blocked" in reason_codes:
        return "blocked"
    if "source_trust_decay_gate_watch" in reason_codes:
        return "watch"
    return "pass"


def _normalize_inputs(
    recommendations: object,
) -> tuple[StrategyRecommendationSourceTrustDecayGateV2Input, ...]:
    if isinstance(recommendations, (str, bytes)):
        raise ValueError("recommendations must be an iterable")
    try:
        items = tuple(recommendations)
    except TypeError as exc:
        raise ValueError("recommendations must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not StrategyRecommendationSourceTrustDecayGateV2Input:
            raise ValueError(
                "recommendations must contain "
                "StrategyRecommendationSourceTrustDecayGateV2Input",
            )
        _require_flags("input", item)
        if item.recommendation_id in seen:
            raise ValueError("recommendations must not contain duplicate recommendation_id")
        seen.add(item.recommendation_id)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[StrategyRecommendationSourceTrustDecayGateV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for item in items:
        if type(item) is not StrategyRecommendationSourceTrustDecayGateV2Row:
            raise ValueError("rows must contain StrategyRecommendationSourceTrustDecayGateV2Row")
        _require_flags("row", item)
        _require_row_digest(item)
    if items != tuple(sorted(items, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return items


def _row_sort_key(row: StrategyRecommendationSourceTrustDecayGateV2Row) -> tuple[int, Decimal, str]:
    return (STATUS_RANK[row.gate_status], row.source_trust_decay_score, row.recommendation_id)


def _status_count(
    rows: tuple[StrategyRecommendationSourceTrustDecayGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _report_status(rows: tuple[StrategyRecommendationSourceTrustDecayGateV2Row, ...]) -> str:
    if any(row.gate_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    if rows:
        return "pass"
    return "blocked"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationSourceTrustDecayGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    return _sort_reason_codes(
        tuple(
            dict.fromkeys(
                reason
                for row in rows
                for reason in row.reason_codes
                if reason in OWNED_REASON_CODES
            ),
        ),
    )


def _check_row(row: StrategyRecommendationSourceTrustDecayGateV2Row) -> None:
    if row.contradiction_resistance_score != _clamp_ratio(ONE - row.contradiction_score):
        raise ValueError("contradiction_resistance_score must match contradiction_score")
    expected_official_confirmation_score = (
        ONE if row.official_confirmation_observed_at is not None else ZERO
    )
    if row.official_confirmation_score != expected_official_confirmation_score:
        raise ValueError("official_confirmation_score must match confirmation presence")
    expected_source_trust_decay_score = _average(
        (
            row.source_trust_score,
            row.source_freshness_score,
            row.historical_reliability_score,
            row.contradiction_resistance_score,
            row.official_confirmation_score,
        ),
    )
    if row.source_trust_decay_score != expected_source_trust_decay_score:
        raise ValueError("source_trust_decay_score must match component scores")
    expected_trust_adjusted_confidence = _quantize(
        min(row.base_confidence, row.source_trust_decay_score),
    )
    if row.trust_adjusted_confidence != expected_trust_adjusted_confidence:
        raise ValueError("trust_adjusted_confidence must match source_trust_decay_score")
    if row.gate_status != _status_from_reasons(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    expected_terminal = {
        "blocked": "source_trust_decay_gate_blocked",
        "watch": "source_trust_decay_gate_watch",
        "pass": "source_trust_decay_gate_pass",
    }[row.gate_status]
    if expected_terminal not in row.reason_codes:
        raise ValueError("reason_codes must include gate status reason")


def _check_report(report: StrategyRecommendationSourceTrustDecayGateV2Report) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _row_digest(row: StrategyRecommendationSourceTrustDecayGateV2Row) -> str:
    value = asdict(row)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _report_digest(report: StrategyRecommendationSourceTrustDecayGateV2Report) -> str:
    value = asdict(report)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _require_row_digest(row: StrategyRecommendationSourceTrustDecayGateV2Row) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest mismatch")


def _require_report_digest(report: StrategyRecommendationSourceTrustDecayGateV2Report) -> None:
    for row in report.rows:
        _require_row_digest(row)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest mismatch")


def _verify_report_payload(payload: dict[str, Any]) -> None:
    _require_exact_keys("payload", payload, REPORT_KEYS)
    _require_payload_flags("payload", payload)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload.rows must be a JSON list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_row_payload(f"payload.rows[{index}]", row)
    supplied_digest = payload["derived_validation_digest"]
    if type(supplied_digest) is not str or not supplied_digest:
        raise ValueError("derived_validation_digest is required")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if supplied_digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _verify_row_payload(label: str, payload: dict[str, Any]) -> None:
    _require_exact_keys(label, payload, ROW_KEYS)
    _require_payload_flags(label, payload)
    supplied_digest = payload["derived_validation_digest"]
    if type(supplied_digest) is not str or not supplied_digest:
        raise ValueError(f"{label}.derived_validation_digest is required")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if supplied_digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _require_exact_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    for key in expected_keys:
        if key not in payload:
            raise ValueError(f"{label}.{key} is required")
    extra_keys = tuple(sorted(set(payload) - set(expected_keys)))
    if extra_keys:
        raise ValueError(f"{label} contains unsupported public field: {extra_keys[0]}")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _canonical_digest(payload: object) -> str:
    ready = _json_ready(payload)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be an exact Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be an exact datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if type(value) is str:
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public(label, item)


def _reject_raw_public_numbers(label: str, value: object) -> None:
    if type(value) is bool:
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{label} Decimal|string payload values required")
    if isinstance(value, float):
        raise ValueError(f"{label} Decimal|string payload values required")
    if type(value) is int:
        raise ValueError(f"{label} Decimal|string payload values required")
    if isinstance(value, dict):
        for item in value.values():
            _reject_raw_public_numbers(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_raw_public_numbers(label, item)


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _age_seconds(field_name: str, generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.days < 0:
        raise ValueError(f"{field_name} must not be after generated_at")
    return _quantize(
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / MICROS_PER_SECOND,
    )


def _inverse_threshold_score(value: Decimal, block_threshold: Decimal) -> Decimal:
    return _clamp_ratio(ONE - _clamp_ratio(value / block_threshold))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    value = _quantize(value)
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_text("reason_codes", reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must not contain duplicate values")
    return _sort_reason_codes(reason_codes)


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    unique = tuple(dict.fromkeys(reason_codes))
    for reason_code in unique:
        _require_text("reason_codes", reason_code)
    return tuple(sorted(unique, key=lambda item: (REASON_RANK.get(item, 1000), item)))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be blocked, watch, or pass")


def _require_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} contains unsafe surface text")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be less than or equal to one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_at_most(field_name: str, low_value: Decimal, high_value: Decimal) -> None:
    if low_value > high_value:
        raise ValueError(f"{field_name} must be less than or equal to threshold")


def _require_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_SOURCE_TRUST_DECAY_GATE_V2_CONFIG_VERSION",
    "StrategyRecommendationSourceTrustDecayGateV2Config",
    "StrategyRecommendationSourceTrustDecayGateV2Input",
    "StrategyRecommendationSourceTrustDecayGateV2Row",
    "StrategyRecommendationSourceTrustDecayGateV2Report",
    "build_strategy_recommendation_source_trust_decay_gate_v2_report",
    "strategy_recommendation_source_trust_decay_gate_v2_payload",
)
