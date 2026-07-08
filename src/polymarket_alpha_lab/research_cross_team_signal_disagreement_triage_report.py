"""Pure public triage reducer for cross-team signal disagreement."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_CROSS_TEAM_SIGNAL_DISAGREEMENT_TRIAGE_CONFIG_VERSION = (
    "research-cross-team-signal-disagreement-triage-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_REASON_RANK = {
    "model_disagreement_block": 0,
    "signal_spread_block": 1,
    "freshness_block": 2,
    "insufficient_team_count": 3,
    "freshness_watch": 4,
    "model_disagreement_watch": 5,
    "signal_spread_watch": 6,
    "triage_score_block": 7,
    "triage_score_watch": 8,
    "cross_team_disagreement_triage_pass": 9,
    "empty_input": 10,
}
_PASS_REASON = "cross_team_disagreement_triage_pass"
_EMPTY_REASON = "empty_input"


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _surface_term("wa", "llet"),
        _surface_term("au", "th"),
        _surface_term("or", "der"),
        _surface_term("tra", "de"),
        _surface_term("private", "_", "key"),
        _surface_term("private", "-", "key"),
        _surface_term("private", " ", "key"),
        _surface_term("data", "base"),
        _surface_term("net", "work"),
        _surface_term("mut", "ation"),
        _surface_term("sign", "ing"),
        _surface_term("secret"),
        _surface_term("token"),
    ),
)


@dataclass(frozen=True)
class ResearchCrossTeamSignalDisagreementTriageConfig:
    config_version: str
    pass_triage_score: Decimal
    watch_triage_score: Decimal
    block_model_disagreement: Decimal
    block_signal_spread: Decimal
    watch_model_disagreement: Decimal
    watch_signal_spread: Decimal
    freshness_watch_age_hours: Decimal
    freshness_block_age_hours: Decimal
    min_team_count: Decimal
    confidence_weight: Decimal
    evidence_quality_weight: Decimal
    freshness_weight: Decimal
    model_agreement_weight: Decimal
    signal_agreement_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        for field_name in (
            "pass_triage_score",
            "watch_triage_score",
            "block_model_disagreement",
            "block_signal_spread",
            "watch_model_disagreement",
            "watch_signal_spread",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.pass_triage_score < self.watch_triage_score:
            raise ValueError("pass_triage_score must be at least watch_triage_score")
        if self.block_model_disagreement < self.watch_model_disagreement:
            raise ValueError(
                "block_model_disagreement must be at least watch_model_disagreement",
            )
        if self.block_signal_spread < self.watch_signal_spread:
            raise ValueError("block_signal_spread must be at least watch_signal_spread")
        for field_name in (
            "freshness_watch_age_hours",
            "freshness_block_age_hours",
            "min_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.freshness_block_age_hours < self.freshness_watch_age_hours:
            raise ValueError(
                "freshness_block_age_hours must be at least freshness_watch_age_hours",
            )
        for field_name in (
            "confidence_weight",
            "evidence_quality_weight",
            "freshness_weight",
            "model_agreement_weight",
            "signal_agreement_weight",
        ):
            value = _normalize_ratio(field_name, getattr(self, field_name))
            if value <= _ZERO:
                raise ValueError(f"{field_name} must be positive")
            object.__setattr__(self, field_name, value)
        _require_flags("config", self)


@dataclass(frozen=True)
class ResearchCrossTeamSignalDisagreementTriageInput:
    domain_key: str
    team_key: str
    aggregate_confidence: Decimal
    evidence_quality: Decimal
    freshness_age_hours: Decimal
    model_disagreement: Decimal
    signal_value: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("domain_key", self.domain_key)
        _require_text("team_key", self.team_key)
        for field_name in (
            "aggregate_confidence",
            "evidence_quality",
            "model_disagreement",
            "signal_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_age_hours",
            _normalize_nonnegative_decimal(
                "freshness_age_hours",
                self.freshness_age_hours,
            ),
        )
        _require_flags("input", self)


@dataclass(frozen=True)
class ResearchCrossTeamSignalDisagreementTriageRow:
    domain_digest: str
    status: str
    team_count: Decimal
    average_aggregate_confidence: Decimal
    average_evidence_quality: Decimal
    average_freshness_age_hours: Decimal
    freshness_score: Decimal
    average_model_disagreement: Decimal
    model_agreement_score: Decimal
    signal_spread: Decimal
    signal_agreement_score: Decimal
    triage_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_digest_label("domain_digest", self.domain_digest)
        _require_status("status", self.status)
        object.__setattr__(self, "team_count", _normalize_count("team_count", self.team_count))
        for field_name in (
            "average_aggregate_confidence",
            "average_evidence_quality",
            "freshness_score",
            "average_model_disagreement",
            "model_agreement_score",
            "signal_spread",
            "signal_agreement_score",
            "triage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_freshness_age_hours",
            _normalize_nonnegative_decimal(
                "average_freshness_age_hours",
                self.average_freshness_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags("row", self)


@dataclass(frozen=True)
class ResearchCrossTeamSignalDisagreementTriageReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_ratio("row_ratio", self.row_ratio),
        )
        _require_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchCrossTeamSignalDisagreementTriageReport:
    generated_at: datetime
    config_version: str
    status: str
    domain_count: Decimal
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_triage_score: Decimal
    max_model_disagreement: Decimal
    max_signal_spread: Decimal
    max_freshness_age_hours: Decimal
    min_team_count: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchCrossTeamSignalDisagreementTriageRow, ...]
    reason_code_counts: tuple[ResearchCrossTeamSignalDisagreementTriageReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "domain_count",
            "signal_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_triage_score",
            "max_model_disagreement",
            "max_signal_spread",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_freshness_age_hours", "min_team_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
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
        _check_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_cross_team_signal_disagreement_triage_report_payload(self)


def build_research_cross_team_signal_disagreement_triage_report(
    inputs: object,
    *,
    config: ResearchCrossTeamSignalDisagreementTriageConfig,
    generated_at: datetime,
) -> ResearchCrossTeamSignalDisagreementTriageReport:
    if type(config) is not ResearchCrossTeamSignalDisagreementTriageConfig:
        raise ValueError(
            "config must be a ResearchCrossTeamSignalDisagreementTriageConfig",
        )
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_for_domain(domain_key, domain_inputs, config=config)
                for domain_key, domain_inputs in _group_inputs(normalized_inputs)
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchCrossTeamSignalDisagreementTriageReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        domain_count=_count(len(rows)),
        signal_count=_count(len(normalized_inputs)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_triage_score=_average_or_zero(tuple(row.triage_score for row in rows)),
        max_model_disagreement=_max_or_zero(
            tuple(row.average_model_disagreement for row in rows),
        ),
        max_signal_spread=_max_or_zero(tuple(row.signal_spread for row in rows)),
        max_freshness_age_hours=_max_or_zero(
            tuple(row.average_freshness_age_hours for row in rows),
        ),
        min_team_count=_min_or_zero(tuple(row.team_count for row in rows)),
        reason_codes=reason_codes,
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
    )


def research_cross_team_signal_disagreement_triage_report_payload(
    report: ResearchCrossTeamSignalDisagreementTriageReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchCrossTeamSignalDisagreementTriageReport:
        _require_flags("report", report)
        _reject_unsafe_public("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public("payload", report)
        _reject_flag_downgrades("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchCrossTeamSignalDisagreementTriageReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_flags("payload", _DictFlags(payload))
    _reject_unsafe_public("payload", payload)
    _reject_flag_downgrades("payload", payload)
    _verify_payload_digest(payload)
    return payload


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


def _row_for_domain(
    domain_key: str,
    inputs: tuple[ResearchCrossTeamSignalDisagreementTriageInput, ...],
    *,
    config: ResearchCrossTeamSignalDisagreementTriageConfig,
) -> ResearchCrossTeamSignalDisagreementTriageRow:
    team_count = _count(len(inputs))
    average_confidence = _average(tuple(item.aggregate_confidence for item in inputs))
    average_evidence_quality = _average(tuple(item.evidence_quality for item in inputs))
    average_freshness_age = _average(tuple(item.freshness_age_hours for item in inputs))
    freshness_score = _freshness_score(average_freshness_age, config.freshness_block_age_hours)
    average_model_disagreement = _average(
        tuple(item.model_disagreement for item in inputs),
    )
    model_agreement_score = _clamp_ratio(_ONE - average_model_disagreement)
    signal_values = tuple(item.signal_value for item in inputs)
    signal_spread = _quantize(max(signal_values) - min(signal_values))
    signal_agreement_score = _clamp_ratio(_ONE - signal_spread)
    triage_score = _weighted_score(
        average_confidence=average_confidence,
        average_evidence_quality=average_evidence_quality,
        freshness_score=freshness_score,
        model_agreement_score=model_agreement_score,
        signal_agreement_score=signal_agreement_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        team_count=team_count,
        average_freshness_age=average_freshness_age,
        average_model_disagreement=average_model_disagreement,
        signal_spread=signal_spread,
        triage_score=triage_score,
        config=config,
    )
    return ResearchCrossTeamSignalDisagreementTriageRow(
        domain_digest=_digest_label(domain_key),
        status=_row_status(reason_codes),
        team_count=team_count,
        average_aggregate_confidence=average_confidence,
        average_evidence_quality=average_evidence_quality,
        average_freshness_age_hours=average_freshness_age,
        freshness_score=freshness_score,
        average_model_disagreement=average_model_disagreement,
        model_agreement_score=model_agreement_score,
        signal_spread=signal_spread,
        signal_agreement_score=signal_agreement_score,
        triage_score=triage_score,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    team_count: Decimal,
    average_freshness_age: Decimal,
    average_model_disagreement: Decimal,
    signal_spread: Decimal,
    triage_score: Decimal,
    config: ResearchCrossTeamSignalDisagreementTriageConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    model_blocked = average_model_disagreement >= config.block_model_disagreement
    signal_blocked = signal_spread >= config.block_signal_spread
    if model_blocked:
        reasons.append("model_disagreement_block")
    if signal_blocked:
        reasons.append("signal_spread_block")
    if average_freshness_age >= config.freshness_block_age_hours:
        reasons.append("freshness_block")
    if team_count < config.min_team_count:
        reasons.append("insufficient_team_count")
    if average_freshness_age >= config.freshness_watch_age_hours:
        reasons.append("freshness_watch")
    if not model_blocked and average_model_disagreement >= config.watch_model_disagreement:
        reasons.append("model_disagreement_watch")
    if not signal_blocked and signal_spread >= config.watch_signal_spread:
        reasons.append("signal_spread_watch")
    if triage_score < config.watch_triage_score:
        reasons.append("triage_score_block")
    elif triage_score < config.pass_triage_score:
        reasons.append("triage_score_watch")
    if not reasons:
        reasons.append(_PASS_REASON)
    return _sort_reason_codes(tuple(dict.fromkeys(reasons)))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if "insufficient_team_count" in reason_codes:
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchCrossTeamSignalDisagreementTriageRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchCrossTeamSignalDisagreementTriageRow, ...],
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
    rows: tuple[ResearchCrossTeamSignalDisagreementTriageRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchCrossTeamSignalDisagreementTriageReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchCrossTeamSignalDisagreementTriageReasonCodeCount(
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
        ResearchCrossTeamSignalDisagreementTriageReasonCodeCount(
            reason_code=reason,
            count=_count(counts[reason]),
            row_ratio=_ratio(_count(counts[reason]), denominator),
        )
        for reason in sorted(counts, key=_reason_key)
    )


def _normalize_inputs(
    inputs: object,
) -> tuple[ResearchCrossTeamSignalDisagreementTriageInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not ResearchCrossTeamSignalDisagreementTriageInput:
            raise ValueError(
                "inputs must contain ResearchCrossTeamSignalDisagreementTriageInput",
            )
        _require_flags("input", item)
        key = (item.domain_key, item.team_key)
        if key in seen:
            raise ValueError("inputs must contain unique domain_key and team_key values")
        seen.add(key)
    return items


def _group_inputs(
    inputs: tuple[ResearchCrossTeamSignalDisagreementTriageInput, ...],
) -> tuple[tuple[str, tuple[ResearchCrossTeamSignalDisagreementTriageInput, ...]], ...]:
    domain_keys = tuple(sorted({item.domain_key for item in inputs}))
    return tuple(
        (
            domain_key,
            tuple(
                sorted(
                    (item for item in inputs if item.domain_key == domain_key),
                    key=lambda item: item.team_key,
                ),
            ),
        )
        for domain_key in domain_keys
    )


def _weighted_score(
    *,
    average_confidence: Decimal,
    average_evidence_quality: Decimal,
    freshness_score: Decimal,
    model_agreement_score: Decimal,
    signal_agreement_score: Decimal,
    config: ResearchCrossTeamSignalDisagreementTriageConfig,
) -> Decimal:
    return _quantize(
        average_confidence * config.confidence_weight
        + average_evidence_quality * config.evidence_quality_weight
        + freshness_score * config.freshness_weight
        + model_agreement_score * config.model_agreement_weight
        + signal_agreement_score * config.signal_agreement_weight,
    )


def _freshness_score(age_hours: Decimal, block_age_hours: Decimal) -> Decimal:
    if age_hours >= block_age_hours:
        return _ZERO
    return _clamp_ratio(_ONE - _ratio(age_hours, block_age_hours))


def _status_count(
    rows: tuple[ResearchCrossTeamSignalDisagreementTriageRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _check_report(report: ResearchCrossTeamSignalDisagreementTriageReport) -> None:
    rows = report.rows
    if report.domain_count != _count(len(rows)):
        raise ValueError("domain_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.average_triage_score != _average_or_zero(tuple(row.triage_score for row in rows)):
        raise ValueError("average_triage_score must match rows")
    if report.max_model_disagreement != _max_or_zero(
        tuple(row.average_model_disagreement for row in rows),
    ):
        raise ValueError("max_model_disagreement must match rows")
    if report.max_signal_spread != _max_or_zero(tuple(row.signal_spread for row in rows)):
        raise ValueError("max_signal_spread must match rows")
    if report.max_freshness_age_hours != _max_or_zero(
        tuple(row.average_freshness_age_hours for row in rows),
    ):
        raise ValueError("max_freshness_age_hours must match rows")
    if report.min_team_count != _min_or_zero(tuple(row.team_count for row in rows)):
        raise ValueError("min_team_count must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchCrossTeamSignalDisagreementTriageRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchCrossTeamSignalDisagreementTriageRow:
            raise ValueError(
                "rows must contain ResearchCrossTeamSignalDisagreementTriageRow",
            )
        _require_flags("row", item)
    return items


def _normalize_reason_code_counts(
    reason_code_counts: object,
) -> tuple[ResearchCrossTeamSignalDisagreementTriageReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        items = tuple(reason_code_counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchCrossTeamSignalDisagreementTriageReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchCrossTeamSignalDisagreementTriageReasonCodeCount",
            )
        _require_flags("reason code count", item)
    return items


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
        _require_text(name, item)
        if item in seen:
            raise ValueError(f"{name} must not contain duplicates")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(reason_codes, key=_reason_key))


def _reason_key(reason_code: str) -> tuple[int, str]:
    return (_REASON_RANK.get(reason_code, len(_REASON_RANK)), reason_code)


def _row_sort_key(row: ResearchCrossTeamSignalDisagreementTriageRow) -> tuple[int, str]:
    return (_STATUS_RANK[row.status], row.domain_digest)


def _report_digest(report: ResearchCrossTeamSignalDisagreementTriageReport) -> str:
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
    encoded = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
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


def _min_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(min(values))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        raise ValueError("ratio denominator must be non-zero")
    return _quantize(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(_ONE, max(_ZERO, _quantize(value)))


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


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be non-negative")
    return normalized


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


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be non-empty without surrounding whitespace")
    if _has_unsafe_fragment(value):
        raise ValueError(f"unsafe value in {name}")


def _require_status(name: str, value: object) -> None:
    if value not in _STATUS_RANK:
        raise ValueError(f"{name} must be one of pass, watch, block")


def _require_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


__all__ = (
    "DEFAULT_RESEARCH_CROSS_TEAM_SIGNAL_DISAGREEMENT_TRIAGE_CONFIG_VERSION",
    "ResearchCrossTeamSignalDisagreementTriageConfig",
    "ResearchCrossTeamSignalDisagreementTriageInput",
    "ResearchCrossTeamSignalDisagreementTriageReasonCodeCount",
    "ResearchCrossTeamSignalDisagreementTriageReport",
    "ResearchCrossTeamSignalDisagreementTriageRow",
    "build_research_cross_team_signal_disagreement_triage_report",
    "research_cross_team_signal_disagreement_triage_report_payload",
)
