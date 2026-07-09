"""Report-only specialist signal drift gate for strategy-team research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_STRATEGY_TEAM_SPECIALIST_SIGNAL_DRIFT_GATE_REPORT_CONFIG_VERSION = (
    "research-strategy-team-specialist-signal-drift-gate-report-v0"
)

DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_RANK = {
    STATUS_BLOCK: 0,
    STATUS_WATCH: 1,
    STATUS_PASS: 2,
}

PASS_REASON = "signal_drift_gate_pass"
WATCH_REASON = "signal_drift_gate_watch"
BLOCK_REASON = "signal_drift_gate_block"
ABSOLUTE_SIGNAL_DRIFT_WATCH_REASON = "absolute_signal_drift_watch"
ABSOLUTE_SIGNAL_DRIFT_BLOCK_REASON = "absolute_signal_drift_block"
RANK_DRIFT_WATCH_REASON = "rank_drift_watch"
RANK_DRIFT_BLOCK_REASON = "rank_drift_block"
SPECIALIST_QUORUM_GAP_REASON = "specialist_quorum_gap"
STALE_SIGNAL_OBSERVATION_REASON = "stale_signal_observation"

STATUS_REASON_CODES = (PASS_REASON, WATCH_REASON, BLOCK_REASON)
BASE_DETAIL_REASON_CODES = (
    ABSOLUTE_SIGNAL_DRIFT_WATCH_REASON,
    ABSOLUTE_SIGNAL_DRIFT_BLOCK_REASON,
    RANK_DRIFT_WATCH_REASON,
    RANK_DRIFT_BLOCK_REASON,
    SPECIALIST_QUORUM_GAP_REASON,
    STALE_SIGNAL_OBSERVATION_REASON,
)
BASE_REASON_CODE_SET = frozenset((*STATUS_REASON_CODES, *BASE_DETAIL_REASON_CODES))
DETAIL_REASON_CODE_SEQUENCE = (
    ABSOLUTE_SIGNAL_DRIFT_BLOCK_REASON,
    RANK_DRIFT_BLOCK_REASON,
    SPECIALIST_QUORUM_GAP_REASON,
    STALE_SIGNAL_OBSERVATION_REASON,
    ABSOLUTE_SIGNAL_DRIFT_WATCH_REASON,
    RANK_DRIFT_WATCH_REASON,
)

UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        "://",
        "http",
        "url",
        "market",
        "slug",
        "question",
        "dsn",
        "postgres",
        "mysql",
        "sqlite",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "auth",
        "account",
        "broker",
        "buy",
        "sell",
        "live",
        "execute",
        "execution",
        "position",
        "recommend",
        "sizing",
        "persist",
        "storage",
        "file_path",
    ),
)

REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "quorum_gap_count",
    "stale_observation_count",
    "average_absolute_signal_drift",
    "max_absolute_signal_drift",
    "max_rank_drift",
)
ROW_DECIMAL_PAYLOAD_FIELDS = (
    "observation_age_seconds",
    "prior_signal_score",
    "current_signal_score",
    "absolute_signal_drift",
    "prior_rank",
    "current_rank",
    "rank_drift",
    "specialist_quorum_count",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "status",
    *REPORT_DECIMAL_PAYLOAD_FIELDS,
    "rows",
    "reason_code_counts",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "candidate_digest",
    "specialist_key",
    "observed_at",
    *ROW_DECIMAL_PAYLOAD_FIELDS,
    "status",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_CODE_COUNT_PAYLOAD_KEYS = (
    "reason_code",
    "row_count",
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_SPECIALIST_SIGNAL_DRIFT_GATE_REPORT_CONFIG_VERSION",
    "ResearchStrategyTeamSpecialistSignalDriftGateConfig",
    "ResearchStrategyTeamSpecialistSignalDriftGateInput",
    "ResearchStrategyTeamSpecialistSignalDriftGateRow",
    "ResearchStrategyTeamSpecialistSignalDriftGateReasonCodeCount",
    "ResearchStrategyTeamSpecialistSignalDriftGateReport",
    "build_research_strategy_team_specialist_signal_drift_gate_report",
    "research_strategy_team_specialist_signal_drift_gate_report_payload",
    "validate_research_strategy_team_specialist_signal_drift_gate_public_payload",
)


@dataclass(frozen=True)
class ResearchStrategyTeamSpecialistSignalDriftGateConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_TEAM_SPECIALIST_SIGNAL_DRIFT_GATE_REPORT_CONFIG_VERSION
    )
    watch_absolute_signal_drift: Decimal = Decimal("0.150000")
    block_absolute_signal_drift: Decimal = Decimal("0.300000")
    watch_rank_drift: Decimal = Decimal("3.000000")
    block_rank_drift: Decimal = Decimal("6.000000")
    min_specialist_quorum_count: Decimal = Decimal("2.000000")
    max_observation_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSpecialistSignalDriftGateConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_SPECIALIST_SIGNAL_DRIFT_GATE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_absolute_signal_drift",
            "block_absolute_signal_drift",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_rank_drift",
            "block_rank_drift",
            "min_specialist_quorum_count",
            "max_observation_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_specialist_quorum_count",
            _whole_decimal(
                "min_specialist_quorum_count",
                self.min_specialist_quorum_count,
            ),
        )
        if self.watch_absolute_signal_drift >= self.block_absolute_signal_drift:
            raise ValueError(
                "watch_absolute_signal_drift must be below "
                "block_absolute_signal_drift",
            )
        if self.watch_rank_drift >= self.block_rank_drift:
            raise ValueError("watch_rank_drift must be below block_rank_drift")
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyTeamSpecialistSignalDriftGateInput:
    candidate_ref: str
    specialist_key: str
    observed_at: datetime
    prior_signal_score: Decimal
    current_signal_score: Decimal
    prior_rank: Decimal
    current_rank: Decimal
    specialist_quorum_count: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSpecialistSignalDriftGateInput,
            "input",
        )
        _require_public_string("candidate_ref", self.candidate_ref)
        _require_public_string("specialist_key", self.specialist_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("prior_signal_score", "current_signal_score"):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("prior_rank", "current_rank", "specialist_quorum_count"):
            object.__setattr__(
                self,
                field_name,
                _whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyTeamSpecialistSignalDriftGateRow:
    candidate_digest: str
    specialist_key: str
    observed_at: datetime
    observation_age_seconds: Decimal
    prior_signal_score: Decimal
    current_signal_score: Decimal
    absolute_signal_drift: Decimal
    prior_rank: Decimal
    current_rank: Decimal
    rank_drift: Decimal
    specialist_quorum_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSpecialistSignalDriftGateRow,
            "row",
        )
        _require_candidate_digest("candidate_digest", self.candidate_digest)
        _require_public_string("specialist_key", self.specialist_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "observation_age_seconds",
            _nonnegative_decimal("observation_age_seconds", self.observation_age_seconds),
        )
        for field_name in (
            "prior_signal_score",
            "current_signal_score",
            "absolute_signal_drift",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("prior_rank", "current_rank", "rank_drift"):
            object.__setattr__(
                self,
                field_name,
                _whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "specialist_quorum_count",
            _whole_decimal("specialist_quorum_count", self.specialist_quorum_count),
        )
        _require_choice("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_zero=False),
        )
        _validate_row_consistency(self)
        require_paper_only_flags("row", self)
        _reject_unsafe_public_payload_text(
            "row public payload",
            _json_ready_without_digest(self),
        )
        _set_or_validate_digest(self, "row")


@dataclass(frozen=True)
class ResearchStrategyTeamSpecialistSignalDriftGateReasonCodeCount:
    reason_code: str
    row_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSpecialistSignalDriftGateReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "row_count", _count_decimal("row_count", self.row_count))
        require_paper_only_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchStrategyTeamSpecialistSignalDriftGateReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    quorum_gap_count: Decimal
    stale_observation_count: Decimal
    average_absolute_signal_drift: Decimal
    max_absolute_signal_drift: Decimal
    max_rank_drift: Decimal
    rows: tuple[ResearchStrategyTeamSpecialistSignalDriftGateRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyTeamSpecialistSignalDriftGateReasonCodeCount,
        ...
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSpecialistSignalDriftGateReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_SPECIALIST_SIGNAL_DRIFT_GATE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_choice("status", self.status, STATUSES)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "quorum_gap_count",
            "stale_observation_count",
            "average_absolute_signal_drift",
            "max_absolute_signal_drift",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "max_rank_drift", _whole_decimal("max_rank_drift", self.max_rank_drift))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        require_paper_only_flags("report", self)
        _reject_unsafe_public_payload_text(
            "report public payload",
            _json_ready_without_digest(self),
        )
        _set_or_validate_digest(self, "report")


def build_research_strategy_team_specialist_signal_drift_gate_report(
    rows: Iterable[ResearchStrategyTeamSpecialistSignalDriftGateInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyTeamSpecialistSignalDriftGateConfig | None = None,
) -> ResearchStrategyTeamSpecialistSignalDriftGateReport:
    cfg = config or ResearchStrategyTeamSpecialistSignalDriftGateConfig()
    if type(cfg) is not ResearchStrategyTeamSpecialistSignalDriftGateConfig:
        raise ValueError(
            "config must be exactly ResearchStrategyTeamSpecialistSignalDriftGateConfig",
        )
    require_paper_only_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(rows)
    report_rows = tuple(
        sorted(
            (
                _row_from_input(row, generated_at=generated_at_utc, config=cfg)
                for row in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _decimal_from_int(len(report_rows))
    return ResearchStrategyTeamSpecialistSignalDriftGateReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=_report_status(report_rows),
        row_count=row_count,
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        quorum_gap_count=_reason_count(report_rows, SPECIALIST_QUORUM_GAP_REASON),
        stale_observation_count=_reason_count(report_rows, STALE_SIGNAL_OBSERVATION_REASON),
        average_absolute_signal_drift=_average_absolute_signal_drift(report_rows),
        max_absolute_signal_drift=max(
            (row.absolute_signal_drift for row in report_rows),
            default=ZERO,
        ),
        max_rank_drift=max((row.rank_drift for row in report_rows), default=ZERO),
        rows=report_rows,
        reason_code_counts=_reason_code_counts(report_rows),
    )


def research_strategy_team_specialist_signal_drift_gate_report_payload(
    report: ResearchStrategyTeamSpecialistSignalDriftGateReport,
) -> "FrozenJsonObject":
    if type(report) is not ResearchStrategyTeamSpecialistSignalDriftGateReport:
        raise ValueError(
            "report must be exactly "
            "ResearchStrategyTeamSpecialistSignalDriftGateReport",
        )
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload_text("report public payload", payload)
    validate_research_strategy_team_specialist_signal_drift_gate_public_payload(
        payload,
    )
    return _freeze_json_object(payload)


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def validate_research_strategy_team_specialist_signal_drift_gate_public_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_payload_keys("public payload", payload, REPORT_PAYLOAD_KEYS)
    _reject_unsafe_public_payload_text("public payload", payload)
    report = _report_from_public_payload(payload)
    canonical_payload = json_ready_no_floats(report)
    if canonical_payload != payload:
        raise ValueError("public payload must use canonical values")
    return True


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyTeamSpecialistSignalDriftGateReport:
    return ResearchStrategyTeamSpecialistSignalDriftGateReport(
        generated_at=_payload_datetime(payload, "generated_at"),
        config_version=_payload_string(payload, "config_version"),
        status=_payload_string(payload, "status"),
        row_count=_payload_decimal(payload, "row_count"),
        pass_count=_payload_decimal(payload, "pass_count"),
        watch_count=_payload_decimal(payload, "watch_count"),
        block_count=_payload_decimal(payload, "block_count"),
        quorum_gap_count=_payload_decimal(payload, "quorum_gap_count"),
        stale_observation_count=_payload_decimal(
            payload,
            "stale_observation_count",
        ),
        average_absolute_signal_drift=_payload_decimal(
            payload,
            "average_absolute_signal_drift",
        ),
        max_absolute_signal_drift=_payload_decimal(
            payload,
            "max_absolute_signal_drift",
        ),
        max_rank_drift=_payload_decimal(payload, "max_rank_drift"),
        rows=tuple(
            _row_from_public_payload(row)
            for row in _payload_object_list(payload, "rows")
        ),
        reason_code_counts=tuple(
            _reason_code_count_from_public_payload(row)
            for row in _payload_object_list(payload, "reason_code_counts")
        ),
        derived_validation_digest=_payload_digest(
            payload,
            "derived_validation_digest",
        ),
        paper_only=_payload_true(payload, "paper_only"),
        report_only=_payload_true(payload, "report_only"),
        readonly=_payload_true(payload, "readonly"),
    )


def _row_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyTeamSpecialistSignalDriftGateRow:
    _require_payload_keys("row payload", payload, ROW_PAYLOAD_KEYS)
    return ResearchStrategyTeamSpecialistSignalDriftGateRow(
        candidate_digest=_payload_string(payload, "candidate_digest"),
        specialist_key=_payload_string(payload, "specialist_key"),
        observed_at=_payload_datetime(payload, "observed_at"),
        observation_age_seconds=_payload_decimal(
            payload,
            "observation_age_seconds",
        ),
        prior_signal_score=_payload_decimal(payload, "prior_signal_score"),
        current_signal_score=_payload_decimal(payload, "current_signal_score"),
        absolute_signal_drift=_payload_decimal(
            payload,
            "absolute_signal_drift",
        ),
        prior_rank=_payload_decimal(payload, "prior_rank"),
        current_rank=_payload_decimal(payload, "current_rank"),
        rank_drift=_payload_decimal(payload, "rank_drift"),
        specialist_quorum_count=_payload_decimal(
            payload,
            "specialist_quorum_count",
        ),
        status=_payload_string(payload, "status"),
        reason_codes=_payload_string_tuple(payload, "reason_codes"),
        derived_validation_digest=_payload_digest(
            payload,
            "derived_validation_digest",
        ),
        paper_only=_payload_true(payload, "paper_only"),
        report_only=_payload_true(payload, "report_only"),
        readonly=_payload_true(payload, "readonly"),
    )


def _reason_code_count_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyTeamSpecialistSignalDriftGateReasonCodeCount:
    _require_payload_keys(
        "reason code count payload",
        payload,
        REASON_CODE_COUNT_PAYLOAD_KEYS,
    )
    return ResearchStrategyTeamSpecialistSignalDriftGateReasonCodeCount(
        reason_code=_payload_string(payload, "reason_code"),
        row_count=_payload_decimal(payload, "row_count"),
        paper_only=_payload_true(payload, "paper_only"),
        report_only=_payload_true(payload, "report_only"),
        readonly=_payload_true(payload, "readonly"),
    )


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    if set(payload) != set(expected_keys):
        raise ValueError(f"{label} keys must match schema")


def _payload_required(payload: dict[str, Any], field_name: str) -> Any:
    try:
        return payload[field_name]
    except KeyError as exc:
        raise ValueError(f"{field_name} is required") from exc


def _payload_string(payload: dict[str, Any], field_name: str) -> str:
    value = _payload_required(payload, field_name)
    _require_public_string(field_name, value)
    return value


def _payload_decimal(payload: dict[str, Any], field_name: str) -> Decimal:
    value = _payload_required(payload, field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = _decimal(field_name, parsed)
    if value != str(normalized):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _payload_datetime(payload: dict[str, Any], field_name: str) -> datetime:
    value = _payload_string(payload, field_name)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _payload_string_tuple(
    payload: dict[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    value = _payload_required(payload, field_name)
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    values: list[str] = []
    for item in value:
        if type(item) is not str:
            raise ValueError(f"{field_name} must contain strings")
        values.append(item)
    return tuple(values)


def _payload_object_list(
    payload: dict[str, Any],
    field_name: str,
) -> tuple[dict[str, Any], ...]:
    value = _payload_required(payload, field_name)
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    values: list[dict[str, Any]] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError(f"{field_name} must contain JSON objects")
        values.append(item)
    return tuple(values)


def _payload_digest(payload: dict[str, Any], field_name: str) -> str:
    value = _payload_required(payload, field_name)
    _require_digest(field_name, value)
    return value


def _payload_true(payload: dict[str, Any], field_name: str) -> bool:
    value = _payload_required(payload, field_name)
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _row_from_input(
    row: ResearchStrategyTeamSpecialistSignalDriftGateInput,
    *,
    generated_at: datetime,
    config: ResearchStrategyTeamSpecialistSignalDriftGateConfig,
) -> ResearchStrategyTeamSpecialistSignalDriftGateRow:
    if row.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    absolute_signal_drift = abs(row.current_signal_score - row.prior_signal_score)
    rank_drift = abs(row.current_rank - row.prior_rank)
    observation_age_seconds = _duration_seconds(row.observed_at, generated_at)
    reason_codes = _reason_codes_for_values(
        absolute_signal_drift=absolute_signal_drift,
        rank_drift=rank_drift,
        specialist_quorum_count=row.specialist_quorum_count,
        observation_age_seconds=observation_age_seconds,
        upstream_reason_codes=row.upstream_reason_codes,
        config=config,
    )
    return ResearchStrategyTeamSpecialistSignalDriftGateRow(
        candidate_digest=_candidate_digest(row.candidate_ref),
        specialist_key=row.specialist_key,
        observed_at=row.observed_at,
        observation_age_seconds=observation_age_seconds,
        prior_signal_score=row.prior_signal_score,
        current_signal_score=row.current_signal_score,
        absolute_signal_drift=_quantize(absolute_signal_drift),
        prior_rank=row.prior_rank,
        current_rank=row.current_rank,
        rank_drift=_whole_decimal("rank_drift", rank_drift),
        specialist_quorum_count=row.specialist_quorum_count,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _reason_codes_for_values(
    *,
    absolute_signal_drift: Decimal,
    rank_drift: Decimal,
    specialist_quorum_count: Decimal,
    observation_age_seconds: Decimal,
    upstream_reason_codes: tuple[str, ...],
    config: ResearchStrategyTeamSpecialistSignalDriftGateConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if absolute_signal_drift >= config.block_absolute_signal_drift:
        block_reasons.append(ABSOLUTE_SIGNAL_DRIFT_BLOCK_REASON)
    elif absolute_signal_drift >= config.watch_absolute_signal_drift:
        watch_reasons.append(ABSOLUTE_SIGNAL_DRIFT_WATCH_REASON)
    if rank_drift >= config.block_rank_drift:
        block_reasons.append(RANK_DRIFT_BLOCK_REASON)
    elif rank_drift >= config.watch_rank_drift:
        watch_reasons.append(RANK_DRIFT_WATCH_REASON)
    if specialist_quorum_count < config.min_specialist_quorum_count:
        block_reasons.append(SPECIALIST_QUORUM_GAP_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        block_reasons.append(STALE_SIGNAL_OBSERVATION_REASON)
    upstream_reasons = tuple(f"upstream_{reason_code}" for reason_code in upstream_reason_codes)
    if block_reasons:
        return (BLOCK_REASON, *block_reasons, *watch_reasons, *upstream_reasons)
    if watch_reasons or upstream_reasons:
        return (WATCH_REASON, *watch_reasons, *upstream_reasons)
    return (PASS_REASON,)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == BLOCK_REASON:
        return STATUS_BLOCK
    if reason_codes[0] == WATCH_REASON:
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[ResearchStrategyTeamSpecialistSignalDriftGateRow, ...],
) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _normalize_inputs(
    rows: Iterable[ResearchStrategyTeamSpecialistSignalDriftGateInput],
) -> tuple[ResearchStrategyTeamSpecialistSignalDriftGateInput, ...]:
    if isinstance(rows, (str, bytes, dict)):
        raise ValueError("rows must be an iterable of inputs")
    normalized = tuple(rows)
    seen_pairs: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyTeamSpecialistSignalDriftGateInput:
            raise ValueError(
                "rows must contain ResearchStrategyTeamSpecialistSignalDriftGateInput",
            )
        require_paper_only_flags("input", row)
        key = (row.candidate_ref, row.specialist_key)
        if key in seen_pairs:
            raise ValueError("rows candidate_ref and specialist_key pairs must be unique")
        seen_pairs.add(key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyTeamSpecialistSignalDriftGateRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_pairs: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyTeamSpecialistSignalDriftGateRow:
            raise ValueError(
                "rows must contain ResearchStrategyTeamSpecialistSignalDriftGateRow",
            )
        require_paper_only_flags("row", row)
        key = (row.candidate_digest, row.specialist_key)
        if key in seen_pairs:
            raise ValueError("rows candidate_digest and specialist_key pairs must be unique")
        seen_pairs.add(key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchStrategyTeamSpecialistSignalDriftGateReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    seen_reason_codes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyTeamSpecialistSignalDriftGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyTeamSpecialistSignalDriftGateReasonCodeCount",
            )
        require_paper_only_flags("reason code count", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _row_sort_key(
    row: ResearchStrategyTeamSpecialistSignalDriftGateRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        STATUS_SORT_RANK[row.status],
        -row.absolute_signal_drift,
        -row.rank_drift,
        row.specialist_key,
        row.candidate_digest,
    )


def _reason_code_counts(
    rows: tuple[ResearchStrategyTeamSpecialistSignalDriftGateRow, ...],
) -> tuple[ResearchStrategyTeamSpecialistSignalDriftGateReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyTeamSpecialistSignalDriftGateReasonCodeCount(
                reason_code=PASS_REASON,
                row_count=ZERO,
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchStrategyTeamSpecialistSignalDriftGateReasonCodeCount(
            reason_code=reason_code,
            row_count=count,
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[ResearchStrategyTeamSpecialistSignalDriftGateRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchStrategyTeamSpecialistSignalDriftGateRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_absolute_signal_drift(
    rows: tuple[ResearchStrategyTeamSpecialistSignalDriftGateRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize(
        sum((row.absolute_signal_drift for row in rows), ZERO)
        / _decimal_from_int(len(rows)),
    )


def _validate_row_consistency(
    row: ResearchStrategyTeamSpecialistSignalDriftGateRow,
) -> None:
    expected_absolute_signal_drift = _quantize(
        abs(row.current_signal_score - row.prior_signal_score),
    )
    if row.absolute_signal_drift != expected_absolute_signal_drift:
        raise ValueError("absolute_signal_drift must match signal scores")
    expected_rank_drift = _whole_decimal("rank_drift", abs(row.current_rank - row.prior_rank))
    if row.rank_drift != expected_rank_drift:
        raise ValueError("rank_drift must match ranks")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.reason_codes[0] == PASS_REASON and len(row.reason_codes) != 1:
        raise ValueError("pass reason_codes must stand alone")
    detail_reasons = row.reason_codes[1:]
    if row.status != STATUS_PASS and not detail_reasons:
        raise ValueError("watch or block rows require detail reason_codes")


def _validate_report_consistency(
    report: ResearchStrategyTeamSpecialistSignalDriftGateReport,
) -> None:
    for row in report.rows:
        expected_observation_age_seconds = _duration_seconds(
            row.observed_at,
            report.generated_at,
        )
        if row.observation_age_seconds != expected_observation_age_seconds:
            raise ValueError(
                "observation_age_seconds must match observed_at and generated_at",
            )
    expected_values = {
        "row_count": _decimal_from_int(len(report.rows)),
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
        "quorum_gap_count": _reason_count(report.rows, SPECIALIST_QUORUM_GAP_REASON),
        "stale_observation_count": _reason_count(
            report.rows,
            STALE_SIGNAL_OBSERVATION_REASON,
        ),
        "average_absolute_signal_drift": _average_absolute_signal_drift(report.rows),
        "max_absolute_signal_drift": max(
            (row.absolute_signal_drift for row in report.rows),
            default=ZERO,
        ),
        "max_rank_drift": max((row.rank_drift for row in report.rows), default=ZERO),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_upstream_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("upstream_reason_codes must be a tuple or list")
    reason_codes = tuple(value)
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_string("upstream_reason_codes", reason_code)
        if any(fragment in reason_code.lower() for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError("upstream_reason_codes contain unsafe public text")
        if not reason_code.replace("_", "").isalnum() or reason_code.lower() != reason_code:
            raise ValueError("upstream_reason_codes must be lower snake case")
        if reason_code in seen:
            raise ValueError("upstream_reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(sorted(normalized))


def _normalize_reason_codes(value: object, *, allow_zero: bool) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        if allow_zero:
            return ()
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    if reason_codes[0] not in STATUS_REASON_CODES:
        raise ValueError("reason_codes must begin with a status reason")
    if reason_codes[0] == PASS_REASON and len(reason_codes) != 1:
        raise ValueError("pass reason_codes must stand alone")
    if reason_codes[0] != PASS_REASON and len(reason_codes) == 1:
        raise ValueError("watch or block reason_codes require detail reasons")
    if reason_codes[0] == WATCH_REASON and any(
        reason
        in (
            ABSOLUTE_SIGNAL_DRIFT_BLOCK_REASON,
            RANK_DRIFT_BLOCK_REASON,
            SPECIALIST_QUORUM_GAP_REASON,
            STALE_SIGNAL_OBSERVATION_REASON,
        )
        for reason in reason_codes[1:]
    ):
        raise ValueError("watch reason_codes must not contain block reasons")
    return (
        reason_codes[0],
        *tuple(sorted(reason_codes[1:], key=_reason_code_sort_key)),
    )


def _reason_code_sort_key(reason_code: str) -> tuple[Decimal, str]:
    if reason_code in DETAIL_REASON_CODE_SEQUENCE:
        return (
            _decimal_from_int(DETAIL_REASON_CODE_SEQUENCE.index(reason_code)),
            reason_code,
        )
    return (_decimal_from_int(len(DETAIL_REASON_CODE_SEQUENCE)), reason_code)


def _set_or_validate_digest(value: object, label: str) -> None:
    current_digest = getattr(value, "derived_validation_digest")
    if current_digest == "":
        object.__setattr__(
            value,
            "derived_validation_digest",
            _derived_validation_digest(value, label),
        )
        return
    _require_digest("derived_validation_digest", current_digest)
    if current_digest != _derived_validation_digest(value, label):
        raise ValueError("derived_validation_digest does not match payload")


def _derived_validation_digest(value: object, label: str) -> str:
    ready_value = _json_ready_without_digest(value)
    _reject_unsafe_public_payload_text(f"{label} public payload", ready_value)
    canonical_payload = json.dumps(
        ready_value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready_without_digest(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass instance")
    ready = json_ready_no_floats(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    ready.pop("derived_validation_digest", None)
    return ready


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _reject_unsafe_public_payload_text(label: str, payload: object) -> None:
    for value in _iter_string_values(payload):
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"unsafe public payload text in {label}")


def _iter_string_values(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_iter_string_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_iter_string_values(item))
        return tuple(values)
    return ()


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    start = _as_utc("started_at", started_at)
    finish = _as_utc("finished_at", finished_at)
    if finish < start:
        raise ValueError("duration seconds must be nonnegative")
    delta = finish - start
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize(seconds)


def _candidate_digest(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _decimal_from_int(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _count_decimal(name: str, value: object) -> Decimal:
    normalized = _whole_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _whole_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _probability_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be quantizable") from exc


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_choice(name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        joined_choices = ", ".join(choices)
        raise ValueError(f"{name} must be one of: {joined_choices}")


def _require_reason_code(name: str, value: object) -> None:
    _require_public_string(name, value)
    if value in BASE_REASON_CODE_SET:
        return
    if value.startswith("upstream_"):
        tail = value.removeprefix("upstream_")
        if tail and tail.replace("_", "").isalnum() and tail.lower() == tail:
            if not any(fragment in tail for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
                return
    raise ValueError(f"{name} must be a known reason code")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a 64-character hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be lowercase hex")


def _require_candidate_digest(name: str, value: object) -> None:
    if type(value) is not str or not value.startswith("sha256:"):
        raise ValueError(f"{name} must be a sha256 digest")
    _require_digest(name, value.removeprefix("sha256:"))
