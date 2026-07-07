"""Paper-only base-rate anchoring score for candidate probability research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_CANDIDATE_DECISION_BASE_RATE_ANCHOR_SCORE_CONFIG_VERSION = (
    "candidate-decision-base-rate-anchor-score-v1"
)
BOUNDARY_STATEMENT = (
    "Paper-only base-rate grounding research support; operations are out of scope."
)

PUBLIC_DATACLASS_NAMES = frozenset(
    (
        "CandidateDecisionBaseRateAnchorScoreConfig",
        "CandidateDecisionBaseRateAnchorFact",
        "CandidateDecisionBaseRateAnchorScoreRow",
        "CandidateDecisionBaseRateAnchorScoreReport",
    ),
)
DECIMAL_CONTEXT = Context(prec=64)
SCORE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
SCORE_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

ROW_REASON_CODES = frozenset(
    (
        "base_rate_anchor_pass",
        "base_rate_anchor_watch_score",
        "base_rate_anchor_blocked_score",
        "base_rate_sample_size_below_floor",
        "base_rate_recency_below_floor",
        "base_rate_similarity_below_floor",
        "base_rate_dispersion_above_ceiling",
        "specialist_calibration_below_floor",
        "candidate_deviation_justification_below_floor",
        "candidate_forecast_materially_deviates",
        "candidate_forecast_close_to_base_rate",
        "candidate_deviation_justified",
        "candidate_forecast_deviation_unjustified",
    ),
)
REPORT_REASON_CODES = frozenset(
    (
        "base_rate_anchor_empty",
        "base_rate_anchor_report_pass",
        "base_rate_anchor_report_watch",
        "base_rate_anchor_report_blocked",
        *ROW_REASON_CODES,
    ),
)
UNSAFE_PUBLIC_TERMS = frozenset(
    (
        "".join(("li", "ve")),
        "".join(("au", "th")),
        "".join(("wall", "et")),
        "".join(("acc", "ount")),
        "".join(("or", "der")),
        "".join(("recom", "mend")),
        "".join(("siz", "ing")),
        "".join(("pos", "ition")),
        "".join(("net", "work")),
        "".join(("data", "base")),
        "".join(("per", "sist")),
        "".join(("sign", "ing")),
        "".join(("muta", "tion")),
        "".join(("private", "_", "key")),
        "".join(("se", "cret")),
        "".join(("to", "ken")),
        "".join(("b", "uy")),
        "".join(("s", "ell")),
        "".join(("tr", "ade")),
        "".join(("trad", "ing")),
        "".join(("sou", "rce")),
        "".join(("ac", "tion")),
        "".join(("exec", "ute")),
        "".join(("execu", "ted")),
        "".join(("execu", "tion")),
        "".join(("mark", "et")),
        "".join(("sl", "ug")),
        "".join(("ques", "tion")),
        "".join(("u", "rl")),
        "".join(("ht", "tp")),
        "www.",
    ),
)
REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "score_status",
        "row_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "average_base_rate_anchor_score",
        "max_forecast_base_rate_deviation",
        "rows",
        "fact_config_versions",
        "reason_codes",
        "derived_validation_digest",
        "boundary_statement",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "rank",
        "redacted_candidate_id",
        "redacted_team_id",
        "redacted_domain_id",
        "observed_at",
        "candidate_forecast_probability",
        "base_rate_probability",
        "forecast_base_rate_deviation",
        "base_rate_sample_size",
        "sample_size_score",
        "base_rate_recency_score",
        "base_rate_similarity_score",
        "base_rate_dispersion_score",
        "dispersion_grounding_score",
        "specialist_calibration_score",
        "deviation_justification_score",
        "base_rate_anchor_score",
        "score_status",
        "reason_codes",
        "redacted_refs",
        "fact_config_version",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__module__ != __name__ or cls.__name__ not in PUBLIC_DATACLASS_NAMES:
            raise TypeError("subclassing is not allowed")


@dataclass(frozen=True)
class CandidateDecisionBaseRateAnchorScoreConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_CANDIDATE_DECISION_BASE_RATE_ANCHOR_SCORE_CONFIG_VERSION
    minimum_base_rate_sample_size: Decimal = Decimal("30.000000")
    minimum_recency_score: Decimal = Decimal("0.600000")
    minimum_similarity_score: Decimal = Decimal("0.650000")
    maximum_dispersion_score: Decimal = Decimal("0.400000")
    minimum_specialist_calibration_score: Decimal = Decimal("0.650000")
    minimum_deviation_justification_score: Decimal = Decimal("0.600000")
    material_deviation_floor: Decimal = Decimal("0.050000")
    sample_size_weight: Decimal = Decimal("0.200000")
    recency_weight: Decimal = Decimal("0.150000")
    similarity_weight: Decimal = Decimal("0.200000")
    dispersion_weight: Decimal = Decimal("0.150000")
    specialist_calibration_weight: Decimal = Decimal("0.150000")
    deviation_justification_weight: Decimal = Decimal("0.150000")
    pass_score_floor: Decimal = Decimal("0.750000")
    watch_score_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            CandidateDecisionBaseRateAnchorScoreConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "minimum_base_rate_sample_size",
            _require_positive_decimal(
                "minimum_base_rate_sample_size",
                self.minimum_base_rate_sample_size,
            ),
        )
        for field_name in (
            "minimum_recency_score",
            "minimum_similarity_score",
            "maximum_dispersion_score",
            "minimum_specialist_calibration_score",
            "minimum_deviation_justification_score",
            "material_deviation_floor",
            "sample_size_weight",
            "recency_weight",
            "similarity_weight",
            "dispersion_weight",
            "specialist_calibration_weight",
            "deviation_justification_weight",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class CandidateDecisionBaseRateAnchorFact(_FinalPublicDataclass):
    redacted_candidate_id: str
    redacted_team_id: str
    redacted_domain_id: str
    observed_at: datetime
    candidate_forecast_probability: Decimal
    base_rate_probability: Decimal
    base_rate_sample_size: Decimal
    base_rate_recency_score: Decimal
    base_rate_similarity_score: Decimal
    base_rate_dispersion_score: Decimal
    specialist_calibration_score: Decimal
    deviation_justification_score: Decimal
    base_rate_ref: str
    specialist_calibration_ref: str
    deviation_justification_ref: str
    fact_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionBaseRateAnchorFact, "fact")
        for field_name in (
            "redacted_candidate_id",
            "redacted_team_id",
            "redacted_domain_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_redacted_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "fact_config_version",
            _require_public_string("fact_config_version", self.fact_config_version),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "base_rate_sample_size",
            _require_nonnegative_decimal("base_rate_sample_size", self.base_rate_sample_size),
        )
        for field_name in (
            "candidate_forecast_probability",
            "base_rate_probability",
            "base_rate_recency_score",
            "base_rate_similarity_score",
            "base_rate_dispersion_score",
            "specialist_calibration_score",
            "deviation_justification_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "base_rate_ref",
            "specialist_calibration_ref",
            "deviation_justification_ref",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_redacted_ref(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("fact", self)
        _reject_unsafe_public_payload("fact", _payload_value(self))


@dataclass(frozen=True)
class CandidateDecisionBaseRateAnchorScoreRow(_FinalPublicDataclass):
    rank: Decimal
    redacted_candidate_id: str
    redacted_team_id: str
    redacted_domain_id: str
    observed_at: datetime
    candidate_forecast_probability: Decimal
    base_rate_probability: Decimal
    forecast_base_rate_deviation: Decimal
    base_rate_sample_size: Decimal
    sample_size_score: Decimal
    base_rate_recency_score: Decimal
    base_rate_similarity_score: Decimal
    base_rate_dispersion_score: Decimal
    dispersion_grounding_score: Decimal
    specialist_calibration_score: Decimal
    deviation_justification_score: Decimal
    base_rate_anchor_score: Decimal
    score_status: str
    reason_codes: tuple[str, ...]
    redacted_refs: tuple[str, ...]
    fact_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionBaseRateAnchorScoreRow, "row")
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        for field_name in (
            "redacted_candidate_id",
            "redacted_team_id",
            "redacted_domain_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_redacted_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "fact_config_version",
            _require_public_string("fact_config_version", self.fact_config_version),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "base_rate_sample_size",
            _require_nonnegative_decimal("base_rate_sample_size", self.base_rate_sample_size),
        )
        for field_name in (
            "candidate_forecast_probability",
            "base_rate_probability",
            "forecast_base_rate_deviation",
            "sample_size_score",
            "base_rate_recency_score",
            "base_rate_similarity_score",
            "base_rate_dispersion_score",
            "dispersion_grounding_score",
            "specialist_calibration_score",
            "deviation_justification_score",
            "base_rate_anchor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("score_status", self.score_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        object.__setattr__(
            self,
            "redacted_refs",
            _require_redacted_refs("redacted_refs", self.redacted_refs),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class CandidateDecisionBaseRateAnchorScoreReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    score_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_base_rate_anchor_score: Decimal
    max_forecast_base_rate_deviation: Decimal
    rows: tuple[CandidateDecisionBaseRateAnchorScoreRow, ...]
    fact_config_versions: tuple[tuple[str, str, str, str], ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionBaseRateAnchorScoreReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_status("score_status", self.score_status)
        for field_name in ("row_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_base_rate_anchor_score",
            "max_forecast_base_rate_deviation",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "fact_config_versions",
            _require_fact_config_versions(self.fact_config_versions),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match paper-only scope")
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _validate_report(self)
        _require_matching_digest(_payload_value(self))


def build_candidate_decision_base_rate_anchor_score(
    facts: Iterable[CandidateDecisionBaseRateAnchorFact],
    *,
    config: CandidateDecisionBaseRateAnchorScoreConfig | None = None,
    generated_at: datetime,
) -> CandidateDecisionBaseRateAnchorScoreReport:
    cfg = config or CandidateDecisionBaseRateAnchorScoreConfig()
    if type(cfg) is not CandidateDecisionBaseRateAnchorScoreConfig:
        raise ValueError(
            "config must be exactly CandidateDecisionBaseRateAnchorScoreConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_facts(facts)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        _row_for_fact(rank=index, fact=item, config=cfg)
        for index, item in enumerate(_sorted_facts(normalized), start=1)
    )
    status = _report_status(rows)
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "score_status": status,
        "row_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "blocked_count": _status_count(rows, STATUS_BLOCK),
        "average_base_rate_anchor_score": _average(
            row.base_rate_anchor_score for row in rows
        ),
        "max_forecast_base_rate_deviation": max(
            (row.forecast_base_rate_deviation for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "fact_config_versions": tuple(
            sorted(
                (
                    item.redacted_candidate_id,
                    item.redacted_team_id,
                    item.redacted_domain_id,
                    item.fact_config_version,
                )
                for item in normalized
            ),
        ),
        "reason_codes": _report_reason_codes(rows, status),
        "boundary_statement": BOUNDARY_STATEMENT,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return CandidateDecisionBaseRateAnchorScoreReport(**values)


def candidate_decision_base_rate_anchor_score_payload(
    report: CandidateDecisionBaseRateAnchorScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionBaseRateAnchorScoreReport:
        raise ValueError("report must be exactly CandidateDecisionBaseRateAnchorScoreReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    return payload


def validate_candidate_decision_base_rate_anchor_score_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    _report_from_payload(payload)
    return True


def _row_for_fact(
    *,
    rank: int,
    fact: CandidateDecisionBaseRateAnchorFact,
    config: CandidateDecisionBaseRateAnchorScoreConfig,
) -> CandidateDecisionBaseRateAnchorScoreRow:
    sample_score = _sample_size_score(fact.base_rate_sample_size, config)
    dispersion_grounding = _subtract_ratio(ONE, fact.base_rate_dispersion_score)
    deviation = _forecast_base_rate_deviation(
        fact.candidate_forecast_probability,
        fact.base_rate_probability,
    )
    anchor_score = _base_rate_anchor_score(
        sample_size_score=sample_score,
        recency_score=fact.base_rate_recency_score,
        similarity_score=fact.base_rate_similarity_score,
        dispersion_grounding_score=dispersion_grounding,
        specialist_calibration_score=fact.specialist_calibration_score,
        deviation_justification_score=fact.deviation_justification_score,
        config=config,
    )
    status = _row_status(anchor_score, config)
    return CandidateDecisionBaseRateAnchorScoreRow(
        rank=_count_decimal(rank),
        redacted_candidate_id=fact.redacted_candidate_id,
        redacted_team_id=fact.redacted_team_id,
        redacted_domain_id=fact.redacted_domain_id,
        observed_at=fact.observed_at,
        candidate_forecast_probability=fact.candidate_forecast_probability,
        base_rate_probability=fact.base_rate_probability,
        forecast_base_rate_deviation=deviation,
        base_rate_sample_size=fact.base_rate_sample_size,
        sample_size_score=sample_score,
        base_rate_recency_score=fact.base_rate_recency_score,
        base_rate_similarity_score=fact.base_rate_similarity_score,
        base_rate_dispersion_score=fact.base_rate_dispersion_score,
        dispersion_grounding_score=dispersion_grounding,
        specialist_calibration_score=fact.specialist_calibration_score,
        deviation_justification_score=fact.deviation_justification_score,
        base_rate_anchor_score=anchor_score,
        score_status=status,
        reason_codes=_row_reason_codes(
            fact=fact,
            sample_size_score=sample_score,
            forecast_base_rate_deviation=deviation,
            base_rate_anchor_score=anchor_score,
            config=config,
        ),
        redacted_refs=(
            fact.base_rate_ref,
            fact.specialist_calibration_ref,
            fact.deviation_justification_ref,
        ),
        fact_config_version=fact.fact_config_version,
    )


def _sample_size_score(
    base_rate_sample_size: Decimal,
    config: CandidateDecisionBaseRateAnchorScoreConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(base_rate_sample_size / config.minimum_base_rate_sample_size)


def _forecast_base_rate_deviation(
    candidate_forecast_probability: Decimal,
    base_rate_probability: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(abs(candidate_forecast_probability - base_rate_probability))


def _base_rate_anchor_score(
    *,
    sample_size_score: Decimal,
    recency_score: Decimal,
    similarity_score: Decimal,
    dispersion_grounding_score: Decimal,
    specialist_calibration_score: Decimal,
    deviation_justification_score: Decimal,
    config: CandidateDecisionBaseRateAnchorScoreConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sample_size_score * config.sample_size_weight
            + recency_score * config.recency_weight
            + similarity_score * config.similarity_weight
            + dispersion_grounding_score * config.dispersion_weight
            + specialist_calibration_score * config.specialist_calibration_weight
            + deviation_justification_score * config.deviation_justification_weight,
        )


def _row_status(
    base_rate_anchor_score: Decimal,
    config: CandidateDecisionBaseRateAnchorScoreConfig,
) -> str:
    if base_rate_anchor_score < config.watch_score_floor:
        return STATUS_BLOCK
    if base_rate_anchor_score < config.pass_score_floor:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    fact: CandidateDecisionBaseRateAnchorFact,
    sample_size_score: Decimal,
    forecast_base_rate_deviation: Decimal,
    base_rate_anchor_score: Decimal,
    config: CandidateDecisionBaseRateAnchorScoreConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if base_rate_anchor_score < config.watch_score_floor:
        codes.append("base_rate_anchor_blocked_score")
    elif base_rate_anchor_score < config.pass_score_floor:
        codes.append("base_rate_anchor_watch_score")
    else:
        codes.append("base_rate_anchor_pass")
    if sample_size_score < ONE:
        codes.append("base_rate_sample_size_below_floor")
    if fact.base_rate_recency_score < config.minimum_recency_score:
        codes.append("base_rate_recency_below_floor")
    if fact.base_rate_similarity_score < config.minimum_similarity_score:
        codes.append("base_rate_similarity_below_floor")
    if fact.base_rate_dispersion_score > config.maximum_dispersion_score:
        codes.append("base_rate_dispersion_above_ceiling")
    if fact.specialist_calibration_score < config.minimum_specialist_calibration_score:
        codes.append("specialist_calibration_below_floor")
    if fact.deviation_justification_score < config.minimum_deviation_justification_score:
        codes.append("candidate_deviation_justification_below_floor")
    if forecast_base_rate_deviation >= config.material_deviation_floor:
        codes.append("candidate_forecast_materially_deviates")
        if fact.deviation_justification_score >= config.minimum_deviation_justification_score:
            codes.append("candidate_deviation_justified")
        else:
            codes.append("candidate_forecast_deviation_unjustified")
    else:
        codes.append("candidate_forecast_close_to_base_rate")
    return tuple(codes)


def _normalize_facts(
    facts: Iterable[CandidateDecisionBaseRateAnchorFact],
) -> tuple[CandidateDecisionBaseRateAnchorFact, ...]:
    if isinstance(facts, (str, bytes)):
        raise ValueError("facts must be an iterable")
    try:
        normalized = tuple(facts)
    except TypeError as exc:
        raise ValueError("facts must be an iterable") from exc
    seen: set[tuple[str, str, str]] = set()
    for item in normalized:
        if type(item) is not CandidateDecisionBaseRateAnchorFact:
            raise ValueError("facts must contain CandidateDecisionBaseRateAnchorFact")
        _require_hard_flags("fact", item)
        key = (
            item.redacted_candidate_id,
            item.redacted_team_id,
            item.redacted_domain_id,
        )
        if key in seen:
            raise ValueError("duplicate candidate/team/domain fact")
        seen.add(key)
    return normalized


def _sorted_facts(
    facts: tuple[CandidateDecisionBaseRateAnchorFact, ...],
) -> tuple[CandidateDecisionBaseRateAnchorFact, ...]:
    return tuple(
        sorted(
            facts,
            key=lambda item: (
                item.redacted_candidate_id,
                item.redacted_team_id,
                item.redacted_domain_id,
                item.observed_at.isoformat(),
            ),
        ),
    )


def _require_rows(
    rows: object,
) -> tuple[CandidateDecisionBaseRateAnchorScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not CandidateDecisionBaseRateAnchorScoreRow:
            raise ValueError("rows must contain CandidateDecisionBaseRateAnchorScoreRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=lambda row: row.rank)):
        raise ValueError("rows must be sorted by rank")
    expected_ranks = tuple(_count_decimal(index) for index in range(1, len(normalized) + 1))
    if tuple(row.rank for row in normalized) != expected_ranks:
        raise ValueError("rows must use contiguous ranks")
    return normalized


def _require_fact_config_versions(values: object) -> tuple[tuple[str, str, str, str], ...]:
    if type(values) is not tuple:
        raise ValueError("fact_config_versions must be a tuple")
    normalized: list[tuple[str, str, str, str]] = []
    for value in values:
        if type(value) is not tuple or len(value) != 4:
            raise ValueError("fact_config_versions entries must be string quartets")
        redacted_candidate_id, redacted_team_id, redacted_domain_id, fact_config_version = value
        normalized.append(
            (
                _require_redacted_identifier(
                    "fact_config_versions",
                    redacted_candidate_id,
                ),
                _require_redacted_identifier("fact_config_versions", redacted_team_id),
                _require_redacted_identifier("fact_config_versions", redacted_domain_id),
                _require_public_string("fact_config_versions", fact_config_version),
            ),
        )
    result = tuple(normalized)
    if result != tuple(sorted(result)):
        raise ValueError("fact_config_versions must be sorted")
    return result


def _report_status(rows: tuple[CandidateDecisionBaseRateAnchorScoreRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.score_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.score_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[CandidateDecisionBaseRateAnchorScoreRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("base_rate_anchor_empty",)
    if status == STATUS_BLOCK:
        codes = ["base_rate_anchor_report_blocked"]
    else:
        codes = [f"base_rate_anchor_report_{status}"]
    for row in rows:
        for code in row.reason_codes:
            if code not in codes:
                codes.append(code)
    return tuple(codes)


def _validate_config(config: CandidateDecisionBaseRateAnchorScoreConfig) -> None:
    if config.pass_score_floor < config.watch_score_floor:
        raise ValueError("pass_score_floor must not be below watch_score_floor")
    with localcontext(DECIMAL_CONTEXT):
        weight_total = (
            config.sample_size_weight
            + config.recency_weight
            + config.similarity_weight
            + config.dispersion_weight
            + config.specialist_calibration_weight
            + config.deviation_justification_weight
        )
    if weight_total != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_report(report: CandidateDecisionBaseRateAnchorScoreReport) -> None:
    rows = report.rows
    for row in rows:
        if row.forecast_base_rate_deviation != _forecast_base_rate_deviation(
            row.candidate_forecast_probability,
            row.base_rate_probability,
        ):
            raise ValueError("forecast_base_rate_deviation must match row probabilities")
    if report.row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("blocked_count must match rows")
    if report.score_status != _report_status(rows):
        raise ValueError("score_status must match rows")
    if report.average_base_rate_anchor_score != _average(
        row.base_rate_anchor_score for row in rows
    ):
        raise ValueError("average_base_rate_anchor_score must match rows")
    if report.max_forecast_base_rate_deviation != max(
        (row.forecast_base_rate_deviation for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_forecast_base_rate_deviation must match rows")
    expected_fact_config_versions = tuple(
        sorted(
            (
                row.redacted_candidate_id,
                row.redacted_team_id,
                row.redacted_domain_id,
                row.fact_config_version,
            )
            for row in rows
        ),
    )
    if report.fact_config_versions != expected_fact_config_versions:
        raise ValueError("fact_config_versions must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.score_status):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[CandidateDecisionBaseRateAnchorScoreRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.score_status == status))


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(sum(items, ZERO) / Decimal(len(items)))


def _subtract_ratio(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(left - right)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize_decimal(value)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANTUM)


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_redacted_ref(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if not value.startswith("redacted-"):
        raise ValueError(f"{field_name} must be a redacted ref")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_redacted_identifier(field_name: str, value: str) -> str:
    value = _require_public_string(field_name, value)
    if not (value.startswith("redacted-") or "-redacted-" in value):
        raise ValueError(f"{field_name} must be a redacted identifier")
    return value


def _require_redacted_refs(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_require_redacted_ref(field_name, value) for value in values)
    if len(normalized) != 3:
        raise ValueError(f"{field_name} must contain three refs")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized))


def _require_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed_codes: frozenset[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    seen: set[str] = set()
    for value in normalized:
        _require_public_string(field_name, value)
        if value not in allowed_codes:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(value)
    return normalized


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in SCORE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if payload.get(flag) is not True:
            raise ValueError(f"payload {flag} must be True")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain dicts")
        for flag in ("paper_only", "report_only", "readonly"):
            if row.get(flag) is not True:
                raise ValueError(f"payload row {flag} must be True")


def _report_from_payload(payload: dict[str, Any]) -> CandidateDecisionBaseRateAnchorScoreReport:
    _require_payload_keys("payload", payload, REPORT_PAYLOAD_KEYS)
    return CandidateDecisionBaseRateAnchorScoreReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_public_string("config_version", payload["config_version"]),
        score_status=_payload_public_string("score_status", payload["score_status"]),
        row_count=_payload_decimal("row_count", payload["row_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        blocked_count=_payload_decimal("blocked_count", payload["blocked_count"]),
        average_base_rate_anchor_score=_payload_decimal(
            "average_base_rate_anchor_score",
            payload["average_base_rate_anchor_score"],
        ),
        max_forecast_base_rate_deviation=_payload_decimal(
            "max_forecast_base_rate_deviation",
            payload["max_forecast_base_rate_deviation"],
        ),
        rows=_payload_rows(payload["rows"]),
        fact_config_versions=_payload_fact_config_versions(
            payload["fact_config_versions"],
        ),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        derived_validation_digest=_payload_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        boundary_statement=_payload_public_string(
            "boundary_statement",
            payload["boundary_statement"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _row_from_payload(payload: dict[str, Any]) -> CandidateDecisionBaseRateAnchorScoreRow:
    _require_payload_keys("payload row", payload, ROW_PAYLOAD_KEYS)
    return CandidateDecisionBaseRateAnchorScoreRow(
        rank=_payload_decimal("rank", payload["rank"]),
        redacted_candidate_id=_payload_redacted_identifier(
            "redacted_candidate_id",
            payload["redacted_candidate_id"],
        ),
        redacted_team_id=_payload_redacted_identifier(
            "redacted_team_id",
            payload["redacted_team_id"],
        ),
        redacted_domain_id=_payload_redacted_identifier(
            "redacted_domain_id",
            payload["redacted_domain_id"],
        ),
        observed_at=_payload_datetime("observed_at", payload["observed_at"]),
        candidate_forecast_probability=_payload_decimal(
            "candidate_forecast_probability",
            payload["candidate_forecast_probability"],
        ),
        base_rate_probability=_payload_decimal(
            "base_rate_probability",
            payload["base_rate_probability"],
        ),
        forecast_base_rate_deviation=_payload_decimal(
            "forecast_base_rate_deviation",
            payload["forecast_base_rate_deviation"],
        ),
        base_rate_sample_size=_payload_decimal(
            "base_rate_sample_size",
            payload["base_rate_sample_size"],
        ),
        sample_size_score=_payload_decimal("sample_size_score", payload["sample_size_score"]),
        base_rate_recency_score=_payload_decimal(
            "base_rate_recency_score",
            payload["base_rate_recency_score"],
        ),
        base_rate_similarity_score=_payload_decimal(
            "base_rate_similarity_score",
            payload["base_rate_similarity_score"],
        ),
        base_rate_dispersion_score=_payload_decimal(
            "base_rate_dispersion_score",
            payload["base_rate_dispersion_score"],
        ),
        dispersion_grounding_score=_payload_decimal(
            "dispersion_grounding_score",
            payload["dispersion_grounding_score"],
        ),
        specialist_calibration_score=_payload_decimal(
            "specialist_calibration_score",
            payload["specialist_calibration_score"],
        ),
        deviation_justification_score=_payload_decimal(
            "deviation_justification_score",
            payload["deviation_justification_score"],
        ),
        base_rate_anchor_score=_payload_decimal(
            "base_rate_anchor_score",
            payload["base_rate_anchor_score"],
        ),
        score_status=_payload_public_string("score_status", payload["score_status"]),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        redacted_refs=_payload_string_tuple("redacted_refs", payload["redacted_refs"]),
        fact_config_version=_payload_public_string(
            "fact_config_version",
            payload["fact_config_version"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _payload_rows(value: object) -> tuple[CandidateDecisionBaseRateAnchorScoreRow, ...]:
    if type(value) is not list:
        raise ValueError("payload rows must be a list")
    rows: list[CandidateDecisionBaseRateAnchorScoreRow] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError("payload rows must contain dicts")
        rows.append(_row_from_payload(item))
    return tuple(rows)


def _payload_fact_config_versions(value: object) -> tuple[tuple[str, str, str, str], ...]:
    if type(value) is not list:
        raise ValueError("fact_config_versions must be a list")
    normalized: list[tuple[str, str, str, str]] = []
    for item in value:
        if type(item) is not list or len(item) != 4:
            raise ValueError("fact_config_versions entries must be string quartets")
        normalized.append(
            (
                _payload_redacted_identifier("fact_config_versions", item[0]),
                _payload_redacted_identifier("fact_config_versions", item[1]),
                _payload_redacted_identifier("fact_config_versions", item[2]),
                _payload_public_string("fact_config_versions", item[3]),
            ),
        )
    return tuple(normalized)


def _payload_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_payload_public_string(field_name, item) for item in value)


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    return _require_decimal(field_name, parsed)


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    return _as_utc(field_name, parsed)


def _payload_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return _require_public_string(field_name, value)


def _payload_redacted_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return _require_redacted_identifier(field_name, value)


def _payload_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _require_digest(field_name, value)
    return value


def _payload_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = set(payload)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        if missing:
            raise ValueError(f"{label} missing keys: {', '.join(missing)}")
        raise ValueError(f"{label} contains unexpected keys: {', '.join(unexpected)}")


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if type(payload) is dict:
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_string(label, key)
            _reject_unsafe_public_payload(label, value)
        return
    if type(payload) is list:
        for item in payload:
            _reject_unsafe_public_payload(label, item)
        return
    if type(payload) is str:
        _reject_unsafe_public_string(label, payload)
        return
    if type(payload) in (bool,) or payload is None:
        return
    raise ValueError("public payload values must be strings, booleans, lists, or dicts")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lower_value = value.lower()
    if any(term in lower_value for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public surface in {field_name}")


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_matching_digest(payload: dict[str, Any]) -> None:
    digest_value = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest_value)
    if digest_value != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_BASE_RATE_ANCHOR_SCORE_CONFIG_VERSION",
    "BOUNDARY_STATEMENT",
    "CandidateDecisionBaseRateAnchorScoreConfig",
    "CandidateDecisionBaseRateAnchorFact",
    "CandidateDecisionBaseRateAnchorScoreRow",
    "CandidateDecisionBaseRateAnchorScoreReport",
    "build_candidate_decision_base_rate_anchor_score",
    "candidate_decision_base_rate_anchor_score_payload",
    "validate_candidate_decision_base_rate_anchor_score_payload",
)
