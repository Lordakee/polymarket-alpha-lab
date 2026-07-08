"""Pure public event evidence revision risk report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "ResearchEventEvidenceRevisionRiskConfig",
    "ResearchEventEvidenceRevisionRiskObservation",
    "ResearchEventEvidenceRevisionRiskReasonCodeCount",
    "ResearchEventEvidenceRevisionRiskReport",
    "ResearchEventEvidenceRevisionRiskRow",
    "build_research_event_evidence_revision_risk_report",
    "research_event_evidence_revision_risk_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-event-evidence-revision-risk-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "block": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")
UNSAFE_PUBLIC_FRAGMENTS = (
    "r" + "aw",
    "mar" + "ket",
    "sou" + "rce",
    "u" + "rl",
    "wallet",
    "auth",
    "or" + "der",
    "tr" + "ade",
    "b" + "uy",
    "se" + "ll",
    "recom" + "mend",
    "siz" + "ing",
    "token",
    "private_key",
    "://",
    "@",
    "?",
)


class _Missing:
    pass


_MISSING = _Missing()


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchEventEvidenceRevisionRiskConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_stale_evidence_seconds: Decimal = Decimal("21600")
    watch_materiality_score: Decimal = Decimal("0.300000")
    block_materiality_score: Decimal = Decimal("0.700000")
    watch_contradiction_pressure_score: Decimal = Decimal("0.300000")
    block_contradiction_pressure_score: Decimal = Decimal("0.700000")
    watch_manual_review_urgency_score: Decimal = Decimal("0.300000")
    block_manual_review_urgency_score: Decimal = Decimal("0.700000")
    watch_revision_risk_score: Decimal = Decimal("0.300000")
    block_revision_risk_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventEvidenceRevisionRiskConfig, "config")
        _require_public_label("config_version", self.config_version)
        object.__setattr__(
            self,
            "watch_stale_evidence_seconds",
            _require_positive_decimal(
                "watch_stale_evidence_seconds",
                self.watch_stale_evidence_seconds,
            ),
        )
        for field_name in (
            "watch_materiality_score",
            "block_materiality_score",
            "watch_contradiction_pressure_score",
            "block_contradiction_pressure_score",
            "watch_manual_review_urgency_score",
            "block_manual_review_urgency_score",
            "watch_revision_risk_score",
            "block_revision_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventEvidenceRevisionRiskObservation(_FinalPublicDataclass):
    event_label: str
    evidence_version_label: str
    observed_at: datetime
    claim_materiality_score: Decimal
    contradiction_pressure_score: Decimal
    conflicting_update: bool = False
    unresolved_contradiction: bool = False
    manual_review_signal: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventEvidenceRevisionRiskObservation, "observation")
        _require_public_label("event_label", self.event_label)
        _require_public_label("evidence_version_label", self.evidence_version_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("claim_materiality_score", "contradiction_pressure_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "conflicting_update",
            "unresolved_contradiction",
            "manual_review_signal",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchEventEvidenceRevisionRiskRow(_FinalPublicDataclass):
    event_label: str
    evidence_update_count: Decimal
    conflicting_update_count: Decimal
    stale_evidence_update_count: Decimal
    material_change_count: Decimal
    unresolved_contradiction_count: Decimal
    manual_review_signal_count: Decimal
    latest_observed_at: datetime
    latest_evidence_age_seconds: Decimal
    max_evidence_age_seconds: Decimal
    claim_materiality_score: Decimal
    contradiction_pressure_score: Decimal
    manual_review_urgency_score: Decimal
    revision_risk_score: Decimal
    status: str
    evidence_version_labels: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventEvidenceRevisionRiskRow, "row")
        _require_public_label("event_label", self.event_label)
        for field_name in (
            "evidence_update_count",
            "conflicting_update_count",
            "stale_evidence_update_count",
            "material_change_count",
            "unresolved_contradiction_count",
            "manual_review_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in ("latest_evidence_age_seconds", "max_evidence_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "claim_materiality_score",
            "contradiction_pressure_score",
            "manual_review_urgency_score",
            "revision_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "evidence_version_labels",
            _normalize_public_label_tuple(
                "evidence_version_labels",
                self.evidence_version_labels,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row_materialized_fields(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventEvidenceRevisionRiskReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventEvidenceRevisionRiskReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventEvidenceRevisionRiskReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    event_count: Decimal
    evidence_update_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    conflicting_update_count: Decimal
    stale_evidence_update_count: Decimal
    material_change_count: Decimal
    unresolved_contradiction_count: Decimal
    manual_review_signal_count: Decimal
    status: str
    rows: tuple[ResearchEventEvidenceRevisionRiskRow, ...]
    reason_code_counts: tuple[ResearchEventEvidenceRevisionRiskReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventEvidenceRevisionRiskReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "event_count",
            "evidence_update_count",
            "pass_count",
            "watch_count",
            "block_count",
            "conflicting_update_count",
            "stale_evidence_update_count",
            "material_change_count",
            "unresolved_contradiction_count",
            "manual_review_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report_materialized_fields(self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)


def build_research_event_evidence_revision_risk_report(
    observations: Iterable[object],
    *,
    config: ResearchEventEvidenceRevisionRiskConfig,
    generated_at: datetime,
) -> ResearchEventEvidenceRevisionRiskReport:
    if type(config) is not ResearchEventEvidenceRevisionRiskConfig:
        raise ValueError("config must be a ResearchEventEvidenceRevisionRiskConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observation_items = _normalize_observations(observations)
    for item in observation_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must be <= generated_at")

    grouped: dict[str, list[ResearchEventEvidenceRevisionRiskObservation]] = {}
    for item in observation_items:
        grouped.setdefault(item.event_label, []).append(item)

    rows = tuple(
        sorted(
            (
                _row_from_observations(
                    event_label=event_label,
                    observations=tuple(grouped[event_label]),
                    config=config,
                    generated_at=generated_at_utc,
                )
                for event_label in sorted(grouped)
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchEventEvidenceRevisionRiskReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_count(len(rows)),
        evidence_update_count=sum((row.evidence_update_count for row in rows), ZERO),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        conflicting_update_count=sum((row.conflicting_update_count for row in rows), ZERO),
        stale_evidence_update_count=sum(
            (row.stale_evidence_update_count for row in rows),
            ZERO,
        ),
        material_change_count=sum((row.material_change_count for row in rows), ZERO),
        unresolved_contradiction_count=sum(
            (row.unresolved_contradiction_count for row in rows),
            ZERO,
        ),
        manual_review_signal_count=sum(
            (row.manual_review_signal_count for row in rows),
            ZERO,
        ),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_summary_reason_codes(rows),
    )


def research_event_evidence_revision_risk_report_payload(
    report: ResearchEventEvidenceRevisionRiskReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventEvidenceRevisionRiskReport:
        _require_hard_flags("report", report)
        _validate_report_materialized_fields(report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        supplied_digest = payload.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError("report must be a ResearchEventEvidenceRevisionRiskReport")


@dataclass(frozen=True)
class _PayloadFlags:
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


def _row_from_observations(
    *,
    event_label: str,
    observations: tuple[ResearchEventEvidenceRevisionRiskObservation, ...],
    config: ResearchEventEvidenceRevisionRiskConfig,
    generated_at: datetime,
) -> ResearchEventEvidenceRevisionRiskRow:
    ordered = tuple(sorted(observations, key=lambda item: item.evidence_version_label))
    evidence_update_count = _count(len(ordered))
    ages = tuple(_age_seconds(item.observed_at, generated_at) for item in ordered)
    stale_count = _count(
        sum(1 for age in ages if age > config.watch_stale_evidence_seconds),
    )
    conflicting_count = _count(sum(1 for item in ordered if item.conflicting_update))
    unresolved_count = _count(sum(1 for item in ordered if item.unresolved_contradiction))
    manual_count = _count(sum(1 for item in ordered if item.manual_review_signal))
    material_count = _count(
        sum(
            1
            for item in ordered
            if item.claim_materiality_score > config.watch_materiality_score
        ),
    )
    claim_materiality_score = max(item.claim_materiality_score for item in ordered)
    contradiction_pressure_score = max(
        (item.contradiction_pressure_score for item in ordered),
    )
    manual_review_urgency_score = _manual_review_urgency_score(
        evidence_update_count=evidence_update_count,
        conflicting_update_count=conflicting_count,
        unresolved_contradiction_count=unresolved_count,
        manual_review_signal_count=manual_count,
        claim_materiality_score=claim_materiality_score,
        contradiction_pressure_score=contradiction_pressure_score,
    )
    revision_risk_score = _revision_risk_score(
        evidence_update_count=evidence_update_count,
        stale_evidence_update_count=stale_count,
        conflicting_update_count=conflicting_count,
        unresolved_contradiction_count=unresolved_count,
        claim_materiality_score=claim_materiality_score,
        contradiction_pressure_score=contradiction_pressure_score,
        manual_review_urgency_score=manual_review_urgency_score,
    )
    status = _row_status(
        stale_evidence_update_count=stale_count,
        conflicting_update_count=conflicting_count,
        unresolved_contradiction_count=unresolved_count,
        manual_review_signal_count=manual_count,
        claim_materiality_score=claim_materiality_score,
        contradiction_pressure_score=contradiction_pressure_score,
        manual_review_urgency_score=manual_review_urgency_score,
        revision_risk_score=revision_risk_score,
        config=config,
    )

    return ResearchEventEvidenceRevisionRiskRow(
        event_label=event_label,
        evidence_update_count=evidence_update_count,
        conflicting_update_count=conflicting_count,
        stale_evidence_update_count=stale_count,
        material_change_count=material_count,
        unresolved_contradiction_count=unresolved_count,
        manual_review_signal_count=manual_count,
        latest_observed_at=max(item.observed_at for item in ordered),
        latest_evidence_age_seconds=min(ages),
        max_evidence_age_seconds=max(ages),
        claim_materiality_score=claim_materiality_score,
        contradiction_pressure_score=contradiction_pressure_score,
        manual_review_urgency_score=manual_review_urgency_score,
        revision_risk_score=revision_risk_score,
        status=status,
        evidence_version_labels=tuple(item.evidence_version_label for item in ordered),
        reason_codes=_row_reason_codes(
            observations=ordered,
            stale_evidence_update_count=stale_count,
            conflicting_update_count=conflicting_count,
            unresolved_contradiction_count=unresolved_count,
            manual_review_signal_count=manual_count,
            claim_materiality_score=claim_materiality_score,
            contradiction_pressure_score=contradiction_pressure_score,
            manual_review_urgency_score=manual_review_urgency_score,
            revision_risk_score=revision_risk_score,
            status=status,
            config=config,
        ),
    )


def _manual_review_urgency_score(
    *,
    evidence_update_count: Decimal,
    conflicting_update_count: Decimal,
    unresolved_contradiction_count: Decimal,
    manual_review_signal_count: Decimal,
    claim_materiality_score: Decimal,
    contradiction_pressure_score: Decimal,
) -> Decimal:
    return min(
        _quantize_ratio(
            (claim_materiality_score * Decimal("0.200000"))
            + (contradiction_pressure_score * Decimal("0.400000"))
            + (_ratio(conflicting_update_count, evidence_update_count) * Decimal("0.100000"))
            + (
                _ratio(unresolved_contradiction_count, evidence_update_count)
                * Decimal("0.100000")
            )
            + (_ratio(manual_review_signal_count, evidence_update_count) * Decimal("0.200000")),
        ),
        ONE_RATIO,
    )


def _revision_risk_score(
    *,
    evidence_update_count: Decimal,
    stale_evidence_update_count: Decimal,
    conflicting_update_count: Decimal,
    unresolved_contradiction_count: Decimal,
    claim_materiality_score: Decimal,
    contradiction_pressure_score: Decimal,
    manual_review_urgency_score: Decimal,
) -> Decimal:
    return min(
        _quantize_ratio(
            (claim_materiality_score * Decimal("0.150000"))
            + (contradiction_pressure_score * Decimal("0.150000"))
            + (manual_review_urgency_score * Decimal("0.250000"))
            + (_ratio(conflicting_update_count, evidence_update_count) * Decimal("0.200000"))
            + (
                _ratio(unresolved_contradiction_count, evidence_update_count)
                * Decimal("0.200000")
            )
            + (_ratio(stale_evidence_update_count, evidence_update_count) * Decimal("0.125000")),
        ),
        ONE_RATIO,
    )


def _row_status(
    *,
    stale_evidence_update_count: Decimal,
    conflicting_update_count: Decimal,
    unresolved_contradiction_count: Decimal,
    manual_review_signal_count: Decimal,
    claim_materiality_score: Decimal,
    contradiction_pressure_score: Decimal,
    manual_review_urgency_score: Decimal,
    revision_risk_score: Decimal,
    config: ResearchEventEvidenceRevisionRiskConfig,
) -> str:
    if (
        revision_risk_score >= config.block_revision_risk_score
        or claim_materiality_score >= config.block_materiality_score
        or contradiction_pressure_score >= config.block_contradiction_pressure_score
        or manual_review_urgency_score >= config.block_manual_review_urgency_score
        or (conflicting_update_count > ZERO and unresolved_contradiction_count > ZERO)
    ):
        return "block"
    if (
        stale_evidence_update_count > ZERO
        or conflicting_update_count > ZERO
        or unresolved_contradiction_count > ZERO
        or manual_review_signal_count > ZERO
        or revision_risk_score >= config.watch_revision_risk_score
        or claim_materiality_score >= config.watch_materiality_score
        or contradiction_pressure_score >= config.watch_contradiction_pressure_score
        or manual_review_urgency_score >= config.watch_manual_review_urgency_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    observations: tuple[ResearchEventEvidenceRevisionRiskObservation, ...],
    stale_evidence_update_count: Decimal,
    conflicting_update_count: Decimal,
    unresolved_contradiction_count: Decimal,
    manual_review_signal_count: Decimal,
    claim_materiality_score: Decimal,
    contradiction_pressure_score: Decimal,
    manual_review_urgency_score: Decimal,
    revision_risk_score: Decimal,
    status: str,
    config: ResearchEventEvidenceRevisionRiskConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for item in observations:
        reason_codes.extend(f"input_{reason_code}" for reason_code in item.reason_codes)
    reason_codes.append(
        "conflicting_updates_present"
        if conflicting_update_count > ZERO
        else "conflicting_updates_clear",
    )
    if contradiction_pressure_score >= config.block_contradiction_pressure_score:
        reason_codes.append("contradiction_pressure_block")
    elif contradiction_pressure_score >= config.watch_contradiction_pressure_score:
        reason_codes.append("contradiction_pressure_watch")
    else:
        reason_codes.append("contradiction_pressure_low")
    reason_codes.append(
        "evidence_stale" if stale_evidence_update_count > ZERO else "evidence_recent",
    )
    reason_codes.append(f"evidence_revision_risk_{status}")
    reason_codes.append(
        "manual_review_needed"
        if manual_review_signal_count > ZERO
        else "manual_review_not_needed",
    )
    if manual_review_urgency_score >= config.block_manual_review_urgency_score:
        reason_codes.append("manual_review_urgency_block")
    elif manual_review_urgency_score >= config.watch_manual_review_urgency_score:
        reason_codes.append("manual_review_urgency_watch")
    if claim_materiality_score >= config.block_materiality_score:
        reason_codes.append("materiality_block")
    elif claim_materiality_score >= config.watch_materiality_score:
        reason_codes.append("materiality_watch")
    else:
        reason_codes.append("materiality_low")
    if revision_risk_score >= config.block_revision_risk_score:
        reason_codes.append("revision_risk_score_block")
    elif revision_risk_score >= config.watch_revision_risk_score:
        reason_codes.append("revision_risk_score_watch")
    else:
        reason_codes.append("revision_risk_score_low")
    reason_codes.append(
        "unresolved_contradiction_present"
        if unresolved_contradiction_count > ZERO
        else "unresolved_contradiction_clear",
    )
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=False)


def _summary_status(rows: tuple[ResearchEventEvidenceRevisionRiskRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchEventEvidenceRevisionRiskRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_evidence_revision_observations",)
    return (f"evidence_revision_risk_{_summary_status(rows)}",)


def _reason_code_counts(
    rows: tuple[ResearchEventEvidenceRevisionRiskRow, ...],
) -> tuple[ResearchEventEvidenceRevisionRiskReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventEvidenceRevisionRiskReasonCodeCount(
                reason_code="no_evidence_revision_observations",
                count=Decimal("1"),
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchEventEvidenceRevisionRiskReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items())
    )


def _normalize_observations(
    values: Iterable[object],
) -> tuple[ResearchEventEvidenceRevisionRiskObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    return tuple(_coerce_observation(item) for item in items)


def _coerce_observation(value: object) -> ResearchEventEvidenceRevisionRiskObservation:
    if type(value) is ResearchEventEvidenceRevisionRiskObservation:
        return value
    if isinstance(value, Mapping):
        _reject_unsafe_public_payload("observation", value)
    return ResearchEventEvidenceRevisionRiskObservation(
        event_label=_field_value(value, "event_label"),
        evidence_version_label=_field_value(value, "evidence_version_label"),
        observed_at=_field_value(value, "observed_at"),
        claim_materiality_score=_field_value(value, "claim_materiality_score"),
        contradiction_pressure_score=_field_value(value, "contradiction_pressure_score"),
        conflicting_update=_field_value(value, "conflicting_update", default=False),
        unresolved_contradiction=_field_value(
            value,
            "unresolved_contradiction",
            default=False,
        ),
        manual_review_signal=_field_value(value, "manual_review_signal", default=False),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only", default=True),
        report_only=_field_value(value, "report_only", default=True),
        readonly=_field_value(value, "readonly", default=True),
    )


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> Any:
    if isinstance(value, Mapping) and field_name in value:
        return value[field_name]
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _row_sort_key(row: ResearchEventEvidenceRevisionRiskRow) -> tuple[Decimal, str]:
    return (-STATUS_WEIGHT[row.status], row.event_label)


def _normalize_rows(value: object) -> tuple[ResearchEventEvidenceRevisionRiskRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchEventEvidenceRevisionRiskRow:
            raise ValueError("rows must contain ResearchEventEvidenceRevisionRiskRow values")
        _require_hard_flags("row", row)
    if value != tuple(sorted(value, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchEventEvidenceRevisionRiskReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for item in value:
        if type(item) is not ResearchEventEvidenceRevisionRiskReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventEvidenceRevisionRiskReasonCodeCount values",
            )
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must contain unique reason_code values")
        seen.add(item.reason_code)
        _require_hard_flags("reason_code_count", item)
    if value != tuple(sorted(value, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sort")
    return value


def _validate_config(config: ResearchEventEvidenceRevisionRiskConfig) -> None:
    if config.block_materiality_score < config.watch_materiality_score:
        raise ValueError("block_materiality_score must be >= watch_materiality_score")
    if (
        config.block_contradiction_pressure_score
        < config.watch_contradiction_pressure_score
    ):
        raise ValueError(
            "block_contradiction_pressure_score must be >= "
            "watch_contradiction_pressure_score",
        )
    if config.block_manual_review_urgency_score < config.watch_manual_review_urgency_score:
        raise ValueError(
            "block_manual_review_urgency_score must be >= "
            "watch_manual_review_urgency_score",
        )
    if config.block_revision_risk_score < config.watch_revision_risk_score:
        raise ValueError("block_revision_risk_score must be >= watch_revision_risk_score")


def _validate_row_materialized_fields(
    row: ResearchEventEvidenceRevisionRiskRow,
) -> None:
    for field_name in (
        "conflicting_update_count",
        "stale_evidence_update_count",
        "material_change_count",
        "unresolved_contradiction_count",
        "manual_review_signal_count",
    ):
        if getattr(row, field_name) > row.evidence_update_count:
            raise ValueError(f"{field_name} must be <= evidence_update_count")
    if _count(len(row.evidence_version_labels)) != row.evidence_update_count:
        raise ValueError("evidence_version_labels must match evidence_update_count")
    if row.latest_evidence_age_seconds > row.max_evidence_age_seconds:
        raise ValueError("latest_evidence_age_seconds must be <= max_evidence_age_seconds")
    expected_status_code = f"evidence_revision_risk_{row.status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_materialized_fields(
    report: ResearchEventEvidenceRevisionRiskReport,
) -> None:
    rows = report.rows
    expected = {
        "event_count": _count(len(rows)),
        "evidence_update_count": sum((row.evidence_update_count for row in rows), ZERO),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "conflicting_update_count": sum(
            (row.conflicting_update_count for row in rows),
            ZERO,
        ),
        "stale_evidence_update_count": sum(
            (row.stale_evidence_update_count for row in rows),
            ZERO,
        ),
        "material_change_count": sum((row.material_change_count for row in rows), ZERO),
        "unresolved_contradiction_count": sum(
            (row.unresolved_contradiction_count for row in rows),
            ZERO,
        ),
        "manual_review_signal_count": sum(
            (row.manual_review_signal_count for row in rows),
            ZERO,
        ),
    }
    for field_name, expected_value in expected.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _summary_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchEventEvidenceRevisionRiskRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_ratio(seconds + microseconds)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    if normalized.is_nan() or normalized.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize_ratio(normalized)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_ratio(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    quantized = normalized.quantize(COUNT_QUANTUM)
    if normalized != quantized:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    quantized = _require_nonnegative_whole_decimal(field_name, value)
    if quantized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    quantized = _quantize_ratio(normalized)
    if quantized < ZERO_RATIO or quantized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return quantized


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty public label")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_text(field_name, value)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase reason code")
    _reject_unsafe_public_text(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_public_label_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    for item in value:
        _require_public_label(field_name, item)
    normalized = tuple(sorted(dict.fromkeys(value)))
    if len(normalized) != len(value):
        raise ValueError(f"{field_name} must contain unique values")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    for item in value:
        _require_reason_code(field_name, item)
    normalized = tuple(sorted(dict.fromkeys(value)))
    if len(normalized) != len(value):
        raise ValueError(f"{field_name} must contain unique values")
    return normalized


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(report: ResearchEventEvidenceRevisionRiskReport) -> str:
    payload = _json_ready_without_digest(report)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = _strip_digest(payload)
    canonical = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_digest(item)
            for key, item in sorted(value.items())
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_strip_digest(item) for item in value]
    return value


def _json_ready_without_digest(
    report: ResearchEventEvidenceRevisionRiskReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is Decimal:
        return str(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains unsafe public value")
            _reject_unsafe_public_text("public key", key)
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public value")
