"""Pure report-only information-gap diagnostic budget reducer."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVENT_INFORMATION_GAP_BUDGET_REPORT_CONFIG_VERSION",
    "ResearchStrategyEventInformationGapBudgetConfig",
    "ResearchStrategyEventInformationGapBudgetInput",
    "ResearchStrategyEventInformationGapBudgetReport",
    "ResearchStrategyEventInformationGapBudgetRow",
    "build_research_strategy_event_information_gap_budget_report",
    "research_strategy_event_information_gap_budget_report_digest",
    "research_strategy_event_information_gap_budget_report_payload",
    "validate_research_strategy_event_information_gap_budget_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_EVENT_INFORMATION_GAP_BUDGET_REPORT_CONFIG_VERSION = (
    "research-strategy-event-information-gap-budget-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DECIMAL_CONTEXT_PRECISION = 64
DECIMAL_CONTEXT_ROUNDING = ROUND_HALF_EVEN
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
PASS_REASON = "information_gap_priority_pass"
EMPTY_REASON = "information_gap_budget_no_unresolved_events"
REASON_PRIORITY = (
    "source_freshness_gap_block",
    "authority_gap_block",
    "team_coverage_gap_block",
    "resolution_proximity_block",
    "information_gap_pressure_block",
    "diagnostic_budget_share_block",
    "source_freshness_gap_watch",
    "authority_gap_watch",
    "team_coverage_gap_watch",
    "resolution_proximity_watch",
    "information_gap_pressure_watch",
    "diagnostic_budget_share_watch",
    PASS_REASON,
    EMPTY_REASON,
)
ROW_PAYLOAD_KEYS = (
    "row_number",
    "source_freshness_gap_score",
    "authority_gap_score",
    "team_coverage_gap_score",
    "resolution_proximity_score",
    "source_freshness_gap_weight",
    "authority_gap_weight",
    "team_coverage_gap_weight",
    "resolution_proximity_weight",
    "watch_component_gap_threshold",
    "block_component_gap_threshold",
    "watch_information_gap_pressure_threshold",
    "block_information_gap_pressure_threshold",
    "watch_diagnostic_budget_share_threshold",
    "block_diagnostic_budget_share_threshold",
    "information_gap_pressure",
    "diagnostic_budget_share",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "event_count",
    "pass_count",
    "watch_count",
    "block_count",
    "total_information_gap_pressure",
    "max_information_gap_pressure",
    "average_information_gap_pressure",
    "max_diagnostic_budget_share",
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
UNSAFE_PUBLIC_TERMS = (
    "candidate" "_" "id",
    "market" "_" "id",
    "market" "_" "slug",
    "question",
    "source" "_" "url",
    "source" "_" "text",
    "dsn",
    "table",
    "tok" "en",
    "private",
    "sec" "ret",
    "pass" "word",
    "api" "_" "key",
    "auth" "_" "token",
    "wal" "let",
    "bro" "ker",
    "or" "der",
    "can" "cel",
    "re" "place",
    "sign" "ing",
    "li" "ve " "trading",
    "data" "base",
    "net" "work",
    "://",
    "reco" "mmend" "ation",
    "siz" "ing",
    "b" "uy",
    "s" "ell",
)


class _FinalDataclass:
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True, slots=True)
class ResearchStrategyEventInformationGapBudgetConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVENT_INFORMATION_GAP_BUDGET_REPORT_CONFIG_VERSION
    )
    source_freshness_gap_weight: Decimal = Decimal("0.300000")
    authority_gap_weight: Decimal = Decimal("0.300000")
    team_coverage_gap_weight: Decimal = Decimal("0.200000")
    resolution_proximity_weight: Decimal = Decimal("0.200000")
    watch_component_gap_threshold: Decimal = Decimal("0.400000")
    block_component_gap_threshold: Decimal = Decimal("0.750000")
    watch_information_gap_pressure_threshold: Decimal = Decimal("0.350000")
    block_information_gap_pressure_threshold: Decimal = Decimal("0.700000")
    watch_diagnostic_budget_share_threshold: Decimal = Decimal("0.250000")
    block_diagnostic_budget_share_threshold: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEventInformationGapBudgetConfig,
            "config",
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVENT_INFORMATION_GAP_BUDGET_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "source_freshness_gap_weight",
            "authority_gap_weight",
            "team_coverage_gap_weight",
            "resolution_proximity_weight",
            "watch_component_gap_threshold",
            "block_component_gap_threshold",
            "watch_information_gap_pressure_threshold",
            "block_information_gap_pressure_threshold",
            "watch_diagnostic_budget_share_threshold",
            "block_diagnostic_budget_share_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config_values(
            source_freshness_gap_weight=self.source_freshness_gap_weight,
            authority_gap_weight=self.authority_gap_weight,
            team_coverage_gap_weight=self.team_coverage_gap_weight,
            resolution_proximity_weight=self.resolution_proximity_weight,
            watch_component_gap_threshold=self.watch_component_gap_threshold,
            block_component_gap_threshold=self.block_component_gap_threshold,
            watch_information_gap_pressure_threshold=(
                self.watch_information_gap_pressure_threshold
            ),
            block_information_gap_pressure_threshold=(
                self.block_information_gap_pressure_threshold
            ),
            watch_diagnostic_budget_share_threshold=(
                self.watch_diagnostic_budget_share_threshold
            ),
            block_diagnostic_budget_share_threshold=(
                self.block_diagnostic_budget_share_threshold
            ),
        )
        _require_hard_phase_flags("config", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyEventInformationGapBudgetInput(_FinalDataclass):
    event_ref: str
    source_freshness_gap_score: Decimal
    authority_gap_score: Decimal
    team_coverage_gap_score: Decimal
    resolution_proximity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEventInformationGapBudgetInput,
            "input",
        )
        _require_private_reference("event_ref", self.event_ref)
        for field_name in (
            "source_freshness_gap_score",
            "authority_gap_score",
            "team_coverage_gap_score",
            "resolution_proximity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_phase_flags("input", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyEventInformationGapBudgetRow(_FinalDataclass):
    row_number: Decimal
    source_freshness_gap_score: Decimal
    authority_gap_score: Decimal
    team_coverage_gap_score: Decimal
    resolution_proximity_score: Decimal
    source_freshness_gap_weight: Decimal
    authority_gap_weight: Decimal
    team_coverage_gap_weight: Decimal
    resolution_proximity_weight: Decimal
    watch_component_gap_threshold: Decimal
    block_component_gap_threshold: Decimal
    watch_information_gap_pressure_threshold: Decimal
    block_information_gap_pressure_threshold: Decimal
    watch_diagnostic_budget_share_threshold: Decimal
    block_diagnostic_budget_share_threshold: Decimal
    information_gap_pressure: Decimal
    diagnostic_budget_share: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEventInformationGapBudgetRow,
            "row",
        )
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        for field_name in (
            "source_freshness_gap_score",
            "authority_gap_score",
            "team_coverage_gap_score",
            "resolution_proximity_score",
            "source_freshness_gap_weight",
            "authority_gap_weight",
            "team_coverage_gap_weight",
            "resolution_proximity_weight",
            "watch_component_gap_threshold",
            "block_component_gap_threshold",
            "watch_information_gap_pressure_threshold",
            "block_information_gap_pressure_threshold",
            "watch_diagnostic_budget_share_threshold",
            "block_diagnostic_budget_share_threshold",
            "information_gap_pressure",
            "diagnostic_budget_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config_values(
            source_freshness_gap_weight=self.source_freshness_gap_weight,
            authority_gap_weight=self.authority_gap_weight,
            team_coverage_gap_weight=self.team_coverage_gap_weight,
            resolution_proximity_weight=self.resolution_proximity_weight,
            watch_component_gap_threshold=self.watch_component_gap_threshold,
            block_component_gap_threshold=self.block_component_gap_threshold,
            watch_information_gap_pressure_threshold=(
                self.watch_information_gap_pressure_threshold
            ),
            block_information_gap_pressure_threshold=(
                self.block_information_gap_pressure_threshold
            ),
            watch_diagnostic_budget_share_threshold=(
                self.watch_diagnostic_budget_share_threshold
            ),
            block_diagnostic_budget_share_threshold=(
                self.block_diagnostic_budget_share_threshold
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_phase_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyEventInformationGapBudgetReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_information_gap_pressure: Decimal
    max_information_gap_pressure: Decimal | None
    average_information_gap_pressure: Decimal | None
    max_diagnostic_budget_share: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyEventInformationGapBudgetRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEventInformationGapBudgetReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVENT_INFORMATION_GAP_BUDGET_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_information_gap_pressure",
            _normalize_nonnegative_decimal(
                "total_information_gap_pressure",
                self.total_information_gap_pressure,
            ),
        )
        for field_name in (
            "max_information_gap_pressure",
            "average_information_gap_pressure",
            "max_diagnostic_budget_share",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _normalize_ratio(field_name, value),
                )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_phase_flags("report", self)
        _validate_report(self)


@dataclass(frozen=True, slots=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def build_research_strategy_event_information_gap_budget_report(
    events: Iterable[ResearchStrategyEventInformationGapBudgetInput],
    *,
    config: ResearchStrategyEventInformationGapBudgetConfig,
    generated_at: datetime,
) -> ResearchStrategyEventInformationGapBudgetReport:
    if type(config) is not ResearchStrategyEventInformationGapBudgetConfig:
        raise ValueError(
            "config must be a ResearchStrategyEventInformationGapBudgetConfig",
        )
    _require_hard_phase_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_events = _normalize_inputs(events)
    base_rows = tuple(
        _base_row_from_input(item, config=config) for item in normalized_events
    )
    total_pressure = _sum_decimal(
        item["information_gap_pressure"] for item in base_rows
    )
    prepared_rows = tuple(
        sorted(
            (
                _prepared_row_with_share(
                    item,
                    total_information_gap_pressure=total_pressure,
                )
                for item in base_rows
            ),
            key=_prepared_row_sort_key,
        ),
    )
    rows = tuple(
        _row_from_prepared(row_number=_count(index + 1), prepared=item)
        for index, item in enumerate(prepared_rows)
    )
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "event_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "total_information_gap_pressure": total_pressure,
        "max_information_gap_pressure": (
            None
            if not rows
            else max(row.information_gap_pressure for row in rows)
        ),
        "average_information_gap_pressure": _average_pressure(rows),
        "max_diagnostic_budget_share": (
            None
            if not rows
            else max(row.diagnostic_budget_share for row in rows)
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyEventInformationGapBudgetReport(
        **report_values,
        derived_validation_digest=_report_digest_from_values(report_values),
    )


def research_strategy_event_information_gap_budget_report_payload(
    report: (
        ResearchStrategyEventInformationGapBudgetReport | Mapping[str, object]
    ),
) -> dict[str, object]:
    if type(report) is ResearchStrategyEventInformationGapBudgetReport:
        return _payload_from_report(report)
    if type(report) is dict:
        _reject_public_numeric_scalars("report payload", report)
        _reject_unsafe_public_payload("report payload", report)
        _require_hard_phase_flags("report payload", _MappingFlags(report))
        restored = _report_from_payload(report)
        canonical = _payload_from_report(restored)
        if canonical != dict(report):
            raise ValueError("report payload must be canonical")
        return canonical
    if isinstance(report, Mapping):
        raise ValueError("report payload must be a JSON object")
    raise ValueError(
        "report must be a ResearchStrategyEventInformationGapBudgetReport",
    )


def research_strategy_event_information_gap_budget_report_digest(
    report: (
        ResearchStrategyEventInformationGapBudgetReport | Mapping[str, object]
    ),
) -> str:
    payload = research_strategy_event_information_gap_budget_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_strategy_event_information_gap_budget_report_payload(
    payload: Mapping[str, object],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    research_strategy_event_information_gap_budget_report_payload(payload)
    return True


def _payload_from_report(
    report: ResearchStrategyEventInformationGapBudgetReport,
) -> dict[str, object]:
    _require_exact_type(
        report,
        ResearchStrategyEventInformationGapBudgetReport,
        "report",
    )
    _validate_report(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload)
    _require_hard_phase_flags("report payload", _MappingFlags(payload))
    if payload["derived_validation_digest"] != _digest_from_payload(payload):
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def _report_from_payload(
    payload: Mapping[str, object],
) -> ResearchStrategyEventInformationGapBudgetReport:
    _require_exact_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(_row_from_payload(item) for item in rows_value)
    reason_codes = _payload_reason_codes("reason_codes", payload["reason_codes"])
    return ResearchStrategyEventInformationGapBudgetReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_text("config_version", payload["config_version"]),
        event_count=_payload_count("event_count", payload["event_count"]),
        pass_count=_payload_count("pass_count", payload["pass_count"]),
        watch_count=_payload_count("watch_count", payload["watch_count"]),
        block_count=_payload_count("block_count", payload["block_count"]),
        total_information_gap_pressure=_payload_nonnegative_decimal(
            "total_information_gap_pressure",
            payload["total_information_gap_pressure"],
        ),
        max_information_gap_pressure=_payload_optional_ratio(
            "max_information_gap_pressure",
            payload["max_information_gap_pressure"],
        ),
        average_information_gap_pressure=_payload_optional_ratio(
            "average_information_gap_pressure",
            payload["average_information_gap_pressure"],
        ),
        max_diagnostic_budget_share=_payload_optional_ratio(
            "max_diagnostic_budget_share",
            payload["max_diagnostic_budget_share"],
        ),
        status=_payload_text("status", payload["status"]),
        reason_codes=reason_codes,
        rows=rows,
        derived_validation_digest=_payload_text(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _row_from_payload(
    payload: object,
) -> ResearchStrategyEventInformationGapBudgetRow:
    if type(payload) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_exact_keys("row payload", payload, ROW_PAYLOAD_KEYS)
    return ResearchStrategyEventInformationGapBudgetRow(
        row_number=_payload_positive_count("row_number", payload["row_number"]),
        source_freshness_gap_score=_payload_ratio(
            "source_freshness_gap_score",
            payload["source_freshness_gap_score"],
        ),
        authority_gap_score=_payload_ratio(
            "authority_gap_score",
            payload["authority_gap_score"],
        ),
        team_coverage_gap_score=_payload_ratio(
            "team_coverage_gap_score",
            payload["team_coverage_gap_score"],
        ),
        resolution_proximity_score=_payload_ratio(
            "resolution_proximity_score",
            payload["resolution_proximity_score"],
        ),
        source_freshness_gap_weight=_payload_ratio(
            "source_freshness_gap_weight",
            payload["source_freshness_gap_weight"],
        ),
        authority_gap_weight=_payload_ratio(
            "authority_gap_weight",
            payload["authority_gap_weight"],
        ),
        team_coverage_gap_weight=_payload_ratio(
            "team_coverage_gap_weight",
            payload["team_coverage_gap_weight"],
        ),
        resolution_proximity_weight=_payload_ratio(
            "resolution_proximity_weight",
            payload["resolution_proximity_weight"],
        ),
        watch_component_gap_threshold=_payload_ratio(
            "watch_component_gap_threshold",
            payload["watch_component_gap_threshold"],
        ),
        block_component_gap_threshold=_payload_ratio(
            "block_component_gap_threshold",
            payload["block_component_gap_threshold"],
        ),
        watch_information_gap_pressure_threshold=_payload_ratio(
            "watch_information_gap_pressure_threshold",
            payload["watch_information_gap_pressure_threshold"],
        ),
        block_information_gap_pressure_threshold=_payload_ratio(
            "block_information_gap_pressure_threshold",
            payload["block_information_gap_pressure_threshold"],
        ),
        watch_diagnostic_budget_share_threshold=_payload_ratio(
            "watch_diagnostic_budget_share_threshold",
            payload["watch_diagnostic_budget_share_threshold"],
        ),
        block_diagnostic_budget_share_threshold=_payload_ratio(
            "block_diagnostic_budget_share_threshold",
            payload["block_diagnostic_budget_share_threshold"],
        ),
        information_gap_pressure=_payload_ratio(
            "information_gap_pressure",
            payload["information_gap_pressure"],
        ),
        diagnostic_budget_share=_payload_ratio(
            "diagnostic_budget_share",
            payload["diagnostic_budget_share"],
        ),
        status=_payload_text("status", payload["status"]),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _base_row_from_input(
    item: ResearchStrategyEventInformationGapBudgetInput,
    *,
    config: ResearchStrategyEventInformationGapBudgetConfig,
) -> dict[str, Any]:
    pressure = _information_gap_pressure(
        source_freshness_gap_score=item.source_freshness_gap_score,
        authority_gap_score=item.authority_gap_score,
        team_coverage_gap_score=item.team_coverage_gap_score,
        resolution_proximity_score=item.resolution_proximity_score,
        source_freshness_gap_weight=config.source_freshness_gap_weight,
        authority_gap_weight=config.authority_gap_weight,
        team_coverage_gap_weight=config.team_coverage_gap_weight,
        resolution_proximity_weight=config.resolution_proximity_weight,
    )
    return {
        "event_ref": item.event_ref,
        "source_freshness_gap_score": item.source_freshness_gap_score,
        "authority_gap_score": item.authority_gap_score,
        "team_coverage_gap_score": item.team_coverage_gap_score,
        "resolution_proximity_score": item.resolution_proximity_score,
        "source_freshness_gap_weight": config.source_freshness_gap_weight,
        "authority_gap_weight": config.authority_gap_weight,
        "team_coverage_gap_weight": config.team_coverage_gap_weight,
        "resolution_proximity_weight": config.resolution_proximity_weight,
        "watch_component_gap_threshold": config.watch_component_gap_threshold,
        "block_component_gap_threshold": config.block_component_gap_threshold,
        "watch_information_gap_pressure_threshold": (
            config.watch_information_gap_pressure_threshold
        ),
        "block_information_gap_pressure_threshold": (
            config.block_information_gap_pressure_threshold
        ),
        "watch_diagnostic_budget_share_threshold": (
            config.watch_diagnostic_budget_share_threshold
        ),
        "block_diagnostic_budget_share_threshold": (
            config.block_diagnostic_budget_share_threshold
        ),
        "information_gap_pressure": pressure,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _prepared_row_with_share(
    base_row: dict[str, Any],
    *,
    total_information_gap_pressure: Decimal,
) -> dict[str, Any]:
    share = (
        ZERO
        if total_information_gap_pressure == ZERO
        else _ratio(
            base_row["information_gap_pressure"],
            total_information_gap_pressure,
        )
    )
    reason_codes = _row_reason_codes(
        source_freshness_gap_score=base_row["source_freshness_gap_score"],
        authority_gap_score=base_row["authority_gap_score"],
        team_coverage_gap_score=base_row["team_coverage_gap_score"],
        resolution_proximity_score=base_row["resolution_proximity_score"],
        information_gap_pressure=base_row["information_gap_pressure"],
        diagnostic_budget_share=share,
        watch_component_gap_threshold=base_row[
            "watch_component_gap_threshold"
        ],
        block_component_gap_threshold=base_row[
            "block_component_gap_threshold"
        ],
        watch_information_gap_pressure_threshold=base_row[
            "watch_information_gap_pressure_threshold"
        ],
        block_information_gap_pressure_threshold=base_row[
            "block_information_gap_pressure_threshold"
        ],
        watch_diagnostic_budget_share_threshold=base_row[
            "watch_diagnostic_budget_share_threshold"
        ],
        block_diagnostic_budget_share_threshold=base_row[
            "block_diagnostic_budget_share_threshold"
        ],
    )
    return {
        **base_row,
        "diagnostic_budget_share": share,
        "status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
    }


def _row_from_prepared(
    *,
    row_number: Decimal,
    prepared: dict[str, Any],
) -> ResearchStrategyEventInformationGapBudgetRow:
    values = {key: value for key, value in prepared.items() if key != "event_ref"}
    values["row_number"] = row_number
    return ResearchStrategyEventInformationGapBudgetRow(**values)


def _information_gap_pressure(
    *,
    source_freshness_gap_score: Decimal,
    authority_gap_score: Decimal,
    team_coverage_gap_score: Decimal,
    resolution_proximity_score: Decimal,
    source_freshness_gap_weight: Decimal,
    authority_gap_weight: Decimal,
    team_coverage_gap_weight: Decimal,
    resolution_proximity_weight: Decimal,
) -> Decimal:
    return _sum_decimal(
        (
            _multiply_decimal(
                source_freshness_gap_score,
                source_freshness_gap_weight,
            ),
            _multiply_decimal(authority_gap_score, authority_gap_weight),
            _multiply_decimal(
                team_coverage_gap_score,
                team_coverage_gap_weight,
            ),
            _multiply_decimal(
                resolution_proximity_score,
                resolution_proximity_weight,
            ),
        ),
    )


def _row_reason_codes(
    *,
    source_freshness_gap_score: Decimal,
    authority_gap_score: Decimal,
    team_coverage_gap_score: Decimal,
    resolution_proximity_score: Decimal,
    information_gap_pressure: Decimal,
    diagnostic_budget_share: Decimal,
    watch_component_gap_threshold: Decimal,
    block_component_gap_threshold: Decimal,
    watch_information_gap_pressure_threshold: Decimal,
    block_information_gap_pressure_threshold: Decimal,
    watch_diagnostic_budget_share_threshold: Decimal,
    block_diagnostic_budget_share_threshold: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    for metric, watch_reason, block_reason in (
        (
            source_freshness_gap_score,
            "source_freshness_gap_watch",
            "source_freshness_gap_block",
        ),
        (
            authority_gap_score,
            "authority_gap_watch",
            "authority_gap_block",
        ),
        (
            team_coverage_gap_score,
            "team_coverage_gap_watch",
            "team_coverage_gap_block",
        ),
        (
            resolution_proximity_score,
            "resolution_proximity_watch",
            "resolution_proximity_block",
        ),
    ):
        _append_threshold_reason(
            reasons,
            metric=metric,
            watch_threshold=watch_component_gap_threshold,
            block_threshold=block_component_gap_threshold,
            watch_reason=watch_reason,
            block_reason=block_reason,
        )
    _append_threshold_reason(
        reasons,
        metric=information_gap_pressure,
        watch_threshold=watch_information_gap_pressure_threshold,
        block_threshold=block_information_gap_pressure_threshold,
        watch_reason="information_gap_pressure_watch",
        block_reason="information_gap_pressure_block",
    )
    _append_threshold_reason(
        reasons,
        metric=diagnostic_budget_share,
        watch_threshold=watch_diagnostic_budget_share_threshold,
        block_threshold=block_diagnostic_budget_share_threshold,
        watch_reason="diagnostic_budget_share_watch",
        block_reason="diagnostic_budget_share_block",
    )
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _append_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if metric >= block_threshold:
        reasons.append(block_reason)
    elif metric >= watch_threshold:
        reasons.append(watch_reason)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategyEventInformationGapBudgetRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyEventInformationGapBudgetRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != PASS_REASON
    )
    if not reasons:
        return (PASS_REASON,)
    return _normalize_reason_codes("reason_codes", reasons)


def _validate_config_values(
    *,
    source_freshness_gap_weight: Decimal,
    authority_gap_weight: Decimal,
    team_coverage_gap_weight: Decimal,
    resolution_proximity_weight: Decimal,
    watch_component_gap_threshold: Decimal,
    block_component_gap_threshold: Decimal,
    watch_information_gap_pressure_threshold: Decimal,
    block_information_gap_pressure_threshold: Decimal,
    watch_diagnostic_budget_share_threshold: Decimal,
    block_diagnostic_budget_share_threshold: Decimal,
) -> None:
    if _sum_decimal(
        (
            source_freshness_gap_weight,
            authority_gap_weight,
            team_coverage_gap_weight,
            resolution_proximity_weight,
        ),
    ) != ONE:
        raise ValueError("information gap weights must sum to 1.000000")
    _require_above(
        "block_component_gap_threshold",
        block_component_gap_threshold,
        watch_component_gap_threshold,
    )
    _require_above(
        "block_information_gap_pressure_threshold",
        block_information_gap_pressure_threshold,
        watch_information_gap_pressure_threshold,
    )
    _require_above(
        "block_diagnostic_budget_share_threshold",
        block_diagnostic_budget_share_threshold,
        watch_diagnostic_budget_share_threshold,
    )


def _validate_row(
    row: ResearchStrategyEventInformationGapBudgetRow,
) -> None:
    expected_pressure = _information_gap_pressure(
        source_freshness_gap_score=row.source_freshness_gap_score,
        authority_gap_score=row.authority_gap_score,
        team_coverage_gap_score=row.team_coverage_gap_score,
        resolution_proximity_score=row.resolution_proximity_score,
        source_freshness_gap_weight=row.source_freshness_gap_weight,
        authority_gap_weight=row.authority_gap_weight,
        team_coverage_gap_weight=row.team_coverage_gap_weight,
        resolution_proximity_weight=row.resolution_proximity_weight,
    )
    if row.information_gap_pressure != expected_pressure:
        raise ValueError("information_gap_pressure must match component scores")
    expected_reasons = _row_reason_codes(
        source_freshness_gap_score=row.source_freshness_gap_score,
        authority_gap_score=row.authority_gap_score,
        team_coverage_gap_score=row.team_coverage_gap_score,
        resolution_proximity_score=row.resolution_proximity_score,
        information_gap_pressure=row.information_gap_pressure,
        diagnostic_budget_share=row.diagnostic_budget_share,
        watch_component_gap_threshold=row.watch_component_gap_threshold,
        block_component_gap_threshold=row.block_component_gap_threshold,
        watch_information_gap_pressure_threshold=(
            row.watch_information_gap_pressure_threshold
        ),
        block_information_gap_pressure_threshold=(
            row.block_information_gap_pressure_threshold
        ),
        watch_diagnostic_budget_share_threshold=(
            row.watch_diagnostic_budget_share_threshold
        ),
        block_diagnostic_budget_share_threshold=(
            row.block_diagnostic_budget_share_threshold
        ),
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match diagnostic inputs")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(
    report: ResearchStrategyEventInformationGapBudgetReport,
) -> None:
    rows = report.rows
    for row in rows:
        _validate_row(row)
    if rows:
        signature = _row_config_signature(rows[0])
        if any(_row_config_signature(row) != signature for row in rows[1:]):
            raise ValueError("row diagnostic configuration must match")
    if report.event_count != _count(len(rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    expected_total_pressure = _sum_decimal(
        row.information_gap_pressure for row in rows
    )
    if report.total_information_gap_pressure != expected_total_pressure:
        raise ValueError("total_information_gap_pressure must match rows")
    for row in rows:
        expected_share = (
            ZERO
            if expected_total_pressure == ZERO
            else _ratio(row.information_gap_pressure, expected_total_pressure)
        )
        if row.diagnostic_budget_share != expected_share:
            raise ValueError(
                "diagnostic_budget_share must match total information gap pressure",
            )
    expected_max_pressure = (
        None if not rows else max(row.information_gap_pressure for row in rows)
    )
    if report.max_information_gap_pressure != expected_max_pressure:
        raise ValueError("max_information_gap_pressure must match rows")
    if report.average_information_gap_pressure != _average_pressure(rows):
        raise ValueError("average_information_gap_pressure must match rows")
    expected_max_share = (
        None if not rows else max(row.diagnostic_budget_share for row in rows)
    )
    if report.max_diagnostic_budget_share != expected_max_share:
        raise ValueError("max_diagnostic_budget_share must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    expected_digest = _report_digest_from_values(
        _report_values_without_digest(report),
    )
    if report.derived_validation_digest != expected_digest:
        raise ValueError(
            "derived_validation_digest does not match report payload",
        )


def _normalize_inputs(
    events: Iterable[ResearchStrategyEventInformationGapBudgetInput],
) -> tuple[ResearchStrategyEventInformationGapBudgetInput, ...]:
    if isinstance(events, (str, bytes)):
        raise ValueError("events must be an iterable")
    try:
        values = tuple(events)
    except TypeError as exc:
        raise ValueError("events must be an iterable") from exc
    seen: set[str] = set()
    for item in values:
        if type(item) is not ResearchStrategyEventInformationGapBudgetInput:
            raise ValueError(
                "events must contain ResearchStrategyEventInformationGapBudgetInput",
            )
        _require_hard_phase_flags("input", item)
        if item.event_ref in seen:
            raise ValueError("event_ref values must be unique")
        seen.add(item.event_ref)
    return values


def _normalize_rows(
    rows: Iterable[ResearchStrategyEventInformationGapBudgetRow],
) -> tuple[ResearchStrategyEventInformationGapBudgetRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    expected_row_number = ONE
    for row in values:
        if type(row) is not ResearchStrategyEventInformationGapBudgetRow:
            raise ValueError(
                "rows must contain ResearchStrategyEventInformationGapBudgetRow",
            )
        _require_hard_phase_flags("row", row)
        if row.row_number != expected_row_number:
            raise ValueError("rows must be sorted deterministically")
        expected_row_number = _sum_decimal((expected_row_number, ONE))
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return values


def _prepared_row_sort_key(
    prepared: dict[str, Any],
) -> tuple[
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    str,
]:
    return (
        STATUS_WEIGHT[prepared["status"]],
        prepared["diagnostic_budget_share"].copy_negate(),
        prepared["information_gap_pressure"].copy_negate(),
        prepared["source_freshness_gap_score"].copy_negate(),
        prepared["authority_gap_score"].copy_negate(),
        prepared["team_coverage_gap_score"].copy_negate(),
        prepared["resolution_proximity_score"].copy_negate(),
        prepared["event_ref"],
    )


def _row_sort_key(
    row: ResearchStrategyEventInformationGapBudgetRow,
) -> tuple[
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
]:
    return (
        STATUS_WEIGHT[row.status],
        row.diagnostic_budget_share.copy_negate(),
        row.information_gap_pressure.copy_negate(),
        row.source_freshness_gap_score.copy_negate(),
        row.authority_gap_score.copy_negate(),
        row.team_coverage_gap_score.copy_negate(),
        row.resolution_proximity_score.copy_negate(),
        row.row_number,
    )


def _row_config_signature(
    row: ResearchStrategyEventInformationGapBudgetRow,
) -> tuple[Decimal, ...]:
    return (
        row.source_freshness_gap_weight,
        row.authority_gap_weight,
        row.team_coverage_gap_weight,
        row.resolution_proximity_weight,
        row.watch_component_gap_threshold,
        row.block_component_gap_threshold,
        row.watch_information_gap_pressure_threshold,
        row.block_information_gap_pressure_threshold,
        row.watch_diagnostic_budget_share_threshold,
        row.block_diagnostic_budget_share_threshold,
    )


def _status_count(
    rows: tuple[ResearchStrategyEventInformationGapBudgetRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(row.status == status for row in rows))


def _average_pressure(
    rows: tuple[ResearchStrategyEventInformationGapBudgetRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _ratio(
        _sum_decimal(row.information_gap_pressure for row in rows),
        _count(len(rows)),
    )


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    allowed = set(REASON_PRIORITY)
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not str or item not in allowed:
            raise ValueError(f"{field_name} contains an unsupported reason code")
        if item not in seen:
            normalized.append(item)
            seen.add(item)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(sorted(normalized, key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    try:
        return (REASON_PRIORITY.index(reason_code), reason_code)
    except ValueError:
        return (len(REASON_PRIORITY), reason_code)


def _report_values_without_digest(
    report: ResearchStrategyEventInformationGapBudgetReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(dict(values))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload)
    return _digest_from_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        if value.is_zero() and value.is_signed():
            raise ValueError("JSON Decimal value must not be signed zero")
        return format(value, "f")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    raise ValueError("report payload contains unsupported value")


def _reject_public_numeric_scalars(label: str, value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError(f"unsafe public payload numeric scalar in {label}")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numeric_scalars(label, item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_public_numeric_scalars(label, item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for item in _iter_public_text(value):
        lowered = item.lower()
        if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _iter_public_text(value: object) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key)
            yield from _iter_public_text(item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            yield from _iter_public_text(item)
        return
    if type(value) is str:
        yield value


def _require_exact_keys(
    label: str,
    value: Mapping[str, object],
    expected_keys: tuple[str, ...],
) -> None:
    if any(type(key) is not str for key in value):
        raise ValueError(f"{label} keys must be strings")
    if tuple(value) != expected_keys:
        raise ValueError(f"{label} must contain the canonical keys")


def _payload_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if any(type(item) is not str for item in value):
        raise ValueError(f"{field_name} must contain strings")
    return tuple(value)


def _payload_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _payload_datetime(field_name: str, value: object) -> datetime:
    text = _payload_text(field_name, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if text != normalized.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _payload_decimal(field_name: str, value: object) -> Decimal:
    text = _payload_text(field_name, value)
    try:
        parsed = Decimal(text)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = _normalize_decimal(field_name, parsed)
    if text != format(normalized, "f"):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _payload_ratio(field_name: str, value: object) -> Decimal:
    return _normalize_ratio(field_name, _payload_decimal(field_name, value))


def _payload_optional_ratio(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _payload_ratio(field_name, value)


def _payload_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        field_name,
        _payload_decimal(field_name, value),
    )


def _payload_count(field_name: str, value: object) -> Decimal:
    return _normalize_nonnegative_count(
        field_name,
        _payload_decimal(field_name, value),
    )


def _payload_positive_count(field_name: str, value: object) -> Decimal:
    return _normalize_positive_count(
        field_name,
        _payload_decimal(field_name, value),
    )


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return _quantize(Decimal(value), field_name="count")


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(_new_decimal_context()):
        total = sum(values, Decimal("0"))
    return _quantize(total, field_name="Decimal sum")


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_new_decimal_context()):
        product = left * right
    return _quantize(product, field_name="Decimal product")


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(_new_decimal_context()):
        value = numerator / denominator
    return _quantize(value, field_name="Decimal ratio")


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(raw, field_name=field_name)


def _normalize_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw, field_name=field_name)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < ZERO or raw > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return _quantize(raw, field_name=field_name)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _quantize(
        _require_decimal(field_name, value),
        field_name=field_name,
    )


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _quantize(value: Decimal, *, field_name: str = "Decimal value") -> Decimal:
    try:
        with localcontext(_new_decimal_context()):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(
            f"{field_name} cannot be quantized to six decimals",
        ) from exc


def _new_decimal_context() -> Context:
    return Context(
        prec=64,
        rounding="ROUND_HALF_EVEN",
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(
    value: object,
    expected_type: type[object],
    label: str,
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_above(
    field_name: str,
    value: Decimal,
    floor: Decimal,
) -> None:
    if value <= floor:
        raise ValueError(f"{field_name} must exceed its watch threshold")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_private_reference(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} contains control characters")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} contains control characters")
    lowered = value.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _require_sha256(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def _require_hard_phase_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")
