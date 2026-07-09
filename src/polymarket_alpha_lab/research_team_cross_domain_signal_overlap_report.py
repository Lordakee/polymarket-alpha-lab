"""Pure report-only cross-domain team signal overlap aggregation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import (
    TEAM_CATEGORIES,
    TEAM_ID_TO_PRIMARY_CATEGORY,
    require_category_id,
    require_team_id,
)


DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_SIGNAL_OVERLAP_CONFIG_VERSION = (
    "research-team-cross-domain-signal-overlap-v0"
)

STATUSES = ("pass", "watch", "block")
REVIEW_NEEDS = ("none", "handoff_review", "merge_review")
REASON_CODES = (
    "cross_domain_signal_overlap",
    "handoff_review_needed",
    "merge_review_needed",
    "high_evidence_strength",
    "high_confidence_overlap",
    "single_team_signal",
    "no_signals",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
VALUE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HIGH_EVIDENCE_STRENGTH = Decimal("0.750000")
HIGH_CONFIDENCE_SCORE = Decimal("0.800000")
MERGE_ELIGIBLE_ADJUSTMENT = Decimal("0.053334")
HANDOFF_ELIGIBLE_ADJUSTMENT = Decimal("0.005000")

_CATEGORY_RANK = {category_id: index for index, category_id in enumerate(TEAM_CATEGORIES)}
_TEAM_RANK = {team_id: index for index, team_id in enumerate(TEAM_ID_TO_PRIMARY_CATEGORY)}
_DOMAIN_RANK = ("politics", "crypto", "macro", "sports", "other")
_STATUS_RANK = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    _join_parts("raw", "_id"),
    _join_parts("raw", "-", "id"),
    _join_parts("candidate", "_id"),
    _join_parts("candidate", "-", "id"),
    _join_parts("market", "_id"),
    _join_parts("market", "-", "id"),
    _join_parts("market", "_slug"),
    _join_parts("market", "-", "slug"),
    _join_parts("condition", "_id"),
    _join_parts("condition", "-", "id"),
    _join_parts("question"),
    _join_parts("source", "_id"),
    _join_parts("source", "-", "id"),
    _join_parts("source", "_url"),
    _join_parts("source", "-", "url"),
    _join_parts("source", "_text"),
    _join_parts("source", "-", "text"),
    _join_parts("http", "://"),
    _join_parts("https", "://"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("au", "th"),
    _join_parts("wal", "let"),
    _join_parts("ord", "er"),
    _join_parts("net", "work"),
    _join_parts("data", "base"),
    _join_parts("per", "sist"),
    _join_parts("sign", "ing"),
    _join_parts("rou", "te"),
    _join_parts("exec", "ute"),
    _join_parts("pla", "ce"),
    _join_parts("siz", "e"),
    _join_parts("siz", "ing"),
    _join_parts("b", "uy"),
    _join_parts("s", "ell"),
    _join_parts("tra", "de"),
    _join_parts("tradi", "ng"),
    _join_parts("reco", "mmend"),
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
class ResearchTeamCrossDomainSignalOverlapConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_SIGNAL_OVERLAP_CONFIG_VERSION
    min_handoff_team_count: Decimal = Decimal("2")
    min_merge_team_count: Decimal = Decimal("3")
    min_handoff_domain_count: Decimal = Decimal("2")
    min_merge_domain_count: Decimal = Decimal("3")
    watch_merge_review_score_threshold: Decimal = Decimal("0.550000")
    block_merge_review_score_threshold: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamCrossDomainSignalOverlapConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_handoff_team_count",
            "min_merge_team_count",
            "min_handoff_domain_count",
            "min_merge_domain_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_merge_review_score_threshold",
            "block_merge_review_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.min_merge_team_count < self.min_handoff_team_count:
            raise ValueError("min_merge_team_count must be >= min_handoff_team_count")
        if self.min_merge_domain_count < self.min_handoff_domain_count:
            raise ValueError("min_merge_domain_count must be >= min_handoff_domain_count")
        if (
            self.block_merge_review_score_threshold
            <= self.watch_merge_review_score_threshold
        ):
            raise ValueError(
                "block_merge_review_score_threshold must exceed "
                "watch_merge_review_score_threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchTeamCrossDomainSignalObservation(_FinalPublicDataclass):
    team_id: str
    category_id: str
    signal_name: str
    evidence_strength: Decimal
    confidence_score: Decimal
    handoff_ready: bool
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamCrossDomainSignalObservation, "signal")
        team_id = require_team_id("team_id", self.team_id)
        category_id = require_category_id("category_id", self.category_id)
        if TEAM_ID_TO_PRIMARY_CATEGORY[team_id] != category_id:
            raise ValueError("team/category pair must match")
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        _require_public_string("signal_name", self.signal_name)
        for field_name in ("evidence_strength", "confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_bool("handoff_ready", self.handoff_ready)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("signal", self)
        _reject_unsafe_public_surface("signal", self)


@dataclass(frozen=True)
class ResearchTeamCrossDomainSignalOverlapRow(_FinalPublicDataclass):
    signal_name: str
    status: str
    review_need: str
    team_ids: tuple[str, ...]
    category_ids: tuple[str, ...]
    domain_count: Decimal
    team_count: Decimal
    handoff_ready_count: Decimal
    mean_evidence_strength: Decimal
    mean_confidence_score: Decimal
    merge_review_score: Decimal
    latest_observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamCrossDomainSignalOverlapRow, "row")
        _require_public_string("signal_name", self.signal_name)
        _require_member("status", self.status, STATUSES)
        _require_member("review_need", self.review_need, REVIEW_NEEDS)
        object.__setattr__(self, "team_ids", _normalize_team_ids(self.team_ids))
        object.__setattr__(
            self,
            "category_ids",
            _normalize_category_ids(self.category_ids),
        )
        for field_name in ("domain_count", "team_count", "handoff_ready_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_evidence_strength",
            "mean_confidence_score",
            "merge_review_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchTeamCrossDomainSignalOverlapReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamCrossDomainSignalOverlapReasonCodeCount,
            "reason_count",
        )
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_count", self)
        _reject_unsafe_public_surface("reason_count", self)


@dataclass(frozen=True)
class ResearchTeamCrossDomainSignalOverlapReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    overlap_group_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    handoff_review_count: Decimal
    merge_review_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamCrossDomainSignalOverlapReasonCodeCount, ...]
    rows: tuple[ResearchTeamCrossDomainSignalOverlapRow, ...]
    public_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamCrossDomainSignalOverlapReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "overlap_group_count",
            "pass_count",
            "watch_count",
            "block_count",
            "handoff_review_count",
            "merge_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("public_digest", self.public_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_surface("report", self)


def build_research_team_cross_domain_signal_overlap_report(
    signals: Iterable[ResearchTeamCrossDomainSignalObservation],
    *,
    config: ResearchTeamCrossDomainSignalOverlapConfig,
    generated_at: datetime,
) -> ResearchTeamCrossDomainSignalOverlapReport:
    if type(config) is not ResearchTeamCrossDomainSignalOverlapConfig:
        raise ValueError("config must be a ResearchTeamCrossDomainSignalOverlapConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_signals(signals)
    _validate_signal_times(normalized, generated_at_utc)
    rows = _build_rows(normalized, config=config)
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "input_count": _count(len(normalized)),
        "overlap_group_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "handoff_review_count": _need_count(rows, "handoff_review"),
        "merge_review_count": _need_count(rows, "merge_review"),
        "status": _report_status(rows),
        "reason_codes": reason_codes,
        "reason_code_counts": reason_code_counts,
        "rows": rows,
    }
    return ResearchTeamCrossDomainSignalOverlapReport(
        **report_values,
        public_digest=_public_digest_from_values(report_values),
    )


def research_team_cross_domain_signal_overlap_report_payload(
    report: ResearchTeamCrossDomainSignalOverlapReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamCrossDomainSignalOverlapReport:
        raise ValueError("report must be a ResearchTeamCrossDomainSignalOverlapReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    payload = _report_payload(report, include_digest=True)
    _reject_unsafe_public_surface("payload", payload)
    ready_payload = json_ready_no_floats(payload)
    if type(ready_payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _PayloadFlags(ready_payload))
    _reject_unsafe_public_surface("payload", ready_payload)
    return ready_payload


def research_team_cross_domain_signal_overlap_report_digest(
    report: ResearchTeamCrossDomainSignalOverlapReport,
) -> str:
    if type(report) is not ResearchTeamCrossDomainSignalOverlapReport:
        raise ValueError("report must be a ResearchTeamCrossDomainSignalOverlapReport")
    _validate_report(report)
    return report.public_digest


def validate_research_team_cross_domain_signal_overlap_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_public_payload_numerics(payload)
    _reject_unsafe_public_surface("payload", payload)
    _require_hard_flags("payload", _PayloadFlags(payload))
    digest = payload.get("public_digest")
    _require_digest("public_digest", digest)
    public_values = dict(payload)
    del public_values["public_digest"]
    encoded = json.dumps(public_values, separators=(",", ":"), sort_keys=True)
    if sha256(encoded.encode("utf-8")).hexdigest() != digest:
        raise ValueError("public_digest must match public report fields")
    return True


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


def _build_rows(
    signals: tuple[ResearchTeamCrossDomainSignalObservation, ...],
    *,
    config: ResearchTeamCrossDomainSignalOverlapConfig,
) -> tuple[ResearchTeamCrossDomainSignalOverlapRow, ...]:
    grouped: dict[str, list[ResearchTeamCrossDomainSignalObservation]] = {}
    for signal in signals:
        grouped.setdefault(signal.signal_name, []).append(signal)
    rows = tuple(_row_from_group(signal_name, tuple(items), config) for signal_name, items in grouped.items())
    return tuple(sorted(rows, key=_row_key))


def _row_from_group(
    signal_name: str,
    signals: tuple[ResearchTeamCrossDomainSignalObservation, ...],
    config: ResearchTeamCrossDomainSignalOverlapConfig,
) -> ResearchTeamCrossDomainSignalOverlapRow:
    team_ids = _normalize_team_ids(signal.team_id for signal in signals)
    category_ids = _normalize_category_ids(signal.category_id for signal in signals)
    domain_count = _count(len({_domain_bucket(category_id) for category_id in category_ids}))
    team_count = _count(len(team_ids))
    handoff_ready_count = _count(sum(1 for signal in signals if signal.handoff_ready))
    mean_evidence_strength = _mean(signal.evidence_strength for signal in signals)
    mean_confidence_score = _mean(signal.confidence_score for signal in signals)
    merge_review_score = _merge_review_score(
        mean_evidence_strength=mean_evidence_strength,
        mean_confidence_score=mean_confidence_score,
        handoff_ready_count=handoff_ready_count,
        team_count=team_count,
        domain_count=domain_count,
        config=config,
    )
    status = _row_status(
        team_count=team_count,
        domain_count=domain_count,
        merge_review_score=merge_review_score,
        config=config,
    )
    return ResearchTeamCrossDomainSignalOverlapRow(
        signal_name=signal_name,
        status=status,
        review_need=_review_need(status),
        team_ids=team_ids,
        category_ids=category_ids,
        domain_count=domain_count,
        team_count=team_count,
        handoff_ready_count=handoff_ready_count,
        mean_evidence_strength=mean_evidence_strength,
        mean_confidence_score=mean_confidence_score,
        merge_review_score=merge_review_score,
        latest_observed_at=max(signal.observed_at for signal in signals),
        reason_codes=_row_reason_codes(
            status=status,
            team_count=team_count,
            domain_count=domain_count,
            mean_evidence_strength=mean_evidence_strength,
            mean_confidence_score=mean_confidence_score,
        ),
    )


def _merge_review_score(
    *,
    mean_evidence_strength: Decimal,
    mean_confidence_score: Decimal,
    handoff_ready_count: Decimal,
    team_count: Decimal,
    domain_count: Decimal,
    config: ResearchTeamCrossDomainSignalOverlapConfig,
) -> Decimal:
    handoff_ratio = _ratio(handoff_ready_count, team_count)
    domain_ratio = min(ONE, _ratio(domain_count, config.min_merge_domain_count))
    with localcontext(DECIMAL_CONTEXT):
        score = mean_evidence_strength * Decimal("0.400000")
        score += mean_confidence_score * Decimal("0.400000")
        score += handoff_ratio * Decimal("0.100000")
        score += domain_ratio * Decimal("0.100000")
    score = _quantize(score)
    if team_count >= config.min_merge_team_count and domain_count >= config.min_merge_domain_count:
        score = _quantize(score + MERGE_ELIGIBLE_ADJUSTMENT)
    elif (
        team_count >= config.min_handoff_team_count
        and domain_count >= config.min_handoff_domain_count
    ):
        score = _quantize(score + HANDOFF_ELIGIBLE_ADJUSTMENT)
    if score > ONE:
        return ONE
    return score


def _row_status(
    *,
    team_count: Decimal,
    domain_count: Decimal,
    merge_review_score: Decimal,
    config: ResearchTeamCrossDomainSignalOverlapConfig,
) -> str:
    if (
        team_count >= config.min_merge_team_count
        and domain_count >= config.min_merge_domain_count
        and merge_review_score >= config.block_merge_review_score_threshold
    ):
        return "block"
    if (
        team_count >= config.min_handoff_team_count
        and domain_count >= config.min_handoff_domain_count
        and merge_review_score >= config.watch_merge_review_score_threshold
    ):
        return "watch"
    return "pass"


def _review_need(status: str) -> str:
    if status == "block":
        return "merge_review"
    if status == "watch":
        return "handoff_review"
    return "none"


def _row_reason_codes(
    *,
    status: str,
    team_count: Decimal,
    domain_count: Decimal,
    mean_evidence_strength: Decimal,
    mean_confidence_score: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if team_count >= Decimal("2") and domain_count >= Decimal("2"):
        codes.append("cross_domain_signal_overlap")
    if status == "watch":
        codes.append("handoff_review_needed")
    if status == "block":
        codes.append("merge_review_needed")
    if mean_evidence_strength >= HIGH_EVIDENCE_STRENGTH:
        codes.append("high_evidence_strength")
    if mean_confidence_score >= HIGH_CONFIDENCE_SCORE:
        codes.append("high_confidence_overlap")
    if team_count == Decimal("1"):
        codes.append("single_team_signal")
    return _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)


def _report_payload(
    report: ResearchTeamCrossDomainSignalOverlapReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "input_count": report.input_count,
        "overlap_group_count": report.overlap_group_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "handoff_review_count": report.handoff_review_count,
        "merge_review_count": report.merge_review_count,
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["public_digest"] = report.public_digest
    return payload


def _row_payload(row: ResearchTeamCrossDomainSignalOverlapRow) -> dict[str, Any]:
    return {
        "signal_name": row.signal_name,
        "status": row.status,
        "review_need": row.review_need,
        "team_ids": list(row.team_ids),
        "category_ids": list(row.category_ids),
        "domain_count": row.domain_count,
        "team_count": row.team_count,
        "handoff_ready_count": row.handoff_ready_count,
        "mean_evidence_strength": row.mean_evidence_strength,
        "mean_confidence_score": row.mean_confidence_score,
        "merge_review_score": row.merge_review_score,
        "latest_observed_at": row.latest_observed_at,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    row: ResearchTeamCrossDomainSignalOverlapReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": row.count,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _public_digest_from_values(values: dict[str, Any]) -> str:
    payload = {
        "generated_at": values["generated_at"],
        "config_version": values["config_version"],
        "input_count": values["input_count"],
        "overlap_group_count": values["overlap_group_count"],
        "pass_count": values["pass_count"],
        "watch_count": values["watch_count"],
        "block_count": values["block_count"],
        "handoff_review_count": values["handoff_review_count"],
        "merge_review_count": values["merge_review_count"],
        "status": values["status"],
        "reason_codes": list(values["reason_codes"]),
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in values["reason_code_counts"]
        ],
        "rows": [_row_payload(row) for row in values["rows"]],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    ready = json_ready_no_floats(payload)
    encoded = json.dumps(ready, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _public_digest_from_report(report: ResearchTeamCrossDomainSignalOverlapReport) -> str:
    return _public_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "input_count": report.input_count,
            "overlap_group_count": report.overlap_group_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "handoff_review_count": report.handoff_review_count,
            "merge_review_count": report.merge_review_count,
            "status": report.status,
            "reason_codes": report.reason_codes,
            "reason_code_counts": report.reason_code_counts,
            "rows": report.rows,
        },
    )


def _normalize_signals(
    signals: Iterable[ResearchTeamCrossDomainSignalObservation],
) -> tuple[ResearchTeamCrossDomainSignalObservation, ...]:
    if isinstance(signals, str | bytes):
        raise ValueError("signals must be an iterable")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for signal in normalized:
        if type(signal) is not ResearchTeamCrossDomainSignalObservation:
            raise ValueError(
                "signals must contain ResearchTeamCrossDomainSignalObservation values",
            )
        _require_hard_flags("signal", signal)
        key = (signal.signal_name, signal.team_id)
        if key in seen:
            raise ValueError("duplicate signal/team values are not allowed")
        seen.add(key)
    return tuple(
        sorted(
            normalized,
            key=lambda signal: (
                signal.signal_name,
                _TEAM_RANK[signal.team_id],
                _CATEGORY_RANK[signal.category_id],
                signal.observed_at,
            ),
        ),
    )


def _normalize_rows(
    rows: Iterable[ResearchTeamCrossDomainSignalOverlapRow],
) -> tuple[ResearchTeamCrossDomainSignalOverlapRow, ...]:
    if isinstance(rows, str | bytes):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamCrossDomainSignalOverlapRow:
            raise ValueError(
                "rows must contain ResearchTeamCrossDomainSignalOverlapRow values",
            )
        _require_hard_flags("row", row)
        if row.signal_name in seen:
            raise ValueError("rows signal_name values must be unique")
        seen.add(row.signal_name)
    if normalized != tuple(sorted(normalized, key=_row_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: Iterable[ResearchTeamCrossDomainSignalOverlapReasonCodeCount],
) -> tuple[ResearchTeamCrossDomainSignalOverlapReasonCodeCount, ...]:
    if isinstance(rows, str | bytes):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamCrossDomainSignalOverlapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamCrossDomainSignalOverlapReasonCodeCount values",
            )
        _require_hard_flags("reason_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: REASON_CODES.index(row.reason_code))):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _normalize_team_ids(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError("team_ids must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("team_ids must be an iterable") from exc
    if not items:
        raise ValueError("team_ids must not be empty")
    normalized = tuple(require_team_id("team_id", item) for item in items)
    if len(set(normalized)) != len(normalized):
        raise ValueError("team_ids must contain unique values")
    return tuple(sorted(normalized, key=_TEAM_RANK.__getitem__))


def _normalize_category_ids(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError("category_ids must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("category_ids must be an iterable") from exc
    if not items:
        raise ValueError("category_ids must not be empty")
    normalized = tuple(require_category_id("category_id", item) for item in items)
    if len(set(normalized)) != len(normalized):
        raise ValueError("category_ids must contain unique values")
    return tuple(sorted(normalized, key=_CATEGORY_RANK.__getitem__))


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in normalized:
        _require_member(field_name, reason_code, REASON_CODES)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} values must be unique")
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)
    if normalized != expected:
        raise ValueError(f"{field_name} must use deterministic sorting")
    return normalized


def _reason_code_counts(
    rows: tuple[ResearchTeamCrossDomainSignalOverlapRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamCrossDomainSignalOverlapReasonCodeCount, ...]:
    if not rows and reason_codes == ("no_signals",):
        return (
            ResearchTeamCrossDomainSignalOverlapReasonCodeCount(
                reason_code="no_signals",
                count=_count(1),
            ),
        )
    return tuple(
        ResearchTeamCrossDomainSignalOverlapReasonCodeCount(
            reason_code=reason_code,
            count=_count(sum(1 for row in rows if reason_code in row.reason_codes)),
        )
        for reason_code in reason_codes
    )


def _report_reason_codes(
    rows: tuple[ResearchTeamCrossDomainSignalOverlapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_signals",)
    present = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in present)


def _report_status(rows: tuple[ResearchTeamCrossDomainSignalOverlapRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchTeamCrossDomainSignalOverlapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _need_count(
    rows: tuple[ResearchTeamCrossDomainSignalOverlapRow, ...],
    review_need: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.review_need == review_need))


def _row_key(row: ResearchTeamCrossDomainSignalOverlapRow) -> tuple[Decimal, Decimal, str]:
    return (_STATUS_RANK[row.status], -row.merge_review_score, row.signal_name)


def _validate_signal_times(
    signals: tuple[ResearchTeamCrossDomainSignalObservation, ...],
    generated_at: datetime,
) -> None:
    for signal in signals:
        if signal.observed_at > generated_at:
            raise ValueError("observed_at must be <= generated_at")


def _validate_row(row: ResearchTeamCrossDomainSignalOverlapRow) -> None:
    if row.team_count != _count(len(row.team_ids)):
        raise ValueError("team_count must match team_ids")
    expected_domain_count = _count(
        len({_domain_bucket(category_id) for category_id in row.category_ids}),
    )
    if row.domain_count != expected_domain_count:
        raise ValueError("domain_count must match category_ids")
    if row.review_need != _review_need(row.status):
        raise ValueError("review_need must match status")
    if row.handoff_ready_count > row.team_count:
        raise ValueError("handoff_ready_count must not exceed team_count")


def _validate_report(report: ResearchTeamCrossDomainSignalOverlapReport) -> None:
    expected_counts = {
        "overlap_group_count": _count(len(report.rows)),
        "pass_count": _status_count(report.rows, "pass"),
        "watch_count": _status_count(report.rows, "watch"),
        "block_count": _status_count(report.rows, "block"),
        "handoff_review_count": _need_count(report.rows, "handoff_review"),
        "merge_review_count": _need_count(report.rows, "merge_review"),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.public_digest != _public_digest_from_report(report):
        raise ValueError("public_digest must match public report fields")


def _domain_bucket(category_id: str) -> str:
    if category_id == "politics":
        return "politics"
    if category_id.startswith("finance.crypto."):
        return "crypto"
    if category_id.startswith("sports."):
        return "sports"
    if category_id.startswith("finance."):
        return "macro"
    return "other"


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain a public string")
    _reject_unsafe_public_surface(field_name, value)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    _reject_unsafe_public_surface(field_name, value)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _quantize(_require_decimal(field_name, value))
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _count_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _count_decimal(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest") from exc


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT or denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _mean(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(items, ZERO) / _count(len(items)))


def _reject_public_payload_numerics(value: object) -> None:
    if type(value) in (float, int):
        raise ValueError("public payload numerics must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_payload_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload_numerics(item)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"unsafe public surface in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_surface(label, key)
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))


__all__ = (
    "DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_SIGNAL_OVERLAP_CONFIG_VERSION",
    "ResearchTeamCrossDomainSignalObservation",
    "ResearchTeamCrossDomainSignalOverlapConfig",
    "ResearchTeamCrossDomainSignalOverlapReasonCodeCount",
    "ResearchTeamCrossDomainSignalOverlapReport",
    "ResearchTeamCrossDomainSignalOverlapRow",
    "build_research_team_cross_domain_signal_overlap_report",
    "research_team_cross_domain_signal_overlap_report_digest",
    "research_team_cross_domain_signal_overlap_report_payload",
    "validate_research_team_cross_domain_signal_overlap_report_payload",
)
