"""Phase 1 paper-only expected-value banding for prediction market candidates."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from typing import Any, Iterable

from .team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


CONFIG_VERSION = "strategy-prediction-market-expected-value-band-v2"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT_PRECISION = 28

EV_BANDS = frozenset(("high", "medium", "low", "negative"))
STATUSES = frozenset(("pass", "watch", "block"))
REPORT_STATUSES = frozenset(("pass", "watch", "block", "empty"))
EV_BAND_PRIORITY = {"high": 0, "medium": 1, "low": 2, "negative": 3}


@dataclass(frozen=True)
class StrategyPredictionMarketExpectedValueBandV2Config:
    config_version: str = CONFIG_VERSION
    high_net_expected_value_usdc: Decimal = Decimal("10.000000")
    medium_net_expected_value_usdc: Decimal = Decimal("5.000000")
    low_net_expected_value_usdc: Decimal = Decimal("0.000001")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyPredictionMarketExpectedValueBandV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            StrategyPredictionMarketExpectedValueBandV2Config,
        )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "high_net_expected_value_usdc",
            "medium_net_expected_value_usdc",
            "low_net_expected_value_usdc",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.low_net_expected_value_usdc > self.medium_net_expected_value_usdc:
            raise ValueError(
                "low_net_expected_value_usdc must be at most medium_net_expected_value_usdc",
            )
        if self.medium_net_expected_value_usdc > self.high_net_expected_value_usdc:
            raise ValueError(
                "medium_net_expected_value_usdc must be at most high_net_expected_value_usdc",
            )
        require_paper_only_flags(
            "StrategyPredictionMarketExpectedValueBandV2Config",
            self,
        )
        reject_unsafe_surface_fields("expected value band config", self)


@dataclass(frozen=True)
class StrategyPredictionMarketExpectedValueBandV2Candidate:
    candidate_id: str
    market_id: str
    event_slug: str
    category: str
    model_probability: Decimal
    market_probability: Decimal
    limit_price: Decimal
    notional_usdc: Decimal
    total_cost_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyPredictionMarketExpectedValueBandV2Candidate "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "candidate",
            self,
            StrategyPredictionMarketExpectedValueBandV2Candidate,
        )
        for field_name in ("candidate_id", "market_id", "event_slug", "category"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        for field_name in ("model_probability", "market_probability", "limit_price"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "notional_usdc",
            _normalize_positive_decimal("notional_usdc", self.notional_usdc),
        )
        object.__setattr__(
            self,
            "total_cost_rate",
            _normalize_ratio("total_cost_rate", self.total_cost_rate),
        )
        require_paper_only_flags(
            "StrategyPredictionMarketExpectedValueBandV2Candidate",
            self,
        )
        reject_unsafe_surface_fields("expected value band candidate", self)


@dataclass(frozen=True)
class StrategyPredictionMarketExpectedValueBandV2Row:
    candidate_id: str
    market_id: str
    event_slug: str
    category: str
    model_probability: Decimal
    market_probability: Decimal
    limit_price: Decimal
    notional_usdc: Decimal
    total_cost_rate: Decimal
    gross_edge: Decimal
    expected_value_usdc: Decimal
    cost_usdc: Decimal
    net_expected_value_usdc: Decimal
    ev_band: str
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyPredictionMarketExpectedValueBandV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, StrategyPredictionMarketExpectedValueBandV2Row)
        for field_name in ("candidate_id", "market_id", "event_slug", "category"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        for field_name in ("model_probability", "market_probability", "limit_price"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "notional_usdc",
            _normalize_positive_decimal("notional_usdc", self.notional_usdc),
        )
        object.__setattr__(
            self,
            "total_cost_rate",
            _normalize_ratio("total_cost_rate", self.total_cost_rate),
        )
        for field_name in (
            "gross_edge",
            "expected_value_usdc",
            "net_expected_value_usdc",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_usdc",
            _normalize_nonnegative_decimal("cost_usdc", self.cost_usdc),
        )
        _require_member("ev_band", self.ev_band, EV_BANDS)
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_row(self)
        require_paper_only_flags("StrategyPredictionMarketExpectedValueBandV2Row", self)
        reject_unsafe_surface_fields("expected value band row", self)


@dataclass(frozen=True)
class StrategyPredictionMarketExpectedValueBandV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyPredictionMarketExpectedValueBandV2ReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason code count",
            self,
            StrategyPredictionMarketExpectedValueBandV2ReasonCodeCount,
        )
        _require_canonical_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        require_paper_only_flags(
            "StrategyPredictionMarketExpectedValueBandV2ReasonCodeCount",
            self,
        )
        reject_unsafe_surface_fields("expected value band reason code count", self)


@dataclass(frozen=True)
class StrategyPredictionMarketExpectedValueBandV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    high_count: Decimal
    medium_count: Decimal
    low_count: Decimal
    negative_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_net_expected_value_usdc: Decimal
    max_net_expected_value_usdc: Decimal
    report_status: str
    reason_code_counts: tuple[StrategyPredictionMarketExpectedValueBandV2ReasonCodeCount, ...]
    rows: tuple[StrategyPredictionMarketExpectedValueBandV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyPredictionMarketExpectedValueBandV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            StrategyPredictionMarketExpectedValueBandV2Report,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "candidate_count",
            "high_count",
            "medium_count",
            "low_count",
            "negative_count",
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
            "total_net_expected_value_usdc",
            "max_net_expected_value_usdc",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        require_paper_only_flags(
            "StrategyPredictionMarketExpectedValueBandV2Report",
            self,
        )
        reject_unsafe_surface_fields("expected value band report", self)


def build_strategy_prediction_market_expected_value_band_v2_report(
    candidates: Iterable[StrategyPredictionMarketExpectedValueBandV2Candidate],
    *,
    config: StrategyPredictionMarketExpectedValueBandV2Config | None = None,
    generated_at: datetime,
) -> StrategyPredictionMarketExpectedValueBandV2Report:
    if config is None:
        config = StrategyPredictionMarketExpectedValueBandV2Config()
    if type(config) is not StrategyPredictionMarketExpectedValueBandV2Config:
        raise ValueError(
            "config must be a StrategyPredictionMarketExpectedValueBandV2Config",
        )
    require_paper_only_flags("config", config)
    reject_unsafe_surface_fields("expected value band config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (_row_from_candidate(candidate, config=config) for candidate in normalized_candidates),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    return _report_from_parts(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
        reason_code_counts=reason_code_counts,
    )


def strategy_prediction_market_expected_value_band_v2_payload(
    report: StrategyPredictionMarketExpectedValueBandV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyPredictionMarketExpectedValueBandV2Report:
        raise ValueError(
            "report must be a StrategyPredictionMarketExpectedValueBandV2Report",
        )
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("expected value band report", report)
    _validate_report(report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_candidate(
    candidate: StrategyPredictionMarketExpectedValueBandV2Candidate,
    *,
    config: StrategyPredictionMarketExpectedValueBandV2Config,
) -> StrategyPredictionMarketExpectedValueBandV2Row:
    gross_edge = _subtract_decimal(candidate.model_probability, candidate.limit_price)
    expected_value_usdc = _multiply_decimal(gross_edge, candidate.notional_usdc)
    cost_usdc = _multiply_decimal(candidate.notional_usdc, candidate.total_cost_rate)
    net_expected_value_usdc = _subtract_decimal(expected_value_usdc, cost_usdc)
    ev_band = _ev_band(net_expected_value_usdc, config=config)
    status = _status_for_band(ev_band)
    reason_codes = _normalize_reason_codes((f"ev_band_{ev_band}",), require_nonempty=True)
    derived_validation_digest = _row_digest_from_parts(
        candidate_id=candidate.candidate_id,
        market_id=candidate.market_id,
        event_slug=candidate.event_slug,
        category=candidate.category,
        model_probability=candidate.model_probability,
        market_probability=candidate.market_probability,
        limit_price=candidate.limit_price,
        notional_usdc=candidate.notional_usdc,
        total_cost_rate=candidate.total_cost_rate,
        gross_edge=gross_edge,
        expected_value_usdc=expected_value_usdc,
        cost_usdc=cost_usdc,
        net_expected_value_usdc=net_expected_value_usdc,
        ev_band=ev_band,
        status=status,
        reason_codes=reason_codes,
    )
    return StrategyPredictionMarketExpectedValueBandV2Row(
        candidate_id=candidate.candidate_id,
        market_id=candidate.market_id,
        event_slug=candidate.event_slug,
        category=candidate.category,
        model_probability=candidate.model_probability,
        market_probability=candidate.market_probability,
        limit_price=candidate.limit_price,
        notional_usdc=candidate.notional_usdc,
        total_cost_rate=candidate.total_cost_rate,
        gross_edge=gross_edge,
        expected_value_usdc=expected_value_usdc,
        cost_usdc=cost_usdc,
        net_expected_value_usdc=net_expected_value_usdc,
        ev_band=ev_band,
        status=status,
        reason_codes=reason_codes,
        derived_validation_digest=derived_validation_digest,
    )


def _report_from_parts(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[StrategyPredictionMarketExpectedValueBandV2Row, ...],
    reason_code_counts: tuple[StrategyPredictionMarketExpectedValueBandV2ReasonCodeCount, ...],
) -> StrategyPredictionMarketExpectedValueBandV2Report:
    candidate_count = _count(len(rows))
    high_count = _band_count(rows, "high")
    medium_count = _band_count(rows, "medium")
    low_count = _band_count(rows, "low")
    negative_count = _band_count(rows, "negative")
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    block_count = _status_count(rows, "block")
    total_net_expected_value_usdc = _sum_decimal(
        tuple(row.net_expected_value_usdc for row in rows),
    )
    max_net_expected_value_usdc = _max_decimal(
        tuple(row.net_expected_value_usdc for row in rows),
    )
    report_status = _report_status(rows)
    derived_validation_digest = _report_digest_from_parts(
        generated_at=generated_at,
        config_version=config_version,
        candidate_count=candidate_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        negative_count=negative_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        total_net_expected_value_usdc=total_net_expected_value_usdc,
        max_net_expected_value_usdc=max_net_expected_value_usdc,
        report_status=report_status,
        reason_code_counts=reason_code_counts,
        rows=rows,
    )
    return StrategyPredictionMarketExpectedValueBandV2Report(
        generated_at=generated_at,
        config_version=config_version,
        candidate_count=candidate_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        negative_count=negative_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        total_net_expected_value_usdc=total_net_expected_value_usdc,
        max_net_expected_value_usdc=max_net_expected_value_usdc,
        report_status=report_status,
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=derived_validation_digest,
    )


def _ev_band(
    net_expected_value_usdc: Decimal,
    *,
    config: StrategyPredictionMarketExpectedValueBandV2Config,
) -> str:
    if net_expected_value_usdc >= config.high_net_expected_value_usdc:
        return "high"
    if net_expected_value_usdc >= config.medium_net_expected_value_usdc:
        return "medium"
    if net_expected_value_usdc >= config.low_net_expected_value_usdc:
        return "low"
    return "negative"


def _status_for_band(ev_band: str) -> str:
    if ev_band == "high":
        return "pass"
    if ev_band in {"medium", "low"}:
        return "watch"
    return "block"


def _report_status(
    rows: tuple[StrategyPredictionMarketExpectedValueBandV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_sort_key(
    row: StrategyPredictionMarketExpectedValueBandV2Row,
) -> tuple[int, Decimal, Decimal, str, str, str]:
    return (
        EV_BAND_PRIORITY[row.ev_band],
        -row.net_expected_value_usdc,
        -row.gross_edge,
        row.category,
        row.event_slug,
        row.candidate_id,
    )


def _reason_code_counts(
    rows: tuple[StrategyPredictionMarketExpectedValueBandV2Row, ...],
) -> tuple[StrategyPredictionMarketExpectedValueBandV2ReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        StrategyPredictionMarketExpectedValueBandV2ReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _validate_row(row: StrategyPredictionMarketExpectedValueBandV2Row) -> None:
    if row.gross_edge != _subtract_decimal(row.model_probability, row.limit_price):
        raise ValueError("gross_edge must match model_probability minus limit_price")
    if row.expected_value_usdc != _multiply_decimal(row.gross_edge, row.notional_usdc):
        raise ValueError("expected_value_usdc must match gross_edge and notional_usdc")
    if row.cost_usdc != _multiply_decimal(row.notional_usdc, row.total_cost_rate):
        raise ValueError("cost_usdc must match notional_usdc and total_cost_rate")
    if row.net_expected_value_usdc != _subtract_decimal(
        row.expected_value_usdc,
        row.cost_usdc,
    ):
        raise ValueError("net_expected_value_usdc must match expected value after costs")
    if row.status != _status_for_band(row.ev_band):
        raise ValueError("status must match ev_band")
    if row.reason_codes != _normalize_reason_codes(
        (f"ev_band_{row.ev_band}",),
        require_nonempty=True,
    ):
        raise ValueError("reason_codes must match ev_band")
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: StrategyPredictionMarketExpectedValueBandV2Report) -> None:
    for row in report.rows:
        _validate_row(row)
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.high_count != _band_count(report.rows, "high"):
        raise ValueError("high_count must match rows")
    if report.medium_count != _band_count(report.rows, "medium"):
        raise ValueError("medium_count must match rows")
    if report.low_count != _band_count(report.rows, "low"):
        raise ValueError("low_count must match rows")
    if report.negative_count != _band_count(report.rows, "negative"):
        raise ValueError("negative_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.total_net_expected_value_usdc != _sum_decimal(
        tuple(row.net_expected_value_usdc for row in report.rows),
    ):
        raise ValueError("total_net_expected_value_usdc must match rows")
    if report.max_net_expected_value_usdc != _max_decimal(
        tuple(row.net_expected_value_usdc for row in report.rows),
    ):
        raise ValueError("max_net_expected_value_usdc must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must be sorted by expected value band")
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _row_digest(row: StrategyPredictionMarketExpectedValueBandV2Row) -> str:
    return _row_digest_from_parts(
        candidate_id=row.candidate_id,
        market_id=row.market_id,
        event_slug=row.event_slug,
        category=row.category,
        model_probability=row.model_probability,
        market_probability=row.market_probability,
        limit_price=row.limit_price,
        notional_usdc=row.notional_usdc,
        total_cost_rate=row.total_cost_rate,
        gross_edge=row.gross_edge,
        expected_value_usdc=row.expected_value_usdc,
        cost_usdc=row.cost_usdc,
        net_expected_value_usdc=row.net_expected_value_usdc,
        ev_band=row.ev_band,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _row_digest_from_parts(
    *,
    candidate_id: str,
    market_id: str,
    event_slug: str,
    category: str,
    model_probability: Decimal,
    market_probability: Decimal,
    limit_price: Decimal,
    notional_usdc: Decimal,
    total_cost_rate: Decimal,
    gross_edge: Decimal,
    expected_value_usdc: Decimal,
    cost_usdc: Decimal,
    net_expected_value_usdc: Decimal,
    ev_band: str,
    status: str,
    reason_codes: tuple[str, ...],
) -> str:
    return _digest_payload(
        {
            "schema": "row-v2",
            "candidate_id": candidate_id,
            "market_id": market_id,
            "event_slug": event_slug,
            "category": category,
            "model_probability": _digest_decimal(model_probability),
            "market_probability": _digest_decimal(market_probability),
            "limit_price": _digest_decimal(limit_price),
            "notional_usdc": _digest_decimal(notional_usdc),
            "total_cost_rate": _digest_decimal(total_cost_rate),
            "gross_edge": _digest_decimal(gross_edge),
            "expected_value_usdc": _digest_decimal(expected_value_usdc),
            "cost_usdc": _digest_decimal(cost_usdc),
            "net_expected_value_usdc": _digest_decimal(net_expected_value_usdc),
            "ev_band": ev_band,
            "status": status,
            "reason_codes": tuple(reason_codes),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )


def _report_digest(report: StrategyPredictionMarketExpectedValueBandV2Report) -> str:
    return _report_digest_from_parts(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        high_count=report.high_count,
        medium_count=report.medium_count,
        low_count=report.low_count,
        negative_count=report.negative_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        total_net_expected_value_usdc=report.total_net_expected_value_usdc,
        max_net_expected_value_usdc=report.max_net_expected_value_usdc,
        report_status=report.report_status,
        reason_code_counts=report.reason_code_counts,
        rows=report.rows,
    )


def _report_digest_from_parts(
    *,
    generated_at: datetime,
    config_version: str,
    candidate_count: Decimal,
    high_count: Decimal,
    medium_count: Decimal,
    low_count: Decimal,
    negative_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    total_net_expected_value_usdc: Decimal,
    max_net_expected_value_usdc: Decimal,
    report_status: str,
    reason_code_counts: tuple[StrategyPredictionMarketExpectedValueBandV2ReasonCodeCount, ...],
    rows: tuple[StrategyPredictionMarketExpectedValueBandV2Row, ...],
) -> str:
    return _digest_payload(
        {
            "schema": "report-v2",
            "generated_at": _digest_datetime(_as_utc("generated_at", generated_at)),
            "config_version": config_version,
            "candidate_count": _digest_decimal(candidate_count),
            "high_count": _digest_decimal(high_count),
            "medium_count": _digest_decimal(medium_count),
            "low_count": _digest_decimal(low_count),
            "negative_count": _digest_decimal(negative_count),
            "pass_count": _digest_decimal(pass_count),
            "watch_count": _digest_decimal(watch_count),
            "block_count": _digest_decimal(block_count),
            "total_net_expected_value_usdc": _digest_decimal(total_net_expected_value_usdc),
            "max_net_expected_value_usdc": _digest_decimal(max_net_expected_value_usdc),
            "report_status": report_status,
            "reason_code_counts": tuple(
                {
                    "reason_code": item.reason_code,
                    "count": _digest_decimal(item.count),
                }
                for item in reason_code_counts
            ),
            "row_digests": tuple(row.derived_validation_digest for row in rows),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )


def _digest_payload(payload: object) -> str:
    encoded = json.dumps(
        _digest_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _digest_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return _digest_decimal(value)
    if isinstance(value, datetime):
        return _digest_datetime(value)
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("digest payload keys must be strings")
            ready[key] = _digest_ready(item)
        return ready
    if isinstance(value, (tuple, list)):
        return [_digest_ready(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("digest value is not supported")


def _digest_decimal(value: Decimal) -> str:
    return str(_normalize_decimal("digest_decimal", value))


def _digest_datetime(value: datetime) -> str:
    return _as_utc("digest_datetime", value).isoformat()


def _normalize_candidates(
    value: Iterable[StrategyPredictionMarketExpectedValueBandV2Candidate],
) -> tuple[StrategyPredictionMarketExpectedValueBandV2Candidate, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        candidates = tuple(value)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    candidate_ids: set[str] = set()
    for candidate in candidates:
        if type(candidate) is not StrategyPredictionMarketExpectedValueBandV2Candidate:
            raise ValueError("candidates must contain exact candidate rows")
        require_paper_only_flags("candidate", candidate)
        reject_unsafe_surface_fields("expected value band candidate", candidate)
        if candidate.candidate_id in candidate_ids:
            raise ValueError("candidate_id values must be unique")
        candidate_ids.add(candidate.candidate_id)
    return candidates


def _normalize_rows(
    value: Iterable[StrategyPredictionMarketExpectedValueBandV2Row],
) -> tuple[StrategyPredictionMarketExpectedValueBandV2Row, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    candidate_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyPredictionMarketExpectedValueBandV2Row:
            raise ValueError("rows must contain exact row values")
        require_paper_only_flags("row", row)
        reject_unsafe_surface_fields("expected value band row", row)
        _validate_row(row)
        if row.candidate_id in candidate_ids:
            raise ValueError("candidate_id values must be unique")
        candidate_ids.add(row.candidate_id)
    return rows


def _normalize_reason_code_counts(
    value: Iterable[StrategyPredictionMarketExpectedValueBandV2ReasonCodeCount],
) -> tuple[StrategyPredictionMarketExpectedValueBandV2ReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    reason_codes: set[str] = set()
    for item in counts:
        if type(item) is not StrategyPredictionMarketExpectedValueBandV2ReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason count values")
        require_paper_only_flags("reason code count", item)
        reject_unsafe_surface_fields("expected value band reason code count", item)
        if item.reason_code in reason_codes:
            raise ValueError("reason_code_counts must be unique by reason_code")
        reason_codes.add(item.reason_code)
    expected_order = tuple(
        sorted(counts, key=lambda item: (-item.count, item.reason_code)),
    )
    if counts != expected_order:
        raise ValueError("reason_code_counts must be sorted by count and reason_code")
    return counts


def _normalize_reason_codes(
    value: Iterable[str],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_public_string("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return tuple(sorted(reason_codes))


def _count(value: int) -> Decimal:
    return _normalize_decimal("count", Decimal(value))


def _band_count(
    rows: tuple[StrategyPredictionMarketExpectedValueBandV2Row, ...],
    ev_band: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.ev_band == ev_band))


def _status_count(
    rows: tuple[StrategyPredictionMarketExpectedValueBandV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _normalize_decimal("sum", sum(values, ZERO))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_decimal("max", max(values))


def _multiply_decimal(*values: Decimal) -> Decimal:
    result = ONE
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        for value in values:
            result *= value
    return _normalize_decimal("product", result)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _normalize_decimal("difference", left - right)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    return _normalize_probability(field_name, value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exact type {expected_type.__name__}")


def _require_member(field_name: str, value: str, allowed: frozenset[str]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {tuple(sorted(allowed))}")


def _require_hex_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_canonical_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be canonical public text")


__all__ = (
    "CONFIG_VERSION",
    "StrategyPredictionMarketExpectedValueBandV2Candidate",
    "StrategyPredictionMarketExpectedValueBandV2Config",
    "StrategyPredictionMarketExpectedValueBandV2ReasonCodeCount",
    "StrategyPredictionMarketExpectedValueBandV2Report",
    "StrategyPredictionMarketExpectedValueBandV2Row",
    "build_strategy_prediction_market_expected_value_band_v2_report",
    "strategy_prediction_market_expected_value_band_v2_payload",
)
