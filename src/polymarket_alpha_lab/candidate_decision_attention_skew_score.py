"""Pure report-only public attention skew scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from decimal import Decimal
from hashlib import sha256
from typing import Any


DEFAULT_CANDIDATE_DECISION_ATTENTION_SKEW_SCORE_CONFIG_VERSION = (
    "candidate-decision-attention-skew-score-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

ATTENTION_SKEW_STATUSES = ("pass", "watch", "block")

_BASE_REASON_CODE = "candidate_decision_attention_skew_score"
_INPUT_FIELDS = (
    "crowd_attention_score",
    "media_concentration_score",
    "contrarian_source_count",
    "sentiment_dispersion_score",
    "liquidity_attention_ratio",
    "evidence_quality_score",
)
_LEVEL_FIELDS = (
    *_INPUT_FIELDS,
    "attention_skew_score",
)
_CONFIG_THRESHOLD_FIELDS = (
    "max_pass_crowd_attention_score",
    "max_watch_crowd_attention_score",
    "max_pass_media_concentration_score",
    "max_watch_media_concentration_score",
    "min_pass_contrarian_source_count",
    "min_watch_contrarian_source_count",
    "max_pass_sentiment_dispersion_score",
    "max_watch_sentiment_dispersion_score",
    "max_pass_liquidity_attention_ratio",
    "max_watch_liquidity_attention_ratio",
    "min_pass_evidence_quality_score",
    "min_watch_evidence_quality_score",
    "max_pass_attention_skew_score",
    "max_watch_attention_skew_score",
)
_CONFIG_WEIGHT_FIELDS = (
    "crowd_attention_weight",
    "media_concentration_weight",
    "contrarian_source_gap_weight",
    "sentiment_dispersion_weight",
    "liquidity_attention_weight",
    "evidence_quality_gap_weight",
)
_DERIVED_FIELDS = (
    "contrarian_source_gap_score",
    "evidence_quality_gap_score",
    "attention_skew_score",
)
_DIGEST_SKIP_FIELDS = ("derived_validation_digest",)

_UNSAFE_PUBLIC_PARTS = (
    ("candidate", "_id"),
    ("raw", "_candidate"),
    ("market", "_id"),
    ("market", "_sl", "ug"),
    ("market", "_ques", "tion"),
    ("ques", "tion"),
    ("source", "_re", "f"),
    ("source", "_ur", "l"),
    ("source", "_te", "xt"),
    ("ur", "l"),
    ("ht", "tp"),
    (":", "/", "/"),
    ("d", "sn"),
    ("table", "_name"),
    ("to", "ken"),
    ("sec", "ret"),
    ("private", "_key"),
    ("wal", "let"),
    ("au", "th"),
    ("or", "der"),
    ("tr", "ade"),
    ("b", "uy"),
    ("se", "ll"),
    ("reco", "mmend"),
    ("reco", "mmendation"),
    ("pos", "ition", "_size"),
    ("pos", "ition", "-", "sizing"),
    ("pos", "ition", " sizing"),
    ("rea", "dy"),
    ("block", "ed"),
    ("mat", "ched"),
    ("sup", "ported"),
)
_UNSAFE_PUBLIC_TERMS = tuple("".join(parts) for parts in _UNSAFE_PUBLIC_PARTS)


@dataclass(frozen=True)
class CandidateDecisionAttentionSkewScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_ATTENTION_SKEW_SCORE_CONFIG_VERSION
    )
    max_pass_crowd_attention_score: Decimal = Decimal("0.550000")
    max_watch_crowd_attention_score: Decimal = Decimal("0.800000")
    max_pass_media_concentration_score: Decimal = Decimal("0.500000")
    max_watch_media_concentration_score: Decimal = Decimal("0.750000")
    min_pass_contrarian_source_count: Decimal = Decimal("3.000000")
    min_watch_contrarian_source_count: Decimal = Decimal("1.000000")
    max_pass_sentiment_dispersion_score: Decimal = Decimal("0.500000")
    max_watch_sentiment_dispersion_score: Decimal = Decimal("0.750000")
    max_pass_liquidity_attention_ratio: Decimal = Decimal("0.500000")
    max_watch_liquidity_attention_ratio: Decimal = Decimal("0.750000")
    min_pass_evidence_quality_score: Decimal = Decimal("0.700000")
    min_watch_evidence_quality_score: Decimal = Decimal("0.400000")
    max_pass_attention_skew_score: Decimal = Decimal("0.350000")
    max_watch_attention_skew_score: Decimal = Decimal("0.650000")
    crowd_attention_weight: Decimal = Decimal("0.200000")
    media_concentration_weight: Decimal = Decimal("0.200000")
    contrarian_source_gap_weight: Decimal = Decimal("0.150000")
    sentiment_dispersion_weight: Decimal = Decimal("0.150000")
    liquidity_attention_weight: Decimal = Decimal("0.150000")
    evidence_quality_gap_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionAttentionSkewScoreConfig:
            raise ValueError("config must be a CandidateDecisionAttentionSkewScoreConfig")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_pass_contrarian_source_count",
            "min_watch_contrarian_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_crowd_attention_score",
            "max_watch_crowd_attention_score",
            "max_pass_media_concentration_score",
            "max_watch_media_concentration_score",
            "max_pass_sentiment_dispersion_score",
            "max_watch_sentiment_dispersion_score",
            "max_pass_liquidity_attention_ratio",
            "max_watch_liquidity_attention_ratio",
            "min_pass_evidence_quality_score",
            "min_watch_evidence_quality_score",
            "max_pass_attention_skew_score",
            "max_watch_attention_skew_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in _CONFIG_WEIGHT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config_thresholds(self)
        if _config_weight_sum(self) != ONE:
            raise ValueError("config weights must sum to 1")
        _require_report_flags("config", self)


@dataclass(frozen=True)
class CandidateDecisionAttentionSkewScoreInput:
    redacted_candidate_ref: str
    crowd_attention_score: Decimal
    media_concentration_score: Decimal
    contrarian_source_count: Decimal
    sentiment_dispersion_score: Decimal
    liquidity_attention_ratio: Decimal
    evidence_quality_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionAttentionSkewScoreInput:
            raise ValueError(
                "input_value must be a CandidateDecisionAttentionSkewScoreInput",
            )
        _require_canonical_string("redacted_candidate_ref", self.redacted_candidate_ref)
        _reject_unsafe_public_text("redacted_candidate_ref", self.redacted_candidate_ref)
        for field_name in (
            "crowd_attention_score",
            "media_concentration_score",
            "sentiment_dispersion_score",
            "liquidity_attention_ratio",
            "evidence_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contrarian_source_count",
            _normalize_whole_nonnegative_decimal(
                "contrarian_source_count",
                self.contrarian_source_count,
            ),
        )
        _require_report_flags("input_value", self)


@dataclass(frozen=True)
class CandidateDecisionAttentionSkewScoreReport:
    config_version: str
    redacted_candidate_ref: str
    crowd_attention_score: Decimal
    media_concentration_score: Decimal
    contrarian_source_count: Decimal
    sentiment_dispersion_score: Decimal
    liquidity_attention_ratio: Decimal
    evidence_quality_score: Decimal
    contrarian_source_gap_score: Decimal
    evidence_quality_gap_score: Decimal
    attention_skew_score: Decimal
    status: str
    hard_flag_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    max_pass_crowd_attention_score: Decimal
    max_watch_crowd_attention_score: Decimal
    max_pass_media_concentration_score: Decimal
    max_watch_media_concentration_score: Decimal
    min_pass_contrarian_source_count: Decimal
    min_watch_contrarian_source_count: Decimal
    max_pass_sentiment_dispersion_score: Decimal
    max_watch_sentiment_dispersion_score: Decimal
    max_pass_liquidity_attention_ratio: Decimal
    max_watch_liquidity_attention_ratio: Decimal
    min_pass_evidence_quality_score: Decimal
    min_watch_evidence_quality_score: Decimal
    max_pass_attention_skew_score: Decimal
    max_watch_attention_skew_score: Decimal
    crowd_attention_weight: Decimal
    media_concentration_weight: Decimal
    contrarian_source_gap_weight: Decimal
    sentiment_dispersion_weight: Decimal
    liquidity_attention_weight: Decimal
    evidence_quality_gap_weight: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionAttentionSkewScoreReport:
            raise ValueError("report must be a CandidateDecisionAttentionSkewScoreReport")
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("redacted_candidate_ref", self.redacted_candidate_ref)
        _reject_unsafe_public_text("redacted_candidate_ref", self.redacted_candidate_ref)
        for field_name in (
            "crowd_attention_score",
            "media_concentration_score",
            "sentiment_dispersion_score",
            "liquidity_attention_ratio",
            "evidence_quality_score",
            *_DERIVED_FIELDS,
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contrarian_source_count",
            _normalize_whole_nonnegative_decimal(
                "contrarian_source_count",
                self.contrarian_source_count,
            ),
        )
        for field_name in _CONFIG_THRESHOLD_FIELDS:
            normalizer = (
                _normalize_whole_nonnegative_decimal
                if field_name.endswith("_source_count")
                else _normalize_unit_decimal
            )
            object.__setattr__(
                self,
                field_name,
                normalizer(field_name, getattr(self, field_name)),
            )
        for field_name in _CONFIG_WEIGHT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, ATTENTION_SKEW_STATUSES)
        object.__setattr__(
            self,
            "hard_flag_codes",
            _normalize_reason_codes("hard_flag_codes", self.hard_flag_codes, True),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, False),
        )
        _require_report_flags("report", self)
        _validate_report_consistency(self)
        validate_candidate_decision_attention_skew_score_public_payload(
            _public_json(asdict(self)),
        )
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_attention_skew_score_payload(self)


def score_candidate_decision_attention_skew(
    input_value: CandidateDecisionAttentionSkewScoreInput,
    *,
    config: CandidateDecisionAttentionSkewScoreConfig,
) -> CandidateDecisionAttentionSkewScoreReport:
    if type(input_value) is not CandidateDecisionAttentionSkewScoreInput:
        raise ValueError("input_value must be a CandidateDecisionAttentionSkewScoreInput")
    if type(config) is not CandidateDecisionAttentionSkewScoreConfig:
        raise ValueError("config must be a CandidateDecisionAttentionSkewScoreConfig")
    _require_report_flags("input_value", input_value)
    _require_report_flags("config", config)

    metrics = _score_metrics(input_value, config)
    levels = _status_levels(input_value, metrics, config)
    status = _status_from_levels(levels)
    hard_flags = _hard_flag_codes(levels)
    report_values: dict[str, object] = {
        "config_version": config.config_version,
        "redacted_candidate_ref": input_value.redacted_candidate_ref,
        "crowd_attention_score": input_value.crowd_attention_score,
        "media_concentration_score": input_value.media_concentration_score,
        "contrarian_source_count": input_value.contrarian_source_count,
        "sentiment_dispersion_score": input_value.sentiment_dispersion_score,
        "liquidity_attention_ratio": input_value.liquidity_attention_ratio,
        "evidence_quality_score": input_value.evidence_quality_score,
        "contrarian_source_gap_score": metrics["contrarian_source_gap_score"],
        "evidence_quality_gap_score": metrics["evidence_quality_gap_score"],
        "attention_skew_score": metrics["attention_skew_score"],
        "status": status,
        "hard_flag_codes": hard_flags,
        "reason_codes": _reason_codes(status, levels, hard_flags),
        **{field_name: getattr(config, field_name) for field_name in _CONFIG_THRESHOLD_FIELDS},
        **{field_name: getattr(config, field_name) for field_name in _CONFIG_WEIGHT_FIELDS},
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return CandidateDecisionAttentionSkewScoreReport(
        **report_values,
        derived_validation_digest=_digest_from_values(report_values),
    )


def candidate_decision_attention_skew_score_payload(
    report: CandidateDecisionAttentionSkewScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionAttentionSkewScoreReport:
        raise ValueError("report must be a CandidateDecisionAttentionSkewScoreReport")
    _require_report_flags("report", report)
    _validate_report_consistency(report)
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = _public_json(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_attention_skew_score_public_payload(payload)
    return payload


def validate_candidate_decision_attention_skew_score_public_payload(
    payload: dict[str, Any],
    *,
    require_flags: bool = True,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_entries(payload)
    _reject_numeric_public_values(payload)
    if require_flags:
        _require_public_payload_flags(payload)
    return True


def _score_metrics(
    input_value: CandidateDecisionAttentionSkewScoreInput,
    config: CandidateDecisionAttentionSkewScoreConfig,
) -> dict[str, Decimal]:
    contrarian_source_gap_score = _normalize_unit_decimal(
        "contrarian_source_gap_score",
        ONE
        - min(
            ONE,
            input_value.contrarian_source_count
            / config.min_pass_contrarian_source_count,
        ),
    )
    evidence_quality_gap_score = _normalize_unit_decimal(
        "evidence_quality_gap_score",
        ONE - input_value.evidence_quality_score,
    )
    attention_skew_score = _normalize_unit_decimal(
        "attention_skew_score",
        input_value.crowd_attention_score * config.crowd_attention_weight
        + input_value.media_concentration_score * config.media_concentration_weight
        + contrarian_source_gap_score * config.contrarian_source_gap_weight
        + input_value.sentiment_dispersion_score * config.sentiment_dispersion_weight
        + input_value.liquidity_attention_ratio * config.liquidity_attention_weight
        + evidence_quality_gap_score * config.evidence_quality_gap_weight,
    )
    return {
        "contrarian_source_gap_score": contrarian_source_gap_score,
        "evidence_quality_gap_score": evidence_quality_gap_score,
        "attention_skew_score": attention_skew_score,
    }


def _status_levels(
    input_value: CandidateDecisionAttentionSkewScoreInput,
    metrics: dict[str, Decimal],
    config: CandidateDecisionAttentionSkewScoreConfig,
) -> dict[str, str]:
    return {
        "crowd_attention_score": _max_threshold_level(
            input_value.crowd_attention_score,
            config.max_pass_crowd_attention_score,
            config.max_watch_crowd_attention_score,
        ),
        "media_concentration_score": _max_threshold_level(
            input_value.media_concentration_score,
            config.max_pass_media_concentration_score,
            config.max_watch_media_concentration_score,
        ),
        "contrarian_source_count": _min_threshold_level(
            input_value.contrarian_source_count,
            config.min_pass_contrarian_source_count,
            config.min_watch_contrarian_source_count,
        ),
        "sentiment_dispersion_score": _max_threshold_level(
            input_value.sentiment_dispersion_score,
            config.max_pass_sentiment_dispersion_score,
            config.max_watch_sentiment_dispersion_score,
        ),
        "liquidity_attention_ratio": _max_threshold_level(
            input_value.liquidity_attention_ratio,
            config.max_pass_liquidity_attention_ratio,
            config.max_watch_liquidity_attention_ratio,
        ),
        "evidence_quality_score": _min_threshold_level(
            input_value.evidence_quality_score,
            config.min_pass_evidence_quality_score,
            config.min_watch_evidence_quality_score,
        ),
        "attention_skew_score": _max_threshold_level(
            metrics["attention_skew_score"],
            config.max_pass_attention_skew_score,
            config.max_watch_attention_skew_score,
        ),
    }


def _status_from_levels(levels: dict[str, str]) -> str:
    if any(level == "block" for level in levels.values()):
        return "block"
    if any(level == "watch" for level in levels.values()):
        return "watch"
    return "pass"


def _hard_flag_codes(levels: dict[str, str]) -> tuple[str, ...]:
    return tuple(
        f"{field_name}_block"
        for field_name in _LEVEL_FIELDS
        if levels[field_name] == "block"
    )


def _reason_codes(
    status: str,
    levels: dict[str, str],
    hard_flag_codes: tuple[str, ...],
) -> tuple[str, ...]:
    return (
        _BASE_REASON_CODE,
        f"status_{status}",
        *(f"{field_name}_{levels[field_name]}" for field_name in _LEVEL_FIELDS),
        "hard_flags_present" if hard_flag_codes else "hard_flags_absent",
    )


def _min_threshold_level(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value < watch_threshold:
        return "block"
    if value < pass_threshold:
        return "watch"
    return "pass"


def _max_threshold_level(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value > watch_threshold:
        return "block"
    if value > pass_threshold:
        return "watch"
    return "pass"


def _validate_report_consistency(
    report: CandidateDecisionAttentionSkewScoreReport,
) -> None:
    config = CandidateDecisionAttentionSkewScoreConfig(
        config_version=report.config_version,
        **{
            field_name: getattr(report, field_name)
            for field_name in (*_CONFIG_THRESHOLD_FIELDS, *_CONFIG_WEIGHT_FIELDS)
        },
    )
    input_value = CandidateDecisionAttentionSkewScoreInput(
        redacted_candidate_ref=report.redacted_candidate_ref,
        crowd_attention_score=report.crowd_attention_score,
        media_concentration_score=report.media_concentration_score,
        contrarian_source_count=report.contrarian_source_count,
        sentiment_dispersion_score=report.sentiment_dispersion_score,
        liquidity_attention_ratio=report.liquidity_attention_ratio,
        evidence_quality_score=report.evidence_quality_score,
    )
    metrics = _score_metrics(input_value, config)
    for field_name in _DERIVED_FIELDS:
        if getattr(report, field_name) != metrics[field_name]:
            raise ValueError(f"{field_name} must match report inputs")
    levels = _status_levels(input_value, metrics, config)
    hard_flags = _hard_flag_codes(levels)
    if report.hard_flag_codes != hard_flags:
        raise ValueError("hard_flag_codes must match report inputs")
    status = _status_from_levels(levels)
    if report.status != status:
        raise ValueError("status must match report inputs")
    expected_reason_codes = _reason_codes(status, levels, hard_flags)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match report inputs")


def _validate_config_thresholds(
    config: CandidateDecisionAttentionSkewScoreConfig,
) -> None:
    if config.max_pass_crowd_attention_score > config.max_watch_crowd_attention_score:
        raise ValueError(
            "max_pass_crowd_attention_score must not exceed watch threshold",
        )
    if (
        config.max_pass_media_concentration_score
        > config.max_watch_media_concentration_score
    ):
        raise ValueError(
            "max_pass_media_concentration_score must not exceed watch threshold",
        )
    if (
        config.min_watch_contrarian_source_count
        > config.min_pass_contrarian_source_count
    ):
        raise ValueError(
            "min_watch_contrarian_source_count must not exceed pass threshold",
        )
    if (
        config.max_pass_sentiment_dispersion_score
        > config.max_watch_sentiment_dispersion_score
    ):
        raise ValueError(
            "max_pass_sentiment_dispersion_score must not exceed watch threshold",
        )
    if (
        config.max_pass_liquidity_attention_ratio
        > config.max_watch_liquidity_attention_ratio
    ):
        raise ValueError(
            "max_pass_liquidity_attention_ratio must not exceed watch threshold",
        )
    if config.min_watch_evidence_quality_score > config.min_pass_evidence_quality_score:
        raise ValueError(
            "min_watch_evidence_quality_score must not exceed pass threshold",
        )
    if config.max_pass_attention_skew_score > config.max_watch_attention_skew_score:
        raise ValueError(
            "max_pass_attention_skew_score must not exceed watch threshold",
        )
    if config.min_pass_contrarian_source_count <= ZERO:
        raise ValueError("min_pass_contrarian_source_count must be positive")


def _config_weight_sum(config: CandidateDecisionAttentionSkewScoreConfig) -> Decimal:
    total = ZERO
    for field_name in _CONFIG_WEIGHT_FIELDS:
        total += getattr(config, field_name)
    return _normalize_nonnegative_decimal("config_weight_sum", total)


def _normalize_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole nonnegative Decimal")
    return _normalize_nonnegative_decimal(field_name, decimal_value)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _normalize_decimal(field_name, decimal_value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _normalize_decimal(field_name, decimal_value)


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM)
    except Exception as exc:
        raise ValueError(f"{field_name} must be quantizable to six decimals") from exc


def _require_exact_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is Decimal:
        return value
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be an exact Decimal")
    raise ValueError(f"{field_name} must be a Decimal")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value != value.strip() or any(ch in value for ch in "\r\n\t"):
        raise ValueError(f"{field_name} must be a canonical string")
    return value


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> str:
    _require_canonical_string(field_name, value)
    if value not in members:
        raise ValueError(f"{field_name} must be one of {members}")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        _reject_unsafe_public_text(field_name, item)
        normalized.append(item)
    return tuple(normalized)


def _require_report_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name, None)
        if type(flag) is not bool or flag is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")
    if payload.get("status") not in ATTENTION_SKEW_STATUSES:
        raise ValueError("status must be pass, watch, or block")


def _reject_unsafe_public_entries(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload field names must be strings")
            _reject_unsafe_public_text("public payload field", key)
            _reject_unsafe_public_entries(item)
    elif type(value) is list or type(value) is tuple:
        for item in value:
            _reject_unsafe_public_entries(item)
    elif type(value) is str:
        _reject_unsafe_public_text("public payload value", value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe {label}")


def _reject_numeric_public_values(value: object) -> None:
    if type(value) is dict:
        for item in value.values():
            _reject_numeric_public_values(item)
    elif type(value) is list or type(value) is tuple:
        for item in value:
            _reject_numeric_public_values(item)
    elif isinstance(value, Decimal) or type(value) is float:
        raise ValueError("numeric public payload values must be stringified")
    elif type(value) is int and type(value) is not bool:
        raise ValueError("numeric public payload values must be stringified")


def _public_json(value: object) -> object:
    if isinstance(value, Decimal):
        return str(_normalize_decimal("payload_decimal", value))
    if type(value) is tuple:
        return [_public_json(item) for item in value]
    if type(value) is list:
        return [_public_json(item) for item in value]
    if type(value) is dict:
        return {key: _public_json(item) for key, item in value.items()}
    if type(value) in {str, bool} or value is None:
        return value
    raise ValueError(f"payload value {type(value).__name__} is not allowed")


def _derived_validation_digest(report: CandidateDecisionAttentionSkewScoreReport) -> str:
    return _digest_from_values(_report_values_without_digest(report))


def _report_values_without_digest(
    report: CandidateDecisionAttentionSkewScoreReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name not in _DIGEST_SKIP_FIELDS
    }


def _digest_from_values(values: dict[str, object]) -> str:
    public_values = _public_json(
        {
            key: value
            for key, value in values.items()
            if key not in _DIGEST_SKIP_FIELDS
        },
    )
    return sha256(_stable_text(public_values).encode("utf-8")).hexdigest()


def _stable_text(value: object) -> str:
    if type(value) is dict:
        parts = []
        for key in sorted(value):
            parts.append(f"{key}:{_stable_text(value[key])}")
        return "{" + ",".join(parts) + "}"
    if type(value) is list:
        return "[" + ",".join(_stable_text(item) for item in value) + "]"
    if type(value) is str:
        return f"str:{value}"
    if type(value) is bool:
        return "bool:true" if value else "bool:false"
    if value is None:
        return "none"
    raise ValueError(f"stable digest value {type(value).__name__} is not allowed")


def _require_digest(value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError("derived_validation_digest must be a 64 character string")
    allowed = set("0123456789abcdef")
    if any(ch not in allowed for ch in value):
        raise ValueError("derived_validation_digest must be lowercase hex")


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_ATTENTION_SKEW_SCORE_CONFIG_VERSION",
    "ATTENTION_SKEW_STATUSES",
    "CandidateDecisionAttentionSkewScoreConfig",
    "CandidateDecisionAttentionSkewScoreInput",
    "CandidateDecisionAttentionSkewScoreReport",
    "score_candidate_decision_attention_skew",
    "candidate_decision_attention_skew_score_payload",
    "validate_candidate_decision_attention_skew_score_public_payload",
)
