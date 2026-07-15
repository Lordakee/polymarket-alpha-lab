"""Report-only domain reducer for sanitized memory signal reuse value."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import InitVar, asdict, dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, final


DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SIGNAL_REUSE_VALUE_CONFIG_VERSION = (
    "research-team-domain-memory-signal-reuse-value-report-v0"
)

PUBLIC_STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "memory_signal_reuse_value_empty"
PASS_REASON = "memory_signal_reuse_value_pass"
REPORT_PASS_REASON = "memory_signal_reuse_value_report_pass"
REPORT_WATCH_REASON = "memory_signal_reuse_value_report_watch"
REPORT_BLOCK_REASON = "memory_signal_reuse_value_report_block"

HISTORICAL_CALIBRATION_GAIN_WATCH_REASON = "historical_calibration_gain_watch"
HISTORICAL_CALIBRATION_GAIN_BLOCK_REASON = "historical_calibration_gain_block"
EVIDENCE_REUSE_QUALITY_WATCH_REASON = "evidence_reuse_quality_watch"
EVIDENCE_REUSE_QUALITY_BLOCK_REASON = "evidence_reuse_quality_block"
PRIOR_ERROR_AVOIDANCE_WATCH_REASON = "prior_error_avoidance_watch"
PRIOR_ERROR_AVOIDANCE_BLOCK_REASON = "prior_error_avoidance_block"
REVIEW_LATENCY_REDUCTION_WATCH_REASON = "review_latency_reduction_watch"
REVIEW_LATENCY_REDUCTION_BLOCK_REASON = "review_latency_reduction_block"
CURRENT_EVIDENCE_GAP_PRESSURE_WATCH_REASON = "current_evidence_gap_pressure_watch"
CURRENT_EVIDENCE_GAP_PRESSURE_BLOCK_REASON = "current_evidence_gap_pressure_block"
MEMORY_REUSE_VALUE_SCORE_WATCH_REASON = "memory_reuse_value_score_watch"
MEMORY_REUSE_VALUE_SCORE_BLOCK_REASON = "memory_reuse_value_score_block"

ROW_REASON_CODES = (
    HISTORICAL_CALIBRATION_GAIN_BLOCK_REASON,
    HISTORICAL_CALIBRATION_GAIN_WATCH_REASON,
    EVIDENCE_REUSE_QUALITY_BLOCK_REASON,
    EVIDENCE_REUSE_QUALITY_WATCH_REASON,
    PRIOR_ERROR_AVOIDANCE_BLOCK_REASON,
    PRIOR_ERROR_AVOIDANCE_WATCH_REASON,
    REVIEW_LATENCY_REDUCTION_BLOCK_REASON,
    REVIEW_LATENCY_REDUCTION_WATCH_REASON,
    CURRENT_EVIDENCE_GAP_PRESSURE_BLOCK_REASON,
    CURRENT_EVIDENCE_GAP_PRESSURE_WATCH_REASON,
    MEMORY_REUSE_VALUE_SCORE_BLOCK_REASON,
    MEMORY_REUSE_VALUE_SCORE_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_CODES = (
    EMPTY_REASON,
    REPORT_BLOCK_REASON,
    REPORT_WATCH_REASON,
    REPORT_PASS_REASON,
) + ROW_REASON_CODES
REASON_CODE_ORDER = REPORT_REASON_CODES
REASON_CODE_RANK = {
    reason_code: index for index, reason_code in enumerate(REASON_CODE_ORDER)
}
BLOCK_REASONS = (
    EMPTY_REASON,
    HISTORICAL_CALIBRATION_GAIN_BLOCK_REASON,
    EVIDENCE_REUSE_QUALITY_BLOCK_REASON,
    PRIOR_ERROR_AVOIDANCE_BLOCK_REASON,
    REVIEW_LATENCY_REDUCTION_BLOCK_REASON,
    CURRENT_EVIDENCE_GAP_PRESSURE_BLOCK_REASON,
    MEMORY_REUSE_VALUE_SCORE_BLOCK_REASON,
    REPORT_BLOCK_REASON,
)
WATCH_REASONS = (
    HISTORICAL_CALIBRATION_GAIN_WATCH_REASON,
    EVIDENCE_REUSE_QUALITY_WATCH_REASON,
    PRIOR_ERROR_AVOIDANCE_WATCH_REASON,
    REVIEW_LATENCY_REDUCTION_WATCH_REASON,
    CURRENT_EVIDENCE_GAP_PRESSURE_WATCH_REASON,
    MEMORY_REUSE_VALUE_SCORE_WATCH_REASON,
    REPORT_WATCH_REASON,
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=50, rounding=ROUND_HALF_UP)
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market_id",
    "market_slug",
    "market",
    "slug",
    "question",
    "source_url",
    "source_text",
    "source",
    "://",
    "dsn",
    "table",
    "token",
    "secret",
    "auth",
    "database",
    "network",
    "endpoint",
    "wallet",
    "order",
    "trade",
    "trading",
    "live",
    "execution",
    "sizing",
    "recommendation",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SIGNAL_REUSE_VALUE_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "ResearchTeamDomainMemorySignalReuseValueConfig",
    "ResearchTeamDomainMemorySignalReuseValueObservation",
    "ResearchTeamDomainMemorySignalReuseValueRow",
    "ResearchTeamDomainMemorySignalReuseValueReasonCodeCount",
    "ResearchTeamDomainMemorySignalReuseValueReport",
    "build_research_team_domain_memory_signal_reuse_value_report",
    "research_team_domain_memory_signal_reuse_value_public_payload",
    "research_team_domain_memory_signal_reuse_value_report_digest",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@final
@dataclass(frozen=True)
class ResearchTeamDomainMemorySignalReuseValueConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SIGNAL_REUSE_VALUE_CONFIG_VERSION
    )
    historical_calibration_gain_weight: Decimal = Decimal("0.250000")
    evidence_reuse_quality_weight: Decimal = Decimal("0.250000")
    prior_error_avoidance_weight: Decimal = Decimal("0.200000")
    review_latency_reduction_weight: Decimal = Decimal("0.150000")
    current_evidence_gap_pressure_weight: Decimal = Decimal("0.150000")
    pass_threshold: Decimal = Decimal("0.800000")
    watch_threshold: Decimal = Decimal("0.600000")
    min_pass_historical_calibration_gain: Decimal = Decimal("0.750000")
    min_watch_historical_calibration_gain: Decimal = Decimal("0.500000")
    min_pass_evidence_reuse_quality: Decimal = Decimal("0.750000")
    min_watch_evidence_reuse_quality: Decimal = Decimal("0.500000")
    min_pass_prior_error_avoidance: Decimal = Decimal("0.750000")
    min_watch_prior_error_avoidance: Decimal = Decimal("0.500000")
    min_pass_review_latency_reduction: Decimal = Decimal("0.650000")
    min_watch_review_latency_reduction: Decimal = Decimal("0.400000")
    max_pass_current_evidence_gap_pressure: Decimal = Decimal("0.200000")
    max_watch_current_evidence_gap_pressure: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchTeamDomainMemorySignalReuseValueConfig,
        )
        object.__setattr__(
            self,
            "config_version",
            _require_supported_config_version(self.config_version),
        )
        for field_name in (
            "historical_calibration_gain_weight",
            "evidence_reuse_quality_weight",
            "prior_error_avoidance_weight",
            "review_latency_reduction_weight",
            "current_evidence_gap_pressure_weight",
            "pass_threshold",
            "watch_threshold",
            "min_pass_historical_calibration_gain",
            "min_watch_historical_calibration_gain",
            "min_pass_evidence_reuse_quality",
            "min_watch_evidence_reuse_quality",
            "min_pass_prior_error_avoidance",
            "min_watch_prior_error_avoidance",
            "min_pass_review_latency_reduction",
            "min_watch_review_latency_reduction",
            "max_pass_current_evidence_gap_pressure",
            "max_watch_current_evidence_gap_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@final
@dataclass(frozen=True)
class ResearchTeamDomainMemorySignalReuseValueObservation(_FinalPublicDataclass):
    domain_key: str
    team_key: str = field(repr=False)
    memory_reference: str = field(repr=False)
    observed_at: datetime
    historical_calibration_gain: Decimal
    evidence_reuse_quality: Decimal
    prior_error_avoidance: Decimal
    review_latency_reduction: Decimal
    current_evidence_gap_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            ResearchTeamDomainMemorySignalReuseValueObservation,
        )
        object.__setattr__(
            self,
            "domain_key",
            _require_public_identifier("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "team_key",
            _require_public_identifier("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "memory_reference",
            _require_private_reference("memory_reference", self.memory_reference),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "historical_calibration_gain",
            "evidence_reuse_quality",
            "prior_error_avoidance",
            "review_latency_reduction",
            "current_evidence_gap_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@final
@dataclass(frozen=True)
class ResearchTeamDomainMemorySignalReuseValueRow(_FinalPublicDataclass):
    domain_key: str
    reuse_value_status: str
    observation_count: Decimal
    team_count: Decimal
    average_historical_calibration_gain: Decimal
    average_evidence_reuse_quality: Decimal
    average_prior_error_avoidance: Decimal
    average_review_latency_reduction: Decimal
    average_current_evidence_gap_pressure: Decimal
    memory_reuse_value_score: Decimal
    signal_memory_digests: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchTeamDomainMemorySignalReuseValueConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchTeamDomainMemorySignalReuseValueConfig | None,
    ) -> None:
        _require_exact_type("row", self, ResearchTeamDomainMemorySignalReuseValueRow)
        object.__setattr__(
            self,
            "domain_key",
            _require_public_identifier("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "reuse_value_status",
            _require_status("reuse_value_status", self.reuse_value_status),
        )
        for field_name in ("observation_count", "team_count"):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_historical_calibration_gain",
            "average_evidence_reuse_quality",
            "average_prior_error_avoidance",
            "average_review_latency_reduction",
            "average_current_evidence_gap_pressure",
            "memory_reuse_value_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "signal_memory_digests",
            _normalize_signal_memory_digests(self.signal_memory_digests),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@final
@dataclass(frozen=True)
class ResearchTeamDomainMemorySignalReuseValueReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason count",
            self,
            ResearchTeamDomainMemorySignalReuseValueReasonCodeCount,
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_whole_count_decimal("count", self.count),
        )
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@final
@dataclass(frozen=True)
class ResearchTeamDomainMemorySignalReuseValueReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    domain_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_memory_reuse_value_score: Decimal
    highest_current_evidence_gap_pressure: Decimal
    rows: tuple[ResearchTeamDomainMemorySignalReuseValueRow, ...]
    reason_code_counts: tuple[ResearchTeamDomainMemorySignalReuseValueReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchTeamDomainMemorySignalReuseValueConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchTeamDomainMemorySignalReuseValueConfig | None,
    ) -> None:
        _require_exact_type("report", self, ResearchTeamDomainMemorySignalReuseValueReport)
        if validation_config is None:
            validation_config = ResearchTeamDomainMemorySignalReuseValueConfig()
        validation_config = _revalidated_config(
            validation_config,
            label="validation_config",
        )
        object.__setattr__(self, "_validation_config", validation_config)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_supported_config_version(self.config_version),
        )
        object.__setattr__(
            self,
            "report_status",
            _require_status("report_status", self.report_status),
        )
        for field_name in (
            "domain_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_memory_reuse_value_score",
            "highest_current_evidence_gap_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "rows",
            _normalize_rows(
                self.rows,
                validation_config=validation_config,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")

    @property
    def public_payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("public payload must be a JSON object")
        return _validate_public_payload(
            payload,
            validation_config=self._validation_config,
        )


def build_research_team_domain_memory_signal_reuse_value_report(
    observations: Sequence[ResearchTeamDomainMemorySignalReuseValueObservation],
    *,
    generated_at: datetime,
    config: ResearchTeamDomainMemorySignalReuseValueConfig | None = None,
) -> ResearchTeamDomainMemorySignalReuseValueReport:
    """Build a deterministic public-safe report from sanitized memory signals."""

    if config is None:
        config = ResearchTeamDomainMemorySignalReuseValueConfig()
    config = _revalidated_config(config, label="config")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(
        observations,
        generated_at=generated_at,
    )
    rows = _build_rows(
        normalized_observations,
        config=config,
    )
    reason_codes = _report_reason_codes(rows)
    report_status = _status_for_reason_codes(reason_codes)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": report_status,
        "domain_count": _decimal_count(len(rows)),
        "observation_count": _decimal_count(len(normalized_observations)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_memory_reuse_value_score": _weighted_row_average(
            rows,
            "memory_reuse_value_score",
        ),
        "highest_current_evidence_gap_pressure": _highest_gap_pressure(rows),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainMemorySignalReuseValueReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
        validation_config=config,
    )


def research_team_domain_memory_signal_reuse_value_public_payload(
    value: object,
    *,
    validation_config: ResearchTeamDomainMemorySignalReuseValueConfig | None = None,
) -> dict[str, Any]:
    if type(value) is ResearchTeamDomainMemorySignalReuseValueReport:
        _require_hard_flags("report", value)
        return value.public_payload
    elif type(value) is dict:
        payload = dict(value)
    else:
        raise ValueError(
            "value must be a ResearchTeamDomainMemorySignalReuseValueReport or JSON object",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    return _validate_public_payload(
        payload,
        validation_config=validation_config,
    )


def research_team_domain_memory_signal_reuse_value_report_digest(
    value: object,
    *,
    validation_config: ResearchTeamDomainMemorySignalReuseValueConfig | None = None,
) -> str:
    if type(value) is ResearchTeamDomainMemorySignalReuseValueReport:
        payload = value.public_payload
    elif type(value) is dict:
        payload = research_team_domain_memory_signal_reuse_value_public_payload(
            value,
            validation_config=validation_config,
        )
    else:
        raise ValueError(
            "value must be a ResearchTeamDomainMemorySignalReuseValueReport or JSON object",
        )
    digest = payload.get("derived_validation_digest")
    return _require_sha256_digest("derived_validation_digest", digest)


def _validate_public_payload(
    payload: dict[str, Any],
    *,
    validation_config: ResearchTeamDomainMemorySignalReuseValueConfig | None,
) -> dict[str, Any]:
    _validate_payload_flags(payload, "public_payload")
    _reject_unsafe_public_payload("public_payload", payload)
    report = _report_from_public_payload(
        payload,
        validation_config=validation_config,
    )
    canonical_payload = _json_ready(asdict(report))
    if type(canonical_payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    if canonical_payload != payload:
        raise ValueError("public payload schema values must be canonical")
    return canonical_payload


def _report_from_public_payload(
    payload: dict[str, Any],
    *,
    validation_config: ResearchTeamDomainMemorySignalReuseValueConfig | None,
) -> ResearchTeamDomainMemorySignalReuseValueReport:
    _require_exact_payload_fields(
        "public payload",
        payload,
        ResearchTeamDomainMemorySignalReuseValueReport,
    )
    rows = tuple(
        _row_from_public_payload(
            item,
            index=index,
            validation_config=validation_config,
        )
        for index, item in enumerate(_require_public_list("rows", payload["rows"]))
    )
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(item, index=index)
        for index, item in enumerate(
            _require_public_list(
                "reason_code_counts",
                payload["reason_code_counts"],
            ),
        )
    )
    return ResearchTeamDomainMemorySignalReuseValueReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        report_status=payload["report_status"],
        domain_count=_public_decimal("domain_count", payload["domain_count"]),
        observation_count=_public_decimal(
            "observation_count",
            payload["observation_count"],
        ),
        pass_count=_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_decimal("watch_count", payload["watch_count"]),
        block_count=_public_decimal("block_count", payload["block_count"]),
        average_memory_reuse_value_score=_public_decimal(
            "average_memory_reuse_value_score",
            payload["average_memory_reuse_value_score"],
        ),
        highest_current_evidence_gap_pressure=_public_decimal(
            "highest_current_evidence_gap_pressure",
            payload["highest_current_evidence_gap_pressure"],
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_public_string_tuple("reason_codes", payload["reason_codes"]),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
        validation_config=validation_config,
    )


def _row_from_public_payload(
    value: object,
    *,
    index: int,
    validation_config: ResearchTeamDomainMemorySignalReuseValueConfig | None,
) -> ResearchTeamDomainMemorySignalReuseValueRow:
    field_name = f"rows[{index}]"
    payload = _require_public_dict(field_name, value)
    _require_exact_payload_fields(
        field_name,
        payload,
        ResearchTeamDomainMemorySignalReuseValueRow,
    )
    return ResearchTeamDomainMemorySignalReuseValueRow(
        domain_key=payload["domain_key"],
        reuse_value_status=payload["reuse_value_status"],
        observation_count=_public_decimal(
            f"{field_name}.observation_count",
            payload["observation_count"],
        ),
        team_count=_public_decimal(
            f"{field_name}.team_count",
            payload["team_count"],
        ),
        average_historical_calibration_gain=_public_decimal(
            f"{field_name}.average_historical_calibration_gain",
            payload["average_historical_calibration_gain"],
        ),
        average_evidence_reuse_quality=_public_decimal(
            f"{field_name}.average_evidence_reuse_quality",
            payload["average_evidence_reuse_quality"],
        ),
        average_prior_error_avoidance=_public_decimal(
            f"{field_name}.average_prior_error_avoidance",
            payload["average_prior_error_avoidance"],
        ),
        average_review_latency_reduction=_public_decimal(
            f"{field_name}.average_review_latency_reduction",
            payload["average_review_latency_reduction"],
        ),
        average_current_evidence_gap_pressure=_public_decimal(
            f"{field_name}.average_current_evidence_gap_pressure",
            payload["average_current_evidence_gap_pressure"],
        ),
        memory_reuse_value_score=_public_decimal(
            f"{field_name}.memory_reuse_value_score",
            payload["memory_reuse_value_score"],
        ),
        signal_memory_digests=_public_string_tuple(
            f"{field_name}.signal_memory_digests",
            payload["signal_memory_digests"],
        ),
        reason_codes=_public_string_tuple(
            f"{field_name}.reason_codes",
            payload["reason_codes"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
        validation_config=validation_config,
    )


def _reason_code_count_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchTeamDomainMemorySignalReuseValueReasonCodeCount:
    field_name = f"reason_code_counts[{index}]"
    payload = _require_public_dict(field_name, value)
    _require_exact_payload_fields(
        field_name,
        payload,
        ResearchTeamDomainMemorySignalReuseValueReasonCodeCount,
    )
    return ResearchTeamDomainMemorySignalReuseValueReasonCodeCount(
        reason_code=payload["reason_code"],
        count=_public_decimal(f"{field_name}.count", payload["count"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _require_exact_payload_fields(
    label: str,
    payload: dict[str, Any],
    expected_type: type[object],
) -> None:
    expected_fields = tuple(field.name for field in fields(expected_type))
    if tuple(payload) != expected_fields:
        raise ValueError(f"{label} schema mismatch")


def _require_public_dict(field_name: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    return value


def _require_public_list(field_name: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    return value


def _public_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    values = _require_public_list(field_name, value)
    if any(type(item) is not str for item in values):
        raise ValueError(f"{field_name} must contain strings")
    return tuple(values)


def _public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return parsed


def _build_rows(
    observations: tuple[ResearchTeamDomainMemorySignalReuseValueObservation, ...],
    *,
    config: ResearchTeamDomainMemorySignalReuseValueConfig,
) -> tuple[ResearchTeamDomainMemorySignalReuseValueRow, ...]:
    grouped: dict[str, list[ResearchTeamDomainMemorySignalReuseValueObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.domain_key, []).append(observation)
    return tuple(
        _build_row(
            domain_key=domain_key,
            observations=tuple(grouped[domain_key]),
            config=config,
        )
        for domain_key in sorted(grouped)
    )


def _build_row(
    *,
    domain_key: str,
    observations: tuple[ResearchTeamDomainMemorySignalReuseValueObservation, ...],
    config: ResearchTeamDomainMemorySignalReuseValueConfig,
) -> ResearchTeamDomainMemorySignalReuseValueRow:
    observation_count = _decimal_count(len(observations))
    team_count = _decimal_count(len({observation.team_key for observation in observations}))
    average_historical = _average(
        tuple(observation.historical_calibration_gain for observation in observations),
    )
    average_evidence = _average(
        tuple(observation.evidence_reuse_quality for observation in observations),
    )
    average_error_avoidance = _average(
        tuple(observation.prior_error_avoidance for observation in observations),
    )
    average_latency = _average(
        tuple(observation.review_latency_reduction for observation in observations),
    )
    average_gap = _average(
        tuple(observation.current_evidence_gap_pressure for observation in observations),
    )
    value_score = _memory_reuse_value_score(
        average_historical_calibration_gain=average_historical,
        average_evidence_reuse_quality=average_evidence,
        average_prior_error_avoidance=average_error_avoidance,
        average_review_latency_reduction=average_latency,
        average_current_evidence_gap_pressure=average_gap,
        config=config,
    )
    reason_codes = _row_reason_codes(
        average_historical_calibration_gain=average_historical,
        average_evidence_reuse_quality=average_evidence,
        average_prior_error_avoidance=average_error_avoidance,
        average_review_latency_reduction=average_latency,
        average_current_evidence_gap_pressure=average_gap,
        memory_reuse_value_score=value_score,
        config=config,
    )
    return ResearchTeamDomainMemorySignalReuseValueRow(
        domain_key=domain_key,
        reuse_value_status=_status_for_reason_codes(reason_codes),
        observation_count=observation_count,
        team_count=team_count,
        average_historical_calibration_gain=average_historical,
        average_evidence_reuse_quality=average_evidence,
        average_prior_error_avoidance=average_error_avoidance,
        average_review_latency_reduction=average_latency,
        average_current_evidence_gap_pressure=average_gap,
        memory_reuse_value_score=value_score,
        signal_memory_digests=tuple(
            sorted({_memory_reference_digest(item.memory_reference) for item in observations}),
        ),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _memory_reuse_value_score(
    *,
    average_historical_calibration_gain: Decimal,
    average_evidence_reuse_quality: Decimal,
    average_prior_error_avoidance: Decimal,
    average_review_latency_reduction: Decimal,
    average_current_evidence_gap_pressure: Decimal,
    config: ResearchTeamDomainMemorySignalReuseValueConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            average_historical_calibration_gain
            * config.historical_calibration_gain_weight
            + average_evidence_reuse_quality * config.evidence_reuse_quality_weight
            + average_prior_error_avoidance * config.prior_error_avoidance_weight
            + average_review_latency_reduction
            * config.review_latency_reduction_weight
            + (ONE - average_current_evidence_gap_pressure)
            * config.current_evidence_gap_pressure_weight
        )
    return _clamp_ratio(score)


def _row_reason_codes(
    *,
    average_historical_calibration_gain: Decimal,
    average_evidence_reuse_quality: Decimal,
    average_prior_error_avoidance: Decimal,
    average_review_latency_reduction: Decimal,
    average_current_evidence_gap_pressure: Decimal,
    memory_reuse_value_score: Decimal,
    config: ResearchTeamDomainMemorySignalReuseValueConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_floor_reason(
        reason_codes,
        value=average_historical_calibration_gain,
        pass_threshold=config.min_pass_historical_calibration_gain,
        watch_threshold=config.min_watch_historical_calibration_gain,
        watch_reason=HISTORICAL_CALIBRATION_GAIN_WATCH_REASON,
        block_reason=HISTORICAL_CALIBRATION_GAIN_BLOCK_REASON,
    )
    _append_floor_reason(
        reason_codes,
        value=average_evidence_reuse_quality,
        pass_threshold=config.min_pass_evidence_reuse_quality,
        watch_threshold=config.min_watch_evidence_reuse_quality,
        watch_reason=EVIDENCE_REUSE_QUALITY_WATCH_REASON,
        block_reason=EVIDENCE_REUSE_QUALITY_BLOCK_REASON,
    )
    _append_floor_reason(
        reason_codes,
        value=average_prior_error_avoidance,
        pass_threshold=config.min_pass_prior_error_avoidance,
        watch_threshold=config.min_watch_prior_error_avoidance,
        watch_reason=PRIOR_ERROR_AVOIDANCE_WATCH_REASON,
        block_reason=PRIOR_ERROR_AVOIDANCE_BLOCK_REASON,
    )
    _append_floor_reason(
        reason_codes,
        value=average_review_latency_reduction,
        pass_threshold=config.min_pass_review_latency_reduction,
        watch_threshold=config.min_watch_review_latency_reduction,
        watch_reason=REVIEW_LATENCY_REDUCTION_WATCH_REASON,
        block_reason=REVIEW_LATENCY_REDUCTION_BLOCK_REASON,
    )
    _append_ceiling_reason(
        reason_codes,
        value=average_current_evidence_gap_pressure,
        pass_threshold=config.max_pass_current_evidence_gap_pressure,
        watch_threshold=config.max_watch_current_evidence_gap_pressure,
        watch_reason=CURRENT_EVIDENCE_GAP_PRESSURE_WATCH_REASON,
        block_reason=CURRENT_EVIDENCE_GAP_PRESSURE_BLOCK_REASON,
    )
    _append_floor_reason(
        reason_codes,
        value=memory_reuse_value_score,
        pass_threshold=config.pass_threshold,
        watch_threshold=config.watch_threshold,
        watch_reason=MEMORY_REUSE_VALUE_SCORE_WATCH_REASON,
        block_reason=MEMORY_REUSE_VALUE_SCORE_BLOCK_REASON,
    )
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _normalize_reason_codes(tuple(reason_codes), ROW_REASON_CODES)


def _append_floor_reason(
    reason_codes: list[str],
    *,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value < watch_threshold:
        reason_codes.append(block_reason)
    elif value < pass_threshold:
        reason_codes.append(watch_reason)


def _append_ceiling_reason(
    reason_codes: list[str],
    *,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value > watch_threshold:
        reason_codes.append(block_reason)
    elif value > pass_threshold:
        reason_codes.append(watch_reason)


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainMemorySignalReuseValueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    row_reason_codes = _normalize_reason_codes(
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
        REPORT_REASON_CODES,
    )
    report_reason = REPORT_PASS_REASON
    if any(row.reuse_value_status == "block" for row in rows):
        report_reason = REPORT_BLOCK_REASON
    elif any(row.reuse_value_status == "watch" for row in rows):
        report_reason = REPORT_WATCH_REASON
    return _normalize_reason_codes((report_reason,) + row_reason_codes, REPORT_REASON_CODES)


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchTeamDomainMemorySignalReuseValueRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.reuse_value_status == status))


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainMemorySignalReuseValueRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamDomainMemorySignalReuseValueReasonCodeCount, ...]:
    if reason_codes == (EMPTY_REASON,):
        return (
            ResearchTeamDomainMemorySignalReuseValueReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            counter[reason_code] += 1
    if REPORT_BLOCK_REASON in reason_codes:
        counter[REPORT_BLOCK_REASON] = 1
    if REPORT_WATCH_REASON in reason_codes:
        counter[REPORT_WATCH_REASON] = 1
    if REPORT_PASS_REASON in reason_codes:
        counter[REPORT_PASS_REASON] = 1
    return tuple(
        ResearchTeamDomainMemorySignalReuseValueReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
        if counter[reason_code] > 0
    )


def _normalize_observations(
    observations: Sequence[ResearchTeamDomainMemorySignalReuseValueObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamDomainMemorySignalReuseValueObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchTeamDomainMemorySignalReuseValueObservation] = []
    for observation_value in observations:
        observation = _revalidated_observation(observation_value)
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        normalized.append(observation)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.domain_key,
                item.team_key,
                item.observed_at,
                item.memory_reference,
                item.historical_calibration_gain,
                item.evidence_reuse_quality,
                item.prior_error_avoidance,
                item.review_latency_reduction,
                item.current_evidence_gap_pressure,
            ),
        )
    )


def _normalize_rows(
    rows: Sequence[ResearchTeamDomainMemorySignalReuseValueRow],
    *,
    validation_config: ResearchTeamDomainMemorySignalReuseValueConfig,
) -> tuple[ResearchTeamDomainMemorySignalReuseValueRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchTeamDomainMemorySignalReuseValueRow] = []
    domain_keys: set[str] = set()
    for row_value in rows:
        row = _revalidated_row(
            row_value,
            validation_config=validation_config,
        )
        if row.domain_key in domain_keys:
            raise ValueError("row domain_key values must be unique")
        domain_keys.add(row.domain_key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.domain_key))


def _normalize_reason_code_counts(
    values: Sequence[ResearchTeamDomainMemorySignalReuseValueReasonCodeCount],
) -> tuple[ResearchTeamDomainMemorySignalReuseValueReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchTeamDomainMemorySignalReuseValueReasonCodeCount] = []
    for reason_code_count_value in values:
        value = _revalidated_reason_code_count(reason_code_count_value)
        normalized.append(value)
    return tuple(sorted(normalized, key=lambda item: REASON_CODE_RANK[item.reason_code]))


def _normalize_reason_codes(
    values: Sequence[str],
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or value not in allowed_reason_codes:
            raise ValueError("reason_codes must contain supported reason codes")
        if value not in normalized:
            normalized.append(value)
    return tuple(reason for reason in allowed_reason_codes if reason in normalized)


def _normalize_signal_memory_digests(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("signal_memory_digests must be a sequence")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not value.startswith("sha256:"):
            raise ValueError("signal_memory_digests must contain sha256 digests")
        _require_sha256_digest("signal_memory_digest", value.removeprefix("sha256:"))
        if value not in normalized:
            normalized.append(value)
    if not normalized:
        raise ValueError("signal_memory_digests must contain at least one digest")
    return tuple(sorted(normalized))


def _revalidated_config(
    value: object,
    *,
    label: str,
) -> ResearchTeamDomainMemorySignalReuseValueConfig:
    if type(value) is not ResearchTeamDomainMemorySignalReuseValueConfig:
        raise ValueError(
            f"{label} must be a ResearchTeamDomainMemorySignalReuseValueConfig",
        )
    return ResearchTeamDomainMemorySignalReuseValueConfig(
        **{
            config_field.name: getattr(value, config_field.name)
            for config_field in fields(ResearchTeamDomainMemorySignalReuseValueConfig)
        },
    )


def _revalidated_observation(
    value: object,
) -> ResearchTeamDomainMemorySignalReuseValueObservation:
    if type(value) is not ResearchTeamDomainMemorySignalReuseValueObservation:
        raise ValueError(
            "observations must contain "
            "ResearchTeamDomainMemorySignalReuseValueObservation",
        )
    return ResearchTeamDomainMemorySignalReuseValueObservation(
        **{
            observation_field.name: getattr(value, observation_field.name)
            for observation_field in fields(
                ResearchTeamDomainMemorySignalReuseValueObservation,
            )
        },
    )


def _revalidated_row(
    value: object,
    *,
    validation_config: ResearchTeamDomainMemorySignalReuseValueConfig,
) -> ResearchTeamDomainMemorySignalReuseValueRow:
    if type(value) is not ResearchTeamDomainMemorySignalReuseValueRow:
        raise ValueError("rows must contain ResearchTeamDomainMemorySignalReuseValueRow")
    return ResearchTeamDomainMemorySignalReuseValueRow(
        **{
            row_field.name: getattr(value, row_field.name)
            for row_field in fields(ResearchTeamDomainMemorySignalReuseValueRow)
        },
        validation_config=validation_config,
    )


def _revalidated_reason_code_count(
    value: object,
) -> ResearchTeamDomainMemorySignalReuseValueReasonCodeCount:
    if type(value) is not ResearchTeamDomainMemorySignalReuseValueReasonCodeCount:
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchTeamDomainMemorySignalReuseValueReasonCodeCount",
        )
    return ResearchTeamDomainMemorySignalReuseValueReasonCodeCount(
        **{
            reason_count_field.name: getattr(value, reason_count_field.name)
            for reason_count_field in fields(
                ResearchTeamDomainMemorySignalReuseValueReasonCodeCount,
            )
        },
    )


def _validate_config(config: ResearchTeamDomainMemorySignalReuseValueConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weight_sum = _quantize(
            config.historical_calibration_gain_weight
            + config.evidence_reuse_quality_weight
            + config.prior_error_avoidance_weight
            + config.review_latency_reduction_weight
            + config.current_evidence_gap_pressure_weight,
        )
    if weight_sum != ONE:
        raise ValueError("weights must sum to 1")
    if config.pass_threshold <= config.watch_threshold:
        raise ValueError("pass_threshold must exceed watch_threshold")
    _require_floor_config_order(
        "historical_calibration_gain",
        config.min_pass_historical_calibration_gain,
        config.min_watch_historical_calibration_gain,
    )
    _require_floor_config_order(
        "evidence_reuse_quality",
        config.min_pass_evidence_reuse_quality,
        config.min_watch_evidence_reuse_quality,
    )
    _require_floor_config_order(
        "prior_error_avoidance",
        config.min_pass_prior_error_avoidance,
        config.min_watch_prior_error_avoidance,
    )
    _require_floor_config_order(
        "review_latency_reduction",
        config.min_pass_review_latency_reduction,
        config.min_watch_review_latency_reduction,
    )
    if (
        config.max_pass_current_evidence_gap_pressure
        >= config.max_watch_current_evidence_gap_pressure
    ):
        raise ValueError(
            "max_pass_current_evidence_gap_pressure must be below watch threshold",
        )


def _require_floor_config_order(
    label: str,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> None:
    if pass_threshold <= watch_threshold:
        raise ValueError(f"min_pass_{label} must exceed watch threshold")


def _validate_row(
    row: ResearchTeamDomainMemorySignalReuseValueRow,
    *,
    config: ResearchTeamDomainMemorySignalReuseValueConfig | None,
) -> None:
    if config is None:
        config = ResearchTeamDomainMemorySignalReuseValueConfig()
    config = _revalidated_config(config, label="validation_config")
    if row.observation_count <= ZERO:
        raise ValueError("observation_count must be positive")
    if row.team_count <= ZERO:
        raise ValueError("team_count must be positive")
    if row.team_count > row.observation_count:
        raise ValueError("team_count must not exceed observation_count")
    if len(row.signal_memory_digests) > int(row.observation_count):
        raise ValueError("signal_memory_digests must not exceed observation_count")
    expected_score = _memory_reuse_value_score(
        average_historical_calibration_gain=row.average_historical_calibration_gain,
        average_evidence_reuse_quality=row.average_evidence_reuse_quality,
        average_prior_error_avoidance=row.average_prior_error_avoidance,
        average_review_latency_reduction=row.average_review_latency_reduction,
        average_current_evidence_gap_pressure=(
            row.average_current_evidence_gap_pressure
        ),
        config=config,
    )
    if row.memory_reuse_value_score != expected_score:
        raise ValueError("memory_reuse_value_score must match row averages")
    expected_reason_codes = _row_reason_codes(
        average_historical_calibration_gain=row.average_historical_calibration_gain,
        average_evidence_reuse_quality=row.average_evidence_reuse_quality,
        average_prior_error_avoidance=row.average_prior_error_avoidance,
        average_review_latency_reduction=row.average_review_latency_reduction,
        average_current_evidence_gap_pressure=(
            row.average_current_evidence_gap_pressure
        ),
        memory_reuse_value_score=row.memory_reuse_value_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row averages and score")
    if row.reuse_value_status != _status_for_reason_codes(expected_reason_codes):
        raise ValueError("reuse_value_status must match reason_codes")


def _validate_report(report: ResearchTeamDomainMemorySignalReuseValueReport) -> None:
    for row in report.rows:
        _validate_row(row, config=report._validation_config)
    if report.domain_count != _decimal_count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    with localcontext(DECIMAL_CONTEXT):
        expected_observation_count = sum(
            (row.observation_count for row in report.rows),
            ZERO,
        )
        expected_status_count = (
            report.pass_count + report.watch_count + report.block_count
        )
    if report.observation_count != expected_observation_count:
        raise ValueError("observation_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if expected_status_count != report.domain_count:
        raise ValueError("status counts must match domain_count")
    if report.average_memory_reuse_value_score != _weighted_row_average(
        report.rows,
        "memory_reuse_value_score",
    ):
        raise ValueError("average_memory_reuse_value_score must match rows")
    if report.highest_current_evidence_gap_pressure != _highest_gap_pressure(report.rows):
        raise ValueError("highest_current_evidence_gap_pressure must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.report_status != _status_for_reason_codes(report.reason_codes):
        raise ValueError("report_status must match reason_codes")


def _highest_gap_pressure(
    rows: tuple[ResearchTeamDomainMemorySignalReuseValueRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.average_current_evidence_gap_pressure for row in rows)


def _weighted_row_average(
    rows: tuple[ResearchTeamDomainMemorySignalReuseValueRow, ...],
    field_name: str,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total_weight = sum((row.observation_count for row in rows), ZERO)
        if total_weight <= ZERO:
            return ZERO
        weighted_total = sum(
            (getattr(row, field_name) * row.observation_count for row in rows),
            ZERO,
        )
        weighted_average = weighted_total / total_weight
    return _clamp_ratio(weighted_average)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        average = sum(values, ZERO) / Decimal(len(values))
    return _quantize(average)


def _memory_reference_digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchTeamDomainMemorySignalReuseValueReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest_payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("Decimal value must be exactly Decimal")
    if type(value) is datetime:
        return _as_utc("datetime value", value).isoformat()
    if isinstance(value, datetime):
        raise ValueError("datetime value must be exactly datetime")
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_string(path or label, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{path or label} must be exactly Decimal")
    if type(value) is datetime:
        _as_utc(path or label, value)
        return
    if isinstance(value, datetime):
        raise ValueError(f"{path or label} must be exactly datetime")
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal-derived values")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_string(item_path, key)
            if key in PHASE_FLAG_FIELDS and nested_value is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _validate_payload_flags(payload: Mapping[str, object], label: str) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_supported_config_version(value: object) -> str:
    if type(value) is not str or value.strip() != value or not value:
        raise ValueError("config_version must be a canonical string")
    if value != DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SIGNAL_REUSE_VALUE_CONFIG_VERSION:
        raise ValueError("config_version must be supported")
    _reject_unsafe_public_string("config_version", value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REPORT_REASON_CODES:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_raw_decimal(field_name, value)
    return _quantize(decimal_value)


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_raw_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _require_whole_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_raw_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        is_whole = decimal_value == decimal_value.to_integral_value()
    if not is_whole:
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(decimal_value)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    try:
        utc_offset = value.utcoffset()
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be representable in UTC") from exc
    if utc_offset is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    try:
        return value.astimezone(UTC)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be representable in UTC") from exc


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("Decimal value must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload at {path}")
