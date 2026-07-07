from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_PACKET_INFORMATION_REFRESH_PRIORITY_V2_CONFIG_VERSION = (
    "research-packet-information-refresh-priority-v2"
)

Q = Decimal("0.000001")
COUNT_Q = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_ZERO = Decimal("0")
COUNT_ONE = Decimal("1")

PRIORITY_BANDS = frozenset(("high", "medium", "low"))
REFRESH_ACTIONS = frozenset(("collect_now", "queue_monitor", "defer_review"))
REASON_PRIORITY = {
    "source_age_high": 0,
    "source_age_watch": 1,
    "source_age_low": 2,
    "event_velocity_high": 3,
    "event_velocity_normal": 4,
    "event_velocity_low": 5,
    "contradiction_severity_high": 6,
    "contradiction_severity_normal": 7,
    "contradiction_severity_low": 8,
    "resolution_horizon_near": 9,
    "resolution_horizon_watch": 10,
    "resolution_horizon_distant": 11,
    "official_source_gap_high": 12,
    "official_source_gap_normal": 13,
    "official_source_gap_none": 14,
    "team_uncertainty_elevated": 15,
    "team_uncertainty_normal": 16,
    "team_uncertainty_low": 17,
    "priority_high": 18,
    "priority_medium": 19,
    "priority_low": 20,
}
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "candidate_count",
        "high_priority_count",
        "medium_priority_count",
        "low_priority_count",
        "average_priority_score",
        "max_priority_score",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "rank",
        "packet_id",
        "event_title",
        "source_age_hours",
        "source_age_score",
        "event_velocity",
        "contradiction_severity",
        "hours_to_resolution",
        "resolution_horizon_score",
        "official_source_gap",
        "team_uncertainty",
        "priority_score",
        "priority_band",
        "refresh_action",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "li" + "ve",
        "au" + "th",
        "wal" + "let",
        "or" + "der",
        "net" + "work",
        "data" + "base",
        "per" + "sist",
        "sign" + "ing",
        "muta" + "tion",
        "b" + "uy",
        "se" + "ll",
        "tra" + "de",
    ),
)


