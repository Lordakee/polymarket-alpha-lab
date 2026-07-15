"""Pure read-only quality gate for specialist team memory metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_MEMORY_QUALITY_GATE_CONFIG_VERSION = "team-memory-quality-gate-v0"

GATE_STATUSES = ("research_ready", "needs_review", "blocked")
GATE_NEXT_STEPS = {
    "research_ready": "allow_specialist_team_memory_research_use",
    "needs_review": "review_specialist_team_memory_before_research_use",
    "blocked": "block_specialist_team_memory_research_use",
}
BUNDLE_SAFETY_STATUSES = ("safe", "unsafe", "empty")
DIGEST_STATUSES = ("pass", "watch", "blocked")
COMPLETENESS_STATUSES = ("pass", "blocked")
FRESHNESS_STATUSES = ("pass", "watch", "blocked")
BLOCKED_STREAK_STATUSES = ("observed", "blocked")
REASON_CODES = (
    "team_memory_quality_gate_passed",
    "team_memory_quality_gate_source_metrics_empty",
    "team_memory_quality_gate_hard_flag_violation",
    "team_memory_quality_gate_bundle_empty",
    "team_memory_quality_gate_bundle_unsafe",
    "team_memory_quality_gate_duplicate_latest_digest",
    "team_memory_quality_gate_digest_blocked",
    "team_memory_quality_gate_blocked_streak_present",
    "team_memory_quality_gate_research_gaps_present",
    "team_memory_quality_gate_completeness_blocked",
    "team_memory_quality_gate_freshness_blocked",
    "team_memory_quality_gate_expired_sources_present",
    "team_memory_quality_gate_unknown_source_age_present",
    "team_memory_quality_gate_blocked_sources_present",
    "team_memory_quality_gate_quality_score_below_review_floor",
    "team_memory_quality_gate_digest_watch",
    "team_memory_quality_gate_blocked_streak_summary_blocked",
    "team_memory_quality_gate_freshness_watch",
    "team_memory_quality_gate_stale_sources_present",
    "team_memory_quality_gate_watch_streak_present",
    "team_memory_quality_gate_watch_sources_present",
    "team_memory_quality_gate_quality_score_below_ready_floor",
)
UNSAFE_PUBLIC_SURFACE_FRAGMENTS = tuple(
    "".join(chr(code) for code in codes)
    for codes in (
        (109, 97, 114, 107, 101, 116, 95, 115, 108, 117, 103),
        (113, 117, 101, 115, 116, 105, 111, 110),
        (105, 110, 118, 101, 115, 116, 109, 101, 110, 116),
        (114, 97, 110, 107),
        (98, 117, 121),
        (115, 101, 108, 108),
        (116, 114, 97, 100, 101),
        (119, 97, 108, 108, 101, 116),
        (111, 114, 100, 101, 114),
        (112, 111, 115, 105, 116, 105, 111, 110),
        (114, 101, 99, 111, 109, 109, 101, 110, 100),
        (115, 116, 114, 97, 116, 101, 103, 121, 95, 119, 101, 105, 103, 104, 116),
        (97, 117, 116, 104),
        (110, 101, 116, 119, 111, 114, 107),
        (108, 105, 118, 101),
    )
)
BLOCKING_REASON_CODES = frozenset(
    (
        "team_memory_quality_gate_source_metrics_empty",
        "team_memory_quality_gate_hard_flag_violation",
        "team_memory_quality_gate_bundle_empty",
        "team_memory_quality_gate_bundle_unsafe",
        "team_memory_quality_gate_duplicate_latest_digest",
        "team_memory_quality_gate_digest_blocked",
        "team_memory_quality_gate_blocked_streak_present",
        "team_memory_quality_gate_research_gaps_present",
        "team_memory_quality_gate_completeness_blocked",
        "team_memory_quality_gate_freshness_blocked",
        "team_memory_quality_gate_expired_sources_present",
        "team_memory_quality_gate_unknown_source_age_present",
        "team_memory_quality_gate_blocked_sources_present",
        "team_memory_quality_gate_quality_score_below_review_floor",
    )
)
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

__all__ = (
    "DEFAULT_TEAM_MEMORY_QUALITY_GATE_CONFIG_VERSION",
    "TeamMemoryQualityGateConfig",
    "TeamMemoryQualityGateMetrics",
    "TeamMemoryQualityGateResult",
    "build_team_memory_quality_gate",
)


@dataclass(frozen=True)
class TeamMemoryQualityGateConfig:
    config_version: str = DEFAULT_TEAM_MEMORY_QUALITY_GATE_CONFIG_VERSION
    min_research_ready_quality_score: Decimal = Decimal("0.800000")
    min_reviewable_quality_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_research_ready_quality_score",
            _require_probability_decimal(
                "min_research_ready_quality_score",
                self.min_research_ready_quality_score,
            ),
        )
        object.__setattr__(
            self,
            "min_reviewable_quality_score",
            _require_probability_decimal(
                "min_reviewable_quality_score",
                self.min_reviewable_quality_score,
            ),
        )
        if self.min_reviewable_quality_score > self.min_research_ready_quality_score:
            raise ValueError(
                "min_reviewable_quality_score must not exceed min_research_ready_quality_score"
            )
        _require_hard_flags("TeamMemoryQualityGateConfig", self)


@dataclass(frozen=True)
class TeamMemoryQualityGateMetrics:
    memory_id: str
    source_report_count: int
    team_count: int
    complete_team_count: int
    pass_source_count: int
    watch_source_count: int
    blocked_source_count: int
    research_gap_count: int
    stale_source_count: int
    expired_source_count: int
    unknown_source_age_count: int
    hard_flag_violation_count: int
    current_watch_streak_count: int
    current_blocked_streak_count: int
    bundle_safety_status: str
    digest_status: str
    completeness_status: str
    freshness_status: str
    blocked_streak_status: str
    latest_quality_score: Decimal
    duplicate_latest_digest_generated_at: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("memory_id", self.memory_id)
        for field_name in (
            "source_report_count",
            "team_count",
            "complete_team_count",
            "pass_source_count",
            "watch_source_count",
            "blocked_source_count",
            "research_gap_count",
            "stale_source_count",
            "expired_source_count",
            "unknown_source_age_count",
            "hard_flag_violation_count",
            "current_watch_streak_count",
            "current_blocked_streak_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_bundle_safety_status("bundle_safety_status", self.bundle_safety_status)
        _require_digest_status("digest_status", self.digest_status)
        _require_completeness_status("completeness_status", self.completeness_status)
        _require_freshness_status("freshness_status", self.freshness_status)
        _require_blocked_streak_status(
            "blocked_streak_status",
            self.blocked_streak_status,
        )
        object.__setattr__(
            self,
            "latest_quality_score",
            _require_probability_decimal(
                "latest_quality_score",
                self.latest_quality_score,
            ),
        )
        if type(self.duplicate_latest_digest_generated_at) is not bool:
            raise ValueError("duplicate_latest_digest_generated_at must be a bool")
        _require_hard_flags("TeamMemoryQualityGateMetrics", self)
        _validate_metrics_consistency(self)


@dataclass(frozen=True)
class TeamMemoryQualityGateResult:
    generated_at: datetime
    config_version: str
    gate_status: str
    gate_next_step: str
    redacted_memory_id: str
    source_report_count: int
    team_count: int
    complete_team_count: int
    pass_source_count: int
    watch_source_count: int
    blocked_source_count: int
    complete_team_ratio: Decimal | None
    watch_source_ratio: Decimal | None
    blocked_source_ratio: Decimal | None
    research_gap_count: int
    stale_source_count: int
    expired_source_count: int
    unknown_source_age_count: int
    hard_flag_violation_count: int
    current_watch_streak_count: int
    current_blocked_streak_count: int
    bundle_safety_status: str
    digest_status: str
    completeness_status: str
    freshness_status: str
    blocked_streak_status: str
    latest_quality_score: Decimal
    quality_score_floor: Decimal
    reviewable_quality_score_floor: Decimal
    duplicate_latest_digest_generated_at: bool
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_gate_status("gate_status", self.gate_status)
        _require_canonical_string("gate_next_step", self.gate_next_step)
        _require_redacted_memory_id("redacted_memory_id", self.redacted_memory_id)
        for field_name in (
            "source_report_count",
            "team_count",
            "complete_team_count",
            "pass_source_count",
            "watch_source_count",
            "blocked_source_count",
            "research_gap_count",
            "stale_source_count",
            "expired_source_count",
            "unknown_source_age_count",
            "hard_flag_violation_count",
            "current_watch_streak_count",
            "current_blocked_streak_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "complete_team_ratio",
            "watch_source_ratio",
            "blocked_source_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_bundle_safety_status("bundle_safety_status", self.bundle_safety_status)
        _require_digest_status("digest_status", self.digest_status)
        _require_completeness_status("completeness_status", self.completeness_status)
        _require_freshness_status("freshness_status", self.freshness_status)
        _require_blocked_streak_status(
            "blocked_streak_status",
            self.blocked_streak_status,
        )
        for field_name in (
            "latest_quality_score",
            "quality_score_floor",
            "reviewable_quality_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.duplicate_latest_digest_generated_at) is not bool:
            raise ValueError("duplicate_latest_digest_generated_at must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("TeamMemoryQualityGateResult", self)
        _reject_unsafe_public_payload(
            "team memory quality gate result",
            _payload_value(asdict(self)),
        )
        _validate_result_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("team memory quality gate payload", payload)
        if not isinstance(payload, dict):
            raise ValueError("team memory quality gate payload must be an object")
        return payload


def build_team_memory_quality_gate(
    metrics: TeamMemoryQualityGateMetrics,
    *,
    config: TeamMemoryQualityGateConfig,
    generated_at: datetime,
) -> TeamMemoryQualityGateResult:
    if type(metrics) is not TeamMemoryQualityGateMetrics:
        raise ValueError("metrics must be a TeamMemoryQualityGateMetrics")
    if type(config) is not TeamMemoryQualityGateConfig:
        raise ValueError("config must be a TeamMemoryQualityGateConfig")
    _require_hard_flags("TeamMemoryQualityGateMetrics", metrics)
    _require_hard_flags("TeamMemoryQualityGateConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    reason_codes = _reason_codes(metrics, config=config)
    gate_status = _gate_status(reason_codes)
    result_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "gate_status": gate_status,
        "gate_next_step": GATE_NEXT_STEPS[gate_status],
        "redacted_memory_id": _redacted_memory_id(metrics.memory_id),
        "source_report_count": metrics.source_report_count,
        "team_count": metrics.team_count,
        "complete_team_count": metrics.complete_team_count,
        "pass_source_count": metrics.pass_source_count,
        "watch_source_count": metrics.watch_source_count,
        "blocked_source_count": metrics.blocked_source_count,
        "complete_team_ratio": _optional_ratio(metrics.complete_team_count, metrics.team_count),
        "watch_source_ratio": _optional_ratio(metrics.watch_source_count, metrics.team_count),
        "blocked_source_ratio": _optional_ratio(metrics.blocked_source_count, metrics.team_count),
        "research_gap_count": metrics.research_gap_count,
        "stale_source_count": metrics.stale_source_count,
        "expired_source_count": metrics.expired_source_count,
        "unknown_source_age_count": metrics.unknown_source_age_count,
        "hard_flag_violation_count": metrics.hard_flag_violation_count,
        "current_watch_streak_count": metrics.current_watch_streak_count,
        "current_blocked_streak_count": metrics.current_blocked_streak_count,
        "bundle_safety_status": metrics.bundle_safety_status,
        "digest_status": metrics.digest_status,
        "completeness_status": metrics.completeness_status,
        "freshness_status": metrics.freshness_status,
        "blocked_streak_status": metrics.blocked_streak_status,
        "latest_quality_score": metrics.latest_quality_score,
        "quality_score_floor": config.min_research_ready_quality_score,
        "reviewable_quality_score_floor": config.min_reviewable_quality_score,
        "duplicate_latest_digest_generated_at": metrics.duplicate_latest_digest_generated_at,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    result_values["derived_validation_digest"] = _derived_validation_digest(result_values)
    return TeamMemoryQualityGateResult(**result_values)


def _reason_codes(
    metrics: TeamMemoryQualityGateMetrics,
    *,
    config: TeamMemoryQualityGateConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if metrics.source_report_count == 0:
        reasons.append("team_memory_quality_gate_source_metrics_empty")
    if metrics.hard_flag_violation_count > 0:
        reasons.append("team_memory_quality_gate_hard_flag_violation")
    if metrics.bundle_safety_status == "empty":
        reasons.append("team_memory_quality_gate_bundle_empty")
    if metrics.bundle_safety_status == "unsafe":
        reasons.append("team_memory_quality_gate_bundle_unsafe")
    if metrics.duplicate_latest_digest_generated_at:
        reasons.append("team_memory_quality_gate_duplicate_latest_digest")
    if metrics.digest_status == "blocked":
        reasons.append("team_memory_quality_gate_digest_blocked")
    if metrics.current_blocked_streak_count > 0:
        reasons.append("team_memory_quality_gate_blocked_streak_present")
    if metrics.research_gap_count > 0:
        reasons.append("team_memory_quality_gate_research_gaps_present")
    if metrics.completeness_status == "blocked":
        reasons.append("team_memory_quality_gate_completeness_blocked")
    if metrics.freshness_status == "blocked":
        reasons.append("team_memory_quality_gate_freshness_blocked")
    if metrics.expired_source_count > 0:
        reasons.append("team_memory_quality_gate_expired_sources_present")
    if metrics.unknown_source_age_count > 0:
        reasons.append("team_memory_quality_gate_unknown_source_age_present")
    if metrics.blocked_source_count > 0:
        reasons.append("team_memory_quality_gate_blocked_sources_present")
    if metrics.latest_quality_score < config.min_reviewable_quality_score:
        reasons.append("team_memory_quality_gate_quality_score_below_review_floor")
    if metrics.digest_status == "watch":
        reasons.append("team_memory_quality_gate_digest_watch")
    if metrics.blocked_streak_status == "blocked":
        reasons.append("team_memory_quality_gate_blocked_streak_summary_blocked")
    if metrics.freshness_status == "watch":
        reasons.append("team_memory_quality_gate_freshness_watch")
    if metrics.stale_source_count > 0:
        reasons.append("team_memory_quality_gate_stale_sources_present")
    if metrics.current_watch_streak_count > 0:
        reasons.append("team_memory_quality_gate_watch_streak_present")
    if metrics.watch_source_count > 0:
        reasons.append("team_memory_quality_gate_watch_sources_present")
    if metrics.latest_quality_score < config.min_research_ready_quality_score:
        reasons.append("team_memory_quality_gate_quality_score_below_ready_floor")
    return tuple(reasons or ("team_memory_quality_gate_passed",))


def _gate_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("team_memory_quality_gate_passed",):
        return "research_ready"
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    return "needs_review"


def _optional_ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_probability(Decimal(numerator) / Decimal(denominator))


def _redacted_memory_id(memory_id: str) -> str:
    return f"memory:{sha256(memory_id.encode('utf-8')).hexdigest()[:12]}"


def _require_redacted_memory_id(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    prefix = "memory:"
    digest = value.removeprefix(prefix)
    if (
        not value.startswith(prefix)
        or len(digest) != 12
        or any(char not in "0123456789abcdef" for char in digest)
    ):
        raise ValueError(f"{field_name} must be redacted")


def _validate_metrics_consistency(metrics: TeamMemoryQualityGateMetrics) -> None:
    if metrics.complete_team_count > metrics.team_count:
        raise ValueError("complete_team_count must not exceed team_count")
    if (
        metrics.pass_source_count
        + metrics.watch_source_count
        + metrics.blocked_source_count
        != metrics.team_count
    ):
        raise ValueError("source counts must equal team_count")
    if metrics.source_report_count == 0 and metrics.team_count != 0:
        raise ValueError("team_count must be zero without source reports")


def _validate_result_consistency(report: TeamMemoryQualityGateResult) -> None:
    if report.complete_team_count > report.team_count:
        raise ValueError("complete_team_count must not exceed team_count")
    if (
        report.pass_source_count
        + report.watch_source_count
        + report.blocked_source_count
        != report.team_count
    ):
        raise ValueError("source counts must equal team_count")
    if report.complete_team_ratio != _optional_ratio(
        report.complete_team_count,
        report.team_count,
    ):
        raise ValueError("complete_team_ratio must match counts")
    if report.watch_source_ratio != _optional_ratio(
        report.watch_source_count,
        report.team_count,
    ):
        raise ValueError("watch_source_ratio must match counts")
    if report.blocked_source_ratio != _optional_ratio(
        report.blocked_source_count,
        report.team_count,
    ):
        raise ValueError("blocked_source_ratio must match counts")
    expected_status = _gate_status(report.reason_codes)
    if report.gate_status != expected_status:
        raise ValueError("gate_status must match reason_codes")
    if report.gate_next_step != GATE_NEXT_STEPS[report.gate_status]:
        raise ValueError("gate_next_step must match gate_status")
    if report.reason_codes == ("team_memory_quality_gate_passed",):
        if report.source_report_count == 0:
            raise ValueError("passed gate requires source reports")
        if report.team_count == 0:
            raise ValueError("passed gate requires teams")
        if report.complete_team_count != report.team_count:
            raise ValueError("passed gate requires complete teams")
        if report.latest_quality_score < report.quality_score_floor:
            raise ValueError("passed gate requires quality score floor")
    if report.reviewable_quality_score_floor > report.quality_score_floor:
        raise ValueError("reviewable_quality_score_floor must not exceed quality_score_floor")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        return str(_require_probability_decimal("payload decimal", value))
    if isinstance(value, datetime):
        return _as_utc("payload datetime", value).isoformat()
    if isinstance(value, dict):
        return {
            key: _payload_value(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    return value


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if isinstance(payload, dict):
        for key, item in payload.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_text(f"{label} key", key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            _reject_unsafe_public_payload(label, item)
        return
    if type(payload) is float:
        raise ValueError(f"unsafe public payload in {label}")
    if type(payload) is str:
        _reject_unsafe_text(label, payload)


def _reject_unsafe_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(value)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)
    if normalized != expected:
        raise ValueError("reason_codes must use deterministic reason sequence")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_gate_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be a known gate status")


def _require_bundle_safety_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in BUNDLE_SAFETY_STATUSES:
        raise ValueError(f"{field_name} must be safe, unsafe, or empty")


def _require_digest_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_completeness_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in COMPLETENESS_STATUSES:
        raise ValueError(f"{field_name} must be pass or blocked")


def _require_freshness_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in FRESHNESS_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_blocked_streak_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in BLOCKED_STREAK_STATUSES:
        raise ValueError(f"{field_name} must be observed or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize_probability(value)


def _require_optional_probability_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _quantize_probability(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
