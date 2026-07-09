"""Pure report-only resolution-claim latency decay floor report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_RESOLUTION_CLAIM_LATENCY_DECAY_FLOOR_REPORT_CONFIG_VERSION = (
    "research-source-resolution-claim-latency-decay-floor-report-v0"
)
RESEARCH_SOURCE_RESOLUTION_CLAIM_LATENCY_DECAY_FLOOR_STATUSES = (
    "pass",
    "watch",
    "block",
)

EMPTY_REASON = "resolution_claim_latency_decay_floor_empty"
PASS_REASON = "resolution_claim_latency_decay_floor_pass"
LATENCY_BLOCK_REASON = "resolution_claim_latency_block"
DECAY_BLOCK_REASON = "resolution_claim_decay_block"
FLOOR_BLOCK_REASON = "resolution_claim_floor_block"
LATENCY_WATCH_REASON = "resolution_claim_latency_watch"
DECAY_WATCH_REASON = "resolution_claim_decay_watch"
FLOOR_WATCH_REASON = "resolution_claim_floor_watch"

ROW_REASON_CODES = (
    LATENCY_BLOCK_REASON,
    DECAY_BLOCK_REASON,
    FLOOR_BLOCK_REASON,
    LATENCY_WATCH_REASON,
    DECAY_WATCH_REASON,
    FLOOR_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")

UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "slug",
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


@dataclass(frozen=True)
class ResearchSourceResolutionClaimLatencyDecayFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_RESOLUTION_CLAIM_LATENCY_DECAY_FLOOR_REPORT_CONFIG_VERSION
    )
    latency_watch_seconds: Decimal = Decimal("1800.000000")
    latency_block_seconds: Decimal = Decimal("7200.000000")
    decay_watch_age_seconds: Decimal = Decimal("3600.000000")
    decay_block_age_seconds: Decimal = Decimal("14400.000000")
    floor_pass_score: Decimal = Decimal("0.800000")
    floor_block_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionClaimLatencyDecayFloorConfig:
            raise TypeError(
                "ResearchSourceResolutionClaimLatencyDecayFloorConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceResolutionClaimLatencyDecayFloorConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_CLAIM_LATENCY_DECAY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "latency_watch_seconds",
            "latency_block_seconds",
            "decay_watch_age_seconds",
            "decay_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("floor_pass_score", "floor_block_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.latency_watch_seconds >= self.latency_block_seconds:
            raise ValueError("latency_watch_seconds must be below latency_block_seconds")
        if self.decay_watch_age_seconds >= self.decay_block_age_seconds:
            raise ValueError("decay_watch_age_seconds must be below decay_block_age_seconds")
        if self.floor_block_score >= self.floor_pass_score:
            raise ValueError("floor_block_score must be below floor_pass_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceResolutionClaimLatencyDecayFloorObservation:
    private_trace_ref: str
    observed_at: datetime
    resolution_family: str
    claim_bucket: str
    authority_confidence_score: Decimal
    claim_confidence_score: Decimal
    resolution_claim_latency_seconds: Decimal
    resolution_claim_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionClaimLatencyDecayFloorObservation:
            raise TypeError(
                "ResearchSourceResolutionClaimLatencyDecayFloorObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceResolutionClaimLatencyDecayFloorObservation,
            "observation",
        )
        _require_private_trace_ref("private_trace_ref", self.private_trace_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolution_family",
            _require_public_label("resolution_family", self.resolution_family),
        )
        object.__setattr__(
            self,
            "claim_bucket",
            _require_public_label("claim_bucket", self.claim_bucket),
        )
        for field_name in ("authority_confidence_score", "claim_confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_claim_latency_seconds",
            "resolution_claim_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceResolutionClaimLatencyDecayFloorRow:
    row_index: Decimal
    resolution_family: str
    claim_bucket: str
    authority_confidence_score: Decimal
    claim_confidence_score: Decimal
    resolution_claim_latency_seconds: Decimal
    resolution_claim_age_seconds: Decimal
    latency_health_score: Decimal
    decay_freshness_score: Decimal
    resolution_claim_latency_decay_floor_score: Decimal
    latency_status: str
    decay_status: str
    floor_status: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionClaimLatencyDecayFloorRow:
            raise TypeError(
                "ResearchSourceResolutionClaimLatencyDecayFloorRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceResolutionClaimLatencyDecayFloorRow, "row")
        object.__setattr__(
            self,
            "row_index",
            _require_positive_whole_decimal("row_index", self.row_index),
        )
        object.__setattr__(
            self,
            "resolution_family",
            _require_public_label("resolution_family", self.resolution_family),
        )
        object.__setattr__(
            self,
            "claim_bucket",
            _require_public_label("claim_bucket", self.claim_bucket),
        )
        for field_name in ("authority_confidence_score", "claim_confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_claim_latency_seconds",
            "resolution_claim_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latency_health_score",
            "decay_freshness_score",
            "resolution_claim_latency_decay_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("latency_status", "decay_status", "floor_status", "status"):
            object.__setattr__(
                self,
                field_name,
                _require_status(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceResolutionClaimLatencyDecayFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionClaimLatencyDecayFloorReasonCodeCount:
            raise TypeError(
                "ResearchSourceResolutionClaimLatencyDecayFloorReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceResolutionClaimLatencyDecayFloorReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_choice("reason_code", self.reason_code, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceResolutionClaimLatencyDecayFloorReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    latency_pressure_count: Decimal
    decay_pressure_count: Decimal
    floor_pressure_count: Decimal
    average_resolution_claim_latency_decay_floor_score: Decimal
    lowest_resolution_claim_latency_decay_floor_score: Decimal
    highest_resolution_claim_latency_seconds: Decimal
    highest_resolution_claim_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourceResolutionClaimLatencyDecayFloorReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchSourceResolutionClaimLatencyDecayFloorRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionClaimLatencyDecayFloorReport:
            raise TypeError(
                "ResearchSourceResolutionClaimLatencyDecayFloorReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceResolutionClaimLatencyDecayFloorReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_CLAIM_LATENCY_DECAY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "latency_pressure_count",
            "decay_pressure_count",
            "floor_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_resolution_claim_latency_decay_floor_score",
            "lowest_resolution_claim_latency_decay_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_resolution_claim_latency_seconds",
            "highest_resolution_claim_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_public_payload(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_resolution_claim_latency_decay_floor_report_payload(self)


def build_research_source_resolution_claim_latency_decay_floor_report(
    observations: object,
    *,
    generated_at: datetime,
    config: ResearchSourceResolutionClaimLatencyDecayFloorConfig | None = None,
) -> ResearchSourceResolutionClaimLatencyDecayFloorReport:
    if config is None:
        config = ResearchSourceResolutionClaimLatencyDecayFloorConfig()
    if type(config) is not ResearchSourceResolutionClaimLatencyDecayFloorConfig:
        raise ValueError(
            "config must be a ResearchSourceResolutionClaimLatencyDecayFloorConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    row_values = tuple(
        _row_values_from_observation(observation, config=config)
        for observation in normalized_observations
    )
    sorted_values = tuple(sorted(row_values, key=_row_values_sort_key))
    rows = tuple(
        ResearchSourceResolutionClaimLatencyDecayFloorRow(
            row_index=_count(index),
            **values,
        )
        for index, values in enumerate(sorted_values, start=1)
    )
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)
    return ResearchSourceResolutionClaimLatencyDecayFloorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(normalized_observations)),
        row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        latency_pressure_count=_status_field_pressure_count(rows, "latency_status"),
        decay_pressure_count=_status_field_pressure_count(rows, "decay_status"),
        floor_pressure_count=_status_field_pressure_count(rows, "floor_status"),
        average_resolution_claim_latency_decay_floor_score=_average(
            row.resolution_claim_latency_decay_floor_score for row in rows
        ),
        lowest_resolution_claim_latency_decay_floor_score=min(
            (row.resolution_claim_latency_decay_floor_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_resolution_claim_latency_seconds=max(
            (row.resolution_claim_latency_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_resolution_claim_age_seconds=max(
            (row.resolution_claim_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_resolution_claim_latency_decay_floor_report_payload(
    report: ResearchSourceResolutionClaimLatencyDecayFloorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceResolutionClaimLatencyDecayFloorReport:
        raise ValueError(
            "report must be a ResearchSourceResolutionClaimLatencyDecayFloorReport",
        )
    _validate_report(report)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match report payload")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload_or_raise(payload)
    return payload


def research_source_resolution_claim_latency_decay_floor_report_digest(
    report: ResearchSourceResolutionClaimLatencyDecayFloorReport,
) -> str:
    payload = research_source_resolution_claim_latency_decay_floor_report_payload(report)
    digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest)
    return digest


def validate_research_source_resolution_claim_latency_decay_floor_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        return False
    try:
        _validate_public_payload_or_raise(payload)
        return True
    except (TypeError, ValueError):
        return False


def _normalize_observations(
    value: object,
) -> tuple[ResearchSourceResolutionClaimLatencyDecayFloorObservation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(value)
    seen: set[tuple[str, str]] = set()
    for observation in normalized:
        if type(observation) is not ResearchSourceResolutionClaimLatencyDecayFloorObservation:
            raise ValueError(
                "observations must contain "
                "ResearchSourceResolutionClaimLatencyDecayFloorObservation",
            )
        _require_hard_flags("observation", observation)
        key = (observation.resolution_family, observation.claim_bucket)
        if key in seen:
            raise ValueError("observations must be unique by resolution_family and claim_bucket")
        seen.add(key)
    return tuple(sorted(normalized, key=_observation_sort_key))


def _observation_sort_key(
    observation: ResearchSourceResolutionClaimLatencyDecayFloorObservation,
) -> tuple[str, str, Decimal, Decimal, Decimal, Decimal]:
    return (
        observation.resolution_family,
        observation.claim_bucket,
        observation.authority_confidence_score,
        observation.claim_confidence_score,
        observation.resolution_claim_latency_seconds,
        observation.resolution_claim_age_seconds,
    )


def _row_values_from_observation(
    observation: ResearchSourceResolutionClaimLatencyDecayFloorObservation,
    *,
    config: ResearchSourceResolutionClaimLatencyDecayFloorConfig,
) -> dict[str, object]:
    latency_health_score = _decay_health_score(
        observation.resolution_claim_latency_seconds,
        config.latency_block_seconds,
    )
    decay_freshness_score = _decay_health_score(
        observation.resolution_claim_age_seconds,
        config.decay_block_age_seconds,
    )
    floor_score = min(
        observation.authority_confidence_score,
        observation.claim_confidence_score,
        latency_health_score,
        decay_freshness_score,
    ).quantize(QUANT)
    latency_status = _ceiling_status(
        observation.resolution_claim_latency_seconds,
        watch_threshold=config.latency_watch_seconds,
        block_threshold=config.latency_block_seconds,
    )
    decay_status = _ceiling_status(
        observation.resolution_claim_age_seconds,
        watch_threshold=config.decay_watch_age_seconds,
        block_threshold=config.decay_block_age_seconds,
    )
    floor_status = _floor_status(
        floor_score,
        pass_floor=config.floor_pass_score,
        block_floor=config.floor_block_score,
    )
    reason_codes = _row_reason_codes(
        latency_status=latency_status,
        decay_status=decay_status,
        floor_status=floor_status,
    )
    return {
        "resolution_family": observation.resolution_family,
        "claim_bucket": observation.claim_bucket,
        "authority_confidence_score": observation.authority_confidence_score,
        "claim_confidence_score": observation.claim_confidence_score,
        "resolution_claim_latency_seconds": observation.resolution_claim_latency_seconds,
        "resolution_claim_age_seconds": observation.resolution_claim_age_seconds,
        "latency_health_score": latency_health_score,
        "decay_freshness_score": decay_freshness_score,
        "resolution_claim_latency_decay_floor_score": floor_score,
        "latency_status": latency_status,
        "decay_status": decay_status,
        "floor_status": floor_status,
        "status": _row_status(reason_codes),
        "reason_codes": reason_codes,
    }


def _row_values_sort_key(value: dict[str, object]) -> tuple[Decimal, Decimal, str, str]:
    status = value["status"]
    floor_score = value["resolution_claim_latency_decay_floor_score"]
    resolution_family = value["resolution_family"]
    claim_bucket = value["claim_bucket"]
    if type(status) is not str:
        raise ValueError("status must be a string")
    if type(floor_score) is not Decimal:
        raise ValueError("floor score must be a Decimal")
    if type(resolution_family) is not str or type(claim_bucket) is not str:
        raise ValueError("public row labels must be strings")
    return (_status_rank(status), floor_score, resolution_family, claim_bucket)


def _row_reason_codes(
    *,
    latency_status: str,
    decay_status: str,
    floor_status: str,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if latency_status == "block":
        reasons.append(LATENCY_BLOCK_REASON)
    elif latency_status == "watch":
        reasons.append(LATENCY_WATCH_REASON)
    if decay_status == "block":
        reasons.append(DECAY_BLOCK_REASON)
    elif decay_status == "watch":
        reasons.append(DECAY_WATCH_REASON)
    if floor_status == "block":
        reasons.append(FLOOR_BLOCK_REASON)
    elif floor_status == "watch":
        reasons.append(FLOOR_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _decay_health_score(value: Decimal, block_threshold: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        decay_ratio = min(value / block_threshold, ONE)
        return (ONE - decay_ratio).quantize(QUANT)


def _ceiling_status(
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value >= block_threshold:
        return "block"
    if value > watch_threshold:
        return "watch"
    return "pass"


def _floor_status(
    value: Decimal,
    *,
    pass_floor: Decimal,
    block_floor: Decimal,
) -> str:
    if value <= block_floor:
        return "block"
    if value < pass_floor:
        return "watch"
    return "pass"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason in reason_codes for reason in _block_reasons()):
        return "block"
    if any(reason in reason_codes for reason in _watch_reasons()):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceResolutionClaimLatencyDecayFloorRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceResolutionClaimLatencyDecayFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    if all(row.status == "pass" for row in rows):
        return (PASS_REASON,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code != PASS_REASON
        ),
        REPORT_REASON_CODES,
    )


def _row_sort_key(
    row: ResearchSourceResolutionClaimLatencyDecayFloorRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        _status_rank(row.status),
        row.resolution_claim_latency_decay_floor_score,
        row.resolution_family,
        row.claim_bucket,
    )


def _status_rank(status: str) -> Decimal:
    if status == "block":
        return Decimal("0.000000")
    if status == "watch":
        return Decimal("1.000000")
    if status == "pass":
        return Decimal("2.000000")
    raise ValueError("status must be pass, watch, or block")


def _block_reasons() -> tuple[str, ...]:
    return (LATENCY_BLOCK_REASON, DECAY_BLOCK_REASON, FLOOR_BLOCK_REASON)


def _watch_reasons() -> tuple[str, ...]:
    return (LATENCY_WATCH_REASON, DECAY_WATCH_REASON, FLOOR_WATCH_REASON)


def _status_count(
    rows: tuple[ResearchSourceResolutionClaimLatencyDecayFloorRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _status_field_pressure_count(
    rows: tuple[ResearchSourceResolutionClaimLatencyDecayFloorRow, ...],
    field_name: str,
) -> Decimal:
    return _count(sum(1 for row in rows if getattr(row, field_name) != "pass"))


def _average(values: object) -> Decimal:
    if type(values) not in (list, tuple):
        values = tuple(values)  # type: ignore[arg-type]
    decimal_values = tuple(values)
    if not decimal_values:
        return ZERO
    for value in decimal_values:
        if type(value) is not Decimal:
            raise ValueError("average values must be Decimals")
    with localcontext(DECIMAL_CONTEXT):
        return (sum(decimal_values, ZERO) / Decimal(len(decimal_values))).quantize(QUANT)


def _reason_code_counts(
    rows: tuple[ResearchSourceResolutionClaimLatencyDecayFloorRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceResolutionClaimLatencyDecayFloorReasonCodeCount, ...]:
    if reason_codes == (EMPTY_REASON,):
        return (
            ResearchSourceResolutionClaimLatencyDecayFloorReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=Decimal("1.000000"),
            ),
        )
    return tuple(
        ResearchSourceResolutionClaimLatencyDecayFloorReasonCodeCount(
            reason_code=reason_code,
            count=_count(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
        )
        for reason_code in reason_codes
    )


def _validate_row(row: ResearchSourceResolutionClaimLatencyDecayFloorRow) -> None:
    expected_floor_score = min(
        row.authority_confidence_score,
        row.claim_confidence_score,
        row.latency_health_score,
        row.decay_freshness_score,
    ).quantize(QUANT)
    if row.resolution_claim_latency_decay_floor_score != expected_floor_score:
        raise ValueError(
            "resolution_claim_latency_decay_floor_score must match component floor",
        )
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows require pass reason")
    if row.status != "pass" and row.reason_codes == (PASS_REASON,):
        raise ValueError("non-pass rows require active reason codes")


def _validate_report(report: ResearchSourceResolutionClaimLatencyDecayFloorReport) -> None:
    if report.rows != _normalize_rows(report.rows):
        raise ValueError("rows must be normalized")
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if tuple(row.row_index for row in report.rows) != tuple(
        _count(index) for index in range(1, len(report.rows) + 1)
    ):
        raise ValueError("row_index must match row order")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.latency_pressure_count != _status_field_pressure_count(
        report.rows,
        "latency_status",
    ):
        raise ValueError("latency_pressure_count must match rows")
    if report.decay_pressure_count != _status_field_pressure_count(
        report.rows,
        "decay_status",
    ):
        raise ValueError("decay_pressure_count must match rows")
    if report.floor_pressure_count != _status_field_pressure_count(
        report.rows,
        "floor_status",
    ):
        raise ValueError("floor_pressure_count must match rows")
    if report.average_resolution_claim_latency_decay_floor_score != _average(
        row.resolution_claim_latency_decay_floor_score for row in report.rows
    ):
        raise ValueError("average floor score must match rows")
    if report.lowest_resolution_claim_latency_decay_floor_score != min(
        (row.resolution_claim_latency_decay_floor_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest floor score must match rows")
    if report.highest_resolution_claim_latency_seconds != max(
        (row.resolution_claim_latency_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest latency seconds must match rows")
    if report.highest_resolution_claim_age_seconds != max(
        (row.resolution_claim_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest age seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourceResolutionClaimLatencyDecayFloorRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchSourceResolutionClaimLatencyDecayFloorRow:
            raise ValueError(
                "rows must contain ResearchSourceResolutionClaimLatencyDecayFloorRow",
            )
        _require_hard_flags("row", row)
        key = (row.resolution_family, row.claim_bucket)
        if key in seen:
            raise ValueError("rows must be unique by resolution_family and claim_bucket")
        seen.add(key)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourceResolutionClaimLatencyDecayFloorReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(value)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchSourceResolutionClaimLatencyDecayFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceResolutionClaimLatencyDecayFloorReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique by reason_code")
        seen.add(item.reason_code)
    return tuple(
        sorted(
            normalized,
            key=lambda item: REPORT_REASON_CODES.index(item.reason_code),
        )
    )


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    items = tuple(value)
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    for item in items:
        _require_choice(field_name, item, allowed)
    return tuple(reason for reason in allowed if reason in items)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or len(value) > 96:
        raise ValueError(f"{field_name} must be a non-empty public string")
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")
    return value


def _require_private_trace_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or len(value) > 2048:
        raise ValueError(f"{field_name} must be a non-empty private string")
    return value


def _require_public_label(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    if PUBLIC_LABEL_RE.fullmatch(text) is None:
        raise ValueError(f"{field_name} must be a public label")
    return text


def _require_choice(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_status(field_name: str, value: object) -> str:
    return _require_choice(
        field_name,
        value,
        RESEARCH_SOURCE_RESOLUTION_CLAIM_LATENCY_DECAY_FLOOR_STATUSES,
    )


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value.quantize(QUANT)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value.quantize(QUANT)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value.quantize(QUANT)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value.quantize(QUANT)


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest") from exc
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _json_ready(value: object) -> object:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value.quantize(QUANT), "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _report_digest_from_public_payload(
    report: ResearchSourceResolutionClaimLatencyDecayFloorReport,
) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_public_payload_or_raise(payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numerics("public payload", payload)
    _reject_flag_downgrades("public payload", payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    _validate_status_values_in_payload(payload)
    digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _payload_validation_digest(unsigned_payload):
        raise ValueError("derived_validation_digest must match public payload")


@dataclass(frozen=True)
class _PayloadFlags:
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


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            if any(fragment in key_lower for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"{label} has unsafe public field")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} has unsafe public value")


def _reject_public_numerics(label: str, value: object) -> None:
    if type(value) is dict:
        for item in value.values():
            _reject_public_numerics(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numerics(label, item)
        return
    if type(value) in (Decimal, int, float):
        raise ValueError(f"{label} must not contain raw numeric values")


def _reject_flag_downgrades(label: str, value: object) -> None:
    if type(value) is dict:
        for flag in ("paper_only", "report_only", "readonly"):
            if flag in value and value[flag] is not True:
                raise ValueError(f"{label} must be {flag}")
        for item in value.values():
            _reject_flag_downgrades(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_flag_downgrades(label, item)


def _validate_status_values_in_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if key.endswith("status") and item not in (
                RESEARCH_SOURCE_RESOLUTION_CLAIM_LATENCY_DECAY_FLOOR_STATUSES
            ):
                raise ValueError("status must be pass, watch, or block")
            _validate_status_values_in_payload(item)
        return
    if type(value) is list:
        for item in value:
            _validate_status_values_in_payload(item)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_RESOLUTION_CLAIM_LATENCY_DECAY_FLOOR_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_RESOLUTION_CLAIM_LATENCY_DECAY_FLOOR_STATUSES",
    "ResearchSourceResolutionClaimLatencyDecayFloorConfig",
    "ResearchSourceResolutionClaimLatencyDecayFloorObservation",
    "ResearchSourceResolutionClaimLatencyDecayFloorReasonCodeCount",
    "ResearchSourceResolutionClaimLatencyDecayFloorReport",
    "ResearchSourceResolutionClaimLatencyDecayFloorRow",
    "build_research_source_resolution_claim_latency_decay_floor_report",
    "research_source_resolution_claim_latency_decay_floor_report_digest",
    "research_source_resolution_claim_latency_decay_floor_report_payload",
    "validate_research_source_resolution_claim_latency_decay_floor_report_payload",
)
