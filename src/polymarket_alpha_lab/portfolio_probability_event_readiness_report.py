from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_CONFIG_VERSION = "portfolio-probability-event-readiness-report-v0"
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
READINESS_STATUSES = ("pass", "watch", "blocked")
REASON_SEQUENCE = (
    "same_outcome_dependency_block",
    "same_outcome_dependency_watch",
    "correlation_cluster_concentration_block",
    "correlation_cluster_concentration_watch",
    "event_category_concentration_block",
    "event_category_concentration_watch",
    "capital_lockup_concentration_block",
    "capital_lockup_concentration_watch",
    "extended_lockup_block",
    "extended_lockup_watch",
    "negative_edge_after_lockup_watch",
    "low_exit_liquidity_watch",
    "portfolio_probability_event_readiness_pass",
)
MANUAL_NEXT_STEPS = (
    "proceed_with_paper_portfolio_review",
    "manual_review_portfolio_concentration",
    "do_not_allocate_until_portfolio_blockers_clear",
)
CONFIG_PAYLOAD_FIELDS = (
    "config_version",
    "same_outcome_watch_concentration",
    "same_outcome_block_concentration",
    "correlation_cluster_watch_concentration",
    "correlation_cluster_block_concentration",
    "event_category_watch_concentration",
    "event_category_block_concentration",
    "capital_lockup_watch_concentration",
    "capital_lockup_block_concentration",
    "lockup_watch_days",
    "lockup_block_days",
    "minimum_exit_liquidity_usdc",
    "paper_only",
    "report_only",
    "readonly",
)
CONFIG_DECIMAL_FIELDS = CONFIG_PAYLOAD_FIELDS[1:12]
ROW_PAYLOAD_FIELDS = (
    "candidate_id",
    "outcome_family",
    "event_category",
    "correlation_cluster",
    "yes_probability_exposure",
    "no_probability_exposure",
    "total_probability_exposure",
    "net_probability_exposure",
    "capital_lockup_usdc",
    "time_to_resolution_days",
    "expected_edge",
    "edge_after_lockup",
    "exit_liquidity_usdc",
    "outcome_family_concentration",
    "correlation_cluster_concentration",
    "event_category_concentration",
    "capital_lockup_concentration",
    "readiness_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_DECIMAL_FIELDS = ROW_PAYLOAD_FIELDS[4:17]
REPORT_PAYLOAD_FIELDS = (
    "config_version",
    "effective_config",
    "candidate_count",
    "total_probability_exposure",
    "total_capital_lockup_usdc",
    "max_outcome_family_concentration",
    "max_correlation_cluster_concentration",
    "max_event_category_concentration",
    "max_capital_lockup_concentration",
    "blocker_count",
    "watch_count",
    "pass_count",
    "readiness_status",
    "reason_codes",
    "manual_next_step",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)
REPORT_COUNT_FIELDS = (
    "candidate_count",
    "blocker_count",
    "watch_count",
    "pass_count",
)
REPORT_DECIMAL_FIELDS = (
    "total_probability_exposure",
    "total_capital_lockup_usdc",
    "max_outcome_family_concentration",
    "max_correlation_cluster_concentration",
    "max_event_category_concentration",
    "max_capital_lockup_concentration",
)


class PortfolioProbabilityEventReadinessPayload(dict[str, object]):
    __slots__ = ("__sealed",)

    def __init__(self, value: Mapping[str, object]) -> None:
        if getattr(
            self,
            "_PortfolioProbabilityEventReadinessPayload__sealed",
            False,
        ):
            raise TypeError("payload is immutable")
        super().__init__(value)
        self.__sealed = True

    def __readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("payload is immutable")

    __setitem__ = __readonly
    __delitem__ = __readonly
    clear = __readonly
    pop = __readonly
    popitem = __readonly
    setdefault = __readonly
    update = __readonly
    __ior__ = __readonly


class PortfolioProbabilityEventReadinessArray(tuple[Any, ...]):
    def append(self, value: object) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: object) -> None:
        raise TypeError("payload is immutable")


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class PortfolioProbabilityEventReadinessConfig(_FinalDataclass):
    config_version: str = DEFAULT_CONFIG_VERSION
    same_outcome_watch_concentration: Decimal = Decimal("0.400000")
    same_outcome_block_concentration: Decimal = Decimal("0.650000")
    correlation_cluster_watch_concentration: Decimal = Decimal("0.400000")
    correlation_cluster_block_concentration: Decimal = Decimal("0.650000")
    event_category_watch_concentration: Decimal = Decimal("0.500000")
    event_category_block_concentration: Decimal = Decimal("0.750000")
    capital_lockup_watch_concentration: Decimal = Decimal("0.500000")
    capital_lockup_block_concentration: Decimal = Decimal("0.800000")
    lockup_watch_days: Decimal = Decimal("14.000000")
    lockup_block_days: Decimal = Decimal("30.000000")
    minimum_exit_liquidity_usdc: Decimal = Decimal("100.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "same_outcome_watch_concentration",
            "same_outcome_block_concentration",
            "correlation_cluster_watch_concentration",
            "correlation_cluster_block_concentration",
            "event_category_watch_concentration",
            "event_category_block_concentration",
            "capital_lockup_watch_concentration",
            "capital_lockup_block_concentration",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lockup_watch_days",
            "lockup_block_days",
            "minimum_exit_liquidity_usdc",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_sequence(
            "same_outcome",
            self.same_outcome_watch_concentration,
            self.same_outcome_block_concentration,
        )
        _require_threshold_sequence(
            "correlation_cluster",
            self.correlation_cluster_watch_concentration,
            self.correlation_cluster_block_concentration,
        )
        _require_threshold_sequence(
            "event_category",
            self.event_category_watch_concentration,
            self.event_category_block_concentration,
        )
        _require_threshold_sequence(
            "capital_lockup",
            self.capital_lockup_watch_concentration,
            self.capital_lockup_block_concentration,
        )
        _require_threshold_sequence(
            "lockup",
            self.lockup_watch_days,
            self.lockup_block_days,
        )
        _require_flags("config", self)


@dataclass(frozen=True)
class PortfolioProbabilityEventReadinessInput(_FinalDataclass):
    candidate_id: str
    outcome_family: str
    event_category: str
    correlation_cluster: str
    yes_probability_exposure: Decimal
    no_probability_exposure: Decimal
    capital_lockup_usdc: Decimal
    time_to_resolution_days: Decimal
    expected_edge: Decimal
    exit_liquidity_usdc: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "outcome_family",
            "event_category",
            "correlation_cluster",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "yes_probability_exposure",
            "no_probability_exposure",
            "capital_lockup_usdc",
            "time_to_resolution_days",
            "exit_liquidity_usdc",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_edge",
            _require_decimal("expected_edge", self.expected_edge),
        )
        _require_flags("input", self)


