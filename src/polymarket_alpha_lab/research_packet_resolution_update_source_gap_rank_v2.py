from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_RESOLUTION_UPDATE_SOURCE_GAP_RANK_V2_CONFIG_VERSION = (
    "research-packet-resolution-update-source-gap-rank-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
ZERO_SECONDS = Decimal("0.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")

GAP_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "resolution_update_missing",
    "resolution_update_watch_stale",
    "resolution_update_block_stale",
    "official_resolution_update_missing",
    "source_count_below_required",
    "official_resolution_update_recent",
    "resolution_update_source_gap_clear",
)
REPORT_REASON_CODES = (
    "source_gap_packets_clear",
    "source_gap_watch_packets_present",
    "source_gap_blocked_packets_present",
    "resolution_updates_missing",
    "resolution_updates_stale",
    "official_resolution_updates_missing",
    "source_counts_below_required",
    "official_resolution_updates_recent",
)
UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
PUBLIC_VALUE_TERM_ALLOWLIST_KEYS = frozenset(("config_version",))
SAFETY_FLAG_NAMES = frozenset(("paper_only", "report_only", "readonly"))


@dataclass(frozen=True)
class ResearchPacketResolutionUpdateSourceGapRankV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_RESOLUTION_UPDATE_SOURCE_GAP_RANK_V2_CONFIG_VERSION
    )
    stale_update_watch_after_seconds: Decimal = Decimal("3600.000000")
    stale_update_block_after_seconds: Decimal = Decimal("7200.000000")
    recent_official_update_boost_seconds: Decimal = Decimal("1800.000000")
    missing_update_penalty_score: Decimal = Decimal("0.500000")
    stale_update_watch_penalty_score: Decimal = Decimal("0.200000")
    stale_update_block_penalty_score: Decimal = Decimal("0.350000")
    missing_official_update_penalty_score: Decimal = Decimal("0.100000")
    low_source_count_penalty_score: Decimal = Decimal("0.150000")
    official_update_boost_score: Decimal = Decimal("0.100000")
    blocked_gap_score: Decimal = Decimal("0.700000")
    watch_gap_score: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string(
            "config_version",
            self.config_version,
            allow_public_terms=True,
        )
        for field_name in (
            "stale_update_watch_after_seconds",
            "stale_update_block_after_seconds",
            "recent_official_update_boost_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "missing_update_penalty_score",
            "stale_update_watch_penalty_score",
            "stale_update_block_penalty_score",
            "missing_official_update_penalty_score",
            "low_source_count_penalty_score",
            "official_update_boost_score",
            "blocked_gap_score",
            "watch_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.stale_update_watch_after_seconds > self.stale_update_block_after_seconds:
            raise ValueError(
                "stale_update_watch_after_seconds must not exceed stale_update_block_after_seconds",
            )
        if self.watch_gap_score > self.blocked_gap_score:
            raise ValueError("watch_gap_score must not exceed blocked_gap_score")
        _require_hard_flags("ResearchPacketResolutionUpdateSourceGapRankV2Config", self)


@dataclass(frozen=True)
class ResearchPacketResolutionUpdateSourceGapRankV2Input:
    packet_id: str
    market_id: str
    update_source_id: str
    latest_resolution_update_at: datetime | None
    latest_official_resolution_update_at: datetime | None
    source_count: Decimal
    required_source_count: Decimal
    update_relevance_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("update_source_id", self.update_source_id)
        object.__setattr__(
            self,
            "latest_resolution_update_at",
            _as_optional_utc(
                "latest_resolution_update_at",
                self.latest_resolution_update_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_official_resolution_update_at",
            _as_optional_utc(
                "latest_official_resolution_update_at",
                self.latest_official_resolution_update_at,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "required_source_count",
            _normalize_positive_count("required_source_count", self.required_source_count),
        )
        object.__setattr__(
            self,
            "update_relevance_score",
            _normalize_ratio("update_relevance_score", self.update_relevance_score),
        )
        _require_hard_flags("ResearchPacketResolutionUpdateSourceGapRankV2Input", self)


@dataclass(frozen=True)
class ResearchPacketResolutionUpdateSourceGapRankV2Row:
    gap_rank: Decimal
    packet_id: str
    market_id: str
    update_source_id: str
    gap_status: str
    latest_resolution_update_at: datetime | None
    latest_official_resolution_update_at: datetime | None
    resolution_update_age_seconds: Decimal | None
    official_resolution_update_age_seconds: Decimal | None
    source_count: Decimal
    required_source_count: Decimal
    source_count_shortfall: Decimal
    source_coverage_ratio: Decimal
    update_relevance_score: Decimal
    missing_update_penalty_score: Decimal
    stale_update_penalty_score: Decimal
    unofficial_update_penalty_score: Decimal
    low_source_count_penalty_score: Decimal
    official_update_boost_score: Decimal
    source_gap_score: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "gap_rank", _normalize_positive_count("gap_rank", self.gap_rank))
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("update_source_id", self.update_source_id)
        _require_member("gap_status", self.gap_status, GAP_STATUSES)
        object.__setattr__(
            self,
            "latest_resolution_update_at",
            _as_optional_utc(
                "latest_resolution_update_at",
                self.latest_resolution_update_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_official_resolution_update_at",
            _as_optional_utc(
                "latest_official_resolution_update_at",
                self.latest_official_resolution_update_at,
            ),
        )
        for field_name in (
            "resolution_update_age_seconds",
            "official_resolution_update_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_seconds(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("source_count", "required_source_count", "source_count_shortfall"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_source_count",
            _normalize_positive_count("required_source_count", self.required_source_count),
        )
        for field_name in (
            "source_coverage_ratio",
            "update_relevance_score",
            "missing_update_penalty_score",
            "stale_update_penalty_score",
            "unofficial_update_penalty_score",
            "low_source_count_penalty_score",
            "official_update_boost_score",
            "source_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("ResearchPacketResolutionUpdateSourceGapRankV2Row", self)
        _validate_digest(self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketResolutionUpdateSourceGapRankV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    packet_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    missing_update_count: Decimal
    stale_update_count: Decimal
    missing_official_update_count: Decimal
    low_source_count: Decimal
    official_update_boost_count: Decimal
    max_source_gap_score: Decimal
    rows: tuple[ResearchPacketResolutionUpdateSourceGapRankV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string(
            "config_version",
            self.config_version,
            allow_public_terms=True,
        )
        _require_member("report_status", self.report_status, GAP_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        for field_name in (
            "packet_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "missing_update_count",
            "stale_update_count",
            "missing_official_update_count",
            "low_source_count",
            "official_update_boost_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_gap_score",
            _normalize_ratio("max_source_gap_score", self.max_source_gap_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("ResearchPacketResolutionUpdateSourceGapRankV2Report", self)
        _validate_digest(self)
        _validate_report(self)


@dataclass(frozen=True)
class _GapDraft:
    packet_id: str
    market_id: str
    update_source_id: str
    gap_status: str
    latest_resolution_update_at: datetime | None
    latest_official_resolution_update_at: datetime | None
    resolution_update_age_seconds: Decimal | None
    official_resolution_update_age_seconds: Decimal | None
    source_count: Decimal
    required_source_count: Decimal
    source_count_shortfall: Decimal
    source_coverage_ratio: Decimal
    update_relevance_score: Decimal
    missing_update_penalty_score: Decimal
    stale_update_penalty_score: Decimal
    unofficial_update_penalty_score: Decimal
    low_source_count_penalty_score: Decimal
    official_update_boost_score: Decimal
    source_gap_score: Decimal
    reason_codes: tuple[str, ...]


def build_research_packet_resolution_update_source_gap_rank_v2_report(
    inputs: list[ResearchPacketResolutionUpdateSourceGapRankV2Input]
    | tuple[ResearchPacketResolutionUpdateSourceGapRankV2Input, ...],
    *,
    config: ResearchPacketResolutionUpdateSourceGapRankV2Config,
    generated_at: datetime,
) -> ResearchPacketResolutionUpdateSourceGapRankV2Report:
    if type(config) is not ResearchPacketResolutionUpdateSourceGapRankV2Config:
        raise ValueError(
            "config must be a ResearchPacketResolutionUpdateSourceGapRankV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs, generated_at_utc)
    drafts = tuple(
        _draft_from_input(row, config=config, generated_at=generated_at_utc)
        for row in normalized_inputs
    )
    rows = tuple(
        _row_from_draft(draft, _count(index))
        for index, draft in enumerate(sorted(drafts, key=_draft_sort_key), start=1)
    )
    return ResearchPacketResolutionUpdateSourceGapRankV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        packet_count=_count(len(rows)),
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        missing_update_count=_reason_count(rows, "resolution_update_missing"),
        stale_update_count=_stale_update_count(rows),
        missing_official_update_count=_reason_count(
            rows,
            "official_resolution_update_missing",
        ),
        low_source_count=_reason_count(rows, "source_count_below_required"),
        official_update_boost_count=_reason_count(
            rows,
            "official_resolution_update_recent",
        ),
        max_source_gap_score=_max_ratio(tuple(row.source_gap_score for row in rows)),
        rows=rows,
    )


def research_packet_resolution_update_source_gap_rank_v2_payload(
    report: ResearchPacketResolutionUpdateSourceGapRankV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketResolutionUpdateSourceGapRankV2Report:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchPacketResolutionUpdateSourceGapRankV2Report or payload",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_payload_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digests(payload)
    return payload


def _normalize_inputs(
    inputs: list[ResearchPacketResolutionUpdateSourceGapRankV2Input]
    | tuple[ResearchPacketResolutionUpdateSourceGapRankV2Input, ...],
    generated_at: datetime,
) -> tuple[ResearchPacketResolutionUpdateSourceGapRankV2Input, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_packet_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketResolutionUpdateSourceGapRankV2Input:
            raise ValueError(
                "inputs must contain ResearchPacketResolutionUpdateSourceGapRankV2Input values",
            )
        _require_hard_flags("input", row)
        if row.packet_id in seen_packet_ids:
            raise ValueError("inputs must not contain duplicate packet_id values")
        seen_packet_ids.add(row.packet_id)
        for field_name in (
            "latest_resolution_update_at",
            "latest_official_resolution_update_at",
        ):
            value = getattr(row, field_name)
            if value is not None and value > generated_at:
                raise ValueError(f"{field_name} must not be after generated_at")
    return rows


def _draft_from_input(
    row: ResearchPacketResolutionUpdateSourceGapRankV2Input,
    *,
    config: ResearchPacketResolutionUpdateSourceGapRankV2Config,
    generated_at: datetime,
) -> _GapDraft:
    update_age_seconds = _age_seconds(row.latest_resolution_update_at, generated_at)
    official_age_seconds = _age_seconds(
        row.latest_official_resolution_update_at,
        generated_at,
    )
    source_count_shortfall = _source_count_shortfall(
        row.source_count,
        row.required_source_count,
    )
    source_coverage_ratio = _source_coverage_ratio(
        row.source_count,
        row.required_source_count,
    )
    missing_update_penalty = (
        config.missing_update_penalty_score
        if update_age_seconds is None
        else ZERO_RATIO
    )
    stale_update_penalty = _stale_update_penalty(update_age_seconds, config)
    unofficial_update_penalty = (
        config.missing_official_update_penalty_score
        if official_age_seconds is None
        else ZERO_RATIO
    )
    low_source_count_penalty = (
        config.low_source_count_penalty_score
        if source_count_shortfall > ZERO_COUNT
        else ZERO_RATIO
    )
    official_update_boost = _official_update_boost(official_age_seconds, config)
    source_gap_score = _source_gap_score(
        update_relevance_score=row.update_relevance_score,
        missing_update_penalty_score=missing_update_penalty,
        stale_update_penalty_score=stale_update_penalty,
        unofficial_update_penalty_score=unofficial_update_penalty,
        low_source_count_penalty_score=low_source_count_penalty,
        official_update_boost_score=official_update_boost,
    )
    reason_codes = _row_reason_codes(
        update_age_seconds=update_age_seconds,
        official_age_seconds=official_age_seconds,
        source_count_shortfall=source_count_shortfall,
        config=config,
    )
    return _GapDraft(
        packet_id=row.packet_id,
        market_id=row.market_id,
        update_source_id=row.update_source_id,
        gap_status=_gap_status(
            reason_codes=reason_codes,
            source_gap_score=source_gap_score,
            config=config,
        ),
        latest_resolution_update_at=row.latest_resolution_update_at,
        latest_official_resolution_update_at=row.latest_official_resolution_update_at,
        resolution_update_age_seconds=update_age_seconds,
        official_resolution_update_age_seconds=official_age_seconds,
        source_count=row.source_count,
        required_source_count=row.required_source_count,
        source_count_shortfall=source_count_shortfall,
        source_coverage_ratio=source_coverage_ratio,
        update_relevance_score=row.update_relevance_score,
        missing_update_penalty_score=missing_update_penalty,
        stale_update_penalty_score=stale_update_penalty,
        unofficial_update_penalty_score=unofficial_update_penalty,
        low_source_count_penalty_score=low_source_count_penalty,
        official_update_boost_score=official_update_boost,
        source_gap_score=source_gap_score,
        reason_codes=reason_codes,
    )


def _row_from_draft(
    draft: _GapDraft,
    gap_rank: Decimal,
) -> ResearchPacketResolutionUpdateSourceGapRankV2Row:
    return ResearchPacketResolutionUpdateSourceGapRankV2Row(
        gap_rank=gap_rank,
        packet_id=draft.packet_id,
        market_id=draft.market_id,
        update_source_id=draft.update_source_id,
        gap_status=draft.gap_status,
        latest_resolution_update_at=draft.latest_resolution_update_at,
        latest_official_resolution_update_at=draft.latest_official_resolution_update_at,
        resolution_update_age_seconds=draft.resolution_update_age_seconds,
        official_resolution_update_age_seconds=draft.official_resolution_update_age_seconds,
        source_count=draft.source_count,
        required_source_count=draft.required_source_count,
        source_count_shortfall=draft.source_count_shortfall,
        source_coverage_ratio=draft.source_coverage_ratio,
        update_relevance_score=draft.update_relevance_score,
        missing_update_penalty_score=draft.missing_update_penalty_score,
        stale_update_penalty_score=draft.stale_update_penalty_score,
        unofficial_update_penalty_score=draft.unofficial_update_penalty_score,
        low_source_count_penalty_score=draft.low_source_count_penalty_score,
        official_update_boost_score=draft.official_update_boost_score,
        source_gap_score=draft.source_gap_score,
        reason_codes=draft.reason_codes,
    )


def _row_reason_codes(
    *,
    update_age_seconds: Decimal | None,
    official_age_seconds: Decimal | None,
    source_count_shortfall: Decimal,
    config: ResearchPacketResolutionUpdateSourceGapRankV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if update_age_seconds is None:
        reason_codes.append("resolution_update_missing")
    elif update_age_seconds >= config.stale_update_block_after_seconds:
        reason_codes.append("resolution_update_block_stale")
    elif update_age_seconds >= config.stale_update_watch_after_seconds:
        reason_codes.append("resolution_update_watch_stale")
    official_recent = False
    if official_age_seconds is None:
        reason_codes.append("official_resolution_update_missing")
    elif official_age_seconds <= config.recent_official_update_boost_seconds:
        official_recent = True
    if source_count_shortfall > ZERO_COUNT:
        reason_codes.append("source_count_below_required")
    if official_recent:
        reason_codes.append("official_resolution_update_recent")
    if not reason_codes:
        reason_codes.append("resolution_update_source_gap_clear")
    return tuple(reason_codes)


def _stale_update_penalty(
    update_age_seconds: Decimal | None,
    config: ResearchPacketResolutionUpdateSourceGapRankV2Config,
) -> Decimal:
    if update_age_seconds is None:
        return ZERO_RATIO
    if update_age_seconds >= config.stale_update_block_after_seconds:
        return config.stale_update_block_penalty_score
    if update_age_seconds >= config.stale_update_watch_after_seconds:
        return config.stale_update_watch_penalty_score
    return ZERO_RATIO


def _official_update_boost(
    official_age_seconds: Decimal | None,
    config: ResearchPacketResolutionUpdateSourceGapRankV2Config,
) -> Decimal:
    if official_age_seconds is None:
        return ZERO_RATIO
    if official_age_seconds <= config.recent_official_update_boost_seconds:
        return config.official_update_boost_score
    return ZERO_RATIO


def _source_gap_score(
    *,
    update_relevance_score: Decimal,
    missing_update_penalty_score: Decimal,
    stale_update_penalty_score: Decimal,
    unofficial_update_penalty_score: Decimal,
    low_source_count_penalty_score: Decimal,
    official_update_boost_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = (
            ONE_RATIO
            - update_relevance_score
            + missing_update_penalty_score
            + stale_update_penalty_score
            + unofficial_update_penalty_score
            + low_source_count_penalty_score
            - official_update_boost_score
        )
    if raw_score < ZERO_RATIO:
        return ZERO_RATIO
    if raw_score > ONE_RATIO:
        return ONE_RATIO
    return _normalize_ratio("source_gap_score", raw_score)


def _gap_status(
    *,
    reason_codes: tuple[str, ...],
    source_gap_score: Decimal,
    config: ResearchPacketResolutionUpdateSourceGapRankV2Config,
) -> str:
    if (
        "resolution_update_missing" in reason_codes
        or "resolution_update_block_stale" in reason_codes
        or source_gap_score >= config.blocked_gap_score
    ):
        return "blocked"
    if source_gap_score >= config.watch_gap_score:
        return "watch"
    return "pass"


def _draft_sort_key(
    draft: _GapDraft,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str, str]:
    return (
        _status_weight(draft.gap_status),
        ONE_RATIO - draft.source_gap_score,
        ZERO_COUNT - draft.missing_update_penalty_score,
        ZERO_COUNT - draft.stale_update_penalty_score,
        draft.market_id,
        draft.packet_id,
        draft.update_source_id,
    )


def _row_sort_key(
    row: ResearchPacketResolutionUpdateSourceGapRankV2Row,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str, str]:
    return (
        _status_weight(row.gap_status),
        ONE_RATIO - row.source_gap_score,
        ZERO_COUNT - row.missing_update_penalty_score,
        ZERO_COUNT - row.stale_update_penalty_score,
        row.market_id,
        row.packet_id,
        row.update_source_id,
    )


def _status_weight(status: str) -> Decimal:
    return {
        "blocked": Decimal("0"),
        "watch": Decimal("1"),
        "pass": Decimal("2"),
    }[status]


def _report_status(rows: tuple[ResearchPacketResolutionUpdateSourceGapRankV2Row, ...]) -> str:
    if any(row.gap_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gap_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketResolutionUpdateSourceGapRankV2Row, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    if status == "blocked":
        reason_codes = ["source_gap_blocked_packets_present"]
    elif status == "watch":
        reason_codes = ["source_gap_watch_packets_present"]
    else:
        reason_codes = ["source_gap_packets_clear"]
    row_reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    if "resolution_update_missing" in row_reason_codes:
        reason_codes.append("resolution_updates_missing")
    if (
        "resolution_update_watch_stale" in row_reason_codes
        or "resolution_update_block_stale" in row_reason_codes
    ):
        reason_codes.append("resolution_updates_stale")
    if "official_resolution_update_missing" in row_reason_codes:
        reason_codes.append("official_resolution_updates_missing")
    if "source_count_below_required" in row_reason_codes:
        reason_codes.append("source_counts_below_required")
    if "official_resolution_update_recent" in row_reason_codes:
        reason_codes.append("official_resolution_updates_recent")
    return tuple(reason_codes)


def _normalize_rows(
    rows: tuple[ResearchPacketResolutionUpdateSourceGapRankV2Row, ...],
) -> tuple[ResearchPacketResolutionUpdateSourceGapRankV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_packet_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        if type(row) is not ResearchPacketResolutionUpdateSourceGapRankV2Row:
            raise ValueError(
                "rows must contain ResearchPacketResolutionUpdateSourceGapRankV2Row values",
            )
        _require_hard_flags("row", row)
        if row.packet_id in seen_packet_ids:
            raise ValueError("rows must not contain duplicate packet_id values")
        if row.gap_rank != _count(index):
            raise ValueError("gap_rank must match row sequence")
        seen_packet_ids.add(row.packet_id)
    return rows


def _validate_row(row: ResearchPacketResolutionUpdateSourceGapRankV2Row) -> None:
    if row.source_count_shortfall != _source_count_shortfall(
        row.source_count,
        row.required_source_count,
    ):
        raise ValueError("source_count_shortfall must match source counts")
    if row.source_coverage_ratio != _source_coverage_ratio(
        row.source_count,
        row.required_source_count,
    ):
        raise ValueError("source_coverage_ratio must match source counts")


def _validate_report(report: ResearchPacketResolutionUpdateSourceGapRankV2Report) -> None:
    if report.packet_count != _count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.packet_count:
        raise ValueError("status counts must match packet_count")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.missing_update_count != _reason_count(report.rows, "resolution_update_missing"):
        raise ValueError("missing_update_count must match rows")
    if report.stale_update_count != _stale_update_count(report.rows):
        raise ValueError("stale_update_count must match rows")
    if report.missing_official_update_count != _reason_count(
        report.rows,
        "official_resolution_update_missing",
    ):
        raise ValueError("missing_official_update_count must match rows")
    if report.low_source_count != _reason_count(report.rows, "source_count_below_required"):
        raise ValueError("low_source_count must match rows")
    if report.official_update_boost_count != _reason_count(
        report.rows,
        "official_resolution_update_recent",
    ):
        raise ValueError("official_update_boost_count must match rows")
    if report.max_source_gap_score != _max_ratio(
        tuple(row.source_gap_score for row in report.rows),
    ):
        raise ValueError("max_source_gap_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministic")


def _status_count(
    rows: tuple[ResearchPacketResolutionUpdateSourceGapRankV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gap_status == status))


def _reason_count(
    rows: tuple[ResearchPacketResolutionUpdateSourceGapRankV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _stale_update_count(
    rows: tuple[ResearchPacketResolutionUpdateSourceGapRankV2Row, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if "resolution_update_watch_stale" in row.reason_codes
            or "resolution_update_block_stale" in row.reason_codes
        ),
    )


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return _normalize_ratio("max_ratio", max(values))


def _source_count_shortfall(source_count: Decimal, required_source_count: Decimal) -> Decimal:
    if source_count >= required_source_count:
        return ZERO_COUNT
    return _normalize_nonnegative_count(
        "source_count_shortfall",
        required_source_count - source_count,
    )


def _source_coverage_ratio(source_count: Decimal, required_source_count: Decimal) -> Decimal:
    if source_count >= required_source_count:
        return ONE_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("source_coverage_ratio", source_count / required_source_count)


def _validate_digest(value: object) -> None:
    current_digest = getattr(value, "derived_validation_digest")
    if current_digest != "":
        _require_digest(current_digest)
    expected_digest = _derived_validation_digest(value)
    if current_digest == "":
        object.__setattr__(value, "derived_validation_digest", expected_digest)
        return
    if current_digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _derived_validation_digest(value: object) -> str:
    payload = _json_ready(value, include_digest=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_payload_digests(value: Any) -> None:
    if isinstance(value, dict):
        if "derived_validation_digest" in value:
            current_digest = value["derived_validation_digest"]
            if type(current_digest) is not str:
                raise ValueError("derived_validation_digest must be a string")
            _require_digest(current_digest)
            expected_digest = _derived_validation_digest_from_payload(value)
            if current_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        for item in value.values():
            _validate_payload_digests(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_digests(item)


def _derived_validation_digest_from_payload(payload: dict[str, Any]) -> str:
    canonical = _copy_without_digest(payload)
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _copy_without_digest(value: Any) -> Any:
    if isinstance(value, dict):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if key == "derived_validation_digest":
                continue
            copied[key] = _copy_without_digest(item)
        return copied
    if isinstance(value, list):
        return [_copy_without_digest(item) for item in value]
    return value


def _require_digest(value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be a lowercase sha256 hex string")


def _json_ready(value: Any, *, include_digest: bool = True) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            if not include_digest and field.name == "derived_validation_digest":
                continue
            ready[field.name] = _json_ready(
                getattr(value, field.name),
                include_digest=include_digest,
            )
        return ready
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) is float:
        raise ValueError("payload must not contain floats")
    if type(value) is int:
        raise ValueError("payload numeric values must be Decimal strings")
    if type(value) is dict:
        ready = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if not include_digest and key == "derived_validation_digest":
                continue
            ready[key] = _json_ready(item, include_digest=include_digest)
        return ready
    if type(value) in (tuple, list):
        return [_json_ready(item, include_digest=include_digest) for item in value]
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _contains_unsafe_public_term(key):
                raise ValueError(f"unsafe public key in {label}: {key}")
            item_path = key if path == "" else f"{path}.{key}"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{path}[{index}]")
        return
    if isinstance(value, str) and _path_leaf(path) not in PUBLIC_VALUE_TERM_ALLOWLIST_KEYS:
        if _contains_unsafe_public_term(value):
            raise ValueError(f"unsafe public value in {label}: {path}")


def _path_leaf(path: str) -> str:
    if "." in path:
        return path.rsplit(".", 1)[1]
    return path


def _contains_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in UNSAFE_PUBLIC_TERMS)


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in SAFETY_FLAG_NAMES:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")
    _require_nested_payload_flags(payload)


def _require_nested_payload_flags(value: Any) -> None:
    if isinstance(value, dict):
        for field_name in SAFETY_FLAG_NAMES:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True for payload")
        for item in value.values():
            _require_nested_payload_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_nested_payload_flags(item)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in SAFETY_FLAG_NAMES:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_canonical_string(
    field_name: str,
    value: str,
    *,
    allow_public_terms: bool = False,
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() == "":
        raise ValueError(f"{field_name} must not be blank")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if not allow_public_terms and _contains_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {field_name}")
    return value


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        _require_canonical_string(field_name, value)
        _require_member(field_name, value, allowed_values)
        if value in seen_values:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(value)
        seen_values.add(value)
    if tuple(value for value in allowed_values if value in normalized) != tuple(normalized):
        raise ValueError(f"{field_name} must be deterministic")
    return tuple(normalized)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value, RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value, SECONDS_QUANTUM)
    if normalized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_seconds(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_optional_nonnegative_seconds(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_seconds(field_name, value)


def _normalize_decimal(field_name: str, value: Decimal, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(quantum)
    if normalized != value:
        raise ValueError(f"{field_name} must align to {quantum}")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _age_seconds(value: datetime | None, generated_at: datetime) -> Decimal | None:
    if value is None:
        return None
    delta = generated_at - value
    seconds = Decimal(delta.days) * SECONDS_PER_DAY + Decimal(delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _normalize_nonnegative_seconds("age_seconds", seconds)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_RESOLUTION_UPDATE_SOURCE_GAP_RANK_V2_CONFIG_VERSION",
    "GAP_STATUSES",
    "REPORT_REASON_CODES",
    "ROW_REASON_CODES",
    "UNSAFE_PUBLIC_TERMS",
    "ResearchPacketResolutionUpdateSourceGapRankV2Config",
    "ResearchPacketResolutionUpdateSourceGapRankV2Input",
    "ResearchPacketResolutionUpdateSourceGapRankV2Report",
    "ResearchPacketResolutionUpdateSourceGapRankV2Row",
    "build_research_packet_resolution_update_source_gap_rank_v2_report",
    "research_packet_resolution_update_source_gap_rank_v2_payload",
)
