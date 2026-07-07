"""Pure report-only post-outcome research learning queue."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_OUTCOME_LEARNING_QUEUE_CONFIG_VERSION = (
    "research-outcome-learning-queue-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_STATES = ("pass", "watch", "block")
_STATE_RANK = {"pass": 0, "watch": 1, "block": 2}
_SETTLEMENT_STATES = frozenset(("settled", "pending", "disputed", "voided"))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "ref",
    "url",
    "text",
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
    "recommend",
    "database",
    "postgres",
    "supabase",
    "psycopg",
    "sqlite",
    "http",
    "https",
)
_REASON_CODE_ORDER = (
    "learning_records_empty",
    "settlement_not_final_block",
    "settlement_needs_review_watch",
    "prediction_deviation_high_block",
    "prediction_deviation_high_watch",
    "evidence_quality_low_block",
    "evidence_quality_low_watch",
    "review_incomplete_block",
    "review_incomplete_watch",
    "learning_ready",
)


@dataclass(frozen=True)
class ResearchOutcomeLearningQueueConfig:
    config_version: str = DEFAULT_RESEARCH_OUTCOME_LEARNING_QUEUE_CONFIG_VERSION
    watch_prediction_deviation: Decimal = Decimal("0.150000")
    block_prediction_deviation: Decimal = Decimal("0.350000")
    watch_min_evidence_quality_score: Decimal = Decimal("0.700000")
    block_min_evidence_quality_score: Decimal = Decimal("0.400000")
    watch_min_review_completeness_score: Decimal = Decimal("0.800000")
    block_min_review_completeness_score: Decimal = Decimal("0.500000")
    prediction_weight: Decimal = Decimal("0.400000")
    evidence_gap_weight: Decimal = Decimal("0.200000")
    review_gap_weight: Decimal = Decimal("0.200000")
    settlement_gate_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeLearningQueueConfig:
            raise TypeError("ResearchOutcomeLearningQueueConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningQueueConfig:
            raise ValueError("config must be exactly ResearchOutcomeLearningQueueConfig")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_OUTCOME_LEARNING_QUEUE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "watch_prediction_deviation",
            "block_prediction_deviation",
            "watch_min_evidence_quality_score",
            "block_min_evidence_quality_score",
            "watch_min_review_completeness_score",
            "block_min_review_completeness_score",
            "prediction_weight",
            "evidence_gap_weight",
            "review_gap_weight",
            "settlement_gate_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_prediction_deviation > self.block_prediction_deviation:
            raise ValueError(
                "watch_prediction_deviation must not exceed block_prediction_deviation",
            )
        if (
            self.block_min_evidence_quality_score
            > self.watch_min_evidence_quality_score
        ):
            raise ValueError(
                "block_min_evidence_quality_score must not exceed "
                "watch_min_evidence_quality_score",
            )
        if (
            self.block_min_review_completeness_score
            > self.watch_min_review_completeness_score
        ):
            raise ValueError(
                "block_min_review_completeness_score must not exceed "
                "watch_min_review_completeness_score",
            )
        weight_sum = _quantize(
            self.prediction_weight
            + self.evidence_gap_weight
            + self.review_gap_weight
            + self.settlement_gate_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("priority weights must sum to 1.000000")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchOutcomeLearningRecord:
    private_case_ref: str
    private_event_ref: str
    settlement_state: str
    predicted_probability: Decimal
    resolved_probability: Decimal
    evidence_quality_score: Decimal
    review_completeness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeLearningRecord:
            raise TypeError("ResearchOutcomeLearningRecord does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningRecord:
            raise ValueError("record must be exactly ResearchOutcomeLearningRecord")
        _require_private_ref("private_case_ref", self.private_case_ref)
        _require_private_ref("private_event_ref", self.private_event_ref)
        _require_settlement_state("settlement_state", self.settlement_state)
        for field_name in (
            "predicted_probability",
            "resolved_probability",
            "evidence_quality_score",
            "review_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("record", self)


@dataclass(frozen=True)
class ResearchOutcomeLearningQueueRow:
    case_key: str
    rank: Decimal
    prediction_deviation: Decimal
    evidence_quality_score: Decimal
    review_completeness_score: Decimal
    priority_score: Decimal
    settlement_gate: str
    prediction_gate: str
    evidence_quality_gate: str
    review_completeness_gate: str
    learning_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeLearningQueueRow:
            raise TypeError("ResearchOutcomeLearningQueueRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningQueueRow:
            raise ValueError("row must be exactly ResearchOutcomeLearningQueueRow")
        _require_public_identifier("case_key", self.case_key)
        object.__setattr__(self, "rank", _require_count_decimal("rank", self.rank))
        for field_name in (
            "prediction_deviation",
            "evidence_quality_score",
            "review_completeness_score",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "settlement_gate",
            "prediction_gate",
            "evidence_quality_gate",
            "review_completeness_gate",
            "learning_status",
        ):
            _require_public_state(field_name, getattr(self, field_name))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchOutcomeLearningQueueReport:
    generated_at: datetime
    config_version: str
    queue_status: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_priority_score: Decimal
    highest_priority_score: Decimal
    watch_prediction_deviation: Decimal
    block_prediction_deviation: Decimal
    watch_min_evidence_quality_score: Decimal
    block_min_evidence_quality_score: Decimal
    watch_min_review_completeness_score: Decimal
    block_min_review_completeness_score: Decimal
    rows: tuple[ResearchOutcomeLearningQueueRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeLearningQueueReport:
            raise TypeError("ResearchOutcomeLearningQueueReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningQueueReport:
            raise ValueError("report must be exactly ResearchOutcomeLearningQueueReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_OUTCOME_LEARNING_QUEUE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        _require_public_state("queue_status", self.queue_status)
        for field_name in ("case_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_priority_score",
            "highest_priority_score",
            "watch_prediction_deviation",
            "block_prediction_deviation",
            "watch_min_evidence_quality_score",
            "block_min_evidence_quality_score",
            "watch_min_review_completeness_score",
            "block_min_review_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_unsafe_public_payload("payload", payload)
        _reject_non_public_status_values("payload", payload)
        return payload


def build_research_outcome_learning_queue(
    records: Sequence[ResearchOutcomeLearningRecord],
    *,
    generated_at: datetime,
    config: ResearchOutcomeLearningQueueConfig | None = None,
) -> ResearchOutcomeLearningQueueReport:
    """Build a deterministic, anonymized, report-only learning queue."""

    if config is None:
        config = ResearchOutcomeLearningQueueConfig()
    if type(config) is not ResearchOutcomeLearningQueueConfig:
        raise ValueError("config must be a ResearchOutcomeLearningQueueConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_records = _normalize_records(records)
    rows_without_rank = tuple(_row_from_record(record, config) for record in normalized_records)
    rows = _rank_rows(rows_without_rank)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "queue_status": _report_status(rows),
        "case_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_priority_score": _average(tuple(row.priority_score for row in rows)),
        "highest_priority_score": _highest_priority_score(rows),
        "watch_prediction_deviation": config.watch_prediction_deviation,
        "block_prediction_deviation": config.block_prediction_deviation,
        "watch_min_evidence_quality_score": config.watch_min_evidence_quality_score,
        "block_min_evidence_quality_score": config.block_min_evidence_quality_score,
        "watch_min_review_completeness_score": (
            config.watch_min_review_completeness_score
        ),
        "block_min_review_completeness_score": (
            config.block_min_review_completeness_score
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchOutcomeLearningQueueReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_outcome_learning_queue_payload(
    report: ResearchOutcomeLearningQueueReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchOutcomeLearningQueueReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = report.payload
        _require_hard_flags("payload", _DictFlags(payload))
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_unsafe_public_payload("payload", payload)
        _reject_non_public_status_values("payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        return payload
    raise ValueError("report must be a ResearchOutcomeLearningQueueReport or payload")


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


def _row_from_record(
    record: ResearchOutcomeLearningRecord,
    config: ResearchOutcomeLearningQueueConfig,
) -> ResearchOutcomeLearningQueueRow:
    prediction_deviation = _quantize(
        abs(record.predicted_probability - record.resolved_probability),
    )
    settlement_gate = _settlement_gate(record.settlement_state)
    prediction_gate = _prediction_gate(prediction_deviation, config)
    evidence_quality_gate = _minimum_score_gate(
        record.evidence_quality_score,
        watch_minimum=config.watch_min_evidence_quality_score,
        block_minimum=config.block_min_evidence_quality_score,
    )
    review_completeness_gate = _minimum_score_gate(
        record.review_completeness_score,
        watch_minimum=config.watch_min_review_completeness_score,
        block_minimum=config.block_min_review_completeness_score,
    )
    learning_status = _worst_state(
        (
            settlement_gate,
            prediction_gate,
            evidence_quality_gate,
            review_completeness_gate,
        ),
    )
    return ResearchOutcomeLearningQueueRow(
        case_key=_case_key(record),
        rank=_ZERO,
        prediction_deviation=prediction_deviation,
        evidence_quality_score=record.evidence_quality_score,
        review_completeness_score=record.review_completeness_score,
        priority_score=_priority_score(
            prediction_deviation=prediction_deviation,
            evidence_quality_score=record.evidence_quality_score,
            review_completeness_score=record.review_completeness_score,
            settlement_gate=settlement_gate,
            config=config,
        ),
        settlement_gate=settlement_gate,
        prediction_gate=prediction_gate,
        evidence_quality_gate=evidence_quality_gate,
        review_completeness_gate=review_completeness_gate,
        learning_status=learning_status,
        reason_codes=_row_reason_codes(
            settlement_gate=settlement_gate,
            prediction_gate=prediction_gate,
            evidence_quality_gate=evidence_quality_gate,
            review_completeness_gate=review_completeness_gate,
        ),
    )


def _rank_rows(
    rows: tuple[ResearchOutcomeLearningQueueRow, ...],
) -> tuple[ResearchOutcomeLearningQueueRow, ...]:
    ranked_rows = []
    for index, row in enumerate(
        sorted(
            rows,
            key=lambda item: (
                -item.priority_score,
                -_STATE_RANK[item.learning_status],
                item.case_key,
            ),
        ),
        start=1,
    ):
        ranked_rows.append(
            ResearchOutcomeLearningQueueRow(
                case_key=row.case_key,
                rank=_decimal_count(index),
                prediction_deviation=row.prediction_deviation,
                evidence_quality_score=row.evidence_quality_score,
                review_completeness_score=row.review_completeness_score,
                priority_score=row.priority_score,
                settlement_gate=row.settlement_gate,
                prediction_gate=row.prediction_gate,
                evidence_quality_gate=row.evidence_quality_gate,
                review_completeness_gate=row.review_completeness_gate,
                learning_status=row.learning_status,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked_rows)


def _settlement_gate(settlement_state: str) -> str:
    if settlement_state == "settled":
        return "pass"
    if settlement_state == "disputed":
        return "watch"
    return "block"


def _prediction_gate(
    prediction_deviation: Decimal,
    config: ResearchOutcomeLearningQueueConfig,
) -> str:
    if prediction_deviation >= config.block_prediction_deviation:
        return "block"
    if prediction_deviation >= config.watch_prediction_deviation:
        return "watch"
    return "pass"


def _minimum_score_gate(
    value: Decimal,
    *,
    watch_minimum: Decimal,
    block_minimum: Decimal,
) -> str:
    if value < block_minimum:
        return "block"
    if value < watch_minimum:
        return "watch"
    return "pass"


def _priority_score(
    *,
    prediction_deviation: Decimal,
    evidence_quality_score: Decimal,
    review_completeness_score: Decimal,
    settlement_gate: str,
    config: ResearchOutcomeLearningQueueConfig,
) -> Decimal:
    settlement_pressure = Decimal(_STATE_RANK[settlement_gate]) / Decimal("2")
    score = (
        prediction_deviation * config.prediction_weight
        + (_ONE - evidence_quality_score) * config.evidence_gap_weight
        + (_ONE - review_completeness_score) * config.review_gap_weight
        + settlement_pressure * config.settlement_gate_weight
    )
    return _clamp_ratio(score)


def _row_reason_codes(
    *,
    settlement_gate: str,
    prediction_gate: str,
    evidence_quality_gate: str,
    review_completeness_gate: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if settlement_gate == "block":
        reason_codes.append("settlement_not_final_block")
    elif settlement_gate == "watch":
        reason_codes.append("settlement_needs_review_watch")
    if prediction_gate == "block":
        reason_codes.append("prediction_deviation_high_block")
    elif prediction_gate == "watch":
        reason_codes.append("prediction_deviation_high_watch")
    if evidence_quality_gate == "block":
        reason_codes.append("evidence_quality_low_block")
    elif evidence_quality_gate == "watch":
        reason_codes.append("evidence_quality_low_watch")
    if review_completeness_gate == "block":
        reason_codes.append("review_incomplete_block")
    elif review_completeness_gate == "watch":
        reason_codes.append("review_incomplete_watch")
    if not reason_codes:
        reason_codes.append("learning_ready")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(rows: tuple[ResearchOutcomeLearningQueueRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("learning_records_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchOutcomeLearningQueueRow, ...]) -> str:
    if not rows:
        return "block"
    return _worst_state(tuple(row.learning_status for row in rows))


def _normalize_records(
    records: Sequence[ResearchOutcomeLearningRecord],
) -> tuple[ResearchOutcomeLearningRecord, ...]:
    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
        raise ValueError("records must be a sequence")
    normalized: list[ResearchOutcomeLearningRecord] = []
    seen_keys: set[str] = set()
    for item in records:
        if type(item) is not ResearchOutcomeLearningRecord:
            raise ValueError("records must contain ResearchOutcomeLearningRecord values")
        _require_hard_flags("record", item)
        case_key = _case_key(item)
        if case_key in seen_keys:
            raise ValueError("records must not contain duplicate private case/event pairs")
        seen_keys.add(case_key)
        normalized.append(item)
    return tuple(sorted(normalized, key=_case_key))


def _normalize_rows(
    rows: Sequence[ResearchOutcomeLearningQueueRow],
) -> tuple[ResearchOutcomeLearningQueueRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchOutcomeLearningQueueRow] = []
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchOutcomeLearningQueueRow:
            raise ValueError("rows must contain ResearchOutcomeLearningQueueRow values")
        if row.case_key in seen_keys:
            raise ValueError("rows must not repeat case_key values")
        seen_keys.add(row.case_key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: (row.rank, row.case_key)))


def _validate_row(row: ResearchOutcomeLearningQueueRow) -> None:
    expected_status = _worst_state(
        (
            row.settlement_gate,
            row.prediction_gate,
            row.evidence_quality_gate,
            row.review_completeness_gate,
        ),
    )
    if row.learning_status != expected_status:
        raise ValueError("learning_status must match gate states")
    if row.learning_status == "pass" and row.reason_codes != ("learning_ready",):
        raise ValueError("pass rows must use learning_ready reason code")
    if row.learning_status != "pass" and "learning_ready" in row.reason_codes:
        raise ValueError("non-pass rows must not use learning_ready")
    expected_reasons = _row_reason_codes(
        settlement_gate=row.settlement_gate,
        prediction_gate=row.prediction_gate,
        evidence_quality_gate=row.evidence_quality_gate,
        review_completeness_gate=row.review_completeness_gate,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match gate states")


def _validate_report(report: ResearchOutcomeLearningQueueReport) -> None:
    if report.case_count != _decimal_count(len(report.rows)):
        raise ValueError("case_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.case_count:
        raise ValueError("status counts must sum to case_count")
    if report.queue_status != _report_status(report.rows):
        raise ValueError("queue_status must match rows")
    if report.average_priority_score != _average(
        tuple(row.priority_score for row in report.rows),
    ):
        raise ValueError("average_priority_score must match rows")
    if report.highest_priority_score != _highest_priority_score(report.rows):
        raise ValueError("highest_priority_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(rows: tuple[ResearchOutcomeLearningQueueRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.learning_status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _highest_priority_score(rows: tuple[ResearchOutcomeLearningQueueRow, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return _quantize(max(row.priority_score for row in rows))


def _worst_state(states: tuple[str, ...]) -> str:
    if not states:
        return "block"
    for state in states:
        _require_public_state("state", state)
    return max(states, key=lambda item: _STATE_RANK[item])


def _case_key(record: ResearchOutcomeLearningRecord) -> str:
    encoded = json.dumps(
        {
            "private_case_ref": record.private_case_ref,
            "private_event_ref": record.private_event_ref,
        },
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "case-" + hashlib.sha256(encoded).hexdigest()[:24]


def _report_values_without_digest(
    report: ResearchOutcomeLearningQueueReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return _decimal_to_json(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("learning queue values must be JSON serializable")


def _decimal_to_json(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("JSON Decimal value must be finite")
    with localcontext() as context:
        context.prec = max(
            28,
            len(value.as_tuple().digits) + abs(value.as_tuple().exponent) + 6,
        )
        quantized = value.quantize(_QUANT, rounding=ROUND_HALF_EVEN)
    if value != quantized:
        raise ValueError("JSON Decimal value must have at most six decimal places")
    if quantized.is_zero():
        quantized = _ZERO
    return format(quantized, "f")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value.quantize(_QUANT, rounding=ROUND_HALF_EVEN)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_EVEN)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_EVEN)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_private_ref(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if len(value) > 4096:
        raise ValueError(f"{field_name} must not exceed 4096 characters")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_state(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _PUBLIC_STATES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_settlement_state(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _SETTLEMENT_STATES:
        raise ValueError(f"{field_name} must be a supported settlement state")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_ORDER:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(code for code in _REASON_CODE_ORDER if code in normalized)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for key in _iter_public_keys(payload):
        _reject_unsafe_public_string(f"{label}.{key}", key)
    for value in _iter_public_string_values(payload):
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _reject_non_public_status_values(label: str, payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            normalized_key = key.lower()
            if "status" in normalized_key or normalized_key.endswith("gate"):
                if value not in _PUBLIC_STATES:
                    raise ValueError(f"{label}.{key} must be a public status")
            _reject_non_public_status_values(f"{label}.{key}", value)
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            _reject_non_public_status_values(f"{label}[{index}]", value)


def _iter_public_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_public_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_public_keys(item))
        return tuple(keys)
    return ()


def _iter_public_string_values(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_string_values(asdict(value))
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_iter_public_string_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_iter_public_string_values(item))
        return tuple(values)
    if type(value) is str:
        return (value,)
    return ()


__all__ = (
    "DEFAULT_RESEARCH_OUTCOME_LEARNING_QUEUE_CONFIG_VERSION",
    "ResearchOutcomeLearningQueueConfig",
    "ResearchOutcomeLearningRecord",
    "ResearchOutcomeLearningQueueReport",
    "ResearchOutcomeLearningQueueRow",
    "build_research_outcome_learning_queue",
    "research_outcome_learning_queue_payload",
)