@dataclass(frozen=True)
class PortfolioProbabilityEventReadinessRow(_FinalDataclass):
    candidate_id: str
    outcome_family: str
    event_category: str
    correlation_cluster: str
    yes_probability_exposure: Decimal
    no_probability_exposure: Decimal
    total_probability_exposure: Decimal
    net_probability_exposure: Decimal
    capital_lockup_usdc: Decimal
    time_to_resolution_days: Decimal
    expected_edge: Decimal
    edge_after_lockup: Decimal
    exit_liquidity_usdc: Decimal
    outcome_family_concentration: Decimal
    correlation_cluster_concentration: Decimal
    event_category_concentration: Decimal
    capital_lockup_concentration: Decimal
    readiness_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PortfolioProbabilityEventReadinessRow:
            raise ValueError("row must be exactly PortfolioProbabilityEventReadinessRow")
        for field_name in (
            "candidate_id",
            "outcome_family",
            "event_category",
            "correlation_cluster",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "yes_probability_exposure",
            "no_probability_exposure",
            "total_probability_exposure",
            "capital_lockup_usdc",
            "time_to_resolution_days",
            "exit_liquidity_usdc",
        ):
            _require_stored_nonnegative_decimal(
                field_name,
                getattr(self, field_name),
            )
        for field_name in (
            "net_probability_exposure",
            "expected_edge",
            "edge_after_lockup",
        ):
            _require_stored_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "outcome_family_concentration",
            "correlation_cluster_concentration",
            "event_category_concentration",
            "capital_lockup_concentration",
        ):
            _require_stored_ratio(field_name, getattr(self, field_name))
        _require_member("readiness_status", self.readiness_status, READINESS_STATUSES)
        _normalize_reason_codes(self.reason_codes)
        _validate_row_consistency(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class PortfolioProbabilityEventReadinessReport(_FinalDataclass):
    config_version: str
    effective_config: PortfolioProbabilityEventReadinessConfig
    candidate_count: Decimal
    total_probability_exposure: Decimal
    total_capital_lockup_usdc: Decimal
    max_outcome_family_concentration: Decimal
    max_correlation_cluster_concentration: Decimal
    max_event_category_concentration: Decimal
    max_capital_lockup_concentration: Decimal
    blocker_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    readiness_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    rows: tuple[PortfolioProbabilityEventReadinessRow, ...]
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _validate_report_object(self)

    @property
    def public_payload(self) -> PortfolioProbabilityEventReadinessPayload:
        return portfolio_probability_event_readiness_report_payload(self)


def build_portfolio_probability_event_readiness_report(
    rows: Iterable[PortfolioProbabilityEventReadinessInput],
    *,
    config: PortfolioProbabilityEventReadinessConfig,
) -> PortfolioProbabilityEventReadinessReport:
    if type(config) is not PortfolioProbabilityEventReadinessConfig:
        raise ValueError("config must be PortfolioProbabilityEventReadinessConfig")
    _validate_config_object(config)
    effective_config = _copy_config(config)
    inputs = tuple(rows)
    for row in inputs:
        if type(row) is not PortfolioProbabilityEventReadinessInput:
            raise ValueError("rows must contain PortfolioProbabilityEventReadinessInput")
        _validate_input_object(row)
    _require_unique_candidate_ids(inputs)

    total_exposure = _sum_decimal(_probability_exposure(row) for row in inputs)
    total_lockup = _sum_decimal(row.capital_lockup_usdc for row in inputs)
    outcome_totals = _bucket_totals(inputs, "outcome_family")
    cluster_totals = _bucket_totals(inputs, "correlation_cluster")
    category_totals = _bucket_totals(inputs, "event_category")
    lockup_totals = _lockup_totals(inputs, "correlation_cluster")
    report_rows = tuple(
        sorted(
            (
                _report_row(
                    row,
                    config=effective_config,
                    total_exposure=total_exposure,
                    total_lockup=total_lockup,
                    outcome_family_total=outcome_totals[row.outcome_family],
                    correlation_cluster_total=cluster_totals[row.correlation_cluster],
                    event_category_total=category_totals[row.event_category],
                    capital_lockup_cluster_total=lockup_totals[row.correlation_cluster],
                )
                for row in inputs
            ),
            key=lambda row: row.candidate_id,
        ),
    )
    reasons = _report_reasons(report_rows)
    status = _highest_readiness_status(report_rows)
    values: dict[str, object] = {
        "config_version": effective_config.config_version,
        "effective_config": effective_config,
        "candidate_count": _count_decimal(len(report_rows)),
        "total_probability_exposure": total_exposure,
        "total_capital_lockup_usdc": total_lockup,
        "max_outcome_family_concentration": _max_decimal(
            row.outcome_family_concentration for row in report_rows
        ),
        "max_correlation_cluster_concentration": _max_decimal(
            row.correlation_cluster_concentration for row in report_rows
        ),
        "max_event_category_concentration": _max_decimal(
            row.event_category_concentration for row in report_rows
        ),
        "max_capital_lockup_concentration": _max_decimal(
            row.capital_lockup_concentration for row in report_rows
        ),
        "blocker_count": _count_decimal(
            sum(1 for row in report_rows if row.readiness_status == "blocked"),
        ),
        "watch_count": _count_decimal(
            sum(1 for row in report_rows if row.readiness_status == "watch"),
        ),
        "pass_count": _count_decimal(
            sum(1 for row in report_rows if row.readiness_status == "pass"),
        ),
        "readiness_status": status,
        "reason_codes": reasons,
        "manual_next_step": _manual_next_step(status),
        "rows": report_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return PortfolioProbabilityEventReadinessReport(
        **values,
        payload_digest=_payload_digest_from_values(values),
    )


def portfolio_probability_event_readiness_report_payload(
    report: PortfolioProbabilityEventReadinessReport | Mapping[str, object],
) -> PortfolioProbabilityEventReadinessPayload:
    if type(report) is PortfolioProbabilityEventReadinessReport:
        _validate_report_object(report)
        payload = _report_payload_items(report, payload_digest=report.payload_digest)
    elif isinstance(report, Mapping):
        payload = _materialize_public_payload(report)
    else:
        raise ValueError("report must be a readiness report or public payload")
    return _freeze_json_object(payload)


def portfolio_probability_event_readiness_report_payload_digest(
    report: PortfolioProbabilityEventReadinessReport | Mapping[str, object],
) -> str:
    if type(report) is PortfolioProbabilityEventReadinessReport:
        _validate_report_object(report)
        return report.payload_digest
    if isinstance(report, Mapping):
        payload = _materialize_public_payload(report)
        return _require_digest("payload_digest", payload["payload_digest"])
    raise ValueError("report must be a readiness report or public payload")


def _payload_digest_from_values(values: Mapping[str, object]) -> str:
    return _report_payload_digest(
        _report_payload_values(values, payload_digest=""),
    )


def _report_payload_items(
    report: PortfolioProbabilityEventReadinessReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    values: dict[str, object] = {
        field_name: getattr(report, field_name)
        for field_name in REPORT_PAYLOAD_FIELDS
        if field_name != "payload_digest"
    }
    return _report_payload_values(values, payload_digest=payload_digest)


def _report_payload_values(
    values: Mapping[str, object],
    *,
    payload_digest: str,
) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "effective_config": _config_payload_items(values["effective_config"]),
        "candidate_count": _decimal_string(values["candidate_count"]),
        "total_probability_exposure": _decimal_string(
            values["total_probability_exposure"],
        ),
        "total_capital_lockup_usdc": _decimal_string(
            values["total_capital_lockup_usdc"],
        ),
        "max_outcome_family_concentration": _decimal_string(
            values["max_outcome_family_concentration"],
        ),
        "max_correlation_cluster_concentration": _decimal_string(
            values["max_correlation_cluster_concentration"],
        ),
        "max_event_category_concentration": _decimal_string(
            values["max_event_category_concentration"],
        ),
        "max_capital_lockup_concentration": _decimal_string(
            values["max_capital_lockup_concentration"],
        ),
        "blocker_count": _decimal_string(values["blocker_count"]),
        "watch_count": _decimal_string(values["watch_count"]),
        "pass_count": _decimal_string(values["pass_count"]),
        "readiness_status": values["readiness_status"],
        "reason_codes": list(values["reason_codes"]),
        "manual_next_step": values["manual_next_step"],
        "rows": tuple(_row_payload_items(row) for row in values["rows"]),
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "payload_digest": payload_digest,
    }


def _config_payload_items(config: object) -> dict[str, object]:
    if type(config) is not PortfolioProbabilityEventReadinessConfig:
        raise ValueError("effective_config must be exactly config")
    return {
        field_name: (
            _decimal_string(getattr(config, field_name))
            if field_name in CONFIG_DECIMAL_FIELDS
            else getattr(config, field_name)
        )
        for field_name in CONFIG_PAYLOAD_FIELDS
    }


def _row_payload_items(row: object) -> dict[str, object]:
    if type(row) is not PortfolioProbabilityEventReadinessRow:
        raise ValueError("rows must contain exact readiness rows")
    return {
        field_name: (
            _decimal_string(getattr(row, field_name))
            if field_name in ROW_DECIMAL_FIELDS
            else list(getattr(row, field_name))
            if field_name == "reason_codes"
            else getattr(row, field_name)
        )
        for field_name in ROW_PAYLOAD_FIELDS
    }


def _materialize_public_payload(
    payload: Mapping[str, object],
) -> dict[str, object]:
    _require_public_mapping("public payload", payload, REPORT_PAYLOAD_FIELDS)
    effective_config = _config_from_public(payload["effective_config"])
    rows = tuple(
        _row_from_public(item)
        for item in _require_public_array("rows", payload["rows"])
    )
    report = PortfolioProbabilityEventReadinessReport(
        config_version=payload["config_version"],
        effective_config=effective_config,
        candidate_count=_parse_public_count("candidate_count", payload["candidate_count"]),
        total_probability_exposure=_parse_public_decimal(
            "total_probability_exposure",
            payload["total_probability_exposure"],
        ),
        total_capital_lockup_usdc=_parse_public_decimal(
            "total_capital_lockup_usdc",
            payload["total_capital_lockup_usdc"],
        ),
        max_outcome_family_concentration=_parse_public_decimal(
            "max_outcome_family_concentration",
            payload["max_outcome_family_concentration"],
        ),
        max_correlation_cluster_concentration=_parse_public_decimal(
            "max_correlation_cluster_concentration",
            payload["max_correlation_cluster_concentration"],
        ),
        max_event_category_concentration=_parse_public_decimal(
            "max_event_category_concentration",
            payload["max_event_category_concentration"],
        ),
        max_capital_lockup_concentration=_parse_public_decimal(
            "max_capital_lockup_concentration",
            payload["max_capital_lockup_concentration"],
        ),
        blocker_count=_parse_public_count("blocker_count", payload["blocker_count"]),
        watch_count=_parse_public_count("watch_count", payload["watch_count"]),
        pass_count=_parse_public_count("pass_count", payload["pass_count"]),
        readiness_status=payload["readiness_status"],
        reason_codes=tuple(
            _require_public_array("reason_codes", payload["reason_codes"]),
        ),
        manual_next_step=payload["manual_next_step"],
        rows=rows,
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
        payload_digest=payload["payload_digest"],
    )
    return _report_payload_items(report, payload_digest=report.payload_digest)


def _config_from_public(value: object) -> PortfolioProbabilityEventReadinessConfig:
    config = _require_public_mapping(
        "effective_config",
        value,
        CONFIG_PAYLOAD_FIELDS,
    )
    return PortfolioProbabilityEventReadinessConfig(
        **{
            field_name: (
                _parse_public_decimal(field_name, config[field_name])
                if field_name in CONFIG_DECIMAL_FIELDS
                else config[field_name]
            )
            for field_name in CONFIG_PAYLOAD_FIELDS
        },
    )


def _row_from_public(value: object) -> PortfolioProbabilityEventReadinessRow:
    row = _require_public_mapping("row", value, ROW_PAYLOAD_FIELDS)
    return PortfolioProbabilityEventReadinessRow(
        **{
            field_name: (
                _parse_public_decimal(field_name, row[field_name])
                if field_name in ROW_DECIMAL_FIELDS
                else tuple(_require_public_array(field_name, row[field_name]))
                if field_name == "reason_codes"
                else row[field_name]
            )
            for field_name in ROW_PAYLOAD_FIELDS
        },
    )


def _require_public_mapping(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> Mapping[str, object]:
    if type(value) not in {dict, PortfolioProbabilityEventReadinessPayload}:
        raise ValueError(f"{label} must be an exact mapping")
    if set(value) != set(expected_fields):
        raise ValueError(f"{label} fields must match the contract")
    return value


def _require_public_array(field_name: str, value: object) -> tuple[object, ...]:
    if type(value) is not list and type(value) is not PortfolioProbabilityEventReadinessArray:
        raise ValueError(f"{field_name} must be an exact array")
    return tuple(value)


def _parse_public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a six decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a six decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if parsed.as_tuple().exponent != QUANTUM.as_tuple().exponent or str(parsed) != value:
        raise ValueError(f"{field_name} must be a six decimal string")
    if parsed.is_zero() and parsed.as_tuple().sign:
        raise ValueError(f"{field_name} must not use signed zero")
    return parsed


def _parse_public_count(field_name: str, value: object) -> Decimal:
    parsed = _parse_public_decimal(field_name, value)
    if parsed != parsed.to_integral_value():
        raise ValueError(f"{field_name} must be an integer decimal string")
    return parsed.quantize(COUNT_QUANTUM)


def _decimal_string(value: object) -> str:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("payload numerics must be Decimal")
    if value.is_zero() and value.as_tuple().sign:
        raise ValueError("payload numerics must not use signed zero")
    with localcontext(DECIMAL_CONTEXT):
        return str(value.quantize(QUANTUM))


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _report_payload_digest(payload: Mapping[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload["payload_digest"] = ""
    encoded = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _freeze_json_object(value: dict[str, object]) -> PortfolioProbabilityEventReadinessPayload:
    return PortfolioProbabilityEventReadinessPayload(
        {field_name: _freeze_json_value(item) for field_name, item in value.items()},
    )


def _freeze_json_value(value: object) -> object:
    if type(value) is dict:
        return _freeze_json_object(value)
    if type(value) in {list, tuple}:
        return PortfolioProbabilityEventReadinessArray(
            _freeze_json_value(item) for item in value
        )
    return value


def _report_row(
    row: PortfolioProbabilityEventReadinessInput,
    *,
    config: PortfolioProbabilityEventReadinessConfig,
    total_exposure: Decimal,
    total_lockup: Decimal,
    outcome_family_total: Decimal,
    correlation_cluster_total: Decimal,
    event_category_total: Decimal,
    capital_lockup_cluster_total: Decimal,
) -> PortfolioProbabilityEventReadinessRow:
    exposure = _probability_exposure(row)
    net_exposure = _quantize(row.yes_probability_exposure - row.no_probability_exposure)
    outcome_family_concentration = _ratio(outcome_family_total, total_exposure)
    correlation_cluster_concentration = _ratio(correlation_cluster_total, total_exposure)
    event_category_concentration = _ratio(event_category_total, total_exposure)
    capital_lockup_concentration = _ratio(capital_lockup_cluster_total, total_lockup)
    edge_after_lockup = row.expected_edge
    reasons = _row_reasons(
        outcome_family_concentration=outcome_family_concentration,
        correlation_cluster_concentration=correlation_cluster_concentration,
        event_category_concentration=event_category_concentration,
        capital_lockup_concentration=capital_lockup_concentration,
        time_to_resolution_days=row.time_to_resolution_days,
        edge_after_lockup=edge_after_lockup,
        exit_liquidity_usdc=row.exit_liquidity_usdc,
        config=config,
    )
    return PortfolioProbabilityEventReadinessRow(
        candidate_id=row.candidate_id,
        outcome_family=row.outcome_family,
        event_category=row.event_category,
        correlation_cluster=row.correlation_cluster,
        yes_probability_exposure=row.yes_probability_exposure,
        no_probability_exposure=row.no_probability_exposure,
        total_probability_exposure=exposure,
        net_probability_exposure=net_exposure,
        capital_lockup_usdc=row.capital_lockup_usdc,
        time_to_resolution_days=row.time_to_resolution_days,
        expected_edge=row.expected_edge,
        edge_after_lockup=edge_after_lockup,
        exit_liquidity_usdc=row.exit_liquidity_usdc,
        outcome_family_concentration=outcome_family_concentration,
        correlation_cluster_concentration=correlation_cluster_concentration,
        event_category_concentration=event_category_concentration,
        capital_lockup_concentration=capital_lockup_concentration,
        readiness_status=_row_readiness_status(reasons),
        reason_codes=reasons,
    )


def _row_reasons(
    *,
    outcome_family_concentration: Decimal,
    correlation_cluster_concentration: Decimal,
    event_category_concentration: Decimal,
    capital_lockup_concentration: Decimal,
    time_to_resolution_days: Decimal,
    edge_after_lockup: Decimal,
    exit_liquidity_usdc: Decimal,
    config: PortfolioProbabilityEventReadinessConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_concentration_reason(
        reasons,
        "same_outcome_dependency",
        outcome_family_concentration,
        config.same_outcome_watch_concentration,
        config.same_outcome_block_concentration,
    )
    _append_concentration_reason(
        reasons,
        "correlation_cluster_concentration",
        correlation_cluster_concentration,
        config.correlation_cluster_watch_concentration,
        config.correlation_cluster_block_concentration,
    )
    _append_concentration_reason(
        reasons,
        "event_category_concentration",
        event_category_concentration,
        config.event_category_watch_concentration,
        config.event_category_block_concentration,
    )
    _append_concentration_reason(
        reasons,
        "capital_lockup_concentration",
        capital_lockup_concentration,
        config.capital_lockup_watch_concentration,
        config.capital_lockup_block_concentration,
    )
    has_blocker = any(_reason_blocks_portfolio(reason) for reason in reasons)
    if time_to_resolution_days >= config.lockup_block_days:
        reasons.append("extended_lockup_block")
    elif not has_blocker and time_to_resolution_days >= config.lockup_watch_days:
        reasons.append("extended_lockup_watch")
    if not has_blocker and edge_after_lockup <= ZERO:
        reasons.append("negative_edge_after_lockup_watch")
    if exit_liquidity_usdc < config.minimum_exit_liquidity_usdc:
        reasons.append("low_exit_liquidity_watch")
    if not reasons:
        reasons.append("portfolio_probability_event_readiness_pass")
    return tuple(reason for reason in REASON_SEQUENCE if reason in reasons)


def _append_concentration_reason(
    reasons: list[str],
    stem: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value >= block_threshold:
        reasons.append(f"{stem}_block")
    elif value >= watch_threshold:
        reasons.append(f"{stem}_watch")


def _report_reasons(
    rows: tuple[PortfolioProbabilityEventReadinessRow, ...],
) -> tuple[str, ...]:
    reasons = tuple(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != "portfolio_probability_event_readiness_pass"
    )
    if not reasons:
        return ("portfolio_probability_event_readiness_pass",)
    blocker_reasons = frozenset(
        reason for reason in reasons if _reason_blocks_portfolio(reason)
    )
    if blocker_reasons:
        material_reasons = blocker_reasons.union(
            reason for reason in reasons if reason == "low_exit_liquidity_watch"
        )
    else:
        material_reasons = frozenset(reasons)
    return tuple(reason for reason in REASON_SEQUENCE if reason in material_reasons)


def _row_readiness_status(reason_codes: tuple[str, ...]) -> str:
    if any(_reason_blocks_portfolio(reason) for reason in reason_codes):
        return "blocked"
    if reason_codes != ("portfolio_probability_event_readiness_pass",):
        return "watch"
    return "pass"


def _reason_blocks_portfolio(reason_code: str) -> bool:
    return reason_code.endswith("_block")


def _highest_readiness_status(
    rows: tuple[PortfolioProbabilityEventReadinessRow, ...],
) -> str:
    if any(row.readiness_status == "blocked" for row in rows):
        return "blocked"
    if any(row.readiness_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _manual_next_step(readiness_status: str) -> str:
    if readiness_status == "blocked":
        return "do_not_allocate_until_portfolio_blockers_clear"
    if readiness_status == "watch":
        return "manual_review_portfolio_concentration"
    return "proceed_with_paper_portfolio_review"


def _probability_exposure(row: PortfolioProbabilityEventReadinessInput) -> Decimal:
    return _quantize(row.yes_probability_exposure + row.no_probability_exposure)


def _bucket_totals(
    rows: tuple[PortfolioProbabilityEventReadinessInput, ...],
    field_name: str,
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in rows:
        key = getattr(row, field_name)
        current = totals.get(key, ZERO)
        totals[key] = _quantize(current + _probability_exposure(row))
    return totals


def _lockup_totals(
    rows: tuple[PortfolioProbabilityEventReadinessInput, ...],
    field_name: str,
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in rows:
        key = getattr(row, field_name)
        current = totals.get(key, ZERO)
        totals[key] = _quantize(current + row.capital_lockup_usdc)
    return totals


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return max(normalized)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized.is_zero():
        return ZERO
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value.quantize(COUNT_QUANTUM)


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must not exceed 1.000000")
    return decimal_value


def _require_stored_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must use six decimal places")
    if value.is_zero() and value.as_tuple().sign:
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _require_stored_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_stored_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_stored_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != COUNT_QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must use the count quantum")
    if value.is_zero() and value.as_tuple().sign:
        raise ValueError(f"{field_name} must not use signed zero")
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_stored_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_stored_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must not exceed 1.000000")
    return decimal_value


def _require_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be text")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    if normalized != value:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_threshold_sequence(
    label: str,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if watch_threshold > block_threshold:
        raise ValueError(f"{label} watch threshold must not exceed block threshold")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be exactly tuple")
    normalized = reason_codes
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason in normalized:
        if reason not in REASON_SEQUENCE:
            raise ValueError("reason_codes must be known")
    expected = tuple(reason for reason in REASON_SEQUENCE if reason in set(normalized))
    if normalized != expected:
        raise ValueError("reason_codes must be sorted and unique")
    return normalized


def _normalize_rows(
    rows: Iterable[PortfolioProbabilityEventReadinessRow],
) -> tuple[PortfolioProbabilityEventReadinessRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be exactly tuple")
    normalized = rows
    for row in normalized:
        if type(row) is not PortfolioProbabilityEventReadinessRow:
            raise ValueError("rows must contain PortfolioProbabilityEventReadinessRow")
        _validate_row_object(row)
    _require_unique_candidate_ids(normalized)
    if normalized != tuple(sorted(normalized, key=lambda row: row.candidate_id)):
        raise ValueError("rows must be sorted")
    return normalized


def _require_unique_candidate_ids(
    rows: Iterable[
        PortfolioProbabilityEventReadinessInput
        | PortfolioProbabilityEventReadinessRow
    ],
) -> None:
    seen: set[str] = set()
    for row in rows:
        if row.candidate_id in seen:
            raise ValueError("candidate_id values must be unique")
        seen.add(row.candidate_id)


def _require_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _validate_config_object(config: PortfolioProbabilityEventReadinessConfig) -> None:
    if type(config) is not PortfolioProbabilityEventReadinessConfig:
        raise ValueError("config must be exactly PortfolioProbabilityEventReadinessConfig")
    _require_text("config_version", config.config_version)
    if config.config_version != DEFAULT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported version")
    for field_name in (
        "same_outcome_watch_concentration",
        "same_outcome_block_concentration",
        "correlation_cluster_watch_concentration",
        "correlation_cluster_block_concentration",
        "event_category_watch_concentration",
        "event_category_block_concentration",
        "capital_lockup_watch_concentration",
        "capital_lockup_block_concentration",
    ):
        _require_stored_ratio(field_name, getattr(config, field_name))
    for field_name in (
        "lockup_watch_days",
        "lockup_block_days",
        "minimum_exit_liquidity_usdc",
    ):
        _require_stored_nonnegative_decimal(field_name, getattr(config, field_name))
    _require_threshold_sequence(
        "same_outcome",
        config.same_outcome_watch_concentration,
        config.same_outcome_block_concentration,
    )
    _require_threshold_sequence(
        "correlation_cluster",
        config.correlation_cluster_watch_concentration,
        config.correlation_cluster_block_concentration,
    )
    _require_threshold_sequence(
        "event_category",
        config.event_category_watch_concentration,
        config.event_category_block_concentration,
    )
    _require_threshold_sequence(
        "capital_lockup",
        config.capital_lockup_watch_concentration,
        config.capital_lockup_block_concentration,
    )
    _require_threshold_sequence(
        "lockup",
        config.lockup_watch_days,
        config.lockup_block_days,
    )
    _require_flags("config", config)


def _copy_config(
    config: PortfolioProbabilityEventReadinessConfig,
) -> PortfolioProbabilityEventReadinessConfig:
    return PortfolioProbabilityEventReadinessConfig(
        **{field_name: getattr(config, field_name) for field_name in CONFIG_PAYLOAD_FIELDS},
    )


def _validate_input_object(row: PortfolioProbabilityEventReadinessInput) -> None:
    if type(row) is not PortfolioProbabilityEventReadinessInput:
        raise ValueError("input must be exactly PortfolioProbabilityEventReadinessInput")
    for field_name in (
        "candidate_id",
        "outcome_family",
        "event_category",
        "correlation_cluster",
    ):
        _require_text(field_name, getattr(row, field_name))
    for field_name in (
        "yes_probability_exposure",
        "no_probability_exposure",
        "capital_lockup_usdc",
        "time_to_resolution_days",
        "exit_liquidity_usdc",
    ):
        _require_stored_nonnegative_decimal(field_name, getattr(row, field_name))
    _require_stored_decimal("expected_edge", row.expected_edge)
    _require_flags("input", row)


def _validate_row_object(row: PortfolioProbabilityEventReadinessRow) -> None:
    if type(row) is not PortfolioProbabilityEventReadinessRow:
        raise ValueError("row must be exactly PortfolioProbabilityEventReadinessRow")
    for field_name in (
        "candidate_id",
        "outcome_family",
        "event_category",
        "correlation_cluster",
    ):
        _require_text(field_name, getattr(row, field_name))
    for field_name in (
        "yes_probability_exposure",
        "no_probability_exposure",
        "total_probability_exposure",
        "capital_lockup_usdc",
        "time_to_resolution_days",
        "exit_liquidity_usdc",
    ):
        _require_stored_nonnegative_decimal(field_name, getattr(row, field_name))
    for field_name in (
        "net_probability_exposure",
        "expected_edge",
        "edge_after_lockup",
    ):
        _require_stored_decimal(field_name, getattr(row, field_name))
    for field_name in (
        "outcome_family_concentration",
        "correlation_cluster_concentration",
        "event_category_concentration",
        "capital_lockup_concentration",
    ):
        _require_stored_ratio(field_name, getattr(row, field_name))
    _require_member("readiness_status", row.readiness_status, READINESS_STATUSES)
    _normalize_reason_codes(row.reason_codes)
    _validate_row_consistency(row)
    _require_flags("row", row)


def _validate_report_object(report: PortfolioProbabilityEventReadinessReport) -> None:
    if type(report) is not PortfolioProbabilityEventReadinessReport:
        raise ValueError("report must be exactly PortfolioProbabilityEventReadinessReport")
    _require_text("config_version", report.config_version)
    if report.config_version != DEFAULT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported version")
    _validate_config_object(report.effective_config)
    if report.effective_config.config_version != report.config_version:
        raise ValueError("effective_config config_version must match report")
    for field_name in REPORT_COUNT_FIELDS:
        _require_stored_count_decimal(field_name, getattr(report, field_name))
    for field_name in (
        "total_probability_exposure",
        "total_capital_lockup_usdc",
    ):
        _require_stored_nonnegative_decimal(field_name, getattr(report, field_name))
    for field_name in (
        "max_outcome_family_concentration",
        "max_correlation_cluster_concentration",
        "max_event_category_concentration",
        "max_capital_lockup_concentration",
    ):
        _require_stored_ratio(field_name, getattr(report, field_name))
    _require_member("readiness_status", report.readiness_status, READINESS_STATUSES)
    _normalize_reason_codes(report.reason_codes)
    _require_member("manual_next_step", report.manual_next_step, MANUAL_NEXT_STEPS)
    _normalize_rows(report.rows)
    _require_digest("payload_digest", report.payload_digest)
    _require_flags("report", report)
    _validate_report_consistency(report)


def _validate_row_consistency(row: PortfolioProbabilityEventReadinessRow) -> None:
    if row.total_probability_exposure != _quantize(
        row.yes_probability_exposure + row.no_probability_exposure,
    ):
        raise ValueError("total_probability_exposure must match yes plus no")
    if row.net_probability_exposure != _quantize(
        row.yes_probability_exposure - row.no_probability_exposure,
    ):
        raise ValueError("net_probability_exposure must match yes minus no")
    if row.edge_after_lockup != row.expected_edge:
        raise ValueError("edge_after_lockup must match expected_edge")
    expected_status = _row_readiness_status(row.reason_codes)
    if row.readiness_status != expected_status:
        raise ValueError("readiness_status must match reason_codes")


def _validate_report_consistency(
    report: PortfolioProbabilityEventReadinessReport,
) -> None:
    total_exposure = _sum_decimal(_probability_exposure(row) for row in report.rows)
    total_lockup = _sum_decimal(row.capital_lockup_usdc for row in report.rows)
    outcome_totals = _bucket_totals(report.rows, "outcome_family")
    cluster_totals = _bucket_totals(report.rows, "correlation_cluster")
    category_totals = _bucket_totals(report.rows, "event_category")
    lockup_totals = _lockup_totals(report.rows, "correlation_cluster")
    for row in report.rows:
        expected_outcome_concentration = _ratio(
            outcome_totals[row.outcome_family],
            total_exposure,
        )
        expected_cluster_concentration = _ratio(
            cluster_totals[row.correlation_cluster],
            total_exposure,
        )
        expected_category_concentration = _ratio(
            category_totals[row.event_category],
            total_exposure,
        )
        expected_lockup_concentration = _ratio(
            lockup_totals[row.correlation_cluster],
            total_lockup,
        )
        if row.outcome_family_concentration != expected_outcome_concentration:
            raise ValueError("outcome_family_concentration must match rows")
        if row.correlation_cluster_concentration != expected_cluster_concentration:
            raise ValueError("correlation_cluster_concentration must match rows")
        if row.event_category_concentration != expected_category_concentration:
            raise ValueError("event_category_concentration must match rows")
        if row.capital_lockup_concentration != expected_lockup_concentration:
            raise ValueError("capital_lockup_concentration must match rows")
        expected_reasons = _row_reasons(
            outcome_family_concentration=expected_outcome_concentration,
            correlation_cluster_concentration=expected_cluster_concentration,
            event_category_concentration=expected_category_concentration,
            capital_lockup_concentration=expected_lockup_concentration,
            time_to_resolution_days=row.time_to_resolution_days,
            edge_after_lockup=row.edge_after_lockup,
            exit_liquidity_usdc=row.exit_liquidity_usdc,
            config=report.effective_config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("row reason_codes must match effective_config")
        if row.readiness_status != _row_readiness_status(expected_reasons):
            raise ValueError("row readiness_status must match effective_config")
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.total_probability_exposure != total_exposure:
        raise ValueError("total_probability_exposure must match rows")
    if report.total_capital_lockup_usdc != total_lockup:
        raise ValueError("total_capital_lockup_usdc must match rows")
    if report.max_outcome_family_concentration != _max_decimal(
        row.outcome_family_concentration for row in report.rows
    ):
        raise ValueError("max_outcome_family_concentration must match rows")
    if report.max_correlation_cluster_concentration != _max_decimal(
        row.correlation_cluster_concentration for row in report.rows
    ):
        raise ValueError("max_correlation_cluster_concentration must match rows")
    if report.max_event_category_concentration != _max_decimal(
        row.event_category_concentration for row in report.rows
    ):
        raise ValueError("max_event_category_concentration must match rows")
    if report.max_capital_lockup_concentration != _max_decimal(
        row.capital_lockup_concentration for row in report.rows
    ):
        raise ValueError("max_capital_lockup_concentration must match rows")
    if report.blocker_count != _count_decimal(
        sum(1 for row in report.rows if row.readiness_status == "blocked"),
    ):
        raise ValueError("blocker_count must match rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in report.rows if row.readiness_status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _count_decimal(
        sum(1 for row in report.rows if row.readiness_status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.readiness_status != _highest_readiness_status(report.rows):
        raise ValueError("readiness_status must match rows")
    if report.reason_codes != _report_reasons(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.manual_next_step != _manual_next_step(report.readiness_status):
        raise ValueError("manual_next_step must match readiness_status")
    expected_digest = _report_payload_digest(
        _report_payload_items(report, payload_digest=""),
    )
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match report payload")
