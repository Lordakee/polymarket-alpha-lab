"""Pure report-only clustering for research strategy candidate events."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_CANDIDATE_CLUSTER_CONFIG_VERSION = (
    "research-strategy-candidate-cluster-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_DEPENDENCY_BANDS = frozenset(("independent", "dependent_watch", "dependent_block"))
_PROBABILITY_GAP_BANDS = frozenset(("aligned", "divergent_watch", "divergent_block"))
_RULE_RISK_BANDS = frozenset(("low", "rule_watch", "rule_block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "raw id",
    "raw_id",
    "raw-id",
    "rawid",
    "source",
    "market",
    "dsn",
    "table",
    "token",
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
    "position",
    "recommend",
)
_REASON_CODE_SEQUENCE = (
    "empty_observations",
    "sparse_cluster_block",
    "dependency_watch",
    "dependency_block",
    "probability_gap_watch",
    "probability_gap_block",
    "rule_risk_watch",
    "rule_risk_block",
    "confidence_watch",
    "confidence_block",
    "cluster_pass",
)


@dataclass(frozen=True)
class ResearchStrategyCandidateClusterConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_CANDIDATE_CLUSTER_CONFIG_VERSION
    min_events_per_cluster: Decimal = Decimal("1.000000")
    watch_dependency_score: Decimal = Decimal("0.350000")
    block_dependency_score: Decimal = Decimal("0.700000")
    watch_probability_gap: Decimal = Decimal("0.100000")
    block_probability_gap: Decimal = Decimal("0.300000")
    watch_rule_risk_score: Decimal = Decimal("0.250000")
    block_rule_risk_score: Decimal = Decimal("0.700000")
    watch_confidence_score: Decimal = Decimal("0.500000")
    block_confidence_score: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCandidateClusterConfig:
            raise TypeError(
                "ResearchStrategyCandidateClusterConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateClusterConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyCandidateClusterConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_STRATEGY_CANDIDATE_CLUSTER_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_events_per_cluster",
            _require_positive_count_decimal(
                "min_events_per_cluster",
                self.min_events_per_cluster,
            ),
        )
        for field_name in (
            "watch_dependency_score",
            "block_dependency_score",
            "watch_probability_gap",
            "block_probability_gap",
            "watch_rule_risk_score",
            "block_rule_risk_score",
            "watch_confidence_score",
            "block_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_ordered_thresholds(
            "dependency_score",
            self.watch_dependency_score,
            self.block_dependency_score,
        )
        _require_ordered_thresholds(
            "probability_gap",
            self.watch_probability_gap,
            self.block_probability_gap,
        )
        _require_ordered_thresholds(
            "rule_risk_score",
            self.watch_rule_risk_score,
            self.block_rule_risk_score,
        )
        if self.block_confidence_score > self.watch_confidence_score:
            raise ValueError("block_confidence_score must not exceed watch_confidence_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateClusterObservation:
    candidate_reference: str
    event_domain: str
    settlement_window: str
    observed_at: datetime
    evidence_dependency_score: Decimal
    candidate_probability: Decimal
    research_probability: Decimal
    rule_risk_score: Decimal
    confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCandidateClusterObservation:
            raise TypeError(
                "ResearchStrategyCandidateClusterObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateClusterObservation:
            raise ValueError(
                "observation must be exactly ResearchStrategyCandidateClusterObservation",
            )
        for field_name in ("candidate_reference", "event_domain", "settlement_window"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "evidence_dependency_score",
            "candidate_probability",
            "research_probability",
            "rule_risk_score",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateClusterPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCandidateClusterPublicPayloadItem:
            raise TypeError(
                "ResearchStrategyCandidateClusterPublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateClusterPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchStrategyCandidateClusterPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateClusterRow:
    event_domain: str
    settlement_window: str
    dependency_band: str
    probability_gap_band: str
    rule_risk_band: str
    event_count: Decimal
    average_dependency_score: Decimal
    average_probability_gap: Decimal
    max_probability_gap: Decimal
    average_rule_risk_score: Decimal
    average_confidence_score: Decimal
    cluster_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCandidateClusterRow:
            raise TypeError(
                "ResearchStrategyCandidateClusterRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateClusterRow:
            raise ValueError("row must be exactly ResearchStrategyCandidateClusterRow")
        _require_public_identifier("event_domain", self.event_domain)
        _require_public_identifier("settlement_window", self.settlement_window)
        _require_enum("dependency_band", self.dependency_band, _DEPENDENCY_BANDS)
        _require_enum(
            "probability_gap_band",
            self.probability_gap_band,
            _PROBABILITY_GAP_BANDS,
        )
        _require_enum("rule_risk_band", self.rule_risk_band, _RULE_RISK_BANDS)
        object.__setattr__(
            self,
            "event_count",
            _require_positive_count_decimal("event_count", self.event_count),
        )
        for field_name in (
            "average_dependency_score",
            "average_probability_gap",
            "max_probability_gap",
            "average_rule_risk_score",
            "average_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("cluster_status", self.cluster_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateClusterReport:
    generated_at: datetime
    config_version: str
    cluster_status: str
    cluster_count: Decimal
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_dependency_score: Decimal
    average_probability_gap: Decimal
    average_rule_risk_score: Decimal
    rows: tuple[ResearchStrategyCandidateClusterRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchStrategyCandidateClusterPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCandidateClusterReport:
            raise TypeError(
                "ResearchStrategyCandidateClusterReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateClusterReport:
            raise ValueError(
                "report must be exactly ResearchStrategyCandidateClusterReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_STRATEGY_CANDIDATE_CLUSTER_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("cluster_status", self.cluster_status)
        for field_name in (
            "cluster_count",
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_dependency_score",
            "average_probability_gap",
            "average_rule_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchStrategyCandidateClusterReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_strategy_candidate_cluster_report(
    observations: Sequence[ResearchStrategyCandidateClusterObservation],
    *,
    generated_at: datetime,
    config: ResearchStrategyCandidateClusterConfig | None = None,
    public_payload: Sequence[ResearchStrategyCandidateClusterPublicPayloadItem] = (),
) -> ResearchStrategyCandidateClusterReport:
    """Build a local paper-only cluster report for caller-supplied observations."""

    if config is None:
        config = ResearchStrategyCandidateClusterConfig()
    if type(config) is not ResearchStrategyCandidateClusterConfig:
        raise ValueError("config must be a ResearchStrategyCandidateClusterConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at:
            raise ValueError("observation observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_observations, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "cluster_status": _report_status(rows),
        "cluster_count": _decimal_count(len(rows)),
        "event_count": sum((row.event_count for row in rows), _ZERO),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_dependency_score": _weighted_row_average(
            rows,
            "average_dependency_score",
        ),
        "average_probability_gap": _weighted_row_average(
            rows,
            "average_probability_gap",
        ),
        "average_rule_risk_score": _weighted_row_average(
            rows,
            "average_rule_risk_score",
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyCandidateClusterReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_candidate_cluster_report_payload(
    value: ResearchStrategyCandidateClusterReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyCandidateClusterReport:
        _require_hard_flags("report", value)
        payload = value.payload
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyCandidateClusterReport or dict",
        )
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


def _build_rows(
    observations: tuple[ResearchStrategyCandidateClusterObservation, ...],
    config: ResearchStrategyCandidateClusterConfig,
) -> tuple[ResearchStrategyCandidateClusterRow, ...]:
    grouped: dict[tuple[str, str, str, str, str], list[ResearchStrategyCandidateClusterObservation]]
    grouped = {}
    for observation in observations:
        probability_gap = _abs_decimal(
            observation.candidate_probability - observation.research_probability,
        )
        key = (
            observation.event_domain,
            observation.settlement_window,
            _dependency_band(observation.evidence_dependency_score, config),
            _probability_gap_band(probability_gap, config),
            _rule_risk_band(observation.rule_risk_score, config),
        )
        grouped.setdefault(key, []).append(observation)
    rows = [
        _row_for_cluster(key, tuple(items), config)
        for key, items in sorted(grouped.items())
    ]
    return tuple(rows)


def _row_for_cluster(
    key: tuple[str, str, str, str, str],
    observations: tuple[ResearchStrategyCandidateClusterObservation, ...],
    config: ResearchStrategyCandidateClusterConfig,
) -> ResearchStrategyCandidateClusterRow:
    (
        event_domain,
        settlement_window,
        dependency_band,
        probability_gap_band,
        rule_risk_band,
    ) = key
    probability_gaps = tuple(
        _abs_decimal(
            observation.candidate_probability - observation.research_probability,
        )
        for observation in observations
    )
    event_count = _decimal_count(len(observations))
    average_dependency = _average(
        tuple(observation.evidence_dependency_score for observation in observations),
    )
    average_probability_gap = _average(probability_gaps)
    max_probability_gap = max(probability_gaps, default=_ZERO)
    average_rule_risk = _average(
        tuple(observation.rule_risk_score for observation in observations),
    )
    average_confidence = _average(
        tuple(observation.confidence_score for observation in observations),
    )
    cluster_status = _row_status(
        event_count=event_count,
        dependency_band=dependency_band,
        probability_gap_band=probability_gap_band,
        rule_risk_band=rule_risk_band,
        average_confidence_score=average_confidence,
        config=config,
    )
    reason_codes = _row_reason_codes(
        event_count=event_count,
        dependency_band=dependency_band,
        probability_gap_band=probability_gap_band,
        rule_risk_band=rule_risk_band,
        average_confidence_score=average_confidence,
        cluster_status=cluster_status,
        config=config,
    )
    return ResearchStrategyCandidateClusterRow(
        event_domain=event_domain,
        settlement_window=settlement_window,
        dependency_band=dependency_band,
        probability_gap_band=probability_gap_band,
        rule_risk_band=rule_risk_band,
        event_count=event_count,
        average_dependency_score=average_dependency,
        average_probability_gap=average_probability_gap,
        max_probability_gap=max_probability_gap,
        average_rule_risk_score=average_rule_risk,
        average_confidence_score=average_confidence,
        cluster_status=cluster_status,
        reason_codes=reason_codes,
    )


def _dependency_band(
    evidence_dependency_score: Decimal,
    config: ResearchStrategyCandidateClusterConfig,
) -> str:
    if evidence_dependency_score >= config.block_dependency_score:
        return "dependent_block"
    if evidence_dependency_score >= config.watch_dependency_score:
        return "dependent_watch"
    return "independent"


def _probability_gap_band(
    probability_gap: Decimal,
    config: ResearchStrategyCandidateClusterConfig,
) -> str:
    if probability_gap >= config.block_probability_gap:
        return "divergent_block"
    if probability_gap >= config.watch_probability_gap:
        return "divergent_watch"
    return "aligned"


def _rule_risk_band(
    rule_risk_score: Decimal,
    config: ResearchStrategyCandidateClusterConfig,
) -> str:
    if rule_risk_score >= config.block_rule_risk_score:
        return "rule_block"
    if rule_risk_score >= config.watch_rule_risk_score:
        return "rule_watch"
    return "low"


def _row_status(
    *,
    event_count: Decimal,
    dependency_band: str,
    probability_gap_band: str,
    rule_risk_band: str,
    average_confidence_score: Decimal,
    config: ResearchStrategyCandidateClusterConfig,
) -> str:
    if event_count < config.min_events_per_cluster:
        return "block"
    if (
        dependency_band == "dependent_block"
        or probability_gap_band == "divergent_block"
        or rule_risk_band == "rule_block"
        or average_confidence_score <= config.block_confidence_score
    ):
        return "block"
    if (
        dependency_band == "dependent_watch"
        or probability_gap_band == "divergent_watch"
        or rule_risk_band == "rule_watch"
        or average_confidence_score <= config.watch_confidence_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    event_count: Decimal,
    dependency_band: str,
    probability_gap_band: str,
    rule_risk_band: str,
    average_confidence_score: Decimal,
    cluster_status: str,
    config: ResearchStrategyCandidateClusterConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if event_count < config.min_events_per_cluster:
        reason_codes.append("sparse_cluster_block")
    if dependency_band == "dependent_block":
        reason_codes.append("dependency_block")
    elif dependency_band == "dependent_watch":
        reason_codes.append("dependency_watch")
    if probability_gap_band == "divergent_block":
        reason_codes.append("probability_gap_block")
    elif probability_gap_band == "divergent_watch":
        reason_codes.append("probability_gap_watch")
    if rule_risk_band == "rule_block":
        reason_codes.append("rule_risk_block")
    elif rule_risk_band == "rule_watch":
        reason_codes.append("rule_risk_watch")
    if average_confidence_score <= config.block_confidence_score:
        reason_codes.append("confidence_block")
    elif average_confidence_score <= config.watch_confidence_score:
        reason_codes.append("confidence_watch")
    if cluster_status == "pass":
        reason_codes.append("cluster_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchStrategyCandidateClusterRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.cluster_status == "block" for row in rows):
        return "block"
    if any(row.cluster_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyCandidateClusterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchStrategyCandidateClusterRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.cluster_status == status))


def _weighted_row_average(
    rows: tuple[ResearchStrategyCandidateClusterRow, ...],
    field_name: str,
) -> Decimal:
    event_count = sum((row.event_count for row in rows), _ZERO)
    if event_count == _ZERO:
        return _ZERO
    total = sum((getattr(row, field_name) * row.event_count for row in rows), _ZERO)
    return _quantize(total / event_count)


def _validate_row_consistency(row: ResearchStrategyCandidateClusterRow) -> None:
    if row.cluster_status == "pass" and row.reason_codes != ("cluster_pass",):
        raise ValueError("pass rows must only include cluster_pass")
    if row.cluster_status == "watch" and not any(
        code.endswith("_watch") for code in row.reason_codes
    ):
        raise ValueError("watch rows must include a watch reason code")
    if row.cluster_status == "block" and not any(
        code.endswith("_block") for code in row.reason_codes
    ):
        raise ValueError("block rows must include a block reason code")


def _validate_report_consistency(report: ResearchStrategyCandidateClusterReport) -> None:
    if report.cluster_count != _decimal_count(len(report.rows)):
        raise ValueError("cluster_count must match rows")
    if report.event_count != sum((row.event_count for row in report.rows), _ZERO):
        raise ValueError("event_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_dependency_score != _weighted_row_average(
        report.rows,
        "average_dependency_score",
    ):
        raise ValueError("average_dependency_score must match rows")
    if report.average_probability_gap != _weighted_row_average(
        report.rows,
        "average_probability_gap",
    ):
        raise ValueError("average_probability_gap must match rows")
    if report.average_rule_risk_score != _weighted_row_average(
        report.rows,
        "average_rule_risk_score",
    ):
        raise ValueError("average_rule_risk_score must match rows")
    if report.cluster_status != _report_status(report.rows):
        raise ValueError("cluster_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Sequence[ResearchStrategyCandidateClusterObservation],
) -> tuple[ResearchStrategyCandidateClusterObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchStrategyCandidateClusterObservation] = []
    seen: set[str] = set()
    for observation in observations:
        if type(observation) is not ResearchStrategyCandidateClusterObservation:
            raise ValueError(
                "observations must contain ResearchStrategyCandidateClusterObservation",
            )
        if observation.candidate_reference in seen:
            raise ValueError("candidate_reference must be unique")
        seen.add(observation.candidate_reference)
        normalized.append(observation)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.event_domain,
                item.settlement_window,
                item.candidate_reference,
                item.observed_at,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchStrategyCandidateClusterRow],
) -> tuple[ResearchStrategyCandidateClusterRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchStrategyCandidateClusterRow] = []
    for row in rows:
        if type(row) is not ResearchStrategyCandidateClusterRow:
            raise ValueError("rows must contain ResearchStrategyCandidateClusterRow")
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                row.event_domain,
                row.settlement_window,
                row.dependency_band,
                row.probability_gap_band,
                row.rule_risk_band,
            ),
        ),
    )


def _normalize_public_payload(
    public_payload: Sequence[ResearchStrategyCandidateClusterPublicPayloadItem],
) -> tuple[ResearchStrategyCandidateClusterPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchStrategyCandidateClusterPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchStrategyCandidateClusterPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "ResearchStrategyCandidateClusterPublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_enum(field_name: str, value: object, allowed: frozenset[str]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a supported value")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be a known status")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_ordered_thresholds(
    label: str,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if block_threshold < watch_threshold:
        raise ValueError(f"block {label} threshold must not be below watch threshold")


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _abs_decimal(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchStrategyCandidateClusterReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
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


def _copy_json_object(value: Mapping[str, object]) -> dict[str, object]:
    copied = _json_ready(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _validate_public_payload_digest(payload: Mapping[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    if digest != _report_digest_from_values(values):
        raise ValueError("derived_validation_digest does not match report payload")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
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
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_CLUSTER_CONFIG_VERSION",
    "ResearchStrategyCandidateClusterConfig",
    "ResearchStrategyCandidateClusterObservation",
    "ResearchStrategyCandidateClusterPublicPayloadItem",
    "ResearchStrategyCandidateClusterReport",
    "ResearchStrategyCandidateClusterRow",
    "build_research_strategy_candidate_cluster_report",
    "research_strategy_candidate_cluster_report_payload",
)
