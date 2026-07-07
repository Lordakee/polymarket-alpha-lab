"""Pure report-only candidate research readiness gate."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_CANDIDATE_DECISION_RESEARCH_READINESS_GATE_CONFIG_VERSION = (
    "research-readiness-gate-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_GATE_STATUSES = frozenset(("pass", "watch", "block"))
_HARD_SAFETY_FLAGS = (
    "paper_only",
    "report_only",
    "readonly",
    "human_research_only",
    "execution_disabled",
)
_BLOCK_REASON_CODES = frozenset(
    (
        "event_specificity_block",
        "evidence_traceability_block",
        "cost_threshold_block",
        "evidence_diversity_block",
        "adjudication_path_clarity_block",
    ),
)
_REASON_CODE_SEQUENCE = (
    "empty_input",
    "event_specificity_block",
    "evidence_traceability_block",
    "cost_threshold_block",
    "evidence_diversity_block",
    "adjudication_path_clarity_block",
    "event_specificity_watch",
    "evidence_traceability_watch",
    "cost_threshold_watch",
    "evidence_diversity_watch",
    "adjudication_path_clarity_watch",
    "readiness_gate_pass",
)
_NEXT_STEP_BY_STATUS = {
    "pass": "manual_research_standard_queue",
    "watch": "manual_research_elevated_queue",
    "block": "hold_for_readiness_rework",
}
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "raw-candidate",
    "raw candidate",
    "candidate",
    "market",
    "slug",
    "question",
    "source_ref",
    "source-ref",
    "source ref",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
    "recommend",
    "http://",
    "https://",
    "://",
)


@dataclass(frozen=True)
class CandidateDecisionResearchReadinessGateConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_RESEARCH_READINESS_GATE_CONFIG_VERSION
    )
    min_pass_event_specificity_score: Decimal = Decimal("0.800000")
    min_watch_event_specificity_score: Decimal = Decimal("0.500000")
    min_pass_evidence_traceability_score: Decimal = Decimal("0.750000")
    min_watch_evidence_traceability_score: Decimal = Decimal("0.500000")
    min_pass_cost_threshold_score: Decimal = Decimal("0.750000")
    min_watch_cost_threshold_score: Decimal = Decimal("0.500000")
    min_pass_evidence_diversity_score: Decimal = Decimal("0.750000")
    min_watch_evidence_diversity_score: Decimal = Decimal("0.550000")
    min_pass_adjudication_path_clarity_score: Decimal = Decimal("0.800000")
    min_watch_adjudication_path_clarity_score: Decimal = Decimal("0.600000")
    event_specificity_weight: Decimal = Decimal("0.200000")
    evidence_traceability_weight: Decimal = Decimal("0.200000")
    cost_threshold_weight: Decimal = Decimal("0.200000")
    evidence_diversity_weight: Decimal = Decimal("0.200000")
    adjudication_path_clarity_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionResearchReadinessGateConfig:
            raise TypeError(
                "CandidateDecisionResearchReadinessGateConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResearchReadinessGateConfig:
            raise ValueError(
                "config must be exactly CandidateDecisionResearchReadinessGateConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_RESEARCH_READINESS_GATE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_event_specificity_score",
            "min_watch_event_specificity_score",
            "min_pass_evidence_traceability_score",
            "min_watch_evidence_traceability_score",
            "min_pass_cost_threshold_score",
            "min_watch_cost_threshold_score",
            "min_pass_evidence_diversity_score",
            "min_watch_evidence_diversity_score",
            "min_pass_adjudication_path_clarity_score",
            "min_watch_adjudication_path_clarity_score",
            "event_specificity_weight",
            "evidence_traceability_weight",
            "cost_threshold_weight",
            "evidence_diversity_weight",
            "adjudication_path_clarity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class CandidateDecisionResearchReadinessInput:
    queue_item_key: str
    event_specificity_score: Decimal
    evidence_traceability_score: Decimal
    cost_threshold_score: Decimal
    evidence_diversity_score: Decimal
    adjudication_path_clarity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionResearchReadinessInput:
            raise TypeError(
                "CandidateDecisionResearchReadinessInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResearchReadinessInput:
            raise ValueError("input must be exactly CandidateDecisionResearchReadinessInput")
        _require_public_identifier("queue_item_key", self.queue_item_key)
        for field_name in (
            "event_specificity_score",
            "evidence_traceability_score",
            "cost_threshold_score",
            "evidence_diversity_score",
            "adjudication_path_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class CandidateDecisionResearchReadinessPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionResearchReadinessPublicPayloadItem:
            raise TypeError(
                "CandidateDecisionResearchReadinessPublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResearchReadinessPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "CandidateDecisionResearchReadinessPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class CandidateDecisionResearchReadinessGateRow:
    queue_item_key: str
    event_specificity_score: Decimal
    evidence_traceability_score: Decimal
    cost_threshold_score: Decimal
    evidence_diversity_score: Decimal
    adjudication_path_clarity_score: Decimal
    research_readiness_score: Decimal
    gate_status: str
    queue_next_step: str
    reason_codes: tuple[str, ...]
    hard_safety_flags: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionResearchReadinessGateRow:
            raise TypeError(
                "CandidateDecisionResearchReadinessGateRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResearchReadinessGateRow:
            raise ValueError("row must be exactly CandidateDecisionResearchReadinessGateRow")
        _require_public_identifier("queue_item_key", self.queue_item_key)
        for field_name in (
            "event_specificity_score",
            "evidence_traceability_score",
            "cost_threshold_score",
            "evidence_diversity_score",
            "adjudication_path_clarity_score",
            "research_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_gate_status("gate_status", self.gate_status)
        if self.queue_next_step != _NEXT_STEP_BY_STATUS[self.gate_status]:
            raise ValueError("queue_next_step must match gate_status")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "hard_safety_flags",
            _normalize_hard_safety_flags(self.hard_safety_flags),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class CandidateDecisionResearchReadinessGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    queue_next_step: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    pass_ratio: Decimal | None
    watch_ratio: Decimal | None
    block_ratio: Decimal | None
    average_research_readiness_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[CandidateDecisionResearchReadinessGateRow, ...]
    public_payload: tuple[CandidateDecisionResearchReadinessPublicPayloadItem, ...]
    hard_safety_flags: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionResearchReadinessGateReport:
            raise TypeError(
                "CandidateDecisionResearchReadinessGateReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResearchReadinessGateReport:
            raise ValueError("report must be exactly CandidateDecisionResearchReadinessGateReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_RESEARCH_READINESS_GATE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_gate_status("gate_status", self.gate_status)
        if self.queue_next_step != _NEXT_STEP_BY_STATUS[self.gate_status]:
            raise ValueError("queue_next_step must match gate_status")
        for field_name in (
            "item_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("pass_ratio", "watch_ratio", "block_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_research_readiness_score",
            _require_ratio_decimal(
                "average_research_readiness_score",
                self.average_research_readiness_score,
            ),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        object.__setattr__(
            self,
            "hard_safety_flags",
            _normalize_hard_safety_flags(self.hard_safety_flags),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return candidate_decision_research_readiness_gate_payload(self)


def build_candidate_decision_research_readiness_gate(
    inputs: Sequence[CandidateDecisionResearchReadinessInput],
    *,
    generated_at: datetime,
    config: CandidateDecisionResearchReadinessGateConfig | None = None,
    public_payload: Sequence[CandidateDecisionResearchReadinessPublicPayloadItem] = (),
) -> CandidateDecisionResearchReadinessGateReport:
    """Build a deterministic paper-only readiness gate for human research intake."""

    if config is None:
        config = CandidateDecisionResearchReadinessGateConfig()
    if type(config) is not CandidateDecisionResearchReadinessGateConfig:
        raise ValueError("config must be a CandidateDecisionResearchReadinessGateConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = _build_rows(normalized_inputs, config)
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "gate_status": status,
        "queue_next_step": _NEXT_STEP_BY_STATUS[status],
        "item_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "pass_ratio": _optional_ratio(_status_count(rows, "pass"), len(rows)),
        "watch_ratio": _optional_ratio(_status_count(rows, "watch"), len(rows)),
        "block_ratio": _optional_ratio(_status_count(rows, "block"), len(rows)),
        "average_research_readiness_score": _average_ratio(
            tuple(row.research_readiness_score for row in rows),
        ),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "public_payload": _normalize_public_payload(public_payload),
        "hard_safety_flags": _HARD_SAFETY_FLAGS,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return CandidateDecisionResearchReadinessGateReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def candidate_decision_research_readiness_gate_payload(
    value: CandidateDecisionResearchReadinessGateReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is CandidateDecisionResearchReadinessGateReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a CandidateDecisionResearchReadinessGateReport or dict",
        )
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


def _build_rows(
    inputs: tuple[CandidateDecisionResearchReadinessInput, ...],
    config: CandidateDecisionResearchReadinessGateConfig,
) -> tuple[CandidateDecisionResearchReadinessGateRow, ...]:
    return tuple(
        sorted(
            (_row_for_input(item, config) for item in inputs),
            key=_row_sort_key,
        ),
    )


def _row_for_input(
    item: CandidateDecisionResearchReadinessInput,
    config: CandidateDecisionResearchReadinessGateConfig,
) -> CandidateDecisionResearchReadinessGateRow:
    readiness_score = _research_readiness_score(item, config)
    reason_codes = _row_reason_codes(item, config)
    status = _row_status(reason_codes)
    return CandidateDecisionResearchReadinessGateRow(
        queue_item_key=item.queue_item_key,
        event_specificity_score=item.event_specificity_score,
        evidence_traceability_score=item.evidence_traceability_score,
        cost_threshold_score=item.cost_threshold_score,
        evidence_diversity_score=item.evidence_diversity_score,
        adjudication_path_clarity_score=item.adjudication_path_clarity_score,
        research_readiness_score=readiness_score,
        gate_status=status,
        queue_next_step=_NEXT_STEP_BY_STATUS[status],
        reason_codes=reason_codes,
        hard_safety_flags=_HARD_SAFETY_FLAGS,
    )


def _research_readiness_score(
    item: CandidateDecisionResearchReadinessInput,
    config: CandidateDecisionResearchReadinessGateConfig,
) -> Decimal:
    return _clamp_ratio(
        item.event_specificity_score * config.event_specificity_weight
        + item.evidence_traceability_score * config.evidence_traceability_weight
        + item.cost_threshold_score * config.cost_threshold_weight
        + item.evidence_diversity_score * config.evidence_diversity_weight
        + item.adjudication_path_clarity_score * config.adjudication_path_clarity_weight,
    )


def _row_reason_codes(
    item: CandidateDecisionResearchReadinessInput,
    config: CandidateDecisionResearchReadinessGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.event_specificity_score < config.min_watch_event_specificity_score:
        reason_codes.append("event_specificity_block")
    if item.evidence_traceability_score < config.min_watch_evidence_traceability_score:
        reason_codes.append("evidence_traceability_block")
    if item.cost_threshold_score < config.min_watch_cost_threshold_score:
        reason_codes.append("cost_threshold_block")
    if item.evidence_diversity_score < config.min_watch_evidence_diversity_score:
        reason_codes.append("evidence_diversity_block")
    if (
        item.adjudication_path_clarity_score
        < config.min_watch_adjudication_path_clarity_score
    ):
        reason_codes.append("adjudication_path_clarity_block")
    if not any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        if item.event_specificity_score < config.min_pass_event_specificity_score:
            reason_codes.append("event_specificity_watch")
        if item.evidence_traceability_score < config.min_pass_evidence_traceability_score:
            reason_codes.append("evidence_traceability_watch")
        if item.cost_threshold_score < config.min_pass_cost_threshold_score:
            reason_codes.append("cost_threshold_watch")
        if item.evidence_diversity_score < config.min_pass_evidence_diversity_score:
            reason_codes.append("evidence_diversity_watch")
        if (
            item.adjudication_path_clarity_score
            < config.min_pass_adjudication_path_clarity_score
        ):
            reason_codes.append("adjudication_path_clarity_watch")
    return tuple(reason_codes or ("readiness_gate_pass",))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("readiness_gate_pass",):
        return "pass"
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    return "watch"


def _report_status(rows: tuple[CandidateDecisionResearchReadinessGateRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.gate_status == "block" for row in rows):
        return "block"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[CandidateDecisionResearchReadinessGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_input",)
    reason_codes: list[str] = []
    for code in _REASON_CODE_SEQUENCE:
        if any(code in row.reason_codes for row in rows):
            reason_codes.append(code)
    return tuple(reason_codes)


def _status_count(
    rows: tuple[CandidateDecisionResearchReadinessGateRow, ...],
    status: str,
) -> int:
    return len(tuple(row for row in rows if row.gate_status == status))


def _validate_config(config: CandidateDecisionResearchReadinessGateConfig) -> None:
    threshold_pairs = (
        ("event_specificity", "min_watch_event_specificity_score", "min_pass_event_specificity_score"),
        (
            "evidence_traceability",
            "min_watch_evidence_traceability_score",
            "min_pass_evidence_traceability_score",
        ),
        ("cost_threshold", "min_watch_cost_threshold_score", "min_pass_cost_threshold_score"),
        (
            "evidence_diversity",
            "min_watch_evidence_diversity_score",
            "min_pass_evidence_diversity_score",
        ),
        (
            "adjudication_path_clarity",
            "min_watch_adjudication_path_clarity_score",
            "min_pass_adjudication_path_clarity_score",
        ),
    )
    for label, watch_field, pass_field in threshold_pairs:
        if getattr(config, watch_field) > getattr(config, pass_field):
            raise ValueError(f"{label} watch threshold must not exceed pass threshold")
    weight_total = (
        config.event_specificity_weight
        + config.evidence_traceability_weight
        + config.cost_threshold_weight
        + config.evidence_diversity_weight
        + config.adjudication_path_clarity_weight
    )
    if _quantize(weight_total) != _ONE:
        raise ValueError("readiness weights must sum to 1.000000")


def _validate_row_consistency(row: CandidateDecisionResearchReadinessGateRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.gate_status != expected_status:
        raise ValueError("gate_status must match reason_codes")


def _validate_report_consistency(
    report: CandidateDecisionResearchReadinessGateReport,
) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.pass_ratio != _optional_ratio(_status_count(report.rows, "pass"), len(report.rows)):
        raise ValueError("pass_ratio must match rows")
    if report.watch_ratio != _optional_ratio(
        _status_count(report.rows, "watch"),
        len(report.rows),
    ):
        raise ValueError("watch_ratio must match rows")
    if report.block_ratio != _optional_ratio(
        _status_count(report.rows, "block"),
        len(report.rows),
    ):
        raise ValueError("block_ratio must match rows")
    if report.average_research_readiness_score != _average_ratio(
        tuple(row.research_readiness_score for row in report.rows),
    ):
        raise ValueError("average_research_readiness_score must match rows")
    if report.gate_status != _report_status(report.rows):
        raise ValueError("gate_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.queue_next_step != _NEXT_STEP_BY_STATUS[report.gate_status]:
        raise ValueError("queue_next_step must match gate_status")
    if report.hard_safety_flags != _HARD_SAFETY_FLAGS:
        raise ValueError("hard_safety_flags must match paper-only research scope")


def _normalize_inputs(
    inputs: Sequence[CandidateDecisionResearchReadinessInput],
) -> tuple[CandidateDecisionResearchReadinessInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not CandidateDecisionResearchReadinessInput:
            raise ValueError("inputs items must be CandidateDecisionResearchReadinessInput")
        _require_hard_flags("input", item)
    item_keys = tuple(item.queue_item_key for item in normalized)
    if len(set(item_keys)) != len(item_keys):
        raise ValueError("queue_item_key values must be unique")
    return normalized


def _normalize_rows(
    rows: tuple[CandidateDecisionResearchReadinessGateRow, ...],
) -> tuple[CandidateDecisionResearchReadinessGateRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not CandidateDecisionResearchReadinessGateRow:
            raise ValueError("rows items must be CandidateDecisionResearchReadinessGateRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic readiness gate ordering")
    item_keys = tuple(row.queue_item_key for row in normalized)
    if len(set(item_keys)) != len(item_keys):
        raise ValueError("row queue_item_key values must be unique")
    return normalized


def _normalize_public_payload(
    public_payload: Sequence[CandidateDecisionResearchReadinessPublicPayloadItem],
) -> tuple[CandidateDecisionResearchReadinessPublicPayloadItem, ...]:
    if type(public_payload) not in (list, tuple):
        raise ValueError("public_payload must be a list or tuple")
    normalized = tuple(public_payload)
    for item in normalized:
        if type(item) is not CandidateDecisionResearchReadinessPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "CandidateDecisionResearchReadinessPublicPayloadItem",
            )
        _require_hard_flags("public payload item", item)
    keys = tuple(item.key for item in normalized)
    if keys != tuple(sorted(keys)):
        raise ValueError("public_payload must be sorted by key")
    if len(set(keys)) != len(keys):
        raise ValueError("public_payload keys must be unique")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known reason codes")
    expected_order = tuple(code for code in _REASON_CODE_SEQUENCE if code in normalized)
    if normalized != expected_order:
        raise ValueError("reason_codes must use canonical ordering")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _normalize_hard_safety_flags(flags: tuple[str, ...]) -> tuple[str, ...]:
    if type(flags) not in (list, tuple):
        raise ValueError("hard_safety_flags must be a list or tuple")
    normalized = tuple(flags)
    if normalized != _HARD_SAFETY_FLAGS:
        raise ValueError("hard_safety_flags must match paper-only research scope")
    return normalized


def _row_sort_key(row: CandidateDecisionResearchReadinessGateRow) -> tuple[int, str]:
    status_weight = {"block": 0, "watch": 1, "pass": 2}
    return (status_weight[row.gate_status], row.queue_item_key)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical public text")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")
    return value


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _optional_ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return _quantize(Decimal(numerator) / Decimal(denominator))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(sum(values, _ZERO) / _decimal_count(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _report_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    gate_status: str,
    queue_next_step: str,
    item_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    pass_ratio: Decimal | None,
    watch_ratio: Decimal | None,
    block_ratio: Decimal | None,
    average_research_readiness_score: Decimal,
    reason_codes: tuple[str, ...],
    rows: tuple[CandidateDecisionResearchReadinessGateRow, ...],
    public_payload: tuple[CandidateDecisionResearchReadinessPublicPayloadItem, ...],
    hard_safety_flags: tuple[str, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, object]:
    return {
        "generated_at": _json_ready(generated_at),
        "config_version": config_version,
        "gate_status": gate_status,
        "queue_next_step": queue_next_step,
        "item_count": _json_ready(item_count),
        "pass_count": _json_ready(pass_count),
        "watch_count": _json_ready(watch_count),
        "block_count": _json_ready(block_count),
        "pass_ratio": _json_ready(pass_ratio),
        "watch_ratio": _json_ready(watch_ratio),
        "block_ratio": _json_ready(block_ratio),
        "average_research_readiness_score": _json_ready(
            average_research_readiness_score,
        ),
        "reason_codes": list(reason_codes),
        "rows": [_row_payload(row) for row in rows],
        "public_payload": [_public_payload_item_payload(item) for item in public_payload],
        "hard_safety_flags": list(hard_safety_flags),
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _row_payload(row: CandidateDecisionResearchReadinessGateRow) -> dict[str, object]:
    return {
        "queue_item_key": row.queue_item_key,
        "event_specificity_score": _json_ready(row.event_specificity_score),
        "evidence_traceability_score": _json_ready(row.evidence_traceability_score),
        "cost_threshold_score": _json_ready(row.cost_threshold_score),
        "evidence_diversity_score": _json_ready(row.evidence_diversity_score),
        "adjudication_path_clarity_score": _json_ready(
            row.adjudication_path_clarity_score,
        ),
        "research_readiness_score": _json_ready(row.research_readiness_score),
        "gate_status": row.gate_status,
        "queue_next_step": row.queue_next_step,
        "reason_codes": list(row.reason_codes),
        "hard_safety_flags": list(row.hard_safety_flags),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _public_payload_item_payload(
    item: CandidateDecisionResearchReadinessPublicPayloadItem,
) -> dict[str, object]:
    return {
        "key": item.key,
        "value": item.value,
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _report_payload(
    report: CandidateDecisionResearchReadinessGateReport,
) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        gate_status=report.gate_status,
        queue_next_step=report.queue_next_step,
        item_count=report.item_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        pass_ratio=report.pass_ratio,
        watch_ratio=report.watch_ratio,
        block_ratio=report.block_ratio,
        average_research_readiness_score=report.average_research_readiness_score,
        reason_codes=report.reason_codes,
        rows=report.rows,
        public_payload=report.public_payload,
        hard_safety_flags=report.hard_safety_flags,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_digest(report: CandidateDecisionResearchReadinessGateReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "gate_status": report.gate_status,
            "queue_next_step": report.queue_next_step,
            "item_count": report.item_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "pass_ratio": report.pass_ratio,
            "watch_ratio": report.watch_ratio,
            "block_ratio": report.block_ratio,
            "average_research_readiness_score": report.average_research_readiness_score,
            "reason_codes": report.reason_codes,
            "rows": report.rows,
            "public_payload": report.public_payload,
            "hard_safety_flags": report.hard_safety_flags,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _report_payload_without_digest(
        generated_at=_require_mapping_value(values, "generated_at", datetime),
        config_version=_require_mapping_value(values, "config_version", str),
        gate_status=_require_mapping_value(values, "gate_status", str),
        queue_next_step=_require_mapping_value(values, "queue_next_step", str),
        item_count=_require_mapping_value(values, "item_count", Decimal),
        pass_count=_require_mapping_value(values, "pass_count", Decimal),
        watch_count=_require_mapping_value(values, "watch_count", Decimal),
        block_count=_require_mapping_value(values, "block_count", Decimal),
        pass_ratio=_require_optional_mapping_value(values, "pass_ratio", Decimal),
        watch_ratio=_require_optional_mapping_value(values, "watch_ratio", Decimal),
        block_ratio=_require_optional_mapping_value(values, "block_ratio", Decimal),
        average_research_readiness_score=_require_mapping_value(
            values,
            "average_research_readiness_score",
            Decimal,
        ),
        reason_codes=_require_mapping_value(values, "reason_codes", tuple),
        rows=_require_mapping_value(values, "rows", tuple),
        public_payload=_require_mapping_value(values, "public_payload", tuple),
        hard_safety_flags=_require_mapping_value(values, "hard_safety_flags", tuple),
        paper_only=_require_mapping_value(values, "paper_only", bool),
        report_only=_require_mapping_value(values, "report_only", bool),
        readonly=_require_mapping_value(values, "readonly", bool),
    )
    return _digest_payload(payload)


def _require_mapping_value(
    values: dict[str, object],
    key: str,
    expected_type: type,
) -> Any:
    value = values[key]
    if type(value) is not expected_type:
        raise ValueError(f"{key} must be {expected_type.__name__}")
    return value


def _require_optional_mapping_value(
    values: dict[str, object],
    key: str,
    expected_type: type,
) -> Any:
    value = values[key]
    if value is None:
        return None
    if type(value) is not expected_type:
        raise ValueError(f"{key} must be {expected_type.__name__} or None")
    return value


def _validate_public_payload_digest(payload: dict[str, object]) -> None:
    _require_payload_status(payload.get("gate_status"))
    digest = payload.get(_DERIVED_VALIDATION_DIGEST_FIELD)
    _require_digest(_DERIVED_VALIDATION_DIGEST_FIELD, digest)
    without_digest = dict(payload)
    without_digest.pop(_DERIVED_VALIDATION_DIGEST_FIELD, None)
    if digest != _digest_payload(without_digest):
        raise ValueError("derived_validation_digest mismatch")


def _require_payload_status(value: object) -> None:
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError("gate_status must be pass, watch, or block")


def _digest_payload(payload: dict[str, object]) -> str:
    _reject_unsafe_public_payload("digest payload", payload, allow_json_containers=True)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = json.loads(json.dumps(value, sort_keys=True, separators=(",", ":")))
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {key: _json_ready(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("value is not JSON-ready")


def _reject_unsafe_public_payload(
    label: str,
    payload: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(payload):
        if not allow_json_containers and not getattr(payload, "__dataclass_params__").frozen:
            raise ValueError(f"{current_path} must be frozen")
        for field in fields(payload):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(payload, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(payload) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in payload.items():
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
    if isinstance(payload, (list, tuple)):
        if type(payload) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(payload):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(payload) is str:
        _reject_unsafe_public_string(current_path, payload)
        return
    if (
        payload is None
        or type(payload) is bool
        or type(payload) is Decimal
        or type(payload) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{path} contains unsafe public detail")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    normalized = "".join(character for character in lowered if character.isalnum())
    for term in _UNSAFE_PUBLIC_FRAGMENTS:
        normalized_term = "".join(character for character in term if character.isalnum())
        if term in lowered or (normalized_term and normalized_term in normalized):
            return True
    return False


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_RESEARCH_READINESS_GATE_CONFIG_VERSION",
    "CandidateDecisionResearchReadinessGateConfig",
    "CandidateDecisionResearchReadinessGateReport",
    "CandidateDecisionResearchReadinessGateRow",
    "CandidateDecisionResearchReadinessInput",
    "CandidateDecisionResearchReadinessPublicPayloadItem",
    "build_candidate_decision_research_readiness_gate",
    "candidate_decision_research_readiness_gate_payload",
)
