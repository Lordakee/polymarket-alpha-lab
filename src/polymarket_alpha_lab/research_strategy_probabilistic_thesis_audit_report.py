"""Pure probabilistic thesis support audit report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_PROBABILISTIC_THESIS_AUDIT_REPORT_CONFIG_VERSION = (
    "research-strategy-probabilistic-thesis-audit-report-v0"
)
RESEARCH_STRATEGY_PROBABILISTIC_THESIS_AUDIT_STATUSES = (
    "pass",
    "watch",
    "block",
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "au" + "th",
    "candidate",
    "credential",
    "dsn",
    "http",
    "market" + "_id",
    "market" + "_slug",
    "private",
    "question",
    "secret",
    "source" + "_text",
    "table",
    "text",
    "token",
    "url",
    "wal" + "let",
    "or" + "der",
    "li" + "ve",
    "tr" + "ade",
    "data" + "base",
    "net" + "work",
    "persist",
    "signing",
    "mutation",
    "b" + "uy",
    "se" + "ll",
    "reco" + "mmendation",
    "siz" + "ing",
    "po" + "sition",
)

ROW_REASON_CODES = (
    "cost_drag_block",
    "cost_drag_watch",
    "evidence_strength_block",
    "evidence_strength_watch",
    "liquidity_reliability_block",
    "liquidity_reliability_watch",
    "model_market_divergence_block",
    "model_market_divergence_watch",
    "probabilistic_thesis_audit_pass",
    "resolution_clarity_block",
    "resolution_clarity_watch",
    "source_freshness_block",
    "source_freshness_watch",
    "specialist_memory_confidence_block",
    "specialist_memory_confidence_watch",
)
REPORT_REASON_CODES = (
    "cost_drag_review",
    "evidence_strength_review",
    "liquidity_reliability_review",
    "model_market_divergence_review",
    "probabilistic_thesis_audit_report_block",
    "probabilistic_thesis_audit_report_empty",
    "probabilistic_thesis_audit_report_pass",
    "probabilistic_thesis_audit_report_watch",
    "resolution_clarity_review",
    "source_freshness_review",
    "specialist_memory_confidence_review",
)


@dataclass(frozen=True)
class ResearchStrategyProbabilisticThesisAuditConfig:
    config_version: str
    evidence_strength_pass_floor: Decimal
    evidence_strength_watch_floor: Decimal
    source_age_pass_ceiling_seconds: Decimal
    source_age_watch_ceiling_seconds: Decimal
    model_market_divergence_pass_ceiling: Decimal
    model_market_divergence_watch_ceiling: Decimal
    cost_drag_pass_ceiling: Decimal
    cost_drag_watch_ceiling: Decimal
    liquidity_reliability_pass_floor: Decimal
    liquidity_reliability_watch_floor: Decimal
    resolution_clarity_pass_floor: Decimal
    resolution_clarity_watch_floor: Decimal
    specialist_memory_confidence_pass_floor: Decimal
    specialist_memory_confidence_watch_floor: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyProbabilisticThesisAuditConfig, "config")
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "evidence_strength_pass_floor",
            "evidence_strength_watch_floor",
            "model_market_divergence_pass_ceiling",
            "model_market_divergence_watch_ceiling",
            "cost_drag_pass_ceiling",
            "cost_drag_watch_ceiling",
            "liquidity_reliability_pass_floor",
            "liquidity_reliability_watch_floor",
            "resolution_clarity_pass_floor",
            "resolution_clarity_watch_floor",
            "specialist_memory_confidence_pass_floor",
            "specialist_memory_confidence_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_age_pass_ceiling_seconds",
            "source_age_watch_ceiling_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "evidence_strength",
            self.evidence_strength_pass_floor,
            self.evidence_strength_watch_floor,
        )
        _require_ceiling_pair(
            "source_age",
            self.source_age_pass_ceiling_seconds,
            self.source_age_watch_ceiling_seconds,
        )
        _require_ceiling_pair(
            "model_market_divergence",
            self.model_market_divergence_pass_ceiling,
            self.model_market_divergence_watch_ceiling,
        )
        _require_ceiling_pair(
            "cost_drag",
            self.cost_drag_pass_ceiling,
            self.cost_drag_watch_ceiling,
        )
        _require_floor_pair(
            "liquidity_reliability",
            self.liquidity_reliability_pass_floor,
            self.liquidity_reliability_watch_floor,
        )
        _require_floor_pair(
            "resolution_clarity",
            self.resolution_clarity_pass_floor,
            self.resolution_clarity_watch_floor,
        )
        _require_floor_pair(
            "specialist_memory_confidence",
            self.specialist_memory_confidence_pass_floor,
            self.specialist_memory_confidence_watch_floor,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilisticThesisAuditInput:
    thesis_ref: str
    observed_at: datetime
    evidence_strength_score: Decimal
    source_age_seconds: Decimal
    model_probability: Decimal
    reference_probability: Decimal
    cost_drag_score: Decimal
    liquidity_reliability_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyProbabilisticThesisAuditInput, "input")
        _require_canonical_public_string("thesis_ref", self.thesis_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "evidence_strength_score",
            "model_probability",
            "reference_probability",
            "cost_drag_score",
            "liquidity_reliability_score",
            "resolution_clarity_score",
            "specialist_memory_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilisticThesisAuditReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilisticThesisAuditReasonCodeCount,
            "reason_code_count",
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
class ResearchStrategyProbabilisticThesisAuditRow:
    thesis_ref: str
    observed_at: datetime
    evidence_strength_score: Decimal
    source_age_seconds: Decimal
    model_probability: Decimal
    reference_probability: Decimal
    model_market_divergence: Decimal
    cost_drag_score: Decimal
    liquidity_reliability_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_confidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyProbabilisticThesisAuditRow, "row")
        _require_canonical_public_string("thesis_ref", self.thesis_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "evidence_strength_score",
            "model_probability",
            "reference_probability",
            "model_market_divergence",
            "cost_drag_score",
            "liquidity_reliability_score",
            "resolution_clarity_score",
            "specialist_memory_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
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
class ResearchStrategyProbabilisticThesisAuditReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_evidence_strength_score: Decimal
    mean_model_market_divergence: Decimal
    mean_cost_drag_score: Decimal
    mean_liquidity_reliability_score: Decimal
    mean_resolution_clarity_score: Decimal
    mean_specialist_memory_confidence_score: Decimal
    max_source_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyProbabilisticThesisAuditReasonCodeCount, ...]
    rows: tuple[ResearchStrategyProbabilisticThesisAuditRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyProbabilisticThesisAuditReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in ("source_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_evidence_strength_score",
            "mean_model_market_divergence",
            "mean_cost_drag_score",
            "mean_liquidity_reliability_score",
            "mean_resolution_clarity_score",
            "mean_specialist_memory_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
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


def build_research_strategy_probabilistic_thesis_audit_report(
    inputs: Iterable[ResearchStrategyProbabilisticThesisAuditInput],
    *,
    config: ResearchStrategyProbabilisticThesisAuditConfig,
    generated_at: datetime,
) -> ResearchStrategyProbabilisticThesisAuditReport:
    if type(config) is not ResearchStrategyProbabilisticThesisAuditConfig:
        raise ValueError(
            "config must be a ResearchStrategyProbabilisticThesisAuditConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyProbabilisticThesisAuditReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_evidence_strength_score=_mean(
            tuple(row.evidence_strength_score for row in rows),
        ),
        mean_model_market_divergence=_mean(
            tuple(row.model_market_divergence for row in rows),
        ),
        mean_cost_drag_score=_mean(tuple(row.cost_drag_score for row in rows)),
        mean_liquidity_reliability_score=_mean(
            tuple(row.liquidity_reliability_score for row in rows),
        ),
        mean_resolution_clarity_score=_mean(
            tuple(row.resolution_clarity_score for row in rows),
        ),
        mean_specialist_memory_confidence_score=_mean(
            tuple(row.specialist_memory_confidence_score for row in rows),
        ),
        max_source_age_seconds=_max_decimal(tuple(row.source_age_seconds for row in rows)),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_probabilistic_thesis_audit_report_payload(
    report: ResearchStrategyProbabilisticThesisAuditReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyProbabilisticThesisAuditReport:
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
            "report must be a ResearchStrategyProbabilisticThesisAuditReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _public_report_payload(
    report: ResearchStrategyProbabilisticThesisAuditReport,
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
    row: ResearchStrategyProbabilisticThesisAuditRow,
) -> dict[str, Any]:
    payload = asdict(row)
    payload.pop("thesis_ref", None)
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
    value: ResearchStrategyProbabilisticThesisAuditInput,
    *,
    config: ResearchStrategyProbabilisticThesisAuditConfig,
    generated_at: datetime,
) -> ResearchStrategyProbabilisticThesisAuditRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    model_market_divergence = _absolute_decimal(
        _subtract_decimal(value.model_probability, value.reference_probability),
    )
    return ResearchStrategyProbabilisticThesisAuditRow(
        thesis_ref=value.thesis_ref,
        observed_at=observed_at,
        evidence_strength_score=value.evidence_strength_score,
        source_age_seconds=value.source_age_seconds,
        model_probability=value.model_probability,
        reference_probability=value.reference_probability,
        model_market_divergence=model_market_divergence,
        cost_drag_score=value.cost_drag_score,
        liquidity_reliability_score=value.liquidity_reliability_score,
        resolution_clarity_score=value.resolution_clarity_score,
        specialist_memory_confidence_score=value.specialist_memory_confidence_score,
        status=_row_status(
            model_market_divergence=model_market_divergence,
            value=value,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            model_market_divergence=model_market_divergence,
            value=value,
            config=config,
        ),
    )


def _row_status(
    *,
    model_market_divergence: Decimal,
    value: ResearchStrategyProbabilisticThesisAuditInput,
    config: ResearchStrategyProbabilisticThesisAuditConfig,
) -> str:
    if (
        value.evidence_strength_score < config.evidence_strength_watch_floor
        or value.source_age_seconds > config.source_age_watch_ceiling_seconds
        or model_market_divergence > config.model_market_divergence_watch_ceiling
        or value.cost_drag_score > config.cost_drag_watch_ceiling
        or value.liquidity_reliability_score < config.liquidity_reliability_watch_floor
        or value.resolution_clarity_score < config.resolution_clarity_watch_floor
        or value.specialist_memory_confidence_score
        < config.specialist_memory_confidence_watch_floor
    ):
        return "block"
    if (
        value.evidence_strength_score < config.evidence_strength_pass_floor
        or value.source_age_seconds > config.source_age_pass_ceiling_seconds
        or model_market_divergence > config.model_market_divergence_pass_ceiling
        or value.cost_drag_score > config.cost_drag_pass_ceiling
        or value.liquidity_reliability_score < config.liquidity_reliability_pass_floor
        or value.resolution_clarity_score < config.resolution_clarity_pass_floor
        or value.specialist_memory_confidence_score
        < config.specialist_memory_confidence_pass_floor
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    model_market_divergence: Decimal,
    value: ResearchStrategyProbabilisticThesisAuditInput,
    config: ResearchStrategyProbabilisticThesisAuditConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if value.cost_drag_score > config.cost_drag_watch_ceiling:
        codes.append("cost_drag_block")
    elif value.cost_drag_score > config.cost_drag_pass_ceiling:
        codes.append("cost_drag_watch")
    if value.evidence_strength_score < config.evidence_strength_watch_floor:
        codes.append("evidence_strength_block")
    elif value.evidence_strength_score < config.evidence_strength_pass_floor:
        codes.append("evidence_strength_watch")
    if value.liquidity_reliability_score < config.liquidity_reliability_watch_floor:
        codes.append("liquidity_reliability_block")
    elif value.liquidity_reliability_score < config.liquidity_reliability_pass_floor:
        codes.append("liquidity_reliability_watch")
    if model_market_divergence > config.model_market_divergence_watch_ceiling:
        codes.append("model_market_divergence_block")
    elif model_market_divergence > config.model_market_divergence_pass_ceiling:
        codes.append("model_market_divergence_watch")
    if value.resolution_clarity_score < config.resolution_clarity_watch_floor:
        codes.append("resolution_clarity_block")
    elif value.resolution_clarity_score < config.resolution_clarity_pass_floor:
        codes.append("resolution_clarity_watch")
    if value.source_age_seconds > config.source_age_watch_ceiling_seconds:
        codes.append("source_freshness_block")
    elif value.source_age_seconds > config.source_age_pass_ceiling_seconds:
        codes.append("source_freshness_watch")
    if (
        value.specialist_memory_confidence_score
        < config.specialist_memory_confidence_watch_floor
    ):
        codes.append("specialist_memory_confidence_block")
    elif (
        value.specialist_memory_confidence_score
        < config.specialist_memory_confidence_pass_floor
    ):
        codes.append("specialist_memory_confidence_watch")
    if not codes:
        codes.append("probabilistic_thesis_audit_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(
    rows: tuple[ResearchStrategyProbabilisticThesisAuditRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyProbabilisticThesisAuditRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("probabilistic_thesis_audit_report_empty",)
    report_status = _report_status(rows)
    codes = [f"probabilistic_thesis_audit_report_{report_status}"]
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    if any(code.startswith("cost_drag_") for code in row_codes):
        codes.append("cost_drag_review")
    if any(code.startswith("evidence_strength_") for code in row_codes):
        codes.append("evidence_strength_review")
    if any(code.startswith("liquidity_reliability_") for code in row_codes):
        codes.append("liquidity_reliability_review")
    if any(code.startswith("model_market_divergence_") for code in row_codes):
        codes.append("model_market_divergence_review")
    if any(code.startswith("resolution_clarity_") for code in row_codes):
        codes.append("resolution_clarity_review")
    if any(code.startswith("source_freshness_") for code in row_codes):
        codes.append("source_freshness_review")
    if any(code.startswith("specialist_memory_confidence_") for code in row_codes):
        codes.append("specialist_memory_confidence_review")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchStrategyProbabilisticThesisAuditRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.evidence_strength_score,
        row.liquidity_reliability_score,
        row.resolution_clarity_score,
        row.specialist_memory_confidence_score,
        -row.model_market_divergence,
        row.thesis_ref,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyProbabilisticThesisAuditInput],
) -> tuple[ResearchStrategyProbabilisticThesisAuditInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyProbabilisticThesisAuditInput:
            raise ValueError(
                "inputs must contain ResearchStrategyProbabilisticThesisAuditInput values",
            )
        _require_hard_flags("input", value)
        if value.thesis_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate thesis_ref values")
        seen_refs.add(value.thesis_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyProbabilisticThesisAuditRow],
) -> tuple[ResearchStrategyProbabilisticThesisAuditRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyProbabilisticThesisAuditRow:
            raise ValueError(
                "rows must contain ResearchStrategyProbabilisticThesisAuditRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.thesis_ref in seen_refs:
            raise ValueError("rows must not contain duplicate thesis_ref values")
        seen_refs.add(row.thesis_ref)
    return normalized


def _validate_row_consistency(row: ResearchStrategyProbabilisticThesisAuditRow) -> None:
    expected_divergence = _absolute_decimal(
        _subtract_decimal(row.model_probability, row.reference_probability),
    )
    if row.model_market_divergence != expected_divergence:
        raise ValueError("model_market_divergence does not match probabilities")
    if row.status == "pass" and row.reason_codes != (
        "probabilistic_thesis_audit_pass",
    ):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(
    report: ResearchStrategyProbabilisticThesisAuditReport,
) -> None:
    if report.source_row_count != _count(len(report.rows)):
        raise ValueError("source_row_count must match rows")
    if report.source_row_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match source_row_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_evidence_strength_score != _mean(
        tuple(row.evidence_strength_score for row in report.rows),
    ):
        raise ValueError("mean_evidence_strength_score must match rows")
    if report.mean_model_market_divergence != _mean(
        tuple(row.model_market_divergence for row in report.rows),
    ):
        raise ValueError("mean_model_market_divergence must match rows")
    if report.mean_cost_drag_score != _mean(
        tuple(row.cost_drag_score for row in report.rows),
    ):
        raise ValueError("mean_cost_drag_score must match rows")
    if report.mean_liquidity_reliability_score != _mean(
        tuple(row.liquidity_reliability_score for row in report.rows),
    ):
        raise ValueError("mean_liquidity_reliability_score must match rows")
    if report.mean_resolution_clarity_score != _mean(
        tuple(row.resolution_clarity_score for row in report.rows),
    ):
        raise ValueError("mean_resolution_clarity_score must match rows")
    if report.mean_specialist_memory_confidence_score != _mean(
        tuple(row.specialist_memory_confidence_score for row in report.rows),
    ):
        raise ValueError("mean_specialist_memory_confidence_score must match rows")
    if report.max_source_age_seconds != _max_decimal(
        tuple(row.source_age_seconds for row in report.rows),
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(report: ResearchStrategyProbabilisticThesisAuditReport) -> None:
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
    rows: tuple[ResearchStrategyProbabilisticThesisAuditRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyProbabilisticThesisAuditRow, ...],
) -> tuple[ResearchStrategyProbabilisticThesisAuditReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategyProbabilisticThesisAuditReasonCodeCount(
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
    value: Iterable[ResearchStrategyProbabilisticThesisAuditReasonCodeCount],
) -> tuple[ResearchStrategyProbabilisticThesisAuditReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategyProbabilisticThesisAuditReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyProbabilisticThesisAuditReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _absolute_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(value))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return max(values).quantize(RATIO_QUANTUM)


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


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
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


def _require_ceiling_pair(
    name: str,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
) -> None:
    if watch_ceiling < pass_ceiling:
        raise ValueError(f"{name}_watch_ceiling must be at least {name}_pass_ceiling")


def _require_status(name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_PROBABILISTIC_THESIS_AUDIT_STATUSES
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


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


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
    "DEFAULT_RESEARCH_STRATEGY_PROBABILISTIC_THESIS_AUDIT_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_PROBABILISTIC_THESIS_AUDIT_STATUSES",
    "ResearchStrategyProbabilisticThesisAuditConfig",
    "ResearchStrategyProbabilisticThesisAuditInput",
    "ResearchStrategyProbabilisticThesisAuditReasonCodeCount",
    "ResearchStrategyProbabilisticThesisAuditRow",
    "ResearchStrategyProbabilisticThesisAuditReport",
    "build_research_strategy_probabilistic_thesis_audit_report",
    "research_strategy_probabilistic_thesis_audit_report_payload",
)
