"""Report-only attribution of probability-edge changes to domain memory factors."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_ATTRIBUTION_MEMORY_REPORT_CONFIG_VERSION = (
    "research-strategy-probability-edge-attribution-memory-report-v0"
)
RESEARCH_STRATEGY_PROBABILITY_EDGE_ATTRIBUTION_MEMORY_STATUSES = (
    "pass",
    "watch",
    "block",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,95}$")
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
STATUS_ORDER = {"block": 0, "watch": 1, "pass": 2}

REASON_CODE_SEQUENCE = (
    "probability_edge_attribution_memory_report_block",
    "probability_edge_attribution_memory_report_watch",
    "probability_edge_attribution_memory_report_pass",
    "empty_memory_changes",
    "probability_edge_attribution_memory_block",
    "probability_edge_attribution_memory_watch",
    "probability_edge_attribution_memory_pass",
    "material_probability_edge_change",
    "immaterial_probability_edge_change",
    "calibration_recency_block",
    "calibration_recency_watch",
    "calibration_recency_fresh",
    "prior_forecast_error_reuse_drag",
    "prior_forecast_error_reuse_support",
    "evidence_update_quality_drag",
    "evidence_update_quality_support",
    "cost_pressure_block",
    "cost_pressure_watch",
    "cost_pressure_low",
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candi" + "date",
        "mar" + "ket",
        "sl" + "ug",
        "quest" + "ion",
        "so" + "urce",
        "u" + "rl",
        "te" + "xt",
        "d" + "sn",
        "ta" + "ble",
        "to" + "ken",
        "wal" + "let",
        "or" + "der",
        "tr" + "ade",
        "li" + "ve",
        "au" + "th",
        "secret",
        "private",
        "credential",
        "database",
        "network",
        "socket",
        "wallet",
        "position",
        "sizing",
        "recommend",
        "buy",
        "sell",
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_ATTRIBUTION_MEMORY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_PROBABILITY_EDGE_ATTRIBUTION_MEMORY_STATUSES",
    "ResearchStrategyProbabilityEdgeAttributionMemoryConfig",
    "ResearchStrategyProbabilityEdgeAttributionMemoryInput",
    "ResearchStrategyProbabilityEdgeAttributionMemoryReasonCodeCount",
    "ResearchStrategyProbabilityEdgeAttributionMemoryReport",
    "ResearchStrategyProbabilityEdgeAttributionMemoryRow",
    "build_research_strategy_probability_edge_attribution_memory_report",
    "research_strategy_probability_edge_attribution_memory_digest",
    "research_strategy_probability_edge_attribution_memory_digest_payload",
    "research_strategy_probability_edge_attribution_memory_report_payload",
    "validate_research_strategy_probability_edge_attribution_memory_public_payload",
)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeAttributionMemoryConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_ATTRIBUTION_MEMORY_REPORT_CONFIG_VERSION
    )
    pass_attribution_score: Decimal = Decimal("0.650000")
    block_attribution_score: Decimal = Decimal("0.350000")
    material_probability_edge_change: Decimal = Decimal("0.050000")
    watch_calibration_recency_hours: Decimal = Decimal("72.000000")
    block_calibration_recency_hours: Decimal = Decimal("168.000000")
    watch_cost_pressure_score: Decimal = Decimal("0.300000")
    block_cost_pressure_score: Decimal = Decimal("0.700000")
    calibration_recency_weight: Decimal = Decimal("0.300000")
    prior_forecast_error_reuse_weight: Decimal = Decimal("0.250000")
    evidence_update_quality_weight: Decimal = Decimal("0.300000")
    cost_pressure_penalty_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityEdgeAttributionMemoryConfig,
            "config",
        )
        _require_config_version(self.config_version)
        for field_name in (
            "pass_attribution_score",
            "block_attribution_score",
            "material_probability_edge_change",
            "watch_cost_pressure_score",
            "block_cost_pressure_score",
            "calibration_recency_weight",
            "prior_forecast_error_reuse_weight",
            "evidence_update_quality_weight",
            "cost_pressure_penalty_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_calibration_recency_hours",
            "block_calibration_recency_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_attribution_score <= self.block_attribution_score:
            raise ValueError("pass_attribution_score must exceed block_attribution_score")
        if (
            self.block_calibration_recency_hours
            <= self.watch_calibration_recency_hours
        ):
            raise ValueError(
                "block_calibration_recency_hours must exceed "
                "watch_calibration_recency_hours",
            )
        if self.block_cost_pressure_score <= self.watch_cost_pressure_score:
            raise ValueError(
                "block_cost_pressure_score must exceed watch_cost_pressure_score",
            )
        if (
            self.calibration_recency_weight
            + self.prior_forecast_error_reuse_weight
            + self.evidence_update_quality_weight
        ) <= ZERO:
            raise ValueError("positive attribution weights must be nonzero")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeAttributionMemoryInput:
    memory_factor_key: str
    domain_key: str
    observed_at: datetime
    probability_edge_change_abs: Decimal
    calibration_recency_hours: Decimal
    prior_forecast_error_reuse_score: Decimal
    evidence_update_quality_score: Decimal
    cost_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityEdgeAttributionMemoryInput,
            "input",
        )
        _require_private_memory_key("memory_factor_key", self.memory_factor_key)
        _require_public_code("domain_key", self.domain_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "probability_edge_change_abs",
            _require_unit_decimal(
                "probability_edge_change_abs",
                self.probability_edge_change_abs,
            ),
        )
        object.__setattr__(
            self,
            "calibration_recency_hours",
            _require_nonnegative_decimal(
                "calibration_recency_hours",
                self.calibration_recency_hours,
            ),
        )
        for field_name in (
            "prior_forecast_error_reuse_score",
            "evidence_update_quality_score",
            "cost_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeAttributionMemoryRow:
    rank: Decimal
    memory_factor_digest: str
    domain_key: str
    observed_at: datetime
    probability_edge_change_abs: Decimal
    calibration_recency_hours: Decimal
    calibration_recency_score: Decimal
    prior_forecast_error_reuse_score: Decimal
    evidence_update_quality_score: Decimal
    cost_pressure_score: Decimal
    memory_attribution_score: Decimal
    attribution_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyProbabilityEdgeAttributionMemoryRow, "row")
        object.__setattr__(self, "rank", _require_count_decimal("rank", self.rank))
        _require_digest_reference("memory_factor_digest", self.memory_factor_digest)
        _require_public_code("domain_key", self.domain_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "probability_edge_change_abs",
            _require_unit_decimal(
                "probability_edge_change_abs",
                self.probability_edge_change_abs,
            ),
        )
        object.__setattr__(
            self,
            "calibration_recency_hours",
            _require_nonnegative_decimal(
                "calibration_recency_hours",
                self.calibration_recency_hours,
            ),
        )
        for field_name in (
            "calibration_recency_score",
            "prior_forecast_error_reuse_score",
            "evidence_update_quality_score",
            "cost_pressure_score",
            "memory_attribution_score",
            "attribution_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", asdict(self))


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeAttributionMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityEdgeAttributionMemoryReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeAttributionMemoryReport:
    generated_at: datetime
    config_version: str
    report_status: str
    change_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_probability_edge_change_abs: Decimal
    average_calibration_recency_score: Decimal
    average_prior_forecast_error_reuse_score: Decimal
    average_evidence_update_quality_score: Decimal
    average_cost_pressure_score: Decimal
    average_memory_attribution_score: Decimal
    max_cost_pressure_score: Decimal
    max_calibration_recency_hours: Decimal
    rows: tuple[ResearchStrategyProbabilityEdgeAttributionMemoryRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyProbabilityEdgeAttributionMemoryReasonCodeCount,
        ...,
    ]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityEdgeAttributionMemoryReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        _require_status("report_status", self.report_status)
        for field_name in ("change_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_probability_edge_change_abs",
            "average_calibration_recency_score",
            "average_prior_forecast_error_reuse_score",
            "average_evidence_update_quality_score",
            "average_cost_pressure_score",
            "average_memory_attribution_score",
            "max_cost_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_calibration_recency_hours",
            _require_nonnegative_decimal(
                "max_calibration_recency_hours",
                self.max_calibration_recency_hours,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_digest_or_empty("public_payload_digest", self.public_payload_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", asdict(self))
        expected_digest = _public_digest_from_values(_report_values_without_digest(self))
        if self.public_payload_digest:
            if self.public_payload_digest != expected_digest:
                raise ValueError("public_payload_digest must match report payload")
        else:
            object.__setattr__(self, "public_payload_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_probability_edge_attribution_memory_report_payload(self)


def build_research_strategy_probability_edge_attribution_memory_report(
    changes: Iterable[ResearchStrategyProbabilityEdgeAttributionMemoryInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyProbabilityEdgeAttributionMemoryConfig | None = None,
) -> ResearchStrategyProbabilityEdgeAttributionMemoryReport:
    """Build a deterministic analyst-only memory attribution report."""

    if config is None:
        config = ResearchStrategyProbabilityEdgeAttributionMemoryConfig()
    if type(config) is not ResearchStrategyProbabilityEdgeAttributionMemoryConfig:
        raise ValueError(
            "config must be ResearchStrategyProbabilityEdgeAttributionMemoryConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_changes = _normalize_inputs(changes)
    for change in normalized_changes:
        if change.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = _rank_rows(
        tuple(_row_from_input(change, config=config) for change in normalized_changes),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "change_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_probability_edge_change_abs": _average(
            tuple(row.probability_edge_change_abs for row in rows),
        ),
        "average_calibration_recency_score": _average(
            tuple(row.calibration_recency_score for row in rows),
        ),
        "average_prior_forecast_error_reuse_score": _average(
            tuple(row.prior_forecast_error_reuse_score for row in rows),
        ),
        "average_evidence_update_quality_score": _average(
            tuple(row.evidence_update_quality_score for row in rows),
        ),
        "average_cost_pressure_score": _average(
            tuple(row.cost_pressure_score for row in rows),
        ),
        "average_memory_attribution_score": _average(
            tuple(row.memory_attribution_score for row in rows),
        ),
        "max_cost_pressure_score": max(
            (row.cost_pressure_score for row in rows),
            default=ZERO,
        ),
        "max_calibration_recency_hours": _quantize_decimal(
            max((row.calibration_recency_hours for row in rows), default=ZERO),
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyProbabilityEdgeAttributionMemoryReport(
        **values,
        public_payload_digest=_public_digest_from_values(values),
    )


def research_strategy_probability_edge_attribution_memory_report_payload(
    report: ResearchStrategyProbabilityEdgeAttributionMemoryReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyProbabilityEdgeAttributionMemoryReport:
        _require_hard_flags("report", report)
        if report.public_payload_digest != research_strategy_probability_edge_attribution_memory_digest(
            report,
        ):
            raise ValueError("public_payload_digest must match report payload")
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _json_ready(dict(report))
    else:
        raise ValueError(
            "report must be a ResearchStrategyProbabilityEdgeAttributionMemoryReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_strategy_probability_edge_attribution_memory_public_payload(payload)
    return payload


def research_strategy_probability_edge_attribution_memory_digest_payload(
    report: ResearchStrategyProbabilityEdgeAttributionMemoryReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyProbabilityEdgeAttributionMemoryReport:
        raise ValueError(
            "report must be a ResearchStrategyProbabilityEdgeAttributionMemoryReport",
        )
    payload = _json_ready(_report_values_without_digest(report))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return payload


def research_strategy_probability_edge_attribution_memory_digest(
    report: ResearchStrategyProbabilityEdgeAttributionMemoryReport,
) -> str:
    if type(report) is not ResearchStrategyProbabilityEdgeAttributionMemoryReport:
        raise ValueError(
            "report must be a ResearchStrategyProbabilityEdgeAttributionMemoryReport",
        )
    return _public_digest_from_values(_report_values_without_digest(report))


def validate_research_strategy_probability_edge_attribution_memory_public_payload(
    payload: Mapping[str, Any],
) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    concrete = dict(payload)
    _reject_unsafe_public_payload("payload", concrete, allow_json_containers=True)
    _reject_payload_numbers("payload", concrete)
    _require_mapping_flags("payload", concrete)
    digest = concrete.get("public_payload_digest")
    _require_sha256_hex("public_payload_digest", digest)
    digest_payload = dict(concrete)
    digest_payload.pop("public_payload_digest", None)
    expected_digest = _public_digest_from_values(digest_payload)
    if digest != expected_digest:
        raise ValueError("public_payload_digest must match report payload")


def _row_from_input(
    change: ResearchStrategyProbabilityEdgeAttributionMemoryInput,
    *,
    config: ResearchStrategyProbabilityEdgeAttributionMemoryConfig,
) -> ResearchStrategyProbabilityEdgeAttributionMemoryRow:
    calibration_score = _calibration_recency_score(change.calibration_recency_hours, config)
    memory_attribution_score = _memory_attribution_score(
        calibration_recency_score=calibration_score,
        prior_forecast_error_reuse_score=change.prior_forecast_error_reuse_score,
        evidence_update_quality_score=change.evidence_update_quality_score,
        cost_pressure_score=change.cost_pressure_score,
        config=config,
    )
    status = _row_status(
        calibration_recency_hours=change.calibration_recency_hours,
        cost_pressure_score=change.cost_pressure_score,
        memory_attribution_score=memory_attribution_score,
        config=config,
    )
    return ResearchStrategyProbabilityEdgeAttributionMemoryRow(
        rank=ONE,
        memory_factor_digest=_memory_factor_digest(
            change.memory_factor_key,
            change.domain_key,
        ),
        domain_key=change.domain_key,
        observed_at=change.observed_at,
        probability_edge_change_abs=change.probability_edge_change_abs,
        calibration_recency_hours=change.calibration_recency_hours,
        calibration_recency_score=calibration_score,
        prior_forecast_error_reuse_score=change.prior_forecast_error_reuse_score,
        evidence_update_quality_score=change.evidence_update_quality_score,
        cost_pressure_score=change.cost_pressure_score,
        memory_attribution_score=memory_attribution_score,
        attribution_pressure=_clamp_unit(ONE - memory_attribution_score),
        status=status,
        reason_codes=_row_reason_codes(
            change=change,
            status=status,
            config=config,
        ),
    )


def _calibration_recency_score(
    calibration_recency_hours: Decimal,
    config: ResearchStrategyProbabilityEdgeAttributionMemoryConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_unit(
            ONE - (calibration_recency_hours / config.block_calibration_recency_hours),
        )


def _memory_attribution_score(
    *,
    calibration_recency_score: Decimal,
    prior_forecast_error_reuse_score: Decimal,
    evidence_update_quality_score: Decimal,
    cost_pressure_score: Decimal,
    config: ResearchStrategyProbabilityEdgeAttributionMemoryConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_unit(
            calibration_recency_score * config.calibration_recency_weight
            + prior_forecast_error_reuse_score
            * config.prior_forecast_error_reuse_weight
            + evidence_update_quality_score * config.evidence_update_quality_weight
            - cost_pressure_score * config.cost_pressure_penalty_weight,
        )


def _row_status(
    *,
    calibration_recency_hours: Decimal,
    cost_pressure_score: Decimal,
    memory_attribution_score: Decimal,
    config: ResearchStrategyProbabilityEdgeAttributionMemoryConfig,
) -> str:
    if (
        memory_attribution_score < config.block_attribution_score
        or calibration_recency_hours >= config.block_calibration_recency_hours
        or cost_pressure_score >= config.block_cost_pressure_score
    ):
        return "block"
    if (
        memory_attribution_score >= config.pass_attribution_score
        and calibration_recency_hours < config.watch_calibration_recency_hours
        and cost_pressure_score < config.watch_cost_pressure_score
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    change: ResearchStrategyProbabilityEdgeAttributionMemoryInput,
    status: str,
    config: ResearchStrategyProbabilityEdgeAttributionMemoryConfig,
) -> tuple[str, ...]:
    codes: list[str] = [f"probability_edge_attribution_memory_{status}"]
    if change.probability_edge_change_abs >= config.material_probability_edge_change:
        codes.append("material_probability_edge_change")
    else:
        codes.append("immaterial_probability_edge_change")
    if change.calibration_recency_hours >= config.block_calibration_recency_hours:
        codes.append("calibration_recency_block")
    elif change.calibration_recency_hours >= config.watch_calibration_recency_hours:
        codes.append("calibration_recency_watch")
    else:
        codes.append("calibration_recency_fresh")
    if change.prior_forecast_error_reuse_score < config.block_attribution_score:
        codes.append("prior_forecast_error_reuse_drag")
    elif change.prior_forecast_error_reuse_score >= config.pass_attribution_score:
        codes.append("prior_forecast_error_reuse_support")
    if change.evidence_update_quality_score < config.block_attribution_score:
        codes.append("evidence_update_quality_drag")
    elif change.evidence_update_quality_score >= config.pass_attribution_score:
        codes.append("evidence_update_quality_support")
    if change.cost_pressure_score >= config.block_cost_pressure_score:
        codes.append("cost_pressure_block")
    elif change.cost_pressure_score >= config.watch_cost_pressure_score:
        codes.append("cost_pressure_watch")
    else:
        codes.append("cost_pressure_low")
    return _normalize_reason_codes(tuple(codes), allow_empty=False)


def _rank_rows(
    rows: tuple[ResearchStrategyProbabilityEdgeAttributionMemoryRow, ...],
) -> tuple[ResearchStrategyProbabilityEdgeAttributionMemoryRow, ...]:
    return tuple(
        ResearchStrategyProbabilityEdgeAttributionMemoryRow(
            rank=_count(index),
            memory_factor_digest=row.memory_factor_digest,
            domain_key=row.domain_key,
            observed_at=row.observed_at,
            probability_edge_change_abs=row.probability_edge_change_abs,
            calibration_recency_hours=row.calibration_recency_hours,
            calibration_recency_score=row.calibration_recency_score,
            prior_forecast_error_reuse_score=row.prior_forecast_error_reuse_score,
            evidence_update_quality_score=row.evidence_update_quality_score,
            cost_pressure_score=row.cost_pressure_score,
            memory_attribution_score=row.memory_attribution_score,
            attribution_pressure=row.attribution_pressure,
            status=row.status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_sort_key(
    row: ResearchStrategyProbabilityEdgeAttributionMemoryRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, datetime, str, str]:
    return (
        STATUS_ORDER[row.status],
        -row.attribution_pressure,
        -row.probability_edge_change_abs,
        -row.cost_pressure_score,
        -row.calibration_recency_hours,
        -row.memory_attribution_score,
        row.observed_at,
        row.domain_key,
        row.memory_factor_digest,
    )


def _normalize_inputs(
    changes: Iterable[ResearchStrategyProbabilityEdgeAttributionMemoryInput],
) -> tuple[ResearchStrategyProbabilityEdgeAttributionMemoryInput, ...]:
    if isinstance(changes, (str, bytes)):
        raise ValueError("changes must be an iterable")
    try:
        normalized = tuple(changes)
    except TypeError as exc:
        raise ValueError("changes must be an iterable") from exc
    for change in normalized:
        if type(change) is not ResearchStrategyProbabilityEdgeAttributionMemoryInput:
            raise ValueError(
                "changes must contain "
                "ResearchStrategyProbabilityEdgeAttributionMemoryInput values",
            )
        _require_hard_flags("input", change)
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchStrategyProbabilityEdgeAttributionMemoryRow],
) -> tuple[ResearchStrategyProbabilityEdgeAttributionMemoryRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyProbabilityEdgeAttributionMemoryRow:
            raise ValueError(
                "rows must contain ResearchStrategyProbabilityEdgeAttributionMemoryRow "
                "values",
            )
        _require_hard_flags("row", row)
    if tuple(sorted(normalized, key=_row_sort_key)) != normalized:
        raise ValueError("rows must use deterministic sequence")
    if tuple(row.rank for row in normalized) != tuple(
        _count(index) for index in range(1, len(normalized) + 1)
    ):
        raise ValueError("rows must use sequential ranks")
    return normalized


def _normalize_reason_code_counts(
    counts: Sequence[ResearchStrategyProbabilityEdgeAttributionMemoryReasonCodeCount],
) -> tuple[ResearchStrategyProbabilityEdgeAttributionMemoryReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized = tuple(counts)
    expected = tuple(sorted(normalized, key=lambda item: _reason_code_rank(item.reason_code)))
    if normalized != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    seen: set[str] = set()
    for count in normalized:
        if type(count) is not ResearchStrategyProbabilityEdgeAttributionMemoryReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must not repeat")
        seen.add(count.reason_code)
    return normalized


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        normalized_code = _require_reason_code("reason_code", reason_code)
        if normalized_code in seen:
            raise ValueError("reason_codes must not repeat")
        seen.add(normalized_code)
        normalized.append(normalized_code)
    if not allow_empty and not normalized:
        raise ValueError("reason_codes must not be empty")
    expected = tuple(code for code in REASON_CODE_SEQUENCE if code in seen)
    if tuple(normalized) != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    return tuple(normalized)


def _report_status(
    rows: tuple[ResearchStrategyProbabilityEdgeAttributionMemoryRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyProbabilityEdgeAttributionMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (
            "probability_edge_attribution_memory_report_block",
            "empty_memory_changes",
        )
    seen: set[str] = {f"probability_edge_attribution_memory_report_{_report_status(rows)}"}
    for row in rows:
        seen.update(row.reason_codes)
    return _normalize_reason_codes(
        tuple(code for code in REASON_CODE_SEQUENCE if code in seen),
        allow_empty=False,
    )


def _reason_code_counts(
    rows: tuple[ResearchStrategyProbabilityEdgeAttributionMemoryRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyProbabilityEdgeAttributionMemoryReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    if not rows:
        counter.update(report_reason_codes)
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyProbabilityEdgeAttributionMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if counter[reason_code] > 0
    )


def _status_count(
    rows: tuple[ResearchStrategyProbabilityEdgeAttributionMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(sum(values, ZERO) / Decimal(len(values)))


def _validate_row_consistency(
    row: ResearchStrategyProbabilityEdgeAttributionMemoryRow,
) -> None:
    if row.rank <= ZERO:
        raise ValueError("rank must be positive")
    if row.attribution_pressure != _clamp_unit(ONE - row.memory_attribution_score):
        raise ValueError("attribution_pressure must match memory_attribution_score")
    if row.status == "pass" and row.reason_codes[0] != (
        "probability_edge_attribution_memory_pass"
    ):
        raise ValueError("pass rows must include pass reason")
    if row.status == "watch" and row.reason_codes[0] != (
        "probability_edge_attribution_memory_watch"
    ):
        raise ValueError("watch rows must include watch reason")
    if row.status == "block" and row.reason_codes[0] != (
        "probability_edge_attribution_memory_block"
    ):
        raise ValueError("block rows must include block reason")


def _validate_report_consistency(
    report: ResearchStrategyProbabilityEdgeAttributionMemoryReport,
) -> None:
    rows = report.rows
    if report.change_count != _count(len(rows)):
        raise ValueError("change_count must match rows")
    if report.change_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match change_count")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_probability_edge_change_abs != _average(
        tuple(row.probability_edge_change_abs for row in rows),
    ):
        raise ValueError("average_probability_edge_change_abs must match rows")
    if report.average_calibration_recency_score != _average(
        tuple(row.calibration_recency_score for row in rows),
    ):
        raise ValueError("average_calibration_recency_score must match rows")
    if report.average_prior_forecast_error_reuse_score != _average(
        tuple(row.prior_forecast_error_reuse_score for row in rows),
    ):
        raise ValueError("average_prior_forecast_error_reuse_score must match rows")
    if report.average_evidence_update_quality_score != _average(
        tuple(row.evidence_update_quality_score for row in rows),
    ):
        raise ValueError("average_evidence_update_quality_score must match rows")
    if report.average_cost_pressure_score != _average(
        tuple(row.cost_pressure_score for row in rows),
    ):
        raise ValueError("average_cost_pressure_score must match rows")
    if report.average_memory_attribution_score != _average(
        tuple(row.memory_attribution_score for row in rows),
    ):
        raise ValueError("average_memory_attribution_score must match rows")
    if report.max_cost_pressure_score != max(
        (row.cost_pressure_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_cost_pressure_score must match rows")
    if report.max_calibration_recency_hours != _quantize_decimal(
        max((row.calibration_recency_hours for row in rows), default=ZERO),
    ):
        raise ValueError("max_calibration_recency_hours must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _public_digest_from_values(values: Mapping[str, Any]) -> str:
    encoded = dumps(
        _json_ready(dict(values)),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _report_values_without_digest(
    report: ResearchStrategyProbabilityEdgeAttributionMemoryReport,
) -> dict[str, Any]:
    values = asdict(report)
    values.pop("public_payload_digest", None)
    return values


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        return str(_quantize_decimal(value))
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_ready(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(nested) for nested in value]
    if isinstance(value, list):
        return [_json_ready(nested) for nested in value]
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    raise ValueError("payload contains unsupported value type")


def _memory_factor_digest(memory_factor_key: str, domain_key: str) -> str:
    encoded = dumps(
        {"domain_key": domain_key, "memory_factor_key": memory_factor_key},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"sha256:{sha256(encoded).hexdigest()}"


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _clamp_unit(value: Decimal) -> Decimal:
    normalized = _quantize_decimal(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize_decimal(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_config_version(value: str) -> None:
    if value != DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_ATTRIBUTION_MEMORY_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be supported")


def _require_private_memory_key(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_public_code(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if PUBLIC_CODE_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public code")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload value")


def _require_reason_code(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_status(field_name: str, value: str) -> None:
    if value not in RESEARCH_STRATEGY_PROBABILITY_EDGE_ATTRIBUTION_MEMORY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_digest_reference(field_name: str, value: str) -> None:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest reference")


def _require_sha256_hex(field_name: str, value: object) -> None:
    if type(value) is not str or SHA256_HEX_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_digest_or_empty(field_name: str, value: str) -> None:
    if value == "":
        return
    _require_sha256_hex(field_name, value)


def _require_unit_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize_decimal(value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_mapping_flags(label: str, value: Mapping[str, Any]) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reason_code_rank(reason_code: str) -> int:
    try:
        return REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("unknown reason code") from exc


def _reject_payload_numbers(label: str, value: object) -> None:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return
    if isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{label} must not contain JSON numeric values")
    if isinstance(value, Mapping):
        for key, nested in value.items():
            _reject_payload_numbers(f"{label}.{key}", nested)
        return
    if isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_payload_numbers(f"{label}[{index}]", nested)
        return
    raise ValueError(f"{label} contains unsupported payload value")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload key at {label}")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"unsafe public payload key at {label}.{key}")
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                nested,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (tuple, list)):
        for index, nested in enumerate(value):
            _reject_unsafe_public_payload(
                f"{label}[{index}]",
                nested,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        lowered_value = value.lower()
        if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public payload value at {label}")
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    if allow_json_containers and type(value) in (int, float):
        return
    raise ValueError(f"unsafe public payload value at {label}")