@dataclass(frozen=True)
class ResearchPacketInformationRefreshPriorityV2Config:
    config_version: str
    stale_source_hours: Decimal
    resolution_horizon_hours: Decimal
    high_priority_threshold: Decimal
    medium_priority_threshold: Decimal
    source_age_weight: Decimal
    event_velocity_weight: Decimal
    contradiction_severity_weight: Decimal
    resolution_horizon_weight: Decimal
    official_source_gap_weight: Decimal
    team_uncertainty_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _config_version(self.config_version)
        for name in ("stale_source_hours", "resolution_horizon_hours"):
            object.__setattr__(self, name, _dec_positive(name, getattr(self, name)))
        for name in ("high_priority_threshold", "medium_priority_threshold"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        if self.medium_priority_threshold > self.high_priority_threshold:
            raise ValueError("medium_priority_threshold must not exceed high_priority_threshold")
        for name in (
            "source_age_weight",
            "event_velocity_weight",
            "contradiction_severity_weight",
            "resolution_horizon_weight",
            "official_source_gap_weight",
            "team_uncertainty_weight",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        if _weight_total(self) != ONE:
            raise ValueError("priority weights must total 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketInformationRefreshPriorityV2Candidate:
    packet_id: str
    event_title: str
    source_age_hours: Decimal
    event_velocity: Decimal
    contradiction_severity: Decimal
    hours_to_resolution: Decimal
    official_source_gap: Decimal
    team_uncertainty: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _safe_text("packet_id", self.packet_id)
        _safe_text("event_title", self.event_title)
        for name in ("source_age_hours", "hours_to_resolution"):
            object.__setattr__(self, name, _dec_nonnegative(name, getattr(self, name)))
        for name in (
            "event_velocity",
            "contradiction_severity",
            "official_source_gap",
            "team_uncertainty",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchPacketInformationRefreshPriorityV2Row:
    rank: Decimal
    packet_id: str
    event_title: str
    source_age_hours: Decimal
    source_age_score: Decimal
    event_velocity: Decimal
    contradiction_severity: Decimal
    hours_to_resolution: Decimal
    resolution_horizon_score: Decimal
    official_source_gap: Decimal
    team_uncertainty: Decimal
    priority_score: Decimal
    priority_band: str
    refresh_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _count_positive("rank", self.rank))
        _safe_text("packet_id", self.packet_id)
        _safe_text("event_title", self.event_title)
        for name in ("source_age_hours", "hours_to_resolution"):
            object.__setattr__(self, name, _dec_nonnegative(name, getattr(self, name)))
        for name in (
            "source_age_score",
            "event_velocity",
            "contradiction_severity",
            "resolution_horizon_score",
            "official_source_gap",
            "team_uncertainty",
            "priority_score",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        _member("priority_band", self.priority_band, PRIORITY_BANDS)
        _member("refresh_action", self.refresh_action, REFRESH_ACTIONS)
        object.__setattr__(self, "reason_codes", _reason_codes(self.reason_codes))
        if self.refresh_action != _refresh_action_for_band(self.priority_band):
            raise ValueError("refresh_action must match priority_band")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchPacketInformationRefreshPriorityV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    high_priority_count: Decimal
    medium_priority_count: Decimal
    low_priority_count: Decimal
    average_priority_score: Decimal
    max_priority_score: Decimal
    rows: tuple[ResearchPacketInformationRefreshPriorityV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _config_version(self.config_version)
        for name in (
            "candidate_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
        ):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        for name in ("average_priority_score", "max_priority_score"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        if (
            type(self.rows) is not tuple
            or not all(
                type(row) is ResearchPacketInformationRefreshPriorityV2Row
                for row in self.rows
            )
        ):
            raise ValueError("rows must contain refresh priority row values")
        _hex_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_digest(self)
        _report_matches(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_information_refresh_priority_v2_payload(self)


def build_research_packet_information_refresh_priority_v2(
    candidates: Iterable[ResearchPacketInformationRefreshPriorityV2Candidate],
    *,
    config: ResearchPacketInformationRefreshPriorityV2Config,
    generated_at: datetime,
) -> ResearchPacketInformationRefreshPriorityV2Report:
    if type(config) is not ResearchPacketInformationRefreshPriorityV2Config:
        raise ValueError("config must be a refresh priority config")
    _require_hard_flags("config", config)
    stamp = _as_utc("generated_at", generated_at)
    source_rows = tuple(candidates)
    if not all(
        type(row) is ResearchPacketInformationRefreshPriorityV2Candidate
        for row in source_rows
    ):
        raise ValueError("candidate rows must contain refresh priority candidates")
    built_rows = tuple(
        _ranked_rows(
            tuple(_row(candidate, config) for candidate in source_rows),
        ),
    )
    report_values = {
        "generated_at": stamp,
        "config_version": config.config_version,
        "candidate_count": Decimal(len(built_rows)),
        "high_priority_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.priority_band == "high"),
        ),
        "medium_priority_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.priority_band == "medium"),
        ),
        "low_priority_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.priority_band == "low"),
        ),
        "average_priority_score": _average(
            tuple(row.priority_score for row in built_rows),
        ),
        "max_priority_score": max(
            (row.priority_score for row in built_rows),
            default=ZERO,
        ),
        "rows": built_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = _derive_digest_from_public_payload(_payload(report_values))
    return ResearchPacketInformationRefreshPriorityV2Report(
        **report_values,
        derived_validation_digest=digest,
    )


def research_packet_information_refresh_priority_v2_payload(
    report: ResearchPacketInformationRefreshPriorityV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketInformationRefreshPriorityV2Report:
        _require_hard_flags("report", report)
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a refresh priority report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _require_payload_digest(payload)
    return payload


def derive_research_packet_information_refresh_priority_v2_digest(
    report: ResearchPacketInformationRefreshPriorityV2Report | dict[str, Any],
) -> str:
    if type(report) is ResearchPacketInformationRefreshPriorityV2Report:
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a refresh priority report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload, digest_required=False)
    _require_hard_flags("payload", _DictFlags(payload))
    return _derive_digest_from_public_payload(payload)


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


def _row(
    candidate: ResearchPacketInformationRefreshPriorityV2Candidate,
    config: ResearchPacketInformationRefreshPriorityV2Config,
) -> ResearchPacketInformationRefreshPriorityV2Row:
    source_age_score = _clamp_unit(_q(candidate.source_age_hours / config.stale_source_hours))
    resolution_horizon_score = _clamp_unit(
        ONE - _q(candidate.hours_to_resolution / config.resolution_horizon_hours),
    )
    priority_score = _priority_score(
        config,
        source_age_score=source_age_score,
        event_velocity=candidate.event_velocity,
        contradiction_severity=candidate.contradiction_severity,
        resolution_horizon_score=resolution_horizon_score,
        official_source_gap=candidate.official_source_gap,
        team_uncertainty=candidate.team_uncertainty,
    )
    band = _priority_band(priority_score, config)
    return ResearchPacketInformationRefreshPriorityV2Row(
        rank=COUNT_ONE,
        packet_id=candidate.packet_id,
        event_title=candidate.event_title,
        source_age_hours=candidate.source_age_hours,
        source_age_score=source_age_score,
        event_velocity=candidate.event_velocity,
        contradiction_severity=candidate.contradiction_severity,
        hours_to_resolution=candidate.hours_to_resolution,
        resolution_horizon_score=resolution_horizon_score,
        official_source_gap=candidate.official_source_gap,
        team_uncertainty=candidate.team_uncertainty,
        priority_score=priority_score,
        priority_band=band,
        refresh_action=_refresh_action_for_band(band),
        reason_codes=_dedupe(
            (
                _source_age_reason(source_age_score),
                _unit_reason("event_velocity", candidate.event_velocity),
                _unit_reason("contradiction_severity", candidate.contradiction_severity),
                _resolution_reason(resolution_horizon_score),
                _official_gap_reason(candidate.official_source_gap),
                _team_uncertainty_reason(candidate.team_uncertainty),
                f"priority_{band}",
            ),
        ),
    )


def _ranked_rows(
    rows: tuple[ResearchPacketInformationRefreshPriorityV2Row, ...],
) -> tuple[ResearchPacketInformationRefreshPriorityV2Row, ...]:
    ranked = []
    for index, row in enumerate(sorted(rows, key=_row_key), start=1):
        ranked.append(
            ResearchPacketInformationRefreshPriorityV2Row(
                rank=Decimal(index),
                packet_id=row.packet_id,
                event_title=row.event_title,
                source_age_hours=row.source_age_hours,
                source_age_score=row.source_age_score,
                event_velocity=row.event_velocity,
                contradiction_severity=row.contradiction_severity,
                hours_to_resolution=row.hours_to_resolution,
                resolution_horizon_score=row.resolution_horizon_score,
                official_source_gap=row.official_source_gap,
                team_uncertainty=row.team_uncertainty,
                priority_score=row.priority_score,
                priority_band=row.priority_band,
                refresh_action=row.refresh_action,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked)


def _row_key(row: ResearchPacketInformationRefreshPriorityV2Row) -> tuple[Decimal, str]:
    return (-row.priority_score, row.packet_id)


def _priority_score(
    config: ResearchPacketInformationRefreshPriorityV2Config,
    *,
    source_age_score: Decimal,
    event_velocity: Decimal,
    contradiction_severity: Decimal,
    resolution_horizon_score: Decimal,
    official_source_gap: Decimal,
    team_uncertainty: Decimal,
) -> Decimal:
    return _q(
        source_age_score * config.source_age_weight
        + event_velocity * config.event_velocity_weight
        + contradiction_severity * config.contradiction_severity_weight
        + resolution_horizon_score * config.resolution_horizon_weight
        + official_source_gap * config.official_source_gap_weight
        + team_uncertainty * config.team_uncertainty_weight,
    )


def _priority_band(
    priority_score: Decimal,
    config: ResearchPacketInformationRefreshPriorityV2Config,
) -> str:
    if priority_score >= config.high_priority_threshold:
        return "high"
    if priority_score >= config.medium_priority_threshold:
        return "medium"
    return "low"


def _refresh_action_for_band(priority_band: str) -> str:
    if priority_band == "high":
        return "collect_now"
    if priority_band == "medium":
        return "queue_monitor"
    return "defer_review"


def _source_age_reason(source_age_score: Decimal) -> str:
    if source_age_score >= Decimal("0.750000"):
        return "source_age_high"
    if source_age_score >= Decimal("0.250000"):
        return "source_age_watch"
    return "source_age_low"


def _unit_reason(prefix: str, value: Decimal) -> str:
    if value >= Decimal("0.750000"):
        return f"{prefix}_high"
    if value >= Decimal("0.250000"):
        return f"{prefix}_normal"
    return f"{prefix}_low"


def _resolution_reason(value: Decimal) -> str:
    if value >= Decimal("0.750000"):
        return "resolution_horizon_near"
    if value >= Decimal("0.250000"):
        return "resolution_horizon_watch"
    return "resolution_horizon_distant"


def _official_gap_reason(value: Decimal) -> str:
    if value >= Decimal("0.500000"):
        return "official_source_gap_high"
    if value > ZERO:
        return "official_source_gap_normal"
    return "official_source_gap_none"


def _team_uncertainty_reason(value: Decimal) -> str:
    if value >= Decimal("0.500000"):
        return "team_uncertainty_elevated"
    if value >= Decimal("0.250000"):
        return "team_uncertainty_normal"
    return "team_uncertainty_low"


def _report_matches(report: ResearchPacketInformationRefreshPriorityV2Report) -> None:
    rows = report.rows
    expected_count = Decimal(len(rows))
    if report.candidate_count != expected_count:
        raise ValueError("candidate_count must match rows")
    if report.high_priority_count != Decimal(
        sum(COUNT_ONE for row in rows if row.priority_band == "high"),
    ):
        raise ValueError("high_priority_count must match rows")
    if report.medium_priority_count != Decimal(
        sum(COUNT_ONE for row in rows if row.priority_band == "medium"),
    ):
        raise ValueError("medium_priority_count must match rows")
    if report.low_priority_count != Decimal(
        sum(COUNT_ONE for row in rows if row.priority_band == "low"),
    ):
        raise ValueError("low_priority_count must match rows")
    if report.average_priority_score != _average(tuple(row.priority_score for row in rows)):
        raise ValueError("average_priority_score must match rows")
    if report.max_priority_score != max(
        (row.priority_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_priority_score must match rows")
    expected_ranks = tuple(Decimal(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("row ranks must be sequential")


def _validate_digest(report: ResearchPacketInformationRefreshPriorityV2Report) -> None:
    if report.derived_validation_digest != _derive_digest_from_public_payload(
        _payload(report),
    ):
        raise ValueError("derived_validation_digest must match report payload")


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _hex_digest("derived_validation_digest", digest)
    if digest != _derive_digest_from_public_payload(payload):
        raise ValueError("derived_validation_digest must match report payload")


def _derive_digest_from_public_payload(payload: dict[str, Any]) -> str:
    core = {
        key: item
        for key, item in payload.items()
        if key != "derived_validation_digest"
    }
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _payload(value: Any, *, field_name: str | None = None) -> Any:
    if isinstance(value, Decimal):
        if field_name in {
            "rank",
            "candidate_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
        } and value == value.to_integral_value():
            return str(value.quantize(COUNT_Q))
        return str(value)
    if type(value) is datetime:
        text = value.astimezone(UTC).isoformat()
        if text.endswith("+00:00"):
            return text[:-6] + "Z"
        return text
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload(getattr(value, field.name), field_name=field.name)
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload(item) for item in value]
    if isinstance(value, list):
        return [_payload(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _payload(item, field_name=key)
            for key, item in value.items()
        }
    return value


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(_payload(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) is bool or type(value) is str or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _unsafe_text(key):
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _unsafe_text(value):
        raise ValueError("unsafe public payload value")


def _require_supported_payload(
    payload: dict[str, Any],
    *,
    digest_required: bool = True,
) -> None:
    for key in payload:
        if key not in REPORT_PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")
    if digest_required and "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest must be present")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain payload objects")
        for key in row:
            if key not in ROW_PAYLOAD_FIELDS:
                raise ValueError("payload field is not supported")
        _require_hard_flags("row payload", _DictFlags(row))


def _unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(_checked_reason(value) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _checked_reason(value: str) -> str:
    if type(value) is not str or value not in REASON_PRIORITY:
        raise ValueError("reason_codes must be supported")
    if _unsafe_text(value):
        raise ValueError("unsafe public payload value")
    return value


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        _checked_reason(value)
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(sorted(result, key=lambda item: REASON_PRIORITY[item]))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _q(sum(values, ZERO) / Decimal(len(values)))


def _weight_total(config: ResearchPacketInformationRefreshPriorityV2Config) -> Decimal:
    return _q(
        config.source_age_weight
        + config.event_velocity_weight
        + config.contradiction_severity_weight
        + config.resolution_horizon_weight
        + config.official_source_gap_weight
        + config.team_uncertainty_weight,
    )


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _safe_text(name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{name} must not have outer whitespace")
    if _unsafe_text(value):
        raise ValueError("unsafe public payload value")


def _config_version(value: str) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_PACKET_INFORMATION_REFRESH_PRIORITY_V2_CONFIG_VERSION:
        raise ValueError("config_version is not supported")


def _hex_digest(name: str, value: str) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _member(name: str, value: str, allowed: frozenset[str]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} is not supported")


def _dec(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _q(value)


def _dec_nonnegative(name: str, value: Decimal) -> Decimal:
    result = _dec(name, value)
    if result < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return result


def _dec_positive(name: str, value: Decimal) -> Decimal:
    result = _dec(name, value)
    if result <= ZERO:
        raise ValueError(f"{name} must be positive")
    return result


def _ratio(name: str, value: Decimal) -> Decimal:
    result = _dec_nonnegative(name, value)
    if result > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return result


def _count(name: str, value: Decimal) -> Decimal:
    result = _dec(name, value)
    if result < COUNT_ZERO or result != result.to_integral_value():
        raise ValueError(f"{name} must be a nonnegative whole Decimal")
    return result


def _count_positive(name: str, value: Decimal) -> Decimal:
    result = _count(name, value)
    if result <= COUNT_ZERO:
        raise ValueError(f"{name} must be positive")
    return result


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} must be readonly")


def _q(value: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 64
        ctx.rounding = ROUND_HALF_EVEN
        return value.quantize(Q)


def _clamp_unit(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


__all__ = (
    "DEFAULT_RESEARCH_PACKET_INFORMATION_REFRESH_PRIORITY_V2_CONFIG_VERSION",
    "ResearchPacketInformationRefreshPriorityV2Candidate",
    "ResearchPacketInformationRefreshPriorityV2Config",
    "ResearchPacketInformationRefreshPriorityV2Report",
    "ResearchPacketInformationRefreshPriorityV2Row",
    "build_research_packet_information_refresh_priority_v2",
    "derive_research_packet_information_refresh_priority_v2_digest",
    "research_packet_information_refresh_priority_v2_payload",
)
