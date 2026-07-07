"""Pure report gate between automated research screening and human confirmation."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_CONFIG_VERSION = "research-human-approval-gate-report-v0"
GATE_STATUSES = ("pass", "watch", "block")
CHECK_STATUSES = GATE_STATUSES
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")


def _chars(*values: int) -> str:
    return "".join(chr(value) for value in values)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        _chars(97, 117, 116, 104),
        _chars(98, 117, 121),
        _chars(105, 110, 118, 101, 115, 116),
        _chars(111, 114, 100, 101, 114),
        _chars(112, 111, 115, 105, 116, 105, 111, 110),
        _chars(114, 101, 99, 111, 109, 109, 101, 110, 100),
        _chars(115, 101, 108, 108),
        _chars(116, 114, 97, 100, 101),
        _chars(119, 97, 108, 108, 101, 116),
    ),
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = UNSAFE_PUBLIC_TEXT_FRAGMENTS


@dataclass(frozen=True)
class ResearchHumanApprovalGateConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_evidence_count: Decimal = Decimal("2")
    min_primary_source_count: Decimal = Decimal("1")
    pass_evidence_quality_score: Decimal = Decimal("0.700000")
    watch_evidence_quality_score: Decimal = Decimal("0.500000")
    watch_cost_amount: Decimal = Decimal("0.030000")
    block_cost_amount: Decimal = Decimal("0.100000")
    watch_cost_uncertainty_score: Decimal = Decimal("0.400000")
    block_cost_uncertainty_score: Decimal = Decimal("0.750000")
    pass_settlement_clarity_score: Decimal = Decimal("0.700000")
    block_settlement_clarity_score: Decimal = Decimal("0.400000")
    pass_settlement_window_hours: Decimal = Decimal("168")
    block_settlement_window_hours: Decimal = Decimal("720")
    pass_team_agreement_ratio: Decimal = Decimal("0.666667")
    block_team_agreement_ratio: Decimal = Decimal("0.500000")
    block_team_disagreement_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("min_evidence_count", "min_primary_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_evidence_quality_score",
            "watch_evidence_quality_score",
            "watch_cost_uncertainty_score",
            "block_cost_uncertainty_score",
            "pass_settlement_clarity_score",
            "block_settlement_clarity_score",
            "pass_team_agreement_ratio",
            "block_team_agreement_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_cost_amount",
            "block_cost_amount",
            "pass_settlement_window_hours",
            "block_settlement_window_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "block_team_disagreement_count",
            _require_nonnegative_whole_decimal(
                "block_team_disagreement_count",
                self.block_team_disagreement_count,
            ),
        )
        if self.pass_evidence_quality_score <= self.watch_evidence_quality_score:
            raise ValueError(
                "pass_evidence_quality_score must be greater than watch_evidence_quality_score",
            )
        if self.block_cost_amount <= self.watch_cost_amount:
            raise ValueError("block_cost_amount must be greater than watch_cost_amount")
        if self.block_cost_uncertainty_score <= self.watch_cost_uncertainty_score:
            raise ValueError(
                "block_cost_uncertainty_score must be greater than watch_cost_uncertainty_score",
            )
        if self.pass_settlement_clarity_score <= self.block_settlement_clarity_score:
            raise ValueError(
                "pass_settlement_clarity_score must be greater than "
                "block_settlement_clarity_score",
            )
        if self.block_settlement_window_hours <= self.pass_settlement_window_hours:
            raise ValueError(
                "block_settlement_window_hours must be greater than "
                "pass_settlement_window_hours",
            )
        if self.pass_team_agreement_ratio <= self.block_team_agreement_ratio:
            raise ValueError(
                "pass_team_agreement_ratio must be greater than block_team_agreement_ratio",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchHumanApprovalGateInput:
    candidate_id: str
    evidence_count: Decimal
    primary_source_count: Decimal
    evidence_quality_score: Decimal
    estimated_cost_amount: Decimal
    cost_uncertainty_score: Decimal
    settlement_clarity_score: Decimal
    settlement_window_hours: Decimal
    team_agreement_ratio: Decimal
    team_disagreement_count: Decimal
    safety_boundary_flags: tuple[str, ...]
    public_notes: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in ("evidence_count", "primary_source_count", "team_disagreement_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_quality_score",
            "cost_uncertainty_score",
            "settlement_clarity_score",
            "team_agreement_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("estimated_cost_amount", "settlement_window_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "safety_boundary_flags",
            _normalize_string_tuple(
                "safety_boundary_flags",
                self.safety_boundary_flags,
                allow_empty=True,
            ),
        )
        _require_canonical_string("public_notes", self.public_notes)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("ResearchHumanApprovalGateInput", self)


@dataclass(frozen=True)
class ResearchHumanApprovalGateRow:
    candidate_id: str
    evidence_count: Decimal
    primary_source_count: Decimal
    evidence_quality_score: Decimal
    evidence_status: str
    estimated_cost_amount: Decimal
    cost_uncertainty_score: Decimal
    cost_status: str
    settlement_clarity_score: Decimal
    settlement_window_hours: Decimal
    settlement_status: str
    team_agreement_ratio: Decimal
    team_disagreement_count: Decimal
    consensus_status: str
    safety_boundary_flag_count: Decimal
    safety_status: str
    gate_status: str
    public_notes: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "evidence_count",
            "primary_source_count",
            "team_disagreement_count",
            "safety_boundary_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_quality_score",
            "cost_uncertainty_score",
            "settlement_clarity_score",
            "team_agreement_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("estimated_cost_amount", "settlement_window_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_status",
            "cost_status",
            "settlement_status",
            "consensus_status",
            "safety_status",
            "gate_status",
        ):
            _require_status(field_name, getattr(self, field_name))
        _require_canonical_string("public_notes", self.public_notes)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("ResearchHumanApprovalGateRow", self)


@dataclass(frozen=True)
class ResearchHumanApprovalGateReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_whole_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchHumanApprovalGateReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    gate_status: str
    rows: tuple[ResearchHumanApprovalGateRow, ...]
    reason_code_counts: tuple[ResearchHumanApprovalGateReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("gate_status", self.gate_status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("ResearchHumanApprovalGateReport", self)


def build_research_human_approval_gate_report(
    candidates: Any,
    *,
    config: ResearchHumanApprovalGateConfig,
    generated_at: datetime,
) -> ResearchHumanApprovalGateReport:
    if type(config) is not ResearchHumanApprovalGateConfig:
        raise ValueError("config must be a ResearchHumanApprovalGateConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_inputs(candidates)
    rows = tuple(
        _row_from_input(candidate, config=config)
        for candidate in sorted(normalized_candidates, key=lambda item: item.candidate_id)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchHumanApprovalGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        gate_status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_human_approval_gate_payload(value: object) -> dict[str, Any]:
    if isinstance(
        value,
        (
            ResearchHumanApprovalGateInput,
            ResearchHumanApprovalGateReasonCodeCount,
            ResearchHumanApprovalGateReport,
            ResearchHumanApprovalGateRow,
        ),
    ):
        _require_hard_flags("payload", value)
    elif not isinstance(value, dict):
        raise ValueError("value must be a human approval gate report, row, input, or JSON object")
    _reject_unsafe_public_payload("human approval gate payload", value)
    payload = _json_ready_decimal_strings(value)
    if not isinstance(payload, dict):
        raise ValueError("human approval gate payload must be a JSON object")
    _validate_payload_flags(payload, "payload", require_current_flags=True)
    _reject_unsafe_public_payload("human approval gate payload", payload)
    return payload


def _row_from_input(
    candidate: ResearchHumanApprovalGateInput,
    *,
    config: ResearchHumanApprovalGateConfig,
) -> ResearchHumanApprovalGateRow:
    evidence_status = _evidence_status(candidate, config)
    cost_status = _cost_status(candidate, config)
    settlement_status = _settlement_status(candidate, config)
    consensus_status = _consensus_status(candidate, config)
    safety_status = "block" if candidate.safety_boundary_flags else "pass"
    gate_status = _row_gate_status(
        (evidence_status, cost_status, settlement_status, consensus_status, safety_status),
    )
    return ResearchHumanApprovalGateRow(
        candidate_id=candidate.candidate_id,
        evidence_count=candidate.evidence_count,
        primary_source_count=candidate.primary_source_count,
        evidence_quality_score=candidate.evidence_quality_score,
        evidence_status=evidence_status,
        estimated_cost_amount=candidate.estimated_cost_amount,
        cost_uncertainty_score=candidate.cost_uncertainty_score,
        cost_status=cost_status,
        settlement_clarity_score=candidate.settlement_clarity_score,
        settlement_window_hours=candidate.settlement_window_hours,
        settlement_status=settlement_status,
        team_agreement_ratio=candidate.team_agreement_ratio,
        team_disagreement_count=candidate.team_disagreement_count,
        consensus_status=consensus_status,
        safety_boundary_flag_count=_decimal_count(len(candidate.safety_boundary_flags)),
        safety_status=safety_status,
        gate_status=gate_status,
        public_notes=candidate.public_notes,
        reason_codes=_row_reason_codes(
            candidate,
            evidence_status=evidence_status,
            cost_status=cost_status,
            settlement_status=settlement_status,
            consensus_status=consensus_status,
            safety_status=safety_status,
            gate_status=gate_status,
            config=config,
        ),
    )


def _evidence_status(
    candidate: ResearchHumanApprovalGateInput,
    config: ResearchHumanApprovalGateConfig,
) -> str:
    if (
        candidate.evidence_count == ZERO
        or candidate.primary_source_count == ZERO
        or candidate.evidence_quality_score < config.watch_evidence_quality_score
    ):
        return "block"
    if (
        candidate.evidence_count < config.min_evidence_count
        or candidate.primary_source_count < config.min_primary_source_count
        or candidate.evidence_quality_score < config.pass_evidence_quality_score
    ):
        return "watch"
    return "pass"


def _cost_status(
    candidate: ResearchHumanApprovalGateInput,
    config: ResearchHumanApprovalGateConfig,
) -> str:
    if (
        candidate.estimated_cost_amount > config.block_cost_amount
        or candidate.cost_uncertainty_score > config.block_cost_uncertainty_score
    ):
        return "block"
    if (
        candidate.estimated_cost_amount > config.watch_cost_amount
        or candidate.cost_uncertainty_score > config.watch_cost_uncertainty_score
    ):
        return "watch"
    return "pass"


def _settlement_status(
    candidate: ResearchHumanApprovalGateInput,
    config: ResearchHumanApprovalGateConfig,
) -> str:
    if (
        candidate.settlement_clarity_score < config.block_settlement_clarity_score
        or candidate.settlement_window_hours > config.block_settlement_window_hours
    ):
        return "block"
    if (
        candidate.settlement_clarity_score < config.pass_settlement_clarity_score
        or candidate.settlement_window_hours > config.pass_settlement_window_hours
    ):
        return "watch"
    return "pass"


def _consensus_status(
    candidate: ResearchHumanApprovalGateInput,
    config: ResearchHumanApprovalGateConfig,
) -> str:
    if (
        candidate.team_agreement_ratio < config.block_team_agreement_ratio
        or candidate.team_disagreement_count > config.block_team_disagreement_count
    ):
        return "block"
    if candidate.team_agreement_ratio < config.pass_team_agreement_ratio:
        return "watch"
    if candidate.team_disagreement_count > ZERO:
        return "watch"
    return "pass"


def _row_gate_status(statuses: tuple[str, ...]) -> str:
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _row_reason_codes(
    candidate: ResearchHumanApprovalGateInput,
    *,
    evidence_status: str,
    cost_status: str,
    settlement_status: str,
    consensus_status: str,
    safety_status: str,
    gate_status: str,
    config: ResearchHumanApprovalGateConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"human_approval_gate_{gate_status}"}
    reason_codes.add(f"evidence_{evidence_status}")
    reason_codes.add(f"cost_{cost_status}")
    reason_codes.add(f"settlement_{settlement_status}")
    reason_codes.add(f"consensus_{consensus_status}")
    reason_codes.add(f"safety_boundary_{safety_status}")
    if candidate.evidence_count < config.min_evidence_count:
        reason_codes.add("evidence_count_below_minimum")
    if candidate.primary_source_count < config.min_primary_source_count:
        reason_codes.add("primary_source_count_below_minimum")
    if candidate.evidence_quality_score < config.pass_evidence_quality_score:
        reason_codes.add("evidence_quality_below_pass_level")
    if candidate.estimated_cost_amount > config.watch_cost_amount:
        reason_codes.add("cost_amount_above_watch_level")
    if candidate.cost_uncertainty_score > config.watch_cost_uncertainty_score:
        reason_codes.add("cost_uncertainty_above_watch_level")
    if candidate.settlement_clarity_score < config.pass_settlement_clarity_score:
        reason_codes.add("settlement_clarity_below_pass_level")
    if candidate.settlement_window_hours > config.pass_settlement_window_hours:
        reason_codes.add("settlement_window_above_watch_level")
    if candidate.team_agreement_ratio < config.pass_team_agreement_ratio:
        reason_codes.add("team_agreement_below_pass_level")
    if candidate.team_disagreement_count > ZERO:
        reason_codes.add("team_disagreement_present")
    if candidate.safety_boundary_flags:
        reason_codes.add("safety_boundary_flag_present")
    for reason_code in candidate.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _normalize_inputs(candidates: Any) -> tuple[ResearchHumanApprovalGateInput, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        values = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchHumanApprovalGateInput:
    if type(value) is ResearchHumanApprovalGateInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchHumanApprovalGateInput(
        candidate_id=_field_value(value, "candidate_id"),
        evidence_count=_field_value(value, "evidence_count"),
        primary_source_count=_field_value(value, "primary_source_count"),
        evidence_quality_score=_field_value(value, "evidence_quality_score"),
        estimated_cost_amount=_field_value(value, "estimated_cost_amount"),
        cost_uncertainty_score=_field_value(value, "cost_uncertainty_score"),
        settlement_clarity_score=_field_value(value, "settlement_clarity_score"),
        settlement_window_hours=_field_value(value, "settlement_window_hours"),
        team_agreement_ratio=_field_value(value, "team_agreement_ratio"),
        team_disagreement_count=_field_value(value, "team_disagreement_count"),
        safety_boundary_flags=_field_value(value, "safety_boundary_flags"),
        public_notes=_field_value(value, "public_notes"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _normalize_rows(
    rows: tuple[ResearchHumanApprovalGateRow, ...],
) -> tuple[ResearchHumanApprovalGateRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchHumanApprovalGateRow:
            raise ValueError("rows must contain ResearchHumanApprovalGateRow values")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=lambda row: row.candidate_id)):
        raise ValueError("rows must be sorted by candidate_id")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchHumanApprovalGateReasonCodeCount, ...],
) -> tuple[ResearchHumanApprovalGateReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchHumanApprovalGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchHumanApprovalGateReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    if counts != tuple(sorted(counts, key=lambda count: count.reason_code)):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _summary_reason_codes(rows: tuple[ResearchHumanApprovalGateRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("no_human_approval_gate_candidates",)
    if all(row.gate_status == "pass" for row in rows):
        return ("human_approval_gate_pass",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_human_approval_gate_candidates",):
        return "block"
    if "human_approval_gate_block" in reason_codes:
        return "block"
    if "human_approval_gate_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchHumanApprovalGateRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchHumanApprovalGateReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchHumanApprovalGateReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchHumanApprovalGateReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(rows: tuple[ResearchHumanApprovalGateRow, ...], status: str) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.gate_status == status))


def _validate_row_consistency(row: ResearchHumanApprovalGateRow) -> None:
    expected_status = _row_gate_status(
        (
            row.evidence_status,
            row.cost_status,
            row.settlement_status,
            row.consensus_status,
            row.safety_status,
        ),
    )
    if row.gate_status != expected_status:
        raise ValueError("gate_status must match check statuses")
    if row.safety_status == "pass" and row.safety_boundary_flag_count != ZERO:
        raise ValueError("safety_status must match safety_boundary_flag_count")
    if row.safety_status == "block" and row.safety_boundary_flag_count == ZERO:
        raise ValueError("safety_status must match safety_boundary_flag_count")
    if f"human_approval_gate_{row.gate_status}" not in row.reason_codes:
        raise ValueError("reason_codes must include gate_status")


def _validate_report_consistency(report: ResearchHumanApprovalGateReport) -> None:
    if report.candidate_count != _decimal_count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.gate_status != _summary_status(report.reason_codes):
        raise ValueError("gate_status must match reason_codes")


def _field_value(value: object, field_name: str, *, default: object = None) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not None:
        return default
    raise ValueError(f"{field_name} is required")


def _json_ready_decimal_strings(value: Any, path: str = "") -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _json_ready_decimal_strings(nested_value, key if not path else f"{path}.{key}")
            for key, nested_value in asdict(value).items()
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or 'value'} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or 'value'} must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or 'value'} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or 'value'} must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is float:
        raise ValueError(f"{path or 'value'} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or 'value'} must use Decimal-derived string values")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            ready[key] = _json_ready_decimal_strings(item, item_path)
        return ready
    if isinstance(value, (list, tuple)):
        return [
            _json_ready_decimal_strings(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{path or 'value'} is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is str:
        if _has_unsafe_public_text(value):
            raise ValueError(f"{path or label} has unsafe public text")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_key(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _has_unsafe_public_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS)


def _has_unsafe_public_key(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS)


def _validate_payload_flags(
    value: object,
    field_path: str,
    *,
    require_current_flags: bool = False,
) -> None:
    if isinstance(value, dict):
        for flag_name in ("paper_only", "report_only", "readonly"):
            if require_current_flags and flag_name not in value:
                raise ValueError(f"{field_path} {flag_name} must be True")
            if flag_name in value and value[flag_name] is not True:
                raise ValueError(f"{field_path} {flag_name} must be True")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _validate_payload_flags(item, f"{field_path} {key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_flags(item, f"{field_path} {index}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized.quantize(RATIO_QUANTUM)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if _has_unsafe_public_text(value):
        raise ValueError(f"{field_name} has unsafe public text")


def _normalize_string_tuple(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string(field_name, value)
        if value not in normalized:
            normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    return tuple(sorted(_normalize_string_tuple(field_name, values, allow_empty=allow_empty)))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "ResearchHumanApprovalGateConfig",
    "ResearchHumanApprovalGateInput",
    "ResearchHumanApprovalGateReasonCodeCount",
    "ResearchHumanApprovalGateReport",
    "ResearchHumanApprovalGateRow",
    "build_research_human_approval_gate_report",
    "research_human_approval_gate_payload",
)
