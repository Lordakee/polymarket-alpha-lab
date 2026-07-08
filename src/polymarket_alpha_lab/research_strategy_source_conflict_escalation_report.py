"""Pure report-only strategy source-conflict escalation readiness aggregation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_SOURCE_CONFLICT_ESCALATION_CONFIG_VERSION = (
    "research-strategy-source-conflict-escalation-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "auth",
    "candidate",
    "database",
    "dsn",
    "live",
    "market",
    "network",
    "order",
    "postgres",
    "question",
    "recommendation",
    "secret",
    "sizing",
    "slug",
    "table",
    "token",
    "trading",
    "url",
    "wallet",
)
_REASON_CODE_SEQUENCE = (
    "empty_conflict_groups",
    "contradiction_pressure_watch",
    "contradiction_pressure_block",
    "source_class_quorum_watch",
    "stale_conflict_age_watch",
    "stale_conflict_age_block",
    "specialist_dissent_watch",
    "specialist_dissent_block",
    "manual_escalation_watch",
    "manual_escalation_block",
    "escalation_readiness_pass",
)


@dataclass(frozen=True)
class ResearchStrategySourceConflictEscalationConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_SOURCE_CONFLICT_ESCALATION_CONFIG_VERSION
    required_source_class_count: Decimal = Decimal("3.000000")
    watch_contradiction_pressure_threshold: Decimal = Decimal("0.500000")
    block_contradiction_pressure_threshold: Decimal = Decimal("0.850000")
    min_source_class_quorum_score: Decimal = Decimal("0.750000")
    stale_conflict_watch_age_seconds: Decimal = Decimal("7200.000000")
    stale_conflict_block_age_seconds: Decimal = Decimal("21600.000000")
    specialist_dissent_watch_threshold: Decimal = Decimal("0.500000")
    specialist_dissent_block_threshold: Decimal = Decimal("0.750000")
    manual_escalation_watch_threshold: Decimal = Decimal("0.500000")
    manual_escalation_block_threshold: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceConflictEscalationConfig:
            raise TypeError(
                "ResearchStrategySourceConflictEscalationConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySourceConflictEscalationConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_CONFLICT_ESCALATION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "required_source_class_count",
            _require_positive_whole_decimal(
                "required_source_class_count",
                self.required_source_class_count,
            ),
        )
        for field_name in (
            "watch_contradiction_pressure_threshold",
            "block_contradiction_pressure_threshold",
            "min_source_class_quorum_score",
            "specialist_dissent_watch_threshold",
            "specialist_dissent_block_threshold",
            "manual_escalation_watch_threshold",
            "manual_escalation_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_conflict_watch_age_seconds",
            "stale_conflict_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.block_contradiction_pressure_threshold
            <= self.watch_contradiction_pressure_threshold
        ):
            raise ValueError(
                "block_contradiction_pressure_threshold must exceed watch threshold",
            )
        if self.stale_conflict_block_age_seconds <= self.stale_conflict_watch_age_seconds:
            raise ValueError("stale_conflict_block_age_seconds must exceed watch age")
        if self.specialist_dissent_block_threshold <= self.specialist_dissent_watch_threshold:
            raise ValueError(
                "specialist_dissent_block_threshold must exceed watch threshold",
            )
        if self.manual_escalation_block_threshold <= self.manual_escalation_watch_threshold:
            raise ValueError(
                "manual_escalation_block_threshold must exceed watch threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategySourceConflictEscalationObservation:
    conflict_group_hash: str
    input_row_number: Decimal
    source_class: str
    observed_at: datetime
    contradiction_score: Decimal
    specialist_dissent_score: Decimal = Decimal("0.000000")
    manual_escalation_urgency: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceConflictEscalationObservation:
            raise TypeError(
                "ResearchStrategySourceConflictEscalationObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySourceConflictEscalationObservation,
            "observation",
        )
        _require_sha256_digest("conflict_group_hash", self.conflict_group_hash)
        object.__setattr__(
            self,
            "input_row_number",
            _require_positive_whole_decimal("input_row_number", self.input_row_number),
        )
        _require_public_identifier("source_class", self.source_class)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "contradiction_score",
            "specialist_dissent_score",
            "manual_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchStrategySourceConflictEscalationRow:
    aggregate_row_number: Decimal
    conflict_group_hash: str
    observation_count: Decimal
    source_class_count: Decimal
    source_class_quorum_score: Decimal
    contradiction_pressure: Decimal
    stale_conflict_age_seconds: Decimal
    specialist_dissent_score: Decimal
    manual_escalation_urgency: Decimal
    escalation_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceConflictEscalationRow:
            raise TypeError(
                "ResearchStrategySourceConflictEscalationRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceConflictEscalationRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _require_positive_whole_decimal(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        _require_sha256_digest("conflict_group_hash", self.conflict_group_hash)
        for field_name in ("observation_count", "source_class_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_quorum_score",
            "contradiction_pressure",
            "specialist_dissent_score",
            "manual_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_conflict_age_seconds",
            _require_nonnegative_decimal(
                "stale_conflict_age_seconds",
                self.stale_conflict_age_seconds,
            ),
        )
        _require_status("escalation_status", self.escalation_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategySourceConflictEscalationReport:
    generated_at: datetime
    config_version: str
    escalation_status: str
    input_count: Decimal
    conflict_group_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_contradiction_pressure: Decimal
    minimum_source_class_quorum_score: Decimal
    max_stale_conflict_age_seconds: Decimal
    max_specialist_dissent_score: Decimal
    max_manual_escalation_urgency: Decimal
    rows: tuple[ResearchStrategySourceConflictEscalationRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceConflictEscalationReport:
            raise TypeError(
                "ResearchStrategySourceConflictEscalationReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceConflictEscalationReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_CONFLICT_ESCALATION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("escalation_status", self.escalation_status)
        for field_name in (
            "input_count",
            "conflict_group_count",
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
            "average_contradiction_pressure",
            "minimum_source_class_quorum_score",
            "max_specialist_dissent_score",
            "max_manual_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_stale_conflict_age_seconds",
            _require_nonnegative_decimal(
                "max_stale_conflict_age_seconds",
                self.max_stale_conflict_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchStrategySourceConflictEscalationReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_strategy_source_conflict_escalation_report(
    observations: Sequence[ResearchStrategySourceConflictEscalationObservation],
    *,
    generated_at: datetime,
    config: ResearchStrategySourceConflictEscalationConfig | None = None,
) -> ResearchStrategySourceConflictEscalationReport:
    """Build a deterministic local report-only conflict escalation snapshot."""

    if config is None:
        config = ResearchStrategySourceConflictEscalationConfig()
    if type(config) is not ResearchStrategySourceConflictEscalationConfig:
        raise ValueError(
            "config must be a ResearchStrategySourceConflictEscalationConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = _build_rows(normalized_observations, config, generated_at_utc)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "escalation_status": _report_status(rows),
        "input_count": _decimal_count(len(normalized_observations)),
        "conflict_group_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_contradiction_pressure": _average(
            tuple(row.contradiction_pressure for row in rows),
        ),
        "minimum_source_class_quorum_score": min(
            (row.source_class_quorum_score for row in rows),
            default=_ZERO,
        ),
        "max_stale_conflict_age_seconds": max(
            (row.stale_conflict_age_seconds for row in rows),
            default=_ZERO,
        ),
        "max_specialist_dissent_score": max(
            (row.specialist_dissent_score for row in rows),
            default=_ZERO,
        ),
        "max_manual_escalation_urgency": max(
            (row.manual_escalation_urgency for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategySourceConflictEscalationReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    observations: tuple[ResearchStrategySourceConflictEscalationObservation, ...],
    config: ResearchStrategySourceConflictEscalationConfig,
    generated_at: datetime,
) -> tuple[ResearchStrategySourceConflictEscalationRow, ...]:
    groups: dict[str, list[ResearchStrategySourceConflictEscalationObservation]] = {}
    for observation in observations:
        groups.setdefault(observation.conflict_group_hash, []).append(observation)
    rows: list[ResearchStrategySourceConflictEscalationRow] = []
    for offset, conflict_group_hash in enumerate(sorted(groups), start=1):
        rows.append(
            _row_for_group(
                aggregate_row_number=_decimal_count(offset),
                conflict_group_hash=conflict_group_hash,
                observations=tuple(groups[conflict_group_hash]),
                config=config,
                generated_at=generated_at,
            ),
        )
    return tuple(rows)


def _row_for_group(
    *,
    aggregate_row_number: Decimal,
    conflict_group_hash: str,
    observations: tuple[ResearchStrategySourceConflictEscalationObservation, ...],
    config: ResearchStrategySourceConflictEscalationConfig,
    generated_at: datetime,
) -> ResearchStrategySourceConflictEscalationRow:
    source_class_count = _decimal_count(
        len({observation.source_class for observation in observations}),
    )
    contradiction_pressure = _average(
        tuple(observation.contradiction_score for observation in observations),
    )
    stale_conflict_age_seconds = max(
        (_age_seconds(generated_at, observation.observed_at) for observation in observations),
        default=_ZERO,
    )
    specialist_dissent_score = max(
        (observation.specialist_dissent_score for observation in observations),
        default=_ZERO,
    )
    manual_escalation_urgency = max(
        (observation.manual_escalation_urgency for observation in observations),
        default=_ZERO,
    )
    source_class_quorum_score = _clamp_ratio(
        source_class_count / config.required_source_class_count,
    )
    status = _row_status(
        contradiction_pressure=contradiction_pressure,
        source_class_quorum_score=source_class_quorum_score,
        stale_conflict_age_seconds=stale_conflict_age_seconds,
        specialist_dissent_score=specialist_dissent_score,
        manual_escalation_urgency=manual_escalation_urgency,
        config=config,
    )
    return ResearchStrategySourceConflictEscalationRow(
        aggregate_row_number=aggregate_row_number,
        conflict_group_hash=conflict_group_hash,
        observation_count=_decimal_count(len(observations)),
        source_class_count=source_class_count,
        source_class_quorum_score=source_class_quorum_score,
        contradiction_pressure=contradiction_pressure,
        stale_conflict_age_seconds=stale_conflict_age_seconds,
        specialist_dissent_score=specialist_dissent_score,
        manual_escalation_urgency=manual_escalation_urgency,
        escalation_status=status,
        reason_codes=_row_reason_codes(
            status=status,
            contradiction_pressure=contradiction_pressure,
            source_class_quorum_score=source_class_quorum_score,
            stale_conflict_age_seconds=stale_conflict_age_seconds,
            specialist_dissent_score=specialist_dissent_score,
            manual_escalation_urgency=manual_escalation_urgency,
            config=config,
        ),
    )


def _row_status(
    *,
    contradiction_pressure: Decimal,
    source_class_quorum_score: Decimal,
    stale_conflict_age_seconds: Decimal,
    specialist_dissent_score: Decimal,
    manual_escalation_urgency: Decimal,
    config: ResearchStrategySourceConflictEscalationConfig,
) -> str:
    if (
        contradiction_pressure >= config.block_contradiction_pressure_threshold
        or stale_conflict_age_seconds >= config.stale_conflict_block_age_seconds
        or specialist_dissent_score >= config.specialist_dissent_block_threshold
        or manual_escalation_urgency >= config.manual_escalation_block_threshold
    ):
        return "block"
    if (
        source_class_quorum_score < config.min_source_class_quorum_score
        or contradiction_pressure >= config.watch_contradiction_pressure_threshold
        or stale_conflict_age_seconds >= config.stale_conflict_watch_age_seconds
        or specialist_dissent_score >= config.specialist_dissent_watch_threshold
        or manual_escalation_urgency >= config.manual_escalation_watch_threshold
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    contradiction_pressure: Decimal,
    source_class_quorum_score: Decimal,
    stale_conflict_age_seconds: Decimal,
    specialist_dissent_score: Decimal,
    manual_escalation_urgency: Decimal,
    config: ResearchStrategySourceConflictEscalationConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if contradiction_pressure >= config.block_contradiction_pressure_threshold:
        reason_codes.append("contradiction_pressure_block")
    elif contradiction_pressure >= config.watch_contradiction_pressure_threshold:
        reason_codes.append("contradiction_pressure_watch")
    if source_class_quorum_score < config.min_source_class_quorum_score:
        reason_codes.append("source_class_quorum_watch")
    if stale_conflict_age_seconds >= config.stale_conflict_block_age_seconds:
        reason_codes.append("stale_conflict_age_block")
    elif stale_conflict_age_seconds >= config.stale_conflict_watch_age_seconds:
        reason_codes.append("stale_conflict_age_watch")
    if specialist_dissent_score >= config.specialist_dissent_block_threshold:
        reason_codes.append("specialist_dissent_block")
    elif specialist_dissent_score >= config.specialist_dissent_watch_threshold:
        reason_codes.append("specialist_dissent_watch")
    if manual_escalation_urgency >= config.manual_escalation_block_threshold:
        reason_codes.append("manual_escalation_block")
    elif manual_escalation_urgency >= config.manual_escalation_watch_threshold:
        reason_codes.append("manual_escalation_watch")
    if status == "pass":
        reason_codes.append("escalation_readiness_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchStrategySourceConflictEscalationRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.escalation_status == "block" for row in rows):
        return "block"
    if any(row.escalation_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategySourceConflictEscalationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_conflict_groups",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchStrategySourceConflictEscalationRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.escalation_status == status))


def _validate_row(row: ResearchStrategySourceConflictEscalationRow) -> None:
    if row.observation_count <= _ZERO:
        raise ValueError("observation_count must be positive")
    if row.source_class_count > row.observation_count:
        raise ValueError("source_class_count must not exceed observation_count")
    if row.escalation_status == "pass" and row.reason_codes != (
        "escalation_readiness_pass",
    ):
        raise ValueError("pass rows must only include escalation_readiness_pass")
    if row.escalation_status != "pass" and not row.reason_codes:
        raise ValueError("watch and block rows must include reason codes")


def _validate_report(report: ResearchStrategySourceConflictEscalationReport) -> None:
    if report.conflict_group_count != _decimal_count(len(report.rows)):
        raise ValueError("conflict_group_count must match rows")
    expected_pass = _status_count(report.rows, "pass")
    expected_watch = _status_count(report.rows, "watch")
    expected_block = _status_count(report.rows, "block")
    if report.pass_count != expected_pass:
        raise ValueError("pass_count must match rows")
    if report.watch_count != expected_watch:
        raise ValueError("watch_count must match rows")
    if report.block_count != expected_block:
        raise ValueError("block_count must match rows")
    if report.escalation_status != _report_status(report.rows):
        raise ValueError("escalation_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.average_contradiction_pressure != _average(
        tuple(row.contradiction_pressure for row in report.rows),
    ):
        raise ValueError("average_contradiction_pressure must match rows")
    expected_min_quorum = min(
        (row.source_class_quorum_score for row in report.rows),
        default=_ZERO,
    )
    if report.minimum_source_class_quorum_score != expected_min_quorum:
        raise ValueError("minimum_source_class_quorum_score must match rows")
    expected_max_age = max(
        (row.stale_conflict_age_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.max_stale_conflict_age_seconds != expected_max_age:
        raise ValueError("max_stale_conflict_age_seconds must match rows")
    expected_max_dissent = max(
        (row.specialist_dissent_score for row in report.rows),
        default=_ZERO,
    )
    if report.max_specialist_dissent_score != expected_max_dissent:
        raise ValueError("max_specialist_dissent_score must match rows")
    expected_max_manual = max(
        (row.manual_escalation_urgency for row in report.rows),
        default=_ZERO,
    )
    if report.max_manual_escalation_urgency != expected_max_manual:
        raise ValueError("max_manual_escalation_urgency must match rows")


def _normalize_observations(
    observations: Sequence[ResearchStrategySourceConflictEscalationObservation],
) -> tuple[ResearchStrategySourceConflictEscalationObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchStrategySourceConflictEscalationObservation] = []
    for observation in observations:
        if type(observation) is not ResearchStrategySourceConflictEscalationObservation:
            raise ValueError(
                "observations must contain "
                "ResearchStrategySourceConflictEscalationObservation",
            )
        normalized.append(observation)
    return tuple(
        sorted(
            normalized,
            key=lambda observation: (
                observation.conflict_group_hash,
                observation.input_row_number,
                observation.observed_at,
                observation.source_class,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchStrategySourceConflictEscalationRow],
) -> tuple[ResearchStrategySourceConflictEscalationRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchStrategySourceConflictEscalationRow] = []
    for row in rows:
        if type(row) is not ResearchStrategySourceConflictEscalationRow:
            raise ValueError(
                "rows must contain ResearchStrategySourceConflictEscalationRow",
            )
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.aggregate_row_number))


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
    return tuple(code for code in _REASON_CODE_SEQUENCE if code in normalized)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
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


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


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


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    seconds = (
        Decimal(delta.days) * _SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    )
    return _quantize(seconds)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchStrategySourceConflictEscalationReport,
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
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SOURCE_CONFLICT_ESCALATION_CONFIG_VERSION",
    "ResearchStrategySourceConflictEscalationConfig",
    "ResearchStrategySourceConflictEscalationObservation",
    "ResearchStrategySourceConflictEscalationReport",
    "ResearchStrategySourceConflictEscalationRow",
    "build_research_strategy_source_conflict_escalation_report",
)
