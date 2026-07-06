"""Paper-only source disagreement adjusted EV digest."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_STRATEGY_CANDIDATE_SOURCE_DISAGREEMENT_ADJUSTED_EV_V2_CONFIG_VERSION = (
    "strategy-candidate-source-disagreement-adjusted-ev-v2"
)

SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

EV_STATUSES = ("pass", "watch", "blocked")
STATUS_PRIORITY = {"blocked": 0, "watch": 1, "pass": 2}

EMPTY_REASON = "source_disagreement_adjusted_ev_empty"
PASS_REASON = "source_disagreement_adjusted_ev_pass"
BELOW_WATCH_REASON = "adjusted_ev_below_watch_floor"
BELOW_PASS_REASON = "adjusted_ev_below_pass_floor"
DISAGREEMENT_WATCH_REASON = "source_disagreement_watch"
DISAGREEMENT_BLOCK_REASON = "source_disagreement_block"
CONTRADICTION_PENALTY_REASON = "source_contradiction_penalty"
CONTRADICTION_BLOCK_REASON = "source_contradiction_block"
CONSENSUS_BOOST_REASON = "source_consensus_boost"
REPORT_REASON_PRIORITY = (
    DISAGREEMENT_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    BELOW_WATCH_REASON,
    BELOW_PASS_REASON,
    DISAGREEMENT_WATCH_REASON,
    CONTRADICTION_PENALTY_REASON,
    CONSENSUS_BOOST_REASON,
    PASS_REASON,
    EMPTY_REASON,
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "ord" + "er",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sign" + "ing",
    "muta" + "tion",
    "b" + "uy",
    "se" + "ll",
    "tr" + "ade",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class StrategyCandidateSourceDisagreementAdjustedEvV2Config(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_SOURCE_DISAGREEMENT_ADJUSTED_EV_V2_CONFIG_VERSION
    )
    watch_adjusted_ev_floor: Decimal = Decimal("0.010000")
    pass_adjusted_ev_floor: Decimal = Decimal("0.030000")
    watch_source_disagreement: Decimal = Decimal("0.050000")
    block_source_disagreement: Decimal = Decimal("0.150000")
    contradiction_ev_abs_floor: Decimal = Decimal("0.010000")
    block_contradiction_count: Decimal = Decimal("2")
    disagreement_penalty_weight: Decimal = Decimal("0.250000")
    contradiction_penalty_weight: Decimal = Decimal("0.030000")
    consensus_boost_weight: Decimal = Decimal("0.010000")
    min_consensus_ratio: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyCandidateSourceDisagreementAdjustedEvV2Config,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_CANDIDATE_SOURCE_DISAGREEMENT_ADJUSTED_EV_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_adjusted_ev_floor",
            "pass_adjusted_ev_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_source_disagreement",
            "block_source_disagreement",
            "contradiction_ev_abs_floor",
            "disagreement_penalty_weight",
            "contradiction_penalty_weight",
            "consensus_boost_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "block_contradiction_count",
            _require_positive_count_decimal(
                "block_contradiction_count",
                self.block_contradiction_count,
            ),
        )
        object.__setattr__(
            self,
            "min_consensus_ratio",
            _require_ratio_decimal("min_consensus_ratio", self.min_consensus_ratio),
        )
        if self.watch_adjusted_ev_floor > self.pass_adjusted_ev_floor:
            raise ValueError(
                "watch_adjusted_ev_floor must not exceed pass_adjusted_ev_floor",
            )
        if self.block_source_disagreement < self.watch_source_disagreement:
            raise ValueError(
                "block_source_disagreement must be at least watch_source_disagreement",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateSourceDisagreementAdjustedEvV2Candidate(_FinalPublicDataclass):
    candidate_reference: str
    market_reference: str
    evaluated_at: datetime
    source_expected_values: tuple[Decimal, ...]
    source_confidence_scores: tuple[Decimal, ...]
    reason_codes: tuple[str, ...] = ("candidate_input",)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyCandidateSourceDisagreementAdjustedEvV2Candidate,
            "candidate",
        )
        _require_public_string("candidate_reference", self.candidate_reference)
        _require_public_string("market_reference", self.market_reference)
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        object.__setattr__(
            self,
            "source_expected_values",
            _require_decimal_tuple(
                "source_expected_values",
                self.source_expected_values,
                minimum_length=2,
                ratio=False,
            ),
        )
        object.__setattr__(
            self,
            "source_confidence_scores",
            _require_decimal_tuple(
                "source_confidence_scores",
                self.source_confidence_scores,
                minimum_length=2,
                ratio=True,
            ),
        )
        if len(self.source_expected_values) != len(self.source_confidence_scores):
            raise ValueError("source_confidence_scores must match source_expected_values")
        if _sum_decimal(self.source_confidence_scores) <= ZERO:
            raise ValueError("source_confidence_scores must include positive confidence")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyCandidateSourceDisagreementAdjustedEvV2Row(_FinalPublicDataclass):
    candidate_reference: str
    market_reference: str
    evaluated_at: datetime
    source_expected_values: tuple[Decimal, ...]
    source_confidence_scores: tuple[Decimal, ...]
    source_count: Decimal
    weighted_source_expected_value: Decimal
    source_disagreement: Decimal
    contradiction_count: Decimal
    consensus_source_ratio: Decimal
    consensus_boost: Decimal
    disagreement_penalty: Decimal
    contradiction_penalty: Decimal
    adjusted_expected_value: Decimal
    ev_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyCandidateSourceDisagreementAdjustedEvV2Row,
            "row",
        )
        _require_public_string("candidate_reference", self.candidate_reference)
        _require_public_string("market_reference", self.market_reference)
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        object.__setattr__(
            self,
            "source_expected_values",
            _require_decimal_tuple(
                "source_expected_values",
                self.source_expected_values,
                minimum_length=2,
                ratio=False,
            ),
        )
        object.__setattr__(
            self,
            "source_confidence_scores",
            _require_decimal_tuple(
                "source_confidence_scores",
                self.source_confidence_scores,
                minimum_length=2,
                ratio=True,
            ),
        )
        for field_name in (
            "source_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "weighted_source_expected_value",
            "adjusted_expected_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_disagreement",
            "consensus_source_ratio",
            "consensus_boost",
            "disagreement_penalty",
            "contradiction_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("ev_status", self.ev_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyCandidateSourceDisagreementAdjustedEvV2Report(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_adjusted_expected_value: Decimal
    max_adjusted_expected_value: Decimal
    min_adjusted_expected_value: Decimal
    max_source_disagreement: Decimal
    total_contradiction_count: Decimal
    digest_status: str
    rows: tuple[StrategyCandidateSourceDisagreementAdjustedEvV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyCandidateSourceDisagreementAdjustedEvV2Report,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_CANDIDATE_SOURCE_DISAGREEMENT_ADJUSTED_EV_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "total_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_adjusted_expected_value",
            "max_adjusted_expected_value",
            "min_adjusted_expected_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_disagreement",
            _require_nonnegative_decimal(
                "max_source_disagreement",
                self.max_source_disagreement,
            ),
        )
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("report", self)
        _validate_report(self)


def build_strategy_candidate_source_disagreement_adjusted_ev_v2(
    candidates: Iterable[object],
    *,
    config: StrategyCandidateSourceDisagreementAdjustedEvV2Config,
    generated_at: datetime,
) -> StrategyCandidateSourceDisagreementAdjustedEvV2Report:
    if type(config) is not StrategyCandidateSourceDisagreementAdjustedEvV2Config:
        raise ValueError(
            "config must be StrategyCandidateSourceDisagreementAdjustedEvV2Config",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    source_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    candidate,
                    config=config,
                    generated_at=generated_at,
                )
                for candidate in source_candidates
            ),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "candidate_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "blocked_count": _status_count(rows, "blocked"),
        "average_adjusted_expected_value": _average_adjusted_expected_value(rows),
        "max_adjusted_expected_value": _max_adjusted_expected_value(rows),
        "min_adjusted_expected_value": _min_adjusted_expected_value(rows),
        "max_source_disagreement": _max_source_disagreement(rows),
        "total_contradiction_count": _sum_decimal(
            (row.contradiction_count for row in rows),
        ).quantize(COUNT_QUANT),
        "digest_status": _digest_status(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, config=config),
        "derived_validation_digest": "",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = (
        derived_validation_digest_for_strategy_candidate_source_disagreement_adjusted_ev_v2(
            values,
        )
    )
    return StrategyCandidateSourceDisagreementAdjustedEvV2Report(**values)


def strategy_candidate_source_disagreement_adjusted_ev_v2_payload(
    report: StrategyCandidateSourceDisagreementAdjustedEvV2Report,
) -> dict[str, object]:
    if type(report) is not StrategyCandidateSourceDisagreementAdjustedEvV2Report:
        raise ValueError(
            "report must be StrategyCandidateSourceDisagreementAdjustedEvV2Report",
        )
    _validate_report(report)
    _require_hard_flags("report", report)
    payload = _payload_value(asdict(report))
    _reject_unsafe_public_payload("report payload", payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def derived_validation_digest_for_strategy_candidate_source_disagreement_adjusted_ev_v2(
    values: dict[str, object],
) -> str:
    if type(values) is not dict:
        raise ValueError("derived validation values must be a dict")
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _row_from_candidate(
    candidate: StrategyCandidateSourceDisagreementAdjustedEvV2Candidate,
    *,
    config: StrategyCandidateSourceDisagreementAdjustedEvV2Config,
    generated_at: datetime,
) -> StrategyCandidateSourceDisagreementAdjustedEvV2Row:
    if candidate.evaluated_at > generated_at:
        raise ValueError("evaluated_at must not be after generated_at")
    weighted_source_expected_value = _weighted_average(
        candidate.source_expected_values,
        candidate.source_confidence_scores,
    )
    source_disagreement = _source_disagreement(candidate.source_expected_values)
    contradiction_count = _contradiction_count(
        candidate.source_expected_values,
        config.contradiction_ev_abs_floor,
    )
    consensus_source_ratio = _consensus_source_ratio(
        candidate.source_expected_values,
        config.contradiction_ev_abs_floor,
    )
    consensus_boost = _consensus_boost(
        consensus_source_ratio=consensus_source_ratio,
        contradiction_count=contradiction_count,
        config=config,
    )
    disagreement_penalty = _multiply_decimal(
        source_disagreement,
        config.disagreement_penalty_weight,
    )
    contradiction_penalty = _divide_decimal(
        _multiply_decimal(contradiction_count, config.contradiction_penalty_weight),
        _count_decimal(len(candidate.source_expected_values)),
    )
    adjusted_expected_value = _add_decimal(
        weighted_source_expected_value,
        consensus_boost,
        -disagreement_penalty,
        -contradiction_penalty,
    )
    ev_status = _row_status(
        adjusted_expected_value=adjusted_expected_value,
        source_disagreement=source_disagreement,
        contradiction_count=contradiction_count,
        config=config,
    )
    return StrategyCandidateSourceDisagreementAdjustedEvV2Row(
        candidate_reference=candidate.candidate_reference,
        market_reference=candidate.market_reference,
        evaluated_at=candidate.evaluated_at,
        source_expected_values=candidate.source_expected_values,
        source_confidence_scores=candidate.source_confidence_scores,
        source_count=_count_decimal(len(candidate.source_expected_values)),
        weighted_source_expected_value=weighted_source_expected_value,
        source_disagreement=source_disagreement,
        contradiction_count=contradiction_count,
        consensus_source_ratio=consensus_source_ratio,
        consensus_boost=consensus_boost,
        disagreement_penalty=disagreement_penalty,
        contradiction_penalty=contradiction_penalty,
        adjusted_expected_value=adjusted_expected_value,
        ev_status=ev_status,
        reason_codes=_row_reason_codes(
            candidate.reason_codes,
            adjusted_expected_value=adjusted_expected_value,
            source_disagreement=source_disagreement,
            contradiction_count=contradiction_count,
            consensus_boost=consensus_boost,
            ev_status=ev_status,
            config=config,
        ),
    )


def _row_status(
    *,
    adjusted_expected_value: Decimal,
    source_disagreement: Decimal,
    contradiction_count: Decimal,
    config: StrategyCandidateSourceDisagreementAdjustedEvV2Config,
) -> str:
    if (
        source_disagreement >= config.block_source_disagreement
        or contradiction_count >= config.block_contradiction_count
    ):
        return "blocked"
    if (
        adjusted_expected_value < config.pass_adjusted_ev_floor
        or source_disagreement >= config.watch_source_disagreement
        or contradiction_count > ZERO
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    existing_reason_codes: tuple[str, ...],
    *,
    adjusted_expected_value: Decimal,
    source_disagreement: Decimal,
    contradiction_count: Decimal,
    consensus_boost: Decimal,
    ev_status: str,
    config: StrategyCandidateSourceDisagreementAdjustedEvV2Config,
) -> tuple[str, ...]:
    reason_codes = list(existing_reason_codes)
    if source_disagreement >= config.block_source_disagreement:
        reason_codes.append(DISAGREEMENT_BLOCK_REASON)
    elif source_disagreement >= config.watch_source_disagreement:
        reason_codes.append(DISAGREEMENT_WATCH_REASON)
    if contradiction_count >= config.block_contradiction_count:
        reason_codes.append(CONTRADICTION_BLOCK_REASON)
    elif contradiction_count > ZERO:
        reason_codes.append(CONTRADICTION_PENALTY_REASON)
    if adjusted_expected_value < config.watch_adjusted_ev_floor:
        reason_codes.append(BELOW_WATCH_REASON)
    elif adjusted_expected_value < config.pass_adjusted_ev_floor:
        reason_codes.append(BELOW_PASS_REASON)
    if consensus_boost > ZERO:
        reason_codes.append(CONSENSUS_BOOST_REASON)
    if ev_status == "pass":
        reason_codes.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[StrategyCandidateSourceDisagreementAdjustedEvV2Row, ...],
    *,
    config: StrategyCandidateSourceDisagreementAdjustedEvV2Config,
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes = {reason for row in rows for reason in row.reason_codes}
    total_contradiction_count = _sum_decimal(row.contradiction_count for row in rows)
    if total_contradiction_count >= config.block_contradiction_count:
        reason_codes.add(CONTRADICTION_BLOCK_REASON)
    return tuple(reason for reason in REPORT_REASON_PRIORITY if reason in reason_codes)


def _normalize_candidates(
    value: Iterable[object],
) -> tuple[StrategyCandidateSourceDisagreementAdjustedEvV2Candidate, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        candidates = tuple(value)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    for candidate in candidates:
        if type(candidate) is not StrategyCandidateSourceDisagreementAdjustedEvV2Candidate:
            raise ValueError(
                "candidates must contain "
                "StrategyCandidateSourceDisagreementAdjustedEvV2Candidate",
            )
        _require_hard_flags("candidate", candidate)
    references = tuple(candidate.candidate_reference for candidate in candidates)
    if len(set(references)) != len(references):
        raise ValueError("duplicate candidate_reference")
    return candidates


def _normalize_rows(
    value: object,
) -> tuple[StrategyCandidateSourceDisagreementAdjustedEvV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not StrategyCandidateSourceDisagreementAdjustedEvV2Row:
            raise ValueError(
                "rows must contain StrategyCandidateSourceDisagreementAdjustedEvV2Row",
            )
        _require_hard_flags("row", row)
    return value


def _row_sort_key(
    row: StrategyCandidateSourceDisagreementAdjustedEvV2Row,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        STATUS_PRIORITY[row.ev_status],
        row.adjusted_expected_value,
        -row.source_disagreement,
        row.candidate_reference,
        row.market_reference,
    )


def _weighted_average(
    values: tuple[Decimal, ...],
    weights: tuple[Decimal, ...],
) -> Decimal:
    numerator = _sum_decimal(
        _multiply_decimal(value, weight) for value, weight in zip(values, weights)
    )
    denominator = _sum_decimal(weights)
    return _divide_decimal(numerator, denominator)


def _source_disagreement(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(max(values) - min(values))


def _contradiction_count(values: tuple[Decimal, ...], floor: Decimal) -> Decimal:
    positive_count = sum(1 for value in values if value >= floor)
    negative_count = sum(1 for value in values if value <= -floor)
    if positive_count == 0 or negative_count == 0:
        return ZERO.quantize(COUNT_QUANT)
    return _count_decimal(min(positive_count, negative_count))


def _consensus_source_ratio(values: tuple[Decimal, ...], floor: Decimal) -> Decimal:
    positive_count = sum(1 for value in values if value >= floor)
    negative_count = sum(1 for value in values if value <= -floor)
    neutral_count = len(values) - positive_count - negative_count
    dominant_count = max(positive_count, negative_count, neutral_count)
    return _divide_decimal(_count_decimal(dominant_count), _count_decimal(len(values)))


def _consensus_boost(
    *,
    consensus_source_ratio: Decimal,
    contradiction_count: Decimal,
    config: StrategyCandidateSourceDisagreementAdjustedEvV2Config,
) -> Decimal:
    if contradiction_count == ZERO and consensus_source_ratio >= config.min_consensus_ratio:
        return config.consensus_boost_weight
    return ZERO


def _status_count(
    rows: tuple[StrategyCandidateSourceDisagreementAdjustedEvV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.ev_status == status))


def _average_adjusted_expected_value(
    rows: tuple[StrategyCandidateSourceDisagreementAdjustedEvV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _divide_decimal(
        _sum_decimal(row.adjusted_expected_value for row in rows),
        _count_decimal(len(rows)),
    )


def _max_adjusted_expected_value(
    rows: tuple[StrategyCandidateSourceDisagreementAdjustedEvV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.adjusted_expected_value for row in rows)


def _min_adjusted_expected_value(
    rows: tuple[StrategyCandidateSourceDisagreementAdjustedEvV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.adjusted_expected_value for row in rows)


def _max_source_disagreement(
    rows: tuple[StrategyCandidateSourceDisagreementAdjustedEvV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.source_disagreement for row in rows)


def _digest_status(
    rows: tuple[StrategyCandidateSourceDisagreementAdjustedEvV2Row, ...],
) -> str:
    if any(row.ev_status == "blocked" for row in rows):
        return "blocked"
    if any(row.ev_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _validate_row(row: StrategyCandidateSourceDisagreementAdjustedEvV2Row) -> None:
    if len(row.source_expected_values) != len(row.source_confidence_scores):
        raise ValueError("source_confidence_scores must match source_expected_values")
    if row.source_count != _count_decimal(len(row.source_expected_values)):
        raise ValueError("source_count must match source_expected_values")
    if row.weighted_source_expected_value != _weighted_average(
        row.source_expected_values,
        row.source_confidence_scores,
    ):
        raise ValueError("weighted_source_expected_value must match source inputs")
    if row.source_disagreement != _source_disagreement(row.source_expected_values):
        raise ValueError("source_disagreement must match source_expected_values")
    if row.adjusted_expected_value != _add_decimal(
        row.weighted_source_expected_value,
        row.consensus_boost,
        -row.disagreement_penalty,
        -row.contradiction_penalty,
    ):
        raise ValueError("adjusted_expected_value must match row penalties")


def _validate_report(
    report: StrategyCandidateSourceDisagreementAdjustedEvV2Report,
) -> None:
    rows = report.rows
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    if report.candidate_count != _count_decimal(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if (
        report.pass_count + report.watch_count + report.blocked_count
        != report.candidate_count
    ):
        raise ValueError("status counts must sum to candidate_count")
    if report.average_adjusted_expected_value != _average_adjusted_expected_value(rows):
        raise ValueError("average_adjusted_expected_value must match rows")
    if report.max_adjusted_expected_value != _max_adjusted_expected_value(rows):
        raise ValueError("max_adjusted_expected_value must match rows")
    if report.min_adjusted_expected_value != _min_adjusted_expected_value(rows):
        raise ValueError("min_adjusted_expected_value must match rows")
    if report.max_source_disagreement != _max_source_disagreement(rows):
        raise ValueError("max_source_disagreement must match rows")
    if report.total_contradiction_count != _sum_decimal(
        (row.contradiction_count for row in rows),
    ).quantize(COUNT_QUANT):
        raise ValueError("total_contradiction_count must match rows")
    if report.digest_status != _digest_status(rows):
        raise ValueError("digest_status must match rows")
    if report.derived_validation_digest != (
        derived_validation_digest_for_strategy_candidate_source_disagreement_adjusted_ev_v2(
            asdict(report),
        )
    ):
        raise ValueError("derived_validation_digest must match report fields")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical public text")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in EV_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    reason_codes: list[str] = []
    seen: set[str] = set()
    for item in value:
        normalized = _require_public_string(field_name, item)
        if normalized not in seen:
            reason_codes.append(normalized)
            seen.add(normalized)
    return tuple(reason_codes)


def _require_decimal_tuple(
    field_name: str,
    value: object,
    *,
    minimum_length: int,
    ratio: bool,
) -> tuple[Decimal, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if len(value) < minimum_length:
        raise ValueError(f"{field_name} must contain at least {minimum_length} values")
    if ratio:
        return tuple(_require_ratio_decimal(field_name, item) for item in value)
    return tuple(_require_signed_decimal(field_name, item) for item in value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANT)


def _require_signed_decimal(field_name: str, value: object) -> Decimal:
    return _require_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than 1.000000")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")
    _reject_unsafe_public_payload(field_name, value)


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_text("payload key", key)
            result[key] = _payload_value(item)
        return result
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        if type(value) is str:
            _reject_unsafe_public_text("payload value", value)
        return value
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (float, int):
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(SCORE_QUANT)


def _add_decimal(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(SCORE_QUANT)


def _multiply_decimal(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        result = ONE
        for value in values:
            result *= value
        return result.quantize(SCORE_QUANT)


def _divide_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        raise ValueError("division denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(SCORE_QUANT)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANT)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_SOURCE_DISAGREEMENT_ADJUSTED_EV_V2_CONFIG_VERSION",
    "StrategyCandidateSourceDisagreementAdjustedEvV2Candidate",
    "StrategyCandidateSourceDisagreementAdjustedEvV2Config",
    "StrategyCandidateSourceDisagreementAdjustedEvV2Report",
    "StrategyCandidateSourceDisagreementAdjustedEvV2Row",
    "build_strategy_candidate_source_disagreement_adjusted_ev_v2",
    "derived_validation_digest_for_strategy_candidate_source_disagreement_adjusted_ev_v2",
    "strategy_candidate_source_disagreement_adjusted_ev_v2_payload",
)
