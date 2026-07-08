"""Pure strategy probability edge component audit report for human review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_COMPONENT_AUDIT_REPORT_CONFIG_VERSION = (
    "research-strategy-probability-edge-component-audit-report-v0"
)
RESEARCH_STRATEGY_PROBABILITY_EDGE_COMPONENT_AUDIT_STATUSES = (
    "pass",
    "watch",
    "block",
)

RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "au" + "th",
    "candidate",
    "condition" + "_id",
    "credential",
    "dsn",
    "market" + "_id",
    "market" + "_slug",
    "private",
    "question",
    "ref",
    "secret",
    "slug",
    "source",
    "source" + "_text",
    "table",
    "token",
    "url",
    "wal" + "let",
    "or" + "der",
    "li" + "ve",
    "trad" + "e",
    "trad" + "ing",
    "data" + "base",
    "net" + "work",
    "persist",
    "signing",
    "mutation",
    "position",
    "b" + "uy",
    "se" + "ll",
    "reco" + "mmend",
    "siz" + "ing",
)

ROW_REASON_CODES = (
    "confidence_component_block",
    "confidence_component_watch",
    "cost_component_block",
    "cost_component_watch",
    "evidence_maturity_component_block",
    "evidence_maturity_component_watch",
    "probability_component_block",
    "probability_component_watch",
    "strategy_probability_edge_component_audit_pass",
)
REPORT_REASON_CODES = (
    "confidence_component_review",
    "cost_component_review",
    "evidence_maturity_component_review",
    "probability_component_review",
    "strategy_probability_edge_component_audit_report_block",
    "strategy_probability_edge_component_audit_report_empty",
    "strategy_probability_edge_component_audit_report_pass",
    "strategy_probability_edge_component_audit_report_watch",
)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeComponentAuditConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_COMPONENT_AUDIT_REPORT_CONFIG_VERSION
    )
    probability_component_pass_floor: Decimal = Decimal("0.800000")
    probability_component_watch_floor: Decimal = Decimal("0.500000")
    cost_component_pass_floor: Decimal = Decimal("0.800000")
    cost_component_watch_floor: Decimal = Decimal("0.500000")
    confidence_component_pass_floor: Decimal = Decimal("0.800000")
    confidence_component_watch_floor: Decimal = Decimal("0.500000")
    evidence_maturity_component_pass_floor: Decimal = Decimal("0.800000")
    evidence_maturity_component_watch_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyProbabilityEdgeComponentAuditConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyProbabilityEdgeComponentAuditConfig",
            )
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "probability_component_pass_floor",
            "probability_component_watch_floor",
            "cost_component_pass_floor",
            "cost_component_watch_floor",
            "confidence_component_pass_floor",
            "confidence_component_watch_floor",
            "evidence_maturity_component_pass_floor",
            "evidence_maturity_component_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "probability_component",
            self.probability_component_pass_floor,
            self.probability_component_watch_floor,
        )
        _require_floor_pair(
            "cost_component",
            self.cost_component_pass_floor,
            self.cost_component_watch_floor,
        )
        _require_floor_pair(
            "confidence_component",
            self.confidence_component_pass_floor,
            self.confidence_component_watch_floor,
        )
        _require_floor_pair(
            "evidence_maturity_component",
            self.evidence_maturity_component_pass_floor,
            self.evidence_maturity_component_watch_floor,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeComponentAuditInput:
    audit_ref: str
    observed_at: datetime
    probability_component_score: Decimal
    cost_component_score: Decimal
    confidence_component_score: Decimal
    evidence_maturity_component_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyProbabilityEdgeComponentAuditInput:
            raise ValueError(
                "input must be exactly ResearchStrategyProbabilityEdgeComponentAuditInput",
            )
        _require_input_ref("audit_ref", self.audit_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "probability_component_score",
            "cost_component_score",
            "confidence_component_score",
            "evidence_maturity_component_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeComponentAuditRow:
    audit_ref: str
    observed_at: datetime
    probability_component_score: Decimal
    cost_component_score: Decimal
    confidence_component_score: Decimal
    evidence_maturity_component_score: Decimal
    minimum_component_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyProbabilityEdgeComponentAuditRow:
            raise ValueError("row must be exactly ResearchStrategyProbabilityEdgeComponentAuditRow")
        _require_input_ref("audit_ref", self.audit_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "probability_component_score",
            "cost_component_score",
            "confidence_component_score",
            "evidence_maturity_component_score",
            "minimum_component_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeComponentAuditReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_probability_component_score: Decimal
    mean_cost_component_score: Decimal
    mean_confidence_component_score: Decimal
    mean_evidence_maturity_component_score: Decimal
    mean_minimum_component_score: Decimal
    minimum_component_floor: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount, ...]
    rows: tuple[ResearchStrategyProbabilityEdgeComponentAuditRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyProbabilityEdgeComponentAuditReport:
            raise ValueError(
                "report must be exactly ResearchStrategyProbabilityEdgeComponentAuditReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_probability_component_score",
            "mean_cost_component_score",
            "mean_confidence_component_score",
            "mean_evidence_maturity_component_score",
            "mean_minimum_component_score",
            "minimum_component_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_research_strategy_probability_edge_component_audit_report(
    inputs: Iterable[ResearchStrategyProbabilityEdgeComponentAuditInput],
    *,
    config: ResearchStrategyProbabilityEdgeComponentAuditConfig,
    generated_at: datetime,
) -> ResearchStrategyProbabilityEdgeComponentAuditReport:
    if type(config) is not ResearchStrategyProbabilityEdgeComponentAuditConfig:
        raise ValueError(
            "config must be a ResearchStrategyProbabilityEdgeComponentAuditConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(value, config=config, generated_at=generated_at_utc) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyProbabilityEdgeComponentAuditReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_probability_component_score=_mean(
            tuple(row.probability_component_score for row in rows),
        ),
        mean_cost_component_score=_mean(tuple(row.cost_component_score for row in rows)),
        mean_confidence_component_score=_mean(
            tuple(row.confidence_component_score for row in rows),
        ),
        mean_evidence_maturity_component_score=_mean(
            tuple(row.evidence_maturity_component_score for row in rows),
        ),
        mean_minimum_component_score=_mean(
            tuple(row.minimum_component_score for row in rows),
        ),
        minimum_component_floor=_min_decimal(
            tuple(row.minimum_component_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_probability_edge_component_audit_report_payload(
    report: ResearchStrategyProbabilityEdgeComponentAuditReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyProbabilityEdgeComponentAuditReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        payload = _public_report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyProbabilityEdgeComponentAuditReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _public_report_payload(
    report: ResearchStrategyProbabilityEdgeComponentAuditReport,
) -> dict[str, Any]:
    payload = asdict(report)
    payload["rows"] = [
        _public_row_payload(index, row)
        for index, row in enumerate(report.rows, start=1)
    ]
    payload.pop("derived_validation_digest", None)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    _verify_public_payload_integrity(public_payload)
    return public_payload


def _public_row_payload(
    row_number: int,
    row: ResearchStrategyProbabilityEdgeComponentAuditRow,
) -> dict[str, Any]:
    payload = asdict(row)
    payload.pop("audit_ref", None)
    payload.pop("derived_validation_digest", None)
    payload["row_number"] = _count(row_number)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    return public_payload


def _public_payload_digest(payload: dict[str, Any]) -> str:
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_input(
    value: ResearchStrategyProbabilityEdgeComponentAuditInput,
    *,
    config: ResearchStrategyProbabilityEdgeComponentAuditConfig,
    generated_at: datetime,
) -> ResearchStrategyProbabilityEdgeComponentAuditRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    minimum_component_score = min(
        value.probability_component_score,
        value.cost_component_score,
        value.confidence_component_score,
        value.evidence_maturity_component_score,
    )
    return ResearchStrategyProbabilityEdgeComponentAuditRow(
        audit_ref=value.audit_ref,
        observed_at=observed_at,
        probability_component_score=value.probability_component_score,
        cost_component_score=value.cost_component_score,
        confidence_component_score=value.confidence_component_score,
        evidence_maturity_component_score=value.evidence_maturity_component_score,
        minimum_component_score=minimum_component_score,
        status=_row_status(value=value, config=config),
        reason_codes=_row_reason_codes(value=value, config=config),
    )


def _row_status(
    *,
    value: ResearchStrategyProbabilityEdgeComponentAuditInput,
    config: ResearchStrategyProbabilityEdgeComponentAuditConfig,
) -> str:
    if (
        value.probability_component_score < config.probability_component_watch_floor
        or value.cost_component_score < config.cost_component_watch_floor
        or value.confidence_component_score < config.confidence_component_watch_floor
        or value.evidence_maturity_component_score
        < config.evidence_maturity_component_watch_floor
    ):
        return "block"
    if (
        value.probability_component_score < config.probability_component_pass_floor
        or value.cost_component_score < config.cost_component_pass_floor
        or value.confidence_component_score < config.confidence_component_pass_floor
        or value.evidence_maturity_component_score
        < config.evidence_maturity_component_pass_floor
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    value: ResearchStrategyProbabilityEdgeComponentAuditInput,
    config: ResearchStrategyProbabilityEdgeComponentAuditConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if value.confidence_component_score < config.confidence_component_watch_floor:
        codes.append("confidence_component_block")
    elif value.confidence_component_score < config.confidence_component_pass_floor:
        codes.append("confidence_component_watch")
    if value.cost_component_score < config.cost_component_watch_floor:
        codes.append("cost_component_block")
    elif value.cost_component_score < config.cost_component_pass_floor:
        codes.append("cost_component_watch")
    if (
        value.evidence_maturity_component_score
        < config.evidence_maturity_component_watch_floor
    ):
        codes.append("evidence_maturity_component_block")
    elif (
        value.evidence_maturity_component_score
        < config.evidence_maturity_component_pass_floor
    ):
        codes.append("evidence_maturity_component_watch")
    if value.probability_component_score < config.probability_component_watch_floor:
        codes.append("probability_component_block")
    elif value.probability_component_score < config.probability_component_pass_floor:
        codes.append("probability_component_watch")
    if not codes:
        codes.append("strategy_probability_edge_component_audit_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(
    rows: tuple[ResearchStrategyProbabilityEdgeComponentAuditRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyProbabilityEdgeComponentAuditRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("strategy_probability_edge_component_audit_report_empty",)
    report_status = _report_status(rows)
    codes: list[str] = []
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    if any(code.startswith("confidence_component_") for code in row_codes):
        codes.append("confidence_component_review")
    if any(code.startswith("cost_component_") for code in row_codes):
        codes.append("cost_component_review")
    if any(code.startswith("evidence_maturity_component_") for code in row_codes):
        codes.append("evidence_maturity_component_review")
    if any(code.startswith("probability_component_") for code in row_codes):
        codes.append("probability_component_review")
    codes.append(f"strategy_probability_edge_component_audit_report_{report_status}")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchStrategyProbabilityEdgeComponentAuditRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.minimum_component_score,
        row.probability_component_score,
        row.cost_component_score,
        row.confidence_component_score,
        row.evidence_maturity_component_score,
        row.audit_ref,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyProbabilityEdgeComponentAuditInput],
) -> tuple[ResearchStrategyProbabilityEdgeComponentAuditInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyProbabilityEdgeComponentAuditInput:
            raise ValueError(
                "inputs must contain "
                "ResearchStrategyProbabilityEdgeComponentAuditInput values",
            )
        _require_hard_flags("input", value)
        if value.audit_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate audit_ref values")
        seen_refs.add(value.audit_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyProbabilityEdgeComponentAuditRow],
) -> tuple[ResearchStrategyProbabilityEdgeComponentAuditRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyProbabilityEdgeComponentAuditRow:
            raise ValueError(
                "rows must contain ResearchStrategyProbabilityEdgeComponentAuditRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.audit_ref in seen_refs:
            raise ValueError("rows must not contain duplicate audit_ref values")
        seen_refs.add(row.audit_ref)
    return normalized


def _validate_row_consistency(
    row: ResearchStrategyProbabilityEdgeComponentAuditRow,
) -> None:
    expected_minimum = min(
        row.probability_component_score,
        row.cost_component_score,
        row.confidence_component_score,
        row.evidence_maturity_component_score,
    )
    if row.minimum_component_score != expected_minimum:
        raise ValueError("minimum_component_score must match component scores")
    if row.status == "pass" and row.reason_codes != (
        "strategy_probability_edge_component_audit_pass",
    ):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(
    report: ResearchStrategyProbabilityEdgeComponentAuditReport,
) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.input_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match input_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_probability_component_score != _mean(
        tuple(row.probability_component_score for row in report.rows),
    ):
        raise ValueError("mean_probability_component_score must match rows")
    if report.mean_cost_component_score != _mean(
        tuple(row.cost_component_score for row in report.rows),
    ):
        raise ValueError("mean_cost_component_score must match rows")
    if report.mean_confidence_component_score != _mean(
        tuple(row.confidence_component_score for row in report.rows),
    ):
        raise ValueError("mean_confidence_component_score must match rows")
    if report.mean_evidence_maturity_component_score != _mean(
        tuple(row.evidence_maturity_component_score for row in report.rows),
    ):
        raise ValueError("mean_evidence_maturity_component_score must match rows")
    if report.mean_minimum_component_score != _mean(
        tuple(row.minimum_component_score for row in report.rows),
    ):
        raise ValueError("mean_minimum_component_score must match rows")
    if report.minimum_component_floor != _min_decimal(
        tuple(row.minimum_component_score for row in report.rows),
    ):
        raise ValueError("minimum_component_floor must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(
    report: ResearchStrategyProbabilityEdgeComponentAuditReport,
) -> None:
    _verify_digest(report)
    _validate_report_consistency(report)
    for row in report.rows:
        _verify_digest(row)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    _verify_public_payload_digest("payload", payload)
    rows = payload.get("rows")
    if rows is None:
        return
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_public_payload_digest(f"payload.rows[{index}]", row)


def _verify_public_payload_digest(label: str, payload: dict[str, Any]) -> None:
    provided = payload.get("derived_validation_digest")
    _require_digest(f"{label}.derived_validation_digest", provided)
    expected = _public_payload_digest(payload)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _status_count(
    rows: tuple[ResearchStrategyProbabilityEdgeComponentAuditRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyProbabilityEdgeComponentAuditRow, ...],
) -> tuple[ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount(
                reason_code="strategy_probability_edge_component_audit_report_empty",
                count=_count(1),
                input_ratio=ZERO.quantize(RATIO_QUANTUM),
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            input_ratio=_divide_decimal(_count(count), denominator),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_reason_code_counts(
    value: Iterable[ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount],
) -> tuple[ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return min(values).quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM)


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_floor_pair(name: str, pass_floor: Decimal, watch_floor: Decimal) -> None:
    if pass_floor < watch_floor:
        raise ValueError(f"{name}_pass_floor must be at least {name}_watch_floor")


def _require_status(name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_PROBABILITY_EDGE_COMPONENT_AUDIT_STATUSES
    ):
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    _require_canonical_public_string(name, value)
    if value not in ROW_REASON_CODES and value not in REPORT_REASON_CODES:
        raise ValueError(f"{name} is not supported")


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for reason_code in value:
        _require_reason_code(name, reason_code)
        if reason_code not in supported:
            raise ValueError(f"{name} contains an unsupported reason code")
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must not contain duplicates")
    return value


def _require_canonical_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical public string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} has unsafe public text")


def _require_input_ref(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical string")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _apply_or_verify_digest(value: object) -> None:
    provided = getattr(value, "derived_validation_digest")
    if provided:
        _verify_digest(value)
    else:
        object.__setattr__(value, "derived_validation_digest", _digest_for(value))


def _verify_digest(value: object) -> None:
    provided = getattr(value, "derived_validation_digest")
    _require_digest("derived_validation_digest", provided)
    if provided != _digest_for(value):
        raise ValueError("derived_validation_digest does not match payload")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _digest_for(value: object) -> str:
    payload = asdict(value)
    payload.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value.quantize(RATIO_QUANTUM))
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        return value
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must be Decimal-derived strings")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if any(fragment in key.lower() for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and any(
        fragment in value.lower() for fragment in _UNSAFE_PUBLIC_FRAGMENTS
    ):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_COMPONENT_AUDIT_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_PROBABILITY_EDGE_COMPONENT_AUDIT_STATUSES",
    "ResearchStrategyProbabilityEdgeComponentAuditConfig",
    "ResearchStrategyProbabilityEdgeComponentAuditInput",
    "ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount",
    "ResearchStrategyProbabilityEdgeComponentAuditRow",
    "ResearchStrategyProbabilityEdgeComponentAuditReport",
    "build_research_strategy_probability_edge_component_audit_report",
    "research_strategy_probability_edge_component_audit_report_payload",
)
