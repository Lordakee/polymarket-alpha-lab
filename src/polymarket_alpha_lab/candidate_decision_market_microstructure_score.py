"""Pure paper/report/readonly market microstructure scoring."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_CANDIDATE_DECISION_MARKET_MICROSTRUCTURE_SCORE_CONFIG_VERSION = (
    "candidate-decision-market-microstructure-score-v0"
)

_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_SPREAD_WEIGHT = Decimal("0.350000")
_DEPTH_WEIGHT = Decimal("0.300000")
_AGE_WEIGHT = Decimal("0.200000")
_IMPACT_WEIGHT = Decimal("0.150000")

_SIDES = ("yes", "no")
_STATUSES = ("pass", "watch", "block")
_STATUS_PRIORITY = {"block": 0, "watch": 1, "pass": 2}

_PASS_REASON_CODE = "market_microstructure_pass"
_EMPTY_REASON_CODE = "market_microstructure_empty"
_CROSSED_BOOK_REASON_CODE = "crossed_book_block"
_SPREAD_BLOCK_REASON_CODE = "spread_block"
_DEPTH_BLOCK_REASON_CODE = "depth_block"
_STALE_BLOCK_REASON_CODE = "book_stale_block"
_IMPACT_BLOCK_REASON_CODE = "price_impact_block"
_SCORE_BLOCK_REASON_CODE = "liquidity_score_block"
_LOCKED_BOOK_REASON_CODE = "locked_book_watch"
_SPREAD_WATCH_REASON_CODE = "spread_watch"
_DEPTH_WATCH_REASON_CODE = "depth_watch"
_STALE_WATCH_REASON_CODE = "book_stale_watch"
_IMPACT_WATCH_REASON_CODE = "price_impact_watch"
_SCORE_WATCH_REASON_CODE = "liquidity_score_watch"

_BLOCK_REASON_CODES = (
    _CROSSED_BOOK_REASON_CODE,
    _SPREAD_BLOCK_REASON_CODE,
    _DEPTH_BLOCK_REASON_CODE,
    _STALE_BLOCK_REASON_CODE,
    _IMPACT_BLOCK_REASON_CODE,
    _SCORE_BLOCK_REASON_CODE,
)
_WATCH_REASON_CODES = (
    _LOCKED_BOOK_REASON_CODE,
    _SPREAD_WATCH_REASON_CODE,
    _DEPTH_WATCH_REASON_CODE,
    _STALE_WATCH_REASON_CODE,
    _IMPACT_WATCH_REASON_CODE,
    _SCORE_WATCH_REASON_CODE,
)
_RESULT_REASON_CODES = (
    _PASS_REASON_CODE,
    _EMPTY_REASON_CODE,
    *_BLOCK_REASON_CODES,
    *_WATCH_REASON_CODES,
)
_REPORT_REASON_PRIORITY = (
    _CROSSED_BOOK_REASON_CODE,
    _SPREAD_BLOCK_REASON_CODE,
    _DEPTH_BLOCK_REASON_CODE,
    _STALE_BLOCK_REASON_CODE,
    _IMPACT_BLOCK_REASON_CODE,
    _SCORE_BLOCK_REASON_CODE,
    _LOCKED_BOOK_REASON_CODE,
    _SPREAD_WATCH_REASON_CODE,
    _DEPTH_WATCH_REASON_CODE,
    _STALE_WATCH_REASON_CODE,
    _IMPACT_WATCH_REASON_CODE,
    _SCORE_WATCH_REASON_CODE,
)

_UNSAFE_KEY_FRAGMENTS = (
    "private" + "_key",
    "sign" + "ing",
)
_UNSAFE_KEY_TOKENS = (
    "acc" + "ount",
    "au" + "th",
    "bal" + "ance",
    "can" + "cel",
    "cred" + "ential",
    "or" + "der",
    "sec" + "ret",
    "sign",
    "to" + "ken",
    "tr" + "ade",
    "wal" + "let",
)
_UNSAFE_TEXT_TOKENS = (
    "cred" + "ential",
    "private" + "_key",
    "sec" + "ret",
    "to" + "ken",
    "wal" + "let",
)
_SAFE_PUBLIC_PAYLOAD_REFERENCE_KEYS = (
    "redactedcandidatereference",
    "redactedmarketreference",
)
_UNSAFE_PUBLIC_PAYLOAD_KEY_COMPACTS = (
    "candidateid",
    "candidatereference",
    "rawcandidateid",
    "rawcandidatereference",
    "marketid",
    "marketslug",
    "marketquestion",
    "rawmarketid",
    "rawmarketslug",
    "rawmarketquestion",
    "question",
    "slug",
    "sourceref",
    "sourcereference",
    "sourceurl",
    "sourceuri",
    "url",
    "uri",
    "dsn",
    "databasename",
    "databaseurl",
    "dburl",
    "tablename",
    "schema",
    "table",
    "paperimpactnotional",
    "papernotional",
    "impactnotional",
    "notional",
    "positionsize",
    "position",
    "quantity",
    "shares",
    "contracts",
    "stake",
    "sizing",
    "b" + "uy",
    "s" + "ell",
    "rec" + "ommend",
    "rec" + "ommendation",
)
_UNSAFE_PUBLIC_PAYLOAD_KEY_FRAGMENTS = (
    "notional",
    "positionsize",
    "sourceurl",
    "sourceuri",
    "sourceref",
    "databaseurl",
    "dburl",
)
_UNSAFE_PUBLIC_PAYLOAD_TEXT_TOKENS = (
    "b" + "uy",
    "s" + "ell",
    "rec" + "ommend",
    "rec" + "ommendation",
    "postgres",
    "postgresql",
    "mysql",
    "sqlite",
    "mongodb",
    "supabase",
)


@dataclass(frozen=True)
class CandidateDecisionMarketMicrostructureScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_MARKET_MICROSTRUCTURE_SCORE_CONFIG_VERSION
    )
    max_pass_spread: Decimal = Decimal("0.020000")
    max_watch_spread: Decimal = Decimal("0.050000")
    min_pass_depth_near_price: Decimal = Decimal("250.000000")
    min_watch_depth_near_price: Decimal = Decimal("50.000000")
    max_pass_book_age_seconds: Decimal = Decimal("30.000000")
    max_watch_book_age_seconds: Decimal = Decimal("120.000000")
    max_pass_price_impact: Decimal = Decimal("0.010000")
    max_watch_price_impact: Decimal = Decimal("0.030000")
    min_pass_liquidity_score: Decimal = Decimal("0.750000")
    min_watch_liquidity_score: Decimal = Decimal("0.400000")
    max_spread_for_score: Decimal = Decimal("0.100000")
    max_book_age_seconds_for_score: Decimal = Decimal("300.000000")
    max_price_impact_for_score: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionMarketMicrostructureScoreConfig:
            raise ValueError(
                "config must be a CandidateDecisionMarketMicrostructureScoreConfig",
            )
        _require_identifier("config_version", self.config_version)
        for field_name in (
            "max_pass_spread",
            "max_watch_spread",
            "max_pass_price_impact",
            "max_watch_price_impact",
            "min_pass_liquidity_score",
            "min_watch_liquidity_score",
            "max_spread_for_score",
            "max_price_impact_for_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_depth_near_price",
            "min_watch_depth_near_price",
            "max_pass_book_age_seconds",
            "max_watch_book_age_seconds",
            "max_book_age_seconds_for_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_spread > self.max_watch_spread:
            raise ValueError("max_pass_spread must not exceed watch threshold")
        if self.min_pass_depth_near_price < self.min_watch_depth_near_price:
            raise ValueError("min_pass_depth_near_price must be at least watch threshold")
        if self.max_pass_book_age_seconds > self.max_watch_book_age_seconds:
            raise ValueError("max_pass_book_age_seconds must not exceed watch threshold")
        if self.max_pass_price_impact > self.max_watch_price_impact:
            raise ValueError("max_pass_price_impact must not exceed watch threshold")
        if self.min_pass_liquidity_score < self.min_watch_liquidity_score:
            raise ValueError("min_pass_liquidity_score must be at least watch threshold")
        if self.min_pass_depth_near_price <= _ZERO:
            raise ValueError("min_pass_depth_near_price must be positive")
        if self.max_spread_for_score <= _ZERO:
            raise ValueError("max_spread_for_score must be positive")
        if self.max_book_age_seconds_for_score <= _ZERO:
            raise ValueError("max_book_age_seconds_for_score must be positive")
        if self.max_price_impact_for_score <= _ZERO:
            raise ValueError("max_price_impact_for_score must be positive")
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class CandidateDecisionMarketMicrostructureCandidate:
    candidate_reference: str
    market_slug: str
    side: str
    best_bid: Decimal
    best_ask: Decimal
    bid_depth_near_price: Decimal
    ask_depth_near_price: Decimal
    book_age_seconds: Decimal
    paper_impact_notional: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionMarketMicrostructureCandidate:
            raise ValueError(
                "candidate must be a CandidateDecisionMarketMicrostructureCandidate",
            )
        _require_identifier("candidate_reference", self.candidate_reference)
        _require_identifier(
            "market_slug",
            self.market_slug,
            reject_unsafe_value=True,
        )
        _require_member("side", self.side, _SIDES)
        for field_name in ("best_bid", "best_ask"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "bid_depth_near_price",
            "ask_depth_near_price",
            "book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "paper_impact_notional",
            _normalize_positive_decimal(
                "paper_impact_notional",
                self.paper_impact_notional,
            ),
        )
        _require_safety_flags("candidate", self)


@dataclass(frozen=True)
class CandidateDecisionMarketMicrostructureResult:
    redacted_candidate_reference: str
    redacted_market_reference: str
    side: str
    best_bid: Decimal
    best_ask: Decimal
    side_bid_price: Decimal
    side_ask_price: Decimal
    spread: Decimal
    midpoint_price: Decimal
    executable_price: Decimal
    bid_depth_near_price: Decimal
    ask_depth_near_price: Decimal
    depth_near_price: Decimal
    book_age_seconds: Decimal
    paper_impact_notional: Decimal
    crossed_book: bool
    locked_book: bool
    price_impact_estimate: Decimal
    liquidity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    max_spread_for_score: Decimal = Decimal("0.100000")
    min_pass_depth_near_price: Decimal = Decimal("250.000000")
    max_book_age_seconds_for_score: Decimal = Decimal("300.000000")
    max_price_impact_for_score: Decimal = Decimal("0.050000")
    result_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionMarketMicrostructureResult:
            raise ValueError("result must be a CandidateDecisionMarketMicrostructureResult")
        _require_redacted_reference(
            "redacted_candidate_reference",
            self.redacted_candidate_reference,
        )
        _require_redacted_market_reference(
            "redacted_market_reference",
            self.redacted_market_reference,
        )
        _require_member("side", self.side, _SIDES)
        for field_name in (
            "best_bid",
            "best_ask",
            "side_bid_price",
            "side_ask_price",
            "midpoint_price",
            "executable_price",
            "liquidity_score",
            "max_spread_for_score",
            "max_price_impact_for_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread",
            "bid_depth_near_price",
            "ask_depth_near_price",
            "depth_near_price",
            "book_age_seconds",
            "paper_impact_notional",
            "price_impact_estimate",
            "min_pass_depth_near_price",
            "max_book_age_seconds_for_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.paper_impact_notional <= _ZERO:
            raise ValueError("paper_impact_notional must be positive")
        if self.min_pass_depth_near_price <= _ZERO:
            raise ValueError("min_pass_depth_near_price must be positive")
        if self.max_spread_for_score <= _ZERO:
            raise ValueError("max_spread_for_score must be positive")
        if self.max_book_age_seconds_for_score <= _ZERO:
            raise ValueError("max_book_age_seconds_for_score must be positive")
        if self.max_price_impact_for_score <= _ZERO:
            raise ValueError("max_price_impact_for_score must be positive")
        _require_bool("crossed_book", self.crossed_book)
        _require_bool("locked_book", self.locked_book)
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("result", self)
        if self.result_sha256 == "":
            object.__setattr__(self, "result_sha256", _result_sha256(self))
        else:
            object.__setattr__(
                self,
                "result_sha256",
                _normalize_sha256("result_sha256", self.result_sha256),
            )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _result_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_result(self)


@dataclass(frozen=True)
class CandidateDecisionMarketMicrostructureScoreReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    min_liquidity_score: Decimal
    max_spread: Decimal
    max_book_age_seconds: Decimal
    max_price_impact_estimate: Decimal
    status: str
    reason_codes: tuple[str, ...]
    results: tuple[CandidateDecisionMarketMicrostructureResult, ...]
    report_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionMarketMicrostructureScoreReport:
            raise ValueError("report must be a CandidateDecisionMarketMicrostructureScoreReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_identifier("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_liquidity_score",
            "max_spread",
            "max_book_age_seconds",
            "max_price_impact_estimate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_liquidity_score > _ONE:
            raise ValueError("min_liquidity_score must not exceed 1")
        if self.max_spread > _ONE:
            raise ValueError("max_spread must not exceed 1")
        if self.max_price_impact_estimate > _ONE:
            raise ValueError("max_price_impact_estimate must not exceed 1")
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "results", _normalize_results(self.results))
        _require_safety_flags("report", self)
        if self.report_sha256 == "":
            object.__setattr__(self, "report_sha256", _report_sha256(self))
        else:
            object.__setattr__(
                self,
                "report_sha256",
                _normalize_sha256("report_sha256", self.report_sha256),
            )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_candidate_decision_market_microstructure_score(
    candidates: Iterable[object],
    *,
    config: CandidateDecisionMarketMicrostructureScoreConfig,
    generated_at: datetime,
) -> CandidateDecisionMarketMicrostructureScoreReport:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        candidate_rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    if type(config) is not CandidateDecisionMarketMicrostructureScoreConfig:
        raise ValueError("config must be a CandidateDecisionMarketMicrostructureScoreConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_safety_flags("config", config)

    seen_references: set[str] = set()
    results: list[CandidateDecisionMarketMicrostructureResult] = []
    for candidate in candidate_rows:
        if type(candidate) is not CandidateDecisionMarketMicrostructureCandidate:
            raise ValueError(
                "candidates must contain CandidateDecisionMarketMicrostructureCandidate",
            )
        _require_safety_flags("candidate", candidate)
        if candidate.candidate_reference in seen_references:
            raise ValueError("duplicate candidate_reference")
        seen_references.add(candidate.candidate_reference)
        results.append(_result_from_candidate(candidate, config=config))

    sorted_results = tuple(sorted(results, key=_result_sort_key))
    return CandidateDecisionMarketMicrostructureScoreReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(sorted_results)),
        pass_count=_status_count(sorted_results, "pass"),
        watch_count=_status_count(sorted_results, "watch"),
        blocked_count=_status_count(sorted_results, "block"),
        min_liquidity_score=_min_liquidity_score(sorted_results),
        max_spread=_max_spread(sorted_results),
        max_book_age_seconds=_max_book_age_seconds(sorted_results),
        max_price_impact_estimate=_max_price_impact_estimate(sorted_results),
        status=_report_status(sorted_results),
        reason_codes=_report_reason_codes(sorted_results),
        results=sorted_results,
    )


def validate_candidate_decision_market_microstructure_score_report(
    report: CandidateDecisionMarketMicrostructureScoreReport,
) -> bool:
    if type(report) is not CandidateDecisionMarketMicrostructureScoreReport:
        raise ValueError("report must be a CandidateDecisionMarketMicrostructureScoreReport")
    _require_safety_flags("report", report)
    _validate_report(report)
    return True


def validate_candidate_decision_market_microstructure_score_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("market microstructure public payload", payload)
    _require_public_payload_flags(payload)
    return True


def candidate_decision_market_microstructure_score_payload(
    report: CandidateDecisionMarketMicrostructureScoreReport,
) -> dict[str, Any]:
    validate_candidate_decision_market_microstructure_score_report(report)
    payload = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "candidate_count": _decimal_payload(report.candidate_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "blocked_count": _decimal_payload(report.blocked_count),
        "min_liquidity_score": _decimal_payload(report.min_liquidity_score),
        "max_spread": _decimal_payload(report.max_spread),
        "max_book_age_seconds": _decimal_payload(report.max_book_age_seconds),
        "max_price_impact_estimate": _decimal_payload(
            report.max_price_impact_estimate,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "results": [_result_payload(result) for result in report.results],
        "report_sha256": report.report_sha256,
        "derived_validation_digest": report.derived_validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    validate_candidate_decision_market_microstructure_score_public_payload(payload)
    return payload


def _result_payload(result: CandidateDecisionMarketMicrostructureResult) -> dict[str, Any]:
    _require_safety_flags("result", result)
    return {
        "redacted_candidate_reference": result.redacted_candidate_reference,
        "redacted_market_reference": result.redacted_market_reference,
        "side": result.side,
        "best_bid": _decimal_payload(result.best_bid),
        "best_ask": _decimal_payload(result.best_ask),
        "side_bid_price": _decimal_payload(result.side_bid_price),
        "side_ask_price": _decimal_payload(result.side_ask_price),
        "spread": _decimal_payload(result.spread),
        "midpoint_price": _decimal_payload(result.midpoint_price),
        "executable_price": _decimal_payload(result.executable_price),
        "bid_depth_near_price": _decimal_payload(result.bid_depth_near_price),
        "ask_depth_near_price": _decimal_payload(result.ask_depth_near_price),
        "depth_near_price": _decimal_payload(result.depth_near_price),
        "book_age_seconds": _decimal_payload(result.book_age_seconds),
        "crossed_book": result.crossed_book,
        "locked_book": result.locked_book,
        "price_impact_estimate": _decimal_payload(result.price_impact_estimate),
        "liquidity_score": _decimal_payload(result.liquidity_score),
        "status": result.status,
        "reason_codes": list(result.reason_codes),
        "max_spread_for_score": _decimal_payload(result.max_spread_for_score),
        "min_pass_depth_near_price": _decimal_payload(
            result.min_pass_depth_near_price,
        ),
        "max_book_age_seconds_for_score": _decimal_payload(
            result.max_book_age_seconds_for_score,
        ),
        "max_price_impact_for_score": _decimal_payload(
            result.max_price_impact_for_score,
        ),
        "result_sha256": result.result_sha256,
        "derived_validation_digest": result.derived_validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _result_from_candidate(
    candidate: CandidateDecisionMarketMicrostructureCandidate,
    *,
    config: CandidateDecisionMarketMicrostructureScoreConfig,
) -> CandidateDecisionMarketMicrostructureResult:
    crossed_book = candidate.best_bid > candidate.best_ask
    locked_book = candidate.best_bid == candidate.best_ask
    side_bid_price = _selected_side_bid_price(
        candidate.side,
        candidate.best_bid,
        candidate.best_ask,
    )
    side_ask_price = _selected_side_ask_price(
        candidate.side,
        candidate.best_bid,
        candidate.best_ask,
    )
    spread = _spread(side_bid_price, side_ask_price)
    midpoint_price = _midpoint_price(side_bid_price, side_ask_price)
    executable_price = side_ask_price
    depth_near_price = _selected_depth_near_price(
        candidate.side,
        candidate.bid_depth_near_price,
        candidate.ask_depth_near_price,
    )
    price_impact_estimate = _price_impact_estimate(
        depth_near_price,
        candidate.paper_impact_notional,
        config.max_price_impact_for_score,
    )
    liquidity_score = _liquidity_score(
        crossed_book=crossed_book,
        spread=spread,
        depth_near_price=depth_near_price,
        book_age_seconds=candidate.book_age_seconds,
        price_impact_estimate=price_impact_estimate,
        max_spread_for_score=config.max_spread_for_score,
        min_pass_depth_near_price=config.min_pass_depth_near_price,
        max_book_age_seconds_for_score=config.max_book_age_seconds_for_score,
        max_price_impact_for_score=config.max_price_impact_for_score,
    )
    reason_codes = _candidate_reason_codes(
        crossed_book=crossed_book,
        locked_book=locked_book,
        spread=spread,
        depth_near_price=depth_near_price,
        book_age_seconds=candidate.book_age_seconds,
        price_impact_estimate=price_impact_estimate,
        liquidity_score=liquidity_score,
        config=config,
    )
    return CandidateDecisionMarketMicrostructureResult(
        redacted_candidate_reference=_redacted_candidate_reference(
            candidate.candidate_reference,
        ),
        redacted_market_reference=_redacted_market_reference(candidate.market_slug),
        side=candidate.side,
        best_bid=candidate.best_bid,
        best_ask=candidate.best_ask,
        side_bid_price=side_bid_price,
        side_ask_price=side_ask_price,
        spread=spread,
        midpoint_price=midpoint_price,
        executable_price=executable_price,
        bid_depth_near_price=candidate.bid_depth_near_price,
        ask_depth_near_price=candidate.ask_depth_near_price,
        depth_near_price=depth_near_price,
        book_age_seconds=candidate.book_age_seconds,
        paper_impact_notional=candidate.paper_impact_notional,
        crossed_book=crossed_book,
        locked_book=locked_book,
        price_impact_estimate=price_impact_estimate,
        liquidity_score=liquidity_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        max_spread_for_score=config.max_spread_for_score,
        min_pass_depth_near_price=config.min_pass_depth_near_price,
        max_book_age_seconds_for_score=config.max_book_age_seconds_for_score,
        max_price_impact_for_score=config.max_price_impact_for_score,
    )


def _candidate_reason_codes(
    *,
    crossed_book: bool,
    locked_book: bool,
    spread: Decimal,
    depth_near_price: Decimal,
    book_age_seconds: Decimal,
    price_impact_estimate: Decimal,
    liquidity_score: Decimal,
    config: CandidateDecisionMarketMicrostructureScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if crossed_book:
        reason_codes.append(_CROSSED_BOOK_REASON_CODE)
    elif locked_book:
        reason_codes.append(_LOCKED_BOOK_REASON_CODE)
    if spread > config.max_watch_spread:
        reason_codes.append(_SPREAD_BLOCK_REASON_CODE)
    elif spread > config.max_pass_spread:
        reason_codes.append(_SPREAD_WATCH_REASON_CODE)
    if depth_near_price < config.min_watch_depth_near_price:
        reason_codes.append(_DEPTH_BLOCK_REASON_CODE)
    elif depth_near_price < config.min_pass_depth_near_price:
        reason_codes.append(_DEPTH_WATCH_REASON_CODE)
    if book_age_seconds > config.max_watch_book_age_seconds:
        reason_codes.append(_STALE_BLOCK_REASON_CODE)
    elif book_age_seconds > config.max_pass_book_age_seconds:
        reason_codes.append(_STALE_WATCH_REASON_CODE)
    if price_impact_estimate > config.max_watch_price_impact:
        reason_codes.append(_IMPACT_BLOCK_REASON_CODE)
    elif price_impact_estimate > config.max_pass_price_impact:
        reason_codes.append(_IMPACT_WATCH_REASON_CODE)
    has_block_reason = any(
        reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes
    )
    if not has_block_reason:
        if liquidity_score < config.min_watch_liquidity_score:
            reason_codes.append(_SCORE_BLOCK_REASON_CODE)
        elif liquidity_score < config.min_pass_liquidity_score:
            reason_codes.append(_SCORE_WATCH_REASON_CODE)
    if not reason_codes:
        return (_PASS_REASON_CODE,)
    return tuple(reason_codes)


def _spread(best_bid: Decimal, best_ask: Decimal) -> Decimal:
    if best_ask <= best_bid:
        return _zero()
    return _q(best_ask - best_bid)


def _selected_side_bid_price(side: str, best_bid: Decimal, best_ask: Decimal) -> Decimal:
    side_bid_price = best_bid if side == "yes" else _ONE - best_ask
    return _normalize_probability("side_bid_price", side_bid_price)


def _selected_side_ask_price(side: str, best_bid: Decimal, best_ask: Decimal) -> Decimal:
    side_ask_price = best_ask if side == "yes" else _ONE - best_bid
    return _normalize_probability("side_ask_price", side_ask_price)


def _midpoint_price(side_bid_price: Decimal, side_ask_price: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        midpoint = (side_bid_price + side_ask_price) / _TWO
    return _normalize_probability("midpoint_price", midpoint)


def _selected_depth_near_price(
    side: str,
    bid_depth_near_price: Decimal,
    ask_depth_near_price: Decimal,
) -> Decimal:
    return ask_depth_near_price if side == "yes" else bid_depth_near_price


def _price_impact_estimate(
    depth_near_price: Decimal,
    paper_impact_notional: Decimal,
    max_price_impact_for_score: Decimal,
) -> Decimal:
    if depth_near_price >= paper_impact_notional:
        return _zero()
    with localcontext(_DECIMAL_CONTEXT):
        shortage_share = (
            paper_impact_notional - depth_near_price
        ) / paper_impact_notional
        estimate = shortage_share * max_price_impact_for_score
    return _bounded_probability(estimate)


def _liquidity_score(
    *,
    crossed_book: bool,
    spread: Decimal,
    depth_near_price: Decimal,
    book_age_seconds: Decimal,
    price_impact_estimate: Decimal,
    max_spread_for_score: Decimal,
    min_pass_depth_near_price: Decimal,
    max_book_age_seconds_for_score: Decimal,
    max_price_impact_for_score: Decimal,
) -> Decimal:
    if crossed_book:
        return _zero()
    spread_score = _ONE - _bounded_ratio(spread, max_spread_for_score)
    depth_score = _bounded_ratio(depth_near_price, min_pass_depth_near_price)
    age_score = _ONE - _bounded_ratio(
        book_age_seconds,
        max_book_age_seconds_for_score,
    )
    impact_score = _ONE - _bounded_ratio(
        price_impact_estimate,
        max_price_impact_for_score,
    )
    with localcontext(_DECIMAL_CONTEXT):
        raw_score = (
            (spread_score * _SPREAD_WEIGHT)
            + (depth_score * _DEPTH_WEIGHT)
            + (age_score * _AGE_WEIGHT)
            + (impact_score * _IMPACT_WEIGHT)
        )
    return _bounded_probability(raw_score)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        ratio = numerator / denominator
    return _bounded_probability(ratio)


def _validate_result(result: CandidateDecisionMarketMicrostructureResult) -> None:
    expected_side_bid_price = _selected_side_bid_price(
        result.side,
        result.best_bid,
        result.best_ask,
    )
    expected_side_ask_price = _selected_side_ask_price(
        result.side,
        result.best_bid,
        result.best_ask,
    )
    expected_spread = _spread(expected_side_bid_price, expected_side_ask_price)
    expected_midpoint_price = _midpoint_price(
        expected_side_bid_price,
        expected_side_ask_price,
    )
    expected_executable_price = expected_side_ask_price
    expected_depth_near_price = _selected_depth_near_price(
        result.side,
        result.bid_depth_near_price,
        result.ask_depth_near_price,
    )
    expected_crossed_book = result.best_bid > result.best_ask
    expected_locked_book = result.best_bid == result.best_ask
    expected_price_impact_estimate = _price_impact_estimate(
        expected_depth_near_price,
        result.paper_impact_notional,
        result.max_price_impact_for_score,
    )
    expected_liquidity_score = _liquidity_score(
        crossed_book=expected_crossed_book,
        spread=expected_spread,
        depth_near_price=expected_depth_near_price,
        book_age_seconds=result.book_age_seconds,
        price_impact_estimate=expected_price_impact_estimate,
        max_spread_for_score=result.max_spread_for_score,
        min_pass_depth_near_price=result.min_pass_depth_near_price,
        max_book_age_seconds_for_score=result.max_book_age_seconds_for_score,
        max_price_impact_for_score=result.max_price_impact_for_score,
    )
    if result.side_bid_price != expected_side_bid_price:
        raise ValueError("side_bid_price must match side and book")
    if result.side_ask_price != expected_side_ask_price:
        raise ValueError("side_ask_price must match side and book")
    if result.spread != expected_spread:
        raise ValueError("spread must match side bid and ask")
    if result.midpoint_price != expected_midpoint_price:
        raise ValueError("midpoint_price must match side and book")
    if result.executable_price != expected_executable_price:
        raise ValueError("executable_price must match side and book")
    if result.depth_near_price != expected_depth_near_price:
        raise ValueError("depth_near_price must match side depth")
    if result.crossed_book is not expected_crossed_book:
        raise ValueError("crossed_book must match best bid and ask")
    if result.locked_book is not expected_locked_book:
        raise ValueError("locked_book must match best bid and ask")
    if result.price_impact_estimate != expected_price_impact_estimate:
        raise ValueError(
            "price_impact_estimate must match depth and paper impact notional",
        )
    if result.liquidity_score != expected_liquidity_score:
        raise ValueError("liquidity_score must match microstructure fields")
    if result.status != _status_from_reason_codes(result.reason_codes):
        raise ValueError("status must match reason_codes")
    if result.result_sha256 != _result_sha256(result):
        raise ValueError("result_sha256 must match result fields")
    if result.derived_validation_digest != _result_derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")


def _validate_report(report: CandidateDecisionMarketMicrostructureScoreReport) -> None:
    results = report.results
    if report.candidate_count != _count_decimal(len(results)):
        raise ValueError("candidate_count must match results")
    if report.pass_count != _status_count(results, "pass"):
        raise ValueError("pass_count must match results")
    if report.watch_count != _status_count(results, "watch"):
        raise ValueError("watch_count must match results")
    if report.blocked_count != _status_count(results, "block"):
        raise ValueError("blocked_count must match results")
    if report.min_liquidity_score != _min_liquidity_score(results):
        raise ValueError("min_liquidity_score must match results")
    if report.max_spread != _max_spread(results):
        raise ValueError("max_spread must match results")
    if report.max_book_age_seconds != _max_book_age_seconds(results):
        raise ValueError("max_book_age_seconds must match results")
    if report.max_price_impact_estimate != _max_price_impact_estimate(results):
        raise ValueError("max_price_impact_estimate must match results")
    if report.status != _report_status(results):
        raise ValueError("status must match results")
    if report.reason_codes != _report_reason_codes(results):
        raise ValueError("reason_codes must match results")
    if report.report_sha256 != _report_sha256(report):
        raise ValueError("report_sha256 must match report fields")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _normalize_results(
    results: object,
) -> tuple[CandidateDecisionMarketMicrostructureResult, ...]:
    if type(results) is not tuple:
        raise ValueError("results must be a tuple")
    normalized = tuple(results)
    for result in normalized:
        if type(result) is not CandidateDecisionMarketMicrostructureResult:
            raise ValueError("results must contain CandidateDecisionMarketMicrostructureResult")
        _require_safety_flags("result", result)
    if normalized != tuple(sorted(normalized, key=_result_sort_key)):
        raise ValueError("results must be deterministically sorted")
    return normalized


def _result_sort_key(
    result: CandidateDecisionMarketMicrostructureResult,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        _STATUS_PRIORITY[result.status],
        result.liquidity_score,
        -result.spread,
        result.redacted_market_reference,
        result.redacted_candidate_reference,
    )


def _status_count(
    results: tuple[CandidateDecisionMarketMicrostructureResult, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for result in results if result.status == status))


def _min_liquidity_score(
    results: tuple[CandidateDecisionMarketMicrostructureResult, ...],
) -> Decimal:
    if not results:
        return _zero()
    return min(result.liquidity_score for result in results)


def _max_spread(
    results: tuple[CandidateDecisionMarketMicrostructureResult, ...],
) -> Decimal:
    if not results:
        return _zero()
    return max(result.spread for result in results)


def _max_book_age_seconds(
    results: tuple[CandidateDecisionMarketMicrostructureResult, ...],
) -> Decimal:
    if not results:
        return _zero()
    return max(result.book_age_seconds for result in results)


def _max_price_impact_estimate(
    results: tuple[CandidateDecisionMarketMicrostructureResult, ...],
) -> Decimal:
    if not results:
        return _zero()
    return max(result.price_impact_estimate for result in results)


def _report_status(
    results: tuple[CandidateDecisionMarketMicrostructureResult, ...],
) -> str:
    if any(result.status == "block" for result in results):
        return "block"
    if any(result.status == "watch" for result in results) or not results:
        return "watch"
    return "pass"


def _report_reason_codes(
    results: tuple[CandidateDecisionMarketMicrostructureResult, ...],
) -> tuple[str, ...]:
    if not results:
        return (_EMPTY_REASON_CODE,)
    observed = {reason_code for result in results for reason_code in result.reason_codes}
    adverse_codes = tuple(
        reason_code for reason_code in _REPORT_REASON_PRIORITY if reason_code in observed
    )
    if adverse_codes:
        return adverse_codes
    return (_PASS_REASON_CODE,)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (_PASS_REASON_CODE,):
        return "pass"
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in _WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    raise ValueError("reason_codes must imply a supported status")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return _q(decimal_value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    normalized = _q(decimal_value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _q(decimal_value)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.quantize(_QUANTUM):
        raise ValueError(f"{field_name} must use six decimal places")
    if normalized != normalized.quantize(Decimal("1.000000")):
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _q(_require_decimal(field_name, value))


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be an exact Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_reason_codes(
    values: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not values:
        raise ValueError("reason_codes must be nonempty")
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    for value in values:
        _require_member("reason_code", value, _RESULT_REASON_CODES)
    return values


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANTUM)


def _bounded_probability(value: Decimal) -> Decimal:
    if value <= _ZERO:
        return _zero()
    if value >= _ONE:
        return _one()
    return _q(value)


def _q(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _zero() -> Decimal:
    return _ZERO.quantize(_QUANTUM)


def _one() -> Decimal:
    return _ONE.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_safety_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")
    _reject_unsafe_public_keys(label, value)


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in public payload")
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("public payload results must be a list")
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("public payload results must contain dict rows")
        for field_name in ("paper_only", "report_only", "readonly"):
            if result.get(field_name) is not True:
                raise ValueError(f"{field_name} must be True in public payload result")


def _reject_unsafe_public_keys(label: str, payload: object) -> None:
    for key in _payload_keys(payload):
        if _is_unsafe_public_key(key):
            raise ValueError(f"unsafe live surface field in {label}: {key}")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    _reject_public_payload_numeric_values(label, payload)
    for key, value in _payload_items(payload):
        if _is_unsafe_public_key(key):
            raise ValueError(f"unsafe live surface field in {label}: {key}")
        if _is_unsafe_public_payload_key(key):
            raise ValueError(f"unsafe public payload field in {label}: {key}")
        if type(value) is str:
            if _is_unsafe_public_text(value):
                raise ValueError(f"unsafe live surface value in {label}: {key}")
            if _is_unsafe_public_payload_text(value):
                raise ValueError(f"unsafe public payload value in {label}: {key}")


def _reject_public_payload_numeric_values(label: str, value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError(f"numeric public payload values must be strings in {label}")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_payload_numeric_values(label, item)
    if isinstance(value, list):
        for item in value:
            _reject_public_payload_numeric_values(label, item)


def _payload_keys(value: object) -> tuple[str, ...]:
    return tuple(key for key, _ in _payload_items(value))


def _payload_items(value: object) -> tuple[tuple[str, object], ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_items(asdict(value))
    if isinstance(value, dict):
        items: list[tuple[str, object]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            items.append((key, item))
            items.extend(_payload_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_payload_items(item))
        return tuple(items)
    return ()


def _is_unsafe_public_key(key: str) -> bool:
    normalized_key = key.lower()
    if any(fragment in normalized_key for fragment in _UNSAFE_KEY_FRAGMENTS):
        return True
    compact_key = _compact_surface_text(normalized_key)
    compact_fragments = tuple(
        "".join(character for character in fragment if character != "_")
        for fragment in _UNSAFE_KEY_FRAGMENTS
    )
    if any(fragment in compact_key for fragment in compact_fragments):
        return True
    tokens = _surface_tokens(normalized_key)
    return any(
        token in tokens or token in compact_key for token in _UNSAFE_KEY_TOKENS
    )


def _is_unsafe_public_payload_key(key: str) -> bool:
    compact_key = _compact_surface_text(key.lower())
    if compact_key in _SAFE_PUBLIC_PAYLOAD_REFERENCE_KEYS:
        return False
    if compact_key in _UNSAFE_PUBLIC_PAYLOAD_KEY_COMPACTS:
        return True
    if any(fragment in compact_key for fragment in _UNSAFE_PUBLIC_PAYLOAD_KEY_FRAGMENTS):
        return True
    if compact_key.startswith(("rawcandidate", "rawmarket")):
        return True
    if compact_key.endswith(("candidateid", "marketid", "marketslug", "marketquestion")):
        return True
    return False


def _is_unsafe_public_text(value: str) -> bool:
    tokens = _surface_tokens(value.lower())
    return any(token in tokens for token in _UNSAFE_TEXT_TOKENS)


def _is_unsafe_public_payload_text(value: str) -> bool:
    normalized_value = value.lower()
    if "://" in normalized_value or normalized_value.startswith("www."):
        return True
    tokens = _surface_tokens(normalized_value)
    compact_value = _compact_surface_text(normalized_value)
    return any(
        token in tokens or token in compact_value
        for token in _UNSAFE_PUBLIC_PAYLOAD_TEXT_TOKENS
    )


def _compact_surface_text(value: str) -> str:
    return "".join(
        character
        for character in value
        if ("a" <= character <= "z") or ("0" <= character <= "9")
    )


def _surface_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in value:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_identifier(
    field_name: str,
    value: object,
    *,
    reject_unsafe_value: bool = False,
) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if reject_unsafe_value and _is_unsafe_public_text(value):
        raise ValueError(f"unsafe live surface value in {field_name}")


def _require_redacted_reference(field_name: str, value: object) -> None:
    _require_identifier(field_name, value)
    if not value.startswith("candidate_ref_"):
        raise ValueError(f"{field_name} must be redacted")


def _require_redacted_market_reference(field_name: str, value: object) -> None:
    _require_identifier(field_name, value)
    if not value.startswith("market_ref_"):
        raise ValueError(f"{field_name} must be redacted")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest") from exc
    return value


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _redacted_candidate_reference(candidate_reference: str) -> str:
    digest = sha256(candidate_reference.encode("utf-8")).hexdigest()[:16]
    return f"candidate_ref_{digest}"


def _redacted_market_reference(market_reference: str) -> str:
    digest = sha256(market_reference.encode("utf-8")).hexdigest()[:16]
    return f"market_ref_{digest}"


def _result_sha256(result: CandidateDecisionMarketMicrostructureResult) -> str:
    return _sha256(
        "result",
        (
            f"redacted_candidate_reference={result.redacted_candidate_reference}",
            f"redacted_market_reference={result.redacted_market_reference}",
            f"side={result.side}",
            f"best_bid={result.best_bid}",
            f"best_ask={result.best_ask}",
            f"side_bid_price={result.side_bid_price}",
            f"side_ask_price={result.side_ask_price}",
            f"spread={result.spread}",
            f"midpoint_price={result.midpoint_price}",
            f"executable_price={result.executable_price}",
            f"bid_depth_near_price={result.bid_depth_near_price}",
            f"ask_depth_near_price={result.ask_depth_near_price}",
            f"depth_near_price={result.depth_near_price}",
            f"book_age_seconds={result.book_age_seconds}",
            f"paper_impact_notional={result.paper_impact_notional}",
            f"crossed_book={result.crossed_book}",
            f"locked_book={result.locked_book}",
            f"price_impact_estimate={result.price_impact_estimate}",
            f"liquidity_score={result.liquidity_score}",
            f"status={result.status}",
            f"reason_codes={_digest_tuple(result.reason_codes)}",
            f"max_spread_for_score={result.max_spread_for_score}",
            f"min_pass_depth_near_price={result.min_pass_depth_near_price}",
            f"max_book_age_seconds_for_score={result.max_book_age_seconds_for_score}",
            f"max_price_impact_for_score={result.max_price_impact_for_score}",
            f"paper_only={result.paper_only}",
            f"report_only={result.report_only}",
            f"readonly={result.readonly}",
        ),
    )


def _result_derived_validation_digest(
    result: CandidateDecisionMarketMicrostructureResult,
) -> str:
    return _sha256(
        "result_derived",
        (
            f"side_bid_price={result.side_bid_price}",
            f"side_ask_price={result.side_ask_price}",
            f"spread={result.spread}",
            f"midpoint_price={result.midpoint_price}",
            f"executable_price={result.executable_price}",
            f"depth_near_price={result.depth_near_price}",
            f"crossed_book={result.crossed_book}",
            f"locked_book={result.locked_book}",
            f"price_impact_estimate={result.price_impact_estimate}",
            f"liquidity_score={result.liquidity_score}",
            f"status={result.status}",
            f"reason_codes={_digest_tuple(result.reason_codes)}",
            f"result_sha256={result.result_sha256}",
            f"paper_only={result.paper_only}",
            f"report_only={result.report_only}",
            f"readonly={result.readonly}",
        ),
    )


def _report_sha256(report: CandidateDecisionMarketMicrostructureScoreReport) -> str:
    return _sha256(
        "report",
        (
            f"generated_at={report.generated_at.isoformat()}",
            f"config_version={report.config_version}",
            f"candidate_count={report.candidate_count}",
            f"pass_count={report.pass_count}",
            f"watch_count={report.watch_count}",
            f"blocked_count={report.blocked_count}",
            f"min_liquidity_score={report.min_liquidity_score}",
            f"max_spread={report.max_spread}",
            f"max_book_age_seconds={report.max_book_age_seconds}",
            f"max_price_impact_estimate={report.max_price_impact_estimate}",
            f"status={report.status}",
            f"reason_codes={_digest_tuple(report.reason_codes)}",
            f"results={_digest_tuple(tuple(result.result_sha256 for result in report.results))}",
            f"paper_only={report.paper_only}",
            f"report_only={report.report_only}",
            f"readonly={report.readonly}",
        ),
    )


def _report_derived_validation_digest(
    report: CandidateDecisionMarketMicrostructureScoreReport,
) -> str:
    return _sha256(
        "report_derived",
        (
            f"candidate_count={report.candidate_count}",
            f"pass_count={report.pass_count}",
            f"watch_count={report.watch_count}",
            f"blocked_count={report.blocked_count}",
            f"min_liquidity_score={report.min_liquidity_score}",
            f"max_spread={report.max_spread}",
            f"max_book_age_seconds={report.max_book_age_seconds}",
            f"max_price_impact_estimate={report.max_price_impact_estimate}",
            f"status={report.status}",
            f"reason_codes={_digest_tuple(report.reason_codes)}",
            "result_derived_validation_digest="
            f"{_digest_tuple(tuple(result.derived_validation_digest for result in report.results))}",
            f"report_sha256={report.report_sha256}",
            f"paper_only={report.paper_only}",
            f"report_only={report.report_only}",
            f"readonly={report.readonly}",
        ),
    )


def _sha256(label: str, values: tuple[str, ...]) -> str:
    return sha256((f"{label}|" + "|".join(values)).encode("utf-8")).hexdigest()


def _digest_tuple(values: tuple[str, ...]) -> str:
    return ",".join(values)


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_MARKET_MICROSTRUCTURE_SCORE_CONFIG_VERSION",
    "CandidateDecisionMarketMicrostructureCandidate",
    "CandidateDecisionMarketMicrostructureResult",
    "CandidateDecisionMarketMicrostructureScoreConfig",
    "CandidateDecisionMarketMicrostructureScoreReport",
    "build_candidate_decision_market_microstructure_score",
    "candidate_decision_market_microstructure_score_payload",
    "validate_candidate_decision_market_microstructure_score_public_payload",
    "validate_candidate_decision_market_microstructure_score_report",
)
