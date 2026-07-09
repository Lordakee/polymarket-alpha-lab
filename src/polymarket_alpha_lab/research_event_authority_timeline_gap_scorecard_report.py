"""Report-only authority timeline gap scorecard for research events."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_AUTHORITY_TIMELINE_GAP_SCORECARD_CONFIG_VERSION = (
    "research-event-authority-timeline-gap-scorecard-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_STATUS_VALUES = frozenset(("pass", "watch", "block"))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "url",
    "text",
    "raw",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "recommendation",
    "sizing",
    "live",
    "network",
    "database",
    "persist",
    "mutation",
    "signing",
    "buy",
    "sell",
)
_REASON_CODE_SEQUENCE = (
    "empty_observations",
    "authority_timeline_pass",
    "timeline_gap_watch",
    "timeline_gap_block",
    "low_authority_confidence",
    "low_authority_coverage",
    "conflicting_authority_block",
)


@dataclass(frozen=True)
class ResearchEventAuthorityTimelineGapScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_AUTHORITY_TIMELINE_GAP_SCORECARD_CONFIG_VERSION
    )
    pass_timeline_gap_minutes: Decimal = Decimal("60.000000")
    watch_timeline_gap_minutes: Decimal = Decimal("240.000000")
    min_authority_confidence_score: Decimal = Decimal("0.700000")
    min_authority_coverage_score: Decimal = Decimal("0.700000")
    conflict_penalty_per_authority: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityTimelineGapScorecardConfig:
            raise TypeError(
                "ResearchEventAuthorityTimelineGapScorecardConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityTimelineGapScorecardConfig:
            raise ValueError(
                "config must be exactly ResearchEventAuthorityTimelineGapScorecardConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_AUTHORITY_TIMELINE_GAP_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "pass_timeline_gap_minutes",
            _require_nonnegative_decimal(
                "pass_timeline_gap_minutes",
                self.pass_timeline_gap_minutes,
            ),
        )
        object.__setattr__(
            self,
            "watch_timeline_gap_minutes",
            _require_positive_decimal(
                "watch_timeline_gap_minutes",
                self.watch_timeline_gap_minutes,
            ),
        )
        if self.watch_timeline_gap_minutes < self.pass_timeline_gap_minutes:
            raise ValueError(
                "watch_timeline_gap_minutes must be at least pass_timeline_gap_minutes",
            )
        for field_name in (
            "min_authority_confidence_score",
            "min_authority_coverage_score",
            "conflict_penalty_per_authority",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventAuthorityTimelineGapObservation:
    event_family: str
    authority_family: str
    observed_at: datetime
    timeline_gap_minutes: Decimal
    authority_confidence_score: Decimal
    authority_coverage_score: Decimal
    conflicting_authority_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityTimelineGapObservation:
            raise TypeError(
                "ResearchEventAuthorityTimelineGapObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityTimelineGapObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchEventAuthorityTimelineGapObservation",
            )
        _require_public_identifier("event_family", self.event_family)
        _require_public_identifier("authority_family", self.authority_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "timeline_gap_minutes",
            _require_nonnegative_decimal(
                "timeline_gap_minutes",
                self.timeline_gap_minutes,
            ),
        )
        for field_name in ("authority_confidence_score", "authority_coverage_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "conflicting_authority_count",
            _require_nonnegative_decimal(
                "conflicting_authority_count",
                self.conflicting_authority_count,
            ),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchEventAuthorityTimelineGapScorecardRow:
    event_family: str
    authority_family: str
    observed_at: datetime
    timeline_gap_minutes: Decimal
    authority_confidence_score: Decimal
    authority_coverage_score: Decimal
    conflicting_authority_count: Decimal
    timeliness_score: Decimal
    gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityTimelineGapScorecardRow:
            raise TypeError(
                "ResearchEventAuthorityTimelineGapScorecardRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityTimelineGapScorecardRow:
            raise ValueError(
                "row must be exactly ResearchEventAuthorityTimelineGapScorecardRow",
            )
        _require_public_identifier("event_family", self.event_family)
        _require_public_identifier("authority_family", self.authority_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "timeline_gap_minutes",
            "conflicting_authority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_confidence_score",
            "authority_coverage_score",
            "timeliness_score",
            "gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventAuthorityTimelineGapScorecardReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    event_family_count: Decimal
    authority_family_count: Decimal
    average_gap_score: Decimal
    max_timeline_gap_minutes: Decimal
    rows: tuple[ResearchEventAuthorityTimelineGapScorecardRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityTimelineGapScorecardReport:
            raise TypeError(
                "ResearchEventAuthorityTimelineGapScorecardReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityTimelineGapScorecardReport:
            raise ValueError(
                "report must be exactly ResearchEventAuthorityTimelineGapScorecardReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_AUTHORITY_TIMELINE_GAP_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "event_family_count",
            "authority_family_count",
            "max_timeline_gap_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_gap_score",
            _require_ratio_decimal("average_gap_score", self.average_gap_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchEventAuthorityTimelineGapScorecardReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_event_authority_timeline_gap_scorecard_report(
    observations: Sequence[ResearchEventAuthorityTimelineGapObservation],
    *,
    generated_at: datetime,
    config: ResearchEventAuthorityTimelineGapScorecardConfig | None = None,
) -> ResearchEventAuthorityTimelineGapScorecardReport:
    """Build a local report-only authority timeline gap scorecard."""

    if config is None:
        config = ResearchEventAuthorityTimelineGapScorecardConfig()
    if type(config) is not ResearchEventAuthorityTimelineGapScorecardConfig:
        raise ValueError(
            "config must be a ResearchEventAuthorityTimelineGapScorecardConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for item in normalized_observations:
        if item.observed_at > generated_at:
            raise ValueError("observation observed_at must not be after generated_at")
    rows = tuple(_row_from_observation(item, config) for item in normalized_observations)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "event_family_count": _decimal_count(
            len({row.event_family for row in rows}),
        ),
        "authority_family_count": _decimal_count(
            len({row.authority_family for row in rows}),
        ),
        "average_gap_score": _average(tuple(row.gap_score for row in rows)),
        "max_timeline_gap_minutes": max(
            (row.timeline_gap_minutes for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventAuthorityTimelineGapScorecardReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _row_from_observation(
    observation: ResearchEventAuthorityTimelineGapObservation,
    config: ResearchEventAuthorityTimelineGapScorecardConfig,
) -> ResearchEventAuthorityTimelineGapScorecardRow:
    timeliness_score = _timeliness_score(observation.timeline_gap_minutes, config)
    conflict_penalty = _clamp_ratio(
        observation.conflicting_authority_count * config.conflict_penalty_per_authority,
    )
    gap_score = _clamp_ratio(
        _average(
            (
                observation.authority_confidence_score,
                observation.authority_coverage_score,
                timeliness_score,
            ),
        )
        - conflict_penalty,
    )
    status = _row_status(observation, config)
    return ResearchEventAuthorityTimelineGapScorecardRow(
        event_family=observation.event_family,
        authority_family=observation.authority_family,
        observed_at=observation.observed_at,
        timeline_gap_minutes=observation.timeline_gap_minutes,
        authority_confidence_score=observation.authority_confidence_score,
        authority_coverage_score=observation.authority_coverage_score,
        conflicting_authority_count=observation.conflicting_authority_count,
        timeliness_score=timeliness_score,
        gap_score=gap_score,
        status=status,
        reason_codes=_row_reason_codes(observation, config, status),
    )


def _timeliness_score(
    timeline_gap_minutes: Decimal,
    config: ResearchEventAuthorityTimelineGapScorecardConfig,
) -> Decimal:
    if timeline_gap_minutes >= config.watch_timeline_gap_minutes:
        return _ZERO
    return _clamp_ratio(_ONE - (timeline_gap_minutes / config.watch_timeline_gap_minutes))


def _row_status(
    observation: ResearchEventAuthorityTimelineGapObservation,
    config: ResearchEventAuthorityTimelineGapScorecardConfig,
) -> str:
    if (
        observation.conflicting_authority_count > _ZERO
        or observation.timeline_gap_minutes > config.watch_timeline_gap_minutes
    ):
        return "block"
    if (
        observation.timeline_gap_minutes > config.pass_timeline_gap_minutes
        or observation.authority_confidence_score < config.min_authority_confidence_score
        or observation.authority_coverage_score < config.min_authority_coverage_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: ResearchEventAuthorityTimelineGapObservation,
    config: ResearchEventAuthorityTimelineGapScorecardConfig,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if status == "pass":
        reason_codes.append("authority_timeline_pass")
    elif observation.timeline_gap_minutes > config.watch_timeline_gap_minutes:
        reason_codes.append("timeline_gap_block")
    elif observation.timeline_gap_minutes > config.pass_timeline_gap_minutes:
        reason_codes.append("timeline_gap_watch")
    if observation.authority_confidence_score < config.min_authority_confidence_score:
        reason_codes.append("low_authority_confidence")
    if observation.authority_coverage_score < config.min_authority_coverage_score:
        reason_codes.append("low_authority_coverage")
    if observation.conflicting_authority_count > _ZERO:
        reason_codes.append("conflicting_authority_block")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchEventAuthorityTimelineGapScorecardRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventAuthorityTimelineGapScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchEventAuthorityTimelineGapScorecardRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_row_consistency(row: ResearchEventAuthorityTimelineGapScorecardRow) -> None:
    if row.status == "pass" and row.reason_codes != ("authority_timeline_pass",):
        raise ValueError("pass rows must include only authority_timeline_pass")
    if row.status == "block" and not (
        "timeline_gap_block" in row.reason_codes
        or "conflicting_authority_block" in row.reason_codes
    ):
        raise ValueError("block rows must include a block reason")


def _validate_report_consistency(
    report: ResearchEventAuthorityTimelineGapScorecardReport,
) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.event_family_count != _decimal_count(
        len({row.event_family for row in report.rows}),
    ):
        raise ValueError("event_family_count must match rows")
    if report.authority_family_count != _decimal_count(
        len({row.authority_family for row in report.rows}),
    ):
        raise ValueError("authority_family_count must match rows")
    if report.average_gap_score != _average(tuple(row.gap_score for row in report.rows)):
        raise ValueError("average_gap_score must match rows")
    expected_max_gap = max(
        (row.timeline_gap_minutes for row in report.rows),
        default=_ZERO,
    )
    if report.max_timeline_gap_minutes != expected_max_gap:
        raise ValueError("max_timeline_gap_minutes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Sequence[ResearchEventAuthorityTimelineGapObservation],
) -> tuple[ResearchEventAuthorityTimelineGapObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchEventAuthorityTimelineGapObservation] = []
    for item in observations:
        if type(item) is not ResearchEventAuthorityTimelineGapObservation:
            raise ValueError(
                "observations must contain ResearchEventAuthorityTimelineGapObservation",
            )
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.event_family,
                item.authority_family,
                item.observed_at,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchEventAuthorityTimelineGapScorecardRow],
) -> tuple[ResearchEventAuthorityTimelineGapScorecardRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchEventAuthorityTimelineGapScorecardRow] = []
    for row in rows:
        if type(row) is not ResearchEventAuthorityTimelineGapScorecardRow:
            raise ValueError(
                "rows must contain ResearchEventAuthorityTimelineGapScorecardRow",
            )
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                row.event_family,
                row.authority_family,
                row.observed_at,
            ),
        ),
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
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


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchEventAuthorityTimelineGapScorecardReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if _has_unsafe_public_term(lowered):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if _has_unsafe_public_term(lowered):
        raise ValueError(f"{field_name} has unsafe public value")


def _has_unsafe_public_term(value: str) -> bool:
    if any(term in value for term in _UNSAFE_PUBLIC_TERMS):
        return True
    return value == "auth" or value.startswith("auth_") or value.endswith("_auth") or "_auth_" in value


__all__ = (
    "DEFAULT_RESEARCH_EVENT_AUTHORITY_TIMELINE_GAP_SCORECARD_CONFIG_VERSION",
    "ResearchEventAuthorityTimelineGapObservation",
    "ResearchEventAuthorityTimelineGapScorecardConfig",
    "ResearchEventAuthorityTimelineGapScorecardReport",
    "ResearchEventAuthorityTimelineGapScorecardRow",
    "build_research_event_authority_timeline_gap_scorecard_report",
)
