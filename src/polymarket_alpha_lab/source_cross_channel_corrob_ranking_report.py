"""Pure readonly cross-channel source corroboration ranking report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_STATUS_VALUES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_REASON_CODE_SEQUENCE = (
    "cross_channel_conflict_detected",
    "official_channel_missing",
    "independent_channel_missing",
    "matching_channel_quorum_missing",
    "fresh_channel_quorum_missing",
    "cross_channel_corroboration_pass",
)
_MANUAL_NEXT_STEPS = frozenset(
    (
        "manual_cross_channel_conflict_review",
        "collect_official_channel_source",
        "collect_independent_channel_source",
        "collect_matching_cross_channel_evidence",
        "refresh_cross_channel_source_evidence",
        "document_cross_channel_source_ranking",
    ),
)


@dataclass(frozen=True)
class SourceCrossChannelCorrobRankingReport:
    official_channel_count: Decimal
    independent_channel_count: Decimal
    matching_channel_count: Decimal
    conflicting_channel_count: Decimal
    fresh_channel_count: Decimal
    corroboration_status: str
    corroboration_score_probability: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SourceCrossChannelCorrobRankingReport:
            raise TypeError(
                "SourceCrossChannelCorrobRankingReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SourceCrossChannelCorrobRankingReport:
            raise ValueError("report must be exactly SourceCrossChannelCorrobRankingReport")
        for field_name in (
            "official_channel_count",
            "independent_channel_count",
            "matching_channel_count",
            "conflicting_channel_count",
            "fresh_channel_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("corroboration_status", self.corroboration_status)
        object.__setattr__(
            self,
            "corroboration_score_probability",
            _require_probability_decimal(
                "corroboration_score_probability",
                self.corroboration_score_probability,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        _require_payload_digest("payload_digest", self.payload_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        if self.payload_digest != _report_digest(self):
            raise ValueError("payload_digest mismatch")

    @property
    def public_payload(self) -> dict[str, Any]:
        return source_cross_channel_corrob_ranking_report_payload(self)


def build_source_cross_channel_corrob_ranking_report(
    *,
    official_channel_count: Decimal,
    independent_channel_count: Decimal,
    matching_channel_count: Decimal,
    conflicting_channel_count: Decimal,
    fresh_channel_count: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> SourceCrossChannelCorrobRankingReport:
    official_count = _require_count_decimal(
        "official_channel_count",
        official_channel_count,
    )
    independent_count = _require_count_decimal(
        "independent_channel_count",
        independent_channel_count,
    )
    matching_count = _require_count_decimal("matching_channel_count", matching_channel_count)
    conflict_count = _require_count_decimal(
        "conflicting_channel_count",
        conflicting_channel_count,
    )
    fresh_count = _require_count_decimal("fresh_channel_count", fresh_channel_count)
    flags = _PhaseFlags(paper_only=paper_only, report_only=report_only, readonly=readonly)
    _require_hard_flags("builder", flags)

    _validate_counts(
        official_channel_count=official_count,
        independent_channel_count=independent_count,
        matching_channel_count=matching_count,
        conflicting_channel_count=conflict_count,
        fresh_channel_count=fresh_count,
    )
    reason_codes = _reason_codes(
        official_channel_count=official_count,
        independent_channel_count=independent_count,
        matching_channel_count=matching_count,
        conflicting_channel_count=conflict_count,
        fresh_channel_count=fresh_count,
    )
    status = _status(reason_codes)
    score = _corroboration_score_probability(
        official_channel_count=official_count,
        independent_channel_count=independent_count,
        matching_channel_count=matching_count,
        conflicting_channel_count=conflict_count,
        fresh_channel_count=fresh_count,
    )
    values: dict[str, Any] = {
        "official_channel_count": official_count,
        "independent_channel_count": independent_count,
        "matching_channel_count": matching_count,
        "conflicting_channel_count": conflict_count,
        "fresh_channel_count": fresh_count,
        "corroboration_status": status,
        "corroboration_score_probability": score,
        "reason_codes": reason_codes,
        "manual_next_step": _manual_next_step(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return SourceCrossChannelCorrobRankingReport(
        **values,
        payload_digest=_digest_from_values(values),
    )


def source_cross_channel_corrob_ranking_report_payload(
    value: SourceCrossChannelCorrobRankingReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is SourceCrossChannelCorrobRankingReport:
        _require_hard_flags("report", value)
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a SourceCrossChannelCorrobRankingReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _verify_payload_digest(payload)
    return payload


@dataclass(frozen=True)
class _PhaseFlags:
    paper_only: bool
    report_only: bool
    readonly: bool


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _reason_codes(
    *,
    official_channel_count: Decimal,
    independent_channel_count: Decimal,
    matching_channel_count: Decimal,
    conflicting_channel_count: Decimal,
    fresh_channel_count: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if conflicting_channel_count > _ZERO:
        codes.append("cross_channel_conflict_detected")
    if official_channel_count == _ZERO:
        codes.append("official_channel_missing")
    if independent_channel_count == _ZERO:
        codes.append("independent_channel_missing")
    if matching_channel_count < Decimal("2.000000"):
        codes.append("matching_channel_quorum_missing")
    if fresh_channel_count < matching_channel_count:
        codes.append("fresh_channel_quorum_missing")
    if not codes:
        codes.append("cross_channel_corroboration_pass")
    return _normalize_reason_codes(codes)


def _status(reason_codes: tuple[str, ...]) -> str:
    if "cross_channel_conflict_detected" in reason_codes:
        return "block"
    if reason_codes != ("cross_channel_corroboration_pass",):
        return "watch"
    return "pass"


def _manual_next_step(reason_codes: tuple[str, ...]) -> str:
    if "cross_channel_conflict_detected" in reason_codes:
        return "manual_cross_channel_conflict_review"
    if "official_channel_missing" in reason_codes:
        return "collect_official_channel_source"
    if "independent_channel_missing" in reason_codes:
        return "collect_independent_channel_source"
    if "matching_channel_quorum_missing" in reason_codes:
        return "collect_matching_cross_channel_evidence"
    if "fresh_channel_quorum_missing" in reason_codes:
        return "refresh_cross_channel_source_evidence"
    return "document_cross_channel_source_ranking"


def _corroboration_score_probability(
    *,
    official_channel_count: Decimal,
    independent_channel_count: Decimal,
    matching_channel_count: Decimal,
    conflicting_channel_count: Decimal,
    fresh_channel_count: Decimal,
) -> Decimal:
    source_channel_count = official_channel_count + independent_channel_count
    total_channel_count = source_channel_count + conflicting_channel_count
    if total_channel_count == _ZERO or matching_channel_count == _ZERO:
        return _ZERO
    match_share = matching_channel_count / total_channel_count
    fresh_share = fresh_channel_count / matching_channel_count
    diversity_score = _ONE
    if official_channel_count == _ZERO or independent_channel_count == _ZERO:
        diversity_score = Decimal("0.666667")
    score = min(match_share, fresh_share, diversity_score)
    return _require_probability_decimal("corroboration_score_probability", score)


def _validate_report_consistency(report: SourceCrossChannelCorrobRankingReport) -> None:
    _validate_counts(
        official_channel_count=report.official_channel_count,
        independent_channel_count=report.independent_channel_count,
        matching_channel_count=report.matching_channel_count,
        conflicting_channel_count=report.conflicting_channel_count,
        fresh_channel_count=report.fresh_channel_count,
    )
    expected_reasons = _reason_codes(
        official_channel_count=report.official_channel_count,
        independent_channel_count=report.independent_channel_count,
        matching_channel_count=report.matching_channel_count,
        conflicting_channel_count=report.conflicting_channel_count,
        fresh_channel_count=report.fresh_channel_count,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match cross-channel counts")
    if report.corroboration_status != _status(expected_reasons):
        raise ValueError("corroboration_status must match reason_codes")
    expected_score = _corroboration_score_probability(
        official_channel_count=report.official_channel_count,
        independent_channel_count=report.independent_channel_count,
        matching_channel_count=report.matching_channel_count,
        conflicting_channel_count=report.conflicting_channel_count,
        fresh_channel_count=report.fresh_channel_count,
    )
    if report.corroboration_score_probability != expected_score:
        raise ValueError("corroboration_score_probability must match counts")
    if report.manual_next_step != _manual_next_step(expected_reasons):
        raise ValueError("manual_next_step must match reason_codes")


def _validate_counts(
    *,
    official_channel_count: Decimal,
    independent_channel_count: Decimal,
    matching_channel_count: Decimal,
    conflicting_channel_count: Decimal,
    fresh_channel_count: Decimal,
) -> None:
    source_channel_count = official_channel_count + independent_channel_count
    if matching_channel_count > source_channel_count:
        raise ValueError("matching_channel_count must not exceed channel counts")
    if conflicting_channel_count >= source_channel_count and conflicting_channel_count > _ZERO:
        raise ValueError("conflicting_channel_count must not exceed channel counts")
    if fresh_channel_count > matching_channel_count + conflicting_channel_count:
        raise ValueError("fresh_channel_count must not exceed corroborating channel counts")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(_QUANT, rounding=ROUND_HALF_UP)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(_QUANT, rounding=ROUND_HALF_UP)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_code must be a string")
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _require_manual_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be supported")


def _require_payload_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _report_digest(report: SourceCrossChannelCorrobRankingReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    payload.pop("payload_digest", None)
    return _digest_from_values(payload)


def _digest_from_values(values: Mapping[str, Any]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    payload.pop("payload_digest", None)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("payload_digest")
    _require_payload_digest("payload_digest", digest)
    expected = _digest_from_values(payload)
    if digest != expected:
        raise ValueError("payload_digest mismatch")


def _copy_json_object(value: dict[str, Any]) -> dict[str, Any]:
    ready = _json_ready(value)
    if type(ready) is not dict:
        raise ValueError("public payload must be a JSON object")
    return ready


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value.quantize(_QUANT, rounding=ROUND_HALF_UP))
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


__all__ = (
    "SourceCrossChannelCorrobRankingReport",
    "build_source_cross_channel_corrob_ranking_report",
    "source_cross_channel_corrob_ranking_report_payload",
)
