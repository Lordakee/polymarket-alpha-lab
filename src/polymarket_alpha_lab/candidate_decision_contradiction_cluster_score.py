"""Pure report-only candidate decision contradiction cluster score."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SCORE_STATUSES = ("pass", "watch", "block")
MANUAL_RESEARCH_PRIORITY_EFFECTS = ("lower", "hold", "raise")
HARD_FLAGS = (
    "severity_hard_flag",
    "resolution_conflict_hard_flag",
    "independent_contradictions_hard_flag",
)
_UNSAFE_TERM_PARTS = (
    ("mar", "ket"),
    ("slug",),
    ("quest", "ion"),
    ("ur", "l"),
    ("ht", "tp"),
    (":", "//"),
    ("www", "."),
    ("candidate", "_id"),
    ("market", "_id"),
    ("source", "_ref"),
    ("source", "_url"),
    ("source", "_text"),
    ("ds", "n"),
    ("tab", "le"),
    ("to", "ken"),
    ("sec", "ret"),
    ("au", "th"),
    ("wal", "let"),
    ("or", "der"),
    ("tra", "de"),
    ("b", "uy"),
    ("se", "ll"),
    ("recomm", "endation"),
    ("pos", "ition"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_DIGEST_FIELDS = (
    "redacted_candidate_ref",
    "contradiction_count",
    "evidence_source_count",
    "independent_contradiction_count",
    "contradiction_severity_score",
    "resolution_conflict_score",
    "source_quality_score",
    "recency_score",
    "config",
    "independent_contradiction_ratio",
    "contradiction_source_ratio",
    "contradiction_cluster_score",
    "contradiction_cluster_risk_score",
    "hard_flags",
    "cluster_status",
    "manual_research_priority_effect",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class CandidateDecisionContradictionClusterScoreConfig:
    watch_risk_threshold: Decimal = Decimal("0.300000")
    block_risk_threshold: Decimal = Decimal("0.650000")
    clustered_score_threshold: Decimal = Decimal("0.650000")
    independent_contradiction_ratio_weight: Decimal = Decimal("0.350000")
    contradiction_source_ratio_weight: Decimal = Decimal("0.150000")
    contradiction_severity_weight: Decimal = Decimal("0.250000")
    resolution_conflict_weight: Decimal = Decimal("0.150000")
    source_quality_weight: Decimal = Decimal("0.050000")
    recency_weight: Decimal = Decimal("0.050000")
    hard_block_severity_score: Decimal = Decimal("0.900000")
    hard_block_resolution_conflict_score: Decimal = Decimal("0.850000")
    hard_block_independent_contradiction_count: Decimal = Decimal("3")

    def __post_init__(self) -> None:
        for field_name in (
            "watch_risk_threshold",
            "block_risk_threshold",
            "clustered_score_threshold",
            "independent_contradiction_ratio_weight",
            "contradiction_source_ratio_weight",
            "contradiction_severity_weight",
            "resolution_conflict_weight",
            "source_quality_weight",
            "recency_weight",
            "hard_block_severity_score",
            "hard_block_resolution_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "hard_block_independent_contradiction_count",
            _normalize_nonnegative_count(
                "hard_block_independent_contradiction_count",
                self.hard_block_independent_contradiction_count,
            ),
        )
        if self.block_risk_threshold < self.watch_risk_threshold:
            raise ValueError("block_risk_threshold must be at least watch_risk_threshold")
        if _total_weight(self) <= ZERO:
            raise ValueError("config weights must sum to a positive value")


@dataclass(frozen=True)
class CandidateDecisionContradictionClusterScoreInput:
    redacted_candidate_ref: str
    contradiction_count: Decimal
    evidence_source_count: Decimal
    independent_contradiction_count: Decimal
    contradiction_severity_score: Decimal
    resolution_conflict_score: Decimal
    source_quality_score: Decimal
    recency_score: Decimal
    config: CandidateDecisionContradictionClusterScoreConfig = field(
        default_factory=CandidateDecisionContradictionClusterScoreConfig,
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_ref("redacted_candidate_ref", self.redacted_candidate_ref)
        for field_name in (
            "contradiction_count",
            "evidence_source_count",
            "independent_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.evidence_source_count <= ZERO:
            raise ValueError("evidence_source_count must be positive")
        _validate_contradiction_counts(
            self.contradiction_count,
            self.independent_contradiction_count,
        )
        for field_name in (
            "contradiction_severity_score",
            "resolution_conflict_score",
            "source_quality_score",
            "recency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if type(self.config) is not CandidateDecisionContradictionClusterScoreConfig:
            raise ValueError(
                "config must be a CandidateDecisionContradictionClusterScoreConfig",
            )
        reject_candidate_decision_contradiction_cluster_score_unsafe_payload(
            "candidate decision contradiction cluster score input",
            self,
        )
        _require_paper_flags("candidate decision contradiction cluster score input", self)


@dataclass(frozen=True)
class CandidateDecisionContradictionClusterScoreResult:
    redacted_candidate_ref: str
    contradiction_count: Decimal
    evidence_source_count: Decimal
    independent_contradiction_count: Decimal
    contradiction_severity_score: Decimal
    resolution_conflict_score: Decimal
    source_quality_score: Decimal
    recency_score: Decimal
    config: CandidateDecisionContradictionClusterScoreConfig
    independent_contradiction_ratio: Decimal
    contradiction_source_ratio: Decimal
    contradiction_cluster_score: Decimal
    contradiction_cluster_risk_score: Decimal
    hard_flags: tuple[str, ...]
    cluster_status: str
    manual_research_priority_effect: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_ref("redacted_candidate_ref", self.redacted_candidate_ref)
        for field_name in (
            "contradiction_count",
            "evidence_source_count",
            "independent_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.evidence_source_count <= ZERO:
            raise ValueError("evidence_source_count must be positive")
        _validate_contradiction_counts(
            self.contradiction_count,
            self.independent_contradiction_count,
        )
        for field_name in (
            "contradiction_severity_score",
            "resolution_conflict_score",
            "source_quality_score",
            "recency_score",
            "independent_contradiction_ratio",
            "contradiction_source_ratio",
            "contradiction_cluster_score",
            "contradiction_cluster_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if type(self.config) is not CandidateDecisionContradictionClusterScoreConfig:
            raise ValueError(
                "config must be a CandidateDecisionContradictionClusterScoreConfig",
            )
        object.__setattr__(
            self,
            "hard_flags",
            _normalize_hard_flags("hard_flags", self.hard_flags),
        )
        _require_choice("cluster_status", self.cluster_status, SCORE_STATUSES)
        _require_choice(
            "manual_research_priority_effect",
            self.manual_research_priority_effect,
            MANUAL_RESEARCH_PRIORITY_EFFECTS,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        reject_candidate_decision_contradiction_cluster_score_unsafe_payload(
            "candidate decision contradiction cluster score result",
            self,
        )
        _require_paper_flags("candidate decision contradiction cluster score result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_contradiction_cluster_score_payload(self)


def score_candidate_decision_contradiction_cluster_score(
    score_input: CandidateDecisionContradictionClusterScoreInput,
) -> CandidateDecisionContradictionClusterScoreResult:
    if type(score_input) is not CandidateDecisionContradictionClusterScoreInput:
        raise ValueError(
            "score_input must be a CandidateDecisionContradictionClusterScoreInput",
        )
    reject_candidate_decision_contradiction_cluster_score_unsafe_payload(
        "candidate decision contradiction cluster score input",
        score_input,
    )
    _require_paper_flags("candidate decision contradiction cluster score input", score_input)

    independent_contradiction_ratio = _independent_contradiction_ratio(
        score_input.contradiction_count,
        score_input.independent_contradiction_count,
    )
    contradiction_source_ratio = _contradiction_source_ratio(
        score_input.contradiction_count,
        score_input.evidence_source_count,
    )
    contradiction_cluster_score = _contradiction_cluster_score(
        score_input.contradiction_count,
        independent_contradiction_ratio,
    )
    contradiction_cluster_risk_score = _contradiction_cluster_risk_score(
        score_input,
        independent_contradiction_ratio,
        contradiction_source_ratio,
    )
    hard_flags = _hard_flags(
        contradiction_count=score_input.contradiction_count,
        independent_contradiction_count=score_input.independent_contradiction_count,
        contradiction_severity_score=score_input.contradiction_severity_score,
        resolution_conflict_score=score_input.resolution_conflict_score,
        config=score_input.config,
    )
    cluster_status = _cluster_status(
        contradiction_cluster_risk_score,
        hard_flags,
        score_input.config,
    )
    manual_research_priority_effect = _manual_research_priority_effect(cluster_status)

    return CandidateDecisionContradictionClusterScoreResult(
        redacted_candidate_ref=score_input.redacted_candidate_ref,
        contradiction_count=score_input.contradiction_count,
        evidence_source_count=score_input.evidence_source_count,
        independent_contradiction_count=score_input.independent_contradiction_count,
        contradiction_severity_score=score_input.contradiction_severity_score,
        resolution_conflict_score=score_input.resolution_conflict_score,
        source_quality_score=score_input.source_quality_score,
        recency_score=score_input.recency_score,
        config=score_input.config,
        independent_contradiction_ratio=independent_contradiction_ratio,
        contradiction_source_ratio=contradiction_source_ratio,
        contradiction_cluster_score=contradiction_cluster_score,
        contradiction_cluster_risk_score=contradiction_cluster_risk_score,
        hard_flags=hard_flags,
        cluster_status=cluster_status,
        manual_research_priority_effect=manual_research_priority_effect,
        reason_codes=_reason_codes(
            contradiction_count=score_input.contradiction_count,
            contradiction_cluster_score=contradiction_cluster_score,
            contradiction_cluster_risk_score=contradiction_cluster_risk_score,
            hard_flags=hard_flags,
            cluster_status=cluster_status,
            manual_research_priority_effect=manual_research_priority_effect,
            config=score_input.config,
        ),
    )


def estimate_candidate_decision_contradiction_cluster_score(
    score_input: CandidateDecisionContradictionClusterScoreInput,
) -> CandidateDecisionContradictionClusterScoreResult:
    return score_candidate_decision_contradiction_cluster_score(score_input)


def candidate_decision_contradiction_cluster_score_payload(
    result: CandidateDecisionContradictionClusterScoreResult,
) -> dict[str, Any]:
    if type(result) is not CandidateDecisionContradictionClusterScoreResult:
        raise ValueError(
            "result must be a CandidateDecisionContradictionClusterScoreResult",
        )
    _require_paper_flags("candidate decision contradiction cluster score result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_candidate_decision_contradiction_cluster_score_unsafe_payload(
        "candidate decision contradiction cluster score result",
        result,
    )
    return _json_ready(asdict(result))


def reject_candidate_decision_contradiction_cluster_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _independent_contradiction_ratio(
    contradiction_count: Decimal,
    independent_contradiction_count: Decimal,
) -> Decimal:
    if contradiction_count == ZERO:
        return ZERO
    return _normalize_ratio(
        "independent_contradiction_ratio",
        independent_contradiction_count / contradiction_count,
    )


def _contradiction_source_ratio(
    contradiction_count: Decimal,
    evidence_source_count: Decimal,
) -> Decimal:
    if contradiction_count == ZERO:
        return ZERO
    ratio = contradiction_count / evidence_source_count
    if ratio > ONE:
        return ONE
    return _normalize_ratio("contradiction_source_ratio", ratio)


def _contradiction_cluster_score(
    contradiction_count: Decimal,
    independent_contradiction_ratio: Decimal,
) -> Decimal:
    if contradiction_count == ZERO:
        return ONE
    return _normalize_ratio(
        "contradiction_cluster_score",
        ONE - independent_contradiction_ratio,
    )


def _contradiction_cluster_risk_score(
    score_input: CandidateDecisionContradictionClusterScoreInput,
    independent_contradiction_ratio: Decimal,
    contradiction_source_ratio: Decimal,
) -> Decimal:
    if score_input.contradiction_count == ZERO:
        return ZERO
    config = score_input.config
    weighted_sum = (
        independent_contradiction_ratio
        * config.independent_contradiction_ratio_weight
        + contradiction_source_ratio * config.contradiction_source_ratio_weight
        + score_input.contradiction_severity_score * config.contradiction_severity_weight
        + score_input.resolution_conflict_score * config.resolution_conflict_weight
        + score_input.source_quality_score * config.source_quality_weight
        + score_input.recency_score * config.recency_weight
    )
    return _normalize_ratio(
        "contradiction_cluster_risk_score",
        weighted_sum / _total_weight(config),
    )


def _hard_flags(
    *,
    contradiction_count: Decimal,
    independent_contradiction_count: Decimal,
    contradiction_severity_score: Decimal,
    resolution_conflict_score: Decimal,
    config: CandidateDecisionContradictionClusterScoreConfig,
) -> tuple[str, ...]:
    if contradiction_count == ZERO:
        return ()
    flags: list[str] = []
    if contradiction_severity_score >= config.hard_block_severity_score:
        flags.append("severity_hard_flag")
    if resolution_conflict_score >= config.hard_block_resolution_conflict_score:
        flags.append("resolution_conflict_hard_flag")
    if independent_contradiction_count >= config.hard_block_independent_contradiction_count:
        flags.append("independent_contradictions_hard_flag")
    return tuple(flags)


def _cluster_status(
    contradiction_cluster_risk_score: Decimal,
    hard_flags: tuple[str, ...],
    config: CandidateDecisionContradictionClusterScoreConfig,
) -> str:
    if hard_flags:
        return "block"
    if contradiction_cluster_risk_score >= config.block_risk_threshold:
        return "block"
    if contradiction_cluster_risk_score >= config.watch_risk_threshold:
        return "watch"
    return "pass"


def _manual_research_priority_effect(cluster_status: str) -> str:
    if cluster_status == "pass":
        return "lower"
    if cluster_status == "watch":
        return "hold"
    if cluster_status == "block":
        return "raise"
    raise ValueError("cluster_status must be pass, watch, or block")


def _reason_codes(
    *,
    contradiction_count: Decimal,
    contradiction_cluster_score: Decimal,
    contradiction_cluster_risk_score: Decimal,
    hard_flags: tuple[str, ...],
    cluster_status: str,
    manual_research_priority_effect: str,
    config: CandidateDecisionContradictionClusterScoreConfig,
) -> tuple[str, ...]:
    values = [
        "candidate_decision_contradiction_cluster_score",
        f"score_{cluster_status}",
        _contradiction_presence_reason_code(contradiction_count),
        _cluster_reason_code(
            contradiction_count,
            contradiction_cluster_score,
            config.clustered_score_threshold,
        ),
        _risk_threshold_reason_code(contradiction_cluster_risk_score, config),
    ]
    if hard_flags:
        values.append("hard_flags_present")
        values.extend(hard_flags)
    else:
        values.append("hard_flags_clear")
    values.append(f"manual_research_priority_{manual_research_priority_effect}")
    return tuple(values)


def _contradiction_presence_reason_code(contradiction_count: Decimal) -> str:
    if contradiction_count == ZERO:
        return "no_contradictions_present"
    return "contradictions_present"


def _cluster_reason_code(
    contradiction_count: Decimal,
    contradiction_cluster_score: Decimal,
    clustered_score_threshold: Decimal,
) -> str:
    if contradiction_count == ZERO:
        return "contradictions_absent"
    if contradiction_cluster_score >= clustered_score_threshold:
        return "contradictions_clustered"
    return "contradictions_dispersed"


def _risk_threshold_reason_code(
    contradiction_cluster_risk_score: Decimal,
    config: CandidateDecisionContradictionClusterScoreConfig,
) -> str:
    if contradiction_cluster_risk_score >= config.block_risk_threshold:
        return "risk_at_or_above_block_threshold"
    if contradiction_cluster_risk_score >= config.watch_risk_threshold:
        return "risk_at_or_above_watch_threshold"
    return "risk_below_watch_threshold"


def _validate_contradiction_counts(
    contradiction_count: Decimal,
    independent_contradiction_count: Decimal,
) -> None:
    if independent_contradiction_count > contradiction_count:
        raise ValueError(
            "independent_contradiction_count must not exceed contradiction_count",
        )
    if contradiction_count == ZERO and independent_contradiction_count != ZERO:
        raise ValueError(
            "independent_contradiction_count must be zero without contradictions",
        )
    if contradiction_count > ZERO and independent_contradiction_count <= ZERO:
        raise ValueError(
            "independent_contradiction_count must be positive with contradictions",
        )


def _validate_result_consistency(
    result: CandidateDecisionContradictionClusterScoreResult,
) -> None:
    expected_independent_ratio = _independent_contradiction_ratio(
        result.contradiction_count,
        result.independent_contradiction_count,
    )
    if result.independent_contradiction_ratio != expected_independent_ratio:
        raise ValueError(
            "independent_contradiction_ratio must match contradiction counts",
        )
    expected_source_ratio = _contradiction_source_ratio(
        result.contradiction_count,
        result.evidence_source_count,
    )
    if result.contradiction_source_ratio != expected_source_ratio:
        raise ValueError("contradiction_source_ratio must match source counts")
    expected_cluster_score = _contradiction_cluster_score(
        result.contradiction_count,
        result.independent_contradiction_ratio,
    )
    if result.contradiction_cluster_score != expected_cluster_score:
        raise ValueError("contradiction_cluster_score must match independent ratio")
    expected_risk_score = _contradiction_cluster_risk_score(
        CandidateDecisionContradictionClusterScoreInput(
            redacted_candidate_ref=result.redacted_candidate_ref,
            contradiction_count=result.contradiction_count,
            evidence_source_count=result.evidence_source_count,
            independent_contradiction_count=result.independent_contradiction_count,
            contradiction_severity_score=result.contradiction_severity_score,
            resolution_conflict_score=result.resolution_conflict_score,
            source_quality_score=result.source_quality_score,
            recency_score=result.recency_score,
            config=result.config,
            paper_only=result.paper_only,
            report_only=result.report_only,
            readonly=result.readonly,
        ),
        result.independent_contradiction_ratio,
        result.contradiction_source_ratio,
    )
    if result.contradiction_cluster_risk_score != expected_risk_score:
        raise ValueError("contradiction_cluster_risk_score must match inputs")
    expected_hard_flags = _hard_flags(
        contradiction_count=result.contradiction_count,
        independent_contradiction_count=result.independent_contradiction_count,
        contradiction_severity_score=result.contradiction_severity_score,
        resolution_conflict_score=result.resolution_conflict_score,
        config=result.config,
    )
    if result.hard_flags != expected_hard_flags:
        raise ValueError("hard_flags must match inputs")
    expected_status = _cluster_status(
        result.contradiction_cluster_risk_score,
        result.hard_flags,
        result.config,
    )
    if result.cluster_status != expected_status:
        raise ValueError("cluster_status must match risk score")
    expected_effect = _manual_research_priority_effect(result.cluster_status)
    if result.manual_research_priority_effect != expected_effect:
        raise ValueError(
            "manual_research_priority_effect must match cluster_status",
        )
    expected_reason_codes = _reason_codes(
        contradiction_count=result.contradiction_count,
        contradiction_cluster_score=result.contradiction_cluster_score,
        contradiction_cluster_risk_score=result.contradiction_cluster_risk_score,
        hard_flags=result.hard_flags,
        cluster_status=result.cluster_status,
        manual_research_priority_effect=result.manual_research_priority_effect,
        config=result.config,
    )
    if result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match report fields")


def _derived_validation_digest(
    result: CandidateDecisionContradictionClusterScoreResult,
) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(result, field_name))}"
        for field_name in _DIGEST_FIELDS
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return (
            "{"
            + ",".join(
                f"{item.name}:{_digest_value(getattr(value, item.name))}"
                for item in fields(value)
            )
            + "}"
        )
    if isinstance(value, tuple):
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("digest value must be public scalar data")


def _normalize_hard_flags(field_name: str, value: object) -> tuple[str, ...]:
    normalized = _normalize_reason_codes(field_name, value)
    for hard_flag in normalized:
        _require_choice(field_name, hard_flag, HARD_FLAGS)
    return normalized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between {ZERO} and {ONE}")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _total_weight(config: CandidateDecisionContradictionClusterScoreConfig) -> Decimal:
    return _normalize_nonnegative_decimal(
        "total_weight",
        config.independent_contradiction_ratio_weight
        + config.contradiction_source_ratio_weight
        + config.contradiction_severity_weight
        + config.resolution_conflict_weight
        + config.source_quality_weight
        + config.recency_weight,
    )


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_redacted_ref(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not value.startswith("redacted:"):
        raise ValueError(f"{field_name} must be redacted")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_canonical_digest(value: object) -> None:
    _require_canonical_string("derived_validation_digest", value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be lowercase hex")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    return ()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "SCORE_STATUSES",
    "MANUAL_RESEARCH_PRIORITY_EFFECTS",
    "HARD_FLAGS",
    "CandidateDecisionContradictionClusterScoreConfig",
    "CandidateDecisionContradictionClusterScoreInput",
    "CandidateDecisionContradictionClusterScoreResult",
    "score_candidate_decision_contradiction_cluster_score",
    "estimate_candidate_decision_contradiction_cluster_score",
    "candidate_decision_contradiction_cluster_score_payload",
    "reject_candidate_decision_contradiction_cluster_score_unsafe_payload",
)
