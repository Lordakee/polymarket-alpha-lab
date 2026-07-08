"""Pure source-side multichannel evidence consensus report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_MULTICHANNEL_EVIDENCE_CONSENSUS_CONFIG_VERSION = (
    "research-source-multichannel-evidence-consensus-v0"
)

STATUSES = ("pass", "watch", "block")
EVIDENCE_FAMILIES = ("official", "web", "social", "news")
STANCES = ("supports", "contradicts", "neutral")
STANCE_RANK = {"supports": Decimal("0.000000"), "contradicts": Decimal("1.000000"), "neutral": Decimal("2.000000")}

NO_EVIDENCE_REASON = "multichannel_evidence_consensus_no_evidence"
LOW_AGREEMENT_BLOCK_REASON = "multichannel_evidence_consensus_low_family_agreement_block"
LOW_AGREEMENT_WATCH_REASON = "multichannel_evidence_consensus_low_family_agreement_watch"
STALE_PRESSURE_BLOCK_REASON = "multichannel_evidence_consensus_stale_family_pressure_block"
STALE_PRESSURE_WATCH_REASON = "multichannel_evidence_consensus_stale_family_pressure_watch"
CONTRADICTION_PRESSURE_BLOCK_REASON = (
    "multichannel_evidence_consensus_contradiction_pressure_block"
)
CONTRADICTION_PRESSURE_WATCH_REASON = (
    "multichannel_evidence_consensus_contradiction_pressure_watch"
)
PASS_REASON = "multichannel_evidence_consensus_pass"
REASON_CODES = (
    NO_EVIDENCE_REASON,
    LOW_AGREEMENT_BLOCK_REASON,
    LOW_AGREEMENT_WATCH_REASON,
    STALE_PRESSURE_BLOCK_REASON,
    STALE_PRESSURE_WATCH_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    PASS_REASON,
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
FLAG_FIELDS = ("paper_only", "report_only", "readonly")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TERMS = (
    _join_parts("candidate", "_", "id"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "_", "slug"),
    _join_parts("que", "stion"),
    _join_parts("http", "://"),
    _join_parts("https", "://"),
    _join_parts("u", "r", "l"),
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "url"),
    _join_parts("source", "_", "ref"),
    _join_parts("raw", "_"),
    _join_parts("d", "s", "n"),
    _join_parts("table", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("au", "th"),
    _join_parts("recom", "mendation"),
    _join_parts("siz", "ing"),
    _join_parts("cre", "dential"),
    _join_parts("private", "_", "key"),
)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_MULTICHANNEL_EVIDENCE_CONSENSUS_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourceMultichannelEvidenceConsensusConfig",
    "ResearchSourceMultichannelEvidenceConsensusInput",
    "ResearchSourceMultichannelEvidenceConsensusFamilyRow",
    "ResearchSourceMultichannelEvidenceConsensusReport",
    "build_research_source_multichannel_evidence_consensus_report",
    "research_source_multichannel_evidence_consensus_report_payload",
    "validate_research_source_multichannel_evidence_consensus_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceMultichannelEvidenceConsensusConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_MULTICHANNEL_EVIDENCE_CONSENSUS_CONFIG_VERSION
    )
    fresh_age_seconds: Decimal = Decimal("3600.000000")
    stale_age_seconds: Decimal = Decimal("86400.000000")
    agreement_watch_threshold: Decimal = Decimal("0.600000")
    agreement_pass_threshold: Decimal = Decimal("0.750000")
    contradiction_watch_threshold: Decimal = Decimal("0.250000")
    contradiction_block_threshold: Decimal = Decimal("0.500000")
    stale_family_watch_ratio: Decimal = Decimal("0.250000")
    stale_family_block_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceMultichannelEvidenceConsensusConfig:
            raise TypeError(
                "ResearchSourceMultichannelEvidenceConsensusConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceMultichannelEvidenceConsensusConfig:
            raise ValueError(
                "config must be exactly ResearchSourceMultichannelEvidenceConsensusConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_MULTICHANNEL_EVIDENCE_CONSENSUS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("fresh_age_seconds", "stale_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must exceed fresh_age_seconds")
        for field_name in (
            "agreement_watch_threshold",
            "agreement_pass_threshold",
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
            "stale_family_watch_ratio",
            "stale_family_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.agreement_pass_threshold <= self.agreement_watch_threshold:
            raise ValueError(
                "agreement_pass_threshold must exceed agreement_watch_threshold",
            )
        if self.contradiction_block_threshold <= self.contradiction_watch_threshold:
            raise ValueError(
                "contradiction_block_threshold must exceed "
                "contradiction_watch_threshold",
            )
        if self.stale_family_block_ratio <= self.stale_family_watch_ratio:
            raise ValueError(
                "stale_family_block_ratio must exceed stale_family_watch_ratio",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceMultichannelEvidenceConsensusInput:
    evidence_family: str
    stance: str
    observed_at: datetime
    evidence_count: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceMultichannelEvidenceConsensusInput:
            raise TypeError(
                "ResearchSourceMultichannelEvidenceConsensusInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceMultichannelEvidenceConsensusInput:
            raise ValueError(
                "input must be exactly ResearchSourceMultichannelEvidenceConsensusInput",
            )
        _require_evidence_family("evidence_family", self.evidence_family)
        _require_stance("stance", self.stance)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "evidence_count",
            _require_positive_whole_decimal("evidence_count", self.evidence_count),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchSourceMultichannelEvidenceConsensusFamilyRow:
    evidence_family: str
    evidence_count: Decimal
    support_count: Decimal
    neutral_count: Decimal
    contradiction_count: Decimal
    latest_observed_at: datetime
    latest_age_seconds: Decimal
    freshness_score: Decimal
    family_stance: str
    family_agreement_score: Decimal
    contradiction_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceMultichannelEvidenceConsensusFamilyRow:
            raise TypeError(
                "ResearchSourceMultichannelEvidenceConsensusFamilyRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceMultichannelEvidenceConsensusFamilyRow:
            raise ValueError(
                "row must be exactly ResearchSourceMultichannelEvidenceConsensusFamilyRow",
            )
        _require_evidence_family("evidence_family", self.evidence_family)
        for field_name in (
            "evidence_count",
            "support_count",
            "neutral_count",
            "contradiction_count",
            "latest_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "freshness_score",
            "family_agreement_score",
            "contradiction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_stance("family_stance", self.family_stance)
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_family_row(self)
        _require_hard_flags("family row", self)
        _reject_unsafe_public_payload("family row", self)


@dataclass(frozen=True)
class ResearchSourceMultichannelEvidenceConsensusReport:
    generated_at: datetime
    config_version: str
    status: str
    consensus_stance: str
    evidence_family_count: Decimal
    evidence_count: Decimal
    support_count: Decimal
    neutral_count: Decimal
    contradiction_count: Decimal
    consensus_family_count: Decimal
    family_agreement_score: Decimal
    contradiction_pressure_score: Decimal
    average_freshness_score: Decimal
    stale_family_ratio: Decimal
    family_rows: tuple[ResearchSourceMultichannelEvidenceConsensusFamilyRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceMultichannelEvidenceConsensusReport:
            raise TypeError(
                "ResearchSourceMultichannelEvidenceConsensusReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceMultichannelEvidenceConsensusReport:
            raise ValueError(
                "report must be exactly ResearchSourceMultichannelEvidenceConsensusReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        _require_stance("consensus_stance", self.consensus_stance)
        for field_name in (
            "evidence_family_count",
            "evidence_count",
            "support_count",
            "neutral_count",
            "contradiction_count",
            "consensus_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "family_agreement_score",
            "contradiction_pressure_score",
            "average_freshness_score",
            "stale_family_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "family_rows", _normalize_family_rows(self.family_rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report(self)
        _require_or_set_digest(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)


def build_research_source_multichannel_evidence_consensus_report(
    inputs: list[ResearchSourceMultichannelEvidenceConsensusInput]
    | tuple[ResearchSourceMultichannelEvidenceConsensusInput, ...],
    *,
    config: ResearchSourceMultichannelEvidenceConsensusConfig,
    generated_at: datetime,
) -> ResearchSourceMultichannelEvidenceConsensusReport:
    if type(config) is not ResearchSourceMultichannelEvidenceConsensusConfig:
        raise ValueError(
            "config must be a ResearchSourceMultichannelEvidenceConsensusConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs, generated_at=generated_at_utc)
    family_rows = _build_family_rows(
        input_rows,
        generated_at=generated_at_utc,
        config=config,
    )
    consensus_stance, consensus_family_count = _report_consensus(family_rows)
    reasons = _report_reason_codes(
        family_rows,
        consensus_family_count=consensus_family_count,
        config=config,
    )
    status = _status_from_reason_codes(reasons)
    return ResearchSourceMultichannelEvidenceConsensusReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        consensus_stance=consensus_stance,
        evidence_family_count=_decimal_count(len(family_rows)),
        evidence_count=_decimal_sum(tuple(row.evidence_count for row in family_rows)),
        support_count=_decimal_sum(tuple(row.support_count for row in family_rows)),
        neutral_count=_decimal_sum(tuple(row.neutral_count for row in family_rows)),
        contradiction_count=_decimal_sum(
            tuple(row.contradiction_count for row in family_rows),
        ),
        consensus_family_count=consensus_family_count,
        family_agreement_score=_ratio(
            consensus_family_count,
            _decimal_count(len(family_rows)),
        ),
        contradiction_pressure_score=_ratio(
            _decimal_count(
                sum(row.family_stance == "contradicts" for row in family_rows),
            ),
            _decimal_count(len(family_rows)),
        ),
        average_freshness_score=_average_ratio(
            tuple(row.freshness_score for row in family_rows),
        ),
        stale_family_ratio=_ratio(
            _decimal_count(
                sum(row.freshness_score == ZERO for row in family_rows),
            ),
            _decimal_count(len(family_rows)),
        ),
        family_rows=family_rows,
        reason_codes=reasons,
    )


def research_source_multichannel_evidence_consensus_report_payload(
    value: ResearchSourceMultichannelEvidenceConsensusReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchSourceMultichannelEvidenceConsensusReport:
        _require_hard_flags("report", value)
        _require_or_set_digest(value)
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchSourceMultichannelEvidenceConsensusReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _verify_public_digest(payload)
    return payload


def validate_research_source_multichannel_evidence_consensus_report_payload(
    payload: dict[str, object],
) -> bool:
    research_source_multichannel_evidence_consensus_report_payload(payload)
    return True


def _build_family_rows(
    rows: tuple[ResearchSourceMultichannelEvidenceConsensusInput, ...],
    *,
    generated_at: datetime,
    config: ResearchSourceMultichannelEvidenceConsensusConfig,
) -> tuple[ResearchSourceMultichannelEvidenceConsensusFamilyRow, ...]:
    grouped: dict[str, list[ResearchSourceMultichannelEvidenceConsensusInput]] = {}
    for row in rows:
        grouped.setdefault(row.evidence_family, []).append(row)
    return tuple(
        _family_row(
            evidence_family,
            tuple(grouped[evidence_family]),
            generated_at=generated_at,
            config=config,
        )
        for evidence_family in sorted(grouped)
    )


def _family_row(
    evidence_family: str,
    rows: tuple[ResearchSourceMultichannelEvidenceConsensusInput, ...],
    *,
    generated_at: datetime,
    config: ResearchSourceMultichannelEvidenceConsensusConfig,
) -> ResearchSourceMultichannelEvidenceConsensusFamilyRow:
    latest = max(rows, key=lambda row: row.observed_at)
    latest_age = _age_seconds(generated_at, latest.observed_at)
    evidence_count = _decimal_sum(tuple(row.evidence_count for row in rows))
    support_count = _stance_count(rows, "supports")
    neutral_count = _stance_count(rows, "neutral")
    contradiction_count = _stance_count(rows, "contradicts")
    family_stance, family_stance_count = _majority_stance(
        support_count=support_count,
        neutral_count=neutral_count,
        contradiction_count=contradiction_count,
    )
    agreement_score = _ratio(family_stance_count, evidence_count)
    contradiction_score = _ratio(contradiction_count, evidence_count)
    freshness_score = _freshness_score(latest_age, config=config)
    reason_codes = _family_reason_codes(
        agreement_score=agreement_score,
        freshness_score=freshness_score,
        config=config,
    )
    return ResearchSourceMultichannelEvidenceConsensusFamilyRow(
        evidence_family=evidence_family,
        evidence_count=evidence_count,
        support_count=support_count,
        neutral_count=neutral_count,
        contradiction_count=contradiction_count,
        latest_observed_at=latest.observed_at,
        latest_age_seconds=latest_age,
        freshness_score=freshness_score,
        family_stance=family_stance,
        family_agreement_score=agreement_score,
        contradiction_pressure_score=contradiction_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _report_consensus(
    rows: tuple[ResearchSourceMultichannelEvidenceConsensusFamilyRow, ...],
) -> tuple[str, Decimal]:
    if not rows:
        return "neutral", ZERO
    counts = {
        stance: _decimal_count(sum(row.family_stance == stance for row in rows))
        for stance in STANCES
    }
    stance = min(STANCES, key=lambda value: (-counts[value], STANCE_RANK[value]))
    return stance, counts[stance]


def _report_reason_codes(
    rows: tuple[ResearchSourceMultichannelEvidenceConsensusFamilyRow, ...],
    *,
    consensus_family_count: Decimal,
    config: ResearchSourceMultichannelEvidenceConsensusConfig,
) -> tuple[str, ...]:
    if not rows:
        return (NO_EVIDENCE_REASON,)
    family_count = _decimal_count(len(rows))
    agreement_score = _ratio(consensus_family_count, family_count)
    contradiction_score = _ratio(
        _decimal_count(sum(row.family_stance == "contradicts" for row in rows)),
        family_count,
    )
    stale_ratio = _ratio(
        _decimal_count(sum(row.freshness_score == ZERO for row in rows)),
        family_count,
    )
    reasons: list[str] = []
    if agreement_score < config.agreement_watch_threshold:
        reasons.append(LOW_AGREEMENT_BLOCK_REASON)
    elif agreement_score < config.agreement_pass_threshold:
        reasons.append(LOW_AGREEMENT_WATCH_REASON)
    if stale_ratio >= config.stale_family_block_ratio:
        reasons.append(STALE_PRESSURE_BLOCK_REASON)
    elif stale_ratio >= config.stale_family_watch_ratio:
        reasons.append(STALE_PRESSURE_WATCH_REASON)
    if contradiction_score >= config.contradiction_block_threshold:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif contradiction_score >= config.contradiction_watch_threshold:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(code for code in REASON_CODES if code in reasons)


def _family_reason_codes(
    *,
    agreement_score: Decimal,
    freshness_score: Decimal,
    config: ResearchSourceMultichannelEvidenceConsensusConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if agreement_score < config.agreement_watch_threshold:
        reasons.append(LOW_AGREEMENT_BLOCK_REASON)
    elif agreement_score < config.agreement_pass_threshold:
        reasons.append(LOW_AGREEMENT_WATCH_REASON)
    if freshness_score == ZERO:
        reasons.append(STALE_PRESSURE_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(code for code in REASON_CODES if code in reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        NO_EVIDENCE_REASON in reason_codes
        or LOW_AGREEMENT_BLOCK_REASON in reason_codes
        or STALE_PRESSURE_BLOCK_REASON in reason_codes
        or CONTRADICTION_PRESSURE_BLOCK_REASON in reason_codes
    ):
        return "block"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _stance_count(
    rows: tuple[ResearchSourceMultichannelEvidenceConsensusInput, ...],
    stance: str,
) -> Decimal:
    return _decimal_sum(
        tuple(row.evidence_count for row in rows if row.stance == stance),
    )


def _majority_stance(
    *,
    support_count: Decimal,
    neutral_count: Decimal,
    contradiction_count: Decimal,
) -> tuple[str, Decimal]:
    counts = {
        "supports": support_count,
        "contradicts": contradiction_count,
        "neutral": neutral_count,
    }
    stance = min(STANCES, key=lambda value: (-counts[value], STANCE_RANK[value]))
    return stance, counts[stance]


def _freshness_score(
    latest_age_seconds: Decimal,
    *,
    config: ResearchSourceMultichannelEvidenceConsensusConfig,
) -> Decimal:
    if latest_age_seconds <= config.fresh_age_seconds:
        return ONE
    if latest_age_seconds >= config.stale_age_seconds:
        return ZERO
    return _ratio(
        config.stale_age_seconds - latest_age_seconds,
        config.stale_age_seconds - config.fresh_age_seconds,
    )


def _normalize_inputs(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceMultichannelEvidenceConsensusInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchSourceMultichannelEvidenceConsensusInput:
            raise ValueError(
                "inputs must contain ResearchSourceMultichannelEvidenceConsensusInput",
            )
        _require_hard_flags("input", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.evidence_family,
                row.stance,
                row.observed_at.isoformat(),
            ),
        ),
    )


def _normalize_family_rows(
    value: object,
) -> tuple[ResearchSourceMultichannelEvidenceConsensusFamilyRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("family_rows must be a list or tuple")
    rows = tuple(value)
    expected = tuple(sorted(rows, key=lambda row: row.evidence_family))
    if rows != expected:
        raise ValueError("family_rows must be sorted deterministically")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceMultichannelEvidenceConsensusFamilyRow:
            raise ValueError(
                "family_rows must contain "
                "ResearchSourceMultichannelEvidenceConsensusFamilyRow",
            )
        _require_hard_flags("family row", row)
        if row.evidence_family in seen:
            raise ValueError("family_rows must be unique by evidence_family")
        seen.add(row.evidence_family)
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_code must be known")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    expected = tuple(code for code in REASON_CODES if code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _validate_family_row(
    row: ResearchSourceMultichannelEvidenceConsensusFamilyRow,
) -> None:
    if row.evidence_count != (
        row.support_count + row.neutral_count + row.contradiction_count
    ).quantize(QUANT):
        raise ValueError("evidence_count must match stance counts")
    if row.family_agreement_score != _ratio(
        max(row.support_count, row.neutral_count, row.contradiction_count),
        row.evidence_count,
    ):
        raise ValueError("family_agreement_score must match stance counts")
    if row.contradiction_pressure_score != _ratio(
        row.contradiction_count,
        row.evidence_count,
    ):
        raise ValueError("contradiction_pressure_score must match stance counts")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchSourceMultichannelEvidenceConsensusReport) -> None:
    if report.evidence_family_count != _decimal_count(len(report.family_rows)):
        raise ValueError("evidence_family_count must match family_rows")
    if report.evidence_count != _decimal_sum(
        tuple(row.evidence_count for row in report.family_rows),
    ):
        raise ValueError("evidence_count must match family_rows")
    if report.support_count != _decimal_sum(
        tuple(row.support_count for row in report.family_rows),
    ):
        raise ValueError("support_count must match family_rows")
    if report.neutral_count != _decimal_sum(
        tuple(row.neutral_count for row in report.family_rows),
    ):
        raise ValueError("neutral_count must match family_rows")
    if report.contradiction_count != _decimal_sum(
        tuple(row.contradiction_count for row in report.family_rows),
    ):
        raise ValueError("contradiction_count must match family_rows")
    consensus_stance, consensus_count = _report_consensus(report.family_rows)
    if report.consensus_stance != consensus_stance:
        raise ValueError("consensus_stance must match family_rows")
    if report.consensus_family_count != consensus_count:
        raise ValueError("consensus_family_count must match family_rows")
    if report.family_agreement_score != _ratio(
        report.consensus_family_count,
        report.evidence_family_count,
    ):
        raise ValueError("family_agreement_score must match family_rows")
    if report.contradiction_pressure_score != _ratio(
        _decimal_count(
            sum(row.family_stance == "contradicts" for row in report.family_rows),
        ),
        report.evidence_family_count,
    ):
        raise ValueError("contradiction_pressure_score must match family_rows")
    if report.average_freshness_score != _average_ratio(
        tuple(row.freshness_score for row in report.family_rows),
    ):
        raise ValueError("average_freshness_score must match family_rows")
    if report.stale_family_ratio != _ratio(
        _decimal_count(sum(row.freshness_score == ZERO for row in report.family_rows)),
        report.evidence_family_count,
    ):
        raise ValueError("stale_family_ratio must match family_rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _decimal_sum(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += _require_nonnegative_decimal("sum value", value)
    return total.quantize(QUANT)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(_decimal_sum(values), _decimal_count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    value = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if value < ZERO:
        raise ValueError("observed_at must not be in the future")
    return value.quantize(QUANT)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            decimal_value = value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_unsafe_public_term(value):
        raise ValueError(f"{field_name} contains unsafe public value")


def _require_evidence_family(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in EVIDENCE_FAMILIES:
        raise ValueError(f"{field_name} must be official, web, social, or news")


def _require_stance(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in STANCES:
        raise ValueError(f"{field_name} must be supports, contradicts, or neutral")


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_or_set_digest(
    report: ResearchSourceMultichannelEvidenceConsensusReport,
) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _report_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 hex digest") from exc
    if value.lower() != value:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _report_digest(report: ResearchSourceMultichannelEvidenceConsensusReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _verify_public_digest(payload: dict[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("derived_validation_digest does not match public payload")


def _canonical_digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


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
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (float, int)):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, str):
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


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _json_ready(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, dict):
        if not allow_json_containers and type(value) is not dict:
            raise ValueError(f"{label} must use plain dict containers")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_term(key):
                raise ValueError(f"unsafe public key in {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, tuple):
        if not allow_json_containers:
            for item in value:
                _reject_unsafe_public_payload(
                    label,
                    item,
                    allow_json_containers=allow_json_containers,
                )
            return
        raise ValueError(f"{label} must use JSON list containers")
    if type(value) in (float, int):
        raise ValueError(f"unsafe public numeric in {label}")
    if type(value) is str and _has_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in UNSAFE_PUBLIC_TERMS)
