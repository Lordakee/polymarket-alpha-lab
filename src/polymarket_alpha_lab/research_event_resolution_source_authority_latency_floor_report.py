"""Pure report-only event-resolution source authority latency floor reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_AUTHORITY_LATENCY_FLOOR_REPORT_CONFIG_VERSION = (
    "research-event-resolution-source-authority-latency-floor-report-v0"
)
RESEARCH_EVENT_RESOLUTION_SOURCE_AUTHORITY_LATENCY_FLOOR_STATUSES = (
    "pass",
    "watch",
    "block",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECOND_DIVISOR = Decimal("1000000")
FLOOR_SCORE_STABILITY_BONUS = Decimal("0.024283")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NO_INPUTS_REASON = "event_resolution_source_authority_latency_floor_no_inputs"
PASS_REASON = "event_resolution_source_authority_latency_floor_pass"
FLOOR_BELOW_PASS_REASON = "source_authority_latency_floor_score_below_pass_threshold"
FLOOR_BELOW_WATCH_REASON = "source_authority_latency_floor_score_below_watch_threshold"
SOURCE_ABOVE_PASS_REASON = "source_latency_above_pass_threshold"
SOURCE_ABOVE_WATCH_REASON = "source_latency_above_watch_threshold"
AUTHORITY_ABOVE_PASS_REASON = "authority_latency_above_pass_threshold"
AUTHORITY_ABOVE_WATCH_REASON = "authority_latency_above_watch_threshold"
GAP_ABOVE_WATCH_REASON = "latency_gap_above_watch_threshold"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    FLOOR_BELOW_WATCH_REASON,
    SOURCE_ABOVE_WATCH_REASON,
    AUTHORITY_ABOVE_WATCH_REASON,
    GAP_ABOVE_WATCH_REASON,
    FLOOR_BELOW_PASS_REASON,
    SOURCE_ABOVE_PASS_REASON,
    AUTHORITY_ABOVE_PASS_REASON,
    PASS_REASON,
)
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
HARD_FLAG_FIELD_NAMES = ("paper_only", "report_only", "readonly")

DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "question",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "http://",
    "https://",
    "www.",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "sizing",
    "recommend",
)
UNSAFE_PUBLIC_KEYS = tuple(
    "".join(character for character in fragment.casefold() if character.isalnum())
    for fragment in UNSAFE_PUBLIC_FRAGMENTS
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_AUTHORITY_LATENCY_FLOOR_REPORT_CONFIG_VERSION",
    "RESEARCH_EVENT_RESOLUTION_SOURCE_AUTHORITY_LATENCY_FLOOR_STATUSES",
    "ResearchEventResolutionSourceAuthorityLatencyFloorConfig",
    "ResearchEventResolutionSourceAuthorityLatencyFloorInput",
    "ResearchEventResolutionSourceAuthorityLatencyFloorObservation",
    "ResearchEventResolutionSourceAuthorityLatencyFloorReasonCodeCount",
    "ResearchEventResolutionSourceAuthorityLatencyFloorReport",
    "ResearchEventResolutionSourceAuthorityLatencyFloorRow",
    "build_research_event_resolution_source_authority_latency_floor_report",
    "research_event_resolution_source_authority_latency_floor_report_digest",
    "research_event_resolution_source_authority_latency_floor_report_payload",
    "validate_research_event_resolution_source_authority_latency_floor_report_payload",
)


@dataclass(frozen=True)
class ResearchEventResolutionSourceAuthorityLatencyFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_AUTHORITY_LATENCY_FLOOR_REPORT_CONFIG_VERSION
    )
    source_latency_pass_threshold_seconds: Decimal = Decimal("1200.000000")
    source_latency_watch_threshold_seconds: Decimal = Decimal("3600.000000")
    authority_latency_pass_threshold_seconds: Decimal = Decimal("1800.000000")
    authority_latency_watch_threshold_seconds: Decimal = Decimal("7200.000000")
    latency_gap_watch_threshold_seconds: Decimal = Decimal("3000.000000")
    source_authority_latency_floor_pass_score: Decimal = Decimal("0.900000")
    source_authority_latency_floor_watch_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceAuthorityLatencyFloorConfig:
            raise TypeError(
                "ResearchEventResolutionSourceAuthorityLatencyFloorConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSourceAuthorityLatencyFloorConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_AUTHORITY_LATENCY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_latency_pass_threshold_seconds",
            "source_latency_watch_threshold_seconds",
            "authority_latency_pass_threshold_seconds",
            "authority_latency_watch_threshold_seconds",
            "latency_gap_watch_threshold_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.source_latency_pass_threshold_seconds
            >= self.source_latency_watch_threshold_seconds
        ):
            raise ValueError("source latency pass threshold must be below watch")
        if (
            self.authority_latency_pass_threshold_seconds
            >= self.authority_latency_watch_threshold_seconds
        ):
            raise ValueError("authority latency pass threshold must be below watch")
        for field_name in (
            "source_authority_latency_floor_pass_score",
            "source_authority_latency_floor_watch_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.source_authority_latency_floor_watch_score
            > self.source_authority_latency_floor_pass_score
        ):
            raise ValueError("floor watch score must not exceed floor pass score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceAuthorityLatencyFloorObservation:
    private_resolution_ref: str
    observed_at: datetime
    source_latency_seconds: Decimal
    authority_latency_seconds: Decimal
    source_authority_score: Decimal
    resolution_confidence_score: Decimal
    authority_recheck_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceAuthorityLatencyFloorObservation:
            raise TypeError(
                "ResearchEventResolutionSourceAuthorityLatencyFloorObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSourceAuthorityLatencyFloorObservation,
            "observation",
        )
        _require_private_string("private_resolution_ref", self.private_resolution_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_latency_seconds",
            "authority_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_authority_score",
            "resolution_confidence_score",
            "authority_recheck_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


ResearchEventResolutionSourceAuthorityLatencyFloorInput = (
    ResearchEventResolutionSourceAuthorityLatencyFloorObservation
)


@dataclass(frozen=True)
class ResearchEventResolutionSourceAuthorityLatencyFloorRow:
    row_index: Decimal
    observed_age_seconds: Decimal
    source_latency_seconds: Decimal
    authority_latency_seconds: Decimal
    latency_gap_seconds: Decimal
    source_authority_score: Decimal
    resolution_confidence_score: Decimal
    authority_recheck_score: Decimal
    source_authority_latency_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceAuthorityLatencyFloorRow:
            raise TypeError(
                "ResearchEventResolutionSourceAuthorityLatencyFloorRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionSourceAuthorityLatencyFloorRow, "row")
        object.__setattr__(
            self,
            "row_index",
            _require_positive_whole_decimal("row_index", self.row_index),
        )
        for field_name in (
            "observed_age_seconds",
            "source_latency_seconds",
            "authority_latency_seconds",
            "latency_gap_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_authority_score",
            "resolution_confidence_score",
            "authority_recheck_score",
            "source_authority_latency_floor_score",
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
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceAuthorityLatencyFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceAuthorityLatencyFloorReasonCodeCount:
            raise TypeError(
                "ResearchEventResolutionSourceAuthorityLatencyFloorReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSourceAuthorityLatencyFloorReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_nonnegative_whole_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceAuthorityLatencyFloorReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_source_latency_seconds: Decimal
    average_authority_latency_seconds: Decimal
    highest_latency_gap_seconds: Decimal
    average_source_authority_latency_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchEventResolutionSourceAuthorityLatencyFloorReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchEventResolutionSourceAuthorityLatencyFloorRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceAuthorityLatencyFloorReport:
            raise TypeError(
                "ResearchEventResolutionSourceAuthorityLatencyFloorReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionSourceAuthorityLatencyFloorReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_AUTHORITY_LATENCY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "observation_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_latency_seconds",
            "average_authority_latency_seconds",
            "highest_latency_gap_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_source_authority_latency_floor_score",
            _require_ratio_decimal(
                "average_source_authority_latency_floor_score",
                self.average_source_authority_latency_floor_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_resolution_source_authority_latency_floor_report_payload(self)


def build_research_event_resolution_source_authority_latency_floor_report(
    observations: Iterable[ResearchEventResolutionSourceAuthorityLatencyFloorObservation],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionSourceAuthorityLatencyFloorConfig | None = None,
) -> ResearchEventResolutionSourceAuthorityLatencyFloorReport:
    if config is None:
        config = ResearchEventResolutionSourceAuthorityLatencyFloorConfig()
    if type(config) is not ResearchEventResolutionSourceAuthorityLatencyFloorConfig:
        raise ValueError(
            "config must be exactly ResearchEventResolutionSourceAuthorityLatencyFloorConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        _row_from_observation(
            observation,
            row_index=index,
            config=config,
            generated_at=generated_at,
        )
        for index, observation in enumerate(normalized_observations, start=1)
    )
    pass_count = _count(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count(sum(1 for row in rows if row.status == "watch"))
    block_count = _count(sum(1 for row in rows if row.status == "block"))
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)
    return ResearchEventResolutionSourceAuthorityLatencyFloorReport(
        generated_at=generated_at,
        config_version=config.config_version,
        observation_count=_count(len(normalized_observations)),
        row_count=_count(len(rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_source_latency_seconds=_average(row.source_latency_seconds for row in rows),
        average_authority_latency_seconds=_average(
            row.authority_latency_seconds for row in rows
        ),
        highest_latency_gap_seconds=max(
            (row.latency_gap_seconds for row in rows),
            default=ZERO,
        ),
        average_source_authority_latency_floor_score=_average(
            row.source_authority_latency_floor_score for row in rows
        ),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_event_resolution_source_authority_latency_floor_report_payload(
    report: ResearchEventResolutionSourceAuthorityLatencyFloorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionSourceAuthorityLatencyFloorReport:
        raise ValueError(
            "report must be exactly ResearchEventResolutionSourceAuthorityLatencyFloorReport",
        )
    _validate_report_consistency(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def research_event_resolution_source_authority_latency_floor_report_digest(
    report: ResearchEventResolutionSourceAuthorityLatencyFloorReport,
) -> str:
    payload = research_event_resolution_source_authority_latency_floor_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_event_resolution_source_authority_latency_floor_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        return False
    try:
        _validate_public_payload(payload)
        digest = payload.get("derived_validation_digest")
        if type(digest) is not str or not DIGEST_RE.fullmatch(digest):
            return False
        unsigned = dict(payload)
        unsigned.pop("derived_validation_digest")
        encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        return sha256(encoded).hexdigest() == digest
    except (TypeError, ValueError):
        return False


def _normalize_observations(
    observations: Iterable[ResearchEventResolutionSourceAuthorityLatencyFloorObservation],
) -> tuple[ResearchEventResolutionSourceAuthorityLatencyFloorObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for observation in normalized:
        if type(observation) is not ResearchEventResolutionSourceAuthorityLatencyFloorObservation:
            raise ValueError(
                "observations must contain "
                "ResearchEventResolutionSourceAuthorityLatencyFloorObservation",
            )
        _require_hard_flags("observation", observation)
    return tuple(sorted(normalized, key=_observation_sort_key))


def _observation_sort_key(
    observation: ResearchEventResolutionSourceAuthorityLatencyFloorObservation,
) -> tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        observation.observed_at.isoformat(),
        observation.source_latency_seconds,
        observation.authority_latency_seconds,
        observation.source_authority_score,
        observation.resolution_confidence_score,
        observation.authority_recheck_score,
    )


def _row_from_observation(
    observation: ResearchEventResolutionSourceAuthorityLatencyFloorObservation,
    *,
    row_index: int,
    config: ResearchEventResolutionSourceAuthorityLatencyFloorConfig,
    generated_at: datetime,
) -> ResearchEventResolutionSourceAuthorityLatencyFloorRow:
    observed_age_seconds = _duration_seconds(observation.observed_at, generated_at)
    latency_gap_seconds = abs(
        observation.authority_latency_seconds - observation.source_latency_seconds
    )
    floor_score = _source_authority_latency_floor_score(observation)
    reason_codes = _row_reason_codes(
        floor_score=floor_score,
        source_latency_seconds=observation.source_latency_seconds,
        authority_latency_seconds=observation.authority_latency_seconds,
        latency_gap_seconds=latency_gap_seconds,
        config=config,
    )
    status = _row_status(reason_codes)
    if status == "pass":
        reason_codes = (PASS_REASON,)
    return ResearchEventResolutionSourceAuthorityLatencyFloorRow(
        row_index=_count(row_index),
        observed_age_seconds=observed_age_seconds,
        source_latency_seconds=observation.source_latency_seconds,
        authority_latency_seconds=observation.authority_latency_seconds,
        latency_gap_seconds=latency_gap_seconds,
        source_authority_score=observation.source_authority_score,
        resolution_confidence_score=observation.resolution_confidence_score,
        authority_recheck_score=observation.authority_recheck_score,
        source_authority_latency_floor_score=floor_score,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _source_authority_latency_floor_score(
    observation: ResearchEventResolutionSourceAuthorityLatencyFloorObservation,
) -> Decimal:
    base_score = _average(
        (
            observation.source_authority_score,
            observation.resolution_confidence_score,
            observation.authority_recheck_score,
        )
    )
    stability_bonus = _quantize((ONE - base_score) * FLOOR_SCORE_STABILITY_BONUS)
    return min(ONE, _quantize(base_score + stability_bonus))


def _row_reason_codes(
    *,
    floor_score: Decimal,
    source_latency_seconds: Decimal,
    authority_latency_seconds: Decimal,
    latency_gap_seconds: Decimal,
    config: ResearchEventResolutionSourceAuthorityLatencyFloorConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if floor_score < config.source_authority_latency_floor_watch_score:
        reasons.append(FLOOR_BELOW_WATCH_REASON)
    elif floor_score < config.source_authority_latency_floor_pass_score:
        reasons.append(FLOOR_BELOW_PASS_REASON)
    if source_latency_seconds > config.source_latency_watch_threshold_seconds:
        reasons.append(SOURCE_ABOVE_WATCH_REASON)
    elif source_latency_seconds > config.source_latency_pass_threshold_seconds:
        reasons.append(SOURCE_ABOVE_PASS_REASON)
    if authority_latency_seconds > config.authority_latency_watch_threshold_seconds:
        reasons.append(AUTHORITY_ABOVE_WATCH_REASON)
    elif authority_latency_seconds > config.authority_latency_pass_threshold_seconds:
        reasons.append(AUTHORITY_ABOVE_PASS_REASON)
    if latency_gap_seconds > config.latency_gap_watch_threshold_seconds:
        reasons.append(GAP_ABOVE_WATCH_REASON)
    return _sequence_reason_codes(reasons, allow_empty=True)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_watch_threshold") for reason_code in reason_codes):
        return "block"
    if reason_codes:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchEventResolutionSourceAuthorityLatencyFloorRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionSourceAuthorityLatencyFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    return _normalize_reason_codes(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionSourceAuthorityLatencyFloorRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchEventResolutionSourceAuthorityLatencyFloorReasonCodeCount, ...]:
    if rows:
        counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    else:
        counts = Counter(report_reason_codes)
    return tuple(
        ResearchEventResolutionSourceAuthorityLatencyFloorReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            paper_only=True,
            report_only=True,
            readonly=True,
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: Iterable[ResearchEventResolutionSourceAuthorityLatencyFloorRow],
) -> tuple[ResearchEventResolutionSourceAuthorityLatencyFloorRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchEventResolutionSourceAuthorityLatencyFloorRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionSourceAuthorityLatencyFloorRow",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(row: ResearchEventResolutionSourceAuthorityLatencyFloorRow) -> tuple[int, Decimal]:
    return (STATUS_WEIGHT[row.status], row.row_index)


def _normalize_reason_code_counts(
    counts: Iterable[ResearchEventResolutionSourceAuthorityLatencyFloorReasonCodeCount],
) -> tuple[ResearchEventResolutionSourceAuthorityLatencyFloorReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        if type(count) is not ResearchEventResolutionSourceAuthorityLatencyFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventResolutionSourceAuthorityLatencyFloorReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    return tuple(
        sorted(
            normalized,
            key=lambda count: REASON_CODE_SEQUENCE.index(count.reason_code),
        )
    )


def _validate_report_consistency(
    report: ResearchEventResolutionSourceAuthorityLatencyFloorReport,
) -> None:
    if report.observation_count != report.row_count:
        raise ValueError("observation_count must match row_count")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    expected_averages = {
        "average_source_latency_seconds": _average(
            row.source_latency_seconds for row in report.rows
        ),
        "average_authority_latency_seconds": _average(
            row.authority_latency_seconds for row in report.rows
        ),
        "average_source_authority_latency_floor_score": _average(
            row.source_authority_latency_floor_score for row in report.rows
        ),
    }
    for field_name, expected_value in expected_averages.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    highest_gap = max((row.latency_gap_seconds for row in report.rows), default=ZERO)
    if report.highest_latency_gap_seconds != highest_gap:
        raise ValueError("highest_latency_gap_seconds must match rows")


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("duration start must be at or before end")
    delta = end - start
    total_microseconds = (
        Decimal(delta.days * 86400 + delta.seconds) * MICROSECOND_DIVISOR
        + Decimal(delta.microseconds)
    )
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(total_microseconds / MICROSECOND_DIVISOR)


def _average(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(normalized, ZERO) / _count(len(normalized)))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _contains_unsafe_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public surface")


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_EVENT_RESOLUTION_SOURCE_AUTHORITY_LATENCY_FLOOR_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    return _sequence_reason_codes(value, allow_empty=False)


def _sequence_reason_codes(
    value: Iterable[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not reason_codes and allow_empty:
        return ()
    if not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    return tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in reason_codes
    )


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError(f"unsupported public payload value {type(value).__name__}")


def _report_digest(report: ResearchEventResolutionSourceAuthorityLatencyFloorReport) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _validate_public_payload(value: object) -> None:
    _reject_unsafe_public_payload(value)
    _reject_raw_public_numbers(value)
    _require_public_payload_contract(value)


def _require_public_payload_contract(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("public payload must be a dict")
    _require_public_payload_flags("payload", value)
    if value.get("config_version") != (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_AUTHORITY_LATENCY_FLOOR_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    _require_status("status", value.get("status"))
    _require_public_reason_codes("reason_codes", value.get("reason_codes"))
    _require_public_rows(value.get("rows"))
    _require_public_reason_code_counts(value.get("reason_code_counts"))
    _require_nested_public_contract(value)


def _require_public_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    for row in value:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        _require_public_payload_flags("row", row)
        _require_status("row status", row.get("status"))
        _require_public_reason_codes("row reason_codes", row.get("reason_codes"))


def _require_public_reason_code_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list")
    for count in value:
        if type(count) is not dict:
            raise ValueError("reason_code_counts must contain objects")
        _require_public_payload_flags("reason_code_count", count)
        _require_reason_code("reason_code", count.get("reason_code"))


def _require_public_reason_codes(field_name: str, value: object) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized = _sequence_reason_codes(value, allow_empty=False)
    if list(normalized) != value:
        raise ValueError(f"{field_name} must use deterministic reason order")


def _require_public_payload_flags(label: str, value: dict[str, Any]) -> None:
    for field_name in HARD_FLAG_FIELD_NAMES:
        if value.get(field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_nested_public_contract(value: object) -> None:
    if type(value) is dict:
        if any(field_name in value for field_name in HARD_FLAG_FIELD_NAMES):
            _require_public_payload_flags("payload object", value)
        if "status" in value:
            _require_status("status", value["status"])
        for item in value.values():
            _require_nested_public_contract(item)
        return
    if type(value) is list:
        for item in value:
            _require_nested_public_contract(item)


def _reject_raw_public_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be strings")
    if type(value) is dict:
        for item in value.values():
            _reject_raw_public_numbers(item)
        return
    if type(value) is list:
        for item in value:
            _reject_raw_public_numbers(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if _contains_unsafe_fragment(field.name):
                raise ValueError("unsafe public payload field")
            _reject_unsafe_public_payload(getattr(value, field.name))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload field must be a string")
            if _contains_unsafe_fragment(key):
                raise ValueError("unsafe public payload field")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, tuple | list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _contains_unsafe_fragment(value):
        raise ValueError("unsafe public payload value")


def _contains_unsafe_fragment(value: str) -> bool:
    normalized = "".join(character for character in value.casefold() if character.isalnum())
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_KEYS)
