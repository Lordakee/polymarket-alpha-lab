"""Readonly readiness report for stale information refresh SLA gating."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json


__all__ = (
    "DEFAULT_INFORMATION_FRESHNESS_REFRESH_SLA_READINESS_CONFIG_VERSION",
    "InformationFreshnessRefreshSlaReadinessConfig",
    "InformationFreshnessRefreshSlaReadinessItem",
    "InformationFreshnessRefreshSlaReadinessReport",
    "InformationFreshnessRefreshSlaReadinessRow",
    "build_information_freshness_refresh_sla_readiness_report",
    "information_freshness_refresh_sla_readiness_report_payload",
)


DEFAULT_INFORMATION_FRESHNESS_REFRESH_SLA_READINESS_CONFIG_VERSION = (
    "information-freshness-refresh-sla-readiness-v0"
)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

INFORMATION_SURFACES = ("market_data", "external_evidence", "research_packet")
READINESS_STATUSES = ("blocked", "watch", "pass")
STATUS_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}

REQUIRED_INFORMATION_BLOCKED_REASON = "required_information_blocked"
MARKET_DATA_STALE_REASON = "market_data_stale"
EXTERNAL_EVIDENCE_STALE_REASON = "external_evidence_stale"
RESEARCH_PACKET_STALE_REASON = "research_packet_stale"
MARKET_DATA_LATENCY_BREACH_REASON = "market_data_latency_sla_breached"
EXTERNAL_EVIDENCE_LATENCY_BREACH_REASON = (
    "external_evidence_latency_sla_breached"
)
RESEARCH_PACKET_LATENCY_BREACH_REASON = "research_packet_latency_sla_breached"
MARKET_DATA_REFRESH_BREACH_REASON = "market_data_refresh_sla_breached"
EXTERNAL_EVIDENCE_REFRESH_BREACH_REASON = "external_evidence_refresh_sla_breached"
RESEARCH_PACKET_REFRESH_BREACH_REASON = "research_packet_refresh_sla_breached"
READY_REASON = "information_freshness_refresh_sla_ready"
NO_INPUTS_REASON = "no_information_freshness_inputs"

REASON_CODES = (
    REQUIRED_INFORMATION_BLOCKED_REASON,
    MARKET_DATA_STALE_REASON,
    EXTERNAL_EVIDENCE_STALE_REASON,
    RESEARCH_PACKET_STALE_REASON,
    MARKET_DATA_LATENCY_BREACH_REASON,
    EXTERNAL_EVIDENCE_LATENCY_BREACH_REASON,
    RESEARCH_PACKET_LATENCY_BREACH_REASON,
    MARKET_DATA_REFRESH_BREACH_REASON,
    EXTERNAL_EVIDENCE_REFRESH_BREACH_REASON,
    RESEARCH_PACKET_REFRESH_BREACH_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
REASON_WEIGHT = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
ISSUE_REASON_WEIGHT = {
    MARKET_DATA_STALE_REASON: 0,
    EXTERNAL_EVIDENCE_STALE_REASON: 1,
    RESEARCH_PACKET_STALE_REASON: 2,
    MARKET_DATA_LATENCY_BREACH_REASON: 3,
    EXTERNAL_EVIDENCE_LATENCY_BREACH_REASON: 4,
    RESEARCH_PACKET_LATENCY_BREACH_REASON: 5,
    MARKET_DATA_REFRESH_BREACH_REASON: 6,
    EXTERNAL_EVIDENCE_REFRESH_BREACH_REASON: 7,
    RESEARCH_PACKET_REFRESH_BREACH_REASON: 8,
    READY_REASON: 9,
    NO_INPUTS_REASON: 10,
}

STALE_REASON_BY_SURFACE = {
    "market_data": MARKET_DATA_STALE_REASON,
    "external_evidence": EXTERNAL_EVIDENCE_STALE_REASON,
    "research_packet": RESEARCH_PACKET_STALE_REASON,
}
LATENCY_REASON_BY_SURFACE = {
    "market_data": MARKET_DATA_LATENCY_BREACH_REASON,
    "external_evidence": EXTERNAL_EVIDENCE_LATENCY_BREACH_REASON,
    "research_packet": RESEARCH_PACKET_LATENCY_BREACH_REASON,
}
REFRESH_REASON_BY_SURFACE = {
    "market_data": MARKET_DATA_REFRESH_BREACH_REASON,
    "external_evidence": EXTERNAL_EVIDENCE_REFRESH_BREACH_REASON,
    "research_packet": RESEARCH_PACKET_REFRESH_BREACH_REASON,
}
GATE_BY_STATUS = {
    "blocked": "block_report_only_stale_information_recommendation",
    "watch": "watch_report_only_information_refresh_queue",
    "pass": "allow_report_only_information_freshness_readiness",
}

REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "effective_config",
    "readiness_status",
    "recommendation_gate",
    "information_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "required_information_count",
    "blocking_required_information_count",
    "stale_information_count",
    "latency_sla_breach_count",
    "upstream_refresh_sla_breach_count",
    "issue_ratio",
    "required_block_ratio",
    "max_age_seconds",
    "max_latency_seconds",
    "rows",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    *REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)

FORBIDDEN_PUBLIC_TEXT_TOKENS = (
    "auth",
    "buy",
    "database",
    "mutation",
    "order",
    "persist",
    "sell",
    "signing",
    "trade",
    "trading",
    "wallet",
)


class _FrozenJsonObject(dict[str, object]):
    def __new__(cls, values: Mapping[str, object]) -> _FrozenJsonObject:
        instance = super().__new__(cls)
        dict.update(instance, values)
        return instance

    def __init__(self, values: Mapping[str, object]) -> None:
        pass

    def _readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public payload is immutable")

    __setitem__ = _readonly
    __delitem__ = _readonly
    clear = _readonly
    pop = _readonly
    popitem = _readonly
    setdefault = _readonly
    update = _readonly
    __ior__ = _readonly


class _FrozenJsonArray(list[object]):
    def __new__(cls, values: object) -> _FrozenJsonArray:
        instance = super().__new__(cls)
        list.extend(instance, values)  # type: ignore[arg-type]
        return instance

    def __init__(self, values: object) -> None:
        pass

    def _readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public payload is immutable")

    __setitem__ = _readonly
    __delitem__ = _readonly
    append = _readonly
    clear = _readonly
    extend = _readonly
    insert = _readonly
    pop = _readonly
    remove = _readonly
    reverse = _readonly
    sort = _readonly
    __iadd__ = _readonly
    __imul__ = _readonly


@dataclass(frozen=True)
class InformationFreshnessRefreshSlaReadinessConfig:
    config_version: str = DEFAULT_INFORMATION_FRESHNESS_REFRESH_SLA_READINESS_CONFIG_VERSION
    market_data_stale_after_seconds: Decimal = Decimal("120.000000")
    external_evidence_stale_after_seconds: Decimal = Decimal("3600.000000")
    research_packet_stale_after_seconds: Decimal = Decimal("7200.000000")
    market_data_latency_sla_seconds: Decimal = Decimal("15.000000")
    external_evidence_latency_sla_seconds: Decimal = Decimal("300.000000")
    research_packet_latency_sla_seconds: Decimal = Decimal("900.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "InformationFreshnessRefreshSlaReadinessConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            InformationFreshnessRefreshSlaReadinessConfig,
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        for field_name in (
            "market_data_stale_after_seconds",
            "external_evidence_stale_after_seconds",
            "research_packet_stale_after_seconds",
            "market_data_latency_sla_seconds",
            "external_evidence_latency_sla_seconds",
            "research_packet_latency_sla_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _reject_forbidden_public_payload("config", self)
        _require_phase_flags("config", self)


@dataclass(frozen=True)
class InformationFreshnessRefreshSlaReadinessItem:
    information_id: str
    information_surface: str
    age_seconds: Decimal
    latency_seconds: Decimal
    upstream_refresh_sla_breached: bool = False
    required_for_recommendation: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "InformationFreshnessRefreshSlaReadinessItem does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "item",
            self,
            InformationFreshnessRefreshSlaReadinessItem,
        )
        object.__setattr__(
            self,
            "information_id",
            _require_canonical_string("information_id", self.information_id),
        )
        object.__setattr__(
            self,
            "information_surface",
            _require_member(
                "information_surface",
                self.information_surface,
                INFORMATION_SURFACES,
            ),
        )
        for field_name in ("age_seconds", "latency_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "upstream_refresh_sla_breached",
            "required_for_recommendation",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _reject_forbidden_public_payload("item", self)
        _require_phase_flags("item", self)


@dataclass(frozen=True)
class InformationFreshnessRefreshSlaReadinessRow:
    information_id: str
    information_surface: str
    age_seconds: Decimal
    latency_seconds: Decimal
    stale_after_seconds: Decimal
    latency_sla_seconds: Decimal
    upstream_refresh_sla_breached: bool
    required_for_recommendation: bool
    readiness_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "InformationFreshnessRefreshSlaReadinessRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, InformationFreshnessRefreshSlaReadinessRow)
        object.__setattr__(
            self,
            "information_id",
            _require_canonical_string("information_id", self.information_id),
        )
        object.__setattr__(
            self,
            "information_surface",
            _require_member(
                "information_surface",
                self.information_surface,
                INFORMATION_SURFACES,
            ),
        )
        for field_name in (
            "age_seconds",
            "latency_seconds",
            "stale_after_seconds",
            "latency_sla_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "upstream_refresh_sla_breached",
            "required_for_recommendation",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "readiness_status",
            _require_member("readiness_status", self.readiness_status, READINESS_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_forbidden_public_payload("row", self)
        _require_phase_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class InformationFreshnessRefreshSlaReadinessReport:
    generated_at: datetime
    config_version: str
    effective_config: InformationFreshnessRefreshSlaReadinessConfig
    readiness_status: str
    recommendation_gate: str
    information_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    required_information_count: Decimal
    blocking_required_information_count: Decimal
    stale_information_count: Decimal
    latency_sla_breach_count: Decimal
    upstream_refresh_sla_breach_count: Decimal
    issue_ratio: Decimal
    required_block_ratio: Decimal
    max_age_seconds: Decimal
    max_latency_seconds: Decimal
    rows: tuple[InformationFreshnessRefreshSlaReadinessRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "InformationFreshnessRefreshSlaReadinessReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            InformationFreshnessRefreshSlaReadinessReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "effective_config",
            _snapshot_config(self.effective_config),
        )
        if self.config_version != self.effective_config.config_version:
            raise ValueError("config_version must match effective_config")
        object.__setattr__(
            self,
            "readiness_status",
            _require_member("readiness_status", self.readiness_status, READINESS_STATUSES),
        )
        object.__setattr__(
            self,
            "recommendation_gate",
            _require_canonical_string("recommendation_gate", self.recommendation_gate),
        )
        for field_name in (
            "information_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "required_information_count",
            "blocking_required_information_count",
            "stale_information_count",
            "latency_sla_breach_count",
            "upstream_refresh_sla_breach_count",
            "issue_ratio",
            "required_block_ratio",
            "max_age_seconds",
            "max_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio("issue_ratio", self.issue_ratio)
        _require_ratio("required_block_ratio", self.required_block_ratio)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_forbidden_public_payload("report", self)
        _require_phase_flags("report", self)
        _validate_report(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)


def build_information_freshness_refresh_sla_readiness_report(
    items: object,
    *,
    config: InformationFreshnessRefreshSlaReadinessConfig,
    generated_at: datetime,
) -> InformationFreshnessRefreshSlaReadinessReport:
    _require_exact_type(
        "config",
        config,
        InformationFreshnessRefreshSlaReadinessConfig,
    )
    _require_phase_flags("config", config)
    effective_config = _snapshot_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_items(items)
    rows = tuple(
        sorted(
            (
                _row_from_item(item, config=effective_config)
                for item in normalized_items
            ),
            key=_row_sort_key,
        ),
    )
    issue_count = _decimal_count(sum(1 for row in rows if row.readiness_status != "pass"))
    required_count = _decimal_count(
        sum(1 for row in rows if row.required_for_recommendation),
    )
    blocking_required_count = _decimal_count(
        sum(
            1
            for row in rows
            if row.required_for_recommendation and row.readiness_status == "blocked"
        ),
    )
    readiness_status = _report_status(rows)
    return InformationFreshnessRefreshSlaReadinessReport(
        generated_at=generated_at_utc,
        config_version=effective_config.config_version,
        effective_config=effective_config,
        readiness_status=readiness_status,
        recommendation_gate=GATE_BY_STATUS[readiness_status],
        information_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        required_information_count=required_count,
        blocking_required_information_count=blocking_required_count,
        stale_information_count=_stale_count(rows),
        latency_sla_breach_count=_latency_count(rows),
        upstream_refresh_sla_breach_count=_refresh_count(rows),
        issue_ratio=_ratio(issue_count, _decimal_count(len(rows))),
        required_block_ratio=_ratio(blocking_required_count, required_count),
        max_age_seconds=max((row.age_seconds for row in rows), default=ZERO),
        max_latency_seconds=max((row.latency_seconds for row in rows), default=ZERO),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def information_freshness_refresh_sla_readiness_report_payload(
    report: InformationFreshnessRefreshSlaReadinessReport | Mapping[str, object],
) -> _FrozenJsonObject:
    if type(report) is InformationFreshnessRefreshSlaReadinessReport:
        materialized_report = _materialize_report_object(report)
        payload = _report_public_payload_values(materialized_report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = (
            materialized_report.derived_validation_digest
        )
        return _freeze_json_object(payload)
    if isinstance(report, Mapping):
        payload = _copy_public_mapping(report)
        _reject_forbidden_public_payload("payload", payload)
        _require_public_payload_fields(payload)
        _validate_public_payload_derived_validation_digest(payload)
        _require_public_payload_json_values(payload)
        _validate_public_payload_materialization(payload)
        return _freeze_json_object(payload)
    raise ValueError(
        "report must be an InformationFreshnessRefreshSlaReadinessReport or payload",
    )


def _materialize_report_object(
    report: InformationFreshnessRefreshSlaReadinessReport,
) -> InformationFreshnessRefreshSlaReadinessReport:
    normalized_generated_at = _as_utc("generated_at", report.generated_at)
    if report.generated_at.tzinfo is not UTC or report.generated_at != normalized_generated_at:
        raise ValueError("generated_at must be normalized to UTC")
    if type(report.rows) is not tuple:
        raise ValueError("rows must be exactly a tuple")
    if type(report.reason_codes) is not tuple:
        raise ValueError("reason_codes must be exactly a tuple")
    _normalize_reason_codes("reason_codes", report.reason_codes)
    for field_name in (
        "information_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "required_information_count",
        "blocking_required_information_count",
        "stale_information_count",
        "latency_sla_breach_count",
        "upstream_refresh_sla_breach_count",
        "issue_ratio",
        "required_block_ratio",
        "max_age_seconds",
        "max_latency_seconds",
    ):
        _require_materialized_decimal(field_name, getattr(report, field_name))
    materialized_rows = tuple(_materialize_row_object(row) for row in report.rows)
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["rows"] = materialized_rows
    return InformationFreshnessRefreshSlaReadinessReport(**values)


def _materialize_row_object(
    row: InformationFreshnessRefreshSlaReadinessRow,
) -> InformationFreshnessRefreshSlaReadinessRow:
    _require_exact_type("row", row, InformationFreshnessRefreshSlaReadinessRow)
    if type(row.reason_codes) is not tuple:
        raise ValueError("row reason_codes must be exactly a tuple")
    _normalize_reason_codes("reason_codes", row.reason_codes)
    for field_name in (
        "age_seconds",
        "latency_seconds",
        "stale_after_seconds",
        "latency_sla_seconds",
    ):
        _require_materialized_decimal(field_name, getattr(row, field_name))
    _require_phase_flags("row", row)
    values = {field.name: getattr(row, field.name) for field in fields(row)}
    return InformationFreshnessRefreshSlaReadinessRow(**values)


def _require_materialized_decimal(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value.as_tuple().exponent != QUANTUM.as_tuple().exponent:  # type: ignore[union-attr]
        raise ValueError(f"{field_name} must use six decimal places")


def _validate_public_payload_materialization(payload: dict[str, object]) -> None:
    materialized_report = _report_from_public_payload(payload)
    expected_payload = _report_public_payload_values(materialized_report)
    expected_payload[DERIVED_VALIDATION_DIGEST_FIELD] = (
        materialized_report.derived_validation_digest
    )
    if payload != expected_payload:
        raise ValueError("public payload must exactly match materialized report")


def _report_from_public_payload(
    payload: dict[str, object],
) -> InformationFreshnessRefreshSlaReadinessReport:
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a public payload list")
    rows = tuple(
        _row_from_public_payload(row_value, index=index)
        for index, row_value in enumerate(rows_value)
    )
    return InformationFreshnessRefreshSlaReadinessReport(
        generated_at=_public_payload_datetime(payload["generated_at"], "generated_at"),
        config_version=_public_payload_string(payload["config_version"], "config_version"),
        effective_config=_config_from_public_payload(payload["effective_config"]),
        readiness_status=_public_payload_string(
            payload["readiness_status"],
            "readiness_status",
        ),
        recommendation_gate=_public_payload_string(
            payload["recommendation_gate"],
            "recommendation_gate",
        ),
        information_count=_public_payload_decimal(
            payload["information_count"],
            "information_count",
        ),
        pass_count=_public_payload_decimal(payload["pass_count"], "pass_count"),
        watch_count=_public_payload_decimal(payload["watch_count"], "watch_count"),
        blocked_count=_public_payload_decimal(payload["blocked_count"], "blocked_count"),
        required_information_count=_public_payload_decimal(
            payload["required_information_count"],
            "required_information_count",
        ),
        blocking_required_information_count=_public_payload_decimal(
            payload["blocking_required_information_count"],
            "blocking_required_information_count",
        ),
        stale_information_count=_public_payload_decimal(
            payload["stale_information_count"],
            "stale_information_count",
        ),
        latency_sla_breach_count=_public_payload_decimal(
            payload["latency_sla_breach_count"],
            "latency_sla_breach_count",
        ),
        upstream_refresh_sla_breach_count=_public_payload_decimal(
            payload["upstream_refresh_sla_breach_count"],
            "upstream_refresh_sla_breach_count",
        ),
        issue_ratio=_public_payload_decimal(payload["issue_ratio"], "issue_ratio"),
        required_block_ratio=_public_payload_decimal(
            payload["required_block_ratio"],
            "required_block_ratio",
        ),
        max_age_seconds=_public_payload_decimal(
            payload["max_age_seconds"],
            "max_age_seconds",
        ),
        max_latency_seconds=_public_payload_decimal(
            payload["max_latency_seconds"],
            "max_latency_seconds",
        ),
        rows=rows,
        reason_codes=_public_payload_reason_codes(
            payload["reason_codes"],
            "reason_codes",
        ),
        derived_validation_digest=_normalize_sha256(
            DERIVED_VALIDATION_DIGEST_FIELD,
            payload[DERIVED_VALIDATION_DIGEST_FIELD],
        ),
        paper_only=_public_payload_bool(payload["paper_only"], "paper_only"),
        report_only=_public_payload_bool(payload["report_only"], "report_only"),
        readonly=_public_payload_bool(payload["readonly"], "readonly"),
    )


def _config_from_public_payload(
    value: object,
) -> InformationFreshnessRefreshSlaReadinessConfig:
    if type(value) is not dict:
        raise ValueError("effective_config must be a public payload object")
    expected_fields = tuple(
        field.name for field in fields(InformationFreshnessRefreshSlaReadinessConfig)
    )
    missing_fields = tuple(
        field_name for field_name in expected_fields if field_name not in value
    )
    if missing_fields:
        raise ValueError(f"effective_config.{missing_fields[0]} is required")
    extra_fields = sorted(set(value) - set(expected_fields))
    if extra_fields:
        raise ValueError(f"unexpected public field: effective_config.{extra_fields[0]}")
    return InformationFreshnessRefreshSlaReadinessConfig(
        config_version=_public_payload_string(
            value["config_version"],
            "effective_config.config_version",
        ),
        market_data_stale_after_seconds=_public_payload_decimal(
            value["market_data_stale_after_seconds"],
            "effective_config.market_data_stale_after_seconds",
        ),
        external_evidence_stale_after_seconds=_public_payload_decimal(
            value["external_evidence_stale_after_seconds"],
            "effective_config.external_evidence_stale_after_seconds",
        ),
        research_packet_stale_after_seconds=_public_payload_decimal(
            value["research_packet_stale_after_seconds"],
            "effective_config.research_packet_stale_after_seconds",
        ),
        market_data_latency_sla_seconds=_public_payload_decimal(
            value["market_data_latency_sla_seconds"],
            "effective_config.market_data_latency_sla_seconds",
        ),
        external_evidence_latency_sla_seconds=_public_payload_decimal(
            value["external_evidence_latency_sla_seconds"],
            "effective_config.external_evidence_latency_sla_seconds",
        ),
        research_packet_latency_sla_seconds=_public_payload_decimal(
            value["research_packet_latency_sla_seconds"],
            "effective_config.research_packet_latency_sla_seconds",
        ),
        paper_only=_public_payload_bool(
            value["paper_only"],
            "effective_config.paper_only",
        ),
        report_only=_public_payload_bool(
            value["report_only"],
            "effective_config.report_only",
        ),
        readonly=_public_payload_bool(
            value["readonly"],
            "effective_config.readonly",
        ),
    )


def _row_from_public_payload(
    value: object,
    *,
    index: int,
) -> InformationFreshnessRefreshSlaReadinessRow:
    path = f"rows[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{path} must be a public payload object")
    expected_fields = tuple(
        field.name for field in fields(InformationFreshnessRefreshSlaReadinessRow)
    )
    missing_fields = tuple(field_name for field_name in expected_fields if field_name not in value)
    if missing_fields:
        raise ValueError(f"{path}.{missing_fields[0]} is required")
    extra_fields = sorted(set(value) - set(expected_fields))
    if extra_fields:
        raise ValueError(f"unexpected public field: {path}.{extra_fields[0]}")
    return InformationFreshnessRefreshSlaReadinessRow(
        information_id=_public_payload_string(
            value["information_id"],
            f"{path}.information_id",
        ),
        information_surface=_public_payload_string(
            value["information_surface"],
            f"{path}.information_surface",
        ),
        age_seconds=_public_payload_decimal(
            value["age_seconds"],
            f"{path}.age_seconds",
        ),
        latency_seconds=_public_payload_decimal(
            value["latency_seconds"],
            f"{path}.latency_seconds",
        ),
        stale_after_seconds=_public_payload_decimal(
            value["stale_after_seconds"],
            f"{path}.stale_after_seconds",
        ),
        latency_sla_seconds=_public_payload_decimal(
            value["latency_sla_seconds"],
            f"{path}.latency_sla_seconds",
        ),
        upstream_refresh_sla_breached=_public_payload_bool(
            value["upstream_refresh_sla_breached"],
            f"{path}.upstream_refresh_sla_breached",
        ),
        required_for_recommendation=_public_payload_bool(
            value["required_for_recommendation"],
            f"{path}.required_for_recommendation",
        ),
        readiness_status=_public_payload_string(
            value["readiness_status"],
            f"{path}.readiness_status",
        ),
        reason_codes=_public_payload_reason_codes(
            value["reason_codes"],
            f"{path}.reason_codes",
        ),
        paper_only=_public_payload_bool(value["paper_only"], f"{path}.paper_only"),
        report_only=_public_payload_bool(value["report_only"], f"{path}.report_only"),
        readonly=_public_payload_bool(value["readonly"], f"{path}.readonly"),
    )


def _public_payload_string(value: object, path: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{path} must be a public payload string")
    return value


def _public_payload_decimal(value: object, path: str) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{path} must be a Decimal-derived string")
    try:
        return Decimal(value)
    except (ArithmeticError, ValueError) as exc:
        raise ValueError(f"{path} must be a Decimal-derived string") from exc


def _public_payload_datetime(value: object, path: str) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{path} must be a datetime string")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{path} must be a datetime string") from exc


def _public_payload_reason_codes(value: object, path: str) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a public payload list")
    return tuple(_public_payload_string(item, path) for item in value)


def _public_payload_bool(value: object, path: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{path} must be a bool")
    return value


def _row_from_item(
    item: InformationFreshnessRefreshSlaReadinessItem,
    *,
    config: InformationFreshnessRefreshSlaReadinessConfig,
) -> InformationFreshnessRefreshSlaReadinessRow:
    stale_after_seconds = _stale_after_seconds(item.information_surface, config)
    latency_sla_seconds = _latency_sla_seconds(item.information_surface, config)
    reason_codes = _row_reason_codes(
        item,
        stale_after_seconds=stale_after_seconds,
        latency_sla_seconds=latency_sla_seconds,
    )
    return InformationFreshnessRefreshSlaReadinessRow(
        information_id=item.information_id,
        information_surface=item.information_surface,
        age_seconds=item.age_seconds,
        latency_seconds=item.latency_seconds,
        stale_after_seconds=stale_after_seconds,
        latency_sla_seconds=latency_sla_seconds,
        upstream_refresh_sla_breached=item.upstream_refresh_sla_breached,
        required_for_recommendation=item.required_for_recommendation,
        readiness_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: InformationFreshnessRefreshSlaReadinessItem,
    *,
    stale_after_seconds: Decimal,
    latency_sla_seconds: Decimal,
) -> tuple[str, ...]:
    issue_codes: list[str] = []
    if item.age_seconds > stale_after_seconds:
        issue_codes.append(STALE_REASON_BY_SURFACE[item.information_surface])
    if item.latency_seconds > latency_sla_seconds:
        issue_codes.append(LATENCY_REASON_BY_SURFACE[item.information_surface])
    if item.upstream_refresh_sla_breached:
        issue_codes.append(REFRESH_REASON_BY_SURFACE[item.information_surface])
    if not issue_codes:
        return (READY_REASON,)
    if item.required_for_recommendation:
        issue_codes.append(REQUIRED_INFORMATION_BLOCKED_REASON)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in issue_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if REQUIRED_INFORMATION_BLOCKED_REASON in reason_codes:
        return "blocked"
    if reason_codes == (READY_REASON,):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[InformationFreshnessRefreshSlaReadinessRow, ...],
) -> str:
    if not rows:
        return "blocked"
    return min((row.readiness_status for row in rows), key=lambda item: STATUS_WEIGHT[item])


def _report_reason_codes(
    rows: tuple[InformationFreshnessRefreshSlaReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    issue_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != READY_REASON
    }
    if not issue_codes:
        return (READY_REASON,)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in issue_codes)


def _stale_after_seconds(
    information_surface: str,
    config: InformationFreshnessRefreshSlaReadinessConfig,
) -> Decimal:
    if information_surface == "market_data":
        return config.market_data_stale_after_seconds
    if information_surface == "external_evidence":
        return config.external_evidence_stale_after_seconds
    return config.research_packet_stale_after_seconds


def _latency_sla_seconds(
    information_surface: str,
    config: InformationFreshnessRefreshSlaReadinessConfig,
) -> Decimal:
    if information_surface == "market_data":
        return config.market_data_latency_sla_seconds
    if information_surface == "external_evidence":
        return config.external_evidence_latency_sla_seconds
    return config.research_packet_latency_sla_seconds


def _normalize_items(
    items: object,
) -> tuple[InformationFreshnessRefreshSlaReadinessItem, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable")
    try:
        normalized = tuple(items)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("items must be an iterable") from exc
    seen_ids: set[str] = set()
    for item in normalized:
        if type(item) is not InformationFreshnessRefreshSlaReadinessItem:
            raise ValueError(
                "items must contain InformationFreshnessRefreshSlaReadinessItem values",
            )
        _require_phase_flags("item", item)
        if item.information_id in seen_ids:
            raise ValueError("items must contain unique information_id values")
        seen_ids.add(item.information_id)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[InformationFreshnessRefreshSlaReadinessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in normalized:
        if type(row) is not InformationFreshnessRefreshSlaReadinessRow:
            raise ValueError(
                "rows must contain InformationFreshnessRefreshSlaReadinessRow values",
            )
        _require_phase_flags("row", row)
        if row.information_id in seen_ids:
            raise ValueError("rows must contain unique information_id values")
        seen_ids.add(row.information_id)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic readiness sort")
    return normalized


def _validate_row(
    row: InformationFreshnessRefreshSlaReadinessRow,
    *,
    config: InformationFreshnessRefreshSlaReadinessConfig | None = None,
) -> None:
    stale_after_seconds = row.stale_after_seconds
    latency_sla_seconds = row.latency_sla_seconds
    if config is not None:
        stale_after_seconds = _stale_after_seconds(row.information_surface, config)
        latency_sla_seconds = _latency_sla_seconds(row.information_surface, config)
        if row.stale_after_seconds != stale_after_seconds:
            raise ValueError("stale_after_seconds must match effective_config")
        if row.latency_sla_seconds != latency_sla_seconds:
            raise ValueError("latency_sla_seconds must match effective_config")
    if row.reason_codes != _row_reason_codes(
        InformationFreshnessRefreshSlaReadinessItem(
            information_id=row.information_id,
            information_surface=row.information_surface,
            age_seconds=row.age_seconds,
            latency_seconds=row.latency_seconds,
            upstream_refresh_sla_breached=row.upstream_refresh_sla_breached,
            required_for_recommendation=row.required_for_recommendation,
        ),
        stale_after_seconds=stale_after_seconds,
        latency_sla_seconds=latency_sla_seconds,
    ):
        raise ValueError("reason_codes must match row inputs")
    if row.readiness_status != _row_status(row.reason_codes):
        raise ValueError("reason_codes must match readiness_status")
    if row.readiness_status == "pass" and row.reason_codes != (READY_REASON,):
        raise ValueError("pass rows must use ready reason")
    if READY_REASON in row.reason_codes and len(row.reason_codes) != 1:
        raise ValueError("ready reason must not mix with issue reasons")


def _config_from_row_thresholds(
    row: InformationFreshnessRefreshSlaReadinessRow,
) -> InformationFreshnessRefreshSlaReadinessConfig:
    return InformationFreshnessRefreshSlaReadinessConfig(
        market_data_stale_after_seconds=(
            row.stale_after_seconds
            if row.information_surface == "market_data"
            else Decimal("120.000000")
        ),
        external_evidence_stale_after_seconds=(
            row.stale_after_seconds
            if row.information_surface == "external_evidence"
            else Decimal("3600.000000")
        ),
        research_packet_stale_after_seconds=(
            row.stale_after_seconds
            if row.information_surface == "research_packet"
            else Decimal("7200.000000")
        ),
        market_data_latency_sla_seconds=(
            row.latency_sla_seconds
            if row.information_surface == "market_data"
            else Decimal("15.000000")
        ),
        external_evidence_latency_sla_seconds=(
            row.latency_sla_seconds
            if row.information_surface == "external_evidence"
            else Decimal("300.000000")
        ),
        research_packet_latency_sla_seconds=(
            row.latency_sla_seconds
            if row.information_surface == "research_packet"
            else Decimal("900.000000")
        ),
    )


def _validate_report(report: InformationFreshnessRefreshSlaReadinessReport) -> None:
    effective_config = _snapshot_config(report.effective_config)
    if report.config_version != effective_config.config_version:
        raise ValueError("config_version must match effective_config")
    rows = report.rows
    for row in rows:
        _require_exact_type("row", row, InformationFreshnessRefreshSlaReadinessRow)
        _require_phase_flags("row", row)
        _validate_row(row, config=effective_config)
    if report.recommendation_gate != GATE_BY_STATUS[report.readiness_status]:
        raise ValueError("recommendation_gate must match readiness_status")
    if report.information_count != _decimal_count(len(rows)):
        raise ValueError("information_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.required_information_count != _decimal_count(
        sum(1 for row in rows if row.required_for_recommendation),
    ):
        raise ValueError("required_information_count must match rows")
    if report.blocking_required_information_count != _decimal_count(
        sum(
            1
            for row in rows
            if row.required_for_recommendation and row.readiness_status == "blocked"
        ),
    ):
        raise ValueError("blocking_required_information_count must match rows")
    if report.stale_information_count != _stale_count(rows):
        raise ValueError("stale_information_count must match rows")
    if report.latency_sla_breach_count != _latency_count(rows):
        raise ValueError("latency_sla_breach_count must match rows")
    if report.upstream_refresh_sla_breach_count != _refresh_count(rows):
        raise ValueError("upstream_refresh_sla_breach_count must match rows")
    issue_count = _decimal_count(sum(1 for row in rows if row.readiness_status != "pass"))
    if report.issue_ratio != _ratio(issue_count, report.information_count):
        raise ValueError("issue_ratio must match rows")
    if report.required_block_ratio != _ratio(
        report.blocking_required_information_count,
        report.required_information_count,
    ):
        raise ValueError("required_block_ratio must match rows")
    if report.max_age_seconds != max((row.age_seconds for row in rows), default=ZERO):
        raise ValueError("max_age_seconds must match rows")
    if report.max_latency_seconds != max(
        (row.latency_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_latency_seconds must match rows")
    if report.readiness_status != _report_status(rows):
        raise ValueError("readiness_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _row_sort_key(row: InformationFreshnessRefreshSlaReadinessRow) -> tuple[int, int, str]:
    return (
        STATUS_WEIGHT[row.readiness_status],
        _primary_issue_weight(row.reason_codes),
        row.information_id,
    )


def _primary_issue_weight(reason_codes: tuple[str, ...]) -> int:
    issue_weights = [
        ISSUE_REASON_WEIGHT[reason_code]
        for reason_code in reason_codes
        if reason_code != REQUIRED_INFORMATION_BLOCKED_REASON
    ]
    return min(issue_weights, default=ISSUE_REASON_WEIGHT[READY_REASON])


def _status_count(
    rows: tuple[InformationFreshnessRefreshSlaReadinessRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.readiness_status == status))


def _stale_count(rows: tuple[InformationFreshnessRefreshSlaReadinessRow, ...]) -> Decimal:
    return _decimal_count(
        sum(
            1
            for row in rows
            if any(
                reason_code in row.reason_codes
                for reason_code in (
                    MARKET_DATA_STALE_REASON,
                    EXTERNAL_EVIDENCE_STALE_REASON,
                    RESEARCH_PACKET_STALE_REASON,
                )
            )
        ),
    )


def _latency_count(
    rows: tuple[InformationFreshnessRefreshSlaReadinessRow, ...],
) -> Decimal:
    return _decimal_count(
        sum(
            1
            for row in rows
            if any(
                reason_code in row.reason_codes
                for reason_code in (
                    MARKET_DATA_LATENCY_BREACH_REASON,
                    EXTERNAL_EVIDENCE_LATENCY_BREACH_REASON,
                    RESEARCH_PACKET_LATENCY_BREACH_REASON,
                )
            )
        ),
    )


def _refresh_count(
    rows: tuple[InformationFreshnessRefreshSlaReadinessRow, ...],
) -> Decimal:
    return _decimal_count(
        sum(
            1
            for row in rows
            if any(
                reason_code in row.reason_codes
                for reason_code in (
                    MARKET_DATA_REFRESH_BREACH_REASON,
                    EXTERNAL_EVIDENCE_REFRESH_BREACH_REASON,
                    RESEARCH_PACKET_REFRESH_BREACH_REASON,
                )
            )
        ),
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_WEIGHT:
            raise ValueError(f"{field_name} must contain known values")
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")
    return value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_exact(field_name, value)


def _require_ratio(field_name: str, value: Decimal) -> None:
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")


def _quantize_exact(field_name: str, value: Decimal) -> Decimal:
    quantized = _quantize(value)
    if value != quantized:
        raise ValueError(f"{field_name} must use six decimal places")
    return quantized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_phase_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        field_value = getattr(value, field_name)
        if type(field_value) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if field_value is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _snapshot_config(
    config: object,
) -> InformationFreshnessRefreshSlaReadinessConfig:
    _require_exact_type(
        "effective_config",
        config,
        InformationFreshnessRefreshSlaReadinessConfig,
    )
    return InformationFreshnessRefreshSlaReadinessConfig(
        **{
            field.name: getattr(config, field.name)
            for field in fields(InformationFreshnessRefreshSlaReadinessConfig)
        },
    )


def _reject_forbidden_public_payload(label: str, value: object) -> None:
    _reject_forbidden_public_value(label, _json_ready(value))


def _reject_forbidden_public_value(label: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(token in lowered for token in FORBIDDEN_PUBLIC_TEXT_TOKENS):
            raise ValueError(f"forbidden public value in {label}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if any(token in key.lower() for token in FORBIDDEN_PUBLIC_TEXT_TOKENS):
                raise ValueError(f"forbidden public field in {label}")
            _reject_forbidden_public_value(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_forbidden_public_value(label, item)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError(f"forbidden public value type in {label}")


def _report_public_payload_values(
    report: InformationFreshnessRefreshSlaReadinessReport,
) -> dict[str, object]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report must convert to a JSON object")
    payload.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    return payload


def _report_derived_validation_digest(
    report: InformationFreshnessRefreshSlaReadinessReport,
) -> str:
    return _derived_validation_digest(_report_public_payload_values(report))


def _validate_report_derived_validation_digest(
    report: InformationFreshnessRefreshSlaReadinessReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


def _validate_public_payload_derived_validation_digest(payload: dict[str, object]) -> None:
    digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _derived_validation_digest(payload: dict[str, object]) -> str:
    payload_without_digest = dict(payload)
    payload_without_digest.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    digest_payload = json.dumps(
        payload_without_digest,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(
        ("information_freshness_refresh_sla_readiness|" + digest_payload).encode(
            "utf-8",
        ),
    ).hexdigest()


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be exactly datetime")
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (float, int):
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _require_public_payload_fields(payload: dict[str, object]) -> None:
    for field_name in REPORT_PAYLOAD_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(REPORT_PAYLOAD_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public field: {extra_fields[0]}")


def _require_public_payload_json_values(payload: dict[str, object]) -> None:
    _json_ready(payload)


def _copy_public_mapping(value: Mapping[object, object]) -> dict[str, object]:
    return {
        key: _copy_public_json_value(item)  # type: ignore[misc]
        for key, item in value.items()
    }


def _copy_public_json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return _copy_public_mapping(value)
    if isinstance(value, list):
        return [_copy_public_json_value(item) for item in value]
    return value


def _freeze_json_object(value: dict[str, object]) -> _FrozenJsonObject:
    return _FrozenJsonObject(
        {key: _freeze_json_value(item) for key, item in value.items()},
    )


def _freeze_json_value(value: object) -> object:
    if type(value) is dict:
        return _freeze_json_object(value)
    if type(value) is list:
        return _FrozenJsonArray(_freeze_json_value(item) for item in value)
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("public payload must contain only JSON values")
