"""Pure deterministic probability and liquidity regime research report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import InitVar, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_REGIME_CONFIG_VERSION",
    "ResearchMarketProbabilityLiquidityRegimeConfig",
    "ResearchMarketProbabilityLiquidityRegimeObservation",
    "ResearchMarketProbabilityLiquidityRegimeRow",
    "ResearchMarketProbabilityLiquidityRegimeReasonCodeCount",
    "ResearchMarketProbabilityLiquidityRegimeReport",
    "build_research_market_probability_liquidity_regime_report",
    "research_market_probability_liquidity_regime_report_payload",
    "validate_research_market_probability_liquidity_regime_report_payload",
)


DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_REGIME_CONFIG_VERSION = (
    "research-market-probability-liquidity-regime-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HALF = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
PROBABILITY_BANDS = ("low_tail", "central", "high_tail")
LIQUIDITY_REGIMES = ("robust", "constrained", "fragile")
STATUS_SORT_RANK = {"block": 0, "watch": 1, "pass": 2}

CONFIG_PAYLOAD_KEYS = (
    "config_version",
    "tail_probability_max",
    "max_pass_spread_rate",
    "max_watch_spread_rate",
    "min_pass_depth_score",
    "min_watch_depth_score",
    "max_pass_cost_rate",
    "max_watch_cost_rate",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "case_digest",
    "rank",
    "observed_at",
    "market_probability",
    "probability_band",
    "probability_extremity_score",
    "spread_rate",
    "spread_quality_score",
    "depth_score",
    "cost_rate",
    "cost_quality_score",
    "liquidity_score",
    "liquidity_regime",
    "regime",
    "status",
    "manual_review_required",
    "upstream_reason_codes",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_COUNT_PAYLOAD_KEYS = (
    "reason_code",
    "row_count",
    "row_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "config",
    "observation_count",
    "pass_count",
    "watch_count",
    "block_count",
    "tail_count",
    "robust_count",
    "constrained_count",
    "fragile_count",
    "manual_review_count",
    "average_market_probability",
    "average_liquidity_score",
    "minimum_depth_score",
    "maximum_spread_rate",
    "maximum_cost_rate",
    "status",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)

CANONICAL_DECIMAL_PATTERN = re.compile(r"(?:0|[1-9][0-9]*)\.[0-9]{6}\Z")
HEX_CHARS = frozenset("0123456789abcdef")
_UNSAFE_REASON_FRAGMENTS = (
    "account" "_" "identifier",
    "api" "_" "key",
    "au" "th",
    "candidate" "_" "id",
    "credential",
    "database",
    "dsn",
    "email" "_" "address",
    "endpoint",
    "ip" "_" "address",
    "market" "_" "id",
    "phone" "_" "number",
    "private",
    "question",
    "secret",
    "session" "_" "identifier",
    "source" "_" "text",
    "source" "_" "url",
    "table" "_" "name",
    "tok" "en",
    "user" "_" "id",
    "wal" "let",
    "or" "der",
    "tra" "de",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchMarketProbabilityLiquidityRegimeConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_REGIME_CONFIG_VERSION
    )
    tail_probability_max: Decimal = Decimal("0.100000")
    max_pass_spread_rate: Decimal = Decimal("0.020000")
    max_watch_spread_rate: Decimal = Decimal("0.050000")
    min_pass_depth_score: Decimal = Decimal("0.700000")
    min_watch_depth_score: Decimal = Decimal("0.400000")
    max_pass_cost_rate: Decimal = Decimal("0.030000")
    max_watch_cost_rate: Decimal = Decimal("0.070000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityLiquidityRegimeConfig,
            "config",
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_REGIME_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "tail_probability_max",
            _tail_boundary_decimal(
                "tail_probability_max",
                self.tail_probability_max,
            ),
        )
        for field_name in (
            "max_pass_spread_rate",
            "max_watch_spread_rate",
            "min_pass_depth_score",
            "min_watch_depth_score",
            "max_pass_cost_rate",
            "max_watch_cost_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_spread_rate >= self.max_watch_spread_rate:
            raise ValueError(
                "max_pass_spread_rate must be below max_watch_spread_rate",
            )
        if self.min_pass_depth_score <= self.min_watch_depth_score:
            raise ValueError(
                "min_pass_depth_score must exceed min_watch_depth_score",
            )
        if self.max_pass_cost_rate >= self.max_watch_cost_rate:
            raise ValueError(
                "max_pass_cost_rate must be below max_watch_cost_rate",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityLiquidityRegimeObservation(_FinalPublicDataclass):
    case_digest: str
    observed_at: datetime
    market_probability: Decimal
    spread_rate: Decimal
    depth_score: Decimal
    cost_rate: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityLiquidityRegimeObservation,
            "observation",
        )
        _require_sha256_digest("case_digest", self.case_digest)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "market_probability",
            "spread_rate",
            "depth_score",
            "cost_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
                allow_empty=True,
                sort_values=True,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityLiquidityRegimeRow(_FinalPublicDataclass):
    case_digest: str
    rank: Decimal
    observed_at: datetime
    market_probability: Decimal
    probability_band: str
    probability_extremity_score: Decimal
    spread_rate: Decimal
    spread_quality_score: Decimal
    depth_score: Decimal
    cost_rate: Decimal
    cost_quality_score: Decimal
    liquidity_score: Decimal
    liquidity_regime: str
    regime: str
    status: str
    manual_review_required: bool
    upstream_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchMarketProbabilityLiquidityRegimeConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchMarketProbabilityLiquidityRegimeConfig | None,
    ) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityLiquidityRegimeRow,
            "row",
        )
        active_config = (
            ResearchMarketProbabilityLiquidityRegimeConfig()
            if validation_config is None
            else validation_config
        )
        _require_exact_type(
            active_config,
            ResearchMarketProbabilityLiquidityRegimeConfig,
            "validation_config",
        )
        _require_hard_flags("validation_config", active_config)
        _require_sha256_digest("case_digest", self.case_digest)
        object.__setattr__(
            self,
            "rank",
            _positive_count_decimal("rank", self.rank),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "market_probability",
            "probability_extremity_score",
            "spread_rate",
            "spread_quality_score",
            "depth_score",
            "cost_rate",
            "cost_quality_score",
            "liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice(
            "probability_band",
            self.probability_band,
            PROBABILITY_BANDS,
        )
        _require_choice(
            "liquidity_regime",
            self.liquidity_regime,
            LIQUIDITY_REGIMES,
        )
        _require_regime("regime", self.regime)
        _require_choice("status", self.status, STATUSES)
        if type(self.manual_review_required) is not bool:
            raise ValueError("manual_review_required must be a bool")
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
                allow_empty=True,
                sort_values=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
                sort_values=False,
            ),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self, config=active_config)


@dataclass(frozen=True)
class ResearchMarketProbabilityLiquidityRegimeReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    row_count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityLiquidityRegimeReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "row_count",
            _nonnegative_count_decimal("row_count", self.row_count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _unit_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityLiquidityRegimeReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    config: ResearchMarketProbabilityLiquidityRegimeConfig
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    tail_count: Decimal
    robust_count: Decimal
    constrained_count: Decimal
    fragile_count: Decimal
    manual_review_count: Decimal
    average_market_probability: Decimal
    average_liquidity_score: Decimal
    minimum_depth_score: Decimal
    maximum_spread_rate: Decimal
    maximum_cost_rate: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchMarketProbabilityLiquidityRegimeReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchMarketProbabilityLiquidityRegimeRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityLiquidityRegimeReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_exact_type(
            self.config,
            ResearchMarketProbabilityLiquidityRegimeConfig,
            "config",
        )
        _require_hard_flags("config", self.config)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "tail_count",
            "robust_count",
            "constrained_count",
            "fragile_count",
            "manual_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_market_probability",
            "average_liquidity_score",
            "minimum_depth_score",
            "maximum_spread_rate",
            "maximum_cost_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
                sort_values=False,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "rows",
            _normalize_rows(self.rows, config=self.config),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_digest(self):
                raise ValueError(
                    "derived_validation_digest does not match report payload",
                )

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_probability_liquidity_regime_report_payload(self)


def build_research_market_probability_liquidity_regime_report(
    observations: Iterable[ResearchMarketProbabilityLiquidityRegimeObservation],
    *,
    config: ResearchMarketProbabilityLiquidityRegimeConfig,
    generated_at: datetime,
) -> ResearchMarketProbabilityLiquidityRegimeReport:
    _require_exact_type(
        config,
        ResearchMarketProbabilityLiquidityRegimeConfig,
        "config",
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    unranked_rows = tuple(
        _row_from_observation(
            observation,
            rank=ONE,
            config=config,
        )
        for observation in normalized_observations
    )
    rows = tuple(
        _copy_row_with_rank(
            row,
            rank=_count_decimal(index),
            config=config,
        )
        for index, row in enumerate(
            sorted(unranked_rows, key=_row_sort_key),
            start=1,
        )
    )
    status = _report_status(rows)
    return ResearchMarketProbabilityLiquidityRegimeReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        config=config,
        observation_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        tail_count=_tail_count(rows),
        robust_count=_liquidity_regime_count(rows, "robust"),
        constrained_count=_liquidity_regime_count(rows, "constrained"),
        fragile_count=_liquidity_regime_count(rows, "fragile"),
        manual_review_count=_manual_review_count(rows),
        average_market_probability=_average_decimal(
            tuple(row.market_probability for row in rows),
        ),
        average_liquidity_score=_average_decimal(
            tuple(row.liquidity_score for row in rows),
        ),
        minimum_depth_score=min(
            (row.depth_score for row in rows),
            default=ZERO,
        ),
        maximum_spread_rate=max(
            (row.spread_rate for row in rows),
            default=ZERO,
        ),
        maximum_cost_rate=max(
            (row.cost_rate for row in rows),
            default=ZERO,
        ),
        status=status,
        reason_codes=_report_reason_codes(rows, status=status),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_market_probability_liquidity_regime_report_payload(
    report: ResearchMarketProbabilityLiquidityRegimeReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketProbabilityLiquidityRegimeReport:
        _require_hard_flags("report", report)
        payload = _report_payload(report, include_digest=True)
    elif type(report) is dict:
        payload = _copy_json_value(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
    else:
        raise ValueError(
            "report must be a ResearchMarketProbabilityLiquidityRegimeReport",
        )
    return validate_research_market_probability_liquidity_regime_report_payload(
        payload,
    )


def validate_research_market_probability_liquidity_regime_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_exact_keys("payload", payload, REPORT_PAYLOAD_KEYS)
    _require_payload_hard_flags("payload", payload)
    _validate_payload_shape_and_scalars(payload)

    supplied_digest = payload["derived_validation_digest"]
    _require_sha256_digest("derived_validation_digest", supplied_digest)
    unsigned_payload = {
        key: _copy_json_value(value)
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    if supplied_digest != _digest_payload(unsigned_payload):
        raise ValueError(
            "derived_validation_digest does not match canonical payload",
        )

    config = _config_from_payload(payload["config"])
    generated_at = _datetime_from_payload("generated_at", payload["generated_at"])
    config_version = _string_from_payload(
        "config_version",
        payload["config_version"],
    )
    if config_version != config.config_version:
        raise ValueError("config_version must match config")

    rows_payload = _list_from_payload("rows", payload["rows"])
    rows = tuple(
        _row_from_payload(row_payload, index=index, config=config)
        for index, row_payload in enumerate(rows_payload)
    )
    reason_counts_payload = _list_from_payload(
        "reason_code_counts",
        payload["reason_code_counts"],
    )
    reason_code_counts = tuple(
        _reason_count_from_payload(value, index=index)
        for index, value in enumerate(reason_counts_payload)
    )

    try:
        report = ResearchMarketProbabilityLiquidityRegimeReport(
            generated_at=generated_at,
            config_version=config_version,
            config=config,
            observation_count=_count_from_payload(
                "observation_count",
                payload["observation_count"],
            ),
            pass_count=_count_from_payload("pass_count", payload["pass_count"]),
            watch_count=_count_from_payload("watch_count", payload["watch_count"]),
            block_count=_count_from_payload("block_count", payload["block_count"]),
            tail_count=_count_from_payload("tail_count", payload["tail_count"]),
            robust_count=_count_from_payload(
                "robust_count",
                payload["robust_count"],
            ),
            constrained_count=_count_from_payload(
                "constrained_count",
                payload["constrained_count"],
            ),
            fragile_count=_count_from_payload(
                "fragile_count",
                payload["fragile_count"],
            ),
            manual_review_count=_count_from_payload(
                "manual_review_count",
                payload["manual_review_count"],
            ),
            average_market_probability=_unit_from_payload(
                "average_market_probability",
                payload["average_market_probability"],
            ),
            average_liquidity_score=_unit_from_payload(
                "average_liquidity_score",
                payload["average_liquidity_score"],
            ),
            minimum_depth_score=_unit_from_payload(
                "minimum_depth_score",
                payload["minimum_depth_score"],
            ),
            maximum_spread_rate=_unit_from_payload(
                "maximum_spread_rate",
                payload["maximum_spread_rate"],
            ),
            maximum_cost_rate=_unit_from_payload(
                "maximum_cost_rate",
                payload["maximum_cost_rate"],
            ),
            status=_choice_from_payload("status", payload["status"], STATUSES),
            reason_codes=_reason_codes_from_payload(
                "reason_codes",
                payload["reason_codes"],
                allow_empty=False,
                sort_values=False,
            ),
            reason_code_counts=reason_code_counts,
            rows=rows,
            derived_validation_digest=supplied_digest,
            paper_only=_true_from_payload("paper_only", payload["paper_only"]),
            report_only=_true_from_payload("report_only", payload["report_only"]),
            readonly=_true_from_payload("readonly", payload["readonly"]),
        )
    except ValueError:
        raise

    canonical_payload = _report_payload(report, include_digest=True)
    _assert_payload_equal(payload, canonical_payload, path="payload")
    return canonical_payload


def _row_from_observation(
    observation: ResearchMarketProbabilityLiquidityRegimeObservation,
    *,
    rank: Decimal,
    config: ResearchMarketProbabilityLiquidityRegimeConfig,
) -> ResearchMarketProbabilityLiquidityRegimeRow:
    probability_band = _probability_band(
        observation.market_probability,
        config=config,
    )
    probability_extremity_score = _probability_extremity_score(
        observation.market_probability,
    )
    spread_quality_score = _ceiling_quality_score(
        observation.spread_rate,
        ceiling=config.max_watch_spread_rate,
    )
    cost_quality_score = _ceiling_quality_score(
        observation.cost_rate,
        ceiling=config.max_watch_cost_rate,
    )
    liquidity_score = _average_decimal(
        (
            spread_quality_score,
            observation.depth_score,
            cost_quality_score,
        ),
    )
    spread_status = _ceiling_status(
        observation.spread_rate,
        pass_limit=config.max_pass_spread_rate,
        watch_limit=config.max_watch_spread_rate,
    )
    depth_status = _floor_status(
        observation.depth_score,
        pass_limit=config.min_pass_depth_score,
        watch_limit=config.min_watch_depth_score,
    )
    cost_status = _ceiling_status(
        observation.cost_rate,
        pass_limit=config.max_pass_cost_rate,
        watch_limit=config.max_watch_cost_rate,
    )
    liquidity_regime = _liquidity_regime(
        spread_status=spread_status,
        depth_status=depth_status,
        cost_status=cost_status,
    )
    status = _row_status(
        probability_band=probability_band,
        liquidity_regime=liquidity_regime,
    )
    return ResearchMarketProbabilityLiquidityRegimeRow(
        case_digest=observation.case_digest,
        rank=rank,
        observed_at=observation.observed_at,
        market_probability=observation.market_probability,
        probability_band=probability_band,
        probability_extremity_score=probability_extremity_score,
        spread_rate=observation.spread_rate,
        spread_quality_score=spread_quality_score,
        depth_score=observation.depth_score,
        cost_rate=observation.cost_rate,
        cost_quality_score=cost_quality_score,
        liquidity_score=liquidity_score,
        liquidity_regime=liquidity_regime,
        regime=f"{probability_band}_{liquidity_regime}",
        status=status,
        manual_review_required=status != "pass",
        upstream_reason_codes=observation.upstream_reason_codes,
        reason_codes=_row_reason_codes(
            probability_band=probability_band,
            liquidity_regime=liquidity_regime,
            status=status,
            spread_status=spread_status,
            depth_status=depth_status,
            cost_status=cost_status,
            upstream_reason_codes=observation.upstream_reason_codes,
        ),
        validation_config=config,
    )


def _copy_row_with_rank(
    row: ResearchMarketProbabilityLiquidityRegimeRow,
    *,
    rank: Decimal,
    config: ResearchMarketProbabilityLiquidityRegimeConfig,
) -> ResearchMarketProbabilityLiquidityRegimeRow:
    return ResearchMarketProbabilityLiquidityRegimeRow(
        case_digest=row.case_digest,
        rank=rank,
        observed_at=row.observed_at,
        market_probability=row.market_probability,
        probability_band=row.probability_band,
        probability_extremity_score=row.probability_extremity_score,
        spread_rate=row.spread_rate,
        spread_quality_score=row.spread_quality_score,
        depth_score=row.depth_score,
        cost_rate=row.cost_rate,
        cost_quality_score=row.cost_quality_score,
        liquidity_score=row.liquidity_score,
        liquidity_regime=row.liquidity_regime,
        regime=row.regime,
        status=row.status,
        manual_review_required=row.manual_review_required,
        upstream_reason_codes=row.upstream_reason_codes,
        reason_codes=row.reason_codes,
        validation_config=config,
    )


def _probability_band(
    probability: Decimal,
    *,
    config: ResearchMarketProbabilityLiquidityRegimeConfig,
) -> str:
    with localcontext(DECIMAL_CONTEXT):
        high_tail_minimum = _quantize(ONE - config.tail_probability_max)
    if probability <= config.tail_probability_max:
        return "low_tail"
    if probability >= high_tail_minimum:
        return "high_tail"
    return "central"


def _probability_extremity_score(probability: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(probability - HALF) * Decimal("2"))


def _ceiling_quality_score(value: Decimal, *, ceiling: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_unit(ONE - (value / ceiling))


def _ceiling_status(
    value: Decimal,
    *,
    pass_limit: Decimal,
    watch_limit: Decimal,
) -> str:
    if value > watch_limit:
        return "block"
    if value > pass_limit:
        return "watch"
    return "pass"


def _floor_status(
    value: Decimal,
    *,
    pass_limit: Decimal,
    watch_limit: Decimal,
) -> str:
    if value < watch_limit:
        return "block"
    if value < pass_limit:
        return "watch"
    return "pass"


def _liquidity_regime(
    *,
    spread_status: str,
    depth_status: str,
    cost_status: str,
) -> str:
    statuses = (spread_status, depth_status, cost_status)
    if "block" in statuses:
        return "fragile"
    if "watch" in statuses:
        return "constrained"
    return "robust"


def _row_status(*, probability_band: str, liquidity_regime: str) -> str:
    if liquidity_regime == "fragile":
        return "block"
    if liquidity_regime == "constrained" or probability_band != "central":
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    probability_band: str,
    liquidity_regime: str,
    status: str,
    spread_status: str,
    depth_status: str,
    cost_status: str,
    upstream_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reasons = [
        f"probability_liquidity_regime_status_{status}",
        f"probability_band_{probability_band}",
        f"liquidity_regime_{liquidity_regime}",
    ]
    for component_name, component_status in (
        ("spread", spread_status),
        ("depth", depth_status),
        ("cost", cost_status),
    ):
        if component_status != "pass":
            reasons.append(f"{component_name}_{component_status}")
    reasons.extend(upstream_reason_codes)
    return tuple(reasons)


def _report_status(
    rows: tuple[ResearchMarketProbabilityLiquidityRegimeRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketProbabilityLiquidityRegimeRow, ...],
    *,
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("probability_liquidity_regime_report_empty",)
    reasons = [f"probability_liquidity_regime_report_{status}"]
    if any(row.probability_band != "central" for row in rows):
        reasons.append("probability_tail_present")
    for regime in ("fragile", "constrained", "robust"):
        if any(row.liquidity_regime == regime for row in rows):
            reasons.append(f"liquidity_{regime}_present")
    if any(row.manual_review_required for row in rows):
        reasons.append("manual_review_required")
    return tuple(reasons)


def _reason_code_counts(
    rows: tuple[ResearchMarketProbabilityLiquidityRegimeRow, ...],
) -> tuple[ResearchMarketProbabilityLiquidityRegimeReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    )
    denominator = _count_decimal(len(rows))
    return tuple(
        ResearchMarketProbabilityLiquidityRegimeReasonCodeCount(
            reason_code=reason_code,
            row_count=_count_decimal(count),
            row_ratio=_divide_decimal(_count_decimal(count), denominator),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_observations(
    observations: Iterable[ResearchMarketProbabilityLiquidityRegimeObservation],
) -> tuple[ResearchMarketProbabilityLiquidityRegimeObservation, ...]:
    if isinstance(observations, (str, bytes, dict)):
        raise ValueError("observations must be an iterable of observations")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable of observations") from exc
    seen: set[str] = set()
    for value in values:
        _require_exact_type(
            value,
            ResearchMarketProbabilityLiquidityRegimeObservation,
            "observation",
        )
        _require_hard_flags("observation", value)
        if value.case_digest in seen:
            raise ValueError("case_digest values must be unique")
        seen.add(value.case_digest)
    return values


def _normalize_rows(
    rows: object,
    *,
    config: ResearchMarketProbabilityLiquidityRegimeConfig,
) -> tuple[ResearchMarketProbabilityLiquidityRegimeRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        _require_exact_type(
            row,
            ResearchMarketProbabilityLiquidityRegimeRow,
            "row",
        )
        _require_hard_flags("row", row)
        if row.case_digest in seen:
            raise ValueError("row case_digest values must be unique")
        seen.add(row.case_digest)
        _validate_row_consistency(row, config=config)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    expected_ranks = tuple(
        _count_decimal(index)
        for index in range(1, len(normalized) + 1)
    )
    if tuple(row.rank for row in normalized) != expected_ranks:
        raise ValueError("rows must use sequential ranks")
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchMarketProbabilityLiquidityRegimeReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(values)
    seen: set[str] = set()
    for value in normalized:
        _require_exact_type(
            value,
            ResearchMarketProbabilityLiquidityRegimeReasonCodeCount,
            "reason code count",
        )
        _require_hard_flags("reason code count", value)
        if value.reason_code in seen:
            raise ValueError("reason_code_counts must not repeat reason codes")
        seen.add(value.reason_code)
    expected = tuple(
        sorted(
            normalized,
            key=lambda value: (-value.row_count, value.reason_code),
        ),
    )
    if normalized != expected:
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _validate_row_consistency(
    row: ResearchMarketProbabilityLiquidityRegimeRow,
    *,
    config: ResearchMarketProbabilityLiquidityRegimeConfig,
) -> None:
    expected_band = _probability_band(row.market_probability, config=config)
    if row.probability_band != expected_band:
        raise ValueError("probability_band must match market_probability")
    expected_extremity = _probability_extremity_score(row.market_probability)
    if row.probability_extremity_score != expected_extremity:
        raise ValueError(
            "probability_extremity_score must match market_probability",
        )
    expected_spread_quality = _ceiling_quality_score(
        row.spread_rate,
        ceiling=config.max_watch_spread_rate,
    )
    if row.spread_quality_score != expected_spread_quality:
        raise ValueError("spread_quality_score must match spread_rate")
    expected_cost_quality = _ceiling_quality_score(
        row.cost_rate,
        ceiling=config.max_watch_cost_rate,
    )
    if row.cost_quality_score != expected_cost_quality:
        raise ValueError("cost_quality_score must match cost_rate")
    expected_liquidity_score = _average_decimal(
        (
            row.spread_quality_score,
            row.depth_score,
            row.cost_quality_score,
        ),
    )
    if row.liquidity_score != expected_liquidity_score:
        raise ValueError("liquidity_score must match liquidity components")

    spread_status = _ceiling_status(
        row.spread_rate,
        pass_limit=config.max_pass_spread_rate,
        watch_limit=config.max_watch_spread_rate,
    )
    depth_status = _floor_status(
        row.depth_score,
        pass_limit=config.min_pass_depth_score,
        watch_limit=config.min_watch_depth_score,
    )
    cost_status = _ceiling_status(
        row.cost_rate,
        pass_limit=config.max_pass_cost_rate,
        watch_limit=config.max_watch_cost_rate,
    )
    expected_liquidity_regime = _liquidity_regime(
        spread_status=spread_status,
        depth_status=depth_status,
        cost_status=cost_status,
    )
    if row.liquidity_regime != expected_liquidity_regime:
        raise ValueError("liquidity_regime must match component statuses")
    expected_regime = f"{expected_band}_{expected_liquidity_regime}"
    if row.regime != expected_regime:
        raise ValueError("regime must match probability and liquidity regimes")
    expected_status = _row_status(
        probability_band=expected_band,
        liquidity_regime=expected_liquidity_regime,
    )
    if row.status != expected_status:
        raise ValueError("status must match row values")
    if row.manual_review_required != (expected_status != "pass"):
        raise ValueError("manual_review_required must match status")
    expected_reasons = _row_reason_codes(
        probability_band=expected_band,
        liquidity_regime=expected_liquidity_regime,
        status=expected_status,
        spread_status=spread_status,
        depth_status=depth_status,
        cost_status=cost_status,
        upstream_reason_codes=row.upstream_reason_codes,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row values")


def _validate_report_consistency(
    report: ResearchMarketProbabilityLiquidityRegimeReport,
) -> None:
    rows = report.rows
    if any(row.observed_at > report.generated_at for row in rows):
        raise ValueError("generated_at must not be before observed_at")
    expected_values = {
        "observation_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "tail_count": _tail_count(rows),
        "robust_count": _liquidity_regime_count(rows, "robust"),
        "constrained_count": _liquidity_regime_count(rows, "constrained"),
        "fragile_count": _liquidity_regime_count(rows, "fragile"),
        "manual_review_count": _manual_review_count(rows),
        "average_market_probability": _average_decimal(
            tuple(row.market_probability for row in rows),
        ),
        "average_liquidity_score": _average_decimal(
            tuple(row.liquidity_score for row in rows),
        ),
        "minimum_depth_score": min(
            (row.depth_score for row in rows),
            default=ZERO,
        ),
        "maximum_spread_rate": max(
            (row.spread_rate for row in rows),
            default=ZERO,
        ),
        "maximum_cost_rate": max(
            (row.cost_rate for row in rows),
            default=ZERO,
        ),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    expected_status = _report_status(rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(rows, status=expected_status)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_reason_counts = _reason_code_counts(rows)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")


def _row_sort_key(
    row: ResearchMarketProbabilityLiquidityRegimeRow,
) -> tuple[int, Decimal, Decimal, str]:
    with localcontext(DECIMAL_CONTEXT):
        return (
            STATUS_SORT_RANK[row.status],
            row.liquidity_score,
            -row.probability_extremity_score,
            row.case_digest,
        )


def _status_count(
    rows: tuple[ResearchMarketProbabilityLiquidityRegimeRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _tail_count(
    rows: tuple[ResearchMarketProbabilityLiquidityRegimeRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if row.probability_band != "central"),
    )


def _liquidity_regime_count(
    rows: tuple[ResearchMarketProbabilityLiquidityRegimeRow, ...],
    regime: str,
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if row.liquidity_regime == regime),
    )


def _manual_review_count(
    rows: tuple[ResearchMarketProbabilityLiquidityRegimeRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if row.manual_review_required),
    )


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _clamp_unit(value: Decimal) -> Decimal:
    return _quantize(min(max(value, ZERO), ONE))


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _tail_boundary_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw <= ZERO or raw > HALF:
        raise ValueError(f"{field_name} must be between 0 and 0.5")
    return _quantize(raw)


def _unit_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if raw > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(raw)


def _positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        integral_value = raw.to_integral_value()
    if raw != integral_value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(raw)


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc
    if normalized.is_zero() and normalized.is_signed():
        return ZERO
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if not all(
        character.islower() or character.isdigit() or character == "_"
        for character in value
    ):
        raise ValueError(f"{field_name} must use lower snake case")
    if any(fragment in value for fragment in _UNSAFE_REASON_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public content")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
    sort_values: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        reason_code = _require_reason_code("reason_code", item)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
        normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    if sort_values:
        normalized.sort()
    return tuple(normalized)


def _require_choice(
    field_name: str,
    value: object,
    choices: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in choices:
        raise ValueError(
            f"{field_name} must be one of {', '.join(choices)}",
        )
    return value


def _require_regime(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    allowed = {
        f"{probability_band}_{liquidity_regime}"
        for probability_band in PROBABILITY_BANDS
        for liquidity_regime in LIQUIDITY_REGIMES
    }
    if value not in allowed:
        raise ValueError(f"{field_name} must be a known regime")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(
    value: object,
    expected_type: type[object],
    label: str,
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _report_payload(
    report: ResearchMarketProbabilityLiquidityRegimeReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "config": _config_payload(report.config),
        "observation_count": _decimal_string(report.observation_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "tail_count": _decimal_string(report.tail_count),
        "robust_count": _decimal_string(report.robust_count),
        "constrained_count": _decimal_string(report.constrained_count),
        "fragile_count": _decimal_string(report.fragile_count),
        "manual_review_count": _decimal_string(report.manual_review_count),
        "average_market_probability": _decimal_string(
            report.average_market_probability,
        ),
        "average_liquidity_score": _decimal_string(
            report.average_liquidity_score,
        ),
        "minimum_depth_score": _decimal_string(report.minimum_depth_score),
        "maximum_spread_rate": _decimal_string(report.maximum_spread_rate),
        "maximum_cost_rate": _decimal_string(report.maximum_cost_rate),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_count_payload(value)
            for value in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    payload.update(
        {
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    return payload


def _config_payload(
    config: ResearchMarketProbabilityLiquidityRegimeConfig,
) -> dict[str, Any]:
    return {
        "config_version": config.config_version,
        "tail_probability_max": _decimal_string(config.tail_probability_max),
        "max_pass_spread_rate": _decimal_string(config.max_pass_spread_rate),
        "max_watch_spread_rate": _decimal_string(config.max_watch_spread_rate),
        "min_pass_depth_score": _decimal_string(config.min_pass_depth_score),
        "min_watch_depth_score": _decimal_string(config.min_watch_depth_score),
        "max_pass_cost_rate": _decimal_string(config.max_pass_cost_rate),
        "max_watch_cost_rate": _decimal_string(config.max_watch_cost_rate),
        "paper_only": config.paper_only,
        "report_only": config.report_only,
        "readonly": config.readonly,
    }


def _row_payload(
    row: ResearchMarketProbabilityLiquidityRegimeRow,
) -> dict[str, Any]:
    return {
        "case_digest": row.case_digest,
        "rank": _decimal_string(row.rank),
        "observed_at": row.observed_at.isoformat(),
        "market_probability": _decimal_string(row.market_probability),
        "probability_band": row.probability_band,
        "probability_extremity_score": _decimal_string(
            row.probability_extremity_score,
        ),
        "spread_rate": _decimal_string(row.spread_rate),
        "spread_quality_score": _decimal_string(row.spread_quality_score),
        "depth_score": _decimal_string(row.depth_score),
        "cost_rate": _decimal_string(row.cost_rate),
        "cost_quality_score": _decimal_string(row.cost_quality_score),
        "liquidity_score": _decimal_string(row.liquidity_score),
        "liquidity_regime": row.liquidity_regime,
        "regime": row.regime,
        "status": row.status,
        "manual_review_required": row.manual_review_required,
        "upstream_reason_codes": list(row.upstream_reason_codes),
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_count_payload(
    value: ResearchMarketProbabilityLiquidityRegimeReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": value.reason_code,
        "row_count": _decimal_string(value.row_count),
        "row_ratio": _decimal_string(value.row_ratio),
        "paper_only": value.paper_only,
        "report_only": value.report_only,
        "readonly": value.readonly,
    }


def _report_digest(
    report: ResearchMarketProbabilityLiquidityRegimeReport,
) -> str:
    return _digest_payload(_report_payload(report, include_digest=False))


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _decimal_string(value: Decimal) -> str:
    return f"{value:.6f}"


def _config_from_payload(
    value: object,
) -> ResearchMarketProbabilityLiquidityRegimeConfig:
    mapping = _dict_from_payload("config", value)
    _require_exact_keys("config", mapping, CONFIG_PAYLOAD_KEYS)
    _require_payload_hard_flags("config", mapping)
    return ResearchMarketProbabilityLiquidityRegimeConfig(
        config_version=_string_from_payload(
            "config.config_version",
            mapping["config_version"],
        ),
        tail_probability_max=_tail_from_payload(
            "config.tail_probability_max",
            mapping["tail_probability_max"],
        ),
        max_pass_spread_rate=_unit_from_payload(
            "config.max_pass_spread_rate",
            mapping["max_pass_spread_rate"],
        ),
        max_watch_spread_rate=_unit_from_payload(
            "config.max_watch_spread_rate",
            mapping["max_watch_spread_rate"],
        ),
        min_pass_depth_score=_unit_from_payload(
            "config.min_pass_depth_score",
            mapping["min_pass_depth_score"],
        ),
        min_watch_depth_score=_unit_from_payload(
            "config.min_watch_depth_score",
            mapping["min_watch_depth_score"],
        ),
        max_pass_cost_rate=_unit_from_payload(
            "config.max_pass_cost_rate",
            mapping["max_pass_cost_rate"],
        ),
        max_watch_cost_rate=_unit_from_payload(
            "config.max_watch_cost_rate",
            mapping["max_watch_cost_rate"],
        ),
        paper_only=_true_from_payload(
            "config.paper_only",
            mapping["paper_only"],
        ),
        report_only=_true_from_payload(
            "config.report_only",
            mapping["report_only"],
        ),
        readonly=_true_from_payload("config.readonly", mapping["readonly"]),
    )


def _row_from_payload(
    value: object,
    *,
    index: int,
    config: ResearchMarketProbabilityLiquidityRegimeConfig,
) -> ResearchMarketProbabilityLiquidityRegimeRow:
    path = f"rows[{index}]"
    mapping = _dict_from_payload(path, value)
    _require_exact_keys(path, mapping, ROW_PAYLOAD_KEYS)
    _require_payload_hard_flags(path, mapping)
    try:
        row = ResearchMarketProbabilityLiquidityRegimeRow(
            case_digest=_digest_from_payload(
                f"{path}.case_digest",
                mapping["case_digest"],
            ),
            rank=_positive_count_from_payload(
                f"{path}.rank",
                mapping["rank"],
            ),
            observed_at=_datetime_from_payload(
                f"{path}.observed_at",
                mapping["observed_at"],
            ),
            market_probability=_unit_from_payload(
                f"{path}.market_probability",
                mapping["market_probability"],
            ),
            probability_band=_choice_from_payload(
                f"{path}.probability_band",
                mapping["probability_band"],
                PROBABILITY_BANDS,
            ),
            probability_extremity_score=_unit_from_payload(
                f"{path}.probability_extremity_score",
                mapping["probability_extremity_score"],
            ),
            spread_rate=_unit_from_payload(
                f"{path}.spread_rate",
                mapping["spread_rate"],
            ),
            spread_quality_score=_unit_from_payload(
                f"{path}.spread_quality_score",
                mapping["spread_quality_score"],
            ),
            depth_score=_unit_from_payload(
                f"{path}.depth_score",
                mapping["depth_score"],
            ),
            cost_rate=_unit_from_payload(
                f"{path}.cost_rate",
                mapping["cost_rate"],
            ),
            cost_quality_score=_unit_from_payload(
                f"{path}.cost_quality_score",
                mapping["cost_quality_score"],
            ),
            liquidity_score=_unit_from_payload(
                f"{path}.liquidity_score",
                mapping["liquidity_score"],
            ),
            liquidity_regime=_choice_from_payload(
                f"{path}.liquidity_regime",
                mapping["liquidity_regime"],
                LIQUIDITY_REGIMES,
            ),
            regime=_regime_from_payload(f"{path}.regime", mapping["regime"]),
            status=_choice_from_payload(
                f"{path}.status",
                mapping["status"],
                STATUSES,
            ),
            manual_review_required=_bool_from_payload(
                f"{path}.manual_review_required",
                mapping["manual_review_required"],
            ),
            upstream_reason_codes=_reason_codes_from_payload(
                f"{path}.upstream_reason_codes",
                mapping["upstream_reason_codes"],
                allow_empty=True,
                sort_values=True,
            ),
            reason_codes=_reason_codes_from_payload(
                f"{path}.reason_codes",
                mapping["reason_codes"],
                allow_empty=False,
                sort_values=False,
            ),
            paper_only=_true_from_payload(
                f"{path}.paper_only",
                mapping["paper_only"],
            ),
            report_only=_true_from_payload(
                f"{path}.report_only",
                mapping["report_only"],
            ),
            readonly=_true_from_payload(
                f"{path}.readonly",
                mapping["readonly"],
            ),
            validation_config=config,
        )
        return row
    except ValueError as exc:
        message = str(exc)
        if message.startswith(path):
            raise
        raise ValueError(f"{path}.{message}") from exc


def _reason_count_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchMarketProbabilityLiquidityRegimeReasonCodeCount:
    path = f"reason_code_counts[{index}]"
    mapping = _dict_from_payload(path, value)
    _require_exact_keys(path, mapping, REASON_COUNT_PAYLOAD_KEYS)
    _require_payload_hard_flags(path, mapping)
    try:
        return ResearchMarketProbabilityLiquidityRegimeReasonCodeCount(
            reason_code=_reason_from_payload(
                f"{path}.reason_code",
                mapping["reason_code"],
            ),
            row_count=_count_from_payload(
                f"{path}.row_count",
                mapping["row_count"],
            ),
            row_ratio=_unit_from_payload(
                f"{path}.row_ratio",
                mapping["row_ratio"],
            ),
            paper_only=_true_from_payload(
                f"{path}.paper_only",
                mapping["paper_only"],
            ),
            report_only=_true_from_payload(
                f"{path}.report_only",
                mapping["report_only"],
            ),
            readonly=_true_from_payload(
                f"{path}.readonly",
                mapping["readonly"],
            ),
        )
    except ValueError as exc:
        message = str(exc)
        if message.startswith(path):
            raise
        raise ValueError(f"{path}.{message}") from exc


def _require_exact_keys(
    path: str,
    mapping: dict[str, Any],
    expected: tuple[str, ...],
) -> None:
    if (
        any(type(key) is not str for key in mapping)
        or set(mapping) != set(expected)
    ):
        raise ValueError(f"{path} must use exact schema")


def _require_payload_hard_flags(
    path: str,
    mapping: dict[str, Any],
) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if mapping.get(field_name) is not True:
            raise ValueError(f"{path}.{field_name} must be True")


def _validate_payload_shape_and_scalars(payload: dict[str, Any]) -> None:
    _datetime_from_payload("generated_at", payload["generated_at"])
    _string_from_payload("config_version", payload["config_version"])
    for field_name in (
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "tail_count",
        "robust_count",
        "constrained_count",
        "fragile_count",
        "manual_review_count",
    ):
        _count_from_payload(field_name, payload[field_name])
    for field_name in (
        "average_market_probability",
        "average_liquidity_score",
        "minimum_depth_score",
        "maximum_spread_rate",
        "maximum_cost_rate",
    ):
        _unit_from_payload(field_name, payload[field_name])
    _choice_from_payload("status", payload["status"], STATUSES)
    _reason_codes_from_payload(
        "reason_codes",
        payload["reason_codes"],
        allow_empty=False,
        sort_values=False,
    )

    config_payload = _dict_from_payload("config", payload["config"])
    _require_exact_keys("config", config_payload, CONFIG_PAYLOAD_KEYS)
    _require_payload_hard_flags("config", config_payload)
    _string_from_payload(
        "config.config_version",
        config_payload["config_version"],
    )
    _tail_from_payload(
        "config.tail_probability_max",
        config_payload["tail_probability_max"],
    )
    for field_name in (
        "max_pass_spread_rate",
        "max_watch_spread_rate",
        "min_pass_depth_score",
        "min_watch_depth_score",
        "max_pass_cost_rate",
        "max_watch_cost_rate",
    ):
        _unit_from_payload(
            f"config.{field_name}",
            config_payload[field_name],
        )

    rows_payload = _list_from_payload("rows", payload["rows"])
    for index, row_value in enumerate(rows_payload):
        path = f"rows[{index}]"
        row_payload = _dict_from_payload(path, row_value)
        _require_exact_keys(path, row_payload, ROW_PAYLOAD_KEYS)
        _require_payload_hard_flags(path, row_payload)
        _digest_from_payload(f"{path}.case_digest", row_payload["case_digest"])
        _positive_count_from_payload(f"{path}.rank", row_payload["rank"])
        _datetime_from_payload(f"{path}.observed_at", row_payload["observed_at"])
        for field_name in (
            "market_probability",
            "probability_extremity_score",
            "spread_rate",
            "spread_quality_score",
            "depth_score",
            "cost_rate",
            "cost_quality_score",
            "liquidity_score",
        ):
            _unit_from_payload(
                f"{path}.{field_name}",
                row_payload[field_name],
            )
        _choice_from_payload(
            f"{path}.probability_band",
            row_payload["probability_band"],
            PROBABILITY_BANDS,
        )
        _choice_from_payload(
            f"{path}.liquidity_regime",
            row_payload["liquidity_regime"],
            LIQUIDITY_REGIMES,
        )
        _regime_from_payload(f"{path}.regime", row_payload["regime"])
        _choice_from_payload(
            f"{path}.status",
            row_payload["status"],
            STATUSES,
        )
        _bool_from_payload(
            f"{path}.manual_review_required",
            row_payload["manual_review_required"],
        )
        _reason_codes_from_payload(
            f"{path}.upstream_reason_codes",
            row_payload["upstream_reason_codes"],
            allow_empty=True,
            sort_values=True,
        )
        _reason_codes_from_payload(
            f"{path}.reason_codes",
            row_payload["reason_codes"],
            allow_empty=False,
            sort_values=False,
        )

    counts_payload = _list_from_payload(
        "reason_code_counts",
        payload["reason_code_counts"],
    )
    for index, count_value in enumerate(counts_payload):
        path = f"reason_code_counts[{index}]"
        count_payload = _dict_from_payload(path, count_value)
        _require_exact_keys(path, count_payload, REASON_COUNT_PAYLOAD_KEYS)
        _require_payload_hard_flags(path, count_payload)
        _reason_from_payload(
            f"{path}.reason_code",
            count_payload["reason_code"],
        )
        _count_from_payload(f"{path}.row_count", count_payload["row_count"])
        _unit_from_payload(f"{path}.row_ratio", count_payload["row_ratio"])


def _dict_from_payload(path: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{path} must be a dict")
    return value


def _list_from_payload(path: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    return value


def _string_from_payload(path: str, value: object) -> str:
    if type(value) is not str or value == "" or value != value.strip():
        raise ValueError(f"{path} must be a canonical string")
    return value


def _digest_from_payload(path: str, value: object) -> str:
    return _require_sha256_digest(path, value)


def _reason_from_payload(path: str, value: object) -> str:
    try:
        return _require_reason_code(path, value)
    except ValueError:
        raise


def _decimal_from_payload(path: str, value: object) -> Decimal:
    if type(value) is not str or CANONICAL_DECIMAL_PATTERN.fullmatch(value) is None:
        if type(value) is str and value.startswith("-0."):
            raise ValueError(f"{path} must not use signed zero")
        raise ValueError(f"{path} must be a canonical Decimal string")
    parsed = Decimal(value)
    if parsed.is_zero() and parsed.is_signed():
        raise ValueError(f"{path} must not use signed zero")
    return parsed


def _unit_from_payload(path: str, value: object) -> Decimal:
    return _unit_decimal(path, _decimal_from_payload(path, value))


def _tail_from_payload(path: str, value: object) -> Decimal:
    return _tail_boundary_decimal(path, _decimal_from_payload(path, value))


def _count_from_payload(path: str, value: object) -> Decimal:
    return _nonnegative_count_decimal(path, _decimal_from_payload(path, value))


def _positive_count_from_payload(path: str, value: object) -> Decimal:
    return _positive_count_decimal(path, _decimal_from_payload(path, value))


def _datetime_from_payload(path: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{path} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{path} must be a canonical UTC datetime string",
        ) from exc
    normalized = _as_utc(path, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{path} must be a canonical UTC datetime string")
    return normalized


def _choice_from_payload(
    path: str,
    value: object,
    choices: tuple[str, ...],
) -> str:
    return _require_choice(path, value, choices)


def _regime_from_payload(path: str, value: object) -> str:
    return _require_regime(path, value)


def _bool_from_payload(path: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{path} must be a bool")
    return value


def _true_from_payload(path: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{path} must be True")
    return True


def _reason_codes_from_payload(
    path: str,
    value: object,
    *,
    allow_empty: bool,
    sort_values: bool,
) -> tuple[str, ...]:
    values = _list_from_payload(path, value)
    try:
        return _normalize_reason_codes(
            path,
            tuple(values),
            allow_empty=allow_empty,
            sort_values=sort_values,
        )
    except ValueError:
        raise


def _copy_json_value(value: object) -> Any:
    if type(value) is dict:
        return {
            key: _copy_json_value(item)
            for key, item in value.items()
        }
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    return value


def _assert_payload_equal(
    actual: object,
    expected: object,
    *,
    path: str,
) -> None:
    if type(actual) is not type(expected):
        raise ValueError(f"{path} must match recomputed report")
    if type(expected) is dict:
        actual_mapping = actual
        expected_mapping = expected
        if set(actual_mapping) != set(expected_mapping):
            raise ValueError(f"{path} must use exact schema")
        for key in expected_mapping:
            _assert_payload_equal(
                actual_mapping[key],
                expected_mapping[key],
                path=f"{path}.{key}",
            )
        return
    if type(expected) is list:
        actual_list = actual
        expected_list = expected
        if len(actual_list) != len(expected_list):
            raise ValueError(f"{path} must match recomputed report")
        for index, expected_item in enumerate(expected_list):
            _assert_payload_equal(
                actual_list[index],
                expected_item,
                path=f"{path}[{index}]",
            )
        return
    if actual != expected:
        raise ValueError(f"{path} must match recomputed report")
