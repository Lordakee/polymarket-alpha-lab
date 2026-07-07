"""Pure report-only liquidity regime shift scoring for candidate priority."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_CANDIDATE_DECISION_LIQUIDITY_REGIME_SHIFT_SCORE_CONFIG_VERSION = (
    "candidate-decision-liquidity-regime-shift-score-v0"
)

_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_STATUSES = ("pass", "watch", "block")
_STATUS_PRIORITY = {"block": 0, "watch": 1, "pass": 2}

_PASS_REASON_CODE = "liquidity_regime_shift_pass"
_EMPTY_REASON_CODE = "liquidity_regime_shift_empty"
_DEPTH_BLOCK_REASON_CODE = "depth_regime_shift_block"
_SPREAD_BLOCK_REASON_CODE = "spread_regime_shift_block"
_VOLUME_BLOCK_REASON_CODE = "volume_regime_shift_block"
_STALE_QUOTE_BLOCK_REASON_CODE = "stale_quote_block"
_SHIFT_SCORE_BLOCK_REASON_CODE = "shift_score_block"
_DEPTH_WATCH_REASON_CODE = "depth_regime_shift_watch"
_SPREAD_WATCH_REASON_CODE = "spread_regime_shift_watch"
_VOLUME_WATCH_REASON_CODE = "volume_regime_shift_watch"
_STALE_QUOTE_WATCH_REASON_CODE = "stale_quote_watch"
_SHIFT_SCORE_WATCH_REASON_CODE = "shift_score_watch"

_BLOCK_REASON_CODES = (
    _DEPTH_BLOCK_REASON_CODE,
    _SPREAD_BLOCK_REASON_CODE,
    _VOLUME_BLOCK_REASON_CODE,
    _STALE_QUOTE_BLOCK_REASON_CODE,
    _SHIFT_SCORE_BLOCK_REASON_CODE,
)
_WATCH_REASON_CODES = (
    _DEPTH_WATCH_REASON_CODE,
    _SPREAD_WATCH_REASON_CODE,
    _VOLUME_WATCH_REASON_CODE,
    _STALE_QUOTE_WATCH_REASON_CODE,
    _SHIFT_SCORE_WATCH_REASON_CODE,
)
_REASON_CODES = (
    _PASS_REASON_CODE,
    _EMPTY_REASON_CODE,
    *_BLOCK_REASON_CODES,
    *_WATCH_REASON_CODES,
)
_REPORT_REASON_PRIORITY = (
    _DEPTH_BLOCK_REASON_CODE,
    _SPREAD_BLOCK_REASON_CODE,
    _VOLUME_BLOCK_REASON_CODE,
    _STALE_QUOTE_BLOCK_REASON_CODE,
    _SHIFT_SCORE_BLOCK_REASON_CODE,
    _DEPTH_WATCH_REASON_CODE,
    _SPREAD_WATCH_REASON_CODE,
    _VOLUME_WATCH_REASON_CODE,
    _STALE_QUOTE_WATCH_REASON_CODE,
    _SHIFT_SCORE_WATCH_REASON_CODE,
)

_UNSAFE_TEXT_TOKENS = (
    "au" + "th",
    "b" + "uy",
    "block" + "ed",
    "cred" + "ential",
    "dsn",
    "match" + "ed",
    "or" + "der",
    "pos" + "ition",
    "private" + "_key",
    "read" + "y",
    "rec" + "ommend",
    "rec" + "ommendation",
    "s" + "ell",
    "sec" + "ret",
    "siz" + "ing",
    "sup" + "abase",
    "support" + "ed",
    "to" + "ken",
    "tr" + "ade",
    "wal" + "let",
    "postgres",
    "postgresql",
    "mysql",
    "sqlite",
    "mongodb",
)
_UNSAFE_KEY_COMPACTS = (
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
    "sourcetext",
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
    "databaseurl",
    "dburl",
    "sourceurl",
    "sourceuri",
    "sourceref",
    "tablename",
    "to" + "ken",
    "sec" + "ret",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "b" + "uy",
    "s" + "ell",
    "rec" + "ommend",
    "pos" + "ition",
    "siz" + "ing",
)

__all__ = (
    "DEFAULT_CANDIDATE_DECISION_LIQUIDITY_REGIME_SHIFT_SCORE_CONFIG_VERSION",
    "CandidateDecisionLiquidityRegimeShiftScoreConfig",
    "CandidateDecisionLiquidityRegimeShiftInput",
    "CandidateDecisionLiquidityRegimeShiftRow",
    "CandidateDecisionLiquidityRegimeShiftReport",
    "build_candidate_decision_liquidity_regime_shift_score",
    "candidate_decision_liquidity_regime_shift_score_payload",
    "validate_candidate_decision_liquidity_regime_shift_public_payload",
)


@dataclass(frozen=True)
class CandidateDecisionLiquidityRegimeShiftScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_LIQUIDITY_REGIME_SHIFT_SCORE_CONFIG_VERSION
    )
    max_pass_shift_score: Decimal = Decimal("0.250000")
    max_watch_shift_score: Decimal = Decimal("0.600000")
    max_pass_depth_drop_score: Decimal = Decimal("0.200000")
    max_watch_depth_drop_score: Decimal = Decimal("0.500000")
    max_pass_spread_widening_score: Decimal = Decimal("0.200000")
    max_watch_spread_widening_score: Decimal = Decimal("0.600000")
    max_pass_volume_decay_score: Decimal = Decimal("0.250000")
    max_watch_volume_decay_score: Decimal = Decimal("0.600000")
    max_pass_stale_quote_minutes: Decimal = Decimal("2.000000")
    max_watch_stale_quote_minutes: Decimal = Decimal("20.000000")
    max_stale_quote_minutes_for_score: Decimal = Decimal("30.000000")
    depth_drop_weight: Decimal = Decimal("0.300000")
    spread_widening_weight: Decimal = Decimal("0.250000")
    volume_decay_weight: Decimal = Decimal("0.200000")
    stale_quote_weight: Decimal = Decimal("0.150000")
    regime_confidence_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionLiquidityRegimeShiftScoreConfig:
            raise ValueError(
                "config must be a CandidateDecisionLiquidityRegimeShiftScoreConfig",
            )
        _require_str("config_version", self.config_version)
        _reject_unsafe_text("config_version", self.config_version)
        for field_name in (
            "max_pass_shift_score",
            "max_watch_shift_score",
            "max_pass_depth_drop_score",
            "max_watch_depth_drop_score",
            "max_pass_spread_widening_score",
            "max_watch_spread_widening_score",
            "max_pass_volume_decay_score",
            "max_watch_volume_decay_score",
            "depth_drop_weight",
            "spread_widening_weight",
            "volume_decay_weight",
            "stale_quote_weight",
            "regime_confidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_stale_quote_minutes",
            "max_watch_stale_quote_minutes",
            "max_stale_quote_minutes_for_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class CandidateDecisionLiquidityRegimeShiftInput:
    redacted_candidate_ref: str
    current_depth_score: Decimal
    historical_depth_score: Decimal
    spread_widening_score: Decimal
    volume_decay_score: Decimal
    stale_quote_minutes: Decimal
    regime_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionLiquidityRegimeShiftInput:
            raise ValueError("input must be a CandidateDecisionLiquidityRegimeShiftInput")
        _require_redacted_candidate_ref(self.redacted_candidate_ref)
        for field_name in (
            "current_depth_score",
            "historical_depth_score",
            "spread_widening_score",
            "volume_decay_score",
            "regime_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_quote_minutes",
            _normalize_nonnegative_decimal(
                "stale_quote_minutes",
                self.stale_quote_minutes,
            ),
        )
        _require_safety_flags("input", self)


@dataclass(frozen=True)
class CandidateDecisionLiquidityRegimeShiftRow:
    redacted_candidate_ref: str
    current_depth_score: Decimal
    historical_depth_score: Decimal
    spread_widening_score: Decimal
    volume_decay_score: Decimal
    stale_quote_minutes: Decimal
    regime_confidence_score: Decimal
    depth_drop_score: Decimal
    stale_quote_component_score: Decimal
    confidence_adjusted_shift_component_score: Decimal
    shift_score: Decimal
    max_stale_quote_minutes_for_score: Decimal
    depth_drop_weight: Decimal
    spread_widening_weight: Decimal
    volume_decay_weight: Decimal
    stale_quote_weight: Decimal
    regime_confidence_weight: Decimal
    status: str
    reason_codes: tuple[str, ...]
    row_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionLiquidityRegimeShiftRow:
            raise ValueError("row must be a CandidateDecisionLiquidityRegimeShiftRow")
        _require_redacted_candidate_ref(self.redacted_candidate_ref)
        for field_name in (
            "current_depth_score",
            "historical_depth_score",
            "spread_widening_score",
            "volume_decay_score",
            "regime_confidence_score",
            "depth_drop_score",
            "stale_quote_component_score",
            "confidence_adjusted_shift_component_score",
            "shift_score",
            "depth_drop_weight",
            "spread_widening_weight",
            "volume_decay_weight",
            "stale_quote_weight",
            "regime_confidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_quote_minutes", "max_stale_quote_minutes_for_score"):
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
class CandidateDecisionLiquidityRegimeShiftReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_shift_score: Decimal
    max_depth_drop_score: Decimal
    max_stale_quote_minutes: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[CandidateDecisionLiquidityRegimeShiftRow, ...]
    report_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionLiquidityRegimeShiftReport:
            raise ValueError("report must be a CandidateDecisionLiquidityRegimeShiftReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_str("config_version", self.config_version)
        _reject_unsafe_text("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_shift_score",
            "max_depth_drop_score",
            "max_stale_quote_minutes",
        ):
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
        return candidate_decision_liquidity_regime_shift_score_payload(self)


def build_candidate_decision_liquidity_regime_shift_score(
    items: Iterable[object],
    *,
    config: CandidateDecisionLiquidityRegimeShiftScoreConfig,
    generated_at: datetime,
) -> CandidateDecisionLiquidityRegimeShiftReport:
    if isinstance(items, str | bytes):
        raise ValueError("items must be an iterable")
    try:
        normalized_items = tuple(items)
    except TypeError as exc:
        raise ValueError("items must be an iterable") from exc
    if type(config) is not CandidateDecisionLiquidityRegimeShiftScoreConfig:
        raise ValueError("config must be a CandidateDecisionLiquidityRegimeShiftScoreConfig")
    _require_safety_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    seen_refs: set[str] = set()
    rows: list[CandidateDecisionLiquidityRegimeShiftRow] = []
    for item in normalized_items:
        if type(item) is not CandidateDecisionLiquidityRegimeShiftInput:
            raise ValueError(
                "items must contain CandidateDecisionLiquidityRegimeShiftInput",
            )
        _require_safety_flags("input", item)
        if item.redacted_candidate_ref in seen_refs:
            raise ValueError("duplicate redacted_candidate_ref")
        seen_refs.add(item.redacted_candidate_ref)
        rows.append(_row_from_input(item, config=config))
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    return CandidateDecisionLiquidityRegimeShiftReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(sorted_rows)),
        pass_count=_status_count(sorted_rows, "pass"),
        watch_count=_status_count(sorted_rows, "watch"),
        block_count=_status_count(sorted_rows, "block"),
        max_shift_score=_max_decimal(sorted_rows, "shift_score"),
        max_depth_drop_score=_max_decimal(sorted_rows, "depth_drop_score"),
        max_stale_quote_minutes=_max_decimal(sorted_rows, "stale_quote_minutes"),
        status=_report_status(sorted_rows),
        reason_codes=_report_reason_codes(sorted_rows),
        rows=sorted_rows,
    )


def candidate_decision_liquidity_regime_shift_score_payload(
    report: CandidateDecisionLiquidityRegimeShiftReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionLiquidityRegimeShiftReport:
        raise ValueError("report must be a CandidateDecisionLiquidityRegimeShiftReport")
    _validate_report(report)
    payload = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "candidate_count": _decimal_payload(report.candidate_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "max_shift_score": _decimal_payload(report.max_shift_score),
        "max_depth_drop_score": _decimal_payload(report.max_depth_drop_score),
        "max_stale_quote_minutes": _decimal_payload(report.max_stale_quote_minutes),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "report_sha256": report.report_sha256,
        "derived_validation_digest": report.derived_validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    validate_candidate_decision_liquidity_regime_shift_public_payload(payload)
    return payload


def validate_candidate_decision_liquidity_regime_shift_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_flags(payload)
    return True


def _row_from_input(
    item: CandidateDecisionLiquidityRegimeShiftInput,
    *,
    config: CandidateDecisionLiquidityRegimeShiftScoreConfig,
) -> CandidateDecisionLiquidityRegimeShiftRow:
    depth_drop_score = _depth_drop_score(item)
    stale_quote_component_score = _ratio_score(
        item.stale_quote_minutes,
        config.max_stale_quote_minutes_for_score,
    )
    confidence_adjusted_shift_component_score = _confidence_adjusted_shift_component(
        depth_drop_score=depth_drop_score,
        spread_widening_score=item.spread_widening_score,
        volume_decay_score=item.volume_decay_score,
        stale_quote_component_score=stale_quote_component_score,
        regime_confidence_score=item.regime_confidence_score,
    )
    shift_score = _shift_score(
        depth_drop_score=depth_drop_score,
        spread_widening_score=item.spread_widening_score,
        volume_decay_score=item.volume_decay_score,
        stale_quote_component_score=stale_quote_component_score,
        confidence_adjusted_shift_component_score=(
            confidence_adjusted_shift_component_score
        ),
        config=config,
    )
    reason_codes = _reason_codes_for_input(
        item,
        depth_drop_score=depth_drop_score,
        shift_score=shift_score,
        config=config,
    )
    return CandidateDecisionLiquidityRegimeShiftRow(
        redacted_candidate_ref=item.redacted_candidate_ref,
        current_depth_score=item.current_depth_score,
        historical_depth_score=item.historical_depth_score,
        spread_widening_score=item.spread_widening_score,
        volume_decay_score=item.volume_decay_score,
        stale_quote_minutes=item.stale_quote_minutes,
        regime_confidence_score=item.regime_confidence_score,
        depth_drop_score=depth_drop_score,
        stale_quote_component_score=stale_quote_component_score,
        confidence_adjusted_shift_component_score=(
            confidence_adjusted_shift_component_score
        ),
        shift_score=shift_score,
        max_stale_quote_minutes_for_score=config.max_stale_quote_minutes_for_score,
        depth_drop_weight=config.depth_drop_weight,
        spread_widening_weight=config.spread_widening_weight,
        volume_decay_weight=config.volume_decay_weight,
        stale_quote_weight=config.stale_quote_weight,
        regime_confidence_weight=config.regime_confidence_weight,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_payload(row: CandidateDecisionLiquidityRegimeShiftRow) -> dict[str, Any]:
    _require_safety_flags("row", row)
    payload = {
        "redacted_candidate_ref": row.redacted_candidate_ref,
        "current_depth_score": _decimal_payload(row.current_depth_score),
        "historical_depth_score": _decimal_payload(row.historical_depth_score),
        "spread_widening_score": _decimal_payload(row.spread_widening_score),
        "volume_decay_score": _decimal_payload(row.volume_decay_score),
        "stale_quote_minutes": _decimal_payload(row.stale_quote_minutes),
        "regime_confidence_score": _decimal_payload(row.regime_confidence_score),
        "depth_drop_score": _decimal_payload(row.depth_drop_score),
        "stale_quote_component_score": _decimal_payload(
            row.stale_quote_component_score,
        ),
        "confidence_adjusted_shift_component_score": _decimal_payload(
            row.confidence_adjusted_shift_component_score,
        ),
        "shift_score": _decimal_payload(row.shift_score),
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
    item: CandidateDecisionLiquidityRegimeShiftInput,
    *,
    depth_drop_score: Decimal,
    shift_score: Decimal,
    config: CandidateDecisionLiquidityRegimeShiftScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_risk_ceiling_reason(
        reason_codes,
        depth_drop_score,
        config.max_pass_depth_drop_score,
        config.max_watch_depth_drop_score,
        _DEPTH_WATCH_REASON_CODE,
        _DEPTH_BLOCK_REASON_CODE,
    )
    _append_risk_ceiling_reason(
        reason_codes,
        item.spread_widening_score,
        config.max_pass_spread_widening_score,
        config.max_watch_spread_widening_score,
        _SPREAD_WATCH_REASON_CODE,
        _SPREAD_BLOCK_REASON_CODE,
    )
    _append_risk_ceiling_reason(
        reason_codes,
        item.volume_decay_score,
        config.max_pass_volume_decay_score,
        config.max_watch_volume_decay_score,
        _VOLUME_WATCH_REASON_CODE,
        _VOLUME_BLOCK_REASON_CODE,
    )
    _append_risk_ceiling_reason(
        reason_codes,
        item.stale_quote_minutes,
        config.max_pass_stale_quote_minutes,
        config.max_watch_stale_quote_minutes,
        _STALE_QUOTE_WATCH_REASON_CODE,
        _STALE_QUOTE_BLOCK_REASON_CODE,
    )
    _append_risk_ceiling_reason(
        reason_codes,
        shift_score,
        config.max_pass_shift_score,
        config.max_watch_shift_score,
        _SHIFT_SCORE_WATCH_REASON_CODE,
        _SHIFT_SCORE_BLOCK_REASON_CODE,
    )
    if not reason_codes:
        return (_PASS_REASON_CODE,)
    return tuple(reason_codes)


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


def _depth_drop_score(item: CandidateDecisionLiquidityRegimeShiftInput) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        drop = item.historical_depth_score - item.current_depth_score
    return _bounded_unit(drop)


def _ratio_score(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("score denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        score = value / denominator
    return _bounded_unit(score)


def _confidence_adjusted_shift_component(
    *,
    depth_drop_score: Decimal,
    spread_widening_score: Decimal,
    volume_decay_score: Decimal,
    stale_quote_component_score: Decimal,
    regime_confidence_score: Decimal,
) -> Decimal:
    max_observed_shift = max(
        depth_drop_score,
        spread_widening_score,
        volume_decay_score,
        stale_quote_component_score,
    )
    with localcontext(_DECIMAL_CONTEXT):
        score = max_observed_shift * regime_confidence_score
    return _bounded_unit(score)


def _shift_score(
    *,
    depth_drop_score: Decimal,
    spread_widening_score: Decimal,
    volume_decay_score: Decimal,
    stale_quote_component_score: Decimal,
    confidence_adjusted_shift_component_score: Decimal,
    config: CandidateDecisionLiquidityRegimeShiftScoreConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        score = (
            depth_drop_score * config.depth_drop_weight
            + spread_widening_score * config.spread_widening_weight
            + volume_decay_score * config.volume_decay_weight
            + stale_quote_component_score * config.stale_quote_weight
            + confidence_adjusted_shift_component_score
            * config.regime_confidence_weight
        )
    return _bounded_unit(score)


def _validate_config(config: CandidateDecisionLiquidityRegimeShiftScoreConfig) -> None:
    if config.max_pass_shift_score > config.max_watch_shift_score:
        raise ValueError("max_pass_shift_score must not exceed watch threshold")
    if config.max_pass_depth_drop_score > config.max_watch_depth_drop_score:
        raise ValueError("max_pass_depth_drop_score must not exceed watch threshold")
    if config.max_pass_spread_widening_score > config.max_watch_spread_widening_score:
        raise ValueError("max_pass_spread_widening_score must not exceed watch threshold")
    if config.max_pass_volume_decay_score > config.max_watch_volume_decay_score:
        raise ValueError("max_pass_volume_decay_score must not exceed watch threshold")
    if config.max_pass_stale_quote_minutes > config.max_watch_stale_quote_minutes:
        raise ValueError("max_pass_stale_quote_minutes must not exceed watch threshold")
    if config.max_stale_quote_minutes_for_score <= _ZERO:
        raise ValueError("max_stale_quote_minutes_for_score must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        weight_sum = (
            config.depth_drop_weight
            + config.spread_widening_weight
            + config.volume_decay_weight
            + config.stale_quote_weight
            + config.regime_confidence_weight
        )
    if _q(weight_sum) != _ONE:
        raise ValueError("weights must sum to 1")


def _validate_row(row: CandidateDecisionLiquidityRegimeShiftRow) -> None:
    expected_depth_drop_score = _bounded_unit(
        row.historical_depth_score - row.current_depth_score,
    )
    if row.depth_drop_score != expected_depth_drop_score:
        raise ValueError("depth_drop_score must match depth scores")
    expected_stale_quote_component_score = _ratio_score(
        row.stale_quote_minutes,
        row.max_stale_quote_minutes_for_score,
    )
    if row.stale_quote_component_score != expected_stale_quote_component_score:
        raise ValueError("stale_quote_component_score must match stale_quote_minutes")
    expected_confidence_component = _confidence_adjusted_shift_component(
        depth_drop_score=row.depth_drop_score,
        spread_widening_score=row.spread_widening_score,
        volume_decay_score=row.volume_decay_score,
        stale_quote_component_score=row.stale_quote_component_score,
        regime_confidence_score=row.regime_confidence_score,
    )
    if row.confidence_adjusted_shift_component_score != expected_confidence_component:
        raise ValueError(
            "confidence_adjusted_shift_component_score must match shift inputs",
        )
    with localcontext(_DECIMAL_CONTEXT):
        weight_sum = (
            row.depth_drop_weight
            + row.spread_widening_weight
            + row.volume_decay_weight
            + row.stale_quote_weight
            + row.regime_confidence_weight
        )
    if _q(weight_sum) != _ONE:
        raise ValueError("weights must sum to 1")
    expected_shift_score = _shift_score(
        depth_drop_score=row.depth_drop_score,
        spread_widening_score=row.spread_widening_score,
        volume_decay_score=row.volume_decay_score,
        stale_quote_component_score=row.stale_quote_component_score,
        confidence_adjusted_shift_component_score=(
            row.confidence_adjusted_shift_component_score
        ),
        config=_row_config(row),
    )
    if row.shift_score != expected_shift_score:
        raise ValueError("shift_score must match component scores and weights")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.row_sha256 != _row_sha256(row):
        raise ValueError("row_sha256 must match row fields")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: CandidateDecisionLiquidityRegimeShiftReport) -> None:
    rows = report.rows
    if report.candidate_count != _count_decimal(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.max_shift_score != _max_decimal(rows, "shift_score"):
        raise ValueError("max_shift_score must match rows")
    if report.max_depth_drop_score != _max_decimal(rows, "depth_drop_score"):
        raise ValueError("max_depth_drop_score must match rows")
    if report.max_stale_quote_minutes != _max_decimal(rows, "stale_quote_minutes"):
        raise ValueError("max_stale_quote_minutes must match rows")
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
) -> tuple[CandidateDecisionLiquidityRegimeShiftRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not CandidateDecisionLiquidityRegimeShiftRow:
            raise ValueError("rows must contain CandidateDecisionLiquidityRegimeShiftRow")
        _require_safety_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _row_config(
    row: CandidateDecisionLiquidityRegimeShiftRow,
) -> CandidateDecisionLiquidityRegimeShiftScoreConfig:
    return CandidateDecisionLiquidityRegimeShiftScoreConfig(
        max_stale_quote_minutes_for_score=row.max_stale_quote_minutes_for_score,
        depth_drop_weight=row.depth_drop_weight,
        spread_widening_weight=row.spread_widening_weight,
        volume_decay_weight=row.volume_decay_weight,
        stale_quote_weight=row.stale_quote_weight,
        regime_confidence_weight=row.regime_confidence_weight,
    )


def _row_sort_key(row: CandidateDecisionLiquidityRegimeShiftRow) -> tuple[int, Decimal, str]:
    return (_STATUS_PRIORITY[row.status], -row.shift_score, row.redacted_candidate_ref)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in _WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[CandidateDecisionLiquidityRegimeShiftRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows) or not rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[CandidateDecisionLiquidityRegimeShiftRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON_CODE,)
    present = {reason for row in rows for reason in row.reason_codes}
    if present == {_PASS_REASON_CODE}:
        return (_PASS_REASON_CODE,)
    present.discard(_PASS_REASON_CODE)
    return tuple(reason for reason in _REPORT_REASON_PRIORITY if reason in present)


def _status_count(
    rows: tuple[CandidateDecisionLiquidityRegimeShiftRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _max_decimal(
    rows: tuple[CandidateDecisionLiquidityRegimeShiftRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _ZERO
    return max(getattr(row, field_name) for row in rows)


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


def _row_sha256(row: CandidateDecisionLiquidityRegimeShiftRow) -> str:
    return _sha256(_row_signature(row, include_validation=False))


def _row_derived_validation_digest(row: CandidateDecisionLiquidityRegimeShiftRow) -> str:
    return _sha256(("row-validation", *_row_signature(row, include_validation=False)))


def _report_sha256(report: CandidateDecisionLiquidityRegimeShiftReport) -> str:
    return _sha256(_report_signature(report, include_validation=False))


def _report_derived_validation_digest(
    report: CandidateDecisionLiquidityRegimeShiftReport,
) -> str:
    return _sha256(
        ("report-validation", *_report_signature(report, include_validation=False)),
    )


def _row_signature(
    row: CandidateDecisionLiquidityRegimeShiftRow,
    *,
    include_validation: bool,
) -> tuple[str, ...]:
    items = (
        row.redacted_candidate_ref,
        _decimal_payload(row.current_depth_score),
        _decimal_payload(row.historical_depth_score),
        _decimal_payload(row.spread_widening_score),
        _decimal_payload(row.volume_decay_score),
        _decimal_payload(row.stale_quote_minutes),
        _decimal_payload(row.regime_confidence_score),
        _decimal_payload(row.depth_drop_score),
        _decimal_payload(row.stale_quote_component_score),
        _decimal_payload(row.confidence_adjusted_shift_component_score),
        _decimal_payload(row.shift_score),
        _decimal_payload(row.max_stale_quote_minutes_for_score),
        _decimal_payload(row.depth_drop_weight),
        _decimal_payload(row.spread_widening_weight),
        _decimal_payload(row.volume_decay_weight),
        _decimal_payload(row.stale_quote_weight),
        _decimal_payload(row.regime_confidence_weight),
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
    report: CandidateDecisionLiquidityRegimeShiftReport,
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
        _decimal_payload(report.max_shift_score),
        _decimal_payload(report.max_depth_drop_score),
        _decimal_payload(report.max_stale_quote_minutes),
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
    if "://" in value or "?" in value:
        raise ValueError(f"{field_name} unsafe public payload value")
    if any(token in compact for token in _UNSAFE_TEXT_TOKENS):
        raise ValueError(f"{field_name} unsafe public payload value")


def _compact(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())
