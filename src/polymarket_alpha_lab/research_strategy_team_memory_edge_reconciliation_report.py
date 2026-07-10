"""Pure team memory and probability edge reconciliation report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_TEAM_MEMORY_EDGE_RECONCILIATION_CONFIG_VERSION = (
    "research-strategy-team-memory-edge-reconciliation-v0"
)
RESEARCH_STRATEGY_TEAM_MEMORY_EDGE_RECONCILIATION_STATUSES = (
    "pass",
    "watch",
    "block",
)

PASS_REASON = "team_memory_edge_reconciliation_pass"
REPORT_BLOCK_REASON = "team_memory_edge_reconciliation_report_block"
REPORT_WATCH_REASON = "team_memory_edge_reconciliation_report_watch"
REPORT_PASS_REASON = "team_memory_edge_reconciliation_report_pass"

ROW_REASON_CODES = (
    "probability_edge_gap",
    "calibration_freshness_gap",
    "prior_outcome_learning_gap",
    "evidence_confidence_gap",
    "cost_pressure_gap",
    "reconciliation_score_gap",
    PASS_REASON,
)
REPORT_REASON_CODES = (
    REPORT_BLOCK_REASON,
    REPORT_WATCH_REASON,
    REPORT_PASS_REASON,
    "probability_edge_review",
    "calibration_freshness_review",
    "prior_outcome_learning_review",
    "evidence_confidence_review",
    "cost_pressure_review",
    "reconciliation_score_review",
)

RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
NEGATIVE_ONE = Decimal("-1.000000")
DIGEST_FIELD = "derived_validation_digest"
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_TEXT_HEXES = (
    "63616e6469646174655f6964",
    "63616e646964617465",
    "6d61726b65745f6964",
    "6d61726b65745f736c7567",
    "6d61726b6574",
    "736c7567",
    "7175657374696f6e",
    "736f757263655f75726c",
    "736f757263655f74657874",
    "736f75726365",
    "75726c",
    "64736e",
    "7461626c655f6e616d65",
    "7461626c65",
    "746f6b656e",
    "77616c6c6574",
    "6f72646572",
    "7472616465",
    "74726164696e67",
    "73697a696e67",
    "6c697665",
    "61757468",
    "707269766174655f6b6579",
    "70726976617465",
    "696e7465726e616c",
    "736563726574",
    "627579",
    "73656c6c",
    "7265636f6d6d656e646174696f6e",
)
PUBLIC_TEXT_BLOCKS = tuple(bytes.fromhex(value).decode("ascii") for value in PUBLIC_TEXT_HEXES)


@dataclass(frozen=True)
class ResearchStrategyTeamMemoryEdgeReconciliationConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_TEAM_MEMORY_EDGE_RECONCILIATION_CONFIG_VERSION
    probability_edge_pass_floor: Decimal = Decimal("0.050000")
    probability_edge_watch_floor: Decimal = Decimal("0.015000")
    calibration_freshness_pass_floor: Decimal = Decimal("0.800000")
    calibration_freshness_watch_floor: Decimal = Decimal("0.500000")
    prior_outcome_learning_pass_floor: Decimal = Decimal("0.750000")
    prior_outcome_learning_watch_floor: Decimal = Decimal("0.500000")
    evidence_confidence_pass_floor: Decimal = Decimal("0.800000")
    evidence_confidence_watch_floor: Decimal = Decimal("0.550000")
    cost_pressure_pass_ceiling: Decimal = Decimal("0.250000")
    cost_pressure_watch_ceiling: Decimal = Decimal("0.600000")
    reconciliation_score_pass_floor: Decimal = Decimal("0.750000")
    reconciliation_score_watch_floor: Decimal = Decimal("0.500000")
    probability_edge_weight: Decimal = Decimal("0.250000")
    calibration_freshness_weight: Decimal = Decimal("0.200000")
    prior_outcome_learning_weight: Decimal = Decimal("0.200000")
    evidence_confidence_weight: Decimal = Decimal("0.250000")
    cost_pressure_weight: Decimal = Decimal("0.100000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyTeamMemoryEdgeReconciliationConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamMemoryEdgeReconciliationConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyTeamMemoryEdgeReconciliationConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "probability_edge_pass_floor",
            "probability_edge_watch_floor",
            "calibration_freshness_pass_floor",
            "calibration_freshness_watch_floor",
            "prior_outcome_learning_pass_floor",
            "prior_outcome_learning_watch_floor",
            "evidence_confidence_pass_floor",
            "evidence_confidence_watch_floor",
            "cost_pressure_pass_ceiling",
            "cost_pressure_watch_ceiling",
            "reconciliation_score_pass_floor",
            "reconciliation_score_watch_floor",
            "probability_edge_weight",
            "calibration_freshness_weight",
            "prior_outcome_learning_weight",
            "evidence_confidence_weight",
            "cost_pressure_weight",
        ):
            object.__setattr__(self, field_name, _normalize_ratio(field_name, getattr(self, field_name)))
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_public_payload(_public_dict(self))
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchStrategyTeamMemoryEdgeReconciliationInput:
    analyst_row_label: str
    memory_signal_label: str
    observed_at: datetime
    probability_edge_estimate: Decimal
    calibration_freshness_score: Decimal
    prior_outcome_learning_score: Decimal
    evidence_confidence_score: Decimal
    cost_pressure_score: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyTeamMemoryEdgeReconciliationInput "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamMemoryEdgeReconciliationInput:
            raise ValueError(
                "input must be exactly ResearchStrategyTeamMemoryEdgeReconciliationInput",
            )
        for field_name in ("analyst_row_label", "memory_signal_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "probability_edge_estimate",
            _normalize_signed_ratio("probability_edge_estimate", self.probability_edge_estimate),
        )
        for field_name in (
            "calibration_freshness_score",
            "prior_outcome_learning_score",
            "evidence_confidence_score",
            "cost_pressure_score",
        ):
            object.__setattr__(self, field_name, _normalize_ratio(field_name, getattr(self, field_name)))
        _require_hard_flags("input", self)
        _reject_public_payload(_public_dict(self))
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        object.__setattr__(self, "input_ratio", _normalize_ratio("input_ratio", self.input_ratio))
        _require_hard_flags("reason_code_count", self)
        _reject_public_payload(_public_dict(self))
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchStrategyTeamMemoryEdgeReconciliationRow:
    analyst_row_label: str
    memory_signal_label: str
    manual_review_rank: Decimal
    observed_at: datetime
    probability_edge_estimate: Decimal
    absolute_probability_edge: Decimal
    probability_edge_score: Decimal
    calibration_freshness_score: Decimal
    prior_outcome_learning_score: Decimal
    evidence_confidence_score: Decimal
    cost_pressure_score: Decimal
    cost_quality_score: Decimal
    reconciliation_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyTeamMemoryEdgeReconciliationRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamMemoryEdgeReconciliationRow:
            raise ValueError("row must be exactly ResearchStrategyTeamMemoryEdgeReconciliationRow")
        for field_name in ("analyst_row_label", "memory_signal_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "manual_review_rank",
            _normalize_positive_count("manual_review_rank", self.manual_review_rank),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "probability_edge_estimate",
            _normalize_signed_ratio("probability_edge_estimate", self.probability_edge_estimate),
        )
        for field_name in (
            "absolute_probability_edge",
            "probability_edge_score",
            "calibration_freshness_score",
            "prior_outcome_learning_score",
            "evidence_confidence_score",
            "cost_pressure_score",
            "cost_quality_score",
            "reconciliation_score",
        ):
            object.__setattr__(self, field_name, _normalize_ratio(field_name, getattr(self, field_name)))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_public_payload(_public_dict(self))
        _require_or_set_digest(self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchStrategyTeamMemoryEdgeReconciliationReport:
    generated_at: datetime
    config_version: str
    config: ResearchStrategyTeamMemoryEdgeReconciliationConfig
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_absolute_probability_edge: Decimal
    average_cost_pressure_score: Decimal
    average_reconciliation_score: Decimal
    min_reconciliation_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount, ...]
    rows: tuple[ResearchStrategyTeamMemoryEdgeReconciliationRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyTeamMemoryEdgeReconciliationReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamMemoryEdgeReconciliationReport:
            raise ValueError("report must be exactly ResearchStrategyTeamMemoryEdgeReconciliationReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if type(self.config) is not ResearchStrategyTeamMemoryEdgeReconciliationConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyTeamMemoryEdgeReconciliationConfig",
            )
        _require_hard_flags("config", self.config)
        _require_or_set_digest(self.config)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(self, field_name, _normalize_count(field_name, getattr(self, field_name)))
        for field_name in (
            "average_absolute_probability_edge",
            "average_cost_pressure_score",
            "average_reconciliation_score",
            "min_reconciliation_score",
        ):
            object.__setattr__(self, field_name, _normalize_ratio(field_name, getattr(self, field_name)))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "reason_code_counts", _normalize_reason_code_counts(self.reason_code_counts))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _reject_public_payload(_public_dict(self))
        _validate_report(self)
        _require_or_set_digest(self)


_CONFIG_PAYLOAD_FIELDS = frozenset(
    {
        "config_version",
        "probability_edge_pass_floor",
        "probability_edge_watch_floor",
        "calibration_freshness_pass_floor",
        "calibration_freshness_watch_floor",
        "prior_outcome_learning_pass_floor",
        "prior_outcome_learning_watch_floor",
        "evidence_confidence_pass_floor",
        "evidence_confidence_watch_floor",
        "cost_pressure_pass_ceiling",
        "cost_pressure_watch_ceiling",
        "reconciliation_score_pass_floor",
        "reconciliation_score_watch_floor",
        "probability_edge_weight",
        "calibration_freshness_weight",
        "prior_outcome_learning_weight",
        "evidence_confidence_weight",
        "cost_pressure_weight",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    },
)
_ROW_PAYLOAD_FIELDS = frozenset(
    {
        "analyst_row_label",
        "memory_signal_label",
        "manual_review_rank",
        "observed_at",
        "probability_edge_estimate",
        "absolute_probability_edge",
        "probability_edge_score",
        "calibration_freshness_score",
        "prior_outcome_learning_score",
        "evidence_confidence_score",
        "cost_pressure_score",
        "cost_quality_score",
        "reconciliation_score",
        "status",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    },
)
_REASON_CODE_COUNT_PAYLOAD_FIELDS = frozenset(
    {
        "reason_code",
        "count",
        "input_ratio",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    },
)
_REPORT_PAYLOAD_FIELDS = frozenset(
    {
        "generated_at",
        "config_version",
        "config",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_absolute_probability_edge",
        "average_cost_pressure_score",
        "average_reconciliation_score",
        "min_reconciliation_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    },
)


def build_research_strategy_team_memory_edge_reconciliation_report(
    inputs: Iterable[ResearchStrategyTeamMemoryEdgeReconciliationInput],
    *,
    config: ResearchStrategyTeamMemoryEdgeReconciliationConfig,
    generated_at: datetime,
) -> ResearchStrategyTeamMemoryEdgeReconciliationReport:
    if type(config) is not ResearchStrategyTeamMemoryEdgeReconciliationConfig:
        raise ValueError("config must be a ResearchStrategyTeamMemoryEdgeReconciliationConfig")
    _require_hard_flags("config", config)
    _require_or_set_digest(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    unranked_rows = tuple(
        sorted(
            (
                _row_from_input(
                    value,
                    manual_review_rank=_count(1),
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    rows = tuple(
        replace(
            row,
            manual_review_rank=_count(index),
            derived_validation_digest="",
        )
        for index, row in enumerate(unranked_rows, start=1)
    )
    report_parts = dict(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        config=config,
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_absolute_probability_edge=_mean(tuple(row.absolute_probability_edge for row in rows)),
        average_cost_pressure_score=_mean(tuple(row.cost_pressure_score for row in rows)),
        average_reconciliation_score=_mean(tuple(row.reconciliation_score for row in rows)),
        min_reconciliation_score=_min_reconciliation_score(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return ResearchStrategyTeamMemoryEdgeReconciliationReport(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def research_strategy_team_memory_edge_reconciliation_report_payload(
    report: ResearchStrategyTeamMemoryEdgeReconciliationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyTeamMemoryEdgeReconciliationReport:
        raise ValueError("report must be a ResearchStrategyTeamMemoryEdgeReconciliationReport")
    _require_hard_flags("report", report)
    _require_or_set_digest(report)
    _validate_report(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    validate_research_strategy_team_memory_edge_reconciliation_report_payload(payload)
    return payload


def validate_research_strategy_team_memory_edge_reconciliation_report_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload(payload)
    _require_payload_flags(payload)
    _validate_payload_schema(payload)
    _validate_payload_digest_tree(payload)
    _report_from_payload(payload)
    return True


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    _require_exact_payload_schema("report payload", payload, _REPORT_PAYLOAD_FIELDS)
    config = payload["config"]
    if type(config) is not dict:
        raise ValueError("config payload must be a JSON object")
    _require_exact_payload_schema("config payload", config, _CONFIG_PAYLOAD_FIELDS)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_exact_payload_schema("row payload", row, _ROW_PAYLOAD_FIELDS)
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for reason_code_count in reason_code_counts:
        if type(reason_code_count) is not dict:
            raise ValueError("reason_code_counts must contain JSON objects")
        _require_exact_payload_schema(
            "reason code count payload",
            reason_code_count,
            _REASON_CODE_COUNT_PAYLOAD_FIELDS,
        )


def _report_from_payload(
    payload: dict[str, Any],
) -> ResearchStrategyTeamMemoryEdgeReconciliationReport:
    config = _config_from_payload(payload["config"])
    rows = tuple(_row_from_payload(value) for value in payload["rows"])
    reason_code_counts = tuple(
        _reason_code_count_from_payload(value)
        for value in payload["reason_code_counts"]
    )
    return ResearchStrategyTeamMemoryEdgeReconciliationReport(
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        config_version=_public_string_from_payload(
            "config_version",
            payload["config_version"],
        ),
        config=config,
        input_count=_count_from_payload("input_count", payload["input_count"]),
        pass_count=_count_from_payload("pass_count", payload["pass_count"]),
        watch_count=_count_from_payload("watch_count", payload["watch_count"]),
        block_count=_count_from_payload("block_count", payload["block_count"]),
        average_absolute_probability_edge=_ratio_from_payload(
            "average_absolute_probability_edge",
            payload["average_absolute_probability_edge"],
        ),
        average_cost_pressure_score=_ratio_from_payload(
            "average_cost_pressure_score",
            payload["average_cost_pressure_score"],
        ),
        average_reconciliation_score=_ratio_from_payload(
            "average_reconciliation_score",
            payload["average_reconciliation_score"],
        ),
        min_reconciliation_score=_ratio_from_payload(
            "min_reconciliation_score",
            payload["min_reconciliation_score"],
        ),
        status=_status_from_payload("status", payload["status"]),
        reason_codes=_reason_codes_from_payload(
            "reason_codes",
            payload["reason_codes"],
            REPORT_REASON_CODES,
        ),
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_digest_from_payload(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_true_from_payload("paper_only", payload["paper_only"]),
        report_only=_true_from_payload("report_only", payload["report_only"]),
        readonly=_true_from_payload("readonly", payload["readonly"]),
    )


def _config_from_payload(
    value: object,
) -> ResearchStrategyTeamMemoryEdgeReconciliationConfig:
    if type(value) is not dict:
        raise ValueError("config payload must be a JSON object")
    return ResearchStrategyTeamMemoryEdgeReconciliationConfig(
        config_version=_public_string_from_payload(
            "config_version",
            value["config_version"],
        ),
        probability_edge_pass_floor=_ratio_from_payload(
            "probability_edge_pass_floor",
            value["probability_edge_pass_floor"],
        ),
        probability_edge_watch_floor=_ratio_from_payload(
            "probability_edge_watch_floor",
            value["probability_edge_watch_floor"],
        ),
        calibration_freshness_pass_floor=_ratio_from_payload(
            "calibration_freshness_pass_floor",
            value["calibration_freshness_pass_floor"],
        ),
        calibration_freshness_watch_floor=_ratio_from_payload(
            "calibration_freshness_watch_floor",
            value["calibration_freshness_watch_floor"],
        ),
        prior_outcome_learning_pass_floor=_ratio_from_payload(
            "prior_outcome_learning_pass_floor",
            value["prior_outcome_learning_pass_floor"],
        ),
        prior_outcome_learning_watch_floor=_ratio_from_payload(
            "prior_outcome_learning_watch_floor",
            value["prior_outcome_learning_watch_floor"],
        ),
        evidence_confidence_pass_floor=_ratio_from_payload(
            "evidence_confidence_pass_floor",
            value["evidence_confidence_pass_floor"],
        ),
        evidence_confidence_watch_floor=_ratio_from_payload(
            "evidence_confidence_watch_floor",
            value["evidence_confidence_watch_floor"],
        ),
        cost_pressure_pass_ceiling=_ratio_from_payload(
            "cost_pressure_pass_ceiling",
            value["cost_pressure_pass_ceiling"],
        ),
        cost_pressure_watch_ceiling=_ratio_from_payload(
            "cost_pressure_watch_ceiling",
            value["cost_pressure_watch_ceiling"],
        ),
        reconciliation_score_pass_floor=_ratio_from_payload(
            "reconciliation_score_pass_floor",
            value["reconciliation_score_pass_floor"],
        ),
        reconciliation_score_watch_floor=_ratio_from_payload(
            "reconciliation_score_watch_floor",
            value["reconciliation_score_watch_floor"],
        ),
        probability_edge_weight=_ratio_from_payload(
            "probability_edge_weight",
            value["probability_edge_weight"],
        ),
        calibration_freshness_weight=_ratio_from_payload(
            "calibration_freshness_weight",
            value["calibration_freshness_weight"],
        ),
        prior_outcome_learning_weight=_ratio_from_payload(
            "prior_outcome_learning_weight",
            value["prior_outcome_learning_weight"],
        ),
        evidence_confidence_weight=_ratio_from_payload(
            "evidence_confidence_weight",
            value["evidence_confidence_weight"],
        ),
        cost_pressure_weight=_ratio_from_payload(
            "cost_pressure_weight",
            value["cost_pressure_weight"],
        ),
        derived_validation_digest=_digest_from_payload(
            "derived_validation_digest",
            value["derived_validation_digest"],
        ),
        paper_only=_true_from_payload("paper_only", value["paper_only"]),
        report_only=_true_from_payload("report_only", value["report_only"]),
        readonly=_true_from_payload("readonly", value["readonly"]),
    )


def _row_from_payload(
    value: object,
) -> ResearchStrategyTeamMemoryEdgeReconciliationRow:
    if type(value) is not dict:
        raise ValueError("row payload must be a JSON object")
    return ResearchStrategyTeamMemoryEdgeReconciliationRow(
        analyst_row_label=_public_string_from_payload(
            "analyst_row_label",
            value["analyst_row_label"],
        ),
        memory_signal_label=_public_string_from_payload(
            "memory_signal_label",
            value["memory_signal_label"],
        ),
        manual_review_rank=_count_from_payload(
            "manual_review_rank",
            value["manual_review_rank"],
        ),
        observed_at=_datetime_from_payload("observed_at", value["observed_at"]),
        probability_edge_estimate=_signed_ratio_from_payload(
            "probability_edge_estimate",
            value["probability_edge_estimate"],
        ),
        absolute_probability_edge=_ratio_from_payload(
            "absolute_probability_edge",
            value["absolute_probability_edge"],
        ),
        probability_edge_score=_ratio_from_payload(
            "probability_edge_score",
            value["probability_edge_score"],
        ),
        calibration_freshness_score=_ratio_from_payload(
            "calibration_freshness_score",
            value["calibration_freshness_score"],
        ),
        prior_outcome_learning_score=_ratio_from_payload(
            "prior_outcome_learning_score",
            value["prior_outcome_learning_score"],
        ),
        evidence_confidence_score=_ratio_from_payload(
            "evidence_confidence_score",
            value["evidence_confidence_score"],
        ),
        cost_pressure_score=_ratio_from_payload(
            "cost_pressure_score",
            value["cost_pressure_score"],
        ),
        cost_quality_score=_ratio_from_payload(
            "cost_quality_score",
            value["cost_quality_score"],
        ),
        reconciliation_score=_ratio_from_payload(
            "reconciliation_score",
            value["reconciliation_score"],
        ),
        status=_status_from_payload("status", value["status"]),
        reason_codes=_reason_codes_from_payload(
            "reason_codes",
            value["reason_codes"],
            ROW_REASON_CODES,
        ),
        derived_validation_digest=_digest_from_payload(
            "derived_validation_digest",
            value["derived_validation_digest"],
        ),
        paper_only=_true_from_payload("paper_only", value["paper_only"]),
        report_only=_true_from_payload("report_only", value["report_only"]),
        readonly=_true_from_payload("readonly", value["readonly"]),
    )


def _reason_code_count_from_payload(
    value: object,
) -> ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("reason code count payload must be a JSON object")
    return ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount(
        reason_code=_reason_code_from_payload("reason_code", value["reason_code"]),
        count=_count_from_payload("count", value["count"]),
        input_ratio=_ratio_from_payload("input_ratio", value["input_ratio"]),
        derived_validation_digest=_digest_from_payload(
            "derived_validation_digest",
            value["derived_validation_digest"],
        ),
        paper_only=_true_from_payload("paper_only", value["paper_only"]),
        report_only=_true_from_payload("report_only", value["report_only"]),
        readonly=_true_from_payload("readonly", value["readonly"]),
    )


def _row_from_input(
    value: ResearchStrategyTeamMemoryEdgeReconciliationInput,
    *,
    manual_review_rank: Decimal,
    config: ResearchStrategyTeamMemoryEdgeReconciliationConfig,
    generated_at: datetime,
) -> ResearchStrategyTeamMemoryEdgeReconciliationRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    absolute_edge = _absolute_decimal(value.probability_edge_estimate)
    probability_edge_score = _clamp_ratio(_divide_decimal(absolute_edge, config.probability_edge_pass_floor))
    cost_quality_score = _subtract_ratio(ONE, value.cost_pressure_score)
    reconciliation_score = _reconciliation_score(
        probability_edge_score=probability_edge_score,
        calibration_freshness_score=value.calibration_freshness_score,
        prior_outcome_learning_score=value.prior_outcome_learning_score,
        evidence_confidence_score=value.evidence_confidence_score,
        cost_quality_score=cost_quality_score,
        config=config,
    )
    status = _row_status(
        absolute_probability_edge=absolute_edge,
        calibration_freshness_score=value.calibration_freshness_score,
        prior_outcome_learning_score=value.prior_outcome_learning_score,
        evidence_confidence_score=value.evidence_confidence_score,
        cost_pressure_score=value.cost_pressure_score,
        reconciliation_score=reconciliation_score,
        config=config,
    )
    row_parts = dict(
        analyst_row_label=value.analyst_row_label,
        memory_signal_label=value.memory_signal_label,
        manual_review_rank=manual_review_rank,
        observed_at=observed_at,
        probability_edge_estimate=value.probability_edge_estimate,
        absolute_probability_edge=absolute_edge,
        probability_edge_score=probability_edge_score,
        calibration_freshness_score=value.calibration_freshness_score,
        prior_outcome_learning_score=value.prior_outcome_learning_score,
        evidence_confidence_score=value.evidence_confidence_score,
        cost_pressure_score=value.cost_pressure_score,
        cost_quality_score=cost_quality_score,
        reconciliation_score=reconciliation_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            absolute_probability_edge=absolute_edge,
            calibration_freshness_score=value.calibration_freshness_score,
            prior_outcome_learning_score=value.prior_outcome_learning_score,
            evidence_confidence_score=value.evidence_confidence_score,
            cost_pressure_score=value.cost_pressure_score,
            reconciliation_score=reconciliation_score,
            config=config,
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return ResearchStrategyTeamMemoryEdgeReconciliationRow(
        **row_parts,
        derived_validation_digest=_digest_public(row_parts),
    )


def _reconciliation_score(
    *,
    probability_edge_score: Decimal,
    calibration_freshness_score: Decimal,
    prior_outcome_learning_score: Decimal,
    evidence_confidence_score: Decimal,
    cost_quality_score: Decimal,
    config: ResearchStrategyTeamMemoryEdgeReconciliationConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            probability_edge_score * config.probability_edge_weight
            + calibration_freshness_score * config.calibration_freshness_weight
            + prior_outcome_learning_score * config.prior_outcome_learning_weight
            + evidence_confidence_score * config.evidence_confidence_weight
            + cost_quality_score * config.cost_pressure_weight,
        )


def _row_status(
    *,
    absolute_probability_edge: Decimal,
    calibration_freshness_score: Decimal,
    prior_outcome_learning_score: Decimal,
    evidence_confidence_score: Decimal,
    cost_pressure_score: Decimal,
    reconciliation_score: Decimal,
    config: ResearchStrategyTeamMemoryEdgeReconciliationConfig,
) -> str:
    if (
        absolute_probability_edge < config.probability_edge_watch_floor
        or calibration_freshness_score < config.calibration_freshness_watch_floor
        or prior_outcome_learning_score < config.prior_outcome_learning_watch_floor
        or evidence_confidence_score < config.evidence_confidence_watch_floor
        or cost_pressure_score > config.cost_pressure_watch_ceiling
        or reconciliation_score < config.reconciliation_score_watch_floor
    ):
        return "block"
    if (
        absolute_probability_edge >= config.probability_edge_pass_floor
        and calibration_freshness_score >= config.calibration_freshness_pass_floor
        and prior_outcome_learning_score >= config.prior_outcome_learning_pass_floor
        and evidence_confidence_score >= config.evidence_confidence_pass_floor
        and cost_pressure_score <= config.cost_pressure_pass_ceiling
        and reconciliation_score >= config.reconciliation_score_pass_floor
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    status: str,
    absolute_probability_edge: Decimal,
    calibration_freshness_score: Decimal,
    prior_outcome_learning_score: Decimal,
    evidence_confidence_score: Decimal,
    cost_pressure_score: Decimal,
    reconciliation_score: Decimal,
    config: ResearchStrategyTeamMemoryEdgeReconciliationConfig,
) -> tuple[str, ...]:
    if status == "pass":
        return (PASS_REASON,)
    requested_codes: set[str] = set()
    if absolute_probability_edge < config.probability_edge_pass_floor:
        requested_codes.add("probability_edge_gap")
    if calibration_freshness_score < config.calibration_freshness_pass_floor:
        requested_codes.add("calibration_freshness_gap")
    if prior_outcome_learning_score < config.prior_outcome_learning_pass_floor:
        requested_codes.add("prior_outcome_learning_gap")
    if evidence_confidence_score < config.evidence_confidence_pass_floor:
        requested_codes.add("evidence_confidence_gap")
    if cost_pressure_score > config.cost_pressure_pass_ceiling:
        requested_codes.add("cost_pressure_gap")
    if reconciliation_score < config.reconciliation_score_pass_floor:
        requested_codes.add("reconciliation_score_gap")
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in requested_codes)


def _report_status(rows: tuple[ResearchStrategyTeamMemoryEdgeReconciliationRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyTeamMemoryEdgeReconciliationRow, ...],
) -> tuple[str, ...]:
    report_status = _report_status(rows)
    if report_status == "pass":
        return (REPORT_PASS_REASON,)
    requested_codes = {f"team_memory_edge_reconciliation_report_{report_status}"}
    row_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    if "probability_edge_gap" in row_codes:
        requested_codes.add("probability_edge_review")
    if "calibration_freshness_gap" in row_codes:
        requested_codes.add("calibration_freshness_review")
    if "prior_outcome_learning_gap" in row_codes:
        requested_codes.add("prior_outcome_learning_review")
    if "evidence_confidence_gap" in row_codes:
        requested_codes.add("evidence_confidence_review")
    if "cost_pressure_gap" in row_codes:
        requested_codes.add("cost_pressure_review")
    if "reconciliation_score_gap" in row_codes:
        requested_codes.add("reconciliation_score_review")
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in requested_codes)


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyTeamMemoryEdgeReconciliationRow, ...],
) -> tuple[ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            input_ratio=_divide_decimal(_count(counts[reason_code]), denominator),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in counts
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyTeamMemoryEdgeReconciliationInput],
) -> tuple[ResearchStrategyTeamMemoryEdgeReconciliationInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchStrategyTeamMemoryEdgeReconciliationInput:
            raise ValueError(
                "inputs must contain ResearchStrategyTeamMemoryEdgeReconciliationInput values",
            )
        _require_hard_flags("input", row)
        _reject_public_payload(_public_dict(row))
        _require_or_set_digest(row)
        key = (row.analyst_row_label, row.memory_signal_label)
        if key in seen_keys:
            raise ValueError("duplicate team memory edge reconciliation input")
        seen_keys.add(key)
    return rows


def _normalize_rows(
    values: Iterable[ResearchStrategyTeamMemoryEdgeReconciliationRow],
) -> tuple[ResearchStrategyTeamMemoryEdgeReconciliationRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchStrategyTeamMemoryEdgeReconciliationRow:
            raise ValueError(
                "rows must contain ResearchStrategyTeamMemoryEdgeReconciliationRow values",
            )
        _require_hard_flags("row", row)
        _reject_public_payload(_public_dict(row))
        _require_or_set_digest(row)
        key = (row.analyst_row_label, row.memory_signal_label)
        if key in seen_keys:
            raise ValueError("rows must be unique")
        seen_keys.add(key)
    return rows


def _normalize_reason_code_counts(
    values: Iterable[ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount],
) -> tuple[ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
        _reject_public_payload(_public_dict(row))
        _require_or_set_digest(row)
    return rows


def _validate_config(config: ResearchStrategyTeamMemoryEdgeReconciliationConfig) -> None:
    if config.config_version != DEFAULT_RESEARCH_STRATEGY_TEAM_MEMORY_EDGE_RECONCILIATION_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    if config.probability_edge_pass_floor <= ZERO:
        raise ValueError(
            "probability_edge_pass_floor must be greater than 0.000000",
        )
    _require_floor_pair(
        "probability_edge",
        config.probability_edge_pass_floor,
        config.probability_edge_watch_floor,
    )
    _require_floor_pair(
        "calibration_freshness",
        config.calibration_freshness_pass_floor,
        config.calibration_freshness_watch_floor,
    )
    _require_floor_pair(
        "prior_outcome_learning",
        config.prior_outcome_learning_pass_floor,
        config.prior_outcome_learning_watch_floor,
    )
    _require_floor_pair(
        "evidence_confidence",
        config.evidence_confidence_pass_floor,
        config.evidence_confidence_watch_floor,
    )
    _require_ceiling_pair(
        "cost_pressure",
        config.cost_pressure_pass_ceiling,
        config.cost_pressure_watch_ceiling,
    )
    _require_floor_pair(
        "reconciliation_score",
        config.reconciliation_score_pass_floor,
        config.reconciliation_score_watch_floor,
    )
    _require_ratio_total(
        config.probability_edge_weight,
        config.calibration_freshness_weight,
        config.prior_outcome_learning_weight,
        config.evidence_confidence_weight,
        config.cost_pressure_weight,
    )


def _validate_row(row: ResearchStrategyTeamMemoryEdgeReconciliationRow) -> None:
    if row.absolute_probability_edge != _absolute_decimal(row.probability_edge_estimate):
        raise ValueError("absolute_probability_edge must match probability_edge_estimate")
    if row.cost_quality_score != _subtract_ratio(ONE, row.cost_pressure_score):
        raise ValueError("cost_quality_score must match cost_pressure_score")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use pass reason")
    if row.status != "pass" and row.reason_codes == (PASS_REASON,):
        raise ValueError("attention rows must include gap reasons")


def _validate_row_against_config(
    row: ResearchStrategyTeamMemoryEdgeReconciliationRow,
    *,
    config: ResearchStrategyTeamMemoryEdgeReconciliationConfig,
) -> None:
    expected_absolute_edge = _absolute_decimal(row.probability_edge_estimate)
    if row.absolute_probability_edge != expected_absolute_edge:
        raise ValueError("absolute_probability_edge must match probability_edge_estimate")
    expected_probability_edge_score = _clamp_ratio(
        _divide_decimal(expected_absolute_edge, config.probability_edge_pass_floor),
    )
    if row.probability_edge_score != expected_probability_edge_score:
        raise ValueError("probability_edge_score must match probability edge policy")
    expected_cost_quality_score = _subtract_ratio(ONE, row.cost_pressure_score)
    if row.cost_quality_score != expected_cost_quality_score:
        raise ValueError("cost_quality_score must match cost_pressure_score")
    expected_reconciliation_score = _reconciliation_score(
        probability_edge_score=expected_probability_edge_score,
        calibration_freshness_score=row.calibration_freshness_score,
        prior_outcome_learning_score=row.prior_outcome_learning_score,
        evidence_confidence_score=row.evidence_confidence_score,
        cost_quality_score=expected_cost_quality_score,
        config=config,
    )
    if row.reconciliation_score != expected_reconciliation_score:
        raise ValueError("reconciliation_score must match configured component weights")
    expected_status = _row_status(
        absolute_probability_edge=expected_absolute_edge,
        calibration_freshness_score=row.calibration_freshness_score,
        prior_outcome_learning_score=row.prior_outcome_learning_score,
        evidence_confidence_score=row.evidence_confidence_score,
        cost_pressure_score=row.cost_pressure_score,
        reconciliation_score=expected_reconciliation_score,
        config=config,
    )
    if row.status != expected_status:
        raise ValueError("status must match row policy")
    expected_reason_codes = _row_reason_codes(
        status=expected_status,
        absolute_probability_edge=expected_absolute_edge,
        calibration_freshness_score=row.calibration_freshness_score,
        prior_outcome_learning_score=row.prior_outcome_learning_score,
        evidence_confidence_score=row.evidence_confidence_score,
        cost_pressure_score=row.cost_pressure_score,
        reconciliation_score=expected_reconciliation_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row policy")


def _validate_report(report: ResearchStrategyTeamMemoryEdgeReconciliationReport) -> None:
    rows = report.rows
    if report.config_version != report.config.config_version:
        raise ValueError("config_version must match config")
    for row in rows:
        if row.observed_at > report.generated_at:
            raise ValueError("observed_at must not be after generated_at")
        _validate_row_against_config(row, config=report.config)
    for index, row in enumerate(rows, start=1):
        if row.manual_review_rank != _count(index):
            raise ValueError("manual_review_rank must match stable row sequence")
    if report.input_count != _count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.input_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match input_count")
    if report.average_absolute_probability_edge != _mean(tuple(row.absolute_probability_edge for row in rows)):
        raise ValueError("average_absolute_probability_edge must match rows")
    if report.average_cost_pressure_score != _mean(tuple(row.cost_pressure_score for row in rows)):
        raise ValueError("average_cost_pressure_score must match rows")
    if report.average_reconciliation_score != _mean(tuple(row.reconciliation_score for row in rows)):
        raise ValueError("average_reconciliation_score must match rows")
    if report.min_reconciliation_score != _min_reconciliation_score(rows):
        raise ValueError("min_reconciliation_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use stable sort")


def _row_sort_key(
    row: ResearchStrategyTeamMemoryEdgeReconciliationRow,
) -> tuple[int, Decimal, str, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.reconciliation_score,
        row.analyst_row_label,
        row.memory_signal_label,
    )


def _status_count(
    rows: tuple[ResearchStrategyTeamMemoryEdgeReconciliationRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _min_reconciliation_score(
    rows: tuple[ResearchStrategyTeamMemoryEdgeReconciliationRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.reconciliation_score for row in rows)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _subtract_ratio(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(left - right)


def _absolute_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    normalized = _quantize_preserving_zero_sign(value)
    _reject_signed_zero(field_name, value, normalized)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    if normalized != normalized.to_integral_value().quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _canonical_zero(normalized)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    normalized = _quantize_preserving_zero_sign(value)
    _reject_signed_zero(field_name, value, normalized)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return _canonical_zero(normalized)


def _normalize_signed_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < NEGATIVE_ONE or value > ONE:
        raise ValueError(f"{field_name} must be between -1.000000 and 1.000000")
    normalized = _quantize_preserving_zero_sign(value)
    _reject_signed_zero(field_name, value, normalized)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return _canonical_zero(normalized)


def _quantize(value: Decimal) -> Decimal:
    return _canonical_zero(_quantize_preserving_zero_sign(value))


def _quantize_preserving_zero_sign(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(RATIO_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError("value must be quantizable to 0.000001") from exc


def _reject_signed_zero(field_name: str, value: Decimal, normalized: Decimal) -> None:
    if (value.is_zero() and value.is_signed()) or (
        normalized.is_zero() and normalized.is_signed()
    ):
        raise ValueError(f"{field_name} must not use signed zero")


def _canonical_zero(value: Decimal) -> Decimal:
    if value.is_zero():
        return ZERO
    return value


def _require_floor_pair(name: str, pass_floor: Decimal, watch_floor: Decimal) -> None:
    if pass_floor < watch_floor:
        raise ValueError(f"{name}_pass_floor must be at least {name}_watch_floor")


def _require_ceiling_pair(name: str, pass_ceiling: Decimal, watch_ceiling: Decimal) -> None:
    if watch_ceiling < pass_ceiling:
        raise ValueError(f"{name}_watch_ceiling must be at least {name}_pass_ceiling")


def _require_ratio_total(*values: Decimal) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total = _quantize(sum(values, ZERO))
    if total != ONE:
        raise ValueError("component weights must sum to 1.000000")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_STRATEGY_TEAM_MEMORY_EDGE_RECONCILIATION_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must contain known values")
    _reject_public_text(value)


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    allowed_ranks = {reason_code: index for index, reason_code in enumerate(allowed_values)}
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code, allowed_values)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must be deterministic")
    if any(reason_code not in allowed_ranks for reason_code in reason_codes):
        raise ValueError(f"{field_name} must contain known values")
    return reason_codes


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    _reject_public_text(value)


def _reject_public_text(value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in PUBLIC_TEXT_BLOCKS):
        raise ValueError("unsafe public value")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_payload_schema(
    label: str,
    value: dict[str, Any],
    expected_fields: frozenset[str],
) -> None:
    if type(value) is not dict or frozenset(value) != expected_fields:
        raise ValueError(f"{label} must use exact schema")


def _decimal_string_from_payload(field_name: str, value: object) -> tuple[str, Decimal]:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    return value, parsed


def _count_from_payload(field_name: str, value: object) -> Decimal:
    text, parsed = _decimal_string_from_payload(field_name, value)
    normalized = _normalize_count(field_name, parsed)
    if text != format(normalized, ".6f"):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _ratio_from_payload(field_name: str, value: object) -> Decimal:
    text, parsed = _decimal_string_from_payload(field_name, value)
    normalized = _normalize_ratio(field_name, parsed)
    if text != format(normalized, ".6f"):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _signed_ratio_from_payload(field_name: str, value: object) -> Decimal:
    text, parsed = _decimal_string_from_payload(field_name, value)
    normalized = _normalize_signed_ratio(field_name, parsed)
    if text != format(normalized, ".6f"):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
        normalized = _as_utc(field_name, parsed)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string") from exc
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _public_string_from_payload(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _status_from_payload(field_name: str, value: object) -> str:
    _require_status(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _reason_code_from_payload(field_name: str, value: object) -> str:
    _require_reason_code(field_name, value, ROW_REASON_CODES)
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain known values")
    return value


def _reason_codes_from_payload(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(field_name, value, allowed_values)


def _digest_from_payload(field_name: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _true_from_payload(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, DIGEST_FIELD)
    expected = _digest_public(_public_dict(value, include_digest=False))
    if current == "":
        object.__setattr__(value, DIGEST_FIELD, expected)
        return
    if type(current) is not str or current != expected:
        raise ValueError("derived_validation_digest payload mismatch")


def _digest_public(value: object) -> str:
    ready = _strip_digest_fields(_json_ready(value))
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _public_dict(value: object, *, include_digest: bool = True) -> dict[str, Any]:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: getattr(value, field.name)
            for field in fields(value)
            if include_digest or field.name != DIGEST_FIELD
        }
    if isinstance(value, dict):
        if include_digest:
            return dict(value)
        return {key: item for key, item in value.items() if key != DIGEST_FIELD}
    raise ValueError("value must be a public object")


def _strip_digest_fields(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _strip_digest_fields(item)
            for key, item in value.items()
            if key != DIGEST_FIELD
        }
    if isinstance(value, list):
        return [_strip_digest_fields(item) for item in value]
    return value


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(_public_dict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        _reject_public_text(value)
        return value
    if type(value) is bool:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_public_text(key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_payload(_public_dict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public key")
            _reject_public_text(key)
            _reject_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) is str:
        _reject_public_text(value)


def _require_payload_flags(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True")
            _require_payload_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_payload_flags(item)


def _validate_payload_digest_tree(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _validate_payload_digest_tree(item)
        if DIGEST_FIELD in value:
            current = value[DIGEST_FIELD]
            if type(current) is not str or current != _digest_public(value):
                raise ValueError("derived_validation_digest payload mismatch")
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_MEMORY_EDGE_RECONCILIATION_CONFIG_VERSION",
    "RESEARCH_STRATEGY_TEAM_MEMORY_EDGE_RECONCILIATION_STATUSES",
    "ResearchStrategyTeamMemoryEdgeReconciliationConfig",
    "ResearchStrategyTeamMemoryEdgeReconciliationInput",
    "ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount",
    "ResearchStrategyTeamMemoryEdgeReconciliationRow",
    "ResearchStrategyTeamMemoryEdgeReconciliationReport",
    "build_research_strategy_team_memory_edge_reconciliation_report",
    "research_strategy_team_memory_edge_reconciliation_report_payload",
    "validate_research_strategy_team_memory_edge_reconciliation_report_payload",
)
