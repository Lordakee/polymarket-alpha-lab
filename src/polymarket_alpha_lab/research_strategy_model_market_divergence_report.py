"""Report-only model-vs-market probability divergence explanation gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_MODEL_MARKET_DIVERGENCE_CONFIG_VERSION = (
    "research-strategy-model-market-divergence-report"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_DIVERGENCE_STATUSES = frozenset(("pass", "watch", "block"))
_DIVERGENCE_DIRECTIONS = frozenset(
    ("aligned", "model_above_market", "market_above_model"),
)
_DOMINANT_EXPLANATIONS = frozenset(
    ("none", "evidence", "costs", "liquidity", "stale_inputs"),
)
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "candidate_id",
    "market_id",
    "slug",
    "question",
    "source_url",
    "source_text",
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
    "recommendation",
    "sizing",
)
_REASON_CODE_SEQUENCE = (
    "empty_observations",
    "aligned_probabilities",
    "model_above_market",
    "market_above_model",
    "immaterial_divergence",
    "evidence_explains_divergence",
    "costs_explain_divergence",
    "liquidity_explains_divergence",
    "stale_inputs_explain_divergence",
    "divergence_explained",
    "partially_unexplained_divergence",
    "material_unexplained_divergence",
    "watch_unexplained_divergence",
    "block_unexplained_divergence",
)


@dataclass(frozen=True)
class ResearchStrategyModelMarketDivergenceConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_MODEL_MARKET_DIVERGENCE_CONFIG_VERSION
    material_divergence_threshold: Decimal = Decimal("0.100000")
    watch_unexplained_divergence_threshold: Decimal = Decimal("0.050000")
    block_unexplained_divergence_threshold: Decimal = Decimal("0.150000")
    stale_input_age_seconds_threshold: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyModelMarketDivergenceConfig:
            raise TypeError(
                "ResearchStrategyModelMarketDivergenceConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyModelMarketDivergenceConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyModelMarketDivergenceConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MODEL_MARKET_DIVERGENCE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "material_divergence_threshold",
            "watch_unexplained_divergence_threshold",
            "block_unexplained_divergence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_input_age_seconds_threshold",
            _require_positive_decimal(
                "stale_input_age_seconds_threshold",
                self.stale_input_age_seconds_threshold,
            ),
        )
        if (
            self.block_unexplained_divergence_threshold
            <= self.watch_unexplained_divergence_threshold
        ):
            raise ValueError(
                "block_unexplained_divergence_threshold must exceed "
                "watch_unexplained_divergence_threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyModelMarketDivergenceObservation:
    analysis_key: str
    candidate_reference: str
    market_reference: str
    model_input_observed_at: datetime
    market_observed_at: datetime
    model_implied_probability: Decimal
    observed_market_probability: Decimal
    evidence_explanation_score: Decimal
    cost_explanation_score: Decimal
    liquidity_explanation_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyModelMarketDivergenceObservation:
            raise TypeError(
                "ResearchStrategyModelMarketDivergenceObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyModelMarketDivergenceObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchStrategyModelMarketDivergenceObservation",
            )
        _require_public_identifier("analysis_key", self.analysis_key)
        object.__setattr__(
            self,
            "candidate_reference",
            _require_private_reference("candidate_reference", self.candidate_reference),
        )
        object.__setattr__(
            self,
            "market_reference",
            _require_private_reference("market_reference", self.market_reference),
        )
        object.__setattr__(
            self,
            "model_input_observed_at",
            _as_utc("model_input_observed_at", self.model_input_observed_at),
        )
        object.__setattr__(
            self,
            "market_observed_at",
            _as_utc("market_observed_at", self.market_observed_at),
        )
        for field_name in (
            "model_implied_probability",
            "observed_market_probability",
            "evidence_explanation_score",
            "cost_explanation_score",
            "liquidity_explanation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchStrategyModelMarketDivergencePublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyModelMarketDivergencePublicPayloadItem:
            raise TypeError(
                "ResearchStrategyModelMarketDivergencePublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyModelMarketDivergencePublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchStrategyModelMarketDivergencePublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchStrategyModelMarketDivergenceRow:
    analysis_key: str
    candidate_reference_digest: str
    market_reference_digest: str
    model_input_observed_at: datetime
    market_observed_at: datetime
    model_input_age_seconds: Decimal
    market_age_seconds: Decimal
    model_implied_probability: Decimal
    observed_market_probability: Decimal
    divergence_magnitude: Decimal
    divergence_direction: str
    evidence_explanation_score: Decimal
    cost_explanation_score: Decimal
    liquidity_explanation_score: Decimal
    stale_input_explanation_score: Decimal
    explanation_score: Decimal
    unexplained_divergence: Decimal
    dominant_explanation: str
    divergence_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyModelMarketDivergenceRow:
            raise TypeError(
                "ResearchStrategyModelMarketDivergenceRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyModelMarketDivergenceRow:
            raise ValueError(
                "row must be exactly ResearchStrategyModelMarketDivergenceRow",
            )
        _require_public_identifier("analysis_key", self.analysis_key)
        _require_public_digest_reference(
            "candidate_reference_digest",
            self.candidate_reference_digest,
        )
        _require_public_digest_reference(
            "market_reference_digest",
            self.market_reference_digest,
        )
        object.__setattr__(
            self,
            "model_input_observed_at",
            _as_utc("model_input_observed_at", self.model_input_observed_at),
        )
        object.__setattr__(
            self,
            "market_observed_at",
            _as_utc("market_observed_at", self.market_observed_at),
        )
        for field_name in ("model_input_age_seconds", "market_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "model_implied_probability",
            "observed_market_probability",
            "divergence_magnitude",
            "evidence_explanation_score",
            "cost_explanation_score",
            "liquidity_explanation_score",
            "stale_input_explanation_score",
            "explanation_score",
            "unexplained_divergence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_divergence_direction("divergence_direction", self.divergence_direction)
        _require_dominant_explanation(
            "dominant_explanation",
            self.dominant_explanation,
        )
        _require_divergence_status("divergence_status", self.divergence_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyModelMarketDivergenceReport:
    generated_at: datetime
    config_version: str
    divergence_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_divergence_magnitude: Decimal
    average_unexplained_divergence: Decimal
    max_unexplained_divergence: Decimal
    rows: tuple[ResearchStrategyModelMarketDivergenceRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchStrategyModelMarketDivergencePublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyModelMarketDivergenceReport:
            raise TypeError(
                "ResearchStrategyModelMarketDivergenceReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyModelMarketDivergenceReport:
            raise ValueError(
                "report must be exactly ResearchStrategyModelMarketDivergenceReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MODEL_MARKET_DIVERGENCE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_divergence_status("divergence_status", self.divergence_status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_divergence_magnitude",
            "average_unexplained_divergence",
            "max_unexplained_divergence",
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
            "ResearchStrategyModelMarketDivergenceReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_strategy_model_market_divergence_report(
    observations: Sequence[ResearchStrategyModelMarketDivergenceObservation],
    *,
    generated_at: datetime,
    config: ResearchStrategyModelMarketDivergenceConfig | None = None,
    public_payload: Sequence[
        ResearchStrategyModelMarketDivergencePublicPayloadItem
    ] = (),
) -> ResearchStrategyModelMarketDivergenceReport:
    """Build a local report-only model-vs-market divergence explanation snapshot."""

    if config is None:
        config = ResearchStrategyModelMarketDivergenceConfig()
    if type(config) is not ResearchStrategyModelMarketDivergenceConfig:
        raise ValueError(
            "config must be a ResearchStrategyModelMarketDivergenceConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.model_input_observed_at > generated_at:
            raise ValueError("model_input_observed_at must not be after generated_at")
        if observation.market_observed_at > generated_at:
            raise ValueError("market_observed_at must not be after generated_at")
    rows = _build_rows(normalized_observations, generated_at, config)
    payload_items = _normalize_public_payload(public_payload)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "divergence_status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_divergence_magnitude": _average(
            tuple(row.divergence_magnitude for row in rows),
        ),
        "average_unexplained_divergence": _average(
            tuple(row.unexplained_divergence for row in rows),
        ),
        "max_unexplained_divergence": max(
            (row.unexplained_divergence for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyModelMarketDivergenceReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    observations: tuple[ResearchStrategyModelMarketDivergenceObservation, ...],
    generated_at: datetime,
    config: ResearchStrategyModelMarketDivergenceConfig,
) -> tuple[ResearchStrategyModelMarketDivergenceRow, ...]:
    return tuple(
        sorted(
            (
                _row_from_observation(observation, generated_at, config)
                for observation in observations
            ),
            key=lambda row: (
                row.analysis_key,
                row.candidate_reference_digest,
                row.market_reference_digest,
            ),
        ),
    )


def _row_from_observation(
    observation: ResearchStrategyModelMarketDivergenceObservation,
    generated_at: datetime,
    config: ResearchStrategyModelMarketDivergenceConfig,
) -> ResearchStrategyModelMarketDivergenceRow:
    model_age_seconds = _seconds_between(generated_at, observation.model_input_observed_at)
    market_age_seconds = _seconds_between(generated_at, observation.market_observed_at)
    stale_score = (
        _ONE
        if model_age_seconds >= config.stale_input_age_seconds_threshold
        else _ZERO
    )
    divergence = _quantize(
        abs(observation.model_implied_probability - observation.observed_market_probability),
    )
    direction = _divergence_direction(
        observation.model_implied_probability,
        observation.observed_market_probability,
    )
    dominant = _dominant_explanation(
        evidence_score=observation.evidence_explanation_score,
        cost_score=observation.cost_explanation_score,
        liquidity_score=observation.liquidity_explanation_score,
        stale_score=stale_score,
    )
    explanation_score = _explanation_score(
        observation.evidence_explanation_score,
        observation.cost_explanation_score,
        observation.liquidity_explanation_score,
        stale_score,
    )
    unexplained = _quantize(divergence * (_ONE - explanation_score))
    status = _row_status(
        divergence_magnitude=divergence,
        unexplained_divergence=unexplained,
        config=config,
    )
    return ResearchStrategyModelMarketDivergenceRow(
        analysis_key=observation.analysis_key,
        candidate_reference_digest=_digest_reference(observation.candidate_reference),
        market_reference_digest=_digest_reference(observation.market_reference),
        model_input_observed_at=observation.model_input_observed_at,
        market_observed_at=observation.market_observed_at,
        model_input_age_seconds=model_age_seconds,
        market_age_seconds=market_age_seconds,
        model_implied_probability=observation.model_implied_probability,
        observed_market_probability=observation.observed_market_probability,
        divergence_magnitude=divergence,
        divergence_direction=direction,
        evidence_explanation_score=observation.evidence_explanation_score,
        cost_explanation_score=observation.cost_explanation_score,
        liquidity_explanation_score=observation.liquidity_explanation_score,
        stale_input_explanation_score=stale_score,
        explanation_score=explanation_score,
        unexplained_divergence=unexplained,
        dominant_explanation=dominant,
        divergence_status=status,
        reason_codes=_row_reason_codes(
            divergence_direction=direction,
            dominant_explanation=dominant,
            divergence_magnitude=divergence,
            unexplained_divergence=unexplained,
            divergence_status=status,
            config=config,
        ),
    )


def _row_reason_codes(
    *,
    divergence_direction: str,
    dominant_explanation: str,
    divergence_magnitude: Decimal,
    unexplained_divergence: Decimal,
    divergence_status: str,
    config: ResearchStrategyModelMarketDivergenceConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if divergence_direction != "aligned":
        reason_codes.append(divergence_direction)
    else:
        reason_codes.append("aligned_probabilities")
    if divergence_magnitude < config.material_divergence_threshold:
        reason_codes.append("immaterial_divergence")
    if dominant_explanation == "evidence":
        reason_codes.append("evidence_explains_divergence")
    if dominant_explanation == "costs":
        reason_codes.append("costs_explain_divergence")
    if dominant_explanation == "liquidity":
        reason_codes.append("liquidity_explains_divergence")
    if dominant_explanation == "stale_inputs":
        reason_codes.append("stale_inputs_explain_divergence")
    if (
        divergence_magnitude >= config.material_divergence_threshold
        and divergence_status == "pass"
    ):
        reason_codes.append("divergence_explained")
    if unexplained_divergence >= config.watch_unexplained_divergence_threshold:
        reason_codes.append("partially_unexplained_divergence")
        reason_codes.append("material_unexplained_divergence")
    if divergence_status == "watch":
        reason_codes.append("watch_unexplained_divergence")
    if divergence_status == "block":
        reason_codes.append("block_unexplained_divergence")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(
    *,
    divergence_magnitude: Decimal,
    unexplained_divergence: Decimal,
    config: ResearchStrategyModelMarketDivergenceConfig,
) -> str:
    if divergence_magnitude < config.material_divergence_threshold:
        return "pass"
    if unexplained_divergence >= config.block_unexplained_divergence_threshold:
        return "block"
    if unexplained_divergence >= config.watch_unexplained_divergence_threshold:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchStrategyModelMarketDivergenceRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.divergence_status == "block" for row in rows):
        return "block"
    if any(row.divergence_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyModelMarketDivergenceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchStrategyModelMarketDivergenceRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.divergence_status == status)


def _validate_row_consistency(row: ResearchStrategyModelMarketDivergenceRow) -> None:
    expected_divergence = _quantize(
        abs(row.model_implied_probability - row.observed_market_probability),
    )
    if row.divergence_magnitude != expected_divergence:
        raise ValueError("divergence_magnitude must match probability difference")
    if row.divergence_direction != _divergence_direction(
        row.model_implied_probability,
        row.observed_market_probability,
    ):
        raise ValueError("divergence_direction must match probability ordering")
    expected_explanation = _explanation_score(
        row.evidence_explanation_score,
        row.cost_explanation_score,
        row.liquidity_explanation_score,
        row.stale_input_explanation_score,
    )
    if row.explanation_score != expected_explanation:
        raise ValueError("explanation_score must match component scores")
    if row.unexplained_divergence != _quantize(
        row.divergence_magnitude * (_ONE - row.explanation_score),
    ):
        raise ValueError("unexplained_divergence must match residual divergence")
    if row.dominant_explanation != _dominant_explanation(
        evidence_score=row.evidence_explanation_score,
        cost_score=row.cost_explanation_score,
        liquidity_score=row.liquidity_explanation_score,
        stale_score=row.stale_input_explanation_score,
    ):
        raise ValueError("dominant_explanation must match highest explanation score")
    if row.divergence_status == "pass" and (
        "watch_unexplained_divergence" in row.reason_codes
        or "block_unexplained_divergence" in row.reason_codes
    ):
        raise ValueError("pass rows must not include watch/block reason codes")
    if row.divergence_status == "block" and (
        "block_unexplained_divergence" not in row.reason_codes
    ):
        raise ValueError("block rows must include block_unexplained_divergence")


def _validate_report_consistency(
    report: ResearchStrategyModelMarketDivergenceReport,
) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_divergence_magnitude != _average(
        tuple(row.divergence_magnitude for row in report.rows),
    ):
        raise ValueError("average_divergence_magnitude must match rows")
    if report.average_unexplained_divergence != _average(
        tuple(row.unexplained_divergence for row in report.rows),
    ):
        raise ValueError("average_unexplained_divergence must match rows")
    expected_max = max(
        (row.unexplained_divergence for row in report.rows),
        default=_ZERO,
    )
    if report.max_unexplained_divergence != expected_max:
        raise ValueError("max_unexplained_divergence must match rows")
    if report.divergence_status != _report_status(report.rows):
        raise ValueError("divergence_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Sequence[ResearchStrategyModelMarketDivergenceObservation],
) -> tuple[ResearchStrategyModelMarketDivergenceObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchStrategyModelMarketDivergenceObservation] = []
    for observation in observations:
        if type(observation) is not ResearchStrategyModelMarketDivergenceObservation:
            raise ValueError(
                "observations must contain "
                "ResearchStrategyModelMarketDivergenceObservation",
            )
        normalized.append(observation)
    return tuple(
        sorted(
            normalized,
            key=lambda observation: (
                observation.analysis_key,
                _digest_reference(observation.candidate_reference),
                _digest_reference(observation.market_reference),
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchStrategyModelMarketDivergenceRow],
) -> tuple[ResearchStrategyModelMarketDivergenceRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchStrategyModelMarketDivergenceRow] = []
    for row in rows:
        if type(row) is not ResearchStrategyModelMarketDivergenceRow:
            raise ValueError(
                "rows must contain ResearchStrategyModelMarketDivergenceRow",
            )
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                row.analysis_key,
                row.candidate_reference_digest,
                row.market_reference_digest,
            ),
        ),
    )


def _normalize_public_payload(
    public_payload: Sequence[ResearchStrategyModelMarketDivergencePublicPayloadItem],
) -> tuple[ResearchStrategyModelMarketDivergencePublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchStrategyModelMarketDivergencePublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchStrategyModelMarketDivergencePublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "ResearchStrategyModelMarketDivergencePublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _divergence_direction(model_probability: Decimal, market_probability: Decimal) -> str:
    if model_probability > market_probability:
        return "model_above_market"
    if market_probability > model_probability:
        return "market_above_model"
    return "aligned"


def _dominant_explanation(
    *,
    evidence_score: Decimal,
    cost_score: Decimal,
    liquidity_score: Decimal,
    stale_score: Decimal,
) -> str:
    best_name = "none"
    best_score = _ZERO
    for name, score in (
        ("evidence", evidence_score),
        ("costs", cost_score),
        ("liquidity", liquidity_score),
        ("stale_inputs", stale_score),
    ):
        if score > best_score:
            best_name = name
            best_score = score
    return best_name


def _explanation_score(*scores: Decimal) -> Decimal:
    if not scores:
        return _ZERO
    return _quantize(max(scores))


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    seconds = later - earlier
    return _require_nonnegative_decimal(
        "age_seconds",
        Decimal(str(seconds.total_seconds())),
    )


def _digest_reference(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty text")
    if len(value) > 2048:
        raise ValueError(f"{field_name} must not exceed 2048 characters")
    return value


def _require_public_digest_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a redacted sha256 reference")
    _require_sha256_digest(field_name, value.removeprefix("sha256:"))
    return value


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


def _require_divergence_direction(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _DIVERGENCE_DIRECTIONS:
        raise ValueError(f"{field_name} must be a known divergence direction")
    return value


def _require_dominant_explanation(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _DOMINANT_EXPLANATIONS:
        raise ValueError(f"{field_name} must be a known dominant explanation")
    return value


def _require_divergence_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _DIVERGENCE_STATUSES:
        raise ValueError(f"{field_name} must be a known divergence status")
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


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


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
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchStrategyModelMarketDivergenceReport,
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


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MODEL_MARKET_DIVERGENCE_CONFIG_VERSION",
    "ResearchStrategyModelMarketDivergenceConfig",
    "ResearchStrategyModelMarketDivergenceObservation",
    "ResearchStrategyModelMarketDivergencePublicPayloadItem",
    "ResearchStrategyModelMarketDivergenceReport",
    "ResearchStrategyModelMarketDivergenceRow",
    "build_research_strategy_model_market_divergence_report",
)
