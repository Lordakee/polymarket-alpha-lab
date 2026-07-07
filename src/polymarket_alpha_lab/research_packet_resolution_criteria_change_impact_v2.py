"""Pure paper report for resolution criteria change impact."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any


DECIMAL_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ZERO_COUNT = Decimal("0")
ONE = Decimal("1.000000")
LOW_SEVERITY_LIMIT = Decimal("0.250000")
HIGH_SEVERITY_LIMIT = Decimal("0.750000")
ELEVATED_EXPOSURE_LIMIT = Decimal("0.250000")
IMPACT_BANDS = ("low", "watch", "high")
REPORT_STATUSES = ("paper_clear", "paper_watch", "paper_blocked")
OFFICIAL_SOURCE_TIERS = ("official", "primary", "proxy", "unmapped")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "liv" + "e",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sig" + "ning",
    "muta" + "tion",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "b" + "uy",
    "se" + "ll",
    "tra" + "de",
)


@dataclass(frozen=True)
class ResearchPacketResolutionCriteriaChangeImpactV2Config:
    config_version: str
    max_fresh_criteria_age_seconds: Decimal
    near_settlement_seconds: Decimal
    watch_impact_bps: Decimal
    high_impact_bps: Decimal
    stale_criteria_penalty_bps: Decimal
    change_severity_weight_bps: Decimal
    primary_source_penalty_bps: Decimal
    proxy_source_penalty_bps: Decimal
    unmapped_source_penalty_bps: Decimal
    market_exposure_weight_bps: Decimal
    contradiction_penalty_bps: Decimal
    settlement_proximity_penalty_bps: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "max_fresh_criteria_age_seconds",
            "near_settlement_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_impact_bps",
            "high_impact_bps",
            "stale_criteria_penalty_bps",
            "change_severity_weight_bps",
            "primary_source_penalty_bps",
            "proxy_source_penalty_bps",
            "unmapped_source_penalty_bps",
            "market_exposure_weight_bps",
            "contradiction_penalty_bps",
            "settlement_proximity_penalty_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.high_impact_bps < self.watch_impact_bps:
            raise ValueError("high_impact_bps must be at least watch threshold")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketResolutionCriteriaChangeImpactV2Input:
    candidate_id: str
    market_slug: str
    criteria_id: str
    criteria_last_verified_at: datetime
    change_severity: Decimal
    official_source_tier: str
    market_exposure: Decimal
    contradiction_count: Decimal
    settlement_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "criteria_id"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "criteria_last_verified_at",
            _as_utc("criteria_last_verified_at", self.criteria_last_verified_at),
        )
        object.__setattr__(
            self,
            "change_severity",
            _normalize_ratio("change_severity", self.change_severity),
        )
        _require_choice(
            "official_source_tier",
            self.official_source_tier,
            OFFICIAL_SOURCE_TIERS,
        )
        object.__setattr__(
            self,
            "market_exposure",
            _normalize_ratio("market_exposure", self.market_exposure),
        )
        object.__setattr__(
            self,
            "contradiction_count",
            _normalize_nonnegative_count(
                "contradiction_count",
                self.contradiction_count,
            ),
        )
        object.__setattr__(
            self,
            "settlement_at",
            _as_utc("settlement_at", self.settlement_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketResolutionCriteriaChangeImpactV2Report:
    generated_at: datetime
    config_version: str
    candidate_id: str
    market_slug: str
    criteria_id: str
    criteria_last_verified_at: datetime
    settlement_at: datetime
    max_fresh_criteria_age_seconds: Decimal
    near_settlement_seconds: Decimal
    watch_impact_bps: Decimal
    high_impact_bps: Decimal
    criteria_age_seconds: Decimal
    change_severity: Decimal
    official_source_tier: str
    market_exposure: Decimal
    contradiction_count: Decimal
    settlement_proximity_seconds: Decimal
    stale_criteria_penalty_bps: Decimal
    change_severity_impact_bps: Decimal
    source_hierarchy_penalty_bps: Decimal
    market_exposure_impact_bps: Decimal
    contradiction_impact_bps: Decimal
    settlement_proximity_impact_bps: Decimal
    raw_impact_bps: Decimal
    impact_band: str
    report_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in ("config_version", "candidate_id", "market_slug", "criteria_id"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "criteria_last_verified_at",
            _as_utc("criteria_last_verified_at", self.criteria_last_verified_at),
        )
        object.__setattr__(
            self,
            "settlement_at",
            _as_utc("settlement_at", self.settlement_at),
        )
        for field_name in (
            "max_fresh_criteria_age_seconds",
            "near_settlement_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_impact_bps",
            "high_impact_bps",
            "criteria_age_seconds",
            "settlement_proximity_seconds",
            "stale_criteria_penalty_bps",
            "change_severity_impact_bps",
            "source_hierarchy_penalty_bps",
            "market_exposure_impact_bps",
            "contradiction_impact_bps",
            "settlement_proximity_impact_bps",
            "raw_impact_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "change_severity",
            _normalize_ratio("change_severity", self.change_severity),
        )
        _require_choice(
            "official_source_tier",
            self.official_source_tier,
            OFFICIAL_SOURCE_TIERS,
        )
        object.__setattr__(
            self,
            "market_exposure",
            _normalize_ratio("market_exposure", self.market_exposure),
        )
        object.__setattr__(
            self,
            "contradiction_count",
            _normalize_nonnegative_count(
                "contradiction_count",
                self.contradiction_count,
            ),
        )
        _require_choice("impact_band", self.impact_band, IMPACT_BANDS)
        _require_choice("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)
        _validate_report_consistency(self)
        expected_digest = _report_validation_digest(self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def estimate_research_packet_resolution_criteria_change_impact_v2(
    score_input: ResearchPacketResolutionCriteriaChangeImpactV2Input,
    *,
    config: ResearchPacketResolutionCriteriaChangeImpactV2Config,
    generated_at: datetime,
) -> ResearchPacketResolutionCriteriaChangeImpactV2Report:
    if type(score_input) is not ResearchPacketResolutionCriteriaChangeImpactV2Input:
        raise ValueError(
            "score_input must be a ResearchPacketResolutionCriteriaChangeImpactV2Input",
        )
    if type(config) is not ResearchPacketResolutionCriteriaChangeImpactV2Config:
        raise ValueError(
            "config must be a ResearchPacketResolutionCriteriaChangeImpactV2Config",
        )
    _require_hard_flags(score_input)
    _require_hard_flags(config)
    normalized_generated_at = _as_utc("generated_at", generated_at)
    if score_input.criteria_last_verified_at > normalized_generated_at:
        raise ValueError("criteria_last_verified_at must not be after generated_at")
    if score_input.settlement_at < normalized_generated_at:
        raise ValueError("settlement_at must not be before generated_at")

    criteria_age_seconds = _seconds_between(
        score_input.criteria_last_verified_at,
        normalized_generated_at,
    )
    settlement_proximity_seconds = _seconds_between(
        normalized_generated_at,
        score_input.settlement_at,
    )
    stale_criteria_penalty_bps = (
        config.stale_criteria_penalty_bps
        if criteria_age_seconds > config.max_fresh_criteria_age_seconds
        else ZERO
    )
    change_severity_impact_bps = _normalize_nonnegative_decimal(
        "change_severity_impact_bps",
        score_input.change_severity * config.change_severity_weight_bps,
    )
    source_hierarchy_penalty_bps = _source_hierarchy_penalty_bps(
        score_input.official_source_tier,
        config,
    )
    market_exposure_impact_bps = _normalize_nonnegative_decimal(
        "market_exposure_impact_bps",
        score_input.market_exposure * config.market_exposure_weight_bps,
    )
    contradiction_impact_bps = _normalize_nonnegative_decimal(
        "contradiction_impact_bps",
        score_input.contradiction_count * config.contradiction_penalty_bps,
    )
    settlement_proximity_impact_bps = (
        config.settlement_proximity_penalty_bps
        if settlement_proximity_seconds <= config.near_settlement_seconds
        else ZERO
    )
    raw_impact_bps = _normalize_nonnegative_decimal(
        "raw_impact_bps",
        stale_criteria_penalty_bps
        + change_severity_impact_bps
        + source_hierarchy_penalty_bps
        + market_exposure_impact_bps
        + contradiction_impact_bps
        + settlement_proximity_impact_bps,
    )
    impact_band = _impact_band(
        raw_impact_bps,
        watch_impact_bps=config.watch_impact_bps,
        high_impact_bps=config.high_impact_bps,
    )

    return ResearchPacketResolutionCriteriaChangeImpactV2Report(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        candidate_id=score_input.candidate_id,
        market_slug=score_input.market_slug,
        criteria_id=score_input.criteria_id,
        criteria_last_verified_at=score_input.criteria_last_verified_at,
        settlement_at=score_input.settlement_at,
        max_fresh_criteria_age_seconds=config.max_fresh_criteria_age_seconds,
        near_settlement_seconds=config.near_settlement_seconds,
        watch_impact_bps=config.watch_impact_bps,
        high_impact_bps=config.high_impact_bps,
        criteria_age_seconds=criteria_age_seconds,
        change_severity=score_input.change_severity,
        official_source_tier=score_input.official_source_tier,
        market_exposure=score_input.market_exposure,
        contradiction_count=score_input.contradiction_count,
        settlement_proximity_seconds=settlement_proximity_seconds,
        stale_criteria_penalty_bps=stale_criteria_penalty_bps,
        change_severity_impact_bps=change_severity_impact_bps,
        source_hierarchy_penalty_bps=source_hierarchy_penalty_bps,
        market_exposure_impact_bps=market_exposure_impact_bps,
        contradiction_impact_bps=contradiction_impact_bps,
        settlement_proximity_impact_bps=settlement_proximity_impact_bps,
        raw_impact_bps=raw_impact_bps,
        impact_band=impact_band,
        report_status=_report_status(impact_band),
        reason_codes=_reason_codes(
            score_input.reason_codes,
            impact_band=impact_band,
            criteria_age_seconds=criteria_age_seconds,
            max_fresh_criteria_age_seconds=config.max_fresh_criteria_age_seconds,
            change_severity=score_input.change_severity,
            official_source_tier=score_input.official_source_tier,
            market_exposure=score_input.market_exposure,
            contradiction_count=score_input.contradiction_count,
            settlement_proximity_seconds=settlement_proximity_seconds,
            near_settlement_seconds=config.near_settlement_seconds,
        ),
    )


def research_packet_resolution_criteria_change_impact_v2_payload(
    report: ResearchPacketResolutionCriteriaChangeImpactV2Report,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketResolutionCriteriaChangeImpactV2Report:
        raise ValueError(
            "report must be a ResearchPacketResolutionCriteriaChangeImpactV2Report",
        )
    _require_hard_flags(report)
    if report.derived_validation_digest != _report_validation_digest(report):
        raise ValueError("derived_validation_digest mismatch")
    payload = _report_payload_without_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    return validate_research_packet_resolution_criteria_change_impact_v2_public_payload(
        payload,
    )


def validate_research_packet_resolution_criteria_change_impact_v2_public_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or isinstance(payload, (str, bytes)):
        raise ValueError("public payload must be a mapping")
    ready = _validate_public_payload_value(payload)
    if not isinstance(ready, dict):
        raise ValueError("public payload must be a JSON object")
    digest = ready.get("derived_validation_digest")
    if digest is not None:
        if type(digest) is not str:
            raise ValueError("derived_validation_digest must be a string")
        _require_sha256("derived_validation_digest", digest)
        digest_source = dict(ready)
        digest_source.pop("derived_validation_digest")
        if digest != _public_payload_digest(digest_source):
            raise ValueError("derived_validation_digest mismatch")
    return ready


def _source_hierarchy_penalty_bps(
    official_source_tier: str,
    config: ResearchPacketResolutionCriteriaChangeImpactV2Config,
) -> Decimal:
    if official_source_tier == "official":
        return ZERO
    if official_source_tier == "primary":
        return config.primary_source_penalty_bps
    if official_source_tier == "proxy":
        return config.proxy_source_penalty_bps
    if official_source_tier == "unmapped":
        return config.unmapped_source_penalty_bps
    raise ValueError("official_source_tier must be one of supported values")


def _impact_band(
    raw_impact_bps: Decimal,
    *,
    watch_impact_bps: Decimal,
    high_impact_bps: Decimal,
) -> str:
    if raw_impact_bps >= high_impact_bps:
        return "high"
    if raw_impact_bps >= watch_impact_bps:
        return "watch"
    return "low"


def _report_status(impact_band: str) -> str:
    if impact_band == "low":
        return "paper_clear"
    if impact_band == "watch":
        return "paper_watch"
    if impact_band == "high":
        return "paper_blocked"
    raise ValueError("impact_band must be supported")


def _reason_codes(
    existing: tuple[str, ...],
    *,
    impact_band: str,
    criteria_age_seconds: Decimal,
    max_fresh_criteria_age_seconds: Decimal,
    change_severity: Decimal,
    official_source_tier: str,
    market_exposure: Decimal,
    contradiction_count: Decimal,
    settlement_proximity_seconds: Decimal,
    near_settlement_seconds: Decimal,
) -> tuple[str, ...]:
    additions = (
        "research_packet_resolution_criteria_change_impact_v2",
        f"impact_band_{impact_band}",
        (
            "criteria_age_stale"
            if criteria_age_seconds > max_fresh_criteria_age_seconds
            else "criteria_age_fresh"
        ),
        f"change_severity_{_severity_band(change_severity)}",
        f"source_hierarchy_{official_source_tier}",
        (
            "market_exposure_elevated"
            if market_exposure >= ELEVATED_EXPOSURE_LIMIT
            else "market_exposure_limited"
        ),
        "contradictions_present"
        if contradiction_count > ZERO_COUNT
        else "no_contradictions",
        (
            "settlement_proximity_near"
            if settlement_proximity_seconds <= near_settlement_seconds
            else "settlement_proximity_not_near"
        ),
        _impact_score_reason(impact_band),
    )
    return _append_reason_codes(existing, additions)


def _severity_band(change_severity: Decimal) -> str:
    if change_severity == ZERO:
        return "none"
    if change_severity < LOW_SEVERITY_LIMIT:
        return "low"
    if change_severity < HIGH_SEVERITY_LIMIT:
        return "medium"
    return "high"


def _impact_score_reason(impact_band: str) -> str:
    if impact_band == "low":
        return "impact_score_below_watch"
    if impact_band == "watch":
        return "impact_score_watch"
    if impact_band == "high":
        return "impact_score_high"
    raise ValueError("impact_band must be supported")


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_report_consistency(
    report: ResearchPacketResolutionCriteriaChangeImpactV2Report,
) -> None:
    if report.high_impact_bps < report.watch_impact_bps:
        raise ValueError("high_impact_bps must be at least watch threshold")
    if report.criteria_last_verified_at > report.generated_at:
        raise ValueError("criteria_last_verified_at must not be after generated_at")
    if report.settlement_at < report.generated_at:
        raise ValueError("settlement_at must not be before generated_at")
    if report.criteria_age_seconds != _seconds_between(
        report.criteria_last_verified_at,
        report.generated_at,
    ):
        raise ValueError("criteria_age_seconds must match timestamps")
    if report.settlement_proximity_seconds != _seconds_between(
        report.generated_at,
        report.settlement_at,
    ):
        raise ValueError("settlement_proximity_seconds must match timestamps")
    expected_raw_impact_bps = _normalize_nonnegative_decimal(
        "raw_impact_bps",
        report.stale_criteria_penalty_bps
        + report.change_severity_impact_bps
        + report.source_hierarchy_penalty_bps
        + report.market_exposure_impact_bps
        + report.contradiction_impact_bps
        + report.settlement_proximity_impact_bps,
    )
    if report.raw_impact_bps != expected_raw_impact_bps:
        raise ValueError("raw_impact_bps must match impact components")
    expected_impact_band = _impact_band(
        report.raw_impact_bps,
        watch_impact_bps=report.watch_impact_bps,
        high_impact_bps=report.high_impact_bps,
    )
    if report.impact_band != expected_impact_band:
        raise ValueError("impact_band must match raw_impact_bps")
    if report.report_status != _report_status(report.impact_band):
        raise ValueError("report_status must match impact_band")
    required_reasons = _reason_codes(
        (),
        impact_band=report.impact_band,
        criteria_age_seconds=report.criteria_age_seconds,
        max_fresh_criteria_age_seconds=report.max_fresh_criteria_age_seconds,
        change_severity=report.change_severity,
        official_source_tier=report.official_source_tier,
        market_exposure=report.market_exposure,
        contradiction_count=report.contradiction_count,
        settlement_proximity_seconds=report.settlement_proximity_seconds,
        near_settlement_seconds=report.near_settlement_seconds,
    )
    for reason_code in required_reasons:
        if reason_code not in report.reason_codes:
            raise ValueError("reason_codes must include deterministic impact reasons")


def _report_payload_without_digest(
    report: ResearchPacketResolutionCriteriaChangeImpactV2Report,
) -> dict[str, Any]:
    return {
        "generated_at": _payload_value(report.generated_at),
        "config_version": report.config_version,
        "candidate_id": report.candidate_id,
        "market_slug": report.market_slug,
        "criteria_id": report.criteria_id,
        "criteria_last_verified_at": _payload_value(report.criteria_last_verified_at),
        "settlement_at": _payload_value(report.settlement_at),
        "max_fresh_criteria_age_seconds": _payload_value(
            report.max_fresh_criteria_age_seconds,
        ),
        "near_settlement_seconds": _payload_value(report.near_settlement_seconds),
        "watch_impact_bps": _payload_value(report.watch_impact_bps),
        "high_impact_bps": _payload_value(report.high_impact_bps),
        "criteria_age_seconds": _payload_value(report.criteria_age_seconds),
        "change_severity": _payload_value(report.change_severity),
        "official_source_tier": report.official_source_tier,
        "market_exposure": _payload_value(report.market_exposure),
        "contradiction_count": _payload_value(report.contradiction_count),
        "settlement_proximity_seconds": _payload_value(
            report.settlement_proximity_seconds,
        ),
        "stale_criteria_penalty_bps": _payload_value(
            report.stale_criteria_penalty_bps,
        ),
        "change_severity_impact_bps": _payload_value(
            report.change_severity_impact_bps,
        ),
        "source_hierarchy_penalty_bps": _payload_value(
            report.source_hierarchy_penalty_bps,
        ),
        "market_exposure_impact_bps": _payload_value(
            report.market_exposure_impact_bps,
        ),
        "contradiction_impact_bps": _payload_value(report.contradiction_impact_bps),
        "settlement_proximity_impact_bps": _payload_value(
            report.settlement_proximity_impact_bps,
        ),
        "raw_impact_bps": _payload_value(report.raw_impact_bps),
        "impact_band": report.impact_band,
        "report_status": report.report_status,
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_validation_digest(
    report: ResearchPacketResolutionCriteriaChangeImpactV2Report,
) -> str:
    return _public_payload_digest(_report_payload_without_digest(report))


def _public_payload_digest(payload_without_digest: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload_without_digest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _payload_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public payload decimal must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        return _payload_datetime(value)
    if type(value) is str:
        _require_canonical_public_string("public payload value", value)
        return value
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("public payload value must use Decimal strings")
    if type(value) is float:
        raise ValueError("public payload value must not be a float")
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    raise ValueError("public payload value is not JSON serializable")


def _payload_datetime(value: datetime) -> str:
    utc_value = _as_utc("public payload datetime", value)
    return utc_value.isoformat().replace("+00:00", "Z")


def _validate_public_payload_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload key must be a string")
            _require_canonical_public_string("public payload key", key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _validate_public_payload_value(item)
        return ready
    if isinstance(value, tuple):
        return [_validate_public_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_validate_public_payload_value(item) for item in value]
    if type(value) is str:
        _require_canonical_public_string("public payload value", value)
        return value
    if type(value) is bool:
        return value
    if isinstance(value, Decimal):
        raise ValueError("public payload value must be a string, not Decimal")
    if isinstance(value, int):
        raise ValueError("public payload value must use Decimal strings")
    if isinstance(value, float):
        raise ValueError("public payload value must not be a float")
    if value is None:
        raise ValueError("public payload value must not be null")
    raise ValueError("public payload value is not JSON serializable")


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _normalize_nonnegative_decimal("seconds", seconds + microseconds)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_public_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be integral")
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
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
    return value.quantize(DECIMAL_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe value")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be lowercase hex")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _require_hard_flags(value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


__all__ = (
    "IMPACT_BANDS",
    "REPORT_STATUSES",
    "OFFICIAL_SOURCE_TIERS",
    "ResearchPacketResolutionCriteriaChangeImpactV2Config",
    "ResearchPacketResolutionCriteriaChangeImpactV2Input",
    "ResearchPacketResolutionCriteriaChangeImpactV2Report",
    "estimate_research_packet_resolution_criteria_change_impact_v2",
    "research_packet_resolution_criteria_change_impact_v2_payload",
    "validate_research_packet_resolution_criteria_change_impact_v2_public_payload",
)
