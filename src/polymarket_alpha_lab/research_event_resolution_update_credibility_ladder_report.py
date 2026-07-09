"""Phase 1 report-only event resolution update credibility ladder."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_EVENT_RESOLUTION_UPDATE_CREDIBILITY_LADDER_REPORT_CONFIG_VERSION = (
    "research-event-resolution-update-credibility-ladder-report-v0"
)

LADDER_STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("candidate", "_", "id"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "_", "slug"),
    _join_parts("que", "stion"),
    _join_parts("source", "_", "url"),
    _join_parts("source", "_", "text"),
    "dsn",
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("li", "ve"),
    _join_parts("au", "th"),
    _join_parts("siz", "ing"),
    _join_parts("recomm", "end"),
    _join_parts("exec", "ution"),
)

REASON_CODE_SEQUENCE = (
    "credibility_ladder_blocked_contradiction_pressure",
    "credibility_ladder_block_threshold",
    "credibility_ladder_watch_threshold",
    "credibility_ladder_pass_threshold",
    "credibility_ladder_corroboration_quorum_shortfall",
    "credibility_ladder_family_quorum_shortfall",
    "credibility_ladder_stale_update",
    "credibility_ladder_deadline_pressure",
    "credibility_ladder_contradiction_pressure",
    "credibility_ladder_empty",
    "credibility_ladder_block_present",
    "credibility_ladder_watch_present",
    "credibility_ladder_clear",
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
class ResearchEventResolutionUpdateCredibilityLadderConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_UPDATE_CREDIBILITY_LADDER_REPORT_CONFIG_VERSION
    )
    pass_threshold: Decimal = Decimal("0.700000")
    watch_threshold: Decimal = Decimal("0.450000")
    required_corroborating_sources: Decimal = Decimal("3.000000")
    required_independent_source_families: Decimal = Decimal("2.000000")
    blocked_contradiction_count: Decimal = Decimal("3.000000")
    fresh_update_seconds: Decimal = Decimal("1800.000000")
    stale_update_seconds: Decimal = Decimal("7200.000000")
    deadline_proximity_window_seconds: Decimal = Decimal("3600.000000")
    corroboration_weight: Decimal = Decimal("0.250000")
    recency_weight: Decimal = Decimal("0.150000")
    contradiction_penalty_weight: Decimal = Decimal("0.350000")
    deadline_proximity_penalty_weight: Decimal = Decimal("0.100000")
    source_tier_weights: tuple[tuple[str, Decimal], ...] = (
        ("official", Decimal("0.500000")),
        ("primary", Decimal("0.400000")),
        ("reporting", Decimal("0.250000")),
        ("social", Decimal("0.100000")),
        ("unknown", Decimal("0.000000")),
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionUpdateCredibilityLadderConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_UPDATE_CREDIBILITY_LADDER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("pass_threshold", "watch_threshold"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_threshold <= self.watch_threshold:
            raise ValueError("pass_threshold must exceed watch_threshold")
        for field_name in (
            "required_corroborating_sources",
            "required_independent_source_families",
            "blocked_contradiction_count",
            "fresh_update_seconds",
            "stale_update_seconds",
            "deadline_proximity_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_update_seconds <= self.fresh_update_seconds:
            raise ValueError("stale_update_seconds must exceed fresh_update_seconds")
        for field_name in (
            "corroboration_weight",
            "recency_weight",
            "contradiction_penalty_weight",
            "deadline_proximity_penalty_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_tier_weights",
            _normalize_source_tier_weights(self.source_tier_weights),
        )
        require_paper_only_flags("credibility ladder config", self)
        _reject_unsafe_public_value("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionUpdateInput(_FinalPublicDataclass):
    event_key: str
    update_key: str
    source_tier: str
    corroborating_source_count: Decimal
    independent_source_family_count: Decimal
    contradiction_count: Decimal
    observed_at: datetime
    event_deadline_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionUpdateInput, "input")
        for field_name in ("event_key", "update_key", "source_tier"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "corroborating_source_count",
            "independent_source_family_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.event_deadline_at is not None:
            object.__setattr__(
                self,
                "event_deadline_at",
                _as_utc("event_deadline_at", self.event_deadline_at),
            )
        require_paper_only_flags("credibility ladder input", self)
        _reject_unsafe_public_value("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionUpdateCredibilityLadderRow(_FinalPublicDataclass):
    event_key: str
    update_key: str
    source_tier: str
    source_tier_weight: Decimal
    corroborating_source_count: Decimal
    independent_source_family_count: Decimal
    contradiction_count: Decimal
    corroboration_score: Decimal
    recency_score: Decimal
    contradiction_penalty: Decimal
    deadline_proximity_penalty: Decimal
    seconds_since_observed: Decimal
    seconds_to_deadline: Decimal | None
    credibility_score: Decimal
    ladder_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionUpdateCredibilityLadderRow,
            "row",
        )
        for field_name in ("event_key", "update_key", "source_tier"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "source_tier_weight",
            "corroborating_source_count",
            "independent_source_family_count",
            "contradiction_count",
            "corroboration_score",
            "recency_score",
            "contradiction_penalty",
            "deadline_proximity_penalty",
            "seconds_since_observed",
            "credibility_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "seconds_to_deadline",
            _normalize_optional_decimal("seconds_to_deadline", self.seconds_to_deadline),
        )
        _require_ladder_status("ladder_status", self.ladder_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        require_paper_only_flags("credibility ladder row", self)
        _reject_unsafe_public_value("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionUpdateCredibilityLadderReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    ladder_status: str
    update_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_credibility_score: Decimal
    max_contradiction_penalty: Decimal
    min_seconds_to_deadline: Decimal | None
    rows: tuple[ResearchEventResolutionUpdateCredibilityLadderRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionUpdateCredibilityLadderReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_ladder_status("ladder_status", self.ladder_status)
        for field_name in (
            "update_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_credibility_score",
            "max_contradiction_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_seconds_to_deadline",
            _normalize_optional_decimal(
                "min_seconds_to_deadline",
                self.min_seconds_to_deadline,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report(self)
        require_paper_only_flags("credibility ladder report", self)
        _reject_unsafe_public_value("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _digest_from_payload(_public_payload(self, include_digest=False)),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            expected = _digest_from_payload(_public_payload(self, include_digest=False))
            if self.derived_validation_digest != expected:
                raise ValueError("derived_validation_digest does not match public payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        _validate_report_for_export(self)
        payload = _public_payload(self, include_digest=True)
        _validate_public_payload_schema(payload)
        return payload


def build_research_event_resolution_update_credibility_ladder_report(
    updates: Sequence[ResearchEventResolutionUpdateInput],
    *,
    config: ResearchEventResolutionUpdateCredibilityLadderConfig,
    generated_at: datetime,
) -> ResearchEventResolutionUpdateCredibilityLadderReport:
    if type(config) is not ResearchEventResolutionUpdateCredibilityLadderConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionUpdateCredibilityLadderConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_updates = _normalize_updates(updates, generated_at=generated_at_utc)
    rows = _sort_rows(
        tuple(_row_from_update(item, config=config, generated_at=generated_at_utc) for item in normalized_updates),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "ladder_status": _report_status(rows),
        "update_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_credibility_score": _average(tuple(row.credibility_score for row in rows)),
        "max_contradiction_penalty": max(
            (row.contradiction_penalty for row in rows),
            default=ZERO,
        ),
        "min_seconds_to_deadline": _min_seconds_to_deadline(rows),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionUpdateCredibilityLadderReport(**values)


def research_event_resolution_update_credibility_ladder_report_to_payload(
    report: ResearchEventResolutionUpdateCredibilityLadderReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionUpdateCredibilityLadderReport:
        raise ValueError(
            "report must be a ResearchEventResolutionUpdateCredibilityLadderReport",
        )
    require_paper_only_flags("credibility ladder report", report)
    return report.public_payload


def _normalize_updates(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchEventResolutionUpdateInput, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("updates must be a sequence")
    updates = tuple(value)
    seen: set[tuple[str, str]] = set()
    for item in updates:
        if type(item) is not ResearchEventResolutionUpdateInput:
            raise ValueError("updates must contain credibility ladder inputs")
        require_paper_only_flags("credibility ladder input", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (item.event_key, item.update_key)
        if key in seen:
            raise ValueError("update_key must be unique per event_key")
        seen.add(key)
    return tuple(sorted(updates, key=lambda item: (item.event_key, item.update_key)))


def _row_from_update(
    item: ResearchEventResolutionUpdateInput,
    *,
    config: ResearchEventResolutionUpdateCredibilityLadderConfig,
    generated_at: datetime,
) -> ResearchEventResolutionUpdateCredibilityLadderRow:
    source_tier_weight = _source_tier_weight(item.source_tier, config)
    corroboration_score = _corroboration_score(item, config)
    seconds_since_observed = _age_seconds(generated_at, item.observed_at)
    recency_score = _recency_score(seconds_since_observed, config)
    contradiction_penalty = _contradiction_penalty(item.contradiction_count, config)
    seconds_to_deadline = _seconds_to_deadline(generated_at, item.event_deadline_at)
    deadline_penalty = _deadline_penalty(seconds_to_deadline, config)
    credibility_score = _clamp_ratio(
        source_tier_weight
        + corroboration_score
        + recency_score
        - contradiction_penalty
        - deadline_penalty,
    )
    status = _row_status(
        item,
        config=config,
        credibility_score=credibility_score,
    )
    return ResearchEventResolutionUpdateCredibilityLadderRow(
        event_key=item.event_key,
        update_key=item.update_key,
        source_tier=item.source_tier,
        source_tier_weight=source_tier_weight,
        corroborating_source_count=item.corroborating_source_count,
        independent_source_family_count=item.independent_source_family_count,
        contradiction_count=item.contradiction_count,
        corroboration_score=corroboration_score,
        recency_score=recency_score,
        contradiction_penalty=contradiction_penalty,
        deadline_proximity_penalty=deadline_penalty,
        seconds_since_observed=seconds_since_observed,
        seconds_to_deadline=seconds_to_deadline,
        credibility_score=credibility_score,
        ladder_status=status,
        reason_codes=_row_reason_codes(
            item,
            config=config,
            status=status,
            credibility_score=credibility_score,
            seconds_since_observed=seconds_since_observed,
            seconds_to_deadline=seconds_to_deadline,
        ),
    )


def _row_status(
    item: ResearchEventResolutionUpdateInput,
    *,
    config: ResearchEventResolutionUpdateCredibilityLadderConfig,
    credibility_score: Decimal,
) -> str:
    if item.contradiction_count >= config.blocked_contradiction_count:
        return "block"
    if credibility_score < config.watch_threshold:
        return "block"
    if (
        credibility_score >= config.pass_threshold
        and item.corroborating_source_count >= config.required_corroborating_sources
        and item.independent_source_family_count >= config.required_independent_source_families
        and item.contradiction_count == ZERO
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    item: ResearchEventResolutionUpdateInput,
    *,
    config: ResearchEventResolutionUpdateCredibilityLadderConfig,
    status: str,
    credibility_score: Decimal,
    seconds_since_observed: Decimal,
    seconds_to_deadline: Decimal | None,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.contradiction_count >= config.blocked_contradiction_count:
        reason_codes.append("credibility_ladder_blocked_contradiction_pressure")
    elif status == "block" and credibility_score < config.watch_threshold:
        reason_codes.append("credibility_ladder_block_threshold")
    elif status == "watch":
        reason_codes.append("credibility_ladder_watch_threshold")
    elif status == "pass":
        reason_codes.append("credibility_ladder_pass_threshold")
    if item.corroborating_source_count < config.required_corroborating_sources:
        reason_codes.append("credibility_ladder_corroboration_quorum_shortfall")
    if item.independent_source_family_count < config.required_independent_source_families:
        reason_codes.append("credibility_ladder_family_quorum_shortfall")
    if seconds_since_observed >= config.stale_update_seconds:
        reason_codes.append("credibility_ladder_stale_update")
    if _has_deadline_pressure(seconds_to_deadline, config):
        reason_codes.append("credibility_ladder_deadline_pressure")
    if ZERO < item.contradiction_count < config.blocked_contradiction_count:
        reason_codes.append("credibility_ladder_contradiction_pressure")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionUpdateCredibilityLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("credibility_ladder_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    if any(row.ladder_status == "block" for row in rows):
        reason_codes.append("credibility_ladder_block_present")
    elif any(row.ladder_status == "watch" for row in rows):
        reason_codes.append("credibility_ladder_watch_present")
    else:
        reason_codes.append("credibility_ladder_clear")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchEventResolutionUpdateCredibilityLadderRow, ...],
) -> str:
    if any(row.ladder_status == "block" for row in rows):
        return "block"
    if any(row.ladder_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _validate_row(row: ResearchEventResolutionUpdateCredibilityLadderRow) -> None:
    if row.credibility_score > ONE:
        raise ValueError("credibility_score must be at most one")
    if row.source_tier_weight > ONE:
        raise ValueError("source_tier_weight must be at most one")
    if row.corroboration_score > ONE:
        raise ValueError("corroboration_score must be at most one")
    if row.recency_score > ONE:
        raise ValueError("recency_score must be at most one")
    if row.contradiction_penalty > ONE:
        raise ValueError("contradiction_penalty must be at most one")
    if row.deadline_proximity_penalty > ONE:
        raise ValueError("deadline_proximity_penalty must be at most one")
    if row.ladder_status == "pass" and (
        "credibility_ladder_pass_threshold" not in row.reason_codes
    ):
        raise ValueError("pass rows require pass reason")
    if row.ladder_status == "watch" and (
        "credibility_ladder_watch_threshold" not in row.reason_codes
    ):
        raise ValueError("watch rows require watch reason")
    if row.ladder_status == "block" and not any(
        reason_code
        in (
            "credibility_ladder_blocked_contradiction_pressure",
            "credibility_ladder_block_threshold",
        )
        for reason_code in row.reason_codes
    ):
        raise ValueError("block rows require block reason")


def _validate_report(report: ResearchEventResolutionUpdateCredibilityLadderReport) -> None:
    if report.update_count != _decimal_count(len(report.rows)):
        raise ValueError("update_count must match rows")
    for status, field_name in (
        ("pass", "pass_count"),
        ("watch", "watch_count"),
        ("block", "block_count"),
    ):
        if getattr(report, field_name) != _decimal_count(_status_count(report.rows, status)):
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.update_count:
        raise ValueError("status counts must sum to update_count")
    if report.average_credibility_score != _average(
        tuple(row.credibility_score for row in report.rows),
    ):
        raise ValueError("average_credibility_score must match rows")
    if report.max_contradiction_penalty != max(
        (row.contradiction_penalty for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_penalty must match rows")
    if report.min_seconds_to_deadline != _min_seconds_to_deadline(report.rows):
        raise ValueError("min_seconds_to_deadline must match rows")
    if report.ladder_status != _report_status(report.rows):
        raise ValueError("ladder_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _validate_report_for_export(
    report: ResearchEventResolutionUpdateCredibilityLadderReport,
) -> None:
    _require_exact_type(
        report,
        ResearchEventResolutionUpdateCredibilityLadderReport,
        "report",
    )
    _as_utc("generated_at", report.generated_at)
    _require_public_identifier("config_version", report.config_version)
    _require_ladder_status("ladder_status", report.ladder_status)
    for field_name in (
        "update_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_credibility_score",
        "max_contradiction_penalty",
    ):
        _require_nonnegative_decimal(field_name, getattr(report, field_name))
    _normalize_optional_decimal(
        "min_seconds_to_deadline",
        report.min_seconds_to_deadline,
    )
    if type(report.rows) is not tuple:
        raise ValueError("rows must remain constructor-normalized")
    for row in report.rows:
        _validate_row_for_export(row)
    if report.rows != _sort_rows(report.rows):
        raise ValueError("rows must remain canonically sorted")
    if type(report.reason_codes) is not tuple:
        raise ValueError("reason_codes must remain constructor-normalized")
    if report.reason_codes != _normalize_reason_codes(report.reason_codes):
        raise ValueError("reason_codes must remain canonical")
    _validate_report(report)
    require_paper_only_flags("credibility ladder report", report)
    _reject_unsafe_public_value("report", report)
    _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    expected = _digest_from_payload(_public_payload(report, include_digest=False))
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _validate_row_for_export(
    row: ResearchEventResolutionUpdateCredibilityLadderRow,
) -> None:
    _require_exact_type(
        row,
        ResearchEventResolutionUpdateCredibilityLadderRow,
        "row",
    )
    for field_name in ("event_key", "update_key", "source_tier"):
        _require_public_identifier(field_name, getattr(row, field_name))
    for field_name in (
        "source_tier_weight",
        "corroborating_source_count",
        "independent_source_family_count",
        "contradiction_count",
        "corroboration_score",
        "recency_score",
        "contradiction_penalty",
        "deadline_proximity_penalty",
        "seconds_since_observed",
        "credibility_score",
    ):
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
    _normalize_optional_decimal("seconds_to_deadline", row.seconds_to_deadline)
    _require_ladder_status("ladder_status", row.ladder_status)
    if type(row.reason_codes) is not tuple:
        raise ValueError("reason_codes must remain constructor-normalized")
    if row.reason_codes != _normalize_reason_codes(row.reason_codes):
        raise ValueError("reason_codes must remain canonical")
    _validate_row(row)
    require_paper_only_flags("credibility ladder row", row)
    _reject_unsafe_public_value("row", row)


def _normalize_source_tier_weights(value: object) -> tuple[tuple[str, Decimal], ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("source_tier_weights must be a sequence")
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for row in value:
        if type(row) not in (tuple, list) or len(row) != 2:
            raise ValueError("source_tier_weights rows must contain tier and weight")
        source_tier, weight = row
        _require_public_identifier("source_tier", source_tier)
        if source_tier in seen:
            raise ValueError("source_tier_weights must be unique by source_tier")
        seen.add(source_tier)
        normalized.append((source_tier, _require_ratio_decimal("source_tier_weights", weight)))
    if not normalized:
        raise ValueError("source_tier_weights must not be empty")
    return tuple(sorted(normalized, key=lambda row: row[0]))


def _normalize_rows(
    value: object,
) -> tuple[ResearchEventResolutionUpdateCredibilityLadderRow, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("rows must be a sequence")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchEventResolutionUpdateCredibilityLadderRow:
            raise ValueError("rows must contain credibility ladder rows")
        require_paper_only_flags("credibility ladder row", row)
    return _sort_rows(rows)


def _sort_rows(
    rows: tuple[ResearchEventResolutionUpdateCredibilityLadderRow, ...],
) -> tuple[ResearchEventResolutionUpdateCredibilityLadderRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.ladder_status],
                row.event_key,
                row.update_key,
            ),
        ),
    )


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in value:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _source_tier_weight(
    source_tier: str,
    config: ResearchEventResolutionUpdateCredibilityLadderConfig,
) -> Decimal:
    weights = dict(config.source_tier_weights)
    if source_tier not in weights:
        raise ValueError("source_tier must be configured")
    return weights[source_tier]


def _corroboration_score(
    item: ResearchEventResolutionUpdateInput,
    config: ResearchEventResolutionUpdateCredibilityLadderConfig,
) -> Decimal:
    corroborating_ratio = _ratio(
        item.corroborating_source_count,
        config.required_corroborating_sources,
    )
    family_ratio = _ratio(
        item.independent_source_family_count,
        config.required_independent_source_families,
    )
    return _quantize(min(corroborating_ratio, family_ratio, ONE) * config.corroboration_weight)


def _recency_score(
    seconds_since_observed: Decimal,
    config: ResearchEventResolutionUpdateCredibilityLadderConfig,
) -> Decimal:
    if seconds_since_observed <= config.fresh_update_seconds:
        return config.recency_weight
    if seconds_since_observed >= config.stale_update_seconds:
        return ZERO
    remaining = config.stale_update_seconds - seconds_since_observed
    span = config.stale_update_seconds - config.fresh_update_seconds
    return _quantize(_ratio(remaining, span) * config.recency_weight)


def _contradiction_penalty(
    contradiction_count: Decimal,
    config: ResearchEventResolutionUpdateCredibilityLadderConfig,
) -> Decimal:
    pressure = min(_ratio(contradiction_count, config.blocked_contradiction_count), ONE)
    return _quantize(pressure * config.contradiction_penalty_weight)


def _deadline_penalty(
    seconds_to_deadline: Decimal | None,
    config: ResearchEventResolutionUpdateCredibilityLadderConfig,
) -> Decimal:
    if not _has_deadline_pressure(seconds_to_deadline, config):
        return ZERO
    return config.deadline_proximity_penalty_weight


def _has_deadline_pressure(
    seconds_to_deadline: Decimal | None,
    config: ResearchEventResolutionUpdateCredibilityLadderConfig,
) -> bool:
    return (
        seconds_to_deadline is not None
        and seconds_to_deadline <= config.deadline_proximity_window_seconds
    )


def _seconds_to_deadline(
    generated_at: datetime,
    deadline_at: datetime | None,
) -> Decimal | None:
    if deadline_at is None:
        return None
    return _signed_age_seconds(deadline_at, generated_at)


def _min_seconds_to_deadline(
    rows: tuple[ResearchEventResolutionUpdateCredibilityLadderRow, ...],
) -> Decimal | None:
    values = tuple(row.seconds_to_deadline for row in rows if row.seconds_to_deadline is not None)
    if not values:
        return None
    return min(values)


def _status_count(
    rows: tuple[ResearchEventResolutionUpdateCredibilityLadderRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.ladder_status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = 64
        return _quantize(numerator / denominator)


def _age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    value = _signed_age_seconds(end_at, start_at)
    if value < ZERO:
        raise ValueError("age_seconds must be nonnegative")
    return value


def _signed_age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    return _quantize(
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    decimal_value = _require_decimal(field_name, value)
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = _quantize(value)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value == ZERO:
        return ZERO
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_ladder_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in LADDER_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _public_payload(
    report: ResearchEventResolutionUpdateCredibilityLadderReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    values = asdict(report)
    digest = values.pop("derived_validation_digest", "")
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("public payload must be an object")
    if include_digest:
        payload["derived_validation_digest"] = digest
    _reject_unsafe_public_value("public payload", payload, allow_json_containers=True)
    return payload


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_exact_payload_keys(
        "public payload",
        payload,
        tuple(
            field.name
            for field in fields(
                ResearchEventResolutionUpdateCredibilityLadderReport,
            )
        ),
    )
    _validate_payload_datetime("generated_at", payload["generated_at"])
    _require_public_identifier("config_version", payload["config_version"])
    _require_ladder_status("ladder_status", payload["ladder_status"])
    for field_name in ("update_count", "pass_count", "watch_count", "block_count"):
        _validate_payload_decimal(field_name, payload[field_name], nonnegative=True)
    for field_name in (
        "average_credibility_score",
        "max_contradiction_penalty",
    ):
        _validate_payload_decimal(
            field_name,
            payload[field_name],
            nonnegative=True,
            ratio=True,
        )
    _validate_optional_payload_decimal(
        "min_seconds_to_deadline",
        payload["min_seconds_to_deadline"],
    )
    rows_payload = payload["rows"]
    if type(rows_payload) is not list:
        raise ValueError("rows must be a JSON list")
    for index, row_payload in enumerate(rows_payload):
        _validate_row_payload_schema(index, row_payload)
    _validate_reason_codes_payload("reason_codes", payload["reason_codes"])
    _validate_payload_flags("public payload", payload)
    provided_digest = _require_sha256_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    if provided_digest != _digest_from_payload(digest_payload):
        raise ValueError("derived_validation_digest does not match public payload")


def _validate_row_payload_schema(index: int, value: object) -> None:
    if type(value) is not dict:
        raise ValueError(f"rows[{index}] must be a JSON object")
    _require_exact_payload_keys(
        f"rows[{index}]",
        value,
        tuple(
            field.name
            for field in fields(
                ResearchEventResolutionUpdateCredibilityLadderRow,
            )
        ),
    )
    for field_name in ("event_key", "update_key", "source_tier"):
        _require_public_identifier(field_name, value[field_name])
    for field_name in (
        "source_tier_weight",
        "corroboration_score",
        "recency_score",
        "contradiction_penalty",
        "deadline_proximity_penalty",
        "credibility_score",
    ):
        _validate_payload_decimal(
            field_name,
            value[field_name],
            nonnegative=True,
            ratio=True,
        )
    for field_name in (
        "corroborating_source_count",
        "independent_source_family_count",
        "contradiction_count",
        "seconds_since_observed",
    ):
        _validate_payload_decimal(field_name, value[field_name], nonnegative=True)
    _validate_optional_payload_decimal(
        "seconds_to_deadline",
        value["seconds_to_deadline"],
    )
    _require_ladder_status("ladder_status", value["ladder_status"])
    _validate_reason_codes_payload("reason_codes", value["reason_codes"])
    _validate_payload_flags(f"rows[{index}]", value)


def _require_exact_payload_keys(
    label: str,
    payload: object,
    expected_fields: tuple[str, ...],
) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    if set(payload) != set(expected_fields) or len(payload) != len(expected_fields):
        raise ValueError(f"{label} fields do not match public schema")


def _validate_payload_datetime(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    if _as_utc(field_name, parsed).isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")


def _validate_payload_decimal(
    field_name: str,
    value: object,
    *,
    nonnegative: bool,
    ratio: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if ratio:
        normalized = _require_ratio_decimal(field_name, parsed)
    elif nonnegative:
        normalized = _require_nonnegative_decimal(field_name, parsed)
    else:
        normalized = _require_decimal(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _validate_optional_payload_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _validate_payload_decimal(field_name, value, nonnegative=False)


def _validate_reason_codes_payload(field_name: str, value: object) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON list")
    normalized = _normalize_reason_codes(tuple(value))
    if list(normalized) != value:
        raise ValueError(f"{field_name} must remain canonical")


def _validate_payload_flags(label: str, payload: Mapping[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _digest_from_payload(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_value("digest payload", payload, allow_json_containers=True)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return str(_require_decimal("Decimal payload value", value))
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
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
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_value(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_value(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_value(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_value(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_UPDATE_CREDIBILITY_LADDER_REPORT_CONFIG_VERSION",
    "ResearchEventResolutionUpdateCredibilityLadderConfig",
    "ResearchEventResolutionUpdateCredibilityLadderReport",
    "ResearchEventResolutionUpdateCredibilityLadderRow",
    "ResearchEventResolutionUpdateInput",
    "build_research_event_resolution_update_credibility_ladder_report",
    "research_event_resolution_update_credibility_ladder_report_to_payload",
)
