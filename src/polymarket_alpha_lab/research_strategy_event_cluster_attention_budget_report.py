"""Pure report-only event cluster attention budget report."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_ATTENTION_BUDGET_REPORT_CONFIG_VERSION",
    "ResearchStrategyEventClusterAttentionBudgetCluster",
    "ResearchStrategyEventClusterAttentionBudgetConfig",
    "ResearchStrategyEventClusterAttentionBudgetReport",
    "ResearchStrategyEventClusterAttentionBudgetRow",
    "build_research_strategy_event_cluster_attention_budget_report",
    "research_strategy_event_cluster_attention_budget_report_digest",
    "research_strategy_event_cluster_attention_budget_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_ATTENTION_BUDGET_REPORT_CONFIG_VERSION = (
    "research-strategy-event-cluster-attention-budget-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
NO_CLUSTERS_REASON = "attention_budget_no_clusters"
PASS_REASON = "attention_budget_pass"
SUMMARY_KEYS = (
    "generated_at",
    "config_version",
    "cluster_count",
    "pass_count",
    "watch_count",
    "block_count",
    "total_attention_pressure",
    "max_attention_pressure",
    "average_attention_pressure",
    "max_attention_share",
    "status",
    "reason_codes",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_PRIORITY = (
    "attention_share_block",
    "attention_pressure_block",
    "attention_share_watch",
    "attention_pressure_watch",
    PASS_REASON,
    NO_CLUSTERS_REASON,
)
ROW_DIGEST_KEYS = (
    "row_number",
    "evidence_urgency_score",
    "timing_risk_score",
    "contradiction_pressure_score",
    "domain_memory_gap_score",
    "evidence_urgency_weight",
    "timing_risk_weight",
    "contradiction_pressure_weight",
    "domain_memory_gap_weight",
    "attention_pressure",
    "attention_share",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_DIGEST_KEYS = (
    "generated_at",
    "config_version",
    "cluster_count",
    "pass_count",
    "watch_count",
    "block_count",
    "total_attention_pressure",
    "max_attention_pressure",
    "average_attention_pressure",
    "max_attention_share",
    "status",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
UNSAFE_TEXT_FRAGMENTS = (
    "candidate" "_" "id",
    "market" "_" "id",
    "market" "_" "slug",
    "question",
    "so" "urce",
    "url",
    "dsn",
    "table",
    "tok" "en",
    "private",
    "sec" "ret",
    "pass" "word",
    "api" "_" "key",
    "au" "th",
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
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyEventClusterAttentionBudgetConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_ATTENTION_BUDGET_REPORT_CONFIG_VERSION
    )
    evidence_urgency_weight: Decimal = Decimal("0.350000")
    timing_risk_weight: Decimal = Decimal("0.250000")
    contradiction_pressure_weight: Decimal = Decimal("0.250000")
    domain_memory_gap_weight: Decimal = Decimal("0.150000")
    watch_attention_pressure_threshold: Decimal = Decimal("0.350000")
    block_attention_pressure_threshold: Decimal = Decimal("0.700000")
    watch_attention_share_threshold: Decimal = Decimal("0.250000")
    block_attention_share_threshold: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEventClusterAttentionBudgetConfig, "config")
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "evidence_urgency_weight",
            "timing_risk_weight",
            "contradiction_pressure_weight",
            "domain_memory_gap_weight",
            "watch_attention_pressure_threshold",
            "block_attention_pressure_threshold",
            "watch_attention_share_threshold",
            "block_attention_share_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if _sum_decimal(
            (
                self.evidence_urgency_weight,
                self.timing_risk_weight,
                self.contradiction_pressure_weight,
                self.domain_memory_gap_weight,
            ),
        ) != ONE:
            raise ValueError("attention weights must sum to 1.000000")
        _require_above(
            "block_attention_pressure_threshold",
            self.block_attention_pressure_threshold,
            self.watch_attention_pressure_threshold,
        )
        _require_above(
            "block_attention_share_threshold",
            self.block_attention_share_threshold,
            self.watch_attention_share_threshold,
        )
        _require_hard_phase_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEventClusterAttentionBudgetCluster(_FinalDataclass):
    cluster_ref: str
    evidence_urgency_score: Decimal
    timing_risk_score: Decimal
    contradiction_pressure_score: Decimal
    domain_memory_gap_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEventClusterAttentionBudgetCluster, "cluster")
        _require_private_reference("cluster_ref", self.cluster_ref)
        for field_name in (
            "evidence_urgency_score",
            "timing_risk_score",
            "contradiction_pressure_score",
            "domain_memory_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_phase_flags("cluster", self)


@dataclass(frozen=True)
class ResearchStrategyEventClusterAttentionBudgetRow(_FinalDataclass):
    row_number: Decimal
    evidence_urgency_score: Decimal
    timing_risk_score: Decimal
    contradiction_pressure_score: Decimal
    domain_memory_gap_score: Decimal
    evidence_urgency_weight: Decimal
    timing_risk_weight: Decimal
    contradiction_pressure_weight: Decimal
    domain_memory_gap_weight: Decimal
    attention_pressure: Decimal
    attention_share: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEventClusterAttentionBudgetRow, "row")
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        for field_name in (
            "evidence_urgency_score",
            "timing_risk_score",
            "contradiction_pressure_score",
            "domain_memory_gap_score",
            "evidence_urgency_weight",
            "timing_risk_weight",
            "contradiction_pressure_weight",
            "domain_memory_gap_weight",
            "attention_pressure",
            "attention_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if _sum_decimal(
            (
                self.evidence_urgency_weight,
                self.timing_risk_weight,
                self.contradiction_pressure_weight,
                self.domain_memory_gap_weight,
            ),
        ) != ONE:
            raise ValueError("attention weights must sum to 1.000000")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_digest("validation_digest", self.validation_digest)
        _validate_row(self)
        _require_hard_phase_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyEventClusterAttentionBudgetReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    cluster_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_attention_pressure: Decimal
    max_attention_pressure: Decimal | None
    average_attention_pressure: Decimal | None
    max_attention_share: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyEventClusterAttentionBudgetRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEventClusterAttentionBudgetReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in ("cluster_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_attention_pressure",
            _normalize_nonnegative_decimal(
                "total_attention_pressure",
                self.total_attention_pressure,
            ),
        )
        for field_name in (
            "max_attention_pressure",
            "average_attention_pressure",
            "max_attention_share",
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
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("report", self)
        _validate_report(self)


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


def build_research_strategy_event_cluster_attention_budget_report(
    clusters: Iterable[ResearchStrategyEventClusterAttentionBudgetCluster],
    *,
    config: ResearchStrategyEventClusterAttentionBudgetConfig,
    generated_at: datetime,
) -> ResearchStrategyEventClusterAttentionBudgetReport:
    if type(config) is not ResearchStrategyEventClusterAttentionBudgetConfig:
        raise ValueError("config must be a ResearchStrategyEventClusterAttentionBudgetConfig")
    _require_hard_phase_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_clusters = _normalize_clusters(clusters)
    base_rows = tuple(
        _base_row_from_cluster(cluster, config=config) for cluster in normalized_clusters
    )
    total_pressure = _sum_decimal(row["attention_pressure"] for row in base_rows)
    prepared_rows = tuple(
        sorted(
            (
                _prepared_row_with_share(
                    base_row,
                    total_attention_pressure=total_pressure,
                    config=config,
                )
                for base_row in base_rows
            ),
            key=_prepared_row_sort_key,
        ),
    )
    rows = tuple(
        _row_from_prepared(row_number=_count(index + 1), prepared=prepared)
        for index, prepared in enumerate(prepared_rows)
    )
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "cluster_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "total_attention_pressure": total_pressure,
        "max_attention_pressure": (
            None if not rows else max(row.attention_pressure for row in rows)
        ),
        "average_attention_pressure": _average_attention_pressure(rows),
        "max_attention_share": None if not rows else max(row.attention_share for row in rows),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyEventClusterAttentionBudgetReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_strategy_event_cluster_attention_budget_report_payload(
    report: ResearchStrategyEventClusterAttentionBudgetReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyEventClusterAttentionBudgetReport:
        _require_hard_phase_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyEventClusterAttentionBudgetReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload(payload)
    _require_hard_phase_flags("payload", _DictFlags(payload))
    _validate_payload_digests(payload)
    return payload


def research_strategy_event_cluster_attention_budget_report_digest(
    report: ResearchStrategyEventClusterAttentionBudgetReport,
) -> dict[str, Any]:
    payload = research_strategy_event_cluster_attention_budget_report_payload(report)
    return {key: payload[key] for key in SUMMARY_KEYS}


def _base_row_from_cluster(
    cluster: ResearchStrategyEventClusterAttentionBudgetCluster,
    *,
    config: ResearchStrategyEventClusterAttentionBudgetConfig,
) -> dict[str, Any]:
    attention_pressure = _attention_pressure(
        evidence_urgency_score=cluster.evidence_urgency_score,
        timing_risk_score=cluster.timing_risk_score,
        contradiction_pressure_score=cluster.contradiction_pressure_score,
        domain_memory_gap_score=cluster.domain_memory_gap_score,
        evidence_urgency_weight=config.evidence_urgency_weight,
        timing_risk_weight=config.timing_risk_weight,
        contradiction_pressure_weight=config.contradiction_pressure_weight,
        domain_memory_gap_weight=config.domain_memory_gap_weight,
    )
    return {
        "cluster_ref": cluster.cluster_ref,
        "evidence_urgency_score": cluster.evidence_urgency_score,
        "timing_risk_score": cluster.timing_risk_score,
        "contradiction_pressure_score": cluster.contradiction_pressure_score,
        "domain_memory_gap_score": cluster.domain_memory_gap_score,
        "evidence_urgency_weight": config.evidence_urgency_weight,
        "timing_risk_weight": config.timing_risk_weight,
        "contradiction_pressure_weight": config.contradiction_pressure_weight,
        "domain_memory_gap_weight": config.domain_memory_gap_weight,
        "attention_pressure": attention_pressure,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _prepared_row_with_share(
    base_row: dict[str, Any],
    *,
    total_attention_pressure: Decimal,
    config: ResearchStrategyEventClusterAttentionBudgetConfig,
) -> dict[str, Any]:
    attention_share = (
        ZERO
        if total_attention_pressure == ZERO
        else _ratio(base_row["attention_pressure"], total_attention_pressure)
    )
    reason_codes = _row_reason_codes(
        attention_pressure=base_row["attention_pressure"],
        attention_share=attention_share,
        config=config,
    )
    return {
        **base_row,
        "attention_share": attention_share,
        "status": _row_status(reason_codes),
        "reason_codes": reason_codes,
    }


def _row_from_prepared(
    *,
    row_number: Decimal,
    prepared: dict[str, Any],
) -> ResearchStrategyEventClusterAttentionBudgetRow:
    row_values = {
        key: value for key, value in prepared.items() if key != "cluster_ref"
    }
    row_values["row_number"] = row_number
    return ResearchStrategyEventClusterAttentionBudgetRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )


def _attention_pressure(
    *,
    evidence_urgency_score: Decimal,
    timing_risk_score: Decimal,
    contradiction_pressure_score: Decimal,
    domain_memory_gap_score: Decimal,
    evidence_urgency_weight: Decimal,
    timing_risk_weight: Decimal,
    contradiction_pressure_weight: Decimal,
    domain_memory_gap_weight: Decimal,
) -> Decimal:
    return _sum_decimal(
        (
            _multiply_decimal(evidence_urgency_score, evidence_urgency_weight),
            _multiply_decimal(timing_risk_score, timing_risk_weight),
            _multiply_decimal(
                contradiction_pressure_score,
                contradiction_pressure_weight,
            ),
            _multiply_decimal(domain_memory_gap_score, domain_memory_gap_weight),
        ),
    )


def _row_reason_codes(
    *,
    attention_pressure: Decimal,
    attention_share: Decimal,
    config: ResearchStrategyEventClusterAttentionBudgetConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_threshold_reason(
        reasons,
        metric=attention_share,
        watch_threshold=config.watch_attention_share_threshold,
        block_threshold=config.block_attention_share_threshold,
        watch_reason="attention_share_watch",
        block_reason="attention_share_block",
    )
    _append_threshold_reason(
        reasons,
        metric=attention_pressure,
        watch_threshold=config.watch_attention_pressure_threshold,
        block_threshold=config.block_attention_pressure_threshold,
        watch_reason="attention_pressure_watch",
        block_reason="attention_pressure_block",
    )
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes(tuple(reasons))


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


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchStrategyEventClusterAttentionBudgetRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyEventClusterAttentionBudgetRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CLUSTERS_REASON,)
    values = tuple(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != PASS_REASON
    )
    if not values:
        return (PASS_REASON,)
    return _normalize_reason_codes(values)


def _normalize_clusters(
    clusters: Iterable[ResearchStrategyEventClusterAttentionBudgetCluster],
) -> tuple[ResearchStrategyEventClusterAttentionBudgetCluster, ...]:
    if isinstance(clusters, (str, bytes)):
        raise ValueError("clusters must be an iterable")
    try:
        values = tuple(clusters)
    except TypeError as exc:
        raise ValueError("clusters must be an iterable") from exc
    seen: set[str] = set()
    for cluster in values:
        if type(cluster) is not ResearchStrategyEventClusterAttentionBudgetCluster:
            raise ValueError(
                "clusters must contain ResearchStrategyEventClusterAttentionBudgetCluster",
            )
        _require_hard_phase_flags("cluster", cluster)
        if cluster.cluster_ref in seen:
            raise ValueError("cluster_ref values must be unique")
        seen.add(cluster.cluster_ref)
    return values


def _normalize_rows(
    rows: Iterable[ResearchStrategyEventClusterAttentionBudgetRow],
) -> tuple[ResearchStrategyEventClusterAttentionBudgetRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    expected_row_number = ONE
    for row in values:
        if type(row) is not ResearchStrategyEventClusterAttentionBudgetRow:
            raise ValueError("rows must contain ResearchStrategyEventClusterAttentionBudgetRow")
        _require_hard_phase_flags("row", row)
        if row.row_number != expected_row_number:
            raise ValueError("rows must be sorted deterministically")
        expected_row_number = _quantize(expected_row_number + ONE)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return values


def _validate_row(row: ResearchStrategyEventClusterAttentionBudgetRow) -> None:
    expected_pressure = _attention_pressure(
        evidence_urgency_score=row.evidence_urgency_score,
        timing_risk_score=row.timing_risk_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
        domain_memory_gap_score=row.domain_memory_gap_score,
        evidence_urgency_weight=row.evidence_urgency_weight,
        timing_risk_weight=row.timing_risk_weight,
        contradiction_pressure_weight=row.contradiction_pressure_weight,
        domain_memory_gap_weight=row.domain_memory_gap_weight,
    )
    if row.attention_pressure != expected_pressure:
        raise ValueError("attention_pressure must match component scores")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.validation_digest != _validation_digest(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_report(report: ResearchStrategyEventClusterAttentionBudgetReport) -> None:
    if report.cluster_count != _count(len(report.rows)):
        raise ValueError("cluster_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.total_attention_pressure != _sum_decimal(
        row.attention_pressure for row in report.rows
    ):
        raise ValueError("total_attention_pressure must match rows")
    expected_max_pressure = (
        None if not report.rows else max(row.attention_pressure for row in report.rows)
    )
    if report.max_attention_pressure != expected_max_pressure:
        raise ValueError("max_attention_pressure must match rows")
    if report.average_attention_pressure != _average_attention_pressure(report.rows):
        raise ValueError("average_attention_pressure must match rows")
    expected_max_share = None if not report.rows else max(row.attention_share for row in report.rows)
    if report.max_attention_share != expected_max_share:
        raise ValueError("max_attention_share must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _validate_payload_digests(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        row_digest = row.get("validation_digest")
        _require_digest("row validation_digest", row_digest)
        if row_digest != _digest_json_ready_values(_require_keys(row, ROW_DIGEST_KEYS)):
            raise ValueError("validation_digest must match row payload")
    report_digest = payload.get("validation_digest")
    _require_digest("validation_digest", report_digest)
    if report_digest != _digest_json_ready_values(
        _require_keys(payload, REPORT_DIGEST_KEYS),
    ):
        raise ValueError("validation_digest must match report payload")


def _require_keys(value: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    missing = tuple(key for key in keys if key not in value)
    if missing:
        raise ValueError("payload is missing required keys")
    return {key: value[key] for key in keys}


def _row_digest_values(row: ResearchStrategyEventClusterAttentionBudgetRow) -> dict[str, Any]:
    return {key: getattr(row, key) for key in ROW_DIGEST_KEYS}


def _report_digest_values(
    report: ResearchStrategyEventClusterAttentionBudgetReport,
) -> dict[str, Any]:
    return {key: getattr(report, key) for key in REPORT_DIGEST_KEYS}


def _prepared_row_sort_key(prepared: dict[str, Any]) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[prepared["status"]],
        ONE - prepared["attention_share"],
        ONE - prepared["attention_pressure"],
        prepared["cluster_ref"],
    )


def _row_sort_key(
    row: ResearchStrategyEventClusterAttentionBudgetRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    return (
        STATUS_WEIGHT[row.status],
        ONE - row.attention_share,
        ONE - row.attention_pressure,
        row.row_number,
    )


def _status_count(
    rows: tuple[ResearchStrategyEventClusterAttentionBudgetRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_attention_pressure(
    rows: tuple[ResearchStrategyEventClusterAttentionBudgetRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _ratio(_sum_decimal(row.attention_pressure for row in rows), _count(len(rows)))


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_public_text("reason_codes", reason_code)
        compact = "".join(part for part in reason_code if part != "_")
        if not compact.isalnum() or reason_code.lower() != reason_code:
            raise ValueError("reason_codes must be lowercase snake case")
    normalized = tuple(sorted(dict.fromkeys(reason_codes), key=_reason_sort_key))
    if PASS_REASON in normalized and len(normalized) != 1:
        raise ValueError("attention_budget_pass must stand alone")
    if NO_CLUSTERS_REASON in normalized and len(normalized) != 1:
        raise ValueError("no clusters reason must stand alone")
    return normalized


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in REASON_PRIORITY:
        return (REASON_PRIORITY.index(reason_code), reason_code)
    return (len(REASON_PRIORITY), reason_code)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += _normalize_decimal("sum value", value)
    return _quantize(total)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    left = _normalize_decimal("left", left)
    right = _normalize_decimal("right", right)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(normalized)


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized > ONE:
        raise ValueError(f"{name} must be no greater than 1.000000")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_above(name: str, value: Decimal, floor: Decimal) -> None:
    if value <= floor:
        raise ValueError(f"{name} must exceed its paired watch threshold")


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_private_reference(name: str, value: object) -> None:
    _require_text(name, value)


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")


def _require_digest(name: str, value: object) -> None:
    _require_text(name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_hard_phase_flags(name: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _validation_digest(values: dict[str, Any]) -> str:
    return _digest_json_ready_values(_json_ready(values))


def _digest_json_ready_values(values: dict[str, Any]) -> str:
    encoded = json.dumps(values, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _require_public_text("payload key", key)
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if type(value) is str:
        _require_public_text("payload value", value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("payload contains unsupported value")
