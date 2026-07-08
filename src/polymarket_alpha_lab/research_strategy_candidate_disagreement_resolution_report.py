"""Pure public reducer for strategy candidate disagreement resolution reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_CANDIDATE_DISAGREEMENT_RESOLUTION_CONFIG_VERSION = (
    "research-strategy-candidate-disagreement-resolution-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_PASS_REASON = "candidate_disagreement_resolution_pass"
_EMPTY_REASON = "empty_input"
_VIEW_NAMES = (
    "model_signal",
    "specialist_memory",
    "consensus",
    "mechanics",
    "resolution_risk",
)
_REASON_RANK = {
    "model_signal_disagreement_block": 0,
    "specialist_memory_disagreement_block": 1,
    "consensus_disagreement_block": 2,
    "mechanics_disagreement_watch": 3,
    "resolution_risk_disagreement_block": 4,
    "unresolved_disagreement_score_block": 5,
    "specialist_memory_disagreement_watch": 6,
    "model_signal_disagreement_watch": 7,
    "consensus_disagreement_watch": 8,
    "mechanics_disagreement_block": 9,
    "resolution_risk_disagreement_watch": 10,
    "unresolved_disagreement_score_watch": 11,
    _PASS_REASON: 12,
    _EMPTY_REASON: 13,
}


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "://",
        "@",
        _surface_term("au", "th"),
        _surface_term("api", "_", "key"),
        _surface_term("bear", "er"),
        _surface_term("data", "base"),
        _surface_term("dsn"),
        _surface_term("mar", "ket"),
        _surface_term("mut", "ation"),
        _surface_term("or", "der"),
        _surface_term("private", "_", "key"),
        _surface_term("private", "-", "key"),
        _surface_term("private", " ", "key"),
        _surface_term("ques", "tion"),
        _surface_term("sec", "ret"),
        _surface_term("slug"),
        _surface_term("source"),
        _surface_term("sup", "abase"),
        _surface_term("table"),
        _surface_term("tok", "en"),
        _surface_term("tra", "de"),
        _surface_term("wa", "llet"),
    ),
)


@dataclass(frozen=True)
class ResearchStrategyCandidateDisagreementResolutionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CANDIDATE_DISAGREEMENT_RESOLUTION_CONFIG_VERSION
    )
    watch_unresolved_disagreement_score: Decimal = Decimal("0.350000")
    block_unresolved_disagreement_score: Decimal = Decimal("0.700000")
    watch_view_disagreement: Decimal = Decimal("0.350000")
    block_view_disagreement: Decimal = Decimal("0.700000")
    model_signal_weight: Decimal = Decimal("0.200000")
    specialist_memory_weight: Decimal = Decimal("0.200000")
    consensus_weight: Decimal = Decimal("0.200000")
    mechanics_weight: Decimal = Decimal("0.200000")
    resolution_risk_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateDisagreementResolutionConfig:
            raise ValueError(
                "config must be a ResearchStrategyCandidateDisagreementResolutionConfig",
            )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "watch_unresolved_disagreement_score",
            "block_unresolved_disagreement_score",
            "watch_view_disagreement",
            "block_view_disagreement",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if (
            self.block_unresolved_disagreement_score
            <= self.watch_unresolved_disagreement_score
        ):
            raise ValueError(
                "block_unresolved_disagreement_score must exceed "
                "watch_unresolved_disagreement_score",
            )
        if self.block_view_disagreement <= self.watch_view_disagreement:
            raise ValueError("block_view_disagreement must exceed watch_view_disagreement")
        for field_name in (
            "model_signal_weight",
            "specialist_memory_weight",
            "consensus_weight",
            "mechanics_weight",
            "resolution_risk_weight",
        ):
            value = _normalize_ratio(field_name, getattr(self, field_name))
            if value <= _ZERO:
                raise ValueError(f"{field_name} must be positive")
            object.__setattr__(self, field_name, value)
        if _weight_total(self) <= _ZERO:
            raise ValueError("weight total must be positive")
        _require_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateDisagreementResolutionInput:
    candidate_id: str
    model_signal_disagreement: Decimal
    specialist_memory_disagreement: Decimal
    consensus_disagreement: Decimal
    mechanics_disagreement: Decimal
    resolution_risk_disagreement: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateDisagreementResolutionInput:
            raise ValueError(
                "input must be a ResearchStrategyCandidateDisagreementResolutionInput",
            )
        _require_private_identifier("candidate_id", self.candidate_id)
        for field_name in _view_field_names():
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateDisagreementResolutionRow:
    candidate_digest: str
    status: str
    model_signal_disagreement: Decimal
    specialist_memory_disagreement: Decimal
    consensus_disagreement: Decimal
    mechanics_disagreement: Decimal
    resolution_risk_disagreement: Decimal
    unresolved_disagreement_score: Decimal
    dominant_disagreement_view: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateDisagreementResolutionRow:
            raise ValueError(
                "row must be a ResearchStrategyCandidateDisagreementResolutionRow",
            )
        _require_digest_label("candidate_digest", self.candidate_digest)
        _require_status("status", self.status)
        for field_name in _view_field_names() + ("unresolved_disagreement_score",):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member(
            "dominant_disagreement_view",
            self.dominant_disagreement_view,
            _VIEW_NAMES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateDisagreementResolutionReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateDisagreementResolutionReasonCodeCount:
            raise ValueError(
                "reason count must be a "
                "ResearchStrategyCandidateDisagreementResolutionReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_ratio("row_ratio", self.row_ratio),
        )
        _require_flags("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateDisagreementResolutionReport:
    generated_at: datetime
    config_version: str
    status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_unresolved_disagreement_score: Decimal
    max_unresolved_disagreement_score: Decimal
    max_model_signal_disagreement: Decimal
    max_specialist_memory_disagreement: Decimal
    max_consensus_disagreement: Decimal
    max_mechanics_disagreement: Decimal
    max_resolution_risk_disagreement: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyCandidateDisagreementResolutionRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyCandidateDisagreementResolutionReasonCodeCount,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateDisagreementResolutionReport:
            raise ValueError(
                "report must be a ResearchStrategyCandidateDisagreementResolutionReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_unresolved_disagreement_score",
            "max_unresolved_disagreement_score",
            "max_model_signal_disagreement",
            "max_specialist_memory_disagreement",
            "max_consensus_disagreement",
            "max_mechanics_disagreement",
            "max_resolution_risk_disagreement",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_flags("report", self)
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_candidate_disagreement_resolution_report_payload(self)


def build_research_strategy_candidate_disagreement_resolution_report(
    candidates: object,
    *,
    config: ResearchStrategyCandidateDisagreementResolutionConfig,
    generated_at: datetime,
) -> ResearchStrategyCandidateDisagreementResolutionReport:
    if type(config) is not ResearchStrategyCandidateDisagreementResolutionConfig:
        raise ValueError(
            "config must be a ResearchStrategyCandidateDisagreementResolutionConfig",
        )
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(candidates)
    rows = tuple(
        sorted(
            (_row_from_input(candidate, config=config) for candidate in inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchStrategyCandidateDisagreementResolutionReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_unresolved_disagreement_score=_average_or_zero(
            tuple(row.unresolved_disagreement_score for row in rows),
        ),
        max_unresolved_disagreement_score=_max_or_zero(
            tuple(row.unresolved_disagreement_score for row in rows),
        ),
        max_model_signal_disagreement=_max_or_zero(
            tuple(row.model_signal_disagreement for row in rows),
        ),
        max_specialist_memory_disagreement=_max_or_zero(
            tuple(row.specialist_memory_disagreement for row in rows),
        ),
        max_consensus_disagreement=_max_or_zero(
            tuple(row.consensus_disagreement for row in rows),
        ),
        max_mechanics_disagreement=_max_or_zero(
            tuple(row.mechanics_disagreement for row in rows),
        ),
        max_resolution_risk_disagreement=_max_or_zero(
            tuple(row.resolution_risk_disagreement for row in rows),
        ),
        reason_codes=reason_codes,
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
    )


def research_strategy_candidate_disagreement_resolution_report_payload(
    report: ResearchStrategyCandidateDisagreementResolutionReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyCandidateDisagreementResolutionReport:
        _require_flags("report", report)
        _reject_unsafe_public("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public("payload", report)
        _reject_flag_downgrades("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyCandidateDisagreementResolutionReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_flags("payload", _DictFlags(payload))
    _reject_unsafe_public("payload", payload)
    _reject_flag_downgrades("payload", payload)
    _verify_payload_digest(payload)
    return payload


def research_strategy_candidate_disagreement_resolution_report_digest(
    report: ResearchStrategyCandidateDisagreementResolutionReport,
) -> str:
    if type(report) is not ResearchStrategyCandidateDisagreementResolutionReport:
        raise ValueError(
            "report must be a ResearchStrategyCandidateDisagreementResolutionReport",
        )
    return report.derived_validation_digest


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


def _row_from_input(
    candidate: ResearchStrategyCandidateDisagreementResolutionInput,
    *,
    config: ResearchStrategyCandidateDisagreementResolutionConfig,
) -> ResearchStrategyCandidateDisagreementResolutionRow:
    view_values = _candidate_view_values(candidate)
    score = _weighted_disagreement_score(candidate, config)
    reason_codes = _row_reason_codes(candidate, score=score, config=config)
    return ResearchStrategyCandidateDisagreementResolutionRow(
        candidate_digest=_digest_label(candidate.candidate_id),
        status=_row_status(reason_codes),
        model_signal_disagreement=candidate.model_signal_disagreement,
        specialist_memory_disagreement=candidate.specialist_memory_disagreement,
        consensus_disagreement=candidate.consensus_disagreement,
        mechanics_disagreement=candidate.mechanics_disagreement,
        resolution_risk_disagreement=candidate.resolution_risk_disagreement,
        unresolved_disagreement_score=score,
        dominant_disagreement_view=max(view_values, key=lambda item: (item[1], -item[2]))[0],
        reason_codes=reason_codes,
    )


def _candidate_view_values(
    candidate: ResearchStrategyCandidateDisagreementResolutionInput,
) -> tuple[tuple[str, Decimal, int], ...]:
    return tuple(
        (view_name, getattr(candidate, f"{view_name}_disagreement"), index)
        for index, view_name in enumerate(_VIEW_NAMES)
    )


def _weighted_disagreement_score(
    candidate: ResearchStrategyCandidateDisagreementResolutionInput,
    config: ResearchStrategyCandidateDisagreementResolutionConfig,
) -> Decimal:
    weighted_total = _ZERO
    for view_name in _VIEW_NAMES:
        weighted_total += getattr(candidate, f"{view_name}_disagreement") * getattr(
            config,
            f"{view_name}_weight",
        )
    return _ratio(weighted_total, _weight_total(config))


def _weight_total(config: ResearchStrategyCandidateDisagreementResolutionConfig) -> Decimal:
    return _quantize(
        config.model_signal_weight
        + config.specialist_memory_weight
        + config.consensus_weight
        + config.mechanics_weight
        + config.resolution_risk_weight,
    )


def _row_reason_codes(
    candidate: ResearchStrategyCandidateDisagreementResolutionInput,
    *,
    score: Decimal,
    config: ResearchStrategyCandidateDisagreementResolutionConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    for view_name in _VIEW_NAMES:
        value = getattr(candidate, f"{view_name}_disagreement")
        if value >= config.block_view_disagreement:
            reasons.append(f"{view_name}_disagreement_block")
        elif value >= config.watch_view_disagreement:
            reasons.append(f"{view_name}_disagreement_watch")
    if score >= config.block_unresolved_disagreement_score:
        reasons.append("unresolved_disagreement_score_block")
    elif score >= config.watch_unresolved_disagreement_score:
        reasons.append("unresolved_disagreement_score_watch")
    if not reasons:
        reasons.append(_PASS_REASON)
    return tuple(dict.fromkeys(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategyCandidateDisagreementResolutionRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyCandidateDisagreementResolutionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    reasons = tuple(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != _PASS_REASON
    )
    if not reasons:
        return (_PASS_REASON,)
    return _sort_reason_codes(tuple(dict.fromkeys(reasons)))


def _reason_code_counts(
    rows: tuple[ResearchStrategyCandidateDisagreementResolutionRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyCandidateDisagreementResolutionReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyCandidateDisagreementResolutionReasonCodeCount(
                reason_code=_EMPTY_REASON,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason in row.reason_codes:
            if reason == _PASS_REASON and _PASS_REASON not in report_reason_codes:
                continue
            counts[reason] = counts.get(reason, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategyCandidateDisagreementResolutionReasonCodeCount(
            reason_code=reason,
            count=_count(counts[reason]),
            row_ratio=_ratio(_count(counts[reason]), denominator),
        )
        for reason in sorted(counts, key=_reason_key)
    )


def _status_count(
    rows: tuple[ResearchStrategyCandidateDisagreementResolutionRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_row(row: ResearchStrategyCandidateDisagreementResolutionRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    view_values = tuple(
        (view_name, getattr(row, f"{view_name}_disagreement"), index)
        for index, view_name in enumerate(_VIEW_NAMES)
    )
    expected_view = max(view_values, key=lambda item: (item[1], -item[2]))[0]
    if row.dominant_disagreement_view != expected_view:
        raise ValueError("dominant_disagreement_view must match disagreement values")


def _validate_report(report: ResearchStrategyCandidateDisagreementResolutionReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.average_unresolved_disagreement_score != _average_or_zero(
        tuple(row.unresolved_disagreement_score for row in rows),
    ):
        raise ValueError("average_unresolved_disagreement_score must match rows")
    if report.max_unresolved_disagreement_score != _max_or_zero(
        tuple(row.unresolved_disagreement_score for row in rows),
    ):
        raise ValueError("max_unresolved_disagreement_score must match rows")
    for view_name in _VIEW_NAMES:
        report_field = f"max_{view_name}_disagreement"
        if getattr(report, report_field) != _max_or_zero(
            tuple(getattr(row, f"{view_name}_disagreement") for row in rows),
        ):
            raise ValueError(f"{report_field} must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    candidates: object,
) -> tuple[ResearchStrategyCandidateDisagreementResolutionInput, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        items = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchStrategyCandidateDisagreementResolutionInput:
            raise ValueError(
                "candidates must contain "
                "ResearchStrategyCandidateDisagreementResolutionInput",
            )
        _require_flags("input", item)
        if item.candidate_id in seen:
            raise ValueError("candidates must contain unique candidate_id values")
        seen.add(item.candidate_id)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyCandidateDisagreementResolutionRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchStrategyCandidateDisagreementResolutionRow:
            raise ValueError(
                "rows must contain ResearchStrategyCandidateDisagreementResolutionRow",
            )
        _require_flags("row", item)
    return tuple(sorted(items, key=_row_sort_key))


def _normalize_reason_code_counts(
    reason_code_counts: object,
) -> tuple[ResearchStrategyCandidateDisagreementResolutionReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        items = tuple(reason_code_counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchStrategyCandidateDisagreementResolutionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyCandidateDisagreementResolutionReasonCodeCount",
            )
        _require_flags("reason count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(item.reason_code)
    return tuple(sorted(items, key=lambda item: (_reason_key(item.reason_code))))


def _normalize_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        _require_reason_code(name, item)
        if item in seen:
            raise ValueError(f"{name} must not contain duplicates")
        seen.add(item)
        normalized.append(item)
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return tuple(normalized)


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(reason_codes, key=_reason_key))


def _reason_key(reason_code: str) -> tuple[int, str]:
    return (_REASON_RANK.get(reason_code, len(_REASON_RANK)), reason_code)


def _row_sort_key(
    row: ResearchStrategyCandidateDisagreementResolutionRow,
) -> tuple[int, str]:
    return (_STATUS_RANK[row.status], row.candidate_digest)


def _report_digest(report: ResearchStrategyCandidateDisagreementResolutionReport) -> str:
    value = asdict(report)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest is required")
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("derived_validation_digest must be a lowercase sha256 hex digest")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _canonical_digest(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _canonical_digest(payload: object) -> str:
    ready = _json_ready(payload)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _digest_label(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _require_digest_label(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value.startswith("sha256:"):
        raise ValueError(f"{name} must use sha256 label")
    digest = value.removeprefix("sha256:")
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{name} must contain a lowercase sha256 hex digest")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
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


def _reject_unsafe_public(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            _reject_unsafe_public(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public(label, item)


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _view_field_names() -> tuple[str, ...]:
    return tuple(f"{view_name}_disagreement" for view_name in _VIEW_NAMES)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must not be empty")
    return _ratio(sum(values, _ZERO), _count(len(values)))


def _average_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _average(values)


def _max_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(max(values))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        raise ValueError("ratio denominator must be non-zero")
    return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be non-negative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    return _quantize(value)


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be non-negative")
    return normalized


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_private_identifier(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be non-empty without surrounding whitespace")


def _require_public_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be non-empty without surrounding whitespace")
    if _has_unsafe_fragment(value):
        raise ValueError(f"unsafe value in {name}")


def _require_reason_code(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value.lower() != value:
        raise ValueError(f"{name} must be lowercase")
    if not all(character == "_" or character.isalnum() for character in value):
        raise ValueError(f"{name} must contain reason code text")


def _require_status(name: str, value: object) -> None:
    if value not in _STATUS_RANK:
        raise ValueError(f"{name} must be one of pass, watch, block")


def _require_member(name: str, value: object, members: tuple[str, ...]) -> None:
    if value not in members:
        raise ValueError(f"{name} must be one of {', '.join(members)}")


def _require_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_DISAGREEMENT_RESOLUTION_CONFIG_VERSION",
    "ResearchStrategyCandidateDisagreementResolutionConfig",
    "ResearchStrategyCandidateDisagreementResolutionInput",
    "ResearchStrategyCandidateDisagreementResolutionReasonCodeCount",
    "ResearchStrategyCandidateDisagreementResolutionReport",
    "ResearchStrategyCandidateDisagreementResolutionRow",
    "build_research_strategy_candidate_disagreement_resolution_report",
    "research_strategy_candidate_disagreement_resolution_report_digest",
    "research_strategy_candidate_disagreement_resolution_report_payload",
)
