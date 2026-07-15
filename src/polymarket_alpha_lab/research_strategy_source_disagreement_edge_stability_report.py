"""Pure source disagreement edge stability report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_SOURCE_DISAGREEMENT_EDGE_STABILITY_REPORT_CONFIG_VERSION = (
    "research-strategy-source-disagreement-edge-stability-report-v0"
)
RESEARCH_STRATEGY_SOURCE_DISAGREEMENT_EDGE_STABILITY_STATUSES = (
    "pass",
    "watch",
    "block",
)

DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PRIVATE_ROW_FIELDS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "source_url",
    "source_text",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "source_url",
    "source_text",
    "slug",
    "raw",
    "private",
    "://",
    "?",
    "dsn",
    "table",
    "token",
    "credential",
    "secret",
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("trad", "ing"),
    _join_parts("li", "ve"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("reco", "mmendation"),
    _join_parts("siz", "ing"),
    _join_parts("b", "uy"),
    _join_parts("se", "ll"),
)

ROW_REASON_CODES = (
    "authority_conflict_pressure_block",
    "authority_conflict_pressure_watch",
    "source_freshness_block",
    "source_freshness_watch",
    "corroboration_block",
    "corroboration_watch",
    "edge_persistence_block",
    "edge_persistence_watch",
    "edge_drift_block",
    "edge_drift_watch",
    "market_cost_pressure_block",
    "market_cost_pressure_watch",
    "composite_stability_block",
    "composite_stability_watch",
    "source_disagreement_edge_stability_pass",
)
REPORT_REASON_CODES = (
    "source_disagreement_edge_stability_report_block",
    "source_disagreement_edge_stability_report_watch",
    "source_disagreement_edge_stability_report_pass",
    "source_disagreement_edge_stability_report_empty",
    "authority_conflict_pressure_review",
    "source_freshness_review",
    "corroboration_review",
    "edge_persistence_review",
    "edge_drift_review",
    "market_cost_pressure_review",
    "composite_stability_review",
)
REPORT_PUBLIC_PAYLOAD_KEYS = frozenset(
    {
        "generated_at",
        "config_version",
        "source_row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_authority_weighted_conflict_pressure",
        "mean_edge_stability_score",
        "mean_market_cost_pressure_score",
        "mean_disagreement_edge_stability_score",
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
ROW_PUBLIC_PAYLOAD_KEYS = frozenset(
    {
        "row_number",
        "observed_at",
        "source_disagreement_probability",
        "source_authority_weight",
        "authority_weighted_conflict_pressure",
        "source_freshness_score",
        "independent_corroboration_score",
        "current_edge_probability",
        "prior_edge_probability",
        "edge_drift_probability",
        "edge_persistence_score",
        "edge_stability_score",
        "market_cost_pressure_score",
        "disagreement_edge_stability_score",
        "status",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    },
)
REASON_CODE_COUNT_PUBLIC_PAYLOAD_KEYS = frozenset(
    {
        "reason_code",
        "count",
        "input_ratio",
        "paper_only",
        "report_only",
        "readonly",
    },
)


@dataclass(frozen=True)
class ResearchStrategySourceDisagreementEdgeStabilityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_SOURCE_DISAGREEMENT_EDGE_STABILITY_REPORT_CONFIG_VERSION
    )
    max_authority_conflict_pass_pressure: Decimal = Decimal("0.200000")
    max_authority_conflict_watch_pressure: Decimal = Decimal("0.450000")
    min_source_freshness_pass_score: Decimal = Decimal("0.750000")
    min_source_freshness_watch_score: Decimal = Decimal("0.500000")
    min_corroboration_pass_score: Decimal = Decimal("0.700000")
    min_corroboration_watch_score: Decimal = Decimal("0.450000")
    min_edge_persistence_pass_score: Decimal = Decimal("0.700000")
    min_edge_persistence_watch_score: Decimal = Decimal("0.400000")
    max_edge_drift_pass_probability: Decimal = Decimal("0.050000")
    max_edge_drift_watch_probability: Decimal = Decimal("0.150000")
    max_market_cost_pass_pressure: Decimal = Decimal("0.300000")
    max_market_cost_watch_pressure: Decimal = Decimal("0.650000")
    composite_pass_floor: Decimal = Decimal("0.700000")
    composite_watch_floor: Decimal = Decimal("0.450000")
    authority_conflict_weight: Decimal = Decimal("1.000000")
    freshness_weight: Decimal = Decimal("1.000000")
    corroboration_weight: Decimal = Decimal("1.000000")
    edge_persistence_weight: Decimal = Decimal("1.000000")
    market_cost_weight: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategySourceDisagreementEdgeStabilityConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchStrategySourceDisagreementEdgeStabilityConfig,
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_DISAGREEMENT_EDGE_STABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "max_authority_conflict_pass_pressure",
            "max_authority_conflict_watch_pressure",
            "min_source_freshness_pass_score",
            "min_source_freshness_watch_score",
            "min_corroboration_pass_score",
            "min_corroboration_watch_score",
            "min_edge_persistence_pass_score",
            "min_edge_persistence_watch_score",
            "max_edge_drift_pass_probability",
            "max_edge_drift_watch_probability",
            "max_market_cost_pass_pressure",
            "max_market_cost_watch_pressure",
            "composite_pass_floor",
            "composite_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_conflict_weight",
            "freshness_weight",
            "corroboration_weight",
            "edge_persistence_weight",
            "market_cost_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_ceiling_pair(
            "max_authority_conflict",
            self.max_authority_conflict_pass_pressure,
            self.max_authority_conflict_watch_pressure,
            pass_field_name="max_authority_conflict_pass_pressure",
        )
        _require_floor_pair(
            "min_source_freshness",
            self.min_source_freshness_pass_score,
            self.min_source_freshness_watch_score,
            pass_field_name="min_source_freshness_pass_score",
        )
        _require_floor_pair(
            "min_corroboration",
            self.min_corroboration_pass_score,
            self.min_corroboration_watch_score,
            pass_field_name="min_corroboration_pass_score",
        )
        _require_floor_pair(
            "min_edge_persistence",
            self.min_edge_persistence_pass_score,
            self.min_edge_persistence_watch_score,
            pass_field_name="min_edge_persistence_pass_score",
        )
        _require_ceiling_pair(
            "max_edge_drift",
            self.max_edge_drift_pass_probability,
            self.max_edge_drift_watch_probability,
            pass_field_name="max_edge_drift_pass_probability",
        )
        _require_ceiling_pair(
            "max_market_cost",
            self.max_market_cost_pass_pressure,
            self.max_market_cost_watch_pressure,
            pass_field_name="max_market_cost_pass_pressure",
        )
        _require_floor_pair(
            "composite",
            self.composite_pass_floor,
            self.composite_watch_floor,
            pass_field_name="composite_pass_floor",
        )
        if _sum_decimals(_config_weights(self)) == ZERO:
            raise ValueError("weight values must include at least one positive weight")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategySourceDisagreementEdgeStabilityInput:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    observed_at: datetime
    source_disagreement_probability: Decimal
    source_authority_weight: Decimal
    source_freshness_score: Decimal
    independent_corroboration_score: Decimal
    current_edge_probability: Decimal
    prior_edge_probability: Decimal
    edge_persistence_score: Decimal
    market_cost_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategySourceDisagreementEdgeStabilityInput "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchStrategySourceDisagreementEdgeStabilityInput,
        )
        for field_name in PRIVATE_ROW_FIELDS:
            _require_private_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_disagreement_probability",
            "source_authority_weight",
            "source_freshness_score",
            "independent_corroboration_score",
            "current_edge_probability",
            "prior_edge_probability",
            "edge_persistence_score",
            "market_cost_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategySourceDisagreementEdgeStabilityReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategySourceDisagreementEdgeStabilityReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchStrategySourceDisagreementEdgeStabilityReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code, ROW_REASON_CODES)
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
class ResearchStrategySourceDisagreementEdgeStabilityRow:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    observed_at: datetime
    source_disagreement_probability: Decimal
    source_authority_weight: Decimal
    authority_weighted_conflict_pressure: Decimal
    source_freshness_score: Decimal
    independent_corroboration_score: Decimal
    current_edge_probability: Decimal
    prior_edge_probability: Decimal
    edge_drift_probability: Decimal
    edge_persistence_score: Decimal
    edge_stability_score: Decimal
    market_cost_pressure_score: Decimal
    disagreement_edge_stability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategySourceDisagreementEdgeStabilityRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "row",
            self,
            ResearchStrategySourceDisagreementEdgeStabilityRow,
        )
        for field_name in PRIVATE_ROW_FIELDS:
            _require_private_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_disagreement_probability",
            "source_authority_weight",
            "authority_weighted_conflict_pressure",
            "source_freshness_score",
            "independent_corroboration_score",
            "current_edge_probability",
            "prior_edge_probability",
            "edge_drift_probability",
            "edge_persistence_score",
            "edge_stability_score",
            "market_cost_pressure_score",
            "disagreement_edge_stability_score",
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
class ResearchStrategySourceDisagreementEdgeStabilityReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_authority_weighted_conflict_pressure: Decimal
    mean_edge_stability_score: Decimal
    mean_market_cost_pressure_score: Decimal
    mean_disagreement_edge_stability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategySourceDisagreementEdgeStabilityReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategySourceDisagreementEdgeStabilityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategySourceDisagreementEdgeStabilityReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchStrategySourceDisagreementEdgeStabilityReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_DISAGREEMENT_EDGE_STABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "source_row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_authority_weighted_conflict_pressure",
            "mean_edge_stability_score",
            "mean_market_cost_pressure_score",
            "mean_disagreement_edge_stability_score",
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


def build_research_strategy_source_disagreement_edge_stability_report(
    inputs: Iterable[ResearchStrategySourceDisagreementEdgeStabilityInput],
    *,
    config: ResearchStrategySourceDisagreementEdgeStabilityConfig,
    generated_at: datetime,
) -> ResearchStrategySourceDisagreementEdgeStabilityReport:
    if type(config) is not ResearchStrategySourceDisagreementEdgeStabilityConfig:
        raise ValueError(
            "config must be a ResearchStrategySourceDisagreementEdgeStabilityConfig",
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
    return ResearchStrategySourceDisagreementEdgeStabilityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_authority_weighted_conflict_pressure=_mean(
            tuple(row.authority_weighted_conflict_pressure for row in rows),
        ),
        mean_edge_stability_score=_mean(
            tuple(row.edge_stability_score for row in rows),
        ),
        mean_market_cost_pressure_score=_mean(
            tuple(row.market_cost_pressure_score for row in rows),
        ),
        mean_disagreement_edge_stability_score=_mean(
            tuple(row.disagreement_edge_stability_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_source_disagreement_edge_stability_report_payload(
    report: ResearchStrategySourceDisagreementEdgeStabilityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategySourceDisagreementEdgeStabilityReport:
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
            "report must be a ResearchStrategySourceDisagreementEdgeStabilityReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _public_report_payload(
    report: ResearchStrategySourceDisagreementEdgeStabilityReport,
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
    row: ResearchStrategySourceDisagreementEdgeStabilityRow,
) -> dict[str, Any]:
    payload = asdict(row)
    for field_name in PRIVATE_ROW_FIELDS:
        payload.pop(field_name, None)
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
        allow_nan=False,
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
    value: ResearchStrategySourceDisagreementEdgeStabilityInput,
    *,
    config: ResearchStrategySourceDisagreementEdgeStabilityConfig,
    generated_at: datetime,
) -> ResearchStrategySourceDisagreementEdgeStabilityRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    authority_pressure = _multiply_decimal(
        value.source_disagreement_probability,
        value.source_authority_weight,
    )
    edge_drift = _absolute_difference(
        value.current_edge_probability,
        value.prior_edge_probability,
    )
    edge_stability = _max_decimal_value(
        ZERO,
        _subtract_decimal(value.edge_persistence_score, edge_drift),
    )
    composite_score = _composite_score(
        authority_pressure=authority_pressure,
        source_freshness_score=value.source_freshness_score,
        corroboration_score=value.independent_corroboration_score,
        edge_stability_score=edge_stability,
        market_cost_pressure_score=value.market_cost_pressure_score,
        config=config,
    )
    component_statuses = _component_statuses(
        authority_pressure=authority_pressure,
        edge_drift=edge_drift,
        edge_stability_score=edge_stability,
        composite_score=composite_score,
        value=value,
        config=config,
    )
    status = _worst_status(component_statuses)
    return ResearchStrategySourceDisagreementEdgeStabilityRow(
        candidate_id=value.candidate_id,
        market_id=value.market_id,
        market_slug=value.market_slug,
        market_question=value.market_question,
        source_url=value.source_url,
        source_text=value.source_text,
        observed_at=observed_at,
        source_disagreement_probability=value.source_disagreement_probability,
        source_authority_weight=value.source_authority_weight,
        authority_weighted_conflict_pressure=authority_pressure,
        source_freshness_score=value.source_freshness_score,
        independent_corroboration_score=value.independent_corroboration_score,
        current_edge_probability=value.current_edge_probability,
        prior_edge_probability=value.prior_edge_probability,
        edge_drift_probability=edge_drift,
        edge_persistence_score=value.edge_persistence_score,
        edge_stability_score=edge_stability,
        market_cost_pressure_score=value.market_cost_pressure_score,
        disagreement_edge_stability_score=composite_score,
        status=status,
        reason_codes=_row_reason_codes(component_statuses, status=status),
    )


def _component_statuses(
    *,
    authority_pressure: Decimal,
    edge_drift: Decimal,
    edge_stability_score: Decimal,
    composite_score: Decimal,
    value: ResearchStrategySourceDisagreementEdgeStabilityInput,
    config: ResearchStrategySourceDisagreementEdgeStabilityConfig,
) -> tuple[tuple[str, str], ...]:
    return (
        (
            "authority_conflict_pressure",
            _status_for_ceiling(
                authority_pressure,
                config.max_authority_conflict_pass_pressure,
                config.max_authority_conflict_watch_pressure,
            ),
        ),
        (
            "source_freshness",
            _status_for_floor(
                value.source_freshness_score,
                config.min_source_freshness_pass_score,
                config.min_source_freshness_watch_score,
            ),
        ),
        (
            "corroboration",
            _status_for_floor(
                value.independent_corroboration_score,
                config.min_corroboration_pass_score,
                config.min_corroboration_watch_score,
            ),
        ),
        (
            "edge_persistence",
            _status_for_edge_persistence(
                persistence_score=value.edge_persistence_score,
                stability_score=edge_stability_score,
                config=config,
            ),
        ),
        (
            "edge_drift",
            _status_for_ceiling(
                edge_drift,
                config.max_edge_drift_pass_probability,
                config.max_edge_drift_watch_probability,
            ),
        ),
        (
            "market_cost_pressure",
            _status_for_ceiling(
                value.market_cost_pressure_score,
                config.max_market_cost_pass_pressure,
                config.max_market_cost_watch_pressure,
            ),
        ),
        (
            "composite_stability",
            _status_for_floor(
                composite_score,
                config.composite_pass_floor,
                config.composite_watch_floor,
            ),
        ),
    )


def _row_reason_codes(
    component_statuses: tuple[tuple[str, str], ...],
    *,
    status: str,
) -> tuple[str, ...]:
    codes = tuple(
        f"{component_name}_{component_status}"
        for component_name, component_status in component_statuses
        if component_status != "pass"
    )
    if not codes and status == "pass":
        return ("source_disagreement_edge_stability_pass",)
    return _normalize_reason_codes("reason_codes", codes, ROW_REASON_CODES)


def _composite_score(
    *,
    authority_pressure: Decimal,
    source_freshness_score: Decimal,
    corroboration_score: Decimal,
    edge_stability_score: Decimal,
    market_cost_pressure_score: Decimal,
    config: ResearchStrategySourceDisagreementEdgeStabilityConfig,
) -> Decimal:
    weights = _config_weights(config)
    scores = (
        _subtract_decimal(ONE, authority_pressure),
        source_freshness_score,
        corroboration_score,
        edge_stability_score,
        _subtract_decimal(ONE, market_cost_pressure_score),
    )
    weighted_values = tuple(
        _multiply_decimal(score, weight)
        for score, weight in zip(scores, weights, strict=True)
    )
    return _divide_decimal(_sum_decimals(weighted_values), _sum_decimals(weights))


def _config_weights(
    config: ResearchStrategySourceDisagreementEdgeStabilityConfig,
) -> tuple[Decimal, ...]:
    return (
        config.authority_conflict_weight,
        config.freshness_weight,
        config.corroboration_weight,
        config.edge_persistence_weight,
        config.market_cost_weight,
    )


def _status_for_ceiling(
    value: Decimal,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
) -> str:
    if value > watch_ceiling:
        return "block"
    if value > pass_ceiling:
        return "watch"
    return "pass"


def _status_for_floor(
    value: Decimal,
    pass_floor: Decimal,
    watch_floor: Decimal,
) -> str:
    if value < watch_floor:
        return "block"
    if value < pass_floor:
        return "watch"
    return "pass"


def _status_for_edge_persistence(
    *,
    persistence_score: Decimal,
    stability_score: Decimal,
    config: ResearchStrategySourceDisagreementEdgeStabilityConfig,
) -> str:
    if persistence_score < config.min_edge_persistence_watch_score:
        return "block"
    if stability_score < config.min_edge_persistence_pass_score:
        return "watch"
    return "pass"


def _worst_status(component_statuses: tuple[tuple[str, str], ...]) -> str:
    statuses = tuple(status for _, status in component_statuses)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategySourceDisagreementEdgeStabilityRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategySourceDisagreementEdgeStabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_disagreement_edge_stability_report_empty",)
    codes = [f"source_disagreement_edge_stability_report_{_report_status(rows)}"]
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    for prefix in (
        "authority_conflict_pressure",
        "source_freshness",
        "corroboration",
        "edge_persistence",
        "edge_drift",
        "market_cost_pressure",
        "composite_stability",
    ):
        if any(code.startswith(f"{prefix}_") for code in row_codes):
            codes.append(f"{prefix}_review")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(codes),
        REPORT_REASON_CODES,
    )


def _row_sort_key(
    row: ResearchStrategySourceDisagreementEdgeStabilityRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.disagreement_edge_stability_score,
        row.edge_stability_score,
        -row.authority_weighted_conflict_pressure,
        row.candidate_id,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategySourceDisagreementEdgeStabilityInput],
) -> tuple[ResearchStrategySourceDisagreementEdgeStabilityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_candidate_ids: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategySourceDisagreementEdgeStabilityInput:
            raise ValueError(
                "inputs must contain "
                "ResearchStrategySourceDisagreementEdgeStabilityInput values",
            )
        _require_hard_flags("input", value)
        if value.candidate_id in seen_candidate_ids:
            raise ValueError("inputs must not contain duplicate candidate_id values")
        seen_candidate_ids.add(value.candidate_id)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategySourceDisagreementEdgeStabilityRow],
) -> tuple[ResearchStrategySourceDisagreementEdgeStabilityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_candidate_ids: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategySourceDisagreementEdgeStabilityRow:
            raise ValueError(
                "rows must contain "
                "ResearchStrategySourceDisagreementEdgeStabilityRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.candidate_id in seen_candidate_ids:
            raise ValueError("rows must not contain duplicate candidate_id values")
        seen_candidate_ids.add(row.candidate_id)
    return normalized


def _normalize_reason_code_counts(
    values: Iterable[ResearchStrategySourceDisagreementEdgeStabilityReasonCodeCount],
) -> tuple[ResearchStrategySourceDisagreementEdgeStabilityReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_reason_codes: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategySourceDisagreementEdgeStabilityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategySourceDisagreementEdgeStabilityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", value)
        if value.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen_reason_codes.add(value.reason_code)
    return normalized


def _validate_row_consistency(
    row: ResearchStrategySourceDisagreementEdgeStabilityRow,
) -> None:
    expected_authority_pressure = _multiply_decimal(
        row.source_disagreement_probability,
        row.source_authority_weight,
    )
    if row.authority_weighted_conflict_pressure != expected_authority_pressure:
        raise ValueError(
            "authority_weighted_conflict_pressure must match source values",
        )
    expected_edge_drift = _absolute_difference(
        row.current_edge_probability,
        row.prior_edge_probability,
    )
    if row.edge_drift_probability != expected_edge_drift:
        raise ValueError("edge_drift_probability must match edge values")
    expected_edge_stability = _max_decimal_value(
        ZERO,
        _subtract_decimal(row.edge_persistence_score, row.edge_drift_probability),
    )
    if row.edge_stability_score != expected_edge_stability:
        raise ValueError("edge_stability_score must match persistence and drift")
    if row.status == "pass" and row.reason_codes != (
        "source_disagreement_edge_stability_pass",
    ):
        raise ValueError("pass rows must contain only the pass reason code")
    if row.status == "watch":
        if not any(code.endswith("_watch") for code in row.reason_codes):
            raise ValueError("watch rows must contain a watch reason code")
        if any(code.endswith("_block") for code in row.reason_codes):
            raise ValueError("watch rows must not contain a block reason code")
    if row.status == "block" and not any(
        code.endswith("_block") for code in row.reason_codes
    ):
        raise ValueError("block rows must contain a block reason code")


def _validate_report_consistency(
    report: ResearchStrategySourceDisagreementEdgeStabilityReport,
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
    if report.mean_authority_weighted_conflict_pressure != _mean(
        tuple(row.authority_weighted_conflict_pressure for row in report.rows),
    ):
        raise ValueError(
            "mean_authority_weighted_conflict_pressure must match rows",
        )
    if report.mean_edge_stability_score != _mean(
        tuple(row.edge_stability_score for row in report.rows),
    ):
        raise ValueError("mean_edge_stability_score must match rows")
    if report.mean_market_cost_pressure_score != _mean(
        tuple(row.market_cost_pressure_score for row in report.rows),
    ):
        raise ValueError("mean_market_cost_pressure_score must match rows")
    if report.mean_disagreement_edge_stability_score != _mean(
        tuple(row.disagreement_edge_stability_score for row in report.rows),
    ):
        raise ValueError("mean_disagreement_edge_stability_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use a deterministic sequence")


def _verify_report_integrity(
    report: ResearchStrategySourceDisagreementEdgeStabilityReport,
) -> None:
    _verify_digest(report)
    _validate_report_consistency(report)
    for row in report.rows:
        _verify_digest(row)
        _validate_row_consistency(row)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    _require_public_payload_keys("payload", payload, REPORT_PUBLIC_PAYLOAD_KEYS)
    _verify_public_payload_digest("payload", payload)
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _require_public_payload_keys(
            f"payload.rows[{index}]",
            row,
            ROW_PUBLIC_PAYLOAD_KEYS,
        )
        _verify_public_payload_digest(f"payload.rows[{index}]", row)
    reason_code_counts = payload.get("reason_code_counts")
    if type(reason_code_counts) is not list:
        raise ValueError("payload.reason_code_counts must be a list")
    for index, count in enumerate(reason_code_counts):
        if type(count) is not dict:
            raise ValueError("payload.reason_code_counts must contain JSON objects")
        _require_public_payload_keys(
            f"payload.reason_code_counts[{index}]",
            count,
            REASON_CODE_COUNT_PUBLIC_PAYLOAD_KEYS,
        )


def _require_public_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = frozenset(payload)
    unexpected_keys = actual_keys - expected_keys
    if unexpected_keys:
        raise ValueError(f"{label} has unexpected public fields")
    missing_keys = expected_keys - actual_keys
    if missing_keys:
        raise ValueError(f"{label} is missing public fields")


def _verify_public_payload_digest(label: str, payload: dict[str, Any]) -> None:
    provided = payload.get("derived_validation_digest")
    _require_digest(f"{label}.derived_validation_digest", provided)
    expected = _public_payload_digest(payload)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _status_count(
    rows: tuple[ResearchStrategySourceDisagreementEdgeStabilityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategySourceDisagreementEdgeStabilityRow, ...],
) -> tuple[ResearchStrategySourceDisagreementEdgeStabilityReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategySourceDisagreementEdgeStabilityReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            input_ratio=_divide_decimal(_count(count), denominator),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _absolute_difference(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(left - right))


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        raise ValueError("decimal denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _max_decimal_value(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(max(left, right))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value, name=name)


def _quantize(value: Decimal, *, name: str = "decimal value") -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(DECIMAL_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{name} cannot be represented at six decimal places") from exc


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_ceiling_pair(
    name: str,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
    *,
    pass_field_name: str,
) -> None:
    if pass_ceiling > watch_ceiling:
        raise ValueError(
            f"{pass_field_name} must not exceed the watch value for {name}",
        )


def _require_floor_pair(
    name: str,
    pass_floor: Decimal,
    watch_floor: Decimal,
    *,
    pass_field_name: str,
) -> None:
    if pass_floor < watch_floor:
        raise ValueError(
            f"{pass_field_name} must be at least the watch value for {name}",
        )


def _require_status(name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_SOURCE_DISAGREEMENT_EDGE_STABILITY_STATUSES
    ):
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_reason_code(
    name: str,
    value: object,
    supported: tuple[str, ...],
) -> None:
    _require_public_string(name, value)
    if value not in supported:
        raise ValueError(f"{name} is not supported")


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not value:
        raise ValueError(f"{name} must not be empty")
    for reason_code in value:
        _require_reason_code(name, reason_code, supported)
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must not contain duplicates")
    return value


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical public string")
    if len(value) > 256:
        raise ValueError(f"{name} must be at most 256 characters")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{name} must be a public label")


def _require_private_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _require_exact_type(name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


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
        raise ValueError(f"{name} must be a lowercase sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase sha256 digest")


def _digest_for(value: object) -> str:
    payload = asdict(value)
    payload.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
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
        return str(_quantize(value))
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
            if _contains_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            if key in HARD_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _contains_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public value in {label}")


def _contains_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SOURCE_DISAGREEMENT_EDGE_STABILITY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_SOURCE_DISAGREEMENT_EDGE_STABILITY_STATUSES",
    "ResearchStrategySourceDisagreementEdgeStabilityConfig",
    "ResearchStrategySourceDisagreementEdgeStabilityInput",
    "ResearchStrategySourceDisagreementEdgeStabilityReasonCodeCount",
    "ResearchStrategySourceDisagreementEdgeStabilityRow",
    "ResearchStrategySourceDisagreementEdgeStabilityReport",
    "build_research_strategy_source_disagreement_edge_stability_report",
    "research_strategy_source_disagreement_edge_stability_report_payload",
)
