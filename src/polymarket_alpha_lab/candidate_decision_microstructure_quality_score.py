"""Pure report-only microstructure quality scoring for research priority."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_CANDIDATE_DECISION_MICROSTRUCTURE_QUALITY_SCORE_CONFIG_VERSION = (
    "candidate-decision-microstructure-quality-score-v0"
)

_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_STATUSES = ("pass", "watch", "block")
_STATUS_PRIORITY = {"block": 0, "watch": 1, "pass": 2}

_PASS_REASON_CODE = "microstructure_quality_pass"
_EMPTY_REASON_CODE = "microstructure_quality_empty"
_SPREAD_BLOCK_REASON_CODE = "spread_quality_block"
_SPREAD_WATCH_REASON_CODE = "spread_quality_watch"
_DEPTH_BLOCK_REASON_CODE = "depth_quality_block"
_DEPTH_WATCH_REASON_CODE = "depth_quality_watch"
_IMBALANCE_BLOCK_REASON_CODE = "imbalance_risk_block"
_IMBALANCE_WATCH_REASON_CODE = "imbalance_risk_watch"
_STALE_BOOK_BLOCK_REASON_CODE = "book_freshness_block"
_STALE_BOOK_WATCH_REASON_CODE = "book_freshness_watch"
_RECENT_ACTIVITY_BLOCK_REASON_CODE = "recent_activity_block"
_RECENT_ACTIVITY_WATCH_REASON_CODE = "recent_activity_watch"
_QUOTE_BLOCK_REASON_CODE = "quote_coverage_block"
_QUOTE_WATCH_REASON_CODE = "quote_coverage_watch"
_OUTLIER_BLOCK_REASON_CODE = "outlier_move_block"
_OUTLIER_WATCH_REASON_CODE = "outlier_move_watch"
_QUALITY_BLOCK_REASON_CODE = "quality_score_block"
_QUALITY_WATCH_REASON_CODE = "quality_score_watch"

_BLOCK_REASON_CODES = (
    _SPREAD_BLOCK_REASON_CODE,
    _DEPTH_BLOCK_REASON_CODE,
    _IMBALANCE_BLOCK_REASON_CODE,
    _STALE_BOOK_BLOCK_REASON_CODE,
    _RECENT_ACTIVITY_BLOCK_REASON_CODE,
    _QUOTE_BLOCK_REASON_CODE,
    _OUTLIER_BLOCK_REASON_CODE,
    _QUALITY_BLOCK_REASON_CODE,
)
_WATCH_REASON_CODES = (
    _SPREAD_WATCH_REASON_CODE,
    _DEPTH_WATCH_REASON_CODE,
    _IMBALANCE_WATCH_REASON_CODE,
    _STALE_BOOK_WATCH_REASON_CODE,
    _RECENT_ACTIVITY_WATCH_REASON_CODE,
    _QUOTE_WATCH_REASON_CODE,
    _OUTLIER_WATCH_REASON_CODE,
    _QUALITY_WATCH_REASON_CODE,
)
_REASON_CODES = (
    _PASS_REASON_CODE,
    _EMPTY_REASON_CODE,
    *_BLOCK_REASON_CODES,
    *_WATCH_REASON_CODES,
)
_REPORT_REASON_PRIORITY = (
    _SPREAD_BLOCK_REASON_CODE,
    _DEPTH_BLOCK_REASON_CODE,
    _IMBALANCE_BLOCK_REASON_CODE,
    _STALE_BOOK_BLOCK_REASON_CODE,
    _RECENT_ACTIVITY_BLOCK_REASON_CODE,
    _QUOTE_BLOCK_REASON_CODE,
    _OUTLIER_BLOCK_REASON_CODE,
    _QUALITY_BLOCK_REASON_CODE,
    _SPREAD_WATCH_REASON_CODE,
    _DEPTH_WATCH_REASON_CODE,
    _IMBALANCE_WATCH_REASON_CODE,
    _STALE_BOOK_WATCH_REASON_CODE,
    _RECENT_ACTIVITY_WATCH_REASON_CODE,
    _QUOTE_WATCH_REASON_CODE,
    _OUTLIER_WATCH_REASON_CODE,
    _QUALITY_WATCH_REASON_CODE,
)

_UNSAFE_TEXT_TOKENS = (
    "au" + "th",
    "b" + "uy",
    "dsn",
    "or" + "der",
    "pos" + "ition",
    "rec" + "ommend",
    "rec" + "ommendation",
    "s" + "ell",
    "sec" + "ret",
    "siz" + "ing",
    "to" + "ken",
    "tr" + "ade",
    "wal" + "let",
)
_UNSAFE_KEY_COMPACTS = (
    "candidateid",
    "candidatereference",
    "marketid",
    "marketslug",
    "marketquestion",
    "question",
    "sourceref",
    "sourcereference",
    "sourceurl",
    "sourceuri",
    "url",
    "uri",
    "dsn",
    "tablename",
    "databasename",
    "databaseurl",
    "dburl",
    "schema",
    "table",
    "last" + "tr" + "ade" + "ageminutes",
    "to" + "ken",
    "sec" + "ret",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "b" + "uy",
    "s" + "ell",
    "rec" + "ommend",
    "rec" + "ommendation",
    "pos" + "ition",
    "positionsize",
    "siz" + "ing",
)
_UNSAFE_KEY_FRAGMENTS = (
    "sourceurl",
    "sourceuri",
    "sourceref",
    "databaseurl",
    "dburl",
    "tablename",
    "last" + "tr" + "ade",
)

__all__ = (
    "DEFAULT_CANDIDATE_DECISION_MICROSTRUCTURE_QUALITY_SCORE_CONFIG_VERSION",
    "CandidateDecisionMicrostructureQualityScoreConfig",
    "CandidateDecisionMicrostructureQualityInput",
    "CandidateDecisionMicrostructureQualityRow",
    "CandidateDecisionMicrostructureQualityReport",
    "build_candidate_decision_microstructure_quality_score",
    "candidate_decision_microstructure_quality_score_payload",
    "validate_candidate_decision_microstructure_quality_public_payload",
)


@dataclass(frozen=True)
class CandidateDecisionMicrostructureQualityScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_MICROSTRUCTURE_QUALITY_SCORE_CONFIG_VERSION
    )
    min_pass_quality_score: Decimal = Decimal("0.750000")
    min_watch_quality_score: Decimal = Decimal("0.500000")
    min_pass_spread_score: Decimal = Decimal("0.700000")
    min_watch_spread_score: Decimal = Decimal("0.400000")
    min_pass_depth_score: Decimal = Decimal("0.700000")
    min_watch_depth_score: Decimal = Decimal("0.400000")
    max_pass_imbalance_score: Decimal = Decimal("0.300000")
    max_watch_imbalance_score: Decimal = Decimal("0.800000")
    max_pass_stale_book_minutes: Decimal = Decimal("2.000000")
    max_watch_stale_book_minutes: Decimal = Decimal("10.000000")
    max_pass_last_trade_age_minutes: Decimal = Decimal("60.000000")
    max_watch_last_trade_age_minutes: Decimal = Decimal("240.000000")
    min_pass_quote_count: Decimal = Decimal("20.000000")
    min_watch_quote_count: Decimal = Decimal("5.000000")
    max_pass_outlier_move_score: Decimal = Decimal("0.200000")
    max_watch_outlier_move_score: Decimal = Decimal("0.700000")
    max_stale_book_minutes_for_score: Decimal = Decimal("10.000000")
    max_last_trade_age_minutes_for_score: Decimal = Decimal("180.000000")
    quote_count_full_score: Decimal = Decimal("40.000000")
    spread_weight: Decimal = Decimal("0.250000")
    depth_weight: Decimal = Decimal("0.250000")
    imbalance_weight: Decimal = Decimal("0.150000")
    stale_book_weight: Decimal = Decimal("0.150000")
    last_activity_weight: Decimal = Decimal("0.100000")
    quote_count_weight: Decimal = Decimal("0.050000")
    outlier_move_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionMicrostructureQualityScoreConfig:
            raise ValueError(
                "config must be a CandidateDecisionMicrostructureQualityScoreConfig",
            )
        _require_str("config_version", self.config_version)
        _reject_unsafe_text("config_version", self.config_version)
        for field_name in (
            "min_pass_quality_score",
            "min_watch_quality_score",
            "min_pass_spread_score",
            "min_watch_spread_score",
            "min_pass_depth_score",
            "min_watch_depth_score",
            "max_pass_imbalance_score",
            "max_watch_imbalance_score",
            "max_pass_outlier_move_score",
            "max_watch_outlier_move_score",
            "spread_weight",
            "depth_weight",
            "imbalance_weight",
            "stale_book_weight",
            "last_activity_weight",
            "quote_count_weight",
            "outlier_move_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_stale_book_minutes",
            "max_watch_stale_book_minutes",
            "max_pass_last_trade_age_minutes",
            "max_watch_last_trade_age_minutes",
            "max_stale_book_minutes_for_score",
            "max_last_trade_age_minutes_for_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_quote_count",
            "min_watch_quote_count",
            "quote_count_full_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class CandidateDecisionMicrostructureQualityInput:
    redacted_candidate_ref: str
    spread_score: Decimal
    depth_score: Decimal
    imbalance_score: Decimal
    stale_book_minutes: Decimal
    last_trade_age_minutes: Decimal
    quote_count: Decimal
    outlier_move_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionMicrostructureQualityInput:
            raise ValueError("input must be a CandidateDecisionMicrostructureQualityInput")
        _require_redacted_candidate_ref(self.redacted_candidate_ref)
        for field_name in (
            "spread_score",
            "depth_score",
            "imbalance_score",
            "outlier_move_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_book_minutes", "last_trade_age_minutes"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quote_count",
            _normalize_count_decimal("quote_count", self.quote_count),
        )
        _require_safety_flags("input", self)


@dataclass(frozen=True)
class CandidateDecisionMicrostructureQualityRow:
    redacted_candidate_ref: str
    spread_score: Decimal
    depth_score: Decimal
    imbalance_score: Decimal
    stale_book_minutes: Decimal
    last_trade_age_minutes: Decimal
    quote_count: Decimal
    outlier_move_score: Decimal
    spread_component_score: Decimal
    depth_component_score: Decimal
    imbalance_component_score: Decimal
    stale_book_component_score: Decimal
    last_activity_component_score: Decimal
    quote_count_component_score: Decimal
    outlier_move_component_score: Decimal
    quality_score: Decimal
    spread_weight: Decimal
    depth_weight: Decimal
    imbalance_weight: Decimal
    stale_book_weight: Decimal
    last_activity_weight: Decimal
    quote_count_weight: Decimal
    outlier_move_weight: Decimal
    status: str
    reason_codes: tuple[str, ...]
    row_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionMicrostructureQualityRow:
            raise ValueError("row must be a CandidateDecisionMicrostructureQualityRow")
        _require_redacted_candidate_ref(self.redacted_candidate_ref)
        for field_name in (
            "spread_score",
            "depth_score",
            "imbalance_score",
            "outlier_move_score",
            "spread_component_score",
            "depth_component_score",
            "imbalance_component_score",
            "stale_book_component_score",
            "last_activity_component_score",
            "quote_count_component_score",
            "outlier_move_component_score",
            "quality_score",
            "spread_weight",
            "depth_weight",
            "imbalance_weight",
            "stale_book_weight",
            "last_activity_weight",
            "quote_count_weight",
            "outlier_move_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_book_minutes", "last_trade_age_minutes"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quote_count",
            _normalize_count_decimal("quote_count", self.quote_count),
        )
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("row", self)
        if self.row_sha256:
            object.__setattr__(
                self,
                "row_sha256",
                _normalize_sha256("row_sha256", self.row_sha256),
            )
        else:
            object.__setattr__(self, "row_sha256", _row_sha256(self))
        if self.derived_validation_digest:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        _validate_row(self)


@dataclass(frozen=True)
class CandidateDecisionMicrostructureQualityReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_quality_score: Decimal
    max_stale_book_minutes: Decimal
    max_last_trade_age_minutes: Decimal
    min_quote_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[CandidateDecisionMicrostructureQualityRow, ...]
    report_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionMicrostructureQualityReport:
            raise ValueError("report must be a CandidateDecisionMicrostructureQualityReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_str("config_version", self.config_version)
        _reject_unsafe_text("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "min_quote_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_quality_score",
            _normalize_unit_decimal("min_quality_score", self.min_quality_score),
        )
        for field_name in ("max_stale_book_minutes", "max_last_trade_age_minutes"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_safety_flags("report", self)
        if self.report_sha256:
            object.__setattr__(
                self,
                "report_sha256",
                _normalize_sha256("report_sha256", self.report_sha256),
            )
        else:
            object.__setattr__(self, "report_sha256", _report_sha256(self))
        if self.derived_validation_digest:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        _validate_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_microstructure_quality_score_payload(self)


def build_candidate_decision_microstructure_quality_score(
    items: Iterable[object],
    *,
    config: CandidateDecisionMicrostructureQualityScoreConfig,
    generated_at: datetime,
) -> CandidateDecisionMicrostructureQualityReport:
    if isinstance(items, str | bytes):
        raise ValueError("items must be an iterable")
    try:
        normalized_items = tuple(items)
    except TypeError as exc:
        raise ValueError("items must be an iterable") from exc
    if type(config) is not CandidateDecisionMicrostructureQualityScoreConfig:
        raise ValueError("config must be a CandidateDecisionMicrostructureQualityScoreConfig")
    _require_safety_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    seen_refs: set[str] = set()
    rows: list[CandidateDecisionMicrostructureQualityRow] = []
    for item in normalized_items:
        if type(item) is not CandidateDecisionMicrostructureQualityInput:
            raise ValueError(
                "items must contain CandidateDecisionMicrostructureQualityInput",
            )
        _require_safety_flags("input", item)
        if item.redacted_candidate_ref in seen_refs:
            raise ValueError("duplicate redacted_candidate_ref")
        seen_refs.add(item.redacted_candidate_ref)
        rows.append(_row_from_input(item, config=config))
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    return CandidateDecisionMicrostructureQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(sorted_rows)),
        pass_count=_status_count(sorted_rows, "pass"),
        watch_count=_status_count(sorted_rows, "watch"),
        block_count=_status_count(sorted_rows, "block"),
        min_quality_score=_min_quality_score(sorted_rows),
        max_stale_book_minutes=_max_decimal(sorted_rows, "stale_book_minutes"),
        max_last_trade_age_minutes=_max_decimal(sorted_rows, "last_trade_age_minutes"),
        min_quote_count=_min_count(sorted_rows, "quote_count"),
        status=_report_status(sorted_rows),
        reason_codes=_report_reason_codes(sorted_rows),
        rows=sorted_rows,
    )


def candidate_decision_microstructure_quality_score_payload(
    report: CandidateDecisionMicrostructureQualityReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionMicrostructureQualityReport:
        raise ValueError("report must be a CandidateDecisionMicrostructureQualityReport")
    _validate_report(report)
    payload = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "candidate_count": _decimal_payload(report.candidate_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "min_quality_score": _decimal_payload(report.min_quality_score),
        "max_stale_book_minutes": _decimal_payload(report.max_stale_book_minutes),
        "max_last_activity_age_minutes": _decimal_payload(
            report.max_last_trade_age_minutes,
        ),
        "min_quote_count": _decimal_payload(report.min_quote_count),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "report_sha256": report.report_sha256,
        "derived_validation_digest": report.derived_validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    validate_candidate_decision_microstructure_quality_public_payload(payload)
    return payload


def validate_candidate_decision_microstructure_quality_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_flags(payload)
    return True


def _row_from_input(
    item: CandidateDecisionMicrostructureQualityInput,
    *,
    config: CandidateDecisionMicrostructureQualityScoreConfig,
) -> CandidateDecisionMicrostructureQualityRow:
    spread_component = item.spread_score
    depth_component = item.depth_score
    imbalance_component = _ONE - item.imbalance_score
    stale_book_component = _inverse_ratio_score(
        item.stale_book_minutes,
        config.max_stale_book_minutes_for_score,
    )
    recent_activity_component = _inverse_ratio_score(
        item.last_trade_age_minutes,
        config.max_last_trade_age_minutes_for_score,
    )
    quote_count_component = _quote_count_component_score(item.quote_count, config)
    outlier_move_component = _ONE - item.outlier_move_score
    quality_score = _quality_score(
        spread_component=spread_component,
        depth_component=depth_component,
        imbalance_component=imbalance_component,
        stale_book_component=stale_book_component,
        recent_activity_component=recent_activity_component,
        quote_count_component=quote_count_component,
        outlier_move_component=outlier_move_component,
        config=config,
    )
    reason_codes = _reason_codes_for_input(
        item,
        quality_score=quality_score,
        config=config,
    )
    return CandidateDecisionMicrostructureQualityRow(
        redacted_candidate_ref=item.redacted_candidate_ref,
        spread_score=item.spread_score,
        depth_score=item.depth_score,
        imbalance_score=item.imbalance_score,
        stale_book_minutes=item.stale_book_minutes,
        last_trade_age_minutes=item.last_trade_age_minutes,
        quote_count=item.quote_count,
        outlier_move_score=item.outlier_move_score,
        spread_component_score=spread_component,
        depth_component_score=depth_component,
        imbalance_component_score=imbalance_component,
        stale_book_component_score=stale_book_component,
        last_activity_component_score=recent_activity_component,
        quote_count_component_score=quote_count_component,
        outlier_move_component_score=outlier_move_component,
        quality_score=quality_score,
        spread_weight=config.spread_weight,
        depth_weight=config.depth_weight,
        imbalance_weight=config.imbalance_weight,
        stale_book_weight=config.stale_book_weight,
        last_activity_weight=config.last_activity_weight,
        quote_count_weight=config.quote_count_weight,
        outlier_move_weight=config.outlier_move_weight,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_payload(row: CandidateDecisionMicrostructureQualityRow) -> dict[str, Any]:
    _require_safety_flags("row", row)
    payload = {
        "redacted_candidate_ref": row.redacted_candidate_ref,
        "spread_score": _decimal_payload(row.spread_score),
        "depth_score": _decimal_payload(row.depth_score),
        "imbalance_score": _decimal_payload(row.imbalance_score),
        "stale_book_minutes": _decimal_payload(row.stale_book_minutes),
        "last_activity_age_minutes": _decimal_payload(row.last_trade_age_minutes),
        "quote_count": _decimal_payload(row.quote_count),
        "outlier_move_score": _decimal_payload(row.outlier_move_score),
        "spread_component_score": _decimal_payload(row.spread_component_score),
        "depth_component_score": _decimal_payload(row.depth_component_score),
        "imbalance_component_score": _decimal_payload(row.imbalance_component_score),
        "stale_book_component_score": _decimal_payload(row.stale_book_component_score),
        "last_activity_component_score": _decimal_payload(
            row.last_activity_component_score,
        ),
        "quote_count_component_score": _decimal_payload(row.quote_count_component_score),
        "outlier_move_component_score": _decimal_payload(
            row.outlier_move_component_score,
        ),
        "quality_score": _decimal_payload(row.quality_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "row_sha256": row.row_sha256,
        "derived_validation_digest": row.derived_validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_public_payload("row payload", payload)
    return payload


def _reason_codes_for_input(
    item: CandidateDecisionMicrostructureQualityInput,
    *,
    quality_score: Decimal,
    config: CandidateDecisionMicrostructureQualityScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_score_floor_reason(
        reason_codes,
        item.spread_score,
        config.min_pass_spread_score,
        config.min_watch_spread_score,
        _SPREAD_WATCH_REASON_CODE,
        _SPREAD_BLOCK_REASON_CODE,
    )
    _append_score_floor_reason(
        reason_codes,
        item.depth_score,
        config.min_pass_depth_score,
        config.min_watch_depth_score,
        _DEPTH_WATCH_REASON_CODE,
        _DEPTH_BLOCK_REASON_CODE,
    )
    _append_risk_ceiling_reason(
        reason_codes,
        item.imbalance_score,
        config.max_pass_imbalance_score,
        config.max_watch_imbalance_score,
        _IMBALANCE_WATCH_REASON_CODE,
        _IMBALANCE_BLOCK_REASON_CODE,
    )
    _append_risk_ceiling_reason(
        reason_codes,
        item.stale_book_minutes,
        config.max_pass_stale_book_minutes,
        config.max_watch_stale_book_minutes,
        _STALE_BOOK_WATCH_REASON_CODE,
        _STALE_BOOK_BLOCK_REASON_CODE,
    )
    _append_risk_ceiling_reason(
        reason_codes,
        item.last_trade_age_minutes,
        config.max_pass_last_trade_age_minutes,
        config.max_watch_last_trade_age_minutes,
        _RECENT_ACTIVITY_WATCH_REASON_CODE,
        _RECENT_ACTIVITY_BLOCK_REASON_CODE,
    )
    _append_score_floor_reason(
        reason_codes,
        item.quote_count,
        config.min_pass_quote_count,
        config.min_watch_quote_count,
        _QUOTE_WATCH_REASON_CODE,
        _QUOTE_BLOCK_REASON_CODE,
    )
    _append_risk_ceiling_reason(
        reason_codes,
        item.outlier_move_score,
        config.max_pass_outlier_move_score,
        config.max_watch_outlier_move_score,
        _OUTLIER_WATCH_REASON_CODE,
        _OUTLIER_BLOCK_REASON_CODE,
    )
    if quality_score < config.min_watch_quality_score:
        reason_codes.append(_QUALITY_BLOCK_REASON_CODE)
    elif quality_score < config.min_pass_quality_score:
        reason_codes.append(_QUALITY_WATCH_REASON_CODE)
    if not reason_codes:
        return (_PASS_REASON_CODE,)
    return tuple(reason_codes)


def _append_score_floor_reason(
    reason_codes: list[str],
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value < watch_threshold:
        reason_codes.append(block_reason)
    elif value < pass_threshold:
        reason_codes.append(watch_reason)


def _append_risk_ceiling_reason(
    reason_codes: list[str],
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value > watch_threshold:
        reason_codes.append(block_reason)
    elif value > pass_threshold:
        reason_codes.append(watch_reason)


def _quality_score(
    *,
    spread_component: Decimal,
    depth_component: Decimal,
    imbalance_component: Decimal,
    stale_book_component: Decimal,
    recent_activity_component: Decimal,
    quote_count_component: Decimal,
    outlier_move_component: Decimal,
    config: CandidateDecisionMicrostructureQualityScoreConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        score = (
            spread_component * config.spread_weight
            + depth_component * config.depth_weight
            + imbalance_component * config.imbalance_weight
            + stale_book_component * config.stale_book_weight
            + recent_activity_component * config.last_activity_weight
            + quote_count_component * config.quote_count_weight
            + outlier_move_component * config.outlier_move_weight
        )
    return _bounded_unit(score)


def _inverse_ratio_score(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("score denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        ratio = value / denominator
        score = _ONE - _bounded_unit(ratio)
    return _bounded_unit(score)


def _quote_count_component_score(
    quote_count: Decimal,
    config: CandidateDecisionMicrostructureQualityScoreConfig,
) -> Decimal:
    if quote_count < config.min_watch_quote_count:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        score = quote_count / config.quote_count_full_score
    return _bounded_unit(score)


def _validate_config(config: CandidateDecisionMicrostructureQualityScoreConfig) -> None:
    if config.min_pass_quality_score < config.min_watch_quality_score:
        raise ValueError("min_pass_quality_score must be at least watch threshold")
    if config.min_pass_spread_score < config.min_watch_spread_score:
        raise ValueError("min_pass_spread_score must be at least watch threshold")
    if config.min_pass_depth_score < config.min_watch_depth_score:
        raise ValueError("min_pass_depth_score must be at least watch threshold")
    if config.max_pass_imbalance_score > config.max_watch_imbalance_score:
        raise ValueError("max_pass_imbalance_score must not exceed watch threshold")
    if config.max_pass_stale_book_minutes > config.max_watch_stale_book_minutes:
        raise ValueError("max_pass_stale_book_minutes must not exceed watch threshold")
    if config.max_pass_last_trade_age_minutes > config.max_watch_last_trade_age_minutes:
        raise ValueError("max_pass_last_trade_age_minutes must not exceed watch threshold")
    if config.min_pass_quote_count < config.min_watch_quote_count:
        raise ValueError("min_pass_quote_count must be at least watch threshold")
    if config.max_pass_outlier_move_score > config.max_watch_outlier_move_score:
        raise ValueError("max_pass_outlier_move_score must not exceed watch threshold")
    if config.max_stale_book_minutes_for_score <= _ZERO:
        raise ValueError("max_stale_book_minutes_for_score must be positive")
    if config.max_last_trade_age_minutes_for_score <= _ZERO:
        raise ValueError("max_last_trade_age_minutes_for_score must be positive")
    if config.quote_count_full_score <= _ZERO:
        raise ValueError("quote_count_full_score must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        weight_sum = (
            config.spread_weight
            + config.depth_weight
            + config.imbalance_weight
            + config.stale_book_weight
            + config.last_activity_weight
            + config.quote_count_weight
            + config.outlier_move_weight
        )
    if _q(weight_sum) != _ONE:
        raise ValueError("weights must sum to 1")


def _validate_row(row: CandidateDecisionMicrostructureQualityRow) -> None:
    if row.spread_component_score != row.spread_score:
        raise ValueError("spread_component_score must match spread_score")
    if row.depth_component_score != row.depth_score:
        raise ValueError("depth_component_score must match depth_score")
    if row.imbalance_component_score != _bounded_unit(_ONE - row.imbalance_score):
        raise ValueError("imbalance_component_score must match imbalance_score")
    with localcontext(_DECIMAL_CONTEXT):
        weight_sum = (
            row.spread_weight
            + row.depth_weight
            + row.imbalance_weight
            + row.stale_book_weight
            + row.last_activity_weight
            + row.quote_count_weight
            + row.outlier_move_weight
        )
    if _q(weight_sum) != _ONE:
        raise ValueError("weights must sum to 1")
    expected_quality_score = _quality_score(
        spread_component=row.spread_component_score,
        depth_component=row.depth_component_score,
        imbalance_component=row.imbalance_component_score,
        stale_book_component=row.stale_book_component_score,
        recent_activity_component=row.last_activity_component_score,
        quote_count_component=row.quote_count_component_score,
        outlier_move_component=row.outlier_move_component_score,
        config=_row_config(row),
    )
    if row.quality_score != expected_quality_score:
        raise ValueError("quality_score must match component scores and weights")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.row_sha256 != _row_sha256(row):
        raise ValueError("row_sha256 must match row fields")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: CandidateDecisionMicrostructureQualityReport) -> None:
    rows = report.rows
    if report.candidate_count != _count_decimal(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.min_quality_score != _min_quality_score(rows):
        raise ValueError("min_quality_score must match rows")
    if report.max_stale_book_minutes != _max_decimal(rows, "stale_book_minutes"):
        raise ValueError("max_stale_book_minutes must match rows")
    if report.max_last_trade_age_minutes != _max_decimal(rows, "last_trade_age_minutes"):
        raise ValueError("max_last_trade_age_minutes must match rows")
    if report.min_quote_count != _min_count(rows, "quote_count"):
        raise ValueError("min_quote_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.report_sha256 != _report_sha256(report):
        raise ValueError("report_sha256 must match report fields")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _normalize_rows(
    rows: object,
) -> tuple[CandidateDecisionMicrostructureQualityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not CandidateDecisionMicrostructureQualityRow:
            raise ValueError("rows must contain CandidateDecisionMicrostructureQualityRow")
        _require_safety_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _row_config(
    row: CandidateDecisionMicrostructureQualityRow,
) -> CandidateDecisionMicrostructureQualityScoreConfig:
    return CandidateDecisionMicrostructureQualityScoreConfig(
        spread_weight=row.spread_weight,
        depth_weight=row.depth_weight,
        imbalance_weight=row.imbalance_weight,
        stale_book_weight=row.stale_book_weight,
        last_activity_weight=row.last_activity_weight,
        quote_count_weight=row.quote_count_weight,
        outlier_move_weight=row.outlier_move_weight,
    )


def _row_sort_key(row: CandidateDecisionMicrostructureQualityRow) -> tuple[int, Decimal, str]:
    return (_STATUS_PRIORITY[row.status], row.quality_score, row.redacted_candidate_ref)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in _WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[CandidateDecisionMicrostructureQualityRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows) or not rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[CandidateDecisionMicrostructureQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON_CODE,)
    present = {reason for row in rows for reason in row.reason_codes}
    if present == {_PASS_REASON_CODE}:
        return (_PASS_REASON_CODE,)
    present.discard(_PASS_REASON_CODE)
    return tuple(reason for reason in _REPORT_REASON_PRIORITY if reason in present)


def _status_count(
    rows: tuple[CandidateDecisionMicrostructureQualityRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _min_quality_score(rows: tuple[CandidateDecisionMicrostructureQualityRow, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return min(row.quality_score for row in rows)


def _max_decimal(
    rows: tuple[CandidateDecisionMicrostructureQualityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_count(
    rows: tuple[CandidateDecisionMicrostructureQualityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _ZERO
    return min(getattr(row, field_name) for row in rows)


def _normalize_reason_codes(
    reason_codes: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_str("reason_codes", reason_code)
        _reject_unsafe_text("reason_codes", reason_code)
        if reason_code not in _REASON_CODES:
            raise ValueError("reason_codes contains unsupported reason")
        if reason_code in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(reason_code)
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must be nonempty")
    return tuple(normalized)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be >= 0")
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be <= 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be an exact Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _q(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _bounded_unit(value: Decimal) -> Decimal:
    if value <= _ZERO:
        return _ZERO
    if value >= _ONE:
        return _ONE
    return _q(value)


def _count_decimal(value: int) -> Decimal:
    return _q(Decimal(str(value)))


def _decimal_payload(value: Decimal) -> str:
    return format(_q(value), "f")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        if isinstance(value, datetime):
            raise ValueError(f"{field_name} must be a datetime")
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_str(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a str")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_redacted_candidate_ref(value: object) -> None:
    _require_str("redacted_candidate_ref", value)
    if not value.startswith("candidate_ref_"):
        raise ValueError("redacted_candidate_ref must start with candidate_ref_")
    _reject_unsafe_text("redacted_candidate_ref", value)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_str(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_bool_true(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    if value is not True:
        raise ValueError(f"{field_name} must be True")


def _require_safety_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        _require_bool_true(field_name, getattr(value, field_name, None))
    _reject_unsafe_public_payload(label, _public_object_view(value))


def _public_object_view(value: object) -> dict[str, Any]:
    return {
        field_name: getattr(value, field_name)
        for field_name in ("paper_only", "report_only", "readonly")
    }


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _normalize_sha256(field_name: str, value: object) -> str:
    _require_str(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _row_sha256(row: CandidateDecisionMicrostructureQualityRow) -> str:
    return _sha256(_row_signature(row, include_validation=False))


def _row_derived_validation_digest(row: CandidateDecisionMicrostructureQualityRow) -> str:
    return _sha256(("row-validation", *_row_signature(row, include_validation=False)))


def _report_sha256(report: CandidateDecisionMicrostructureQualityReport) -> str:
    return _sha256(_report_signature(report, include_validation=False))


def _report_derived_validation_digest(
    report: CandidateDecisionMicrostructureQualityReport,
) -> str:
    return _sha256(
        ("report-validation", *_report_signature(report, include_validation=False)),
    )


def _row_signature(
    row: CandidateDecisionMicrostructureQualityRow,
    *,
    include_validation: bool,
) -> tuple[str, ...]:
    items = (
        row.redacted_candidate_ref,
        _decimal_payload(row.spread_score),
        _decimal_payload(row.depth_score),
        _decimal_payload(row.imbalance_score),
        _decimal_payload(row.stale_book_minutes),
        _decimal_payload(row.last_trade_age_minutes),
        _decimal_payload(row.quote_count),
        _decimal_payload(row.outlier_move_score),
        _decimal_payload(row.spread_component_score),
        _decimal_payload(row.depth_component_score),
        _decimal_payload(row.imbalance_component_score),
        _decimal_payload(row.stale_book_component_score),
        _decimal_payload(row.last_activity_component_score),
        _decimal_payload(row.quote_count_component_score),
        _decimal_payload(row.outlier_move_component_score),
        _decimal_payload(row.quality_score),
        _decimal_payload(row.spread_weight),
        _decimal_payload(row.depth_weight),
        _decimal_payload(row.imbalance_weight),
        _decimal_payload(row.stale_book_weight),
        _decimal_payload(row.last_activity_weight),
        _decimal_payload(row.quote_count_weight),
        _decimal_payload(row.outlier_move_weight),
        row.status,
        ",".join(row.reason_codes),
        str(row.paper_only),
        str(row.report_only),
        str(row.readonly),
    )
    if include_validation:
        return (*items, row.row_sha256, row.derived_validation_digest)
    return items


def _report_signature(
    report: CandidateDecisionMicrostructureQualityReport,
    *,
    include_validation: bool,
) -> tuple[str, ...]:
    items = (
        report.generated_at.isoformat(),
        report.config_version,
        _decimal_payload(report.candidate_count),
        _decimal_payload(report.pass_count),
        _decimal_payload(report.watch_count),
        _decimal_payload(report.block_count),
        _decimal_payload(report.min_quality_score),
        _decimal_payload(report.max_stale_book_minutes),
        _decimal_payload(report.max_last_trade_age_minutes),
        _decimal_payload(report.min_quote_count),
        report.status,
        ",".join(report.reason_codes),
        ";".join(row.row_sha256 for row in report.rows),
        str(report.paper_only),
        str(report.report_only),
        str(report.readonly),
    )
    if include_validation:
        return (*items, report.report_sha256, report.derived_validation_digest)
    return items


def _sha256(parts: tuple[str, ...]) -> str:
    return sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload field")
            _reject_unsafe_key(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list | tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)


def _reject_unsafe_key(label: str, key: str) -> None:
    compact = _compact(key)
    if compact == "redactedcandidateref":
        return
    if compact in _UNSAFE_KEY_COMPACTS:
        raise ValueError(f"unsafe public payload field in {label}")
    if any(fragment in compact for fragment in _UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"unsafe public payload field in {label}")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    compact = _compact(value)
    if any(token in compact for token in _UNSAFE_TEXT_TOKENS):
        raise ValueError(f"{field_name} unsafe public payload value")


def _compact(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())
