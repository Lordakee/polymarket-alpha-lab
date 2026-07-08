"""Pure report-only market resolution/liquidity watch reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


RESOLUTION_LIQUIDITY_WATCH_STATUSES = ("pass", "watch", "block")
DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_WATCH_REPORT_CONFIG_VERSION = (
    "research-market-resolution-liquidity-watch-report-v0"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
NO_CANDIDATES_REASON = "no_resolution_liquidity_candidates_block"
MANUAL_REVIEW_REASON = "manual_resolution_liquidity_review"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "condition_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wal" "let",
    "au" "th",
    "private",
    "secret",
    "credential",
    "or" "der",
    "tra" "de",
    "buy",
    "sell",
    "size",
    "siz" "ing",
    "recommend" "ation",
)


__all__ = (
    "RESOLUTION_LIQUIDITY_WATCH_STATUSES",
    "DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_WATCH_REPORT_CONFIG_VERSION",
    "ResearchMarketResolutionLiquidityWatchCandidate",
    "ResearchMarketResolutionLiquidityWatchConfig",
    "ResearchMarketResolutionLiquidityWatchReasonCodeCount",
    "ResearchMarketResolutionLiquidityWatchReport",
    "ResearchMarketResolutionLiquidityWatchRow",
    "build_research_market_resolution_liquidity_watch_report",
    "research_market_resolution_liquidity_watch_report_digest",
    "research_market_resolution_liquidity_watch_report_payload",
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
class ResearchMarketResolutionLiquidityWatchConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_WATCH_REPORT_CONFIG_VERSION
    )
    pass_max_resolution_pressure_score: Decimal = Decimal("0.250000")
    watch_max_resolution_pressure_score: Decimal = Decimal("0.550000")
    pass_min_liquidity_quality_score: Decimal = Decimal("0.750000")
    watch_min_liquidity_quality_score: Decimal = Decimal("0.450000")
    watch_joint_pressure_score: Decimal = Decimal("0.350000")
    block_joint_pressure_score: Decimal = Decimal("0.650000")
    hard_resolution_uncertainty_floor: Decimal = Decimal("0.850000")
    hard_liquidity_quality_ceiling: Decimal = Decimal("0.200000")
    resolution_uncertainty_weight: Decimal = Decimal("0.500000")
    resolution_source_conflict_weight: Decimal = Decimal("0.250000")
    resolution_rule_ambiguity_weight: Decimal = Decimal("0.250000")
    liquidity_quality_gap_weight: Decimal = Decimal("0.400000")
    liquidity_staleness_weight: Decimal = Decimal("0.200000")
    liquidity_depth_fragility_weight: Decimal = Decimal("0.200000")
    spread_pressure_weight: Decimal = Decimal("0.200000")
    joint_resolution_pressure_weight: Decimal = Decimal("0.450000")
    joint_liquidity_pressure_weight: Decimal = Decimal("0.350000")
    joint_interaction_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionLiquidityWatchConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_WATCH_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_max_resolution_pressure_score",
            "watch_max_resolution_pressure_score",
            "pass_min_liquidity_quality_score",
            "watch_min_liquidity_quality_score",
            "watch_joint_pressure_score",
            "block_joint_pressure_score",
            "hard_resolution_uncertainty_floor",
            "hard_liquidity_quality_ceiling",
            "resolution_uncertainty_weight",
            "resolution_source_conflict_weight",
            "resolution_rule_ambiguity_weight",
            "liquidity_quality_gap_weight",
            "liquidity_staleness_weight",
            "liquidity_depth_fragility_weight",
            "spread_pressure_weight",
            "joint_resolution_pressure_weight",
            "joint_liquidity_pressure_weight",
            "joint_interaction_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if (
            self.pass_max_resolution_pressure_score
            > self.watch_max_resolution_pressure_score
        ):
            raise ValueError(
                "pass_max_resolution_pressure_score must not exceed watch threshold",
            )
        if self.watch_min_liquidity_quality_score > self.pass_min_liquidity_quality_score:
            raise ValueError(
                "watch_min_liquidity_quality_score must not exceed pass threshold",
            )
        if self.watch_joint_pressure_score >= self.block_joint_pressure_score:
            raise ValueError("watch_joint_pressure_score must be below block threshold")
        _require_weights_total_one(
            "resolution pressure weights",
            (
                self.resolution_uncertainty_weight,
                self.resolution_source_conflict_weight,
                self.resolution_rule_ambiguity_weight,
            ),
        )
        _require_weights_total_one(
            "liquidity pressure weights",
            (
                self.liquidity_quality_gap_weight,
                self.liquidity_staleness_weight,
                self.liquidity_depth_fragility_weight,
                self.spread_pressure_weight,
            ),
        )
        _require_weights_total_one(
            "joint pressure weights",
            (
                self.joint_resolution_pressure_weight,
                self.joint_liquidity_pressure_weight,
                self.joint_interaction_weight,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityWatchCandidate(_FinalPublicDataclass):
    candidate_id: str
    observed_at: datetime
    resolution_uncertainty_score: Decimal
    resolution_source_conflict_score: Decimal
    resolution_rule_ambiguity_score: Decimal
    liquidity_quality_score: Decimal
    liquidity_staleness_score: Decimal
    liquidity_depth_fragility_score: Decimal
    spread_pressure_score: Decimal
    market_id: str | None = None
    market_slug: str | None = None
    market_question: str | None = None
    source_url: str | None = None
    source_text: str | None = None
    dsn: str | None = None
    table_name: str | None = None
    private_token: str | None = None
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionLiquidityWatchCandidate,
            "candidate",
        )
        _require_canonical_string("candidate_id", self.candidate_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "resolution_uncertainty_score",
            "resolution_source_conflict_score",
            "resolution_rule_ambiguity_score",
            "liquidity_quality_score",
            "liquidity_staleness_score",
            "liquidity_depth_fragility_score",
            "spread_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "market_id",
            "market_slug",
            "market_question",
            "source_url",
            "source_text",
            "dsn",
            "table_name",
            "private_token",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityWatchRow(_FinalPublicDataclass):
    public_row_ref: str
    observed_at: datetime
    resolution_pressure_score: Decimal
    liquidity_quality_score: Decimal
    liquidity_pressure_score: Decimal
    joint_pressure_score: Decimal
    status: str
    hard_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketResolutionLiquidityWatchRow, "row")
        _require_canonical_string("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "resolution_pressure_score",
            "liquidity_quality_score",
            "liquidity_pressure_score",
            "joint_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "hard_flags",
            _normalize_reason_codes("hard_flags", self.hard_flags, allow_empty=True),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if f"joint_resolution_liquidity_pressure_{self.status}" not in self.reason_codes:
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityWatchReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionLiquidityWatchReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityWatchReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_joint_pressure_score: Decimal
    max_resolution_pressure_score: Decimal
    min_liquidity_quality_score: Decimal
    status: str
    rows: tuple[ResearchMarketResolutionLiquidityWatchRow, ...]
    reason_code_counts: tuple[ResearchMarketResolutionLiquidityWatchReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    public_report_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketResolutionLiquidityWatchReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "mean_joint_pressure_score",
            "max_resolution_pressure_score",
            "min_liquidity_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
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
        _require_hex_digest("public_report_digest", self.public_report_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _expected_public_report_digest(self)
        if self.public_report_digest != expected_digest:
            raise ValueError("public_report_digest must match public report payload")


@dataclass(frozen=True)
class _RowDraft:
    observed_at: datetime
    resolution_pressure_score: Decimal
    liquidity_quality_score: Decimal
    liquidity_pressure_score: Decimal
    joint_pressure_score: Decimal
    status: str
    hard_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]


def build_research_market_resolution_liquidity_watch_report(
    candidates: Iterable[ResearchMarketResolutionLiquidityWatchCandidate],
    *,
    config: ResearchMarketResolutionLiquidityWatchConfig,
    generated_at: datetime,
) -> ResearchMarketResolutionLiquidityWatchReport:
    if type(config) is not ResearchMarketResolutionLiquidityWatchConfig:
        raise ValueError("config must be a ResearchMarketResolutionLiquidityWatchConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_candidates(candidates)
    for candidate in normalized:
        if candidate.observed_at > generated_at_utc:
            raise ValueError("observed_at must be less than or equal to generated_at")
    drafts = tuple(_row_draft(candidate, config=config) for candidate in normalized)
    rows = tuple(
        _row_from_draft(
            public_row_ref=f"resolution_liquidity_watch_row_{index:03d}",
            draft=draft,
        )
        for index, draft in enumerate(sorted(drafts, key=_draft_sort_key), start=1)
    )
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "mean_joint_pressure_score": _mean_joint_pressure_score(rows),
        "max_resolution_pressure_score": _max_or_zero(
            tuple(row.resolution_pressure_score for row in rows),
        ),
        "min_liquidity_quality_score": _min_or_zero(
            tuple(row.liquidity_quality_score for row in rows),
        ),
        "status": _report_status(rows),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": _report_reason_codes(rows),
    }
    return ResearchMarketResolutionLiquidityWatchReport(
        **report_values,
        public_report_digest=_public_digest(_report_payload_without_digest(**report_values)),
    )


def research_market_resolution_liquidity_watch_report_payload(
    report: ResearchMarketResolutionLiquidityWatchReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketResolutionLiquidityWatchReport:
        raise ValueError("report must be a ResearchMarketResolutionLiquidityWatchReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    expected_digest = _expected_public_report_digest(report)
    if report.public_report_digest != expected_digest:
        raise ValueError("public_report_digest must match public report payload")
    payload = _report_payload_without_digest_from_report(report)
    payload["public_report_digest"] = report.public_report_digest
    payload["paper_only"] = True
    payload["report_only"] = True
    payload["readonly"] = True
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_public_payload(ready)
    return ready


def research_market_resolution_liquidity_watch_report_digest(
    report: ResearchMarketResolutionLiquidityWatchReport,
) -> str:
    payload = research_market_resolution_liquidity_watch_report_payload(report)
    digest = payload.get("public_report_digest")
    if type(digest) is not str:
        raise ValueError("public_report_digest must be a string")
    return digest


def _row_draft(
    candidate: ResearchMarketResolutionLiquidityWatchCandidate,
    *,
    config: ResearchMarketResolutionLiquidityWatchConfig,
) -> _RowDraft:
    resolution_pressure_score = _resolution_pressure_score(candidate, config=config)
    liquidity_pressure_score = _liquidity_pressure_score(candidate, config=config)
    joint_pressure_score = _joint_pressure_score(
        resolution_pressure_score=resolution_pressure_score,
        liquidity_pressure_score=liquidity_pressure_score,
        config=config,
    )
    hard_flags = _hard_flags(candidate, config=config)
    status = _row_status(
        resolution_pressure_score=resolution_pressure_score,
        liquidity_quality_score=candidate.liquidity_quality_score,
        joint_pressure_score=joint_pressure_score,
        hard_flags=hard_flags,
        config=config,
    )
    return _RowDraft(
        observed_at=candidate.observed_at,
        resolution_pressure_score=resolution_pressure_score,
        liquidity_quality_score=candidate.liquidity_quality_score,
        liquidity_pressure_score=liquidity_pressure_score,
        joint_pressure_score=joint_pressure_score,
        status=status,
        hard_flags=hard_flags,
        reason_codes=_row_reason_codes(
            candidate=candidate,
            status=status,
            hard_flags=hard_flags,
        ),
    )


def _row_from_draft(
    *,
    public_row_ref: str,
    draft: _RowDraft,
) -> ResearchMarketResolutionLiquidityWatchRow:
    return ResearchMarketResolutionLiquidityWatchRow(
        public_row_ref=public_row_ref,
        observed_at=draft.observed_at,
        resolution_pressure_score=draft.resolution_pressure_score,
        liquidity_quality_score=draft.liquidity_quality_score,
        liquidity_pressure_score=draft.liquidity_pressure_score,
        joint_pressure_score=draft.joint_pressure_score,
        status=draft.status,
        hard_flags=draft.hard_flags,
        reason_codes=draft.reason_codes,
    )


def _resolution_pressure_score(
    candidate: ResearchMarketResolutionLiquidityWatchCandidate,
    *,
    config: ResearchMarketResolutionLiquidityWatchConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            candidate.resolution_uncertainty_score * config.resolution_uncertainty_weight
            + candidate.resolution_source_conflict_score
            * config.resolution_source_conflict_weight
            + candidate.resolution_rule_ambiguity_score
            * config.resolution_rule_ambiguity_weight
        )
    return _normalize_probability("resolution_pressure_score", score)


def _liquidity_pressure_score(
    candidate: ResearchMarketResolutionLiquidityWatchCandidate,
    *,
    config: ResearchMarketResolutionLiquidityWatchConfig,
) -> Decimal:
    liquidity_quality_gap = _normalize_probability(
        "liquidity_quality_gap",
        ONE - candidate.liquidity_quality_score,
    )
    with localcontext(DECIMAL_CONTEXT):
        score = (
            liquidity_quality_gap * config.liquidity_quality_gap_weight
            + candidate.liquidity_staleness_score * config.liquidity_staleness_weight
            + candidate.liquidity_depth_fragility_score
            * config.liquidity_depth_fragility_weight
            + candidate.spread_pressure_score * config.spread_pressure_weight
        )
    return _normalize_probability("liquidity_pressure_score", score)


def _joint_pressure_score(
    *,
    resolution_pressure_score: Decimal,
    liquidity_pressure_score: Decimal,
    config: ResearchMarketResolutionLiquidityWatchConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            resolution_pressure_score * config.joint_resolution_pressure_weight
            + liquidity_pressure_score * config.joint_liquidity_pressure_weight
            + resolution_pressure_score
            * liquidity_pressure_score
            * config.joint_interaction_weight
        )
    return _normalize_probability("joint_pressure_score", score)


def _hard_flags(
    candidate: ResearchMarketResolutionLiquidityWatchCandidate,
    *,
    config: ResearchMarketResolutionLiquidityWatchConfig,
) -> tuple[str, ...]:
    flags: list[str] = []
    if candidate.resolution_uncertainty_score >= config.hard_resolution_uncertainty_floor:
        flags.append("resolution_uncertainty_hard_block")
    if candidate.liquidity_quality_score <= config.hard_liquidity_quality_ceiling:
        flags.append("liquidity_quality_hard_block")
    return tuple(sorted(flags))


def _row_status(
    *,
    resolution_pressure_score: Decimal,
    liquidity_quality_score: Decimal,
    joint_pressure_score: Decimal,
    hard_flags: tuple[str, ...],
    config: ResearchMarketResolutionLiquidityWatchConfig,
) -> str:
    if (
        hard_flags
        or joint_pressure_score >= config.block_joint_pressure_score
        or resolution_pressure_score > config.watch_max_resolution_pressure_score
        or liquidity_quality_score < config.watch_min_liquidity_quality_score
    ):
        return "block"
    if (
        joint_pressure_score >= config.watch_joint_pressure_score
        or resolution_pressure_score > config.pass_max_resolution_pressure_score
        or liquidity_quality_score < config.pass_min_liquidity_quality_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    candidate: ResearchMarketResolutionLiquidityWatchCandidate,
    status: str,
    hard_flags: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = [
        _band_reason(
            candidate.resolution_uncertainty_score,
            low="resolution_uncertainty_low",
            watch="resolution_uncertainty_watch",
            high="resolution_uncertainty_high",
        ),
        _band_reason(
            candidate.resolution_source_conflict_score,
            low="resolution_source_conflict_low",
            watch="resolution_source_conflict_watch",
            high="resolution_source_conflict_high",
        ),
        _band_reason(
            candidate.resolution_rule_ambiguity_score,
            low="resolution_rule_ambiguity_low",
            watch="resolution_rule_ambiguity_watch",
            high="resolution_rule_ambiguity_high",
        ),
        _liquidity_quality_reason(candidate.liquidity_quality_score),
        _band_reason(
            candidate.liquidity_staleness_score,
            low="liquidity_staleness_low",
            watch="liquidity_staleness_watch",
            high="liquidity_staleness_high",
        ),
        _band_reason(
            candidate.liquidity_depth_fragility_score,
            low="liquidity_depth_fragility_low",
            watch="liquidity_depth_fragility_watch",
            high="liquidity_depth_fragility_high",
        ),
        _band_reason(
            candidate.spread_pressure_score,
            low="spread_pressure_low",
            watch="spread_pressure_watch",
            high="spread_pressure_high",
        ),
        f"joint_resolution_liquidity_pressure_{status}",
    ]
    reason_codes.extend(hard_flags)
    for reason_code in candidate.reason_codes:
        reason_codes.append(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _band_reason(value: Decimal, *, low: str, watch: str, high: str) -> str:
    if value <= Decimal("0.250000"):
        return low
    if value >= Decimal("0.750000"):
        return high
    return watch


def _liquidity_quality_reason(value: Decimal) -> str:
    if value <= Decimal("0.250000"):
        return "liquidity_quality_block"
    if value < Decimal("0.750000"):
        return "liquidity_quality_watch"
    return "liquidity_quality_pass"


def _report_status(rows: tuple[ResearchMarketResolutionLiquidityWatchRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketResolutionLiquidityWatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    reason_codes = {f"resolution_liquidity_watch_report_{_report_status(rows)}"}
    reason_codes.update(flag for row in rows for flag in row.hard_flags)
    if any(f"input_{MANUAL_REVIEW_REASON}" in row.reason_codes for row in rows):
        reason_codes.add("manual_resolution_liquidity_review_present")
    return tuple(sorted(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchMarketResolutionLiquidityWatchRow, ...],
) -> tuple[ResearchMarketResolutionLiquidityWatchReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketResolutionLiquidityWatchReasonCodeCount(
                reason_code=NO_CANDIDATES_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    total = _count(len(rows))
    return tuple(
        ResearchMarketResolutionLiquidityWatchReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            row_ratio=_quantize(_count(count) / total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _normalize_candidates(
    candidates: Iterable[ResearchMarketResolutionLiquidityWatchCandidate],
) -> tuple[ResearchMarketResolutionLiquidityWatchCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        values = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchMarketResolutionLiquidityWatchCandidate:
            raise ValueError(
                "candidates must contain ResearchMarketResolutionLiquidityWatchCandidate "
                "values",
            )
        _require_hard_flags("candidate", value)
    candidate_ids = tuple(value.candidate_id for value in values)
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("candidate_id values must be unique")
    return values


def _normalize_rows(
    rows: tuple[ResearchMarketResolutionLiquidityWatchRow, ...],
) -> tuple[ResearchMarketResolutionLiquidityWatchRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketResolutionLiquidityWatchRow:
            raise ValueError(
                "rows must contain ResearchMarketResolutionLiquidityWatchRow values",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=lambda row: row.public_row_ref)):
        raise ValueError("rows must be sorted by public_row_ref")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketResolutionLiquidityWatchReasonCodeCount, ...],
) -> tuple[ResearchMarketResolutionLiquidityWatchReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketResolutionLiquidityWatchReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketResolutionLiquidityWatchReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    if counts != tuple(sorted(counts, key=lambda count: count.reason_code)):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_report(report: ResearchMarketResolutionLiquidityWatchReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_joint_pressure_score != _mean_joint_pressure_score(report.rows):
        raise ValueError("mean_joint_pressure_score must match rows")
    if report.max_resolution_pressure_score != _max_or_zero(
        tuple(row.resolution_pressure_score for row in report.rows),
    ):
        raise ValueError("max_resolution_pressure_score must match rows")
    if report.min_liquidity_quality_score != _min_or_zero(
        tuple(row.liquidity_quality_score for row in report.rows),
    ):
        raise ValueError("min_liquidity_quality_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchMarketResolutionLiquidityWatchRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _mean_joint_pressure_score(
    rows: tuple[ResearchMarketResolutionLiquidityWatchRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize(
        sum((row.joint_pressure_score for row in rows), ZERO) / _count(len(rows)),
    )


def _max_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _min_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _draft_sort_key(
    draft: _RowDraft,
) -> tuple[int, Decimal, Decimal, Decimal, tuple[str, ...], str]:
    return (
        {"block": 0, "pass": 1, "watch": 2}[draft.status],
        draft.joint_pressure_score,
        draft.resolution_pressure_score,
        draft.liquidity_pressure_score,
        draft.reason_codes,
        draft.observed_at.isoformat(),
    )


def _report_payload_without_digest_from_report(
    report: ResearchMarketResolutionLiquidityWatchReport,
) -> dict[str, object]:
    return _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        mean_joint_pressure_score=report.mean_joint_pressure_score,
        max_resolution_pressure_score=report.max_resolution_pressure_score,
        min_liquidity_quality_score=report.min_liquidity_quality_score,
        status=report.status,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
    )


def _report_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    candidate_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    mean_joint_pressure_score: Decimal,
    max_resolution_pressure_score: Decimal,
    min_liquidity_quality_score: Decimal,
    status: str,
    rows: tuple[ResearchMarketResolutionLiquidityWatchRow, ...],
    reason_code_counts: tuple[ResearchMarketResolutionLiquidityWatchReasonCodeCount, ...],
    reason_codes: tuple[str, ...],
) -> dict[str, object]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "candidate_count": candidate_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "mean_joint_pressure_score": mean_joint_pressure_score,
        "max_resolution_pressure_score": max_resolution_pressure_score,
        "min_liquidity_quality_score": min_liquidity_quality_score,
        "status": status,
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
    }


def _expected_public_report_digest(
    report: ResearchMarketResolutionLiquidityWatchReport,
) -> str:
    return _public_digest(_report_payload_without_digest_from_report(report))


def _public_digest(payload: dict[str, object]) -> str:
    ready = _json_ready(payload)
    _require_public_payload(ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
            if field.name not in {"public_report_digest"}
        }
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _require_public_payload(value: object) -> None:
    _walk_public_payload(value)


def _walk_public_payload(value: object, *, key_path: str = "payload") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _contains_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload key: {key_path}.{key}")
            _walk_public_payload(item, key_path=f"{key_path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _walk_public_payload(item, key_path=f"{key_path}[{index}]")
        return
    if isinstance(value, (str, bool)) or value is None:
        if isinstance(value, str) and _contains_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public payload value: {key_path}")
        return
    if isinstance(value, float):
        raise ValueError("public payload must not contain float values")
    if isinstance(value, Decimal):
        raise ValueError("public payload must contain Decimal strings, not Decimal values")
    if isinstance(value, int):
        raise ValueError("public payload must contain Decimal strings, not integer values")


def _contains_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = _quantize(normalized)
    if quantized != quantized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return quantized


def _normalize_optional_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "":
        return None
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must be canonical")
    if any(not (char.islower() or char.isdigit() or char == "_") for char in value):
        raise ValueError(f"{field_name} must contain only lowercase identifiers")
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")
    return value


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_require_reason_code(field_name, value) for value in values)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized))


def _require_status(field_name: str, value: object) -> None:
    if value not in RESOLUTION_LIQUIDITY_WATCH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in PHASE_FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name}.{flag_name} must be True")


def _require_weights_total_one(label: str, values: tuple[Decimal, ...]) -> None:
    total = _quantize(sum(values, ZERO))
    if total != ONE:
        raise ValueError(f"{label} must sum to 1")


def _require_hex_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest") from exc


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)
