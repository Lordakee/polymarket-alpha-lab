"""Phase 1 report-only liquidity-decay-adjusted EV candidate scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_STRATEGY_CANDIDATE_LIQUIDITY_DECAY_ADJUSTED_EV_V2_CONFIG_VERSION = (
    "strategy-candidate-liquidity-decay-adjusted-ev-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_UNSAFE_PUBLIC_TERMS = (
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
)
_REASON_CODE_SEQUENCE = (
    "negative_adjusted_ev",
    "low_adjusted_ev_watch",
    "positive_adjusted_ev",
    "liquidity_decay_penalty",
    "shallow_depth_penalty",
    "stable_liquidity_boost",
)


@dataclass(frozen=True)
class StrategyCandidateLiquidityDecayAdjustedEvV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_LIQUIDITY_DECAY_ADJUSTED_EV_V2_CONFIG_VERSION
    )
    minimum_top_depth_usd: Decimal = Decimal("1000.000000")
    shallow_depth_penalty_rate: Decimal = Decimal("0.050000")
    stable_liquidity_threshold: Decimal = Decimal("0.800000")
    stable_liquidity_boost_rate: Decimal = Decimal("0.020000")
    minimum_adjusted_ev_score: Decimal = Decimal("0.010000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateLiquidityDecayAdjustedEvV2Config:
            raise TypeError(
                "StrategyCandidateLiquidityDecayAdjustedEvV2Config does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateLiquidityDecayAdjustedEvV2Config:
            raise ValueError(
                "config must be exactly "
                "StrategyCandidateLiquidityDecayAdjustedEvV2Config",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_CANDIDATE_LIQUIDITY_DECAY_ADJUSTED_EV_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "minimum_top_depth_usd",
            _require_positive_decimal("minimum_top_depth_usd", self.minimum_top_depth_usd),
        )
        for field_name in (
            "shallow_depth_penalty_rate",
            "stable_liquidity_threshold",
            "stable_liquidity_boost_rate",
            "minimum_adjusted_ev_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class StrategyCandidateLiquidityDecayAdjustedEvV2Candidate:
    candidate_id: str
    market_id: str
    evaluated_at: datetime
    model_probability: Decimal
    market_probability: Decimal
    fee_drag: Decimal
    top_depth_usd: Decimal
    depth_decay_ratio: Decimal
    liquidity_stability_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateLiquidityDecayAdjustedEvV2Candidate:
            raise TypeError(
                "StrategyCandidateLiquidityDecayAdjustedEvV2Candidate does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateLiquidityDecayAdjustedEvV2Candidate:
            raise ValueError(
                "candidate must be exactly "
                "StrategyCandidateLiquidityDecayAdjustedEvV2Candidate",
            )
        _require_public_identifier("candidate_id", self.candidate_id)
        _require_public_identifier("market_id", self.market_id)
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        for field_name in (
            "model_probability",
            "market_probability",
            "fee_drag",
            "depth_decay_ratio",
            "liquidity_stability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "top_depth_usd",
            _require_nonnegative_decimal("top_depth_usd", self.top_depth_usd),
        )
        _require_hard_flags("candidate", self)
        _reject_unsafe_public_payload("candidate", self)


@dataclass(frozen=True)
class StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem:
            raise TypeError(
                "StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class StrategyCandidateLiquidityDecayAdjustedEvV2Row:
    candidate_id: str
    market_id: str
    evaluated_at: datetime
    model_probability: Decimal
    market_probability: Decimal
    fee_drag: Decimal
    top_depth_usd: Decimal
    depth_decay_ratio: Decimal
    liquidity_stability_score: Decimal
    raw_ev_score: Decimal
    depth_penalty: Decimal
    liquidity_decay_penalty: Decimal
    stable_liquidity_boost: Decimal
    adjusted_ev_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateLiquidityDecayAdjustedEvV2Row:
            raise TypeError(
                "StrategyCandidateLiquidityDecayAdjustedEvV2Row does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateLiquidityDecayAdjustedEvV2Row:
            raise ValueError(
                "row must be exactly StrategyCandidateLiquidityDecayAdjustedEvV2Row",
            )
        _require_public_identifier("candidate_id", self.candidate_id)
        _require_public_identifier("market_id", self.market_id)
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        for field_name in (
            "model_probability",
            "market_probability",
            "fee_drag",
            "depth_decay_ratio",
            "liquidity_stability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "top_depth_usd",
            _require_nonnegative_decimal("top_depth_usd", self.top_depth_usd),
        )
        for field_name in (
            "raw_ev_score",
            "depth_penalty",
            "liquidity_decay_penalty",
            "stable_liquidity_boost",
            "adjusted_ev_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class StrategyCandidateLiquidityDecayAdjustedEvV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_adjusted_ev_score: Decimal
    rows: tuple[StrategyCandidateLiquidityDecayAdjustedEvV2Row, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateLiquidityDecayAdjustedEvV2Report:
            raise TypeError(
                "StrategyCandidateLiquidityDecayAdjustedEvV2Report does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateLiquidityDecayAdjustedEvV2Report:
            raise ValueError(
                "report must be exactly StrategyCandidateLiquidityDecayAdjustedEvV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_CANDIDATE_LIQUIDITY_DECAY_ADJUSTED_EV_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("report_status", self.report_status)
        for field_name in ("candidate_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_adjusted_ev_score",
            _require_score_decimal(
                "average_adjusted_ev_score",
                self.average_adjusted_ev_score,
            ),
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
        _reject_unsafe_public_payload("payload", payload)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_strategy_candidate_liquidity_decay_adjusted_ev_v2_report(
    candidates: Sequence[StrategyCandidateLiquidityDecayAdjustedEvV2Candidate],
    *,
    generated_at: datetime,
    config: StrategyCandidateLiquidityDecayAdjustedEvV2Config | None = None,
    public_payload: Sequence[StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem] = (),
) -> StrategyCandidateLiquidityDecayAdjustedEvV2Report:
    """Build a local paper-only liquidity-decay-adjusted EV report."""

    if config is None:
        config = StrategyCandidateLiquidityDecayAdjustedEvV2Config()
    if type(config) is not StrategyCandidateLiquidityDecayAdjustedEvV2Config:
        raise ValueError(
            "config must be a StrategyCandidateLiquidityDecayAdjustedEvV2Config",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    for candidate in normalized_candidates:
        if candidate.evaluated_at > generated_at:
            raise ValueError("candidate evaluated_at must not be after generated_at")
    rows = tuple(
        _row_from_candidate(candidate, config)
        for candidate in sorted(
            normalized_candidates,
            key=lambda item: (item.candidate_id, item.market_id),
        )
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "candidate_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "blocked_count": _decimal_count(_status_count(rows, "block")),
        "average_adjusted_ev_score": _average(
            tuple(row.adjusted_ev_score for row in rows),
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": _normalize_public_payload(public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyCandidateLiquidityDecayAdjustedEvV2Report(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def strategy_candidate_liquidity_decay_adjusted_ev_v2_payload(
    value: StrategyCandidateLiquidityDecayAdjustedEvV2Report | Mapping[str, object],
) -> dict[str, object]:
    """Return and validate the JSON-ready report payload."""

    if type(value) is StrategyCandidateLiquidityDecayAdjustedEvV2Report:
        return value.payload
    if isinstance(value, Mapping):
        payload = _json_ready(dict(value))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        _require_payload_digest(payload)
        return payload
    raise ValueError(
        "value must be a StrategyCandidateLiquidityDecayAdjustedEvV2Report or payload dict",
    )


def _row_from_candidate(
    candidate: StrategyCandidateLiquidityDecayAdjustedEvV2Candidate,
    config: StrategyCandidateLiquidityDecayAdjustedEvV2Config,
) -> StrategyCandidateLiquidityDecayAdjustedEvV2Row:
    edge_before_fee = _quantize(candidate.model_probability - candidate.market_probability)
    raw_ev_score = _quantize(edge_before_fee - candidate.fee_drag)
    liquidity_decay_penalty = _clamp_nonnegative(edge_before_fee * candidate.depth_decay_ratio)
    depth_penalty = _depth_penalty(candidate.top_depth_usd, config)
    stable_liquidity_boost = _stable_liquidity_boost(candidate, config)
    adjusted_ev_score = _quantize(
        raw_ev_score
        - liquidity_decay_penalty
        - depth_penalty
        + stable_liquidity_boost,
    )
    return StrategyCandidateLiquidityDecayAdjustedEvV2Row(
        candidate_id=candidate.candidate_id,
        market_id=candidate.market_id,
        evaluated_at=candidate.evaluated_at,
        model_probability=candidate.model_probability,
        market_probability=candidate.market_probability,
        fee_drag=candidate.fee_drag,
        top_depth_usd=candidate.top_depth_usd,
        depth_decay_ratio=candidate.depth_decay_ratio,
        liquidity_stability_score=candidate.liquidity_stability_score,
        raw_ev_score=raw_ev_score,
        depth_penalty=depth_penalty,
        liquidity_decay_penalty=liquidity_decay_penalty,
        stable_liquidity_boost=stable_liquidity_boost,
        adjusted_ev_score=adjusted_ev_score,
        status=_row_status(
            adjusted_ev_score=adjusted_ev_score,
            depth_penalty=depth_penalty,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            adjusted_ev_score=adjusted_ev_score,
            depth_penalty=depth_penalty,
            liquidity_decay_penalty=liquidity_decay_penalty,
            stable_liquidity_boost=stable_liquidity_boost,
            config=config,
        ),
    )


def _depth_penalty(
    top_depth_usd: Decimal,
    config: StrategyCandidateLiquidityDecayAdjustedEvV2Config,
) -> Decimal:
    if top_depth_usd >= config.minimum_top_depth_usd:
        return _ZERO
    shortfall_ratio = _clamp_ratio(
        (config.minimum_top_depth_usd - top_depth_usd) / config.minimum_top_depth_usd,
    )
    return _quantize(shortfall_ratio * config.shallow_depth_penalty_rate)


def _stable_liquidity_boost(
    candidate: StrategyCandidateLiquidityDecayAdjustedEvV2Candidate,
    config: StrategyCandidateLiquidityDecayAdjustedEvV2Config,
) -> Decimal:
    if (
        candidate.top_depth_usd >= config.minimum_top_depth_usd
        and candidate.liquidity_stability_score >= config.stable_liquidity_threshold
    ):
        return config.stable_liquidity_boost_rate
    return _ZERO


def _row_status(
    *,
    adjusted_ev_score: Decimal,
    depth_penalty: Decimal,
    config: StrategyCandidateLiquidityDecayAdjustedEvV2Config,
) -> str:
    if adjusted_ev_score < _ZERO:
        return "block"
    if depth_penalty > _ZERO or adjusted_ev_score < config.minimum_adjusted_ev_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    adjusted_ev_score: Decimal,
    depth_penalty: Decimal,
    liquidity_decay_penalty: Decimal,
    stable_liquidity_boost: Decimal,
    config: StrategyCandidateLiquidityDecayAdjustedEvV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if adjusted_ev_score < _ZERO:
        reason_codes.append("negative_adjusted_ev")
    elif adjusted_ev_score < config.minimum_adjusted_ev_score:
        reason_codes.append("low_adjusted_ev_watch")
    else:
        reason_codes.append("positive_adjusted_ev")
    if liquidity_decay_penalty > _ZERO:
        reason_codes.append("liquidity_decay_penalty")
    if depth_penalty > _ZERO:
        reason_codes.append("shallow_depth_penalty")
    if stable_liquidity_boost > _ZERO:
        reason_codes.append("stable_liquidity_boost")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[StrategyCandidateLiquidityDecayAdjustedEvV2Row, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyCandidateLiquidityDecayAdjustedEvV2Row, ...],
) -> tuple[str, ...]:
    reason_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    if not reason_codes:
        reason_codes = ("positive_adjusted_ev",)
    return _normalize_reason_codes(reason_codes)


def _status_count(
    rows: tuple[StrategyCandidateLiquidityDecayAdjustedEvV2Row, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _validate_row_consistency(
    row: StrategyCandidateLiquidityDecayAdjustedEvV2Row,
) -> None:
    edge_before_fee = _quantize(row.model_probability - row.market_probability)
    if row.raw_ev_score != _quantize(edge_before_fee - row.fee_drag):
        raise ValueError("raw_ev_score must match probability edge and fee drag")
    if row.liquidity_decay_penalty != _clamp_nonnegative(
        edge_before_fee * row.depth_decay_ratio,
    ):
        raise ValueError("liquidity_decay_penalty must match edge decay")
    expected_adjusted_ev = _quantize(
        row.raw_ev_score
        - row.liquidity_decay_penalty
        - row.depth_penalty
        + row.stable_liquidity_boost,
    )
    if row.adjusted_ev_score != expected_adjusted_ev:
        raise ValueError("adjusted_ev_score must match row components")


def _validate_report_consistency(
    report: StrategyCandidateLiquidityDecayAdjustedEvV2Report,
) -> None:
    if report.candidate_count != _decimal_count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("blocked_count must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.average_adjusted_ev_score != _average(
        tuple(row.adjusted_ev_score for row in report.rows),
    ):
        raise ValueError("average_adjusted_ev_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _report_values_without_digest(
    report: StrategyCandidateLiquidityDecayAdjustedEvV2Report,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(dict(values))
    _reject_unsafe_public_payload("digest payload", payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _require_payload_digest(payload: Mapping[str, object]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    digest = payload["derived_validation_digest"]
    _require_sha256_digest("derived_validation_digest", digest)
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    expected_digest = _report_digest_from_values(values)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("JSON numeric values must be Decimal-derived strings")
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_candidates(
    candidates: Sequence[StrategyCandidateLiquidityDecayAdjustedEvV2Candidate],
) -> tuple[StrategyCandidateLiquidityDecayAdjustedEvV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be a sequence")
    normalized = tuple(candidates)
    for candidate in normalized:
        if type(candidate) is not StrategyCandidateLiquidityDecayAdjustedEvV2Candidate:
            raise ValueError(
                "candidates must contain "
                "StrategyCandidateLiquidityDecayAdjustedEvV2Candidate values",
            )
    return normalized


def _normalize_rows(
    rows: Sequence[StrategyCandidateLiquidityDecayAdjustedEvV2Row],
) -> tuple[StrategyCandidateLiquidityDecayAdjustedEvV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyCandidateLiquidityDecayAdjustedEvV2Row:
            raise ValueError(
                "rows must contain StrategyCandidateLiquidityDecayAdjustedEvV2Row values",
            )
    return normalized


def _normalize_public_payload(
    public_payload: Sequence[StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem],
) -> tuple[StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)):
        raise ValueError("public_payload must be a sequence")
    normalized = tuple(public_payload)
    for item in normalized:
        if type(item) is not StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem values",
            )
    return normalized


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be a sequence")
    allowed = set(_REASON_CODE_SEQUENCE)
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must be strings")
        if reason_code not in allowed:
            raise ValueError("reason_codes contain unsupported value")
        if reason_code not in seen:
            seen.add(reason_code)
            normalized.append(reason_code)
    normalized.sort(key=_REASON_CODE_SEQUENCE.index)
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    return tuple(normalized)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_public_identifier(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a canonical public identifier")
    if _has_unsafe_public_term(value):
        raise ValueError(f"{name} contains unsafe public text")


def _require_public_text(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be canonical nonblank public text")
    if _has_unsafe_public_term(value):
        raise ValueError(f"{name} contains unsafe public text")
    return value


def _require_status(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in _STATUSES:
        raise ValueError(f"{name} must be one of block, pass, watch")


def _require_sha256_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a SHA-256 hex digest")


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < _ZERO or decimal > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(decimal)


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return _quantize(decimal)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(decimal)


def _require_nonnegative_count_decimal(name: str, value: object) -> Decimal:
    decimal = _require_nonnegative_decimal(name, value)
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{name} must be a whole-number Decimal")
    return _quantize(decimal)


def _require_score_decimal(name: str, value: object) -> Decimal:
    return _quantize(_require_decimal(name, value))


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.rounding = ROUND_HALF_UP
        return value.quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    return _quantize(min(max(value, _ZERO), _ONE))


def _clamp_nonnegative(value: Decimal) -> Decimal:
    return _quantize(max(value, _ZERO))


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, Decimal):
        _require_decimal(path or label, value)
        return
    if type(value) is datetime:
        _as_utc(path or label, value)
        return
    if type(value) is int or type(value) is float:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is str:
        if _has_unsafe_public_term(value):
            raise ValueError(f"{path or label} contains unsafe public text")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_term(key):
                raise ValueError(f"{key} is an unsafe public key")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, tuple | list):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not a safe public payload value")


def _has_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _UNSAFE_PUBLIC_TERMS)


__all__ = (
    "StrategyCandidateLiquidityDecayAdjustedEvV2Candidate",
    "StrategyCandidateLiquidityDecayAdjustedEvV2Config",
    "StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem",
    "StrategyCandidateLiquidityDecayAdjustedEvV2Report",
    "StrategyCandidateLiquidityDecayAdjustedEvV2Row",
    "build_strategy_candidate_liquidity_decay_adjusted_ev_v2_report",
    "strategy_candidate_liquidity_decay_adjusted_ev_v2_payload",
)
