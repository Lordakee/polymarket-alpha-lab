"""Pure report-only event dependency graph reducer for human research."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any, Iterable


DEFAULT_CONFIG_VERSION = "research-event-dependency-graph-report-v0"
STATUS_VALUES = ("pass", "watch", "block")
SAFETY_FLAGS = (
    "paper_only",
    "report_only",
    "readonly",
    "redacted_refs_only",
    "local_inputs_only",
    "no_execution_surface",
)
REDACTED_EVENT_REF_PREFIX = "redacted-event-"

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

INPUT_REASON_CODES = ("sanitized_event_dependency_input",)
ROW_REASON_CODE_SEQUENCE = (
    "sanitized_event_dependency_input",
    "research_event_dependency_graph_row",
    "event_dependency_block",
    "event_dependency_watch",
    "event_dependency_pass",
    "dependency_edges_present",
    "dependency_edges_clear",
    "unresolved_dependencies_block",
    "unresolved_dependencies_watch",
    "unresolved_dependencies_clear",
    "external_shock_block",
    "external_shock_watch",
    "external_shock_clear",
    "timeline_quality_block",
    "timeline_quality_watch",
    "timeline_quality_clear",
    "evidence_support_block",
    "evidence_support_watch",
    "evidence_support_strong",
    "dependency_pressure_block",
    "dependency_pressure_watch",
    "dependency_pressure_pass",
)
REPORT_REASON_CODE_SEQUENCE = (
    "research_event_dependency_graph_report_block",
    "research_event_dependency_graph_report_watch",
    "research_event_dependency_graph_report_pass",
    "event_dependency_block_present",
    "event_dependency_watch_present",
    "event_dependency_pass_present",
    "event_dependency_graph_no_inputs",
)
HARD_FLAG_SEQUENCE = (
    "unresolved_dependency_count_block",
    "external_shock_sensitivity_block",
    "timeline_quality_score_block",
    "evidence_support_score_block",
)
_STATUS_SORT_RANK = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}
_WEIGHT_FIELDS = (
    "dependency_edge_count_weight",
    "unresolved_dependency_count_weight",
    "external_shock_sensitivity_weight",
    "timeline_quality_gap_weight",
    "evidence_support_gap_weight",
)
_ROW_DIGEST_FIELDS = (
    "config",
    "config_version",
    "redacted_event_ref",
    "dependency_edge_count",
    "unresolved_dependency_count",
    "external_shock_sensitivity",
    "timeline_quality_score",
    "evidence_support_score",
    "dependency_pressure_score",
    "status",
    "safety_flags",
    "reason_codes",
    "hard_flag_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_DIGEST_FIELDS = (
    "config",
    "generated_at",
    "config_version",
    "node_count",
    "pass_count",
    "watch_count",
    "block_count",
    "max_dependency_pressure_score",
    "min_dependency_pressure_score",
    "average_dependency_pressure_score",
    "max_external_shock_sensitivity",
    "average_external_shock_sensitivity",
    "min_timeline_quality_score",
    "status",
    "safety_flags",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
_UNSAFE_TERM_PARTS = (
    ("candidate", "_id"),
    ("candidate", "-id"),
    ("market", "_id"),
    ("market", "_slug"),
    ("market", "-"),
    ("sl", "ug"),
    ("ques", "tion"),
    ("source", "_ref"),
    ("source", "_refs"),
    ("source", "_url"),
    ("source", "_text"),
    ("source", "_id"),
    ("source", "-ref"),
    ("source", "-url"),
    ("source", "-text"),
    ("source", "-id"),
    ("url",),
    ("://",),
    ("www", "."),
    ("d", "sn"),
    ("connection", "_string"),
    ("ta", "ble"),
    ("sche", "ma"),
    ("warehouse",),
    ("jd", "bc"),
    ("od", "bc"),
    ("postgres", "ql"),
    ("my", "sql"),
    ("sq", "lite"),
    ("snow", "flake"),
    ("big", "query"),
    ("red", "shift"),
    ("to", "ken"),
    ("se", "cret"),
    ("au", "th"),
    ("au", "thor", "ization"),
    ("bear", "er"),
    ("api", "_key"),
    ("private", "_key"),
    ("password",),
    ("cred", "ential"),
    ("sess", "ion"),
    ("j", "wt"),
    ("o", "au", "th"),
    ("wal", "let"),
    ("or", "der"),
    ("tra", "de"),
    ("b", "uy"),
    ("se", "ll"),
    ("reco", "mmendation"),
    ("reco", "mmend"),
    ("position", "_sizing"),
    ("position", "-", "sizing"),
    ("position", "_size"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_HEX_CHARS = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class ResearchEventDependencyGraphReportConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    max_pass_dependency_pressure_score: Decimal = Decimal("0.200000")
    max_watch_dependency_pressure_score: Decimal = Decimal("0.600000")
    dependency_edge_count_cap: Decimal = Decimal("6")
    unresolved_dependency_count_cap: Decimal = Decimal("3")
    max_watch_unresolved_dependency_count: Decimal = Decimal("0")
    max_block_unresolved_dependency_count: Decimal = Decimal("2")
    max_watch_external_shock_sensitivity: Decimal = Decimal("0.500000")
    max_block_external_shock_sensitivity: Decimal = Decimal("0.800000")
    min_watch_timeline_quality_score: Decimal = Decimal("0.500000")
    min_block_timeline_quality_score: Decimal = Decimal("0.200000")
    min_watch_evidence_support_score: Decimal = Decimal("0.500000")
    min_block_evidence_support_score: Decimal = Decimal("0.200000")
    dependency_edge_count_weight: Decimal = Decimal("0.250000")
    unresolved_dependency_count_weight: Decimal = Decimal("0.250000")
    external_shock_sensitivity_weight: Decimal = Decimal("0.200000")
    timeline_quality_gap_weight: Decimal = Decimal("0.200000")
    evidence_support_gap_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventDependencyGraphReportConfig:
            raise TypeError(
                "ResearchEventDependencyGraphReportConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventDependencyGraphReportConfig:
            raise ValueError(
                "config must be exactly ResearchEventDependencyGraphReportConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the default config version")
        for field_name in (
            "max_pass_dependency_pressure_score",
            "max_watch_dependency_pressure_score",
            "max_watch_external_shock_sensitivity",
            "max_block_external_shock_sensitivity",
            "min_watch_timeline_quality_score",
            "min_block_timeline_quality_score",
            "min_watch_evidence_support_score",
            "min_block_evidence_support_score",
        ) + _WEIGHT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "dependency_edge_count_cap",
            "unresolved_dependency_count_cap",
            "max_block_unresolved_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "max_watch_unresolved_dependency_count",
            _normalize_nonnegative_integral_decimal(
                "max_watch_unresolved_dependency_count",
                self.max_watch_unresolved_dependency_count,
            ),
        )
        if self.max_pass_dependency_pressure_score > self.max_watch_dependency_pressure_score:
            raise ValueError("pass pressure threshold must not exceed watch threshold")
        if self.max_watch_unresolved_dependency_count >= self.max_block_unresolved_dependency_count:
            raise ValueError("watch unresolved threshold must be below block threshold")
        if (
            self.max_watch_external_shock_sensitivity
            > self.max_block_external_shock_sensitivity
        ):
            raise ValueError("watch shock threshold must not exceed block threshold")
        if self.min_block_timeline_quality_score > self.min_watch_timeline_quality_score:
            raise ValueError("block timeline threshold must not exceed watch threshold")
        if self.min_block_evidence_support_score > self.min_watch_evidence_support_score:
            raise ValueError("block evidence threshold must not exceed watch threshold")
        if _sum_decimal(getattr(self, field_name) for field_name in _WEIGHT_FIELDS) != ONE:
            raise ValueError("weight fields must sum to 1.000000")
        _require_hard_flags("event dependency graph config", self)
        reject_research_event_dependency_graph_unsafe_payload(
            "event dependency graph config",
            self,
        )


@dataclass(frozen=True)
class ResearchEventDependencyGraphInput:
    redacted_event_ref: str
    dependency_edge_count: Decimal
    unresolved_dependency_count: Decimal
    external_shock_sensitivity: Decimal
    timeline_quality_score: Decimal
    evidence_support_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventDependencyGraphInput:
            raise TypeError(
                "ResearchEventDependencyGraphInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventDependencyGraphInput:
            raise ValueError("input must be exactly ResearchEventDependencyGraphInput")
        object.__setattr__(
            self,
            "redacted_event_ref",
            _normalize_redacted_event_ref("redacted_event_ref", self.redacted_event_ref),
        )
        for field_name in ("dependency_edge_count", "unresolved_dependency_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.unresolved_dependency_count > self.dependency_edge_count:
            raise ValueError("unresolved_dependency_count must not exceed dependency_edge_count")
        for field_name in (
            "external_shock_sensitivity",
            "timeline_quality_score",
            "evidence_support_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_hard_flags("event dependency graph input", self)
        reject_research_event_dependency_graph_unsafe_payload(
            "event dependency graph input",
            self,
        )


@dataclass(frozen=True)
class ResearchEventDependencyGraphRow:
    config: ResearchEventDependencyGraphReportConfig
    config_version: str
    redacted_event_ref: str
    dependency_edge_count: Decimal
    unresolved_dependency_count: Decimal
    external_shock_sensitivity: Decimal
    timeline_quality_score: Decimal
    evidence_support_score: Decimal
    dependency_pressure_score: Decimal
    status: str
    safety_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    hard_flag_codes: tuple[str, ...] = ()
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventDependencyGraphRow:
            raise TypeError(
                "ResearchEventDependencyGraphRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventDependencyGraphRow:
            raise ValueError("row must be exactly ResearchEventDependencyGraphRow")
        if type(self.config) is not ResearchEventDependencyGraphReportConfig:
            raise ValueError("config must be exactly ResearchEventDependencyGraphReportConfig")
        _require_hard_flags("event dependency graph row config", self.config)
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        object.__setattr__(
            self,
            "redacted_event_ref",
            _normalize_redacted_event_ref("redacted_event_ref", self.redacted_event_ref),
        )
        for field_name in ("dependency_edge_count", "unresolved_dependency_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.unresolved_dependency_count > self.dependency_edge_count:
            raise ValueError("unresolved_dependency_count must not exceed dependency_edge_count")
        for field_name in (
            "external_shock_sensitivity",
            "timeline_quality_score",
            "evidence_support_score",
            "dependency_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUS_VALUES)
        object.__setattr__(
            self,
            "safety_flags",
            _normalize_safety_flags(self.safety_flags),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_known_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "hard_flag_codes",
            _normalize_known_reason_codes(
                "hard_flag_codes",
                self.hard_flag_codes,
                HARD_FLAG_SEQUENCE,
                allow_empty=True,
            ),
        )
        _validate_row(self)
        _require_hard_flags("event dependency graph row", self)
        reject_research_event_dependency_graph_unsafe_payload(
            "event dependency graph row",
            self,
        )
        digest = _digest_instance(self, _ROW_DIGEST_FIELDS)
        if not self.derived_validation_digest:
            object.__setattr__(self, "derived_validation_digest", digest)
        elif self.derived_validation_digest != digest:
            raise ValueError("derived_validation_digest must match row values")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(
            _instance_digest_payload(self, _ROW_DIGEST_FIELDS, self.derived_validation_digest),
        )
        if type(payload) is not dict:
            raise ValueError("row payload must be a JSON object")
        reject_research_event_dependency_graph_unsafe_payload("row payload", payload)
        _reject_public_numerics(payload)
        return payload


@dataclass(frozen=True)
class ResearchEventDependencyGraphReport:
    config: ResearchEventDependencyGraphReportConfig
    generated_at: datetime
    config_version: str
    node_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_dependency_pressure_score: Decimal
    min_dependency_pressure_score: Decimal
    average_dependency_pressure_score: Decimal
    max_external_shock_sensitivity: Decimal
    average_external_shock_sensitivity: Decimal
    min_timeline_quality_score: Decimal
    status: str
    safety_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventDependencyGraphRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventDependencyGraphReport:
            raise TypeError(
                "ResearchEventDependencyGraphReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventDependencyGraphReport:
            raise ValueError("report must be exactly ResearchEventDependencyGraphReport")
        if type(self.config) is not ResearchEventDependencyGraphReportConfig:
            raise ValueError("config must be exactly ResearchEventDependencyGraphReportConfig")
        _require_hard_flags("event dependency graph report config", self.config)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in ("node_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "max_dependency_pressure_score",
            "min_dependency_pressure_score",
            "average_dependency_pressure_score",
            "max_external_shock_sensitivity",
            "average_external_shock_sensitivity",
            "min_timeline_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUS_VALUES)
        object.__setattr__(self, "safety_flags", _normalize_safety_flags(self.safety_flags))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_known_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("event dependency graph report", self)
        reject_research_event_dependency_graph_unsafe_payload(
            "event dependency graph report",
            self,
        )
        digest = _digest_instance(self, _REPORT_DIGEST_FIELDS)
        if not self.derived_validation_digest:
            object.__setattr__(self, "derived_validation_digest", digest)
        elif self.derived_validation_digest != digest:
            raise ValueError("derived_validation_digest must match report values")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_dependency_graph_report_payload(self)


def build_research_event_dependency_graph_report(
    rows: list[ResearchEventDependencyGraphInput]
    | tuple[ResearchEventDependencyGraphInput, ...],
    *,
    config: ResearchEventDependencyGraphReportConfig,
    generated_at: datetime,
) -> ResearchEventDependencyGraphReport:
    if type(config) is not ResearchEventDependencyGraphReportConfig:
        raise ValueError("config must be a ResearchEventDependencyGraphReportConfig")
    _require_hard_flags("event dependency graph config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(rows)
    scored_rows = tuple(
        sorted(
            (_row_from_input(row, config=config) for row in inputs),
            key=_row_sort_key,
        ),
    )
    node_count = _count(len(scored_rows))
    pass_count = _count(sum(1 for row in scored_rows if row.status == "pass"))
    watch_count = _count(sum(1 for row in scored_rows if row.status == "watch"))
    block_count = _count(sum(1 for row in scored_rows if row.status == "block"))
    return ResearchEventDependencyGraphReport(
        config=config,
        generated_at=generated_at_utc,
        config_version=config.config_version,
        node_count=node_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_dependency_pressure_score=max(
            (row.dependency_pressure_score for row in scored_rows),
            default=ZERO,
        ),
        min_dependency_pressure_score=min(
            (row.dependency_pressure_score for row in scored_rows),
            default=ZERO,
        ),
        average_dependency_pressure_score=_ratio(
            _sum_decimal(row.dependency_pressure_score for row in scored_rows),
            node_count,
        ),
        max_external_shock_sensitivity=max(
            (row.external_shock_sensitivity for row in scored_rows),
            default=ZERO,
        ),
        average_external_shock_sensitivity=_ratio(
            _sum_decimal(row.external_shock_sensitivity for row in scored_rows),
            node_count,
        ),
        min_timeline_quality_score=min(
            (row.timeline_quality_score for row in scored_rows),
            default=ZERO,
        ),
        status=_report_status(scored_rows),
        safety_flags=SAFETY_FLAGS,
        reason_codes=_report_reason_codes(scored_rows),
        rows=scored_rows,
    )


def research_event_dependency_graph_report_payload(
    report: ResearchEventDependencyGraphReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventDependencyGraphReport:
        raise ValueError("report must be a ResearchEventDependencyGraphReport")
    _require_hard_flags("event dependency graph report", report)
    reject_research_event_dependency_graph_unsafe_payload(
        "event dependency graph report",
        report,
    )
    digest = _digest_instance(report, _REPORT_DIGEST_FIELDS)
    if report.derived_validation_digest != digest:
        raise ValueError("derived_validation_digest must match report values")
    payload = _json_ready(
        _instance_digest_payload(report, _REPORT_DIGEST_FIELDS, report.derived_validation_digest),
    )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_research_event_dependency_graph_unsafe_payload(
        "event dependency graph report payload",
        payload,
    )
    _reject_public_numerics(payload)
    return payload


def reject_research_event_dependency_graph_unsafe_payload(
    label: str,
    value: object,
) -> None:
    _reject_unsafe_payload_entry(label, value)


def _row_from_input(
    row: ResearchEventDependencyGraphInput,
    *,
    config: ResearchEventDependencyGraphReportConfig,
) -> ResearchEventDependencyGraphRow:
    pressure = _dependency_pressure_score(row, config)
    hard_flags = _hard_flag_codes(row, config)
    status = _row_status(row, pressure=pressure, hard_flag_codes=hard_flags, config=config)
    return ResearchEventDependencyGraphRow(
        config=config,
        config_version=config.config_version,
        redacted_event_ref=row.redacted_event_ref,
        dependency_edge_count=row.dependency_edge_count,
        unresolved_dependency_count=row.unresolved_dependency_count,
        external_shock_sensitivity=row.external_shock_sensitivity,
        timeline_quality_score=row.timeline_quality_score,
        evidence_support_score=row.evidence_support_score,
        dependency_pressure_score=pressure,
        status=status,
        safety_flags=SAFETY_FLAGS,
        reason_codes=_row_reason_codes(
            row,
            pressure=pressure,
            status=status,
            config=config,
        ),
        hard_flag_codes=hard_flags,
    )


def _dependency_pressure_score(
    row: ResearchEventDependencyGraphInput | ResearchEventDependencyGraphRow,
    config: ResearchEventDependencyGraphReportConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        edge_ratio = _raw_ratio(row.dependency_edge_count, config.dependency_edge_count_cap)
        unresolved_ratio = _raw_ratio(
            row.unresolved_dependency_count,
            config.unresolved_dependency_count_cap,
        )
        timeline_quality_gap = ONE - row.timeline_quality_score
        evidence_support_gap = ONE - row.evidence_support_score
        return _normalize_unit_decimal(
            "dependency_pressure_score",
            (
                edge_ratio * config.dependency_edge_count_weight
                + unresolved_ratio * config.unresolved_dependency_count_weight
                + row.external_shock_sensitivity
                * config.external_shock_sensitivity_weight
                + timeline_quality_gap * config.timeline_quality_gap_weight
                + evidence_support_gap * config.evidence_support_gap_weight
            ),
        )


def _hard_flag_codes(
    row: ResearchEventDependencyGraphInput | ResearchEventDependencyGraphRow,
    config: ResearchEventDependencyGraphReportConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if row.unresolved_dependency_count >= config.max_block_unresolved_dependency_count:
        codes.append("unresolved_dependency_count_block")
    if row.external_shock_sensitivity >= config.max_block_external_shock_sensitivity:
        codes.append("external_shock_sensitivity_block")
    if row.timeline_quality_score <= config.min_block_timeline_quality_score:
        codes.append("timeline_quality_score_block")
    if row.evidence_support_score <= config.min_block_evidence_support_score:
        codes.append("evidence_support_score_block")
    return tuple(code for code in HARD_FLAG_SEQUENCE if code in codes)


def _row_status(
    row: ResearchEventDependencyGraphInput | ResearchEventDependencyGraphRow,
    *,
    pressure: Decimal,
    hard_flag_codes: tuple[str, ...],
    config: ResearchEventDependencyGraphReportConfig,
) -> str:
    if hard_flag_codes or pressure > config.max_watch_dependency_pressure_score:
        return "block"
    if (
        pressure > config.max_pass_dependency_pressure_score
        or row.unresolved_dependency_count > config.max_watch_unresolved_dependency_count
        or row.external_shock_sensitivity >= config.max_watch_external_shock_sensitivity
        or row.timeline_quality_score <= config.min_watch_timeline_quality_score
        or row.evidence_support_score <= config.min_watch_evidence_support_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    row: ResearchEventDependencyGraphInput | ResearchEventDependencyGraphRow,
    *,
    pressure: Decimal,
    status: str,
    config: ResearchEventDependencyGraphReportConfig,
) -> tuple[str, ...]:
    codes: list[str] = list(row.reason_codes)
    codes.append("research_event_dependency_graph_row")
    codes.append(f"event_dependency_{status}")
    if row.dependency_edge_count > Decimal("0"):
        codes.append("dependency_edges_present")
    else:
        codes.append("dependency_edges_clear")
    if row.unresolved_dependency_count >= config.max_block_unresolved_dependency_count:
        codes.append("unresolved_dependencies_block")
    elif row.unresolved_dependency_count > config.max_watch_unresolved_dependency_count:
        codes.append("unresolved_dependencies_watch")
    else:
        codes.append("unresolved_dependencies_clear")
    if row.external_shock_sensitivity >= config.max_block_external_shock_sensitivity:
        codes.append("external_shock_block")
    elif row.external_shock_sensitivity >= config.max_watch_external_shock_sensitivity:
        codes.append("external_shock_watch")
    else:
        codes.append("external_shock_clear")
    if row.timeline_quality_score <= config.min_block_timeline_quality_score:
        codes.append("timeline_quality_block")
    elif row.timeline_quality_score <= config.min_watch_timeline_quality_score:
        codes.append("timeline_quality_watch")
    else:
        codes.append("timeline_quality_clear")
    if row.evidence_support_score <= config.min_block_evidence_support_score:
        codes.append("evidence_support_block")
    elif row.evidence_support_score <= config.min_watch_evidence_support_score:
        codes.append("evidence_support_watch")
    else:
        codes.append("evidence_support_strong")
    if pressure > config.max_watch_dependency_pressure_score:
        codes.append("dependency_pressure_block")
    elif pressure > config.max_pass_dependency_pressure_score:
        codes.append("dependency_pressure_watch")
    else:
        codes.append("dependency_pressure_pass")
    return tuple(code for code in ROW_REASON_CODE_SEQUENCE if code in codes)


def _report_status(rows: tuple[ResearchEventDependencyGraphRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventDependencyGraphRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (
            "research_event_dependency_graph_report_pass",
            "event_dependency_graph_no_inputs",
        )
    status = _report_status(rows)
    codes = [f"research_event_dependency_graph_report_{status}"]
    if any(row.status == "block" for row in rows):
        codes.append("event_dependency_block_present")
    elif any(row.status == "watch" for row in rows):
        codes.append("event_dependency_watch_present")
    else:
        codes.append("event_dependency_pass_present")
    return tuple(code for code in REPORT_REASON_CODE_SEQUENCE if code in codes)


def _row_sort_key(row: ResearchEventDependencyGraphRow) -> tuple[Decimal, str]:
    return (
        _STATUS_SORT_RANK[row.status],
        row.redacted_event_ref,
    )


def _normalize_inputs(
    rows: list[ResearchEventDependencyGraphInput]
    | tuple[ResearchEventDependencyGraphInput, ...],
) -> tuple[ResearchEventDependencyGraphInput, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventDependencyGraphInput:
            raise ValueError("rows must contain ResearchEventDependencyGraphInput")
        _require_hard_flags("event dependency graph input", row)
        if row.redacted_event_ref in seen:
            raise ValueError("rows must not contain duplicate redacted_event_ref values")
        seen.add(row.redacted_event_ref)
    return normalized


def _normalize_rows(value: object) -> tuple[ResearchEventDependencyGraphRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventDependencyGraphRow:
            raise ValueError("rows must contain ResearchEventDependencyGraphRow")
        _require_hard_flags("event dependency graph row", row)
        if row.redacted_event_ref in seen:
            raise ValueError("rows must not contain duplicate redacted_event_ref values")
        seen.add(row.redacted_event_ref)
    return rows


def _validate_row(row: ResearchEventDependencyGraphRow) -> None:
    expected_pressure = _dependency_pressure_score(row, row.config)
    if row.dependency_pressure_score != expected_pressure:
        raise ValueError("dependency_pressure_score must match row inputs")
    expected_hard_flags = _hard_flag_codes(row, row.config)
    if row.hard_flag_codes != expected_hard_flags:
        raise ValueError("hard_flag_codes must match row inputs")
    expected_status = _row_status(
        row,
        pressure=row.dependency_pressure_score,
        hard_flag_codes=row.hard_flag_codes,
        config=row.config,
    )
    if row.status != expected_status:
        raise ValueError("status must match row inputs")
    expected_reason_codes = _row_reason_codes(
        row,
        pressure=row.dependency_pressure_score,
        status=row.status,
        config=row.config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")


def _validate_report(report: ResearchEventDependencyGraphReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if report.node_count != _count(len(report.rows)):
        raise ValueError("node_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.max_dependency_pressure_score != max(
        (row.dependency_pressure_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_dependency_pressure_score must match rows")
    if report.min_dependency_pressure_score != min(
        (row.dependency_pressure_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_dependency_pressure_score must match rows")
    if report.average_dependency_pressure_score != _ratio(
        _sum_decimal(row.dependency_pressure_score for row in report.rows),
        report.node_count,
    ):
        raise ValueError("average_dependency_pressure_score must match rows")
    if report.max_external_shock_sensitivity != max(
        (row.external_shock_sensitivity for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_external_shock_sensitivity must match rows")
    if report.average_external_shock_sensitivity != _ratio(
        _sum_decimal(row.external_shock_sensitivity for row in report.rows),
        report.node_count,
    ):
        raise ValueError("average_external_shock_sensitivity must match rows")
    if report.min_timeline_quality_score != min(
        (row.timeline_quality_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_timeline_quality_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_input_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for value in values:
        _require_canonical_string("reason_codes", value)
        reject_research_event_dependency_graph_unsafe_payload("reason_codes", value)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must be unique")
    unknown = tuple(value for value in values if value not in INPUT_REASON_CODES)
    if unknown:
        raise ValueError("reason_codes must be supported input reason codes")
    if tuple(code for code in INPUT_REASON_CODES if code in values) != values:
        raise ValueError("reason_codes must use deterministic sequence")
    return values


def _normalize_known_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for value in values:
        _require_canonical_string(field_name, value)
        reject_research_event_dependency_graph_unsafe_payload(field_name, value)
        if value not in allowed:
            raise ValueError(f"{field_name} must contain supported codes")
    if tuple(code for code in allowed if code in values) != values:
        raise ValueError(f"{field_name} must use deterministic sequence")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must be unique")
    return values


def _normalize_safety_flags(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("safety_flags must be a tuple")
    if value != SAFETY_FLAGS:
        raise ValueError("safety_flags must match report-only safety flags")
    return value


def _normalize_redacted_event_ref(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if not value.startswith(REDACTED_EVENT_REF_PREFIX):
        raise ValueError(f"{field_name} must be redacted")
    reject_research_event_dependency_graph_unsafe_payload(field_name, value)
    return value


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_integral_decimal(field_name, value)
    if normalized <= Decimal("0"):
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == Decimal("0"):
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_unit_decimal("ratio", numerator / denominator)


def _raw_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == Decimal("0"):
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        ratio = numerator / denominator
    if ratio > ONE:
        return ONE
    return ratio


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a single-line string")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in _HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _digest_instance(instance: object, field_names: tuple[str, ...]) -> str:
    return _digest_payload(_instance_payload(instance, field_names))


def _digest_payload(payload: object) -> str:
    return sha256(_canonical_digest_text(_json_ready(payload)).encode()).hexdigest()


def _instance_digest_payload(
    instance: object,
    field_names: tuple[str, ...],
    digest: str,
) -> dict[str, object]:
    payload = _instance_payload(instance, field_names)
    payload["derived_validation_digest"] = digest
    return payload


def _instance_payload(instance: object, field_names: tuple[str, ...]) -> dict[str, object]:
    return {field_name: getattr(instance, field_name) for field_name in field_names}


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready({field.name: getattr(value, field.name) for field in fields(value)})
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _canonical_digest_text(value: object) -> str:
    if type(value) is dict:
        return "{" + ",".join(
            f"{key}:{_canonical_digest_text(value[key])}" for key in sorted(value)
        ) + "}"
    if type(value) is list:
        return "[" + ",".join(_canonical_digest_text(item) for item in value) + "]"
    return repr(value)


def _reject_unsafe_payload_entry(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload_entry(
            label,
            {field.name: getattr(value, field.name) for field in fields(value)},
        )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_text(label, key)
            _reject_unsafe_payload_entry(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_payload_entry(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(term in normalized for term in _UNSAFE_TERMS):
        raise ValueError(f"unsafe public payload entry in {label}")


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


__all__ = (
    "STATUS_VALUES",
    "SAFETY_FLAGS",
    "ResearchEventDependencyGraphReportConfig",
    "ResearchEventDependencyGraphInput",
    "ResearchEventDependencyGraphRow",
    "ResearchEventDependencyGraphReport",
    "build_research_event_dependency_graph_report",
    "research_event_dependency_graph_report_payload",
    "reject_research_event_dependency_graph_unsafe_payload",
)
