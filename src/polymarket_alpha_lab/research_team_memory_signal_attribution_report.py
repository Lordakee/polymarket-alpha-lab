"""Pure report-only attribution for team memory signal usefulness."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_MEMORY_SIGNAL_ATTRIBUTION_REPORT_CONFIG_VERSION",
    "MEMORY_SIGNAL_ATTRIBUTION_STATUSES",
    "ResearchTeamMemorySignalAttributionConfig",
    "ResearchTeamMemorySignalAttributionInput",
    "ResearchTeamMemorySignalAttributionReasonCodeCount",
    "ResearchTeamMemorySignalAttributionReport",
    "ResearchTeamMemorySignalAttributionRow",
    "build_research_team_memory_signal_attribution_report",
    "research_team_memory_signal_attribution_report_payload",
    "validate_research_team_memory_signal_attribution_report_payload",
)


DEFAULT_RESEARCH_TEAM_MEMORY_SIGNAL_ATTRIBUTION_REPORT_CONFIG_VERSION = (
    "research-team-memory-signal-attribution-report-v0"
)
MEMORY_SIGNAL_ATTRIBUTION_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
NEGATIVE_ONE = Decimal("-1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
HEX_CHARS = frozenset("0123456789abcdef")
PUBLIC_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,95}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

STATUS_ORDER = {"block": 0, "watch": 1, "pass": 2}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")

REASON_CODE_PRIORITY = (
    "memory_signal_attribution_report_block",
    "memory_signal_attribution_report_watch",
    "memory_signal_attribution_report_pass",
    "memory_signal_attribution_block",
    "memory_signal_attribution_watch",
    "memory_signal_attribution_pass",
    "no_decisions_observed",
    "memory_signal_helped",
    "memory_signal_hurt",
    "memory_signal_mixed",
    "historical_calibration_support",
    "historical_calibration_drag",
    "evidence_contribution_support",
    "evidence_contribution_drag",
    "override_usefulness_support",
    "override_usefulness_drag",
    "no_override_history",
    "stale_memory_penalty_watch",
    "stale_memory_penalty_block",
    "cross_domain_conflict_pressure_watch",
    "cross_domain_conflict_pressure_block",
    "empty_memory_signals",
)

UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candi" + "date",
        "mar" + "ket",
        "sl" + "ug",
        "quest" + "ion",
        "u" + "rl",
        "te" + "xt",
        "d" + "sn",
        "ta" + "ble",
        "to" + "ken",
        "wal" + "let",
        "or" + "der",
        "tr" + "ade",
        "li" + "ve",
        "data" + "base",
        "auth",
        "secret",
        "private",
        "signing",
        "http",
        "socket",
        "sql",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamMemorySignalAttributionConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_TEAM_MEMORY_SIGNAL_ATTRIBUTION_REPORT_CONFIG_VERSION
    pass_attribution_score: Decimal = Decimal("0.650000")
    block_attribution_score: Decimal = Decimal("0.350000")
    watch_stale_memory_age_hours: Decimal = Decimal("72.000000")
    block_stale_memory_age_hours: Decimal = Decimal("168.000000")
    watch_cross_domain_conflict_pressure: Decimal = Decimal("0.250000")
    block_cross_domain_conflict_pressure: Decimal = Decimal("0.600000")
    historical_calibration_weight: Decimal = Decimal("0.250000")
    evidence_contribution_weight: Decimal = Decimal("0.250000")
    override_usefulness_weight: Decimal = Decimal("0.200000")
    decision_help_weight: Decimal = Decimal("0.200000")
    stale_memory_penalty_weight: Decimal = Decimal("0.050000")
    cross_domain_conflict_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemorySignalAttributionConfig, "config")
        _require_config_version(self.config_version)
        for field_name in (
            "pass_attribution_score",
            "block_attribution_score",
            "watch_cross_domain_conflict_pressure",
            "block_cross_domain_conflict_pressure",
            "historical_calibration_weight",
            "evidence_contribution_weight",
            "override_usefulness_weight",
            "decision_help_weight",
            "stale_memory_penalty_weight",
            "cross_domain_conflict_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_stale_memory_age_hours",
            "block_stale_memory_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_attribution_score <= self.block_attribution_score:
            raise ValueError("pass_attribution_score must exceed block_attribution_score")
        if self.block_stale_memory_age_hours <= self.watch_stale_memory_age_hours:
            raise ValueError(
                "block_stale_memory_age_hours must exceed watch_stale_memory_age_hours",
            )
        if (
            self.block_cross_domain_conflict_pressure
            <= self.watch_cross_domain_conflict_pressure
        ):
            raise ValueError(
                "block_cross_domain_conflict_pressure must exceed "
                "watch_cross_domain_conflict_pressure",
            )
        positive_weight = (
            self.historical_calibration_weight
            + self.evidence_contribution_weight
            + self.override_usefulness_weight
            + self.decision_help_weight
        )
        if positive_weight <= ZERO:
            raise ValueError("positive attribution weights must be nonzero")
        _require_hard_flags("config", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchTeamMemorySignalAttributionInput(_FinalPublicDataclass):
    memory_signal_key: str
    domain_key: str
    decision_count: Decimal
    helped_decision_count: Decimal
    hurt_decision_count: Decimal
    historical_calibration_error_sum: Decimal
    evidence_contribution_sum: Decimal
    override_decision_count: Decimal
    helpful_override_count: Decimal
    stale_memory_age_hours_sum: Decimal
    cross_domain_conflict_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemorySignalAttributionInput, "input")
        _require_public_code("memory_signal_key", self.memory_signal_key)
        _require_public_code("domain_key", self.domain_key)
        for field_name in (
            "decision_count",
            "helped_decision_count",
            "hurt_decision_count",
            "override_decision_count",
            "helpful_override_count",
            "cross_domain_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "historical_calibration_error_sum",
            "evidence_contribution_sum",
            "stale_memory_age_hours_sum",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _validate_input(self)
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchTeamMemorySignalAttributionRow(_FinalPublicDataclass):
    memory_signal_digest: str
    domain_key: str
    decision_count: Decimal
    helped_decision_count: Decimal
    hurt_decision_count: Decimal
    historical_calibration_error_sum: Decimal
    evidence_contribution_sum: Decimal
    override_decision_count: Decimal
    helpful_override_count: Decimal
    stale_memory_age_hours_sum: Decimal
    cross_domain_conflict_count: Decimal
    historical_calibration_score: Decimal
    evidence_contribution_score: Decimal
    override_usefulness_score: Decimal
    stale_memory_penalty: Decimal
    cross_domain_conflict_pressure: Decimal
    net_help_ratio: Decimal
    attribution_score: Decimal
    attribution_status: str
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemorySignalAttributionRow, "row")
        _require_digest_reference("memory_signal_digest", self.memory_signal_digest)
        _require_public_code("domain_key", self.domain_key)
        for field_name in (
            "decision_count",
            "helped_decision_count",
            "hurt_decision_count",
            "override_decision_count",
            "helpful_override_count",
            "cross_domain_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "historical_calibration_error_sum",
            "evidence_contribution_sum",
            "stale_memory_age_hours_sum",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "historical_calibration_score",
            "evidence_contribution_score",
            "override_usefulness_score",
            "stale_memory_penalty",
            "cross_domain_conflict_pressure",
            "attribution_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "net_help_ratio",
            _require_signed_unit_decimal("net_help_ratio", self.net_help_ratio),
        )
        _require_status("attribution_status", self.attribution_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchTeamMemorySignalAttributionReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamMemorySignalAttributionReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchTeamMemorySignalAttributionReport(_FinalPublicDataclass):
    generated_at: datetime
    config: ResearchTeamMemorySignalAttributionConfig
    config_version: str
    report_status: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    helped_signal_count: Decimal
    hurt_signal_count: Decimal
    average_attribution_score: Decimal
    average_historical_calibration_score: Decimal
    average_evidence_contribution_score: Decimal
    average_override_usefulness_score: Decimal
    max_stale_memory_penalty: Decimal
    max_cross_domain_conflict_pressure: Decimal
    rows: tuple[ResearchTeamMemorySignalAttributionRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamMemorySignalAttributionReasonCodeCount, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemorySignalAttributionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        if type(self.config) is not ResearchTeamMemorySignalAttributionConfig:
            raise ValueError("config must be ResearchTeamMemorySignalAttributionConfig")
        _require_untampered_public_dataclass(self.config, "config")
        _validate_config(self.config)
        _require_config_version(self.config_version)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        _require_status("report_status", self.report_status)
        for field_name in (
            "signal_count",
            "pass_count",
            "watch_count",
            "block_count",
            "helped_signal_count",
            "hurt_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_attribution_score",
            "average_historical_calibration_score",
            "average_evidence_contribution_score",
            "average_override_usefulness_score",
            "max_stale_memory_penalty",
            "max_cross_domain_conflict_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_sha256_hex("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _store_public_snapshot(self)

    @property
    def payload(self) -> dict[str, Any]:
        _require_untampered_public_dataclass(self.config, "config")
        for row in self.rows:
            _require_untampered_public_dataclass(row, "row")
        for count in self.reason_code_counts:
            _require_untampered_public_dataclass(count, "reason_code_count")
        _require_untampered_public_dataclass(self, "report")
        _validate_report(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        validate_research_team_memory_signal_attribution_report_payload(payload)
        return payload


def build_research_team_memory_signal_attribution_report(
    signals: Sequence[ResearchTeamMemorySignalAttributionInput],
    *,
    generated_at: datetime,
    config: ResearchTeamMemorySignalAttributionConfig | None = None,
) -> ResearchTeamMemorySignalAttributionReport:
    """Build a deterministic in-memory attribution report for team memory signals."""

    if config is None:
        config = ResearchTeamMemorySignalAttributionConfig()
    if type(config) is not ResearchTeamMemorySignalAttributionConfig:
        raise ValueError("config must be ResearchTeamMemorySignalAttributionConfig")
    _require_untampered_public_dataclass(config, "config")
    _validate_config(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_inputs(signals)
    for signal in normalized_signals:
        if signal.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = _build_rows(normalized_signals, config)
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config": config,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "signal_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "helped_signal_count": _decimal_count(
            sum(1 for row in rows if row.helped_decision_count > row.hurt_decision_count),
        ),
        "hurt_signal_count": _decimal_count(
            sum(1 for row in rows if row.hurt_decision_count > row.helped_decision_count),
        ),
        "average_attribution_score": _average(
            tuple(row.attribution_score for row in rows),
        ),
        "average_historical_calibration_score": _average(
            tuple(row.historical_calibration_score for row in rows),
        ),
        "average_evidence_contribution_score": _average(
            tuple(row.evidence_contribution_score for row in rows),
        ),
        "average_override_usefulness_score": _average(
            tuple(row.override_usefulness_score for row in rows),
        ),
        "max_stale_memory_penalty": max(
            (row.stale_memory_penalty for row in rows),
            default=ZERO,
        ),
        "max_cross_domain_conflict_pressure": max(
            (row.cross_domain_conflict_pressure for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "reason_code_counts": reason_code_counts,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamMemorySignalAttributionReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_memory_signal_attribution_report_payload(
    report: ResearchTeamMemorySignalAttributionReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamMemorySignalAttributionReport:
        return report.payload
    if type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        validate_research_team_memory_signal_attribution_report_payload(payload)
        return payload
    raise ValueError(
        "report must be a ResearchTeamMemorySignalAttributionReport or exact dict payload",
    )


def validate_research_team_memory_signal_attribution_report_payload(
    payload: Mapping[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be an exact dict")
    _require_payload_schema(
        payload,
        _public_payload_keys(ResearchTeamMemorySignalAttributionReport),
        "payload",
    )
    _require_nested_payload_schemas(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _reject_payload_values("payload", payload)
    _require_mapping_flags("payload", payload)
    digest = payload["derived_validation_digest"]
    _require_sha256_hex("derived_validation_digest", digest)
    values_without_digest = {
        key: payload[key]
        for key in _public_payload_keys(ResearchTeamMemorySignalAttributionReport)
        if key != "derived_validation_digest"
    }
    expected_digest = _report_digest_from_values(values_without_digest)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    _report_from_public_payload(payload)


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchTeamMemorySignalAttributionReport:
    config = _config_from_public_payload(payload["config"], "config")
    rows = _public_rows(payload["rows"], "rows")
    for row in rows:
        _validate_row_against_config(row, config)
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be in canonical row order")
    reason_codes = _public_reason_codes(payload["reason_codes"], "reason_codes")
    reason_code_counts = _public_reason_code_counts(
        payload["reason_code_counts"],
        "reason_code_counts",
    )
    return ResearchTeamMemorySignalAttributionReport(
        generated_at=_public_datetime(
            "generated_at",
            payload["generated_at"],
            "generated_at",
        ),
        config=config,
        config_version=_public_config_version(
            payload["config_version"],
            "config_version",
        ),
        report_status=_public_status(
            "report_status",
            payload["report_status"],
            "report_status",
        ),
        signal_count=_public_count_decimal(
            "signal_count",
            payload["signal_count"],
            "signal_count",
        ),
        pass_count=_public_count_decimal(
            "pass_count",
            payload["pass_count"],
            "pass_count",
        ),
        watch_count=_public_count_decimal(
            "watch_count",
            payload["watch_count"],
            "watch_count",
        ),
        block_count=_public_count_decimal(
            "block_count",
            payload["block_count"],
            "block_count",
        ),
        helped_signal_count=_public_count_decimal(
            "helped_signal_count",
            payload["helped_signal_count"],
            "helped_signal_count",
        ),
        hurt_signal_count=_public_count_decimal(
            "hurt_signal_count",
            payload["hurt_signal_count"],
            "hurt_signal_count",
        ),
        average_attribution_score=_public_unit_decimal(
            "average_attribution_score",
            payload["average_attribution_score"],
            "average_attribution_score",
        ),
        average_historical_calibration_score=_public_unit_decimal(
            "average_historical_calibration_score",
            payload["average_historical_calibration_score"],
            "average_historical_calibration_score",
        ),
        average_evidence_contribution_score=_public_unit_decimal(
            "average_evidence_contribution_score",
            payload["average_evidence_contribution_score"],
            "average_evidence_contribution_score",
        ),
        average_override_usefulness_score=_public_unit_decimal(
            "average_override_usefulness_score",
            payload["average_override_usefulness_score"],
            "average_override_usefulness_score",
        ),
        max_stale_memory_penalty=_public_unit_decimal(
            "max_stale_memory_penalty",
            payload["max_stale_memory_penalty"],
            "max_stale_memory_penalty",
        ),
        max_cross_domain_conflict_pressure=_public_unit_decimal(
            "max_cross_domain_conflict_pressure",
            payload["max_cross_domain_conflict_pressure"],
            "max_cross_domain_conflict_pressure",
        ),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        derived_validation_digest=_require_sha256_hex(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_public_true_flag(payload["paper_only"], "paper_only"),
        report_only=_public_true_flag(payload["report_only"], "report_only"),
        readonly=_public_true_flag(payload["readonly"], "readonly"),
    )


def _config_from_public_payload(
    value: object,
    path: str,
) -> ResearchTeamMemorySignalAttributionConfig:
    _require_payload_schema(
        value,
        _public_payload_keys(ResearchTeamMemorySignalAttributionConfig),
        path,
    )
    return ResearchTeamMemorySignalAttributionConfig(
        config_version=_public_config_version(
            value["config_version"],
            f"{path}.config_version",
        ),
        pass_attribution_score=_public_unit_decimal(
            "pass_attribution_score",
            value["pass_attribution_score"],
            f"{path}.pass_attribution_score",
        ),
        block_attribution_score=_public_unit_decimal(
            "block_attribution_score",
            value["block_attribution_score"],
            f"{path}.block_attribution_score",
        ),
        watch_stale_memory_age_hours=_public_positive_decimal(
            "watch_stale_memory_age_hours",
            value["watch_stale_memory_age_hours"],
            f"{path}.watch_stale_memory_age_hours",
        ),
        block_stale_memory_age_hours=_public_positive_decimal(
            "block_stale_memory_age_hours",
            value["block_stale_memory_age_hours"],
            f"{path}.block_stale_memory_age_hours",
        ),
        watch_cross_domain_conflict_pressure=_public_unit_decimal(
            "watch_cross_domain_conflict_pressure",
            value["watch_cross_domain_conflict_pressure"],
            f"{path}.watch_cross_domain_conflict_pressure",
        ),
        block_cross_domain_conflict_pressure=_public_unit_decimal(
            "block_cross_domain_conflict_pressure",
            value["block_cross_domain_conflict_pressure"],
            f"{path}.block_cross_domain_conflict_pressure",
        ),
        historical_calibration_weight=_public_unit_decimal(
            "historical_calibration_weight",
            value["historical_calibration_weight"],
            f"{path}.historical_calibration_weight",
        ),
        evidence_contribution_weight=_public_unit_decimal(
            "evidence_contribution_weight",
            value["evidence_contribution_weight"],
            f"{path}.evidence_contribution_weight",
        ),
        override_usefulness_weight=_public_unit_decimal(
            "override_usefulness_weight",
            value["override_usefulness_weight"],
            f"{path}.override_usefulness_weight",
        ),
        decision_help_weight=_public_unit_decimal(
            "decision_help_weight",
            value["decision_help_weight"],
            f"{path}.decision_help_weight",
        ),
        stale_memory_penalty_weight=_public_unit_decimal(
            "stale_memory_penalty_weight",
            value["stale_memory_penalty_weight"],
            f"{path}.stale_memory_penalty_weight",
        ),
        cross_domain_conflict_weight=_public_unit_decimal(
            "cross_domain_conflict_weight",
            value["cross_domain_conflict_weight"],
            f"{path}.cross_domain_conflict_weight",
        ),
        paper_only=_public_true_flag(value["paper_only"], f"{path}.paper_only"),
        report_only=_public_true_flag(value["report_only"], f"{path}.report_only"),
        readonly=_public_true_flag(value["readonly"], f"{path}.readonly"),
    )


def _row_from_public_payload(
    value: object,
    path: str,
) -> ResearchTeamMemorySignalAttributionRow:
    _require_payload_schema(
        value,
        _public_payload_keys(ResearchTeamMemorySignalAttributionRow),
        path,
    )
    return ResearchTeamMemorySignalAttributionRow(
        memory_signal_digest=_public_digest_reference(
            "memory_signal_digest",
            value["memory_signal_digest"],
            f"{path}.memory_signal_digest",
        ),
        domain_key=_public_code("domain_key", value["domain_key"], f"{path}.domain_key"),
        decision_count=_public_count_decimal(
            "decision_count",
            value["decision_count"],
            f"{path}.decision_count",
        ),
        helped_decision_count=_public_count_decimal(
            "helped_decision_count",
            value["helped_decision_count"],
            f"{path}.helped_decision_count",
        ),
        hurt_decision_count=_public_count_decimal(
            "hurt_decision_count",
            value["hurt_decision_count"],
            f"{path}.hurt_decision_count",
        ),
        historical_calibration_error_sum=_public_nonnegative_decimal(
            "historical_calibration_error_sum",
            value["historical_calibration_error_sum"],
            f"{path}.historical_calibration_error_sum",
        ),
        evidence_contribution_sum=_public_nonnegative_decimal(
            "evidence_contribution_sum",
            value["evidence_contribution_sum"],
            f"{path}.evidence_contribution_sum",
        ),
        override_decision_count=_public_count_decimal(
            "override_decision_count",
            value["override_decision_count"],
            f"{path}.override_decision_count",
        ),
        helpful_override_count=_public_count_decimal(
            "helpful_override_count",
            value["helpful_override_count"],
            f"{path}.helpful_override_count",
        ),
        stale_memory_age_hours_sum=_public_nonnegative_decimal(
            "stale_memory_age_hours_sum",
            value["stale_memory_age_hours_sum"],
            f"{path}.stale_memory_age_hours_sum",
        ),
        cross_domain_conflict_count=_public_count_decimal(
            "cross_domain_conflict_count",
            value["cross_domain_conflict_count"],
            f"{path}.cross_domain_conflict_count",
        ),
        historical_calibration_score=_public_unit_decimal(
            "historical_calibration_score",
            value["historical_calibration_score"],
            f"{path}.historical_calibration_score",
        ),
        evidence_contribution_score=_public_unit_decimal(
            "evidence_contribution_score",
            value["evidence_contribution_score"],
            f"{path}.evidence_contribution_score",
        ),
        override_usefulness_score=_public_unit_decimal(
            "override_usefulness_score",
            value["override_usefulness_score"],
            f"{path}.override_usefulness_score",
        ),
        stale_memory_penalty=_public_unit_decimal(
            "stale_memory_penalty",
            value["stale_memory_penalty"],
            f"{path}.stale_memory_penalty",
        ),
        cross_domain_conflict_pressure=_public_unit_decimal(
            "cross_domain_conflict_pressure",
            value["cross_domain_conflict_pressure"],
            f"{path}.cross_domain_conflict_pressure",
        ),
        net_help_ratio=_public_signed_unit_decimal(
            "net_help_ratio",
            value["net_help_ratio"],
            f"{path}.net_help_ratio",
        ),
        attribution_score=_public_unit_decimal(
            "attribution_score",
            value["attribution_score"],
            f"{path}.attribution_score",
        ),
        attribution_status=_public_status(
            "attribution_status",
            value["attribution_status"],
            f"{path}.attribution_status",
        ),
        observed_at=_public_datetime(
            "observed_at",
            value["observed_at"],
            f"{path}.observed_at",
        ),
        reason_codes=_public_reason_codes(value["reason_codes"], f"{path}.reason_codes"),
        paper_only=_public_true_flag(value["paper_only"], f"{path}.paper_only"),
        report_only=_public_true_flag(value["report_only"], f"{path}.report_only"),
        readonly=_public_true_flag(value["readonly"], f"{path}.readonly"),
    )


def _reason_code_count_from_public_payload(
    value: object,
    path: str,
) -> ResearchTeamMemorySignalAttributionReasonCodeCount:
    _require_payload_schema(
        value,
        _public_payload_keys(ResearchTeamMemorySignalAttributionReasonCodeCount),
        path,
    )
    return ResearchTeamMemorySignalAttributionReasonCodeCount(
        reason_code=_public_reason_code(
            "reason_code",
            value["reason_code"],
            f"{path}.reason_code",
        ),
        count=_public_count_decimal("count", value["count"], f"{path}.count"),
        paper_only=_public_true_flag(value["paper_only"], f"{path}.paper_only"),
        report_only=_public_true_flag(value["report_only"], f"{path}.report_only"),
        readonly=_public_true_flag(value["readonly"], f"{path}.readonly"),
    )


def _public_rows(
    value: object,
    path: str,
) -> tuple[ResearchTeamMemorySignalAttributionRow, ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    return tuple(
        _row_from_public_payload(item, f"{path}[{index}]")
        for index, item in enumerate(value)
    )


def _public_reason_code_counts(
    value: object,
    path: str,
) -> tuple[ResearchTeamMemorySignalAttributionReasonCodeCount, ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    counts = tuple(
        _reason_code_count_from_public_payload(item, f"{path}[{index}]")
        for index, item in enumerate(value)
    )
    if tuple(
        sorted(
            counts,
            key=lambda item: REASON_CODE_PRIORITY.index(item.reason_code),
        ),
    ) != counts:
        raise ValueError(f"{path} must be in canonical reason_code order")
    return counts


def _public_payload_keys(dataclass_type: type[object]) -> tuple[str, ...]:
    return tuple(field.name for field in fields(dataclass_type))


def _require_payload_schema(
    value: object,
    expected_keys: tuple[str, ...],
    path: str,
) -> None:
    if type(value) is not dict:
        raise ValueError(f"{path} must be an exact dict")
    actual_keys = tuple(value)
    if actual_keys == expected_keys:
        return
    if set(actual_keys) != set(expected_keys):
        raise ValueError(f"{path} schema must match expected fields")
    raise ValueError(f"{path} schema order must match expected fields")


def _require_nested_payload_schemas(payload: dict[str, Any]) -> None:
    _require_payload_schema(
        payload["config"],
        _public_payload_keys(ResearchTeamMemorySignalAttributionConfig),
        "config",
    )
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for index, row in enumerate(rows):
        _require_payload_schema(
            row,
            _public_payload_keys(ResearchTeamMemorySignalAttributionRow),
            f"rows[{index}]",
        )
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for index, count in enumerate(reason_code_counts):
        _require_payload_schema(
            count,
            _public_payload_keys(ResearchTeamMemorySignalAttributionReasonCodeCount),
            f"reason_code_counts[{index}]",
        )


def _public_config_version(value: object, path: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{path} must be the supported config_version")
    return _require_config_version(value)


def _public_code(field_name: str, value: object, path: str) -> str:
    try:
        return _require_public_code(field_name, value)
    except ValueError as exc:
        raise ValueError(f"{path} must be a public code") from exc


def _public_digest_reference(field_name: str, value: object, path: str) -> str:
    try:
        return _require_digest_reference(field_name, value)
    except ValueError as exc:
        raise ValueError(f"{path} must be a sha256 reference") from exc


def _public_reason_code(field_name: str, value: object, path: str) -> str:
    try:
        return _require_reason_code(field_name, value)
    except ValueError as exc:
        raise ValueError(f"{path} must be a supported reason_code") from exc


def _public_status(field_name: str, value: object, path: str) -> str:
    try:
        return _require_status(field_name, value)
    except ValueError as exc:
        raise ValueError(f"{path} must be pass, watch, or block") from exc


def _public_datetime(field_name: str, value: object, path: str) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{path} must be a canonical UTC datetime string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{path} has unsafe public value")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{path} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{path} must be a canonical UTC datetime string")
    return normalized


def _public_count_decimal(field_name: str, value: object, path: str) -> Decimal:
    return _public_normalized_decimal(field_name, value, path, _require_count_decimal)


def _public_nonnegative_decimal(field_name: str, value: object, path: str) -> Decimal:
    return _public_normalized_decimal(
        field_name,
        value,
        path,
        _require_nonnegative_decimal,
    )


def _public_positive_decimal(field_name: str, value: object, path: str) -> Decimal:
    return _public_normalized_decimal(field_name, value, path, _require_positive_decimal)


def _public_unit_decimal(field_name: str, value: object, path: str) -> Decimal:
    return _public_normalized_decimal(field_name, value, path, _require_unit_decimal)


def _public_signed_unit_decimal(field_name: str, value: object, path: str) -> Decimal:
    return _public_normalized_decimal(
        field_name,
        value,
        path,
        _require_signed_unit_decimal,
    )


def _public_normalized_decimal(
    field_name: str,
    value: object,
    path: str,
    normalizer: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{path} must be a Decimal-derived string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{path} has unsafe public value")
    try:
        raw = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{path} must be a Decimal-derived string") from exc
    try:
        normalized = normalizer(field_name, raw)
    except ValueError as exc:
        raise ValueError(f"{path} {exc}") from exc
    if value != str(normalized):
        raise ValueError(f"{path} must be a canonical Decimal-derived string")
    return normalized


def _public_reason_codes(value: object, path: str) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    reason_codes = tuple(
        _public_reason_code("reason_code", item, f"{path}[{index}]")
        for index, item in enumerate(value)
    )
    normalized = _normalize_reason_codes(reason_codes)
    if reason_codes != normalized:
        raise ValueError(f"{path} must be canonical reason_codes")
    return normalized


def _public_true_flag(value: object, path: str) -> bool:
    if value is not True:
        raise ValueError(f"{path} must be True")
    return True


def _build_rows(
    signals: tuple[ResearchTeamMemorySignalAttributionInput, ...],
    config: ResearchTeamMemorySignalAttributionConfig,
) -> tuple[ResearchTeamMemorySignalAttributionRow, ...]:
    grouped: dict[tuple[str, str], list[ResearchTeamMemorySignalAttributionInput]] = {}
    for signal in signals:
        grouped.setdefault((signal.memory_signal_key, signal.domain_key), []).append(signal)
    rows = tuple(
        _row_for_group(memory_signal_key, domain_key, tuple(group), config)
        for (memory_signal_key, domain_key), group in sorted(grouped.items())
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _row_for_group(
    memory_signal_key: str,
    domain_key: str,
    signals: tuple[ResearchTeamMemorySignalAttributionInput, ...],
    config: ResearchTeamMemorySignalAttributionConfig,
) -> ResearchTeamMemorySignalAttributionRow:
    decision_count = _sum_decimal(tuple(item.decision_count for item in signals))
    helped_count = _sum_decimal(tuple(item.helped_decision_count for item in signals))
    hurt_count = _sum_decimal(tuple(item.hurt_decision_count for item in signals))
    historical_error_sum = _sum_decimal(
        tuple(item.historical_calibration_error_sum for item in signals),
    )
    evidence_sum = _sum_decimal(tuple(item.evidence_contribution_sum for item in signals))
    override_count = _sum_decimal(tuple(item.override_decision_count for item in signals))
    helpful_override_count = _sum_decimal(
        tuple(item.helpful_override_count for item in signals),
    )
    stale_age_sum = _sum_decimal(tuple(item.stale_memory_age_hours_sum for item in signals))
    conflict_count = _sum_decimal(
        tuple(item.cross_domain_conflict_count for item in signals),
    )

    derived = _row_derived_values(
        decision_count=decision_count,
        helped_count=helped_count,
        hurt_count=hurt_count,
        historical_error_sum=historical_error_sum,
        evidence_sum=evidence_sum,
        override_count=override_count,
        helpful_override_count=helpful_override_count,
        stale_age_sum=stale_age_sum,
        conflict_count=conflict_count,
        config=config,
    )
    return ResearchTeamMemorySignalAttributionRow(
        memory_signal_digest=_memory_signal_digest(memory_signal_key, domain_key),
        domain_key=domain_key,
        decision_count=decision_count,
        helped_decision_count=helped_count,
        hurt_decision_count=hurt_count,
        historical_calibration_error_sum=historical_error_sum,
        evidence_contribution_sum=evidence_sum,
        override_decision_count=override_count,
        helpful_override_count=helpful_override_count,
        stale_memory_age_hours_sum=stale_age_sum,
        cross_domain_conflict_count=conflict_count,
        historical_calibration_score=derived["historical_calibration_score"],
        evidence_contribution_score=derived["evidence_contribution_score"],
        override_usefulness_score=derived["override_usefulness_score"],
        stale_memory_penalty=derived["stale_memory_penalty"],
        cross_domain_conflict_pressure=derived["cross_domain_conflict_pressure"],
        net_help_ratio=derived["net_help_ratio"],
        attribution_score=derived["attribution_score"],
        attribution_status=derived["attribution_status"],
        observed_at=max(item.observed_at for item in signals),
        reason_codes=derived["reason_codes"],
    )


def _row_derived_values(
    *,
    decision_count: Decimal,
    helped_count: Decimal,
    hurt_count: Decimal,
    historical_error_sum: Decimal,
    evidence_sum: Decimal,
    override_count: Decimal,
    helpful_override_count: Decimal,
    stale_age_sum: Decimal,
    conflict_count: Decimal,
    config: ResearchTeamMemorySignalAttributionConfig,
) -> dict[str, Any]:
    historical_score = _ratio_or_zero(decision_count - historical_error_sum, decision_count)
    evidence_score = _ratio_or_zero(evidence_sum, decision_count)
    override_score = _ratio_or_zero(helpful_override_count, override_count)
    mean_stale_age = _nonnegative_ratio_or_zero(stale_age_sum, decision_count)
    stale_penalty = _ratio_or_zero(mean_stale_age, config.block_stale_memory_age_hours)
    conflict_pressure = _ratio_or_zero(conflict_count, decision_count)
    net_help_ratio = _signed_ratio_or_zero(helped_count - hurt_count, decision_count)
    with localcontext(DECIMAL_CONTEXT):
        directional_help_score = _clamp_unit(
            (net_help_ratio + ONE) / Decimal("2.000000"),
        )
        attribution_score = _clamp_unit(
            historical_score * config.historical_calibration_weight
            + evidence_score * config.evidence_contribution_weight
            + override_score * config.override_usefulness_weight
            + directional_help_score * config.decision_help_weight
            - stale_penalty * config.stale_memory_penalty_weight
            - conflict_pressure * config.cross_domain_conflict_weight,
        )
    status = _row_status(
        decision_count=decision_count,
        helped_count=helped_count,
        hurt_count=hurt_count,
        attribution_score=attribution_score,
        stale_penalty=stale_penalty,
        conflict_pressure=conflict_pressure,
        config=config,
    )
    return {
        "historical_calibration_score": historical_score,
        "evidence_contribution_score": evidence_score,
        "override_usefulness_score": override_score,
        "stale_memory_penalty": stale_penalty,
        "cross_domain_conflict_pressure": conflict_pressure,
        "net_help_ratio": net_help_ratio,
        "attribution_score": attribution_score,
        "attribution_status": status,
        "reason_codes": _row_reason_codes(
            decision_count=decision_count,
            helped_count=helped_count,
            hurt_count=hurt_count,
            historical_score=historical_score,
            evidence_score=evidence_score,
            override_count=override_count,
            override_score=override_score,
            stale_penalty=stale_penalty,
            conflict_pressure=conflict_pressure,
            status=status,
            config=config,
        ),
    }


def _row_status(
    *,
    decision_count: Decimal,
    helped_count: Decimal,
    hurt_count: Decimal,
    attribution_score: Decimal,
    stale_penalty: Decimal,
    conflict_pressure: Decimal,
    config: ResearchTeamMemorySignalAttributionConfig,
) -> str:
    if decision_count == ZERO:
        return "block"
    if (
        attribution_score < config.block_attribution_score
        or stale_penalty >= ONE
        or conflict_pressure >= config.block_cross_domain_conflict_pressure
        or (hurt_count > helped_count and attribution_score < config.pass_attribution_score)
    ):
        return "block"
    if (
        attribution_score >= config.pass_attribution_score
        and helped_count >= hurt_count
        and stale_penalty < _stale_watch_penalty(config)
        and conflict_pressure < config.watch_cross_domain_conflict_pressure
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    decision_count: Decimal,
    helped_count: Decimal,
    hurt_count: Decimal,
    historical_score: Decimal,
    evidence_score: Decimal,
    override_count: Decimal,
    override_score: Decimal,
    stale_penalty: Decimal,
    conflict_pressure: Decimal,
    status: str,
    config: ResearchTeamMemorySignalAttributionConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"memory_signal_attribution_{status}"]
    if decision_count == ZERO:
        reason_codes.append("no_decisions_observed")
    elif helped_count > hurt_count:
        reason_codes.append("memory_signal_helped")
    elif hurt_count > helped_count:
        reason_codes.append("memory_signal_hurt")
    else:
        reason_codes.append("memory_signal_mixed")
    reason_codes.append(
        "historical_calibration_support"
        if historical_score >= config.pass_attribution_score
        else "historical_calibration_drag",
    )
    reason_codes.append(
        "evidence_contribution_support"
        if evidence_score >= config.pass_attribution_score
        else "evidence_contribution_drag",
    )
    if override_count == ZERO:
        reason_codes.append("no_override_history")
    else:
        reason_codes.append(
            "override_usefulness_support"
            if override_score >= config.pass_attribution_score
            else "override_usefulness_drag",
        )
    if stale_penalty >= ONE:
        reason_codes.append("stale_memory_penalty_block")
    elif stale_penalty >= _stale_watch_penalty(config):
        reason_codes.append("stale_memory_penalty_watch")
    if conflict_pressure >= config.block_cross_domain_conflict_pressure:
        reason_codes.append("cross_domain_conflict_pressure_block")
    elif conflict_pressure >= config.watch_cross_domain_conflict_pressure:
        reason_codes.append("cross_domain_conflict_pressure_watch")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchTeamMemorySignalAttributionRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.attribution_status == "block" for row in rows):
        return "block"
    if any(row.attribution_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamMemorySignalAttributionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("memory_signal_attribution_report_block", "empty_memory_signals")
    reason_codes: list[str] = [f"memory_signal_attribution_report_{_report_status(rows)}"]
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchTeamMemorySignalAttributionRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamMemorySignalAttributionReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    if not rows:
        counter.update(report_reason_codes)
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchTeamMemorySignalAttributionReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in REASON_CODE_PRIORITY
        if counter[reason_code] > 0
    )


def _validate_input(signal: ResearchTeamMemorySignalAttributionInput) -> None:
    if signal.helped_decision_count + signal.hurt_decision_count > signal.decision_count:
        raise ValueError("helped_decision_count plus hurt_decision_count must fit decisions")
    if signal.override_decision_count > signal.decision_count:
        raise ValueError("override_decision_count must not exceed decision_count")
    if signal.helpful_override_count > signal.override_decision_count:
        raise ValueError("helpful_override_count must not exceed override_decision_count")
    if signal.historical_calibration_error_sum > signal.decision_count:
        raise ValueError("historical_calibration_error_sum must not exceed decision_count")
    if signal.evidence_contribution_sum > signal.decision_count:
        raise ValueError("evidence_contribution_sum must not exceed decision_count")
    if signal.cross_domain_conflict_count > signal.decision_count:
        raise ValueError("cross_domain_conflict_count must not exceed decision_count")
    if signal.decision_count == ZERO:
        for field_name in (
            "helped_decision_count",
            "hurt_decision_count",
            "historical_calibration_error_sum",
            "evidence_contribution_sum",
            "override_decision_count",
            "helpful_override_count",
            "cross_domain_conflict_count",
        ):
            if getattr(signal, field_name) != ZERO:
                raise ValueError(f"{field_name} must be zero when decision_count is zero")


def _validate_row(row: ResearchTeamMemorySignalAttributionRow) -> None:
    if row.helped_decision_count + row.hurt_decision_count > row.decision_count:
        raise ValueError("helped_decision_count plus hurt_decision_count must fit decisions")
    if row.override_decision_count > row.decision_count:
        raise ValueError("override_decision_count must not exceed decision_count")
    if row.helpful_override_count > row.override_decision_count:
        raise ValueError("helpful_override_count must not exceed override_decision_count")
    if row.historical_calibration_error_sum > row.decision_count:
        raise ValueError("historical_calibration_error_sum must not exceed decision_count")
    if row.evidence_contribution_sum > row.decision_count:
        raise ValueError("evidence_contribution_sum must not exceed decision_count")
    if row.cross_domain_conflict_count > row.decision_count:
        raise ValueError("cross_domain_conflict_count must not exceed decision_count")
    if row.decision_count == ZERO:
        for field_name in (
            "helped_decision_count",
            "hurt_decision_count",
            "historical_calibration_error_sum",
            "evidence_contribution_sum",
            "override_decision_count",
            "helpful_override_count",
            "cross_domain_conflict_count",
        ):
            if getattr(row, field_name) != ZERO:
                raise ValueError(f"{field_name} must be zero when decision_count is zero")
    if row.attribution_status == "pass" and row.hurt_decision_count > row.helped_decision_count:
        raise ValueError("pass rows must not have more hurt decisions than helped decisions")
    if row.attribution_status == "block" and not any(
        reason_code.endswith("_block") or reason_code == "memory_signal_hurt"
        for reason_code in row.reason_codes
    ):
        raise ValueError("block rows must include a block or hurt reason")


def _validate_report(report: ResearchTeamMemorySignalAttributionReport) -> None:
    rows = report.rows
    _validate_config(report.config)
    if report.config_version != report.config.config_version:
        raise ValueError("config_version must match config")
    for row in rows:
        _validate_row_against_config(row, report.config)
    if report.signal_count != _decimal_count(len(rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.helped_signal_count != _decimal_count(
        sum(1 for row in rows if row.helped_decision_count > row.hurt_decision_count),
    ):
        raise ValueError("helped_signal_count must match rows")
    if report.hurt_signal_count != _decimal_count(
        sum(1 for row in rows if row.hurt_decision_count > row.helped_decision_count),
    ):
        raise ValueError("hurt_signal_count must match rows")
    if report.average_attribution_score != _average(
        tuple(row.attribution_score for row in rows),
    ):
        raise ValueError("average_attribution_score must match rows")
    if report.average_historical_calibration_score != _average(
        tuple(row.historical_calibration_score for row in rows),
    ):
        raise ValueError("average_historical_calibration_score must match rows")
    if report.average_evidence_contribution_score != _average(
        tuple(row.evidence_contribution_score for row in rows),
    ):
        raise ValueError("average_evidence_contribution_score must match rows")
    if report.average_override_usefulness_score != _average(
        tuple(row.override_usefulness_score for row in rows),
    ):
        raise ValueError("average_override_usefulness_score must match rows")
    if report.max_stale_memory_penalty != max(
        (row.stale_memory_penalty for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_stale_memory_penalty must match rows")
    if report.max_cross_domain_conflict_pressure != max(
        (row.cross_domain_conflict_pressure for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_cross_domain_conflict_pressure must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _validate_config(config: ResearchTeamMemorySignalAttributionConfig) -> None:
    _require_exact_type(config, ResearchTeamMemorySignalAttributionConfig, "config")
    _require_config_version(config.config_version)
    for field_name in (
        "pass_attribution_score",
        "block_attribution_score",
        "watch_cross_domain_conflict_pressure",
        "block_cross_domain_conflict_pressure",
        "historical_calibration_weight",
        "evidence_contribution_weight",
        "override_usefulness_weight",
        "decision_help_weight",
        "stale_memory_penalty_weight",
        "cross_domain_conflict_weight",
    ):
        _require_unit_decimal(field_name, getattr(config, field_name))
    for field_name in (
        "watch_stale_memory_age_hours",
        "block_stale_memory_age_hours",
    ):
        _require_positive_decimal(field_name, getattr(config, field_name))
    if config.pass_attribution_score <= config.block_attribution_score:
        raise ValueError("pass_attribution_score must exceed block_attribution_score")
    if config.block_stale_memory_age_hours <= config.watch_stale_memory_age_hours:
        raise ValueError(
            "block_stale_memory_age_hours must exceed watch_stale_memory_age_hours",
        )
    if (
        config.block_cross_domain_conflict_pressure
        <= config.watch_cross_domain_conflict_pressure
    ):
        raise ValueError(
            "block_cross_domain_conflict_pressure must exceed "
            "watch_cross_domain_conflict_pressure",
        )
    positive_weight = (
        config.historical_calibration_weight
        + config.evidence_contribution_weight
        + config.override_usefulness_weight
        + config.decision_help_weight
    )
    if positive_weight <= ZERO:
        raise ValueError("positive attribution weights must be nonzero")
    _require_hard_flags("config", config)


def _validate_row_against_config(
    row: ResearchTeamMemorySignalAttributionRow,
    config: ResearchTeamMemorySignalAttributionConfig,
) -> None:
    expected = _row_derived_values(
        decision_count=row.decision_count,
        helped_count=row.helped_decision_count,
        hurt_count=row.hurt_decision_count,
        historical_error_sum=row.historical_calibration_error_sum,
        evidence_sum=row.evidence_contribution_sum,
        override_count=row.override_decision_count,
        helpful_override_count=row.helpful_override_count,
        stale_age_sum=row.stale_memory_age_hours_sum,
        conflict_count=row.cross_domain_conflict_count,
        config=config,
    )
    for field_name in (
        "historical_calibration_score",
        "evidence_contribution_score",
        "override_usefulness_score",
        "stale_memory_penalty",
        "cross_domain_conflict_pressure",
        "net_help_ratio",
        "attribution_score",
        "attribution_status",
        "reason_codes",
    ):
        if getattr(row, field_name) != expected[field_name]:
            raise ValueError(f"{field_name} must match row inputs and config")


def _status_count(
    rows: tuple[ResearchTeamMemorySignalAttributionRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.attribution_status == status)


def _row_sort_key(row: ResearchTeamMemorySignalAttributionRow) -> tuple[object, ...]:
    return (
        STATUS_ORDER[row.attribution_status],
        row.domain_key,
        row.memory_signal_digest,
        row.observed_at.isoformat(),
        row.decision_count,
        row.helped_decision_count,
        row.hurt_decision_count,
        row.historical_calibration_error_sum,
        row.evidence_contribution_sum,
        row.override_decision_count,
        row.helpful_override_count,
        row.stale_memory_age_hours_sum,
        row.cross_domain_conflict_count,
        row.historical_calibration_score,
        row.evidence_contribution_score,
        row.override_usefulness_score,
        row.stale_memory_penalty,
        row.cross_domain_conflict_pressure,
        row.net_help_ratio,
        row.attribution_score,
        row.reason_codes,
    )


def _normalize_inputs(
    signals: Sequence[ResearchTeamMemorySignalAttributionInput],
) -> tuple[ResearchTeamMemorySignalAttributionInput, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Sequence):
        raise ValueError("signals must be a sequence")
    normalized: list[ResearchTeamMemorySignalAttributionInput] = []
    for signal in signals:
        if type(signal) is not ResearchTeamMemorySignalAttributionInput:
            raise ValueError("signals must contain ResearchTeamMemorySignalAttributionInput")
        _require_untampered_public_dataclass(signal, "input")
        normalized.append(signal)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (item.memory_signal_key, item.domain_key, item.observed_at),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchTeamMemorySignalAttributionRow],
) -> tuple[ResearchTeamMemorySignalAttributionRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchTeamMemorySignalAttributionRow] = []
    for row in rows:
        if type(row) is not ResearchTeamMemorySignalAttributionRow:
            raise ValueError("rows must contain ResearchTeamMemorySignalAttributionRow")
        _require_untampered_public_dataclass(row, "row")
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Sequence[ResearchTeamMemorySignalAttributionReasonCodeCount],
) -> tuple[ResearchTeamMemorySignalAttributionReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchTeamMemorySignalAttributionReasonCodeCount] = []
    for count in counts:
        if type(count) is not ResearchTeamMemorySignalAttributionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamMemorySignalAttributionReasonCodeCount",
            )
        _require_untampered_public_dataclass(count, "reason_code_count")
        normalized.append(count)
    return tuple(
        sorted(
            normalized,
            key=lambda item: REASON_CODE_PRIORITY.index(item.reason_code),
        ),
    )


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    unique: list[str] = []
    for reason_code in reason_codes:
        normalized = _require_reason_code("reason_code", reason_code)
        if normalized not in unique:
            unique.append(normalized)
    return tuple(reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in unique)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_mapping_flags(label: str, value: Mapping[str, Any]) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if value.get(field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _store_public_snapshot(value: object) -> None:
    object.__setattr__(value, "_canonical_public_snapshot", _public_snapshot(value))


def _require_untampered_public_dataclass(value: object, label: str) -> None:
    expected = getattr(value, "_canonical_public_snapshot", None)
    if expected is None:
        raise ValueError(f"{label} canonical snapshot is missing")
    actual = _public_snapshot(value)
    if actual == expected:
        return
    for (field_name, expected_value), (_, actual_value) in zip(expected, actual, strict=True):
        if actual_value != expected_value:
            raise ValueError(f"{field_name} was modified after initialization")
    raise ValueError(f"{label} was modified after initialization")


def _public_snapshot(value: object) -> tuple[tuple[str, Any], ...]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("public snapshot requires a dataclass instance")
    return tuple((field.name, _json_ready(getattr(value, field.name))) for field in fields(value))


def _require_config_version(value: object) -> str:
    if value != DEFAULT_RESEARCH_TEAM_MEMORY_SIGNAL_ATTRIBUTION_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    return _require_public_identifier("config_version", value)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a string")
    lowered = value.lower()
    if len(value) > 128 or not all(
        character.isalnum() or character in "._-"
        for character in value
    ):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(lowered):
        raise ValueError(f"{field_name} has unsafe public value")
    return value


def _require_public_code(field_name: str, value: object) -> str:
    if type(value) is not str or PUBLIC_CODE_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public code")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_CODE_PRIORITY:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in MEMORY_SIGNAL_ATTRIBUTION_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_digest_reference(field_name: str, value: object) -> str:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 reference")
    return value


def _require_sha256_hex(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    normalized = _quantize(raw)
    if raw != normalized:
        raise ValueError(f"{field_name} must be a canonical Decimal with six places")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _require_decimal(field_name, raw)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _require_decimal(field_name, raw)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized % ONE != ZERO:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _require_unit_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if raw > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _require_decimal(field_name, raw)


def _require_signed_unit_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < NEGATIVE_ONE or raw > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return _require_decimal(field_name, raw)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_unit(numerator / denominator)


def _nonnegative_ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        value = _quantize(numerator / denominator)
    if value < ZERO:
        return ZERO
    return value


def _signed_ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_signed_unit(numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _stale_watch_penalty(
    config: ResearchTeamMemorySignalAttributionConfig,
) -> Decimal:
    return _ratio_or_zero(
        config.watch_stale_memory_age_hours,
        config.block_stale_memory_age_hours,
    )


def _clamp_unit(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _clamp_signed_unit(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < NEGATIVE_ONE:
        return NEGATIVE_ONE
    if normalized > ONE:
        return ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _memory_signal_digest(memory_signal_key: str, domain_key: str) -> str:
    material = json.dumps(
        {"domain_key": domain_key, "memory_signal_key": memory_signal_key},
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"sha256:{sha256(material.encode('utf-8')).hexdigest()}"


def _report_values_without_digest(
    report: ResearchTeamMemorySignalAttributionReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: Mapping[str, Any]) -> str:
    ready = _json_ready(dict(values))
    _reject_unsafe_public_payload("digest_payload", ready, allow_json_containers=True)
    encoded = json.dumps(ready, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("JSON numeric values must be Decimal-derived strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_payload_values(label: str, value: object, path: str = "") -> None:
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_payload_values(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_payload_values(label, item, item_path)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} has non-string public key")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{label} exposes unsafe public field")
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if allow_json_containers and value is None:
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"{label} has unsafe public value")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    if "://" in normalized or "@" in normalized:
        return True
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
