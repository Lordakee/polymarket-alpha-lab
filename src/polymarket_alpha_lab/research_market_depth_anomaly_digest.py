"""Pure review digest for public depth-anomaly research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import UNSAFE_SURFACE_FIELD_FRAGMENTS


__all__ = (
    "DEFAULT_RESEARCH_MARKET_DEPTH_ANOMALY_DIGEST_CONFIG_VERSION",
    "ResearchMarketDepthAnomalyDigestConfig",
    "ResearchMarketDepthAnomalyObservation",
    "ResearchMarketDepthAnomalyDigestReasonCodeCount",
    "ResearchMarketDepthAnomalyDigestReport",
    "ResearchMarketDepthAnomalyDigestRow",
    "build_research_market_depth_anomaly_digest_report",
    "research_market_depth_anomaly_digest_payload",
    "research_market_depth_anomaly_public_digest",
)


DEFAULT_RESEARCH_MARKET_DEPTH_ANOMALY_DIGEST_CONFIG_VERSION = (
    "research-market-depth-anomaly-digest-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = "market_depth_anomaly_digest_no_inputs"


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
class ResearchMarketDepthAnomalyDigestConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_MARKET_DEPTH_ANOMALY_DIGEST_CONFIG_VERSION
    depth_shortfall_watch: Decimal = Decimal("0.400000")
    depth_shortfall_block: Decimal = Decimal("0.750000")
    imbalance_watch: Decimal = Decimal("0.600000")
    imbalance_block: Decimal = Decimal("0.850000")
    spread_width_watch: Decimal = Decimal("0.080000")
    spread_width_block: Decimal = Decimal("0.150000")
    stale_snapshot_age_seconds: Decimal = Decimal("900.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthAnomalyDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "depth_shortfall_watch",
            "depth_shortfall_block",
            "imbalance_watch",
            "imbalance_block",
            "spread_width_watch",
            "spread_width_block",
            "stale_snapshot_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_most("depth_shortfall_watch", self.depth_shortfall_watch, self.depth_shortfall_block)
        _require_at_most("imbalance_watch", self.imbalance_watch, self.imbalance_block)
        _require_at_most("spread_width_watch", self.spread_width_watch, self.spread_width_block)
        for field_name in (
            "depth_shortfall_watch",
            "depth_shortfall_block",
            "imbalance_watch",
            "imbalance_block",
        ):
            _require_ratio_at_most_one(field_name, getattr(self, field_name))
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthAnomalyObservation(_FinalPublicDataclass):
    segment: str
    best_bid_depth: Decimal
    best_ask_depth: Decimal
    top_bid_depth: Decimal
    top_ask_depth: Decimal
    baseline_depth: Decimal
    spread_width: Decimal
    snapshot_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthAnomalyObservation, "observation")
        _require_canonical_string("segment", self.segment)
        for field_name in (
            "best_bid_depth",
            "best_ask_depth",
            "top_bid_depth",
            "top_ask_depth",
            "spread_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "baseline_depth",
            _normalize_positive_decimal("baseline_depth", self.baseline_depth),
        )
        object.__setattr__(self, "snapshot_at", _as_utc("snapshot_at", self.snapshot_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketDepthAnomalyDigestRow(_FinalPublicDataclass):
    review_label: str
    segment: str
    status: str
    best_bid_depth: Decimal
    best_ask_depth: Decimal
    top_bid_depth: Decimal
    top_ask_depth: Decimal
    total_depth: Decimal
    baseline_depth: Decimal
    depth_ratio: Decimal
    depth_shortfall_ratio: Decimal
    absolute_imbalance_ratio: Decimal
    spread_width: Decimal
    snapshot_at: datetime
    snapshot_age_seconds: Decimal
    anomaly_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthAnomalyDigestRow, "row")
        _require_canonical_string("review_label", self.review_label)
        _require_canonical_string("segment", self.segment)
        _require_status("status", self.status)
        for field_name in (
            "best_bid_depth",
            "best_ask_depth",
            "top_bid_depth",
            "top_ask_depth",
            "total_depth",
            "depth_ratio",
            "depth_shortfall_ratio",
            "absolute_imbalance_ratio",
            "spread_width",
            "snapshot_age_seconds",
            "anomaly_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "baseline_depth",
            _normalize_positive_decimal("baseline_depth", self.baseline_depth),
        )
        object.__setattr__(self, "snapshot_at", _as_utc("snapshot_at", self.snapshot_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketDepthAnomalyDigestReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthAnomalyDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketDepthAnomalyDigestReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    depth_shortfall_count: Decimal
    depth_imbalance_count: Decimal
    spread_width_count: Decimal
    stale_snapshot_count: Decimal
    mean_anomaly_score: Decimal
    max_anomaly_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketDepthAnomalyDigestReasonCodeCount, ...]
    market_depth_anomaly_rows: tuple[ResearchMarketDepthAnomalyDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthAnomalyDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "depth_shortfall_count",
            "depth_imbalance_count",
            "spread_width_count",
            "stale_snapshot_count",
            "mean_anomaly_score",
            "max_anomaly_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "market_depth_anomaly_rows",
            _normalize_rows(self.market_depth_anomaly_rows),
        )
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchMarketDepthAnomalyDigestConfig,
    ResearchMarketDepthAnomalyObservation,
    ResearchMarketDepthAnomalyDigestReasonCodeCount,
    ResearchMarketDepthAnomalyDigestReport,
    ResearchMarketDepthAnomalyDigestRow,
)


def build_research_market_depth_anomaly_digest_report(
    observations: Iterable[ResearchMarketDepthAnomalyObservation],
    *,
    config: ResearchMarketDepthAnomalyDigestConfig,
    generated_at: datetime,
) -> ResearchMarketDepthAnomalyDigestReport:
    if type(config) is not ResearchMarketDepthAnomalyDigestConfig:
        raise ValueError("config must be a ResearchMarketDepthAnomalyDigestConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_observations(observations)
    unlabeled_rows = tuple(
        sorted(
            (
                _digest_row(
                    row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for row in inputs
            ),
            key=_row_sort_key,
        ),
    )
    rows = tuple(
        _row_with_review_label(row, _review_label(index))
        for index, row in enumerate(unlabeled_rows, start=1)
    )
    return ResearchMarketDepthAnomalyDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        depth_shortfall_count=_reason_prefix_count(rows, "depth_shortfall_"),
        depth_imbalance_count=_reason_prefix_count(rows, "depth_imbalance_"),
        spread_width_count=_reason_prefix_count(rows, "spread_width_"),
        stale_snapshot_count=_reason_member_count(rows, "snapshot_stale_watch"),
        mean_anomaly_score=_mean(tuple(row.anomaly_score for row in rows)),
        max_anomaly_score=_max_decimal(tuple(row.anomaly_score for row in rows)),
        status=_rollup_status(tuple(row.status for row in rows)),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        market_depth_anomaly_rows=rows,
    )


def research_market_depth_anomaly_digest_payload(
    report: ResearchMarketDepthAnomalyDigestReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketDepthAnomalyDigestReport:
        raise ValueError("report must be a ResearchMarketDepthAnomalyDigestReport")
    _require_payload_safe_value("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_market_depth_anomaly_public_digest(
    report: ResearchMarketDepthAnomalyDigestReport,
) -> dict[str, Any]:
    payload = research_market_depth_anomaly_digest_payload(report)
    rows = payload["market_depth_anomaly_rows"]
    if type(rows) is not list:
        raise ValueError("market_depth_anomaly_rows must be a list")
    public_rows = [
        {
            "review_label": row["review_label"],
            "segment": row["segment"],
            "status": row["status"],
            "anomaly_score": row["anomaly_score"],
            "reason_codes": row["reason_codes"],
        }
        for row in rows
    ]
    public_digest = {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "observation_count": payload["observation_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "depth_shortfall_count": payload["depth_shortfall_count"],
        "depth_imbalance_count": payload["depth_imbalance_count"],
        "spread_width_count": payload["spread_width_count"],
        "stale_snapshot_count": payload["stale_snapshot_count"],
        "mean_anomaly_score": payload["mean_anomaly_score"],
        "max_anomaly_score": payload["max_anomaly_score"],
        "status": payload["status"],
        "reason_codes": payload["reason_codes"],
        "reason_code_counts": payload["reason_code_counts"],
        "review_rows": public_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _require_hard_flags("public_digest", _DictFlags(public_digest))
    _reject_unsafe_public_payload("public_digest", public_digest)
    return public_digest


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


def _digest_row(
    row: ResearchMarketDepthAnomalyObservation,
    *,
    config: ResearchMarketDepthAnomalyDigestConfig,
    generated_at: datetime,
) -> ResearchMarketDepthAnomalyDigestRow:
    snapshot_age_seconds = _snapshot_age_seconds(row.snapshot_at, generated_at)
    total_depth = _quantize(row.top_bid_depth + row.top_ask_depth)
    depth_ratio = _quantize(total_depth / row.baseline_depth)
    depth_shortfall_ratio = _quantize(max(ZERO, ONE - depth_ratio))
    absolute_imbalance_ratio = _absolute_imbalance_ratio(row.top_bid_depth, row.top_ask_depth)
    anomaly_score = _quantize(
        depth_shortfall_ratio + absolute_imbalance_ratio + row.spread_width,
    )
    reason_codes = _row_reason_codes(
        row,
        depth_shortfall_ratio=depth_shortfall_ratio,
        absolute_imbalance_ratio=absolute_imbalance_ratio,
        snapshot_age_seconds=snapshot_age_seconds,
        config=config,
    )
    return ResearchMarketDepthAnomalyDigestRow(
        review_label="depth-anomaly-000",
        segment=row.segment,
        status=_row_status(reason_codes),
        best_bid_depth=row.best_bid_depth,
        best_ask_depth=row.best_ask_depth,
        top_bid_depth=row.top_bid_depth,
        top_ask_depth=row.top_ask_depth,
        total_depth=total_depth,
        baseline_depth=row.baseline_depth,
        depth_ratio=depth_ratio,
        depth_shortfall_ratio=depth_shortfall_ratio,
        absolute_imbalance_ratio=absolute_imbalance_ratio,
        spread_width=row.spread_width,
        snapshot_at=row.snapshot_at,
        snapshot_age_seconds=snapshot_age_seconds,
        anomaly_score=anomaly_score,
        reason_codes=reason_codes,
    )


def _row_with_review_label(
    row: ResearchMarketDepthAnomalyDigestRow,
    review_label: str,
) -> ResearchMarketDepthAnomalyDigestRow:
    return ResearchMarketDepthAnomalyDigestRow(
        review_label=review_label,
        segment=row.segment,
        status=row.status,
        best_bid_depth=row.best_bid_depth,
        best_ask_depth=row.best_ask_depth,
        top_bid_depth=row.top_bid_depth,
        top_ask_depth=row.top_ask_depth,
        total_depth=row.total_depth,
        baseline_depth=row.baseline_depth,
        depth_ratio=row.depth_ratio,
        depth_shortfall_ratio=row.depth_shortfall_ratio,
        absolute_imbalance_ratio=row.absolute_imbalance_ratio,
        spread_width=row.spread_width,
        snapshot_at=row.snapshot_at,
        snapshot_age_seconds=row.snapshot_age_seconds,
        anomaly_score=row.anomaly_score,
        reason_codes=row.reason_codes,
    )


def _review_label(index: int) -> str:
    return f"depth-anomaly-{index:03d}"


def _absolute_imbalance_ratio(bid_depth: Decimal, ask_depth: Decimal) -> Decimal:
    total_depth = _quantize(bid_depth + ask_depth)
    if total_depth == ZERO:
        return ONE
    return _quantize(abs(bid_depth - ask_depth) / total_depth)


def _row_reason_codes(
    row: ResearchMarketDepthAnomalyObservation,
    *,
    depth_shortfall_ratio: Decimal,
    absolute_imbalance_ratio: Decimal,
    snapshot_age_seconds: Decimal,
    config: ResearchMarketDepthAnomalyDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(row.reason_codes)
    if depth_shortfall_ratio >= config.depth_shortfall_block:
        reason_codes.append("depth_shortfall_block")
    elif depth_shortfall_ratio >= config.depth_shortfall_watch:
        reason_codes.append("depth_shortfall_watch")
    if absolute_imbalance_ratio >= config.imbalance_block:
        reason_codes.append("depth_imbalance_block")
    elif absolute_imbalance_ratio >= config.imbalance_watch:
        reason_codes.append("depth_imbalance_watch")
    if row.spread_width >= config.spread_width_block:
        reason_codes.append("spread_width_block")
    elif row.spread_width >= config.spread_width_watch:
        reason_codes.append("spread_width_watch")
    if snapshot_age_seconds > config.stale_snapshot_age_seconds:
        reason_codes.append("snapshot_stale_watch")
    if not _has_anomaly_reason(reason_codes):
        reason_codes.append("market_depth_clear")
    return tuple(sorted(reason_codes))


def _has_anomaly_reason(reason_codes: list[str]) -> bool:
    return any(
        reason_code.endswith("_watch") or reason_code.endswith("_block")
        for reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _rollup_reason_codes(
    rows: tuple[ResearchMarketDepthAnomalyDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [f"market_depth_anomaly_digest_{'clear' if status == 'pass' else status}"]
    row_reason_codes = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    )
    for reason_code in (
        "depth_imbalance_block",
        "depth_imbalance_watch",
        "depth_shortfall_block",
        "depth_shortfall_watch",
        "snapshot_stale_watch",
        "spread_width_block",
        "spread_width_watch",
    ):
        if reason_code in row_reason_codes:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchMarketDepthAnomalyDigestRow, ...],
) -> tuple[ResearchMarketDepthAnomalyDigestReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketDepthAnomalyDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchMarketDepthAnomalyDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _snapshot_age_seconds(snapshot_at: datetime, generated_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - _as_utc("snapshot_at", snapshot_at)).total_seconds()))
    age_seconds = _quantize(seconds)
    if age_seconds < ZERO:
        raise ValueError("snapshot_at must not be after generated_at")
    return age_seconds


def _normalize_observations(
    observations: Iterable[ResearchMarketDepthAnomalyObservation],
) -> tuple[ResearchMarketDepthAnomalyObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        rows = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_segments: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketDepthAnomalyObservation:
            raise ValueError(
                "observations must contain ResearchMarketDepthAnomalyObservation values",
            )
        _require_hard_flags("observation", row)
        if row.segment in seen_segments:
            raise ValueError("observations must not contain duplicate segment values")
        seen_segments.add(row.segment)
    return rows


def _normalize_rows(
    rows: Iterable[ResearchMarketDepthAnomalyDigestRow],
) -> tuple[ResearchMarketDepthAnomalyDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("market_depth_anomaly_rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("market_depth_anomaly_rows must be an iterable") from exc
    seen_segments: set[str] = set()
    for row in values:
        if type(row) is not ResearchMarketDepthAnomalyDigestRow:
            raise ValueError(
                "market_depth_anomaly_rows must contain ResearchMarketDepthAnomalyDigestRow values",
            )
        _require_hard_flags("row", row)
        if row.segment in seen_segments:
            raise ValueError("market_depth_anomaly_rows must not contain duplicate segment values")
        seen_segments.add(row.segment)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("market_depth_anomaly_rows must use canonical sequence")
    expected_labels = tuple(_review_label(index) for index in range(1, len(values) + 1))
    if tuple(row.review_label for row in values) != expected_labels:
        raise ValueError("market_depth_anomaly_rows must use canonical review labels")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchMarketDepthAnomalyDigestReasonCodeCount],
) -> tuple[ResearchMarketDepthAnomalyDigestReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchMarketDepthAnomalyDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchMarketDepthAnomalyDigestReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    expected = tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must be sorted by count then reason_code")
    return values


def _row_sort_key(
    row: ResearchMarketDepthAnomalyDigestRow,
) -> tuple[Decimal, Decimal, str]:
    return (-STATUS_WEIGHT[row.status], -row.anomaly_score, row.segment)


def _status_count(
    rows: tuple[ResearchMarketDepthAnomalyDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_prefix_count(
    rows: tuple[ResearchMarketDepthAnomalyDigestRow, ...],
    prefix: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(reason_code.startswith(prefix) for reason_code in row.reason_codes)
        ),
    )


def _reason_member_count(
    rows: tuple[ResearchMarketDepthAnomalyDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _validate_report(report: ResearchMarketDepthAnomalyDigestReport) -> None:
    rows = report.market_depth_anomaly_rows
    if report.observation_count != _count(len(rows)):
        raise ValueError("observation_count must match market_depth_anomaly_rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match market_depth_anomaly_rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match market_depth_anomaly_rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match market_depth_anomaly_rows")
    if report.depth_shortfall_count != _reason_prefix_count(rows, "depth_shortfall_"):
        raise ValueError("depth_shortfall_count must match market_depth_anomaly_rows")
    if report.depth_imbalance_count != _reason_prefix_count(rows, "depth_imbalance_"):
        raise ValueError("depth_imbalance_count must match market_depth_anomaly_rows")
    if report.spread_width_count != _reason_prefix_count(rows, "spread_width_"):
        raise ValueError("spread_width_count must match market_depth_anomaly_rows")
    if report.stale_snapshot_count != _reason_member_count(rows, "snapshot_stale_watch"):
        raise ValueError("stale_snapshot_count must match market_depth_anomaly_rows")
    if report.mean_anomaly_score != _mean(tuple(row.anomaly_score for row in rows)):
        raise ValueError("mean_anomaly_score must match market_depth_anomaly_rows")
    if report.max_anomaly_score != _max_decimal(tuple(row.anomaly_score for row in rows)):
        raise ValueError("max_anomaly_score must match market_depth_anomaly_rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match market_depth_anomaly_rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match market_depth_anomaly_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match market_depth_anomaly_rows")


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        _revalidate_public_dataclass_for_payload(label, value)
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        _rebuild_public_dataclass(label, value)
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            _require_canonical_string(label, value)
        return
    if type(value) in (int, float) or isinstance(value, (list, dict, set)):
        raise ValueError(f"{label} must come from public dataclass fields")
    raise ValueError(f"{label} contains unsupported value")


def _revalidate_public_dataclass_for_payload(label: str, value: object) -> None:
    if type(value) is ResearchMarketDepthAnomalyDigestConfig:
        _revalidate_config_for_payload(value)
        return
    if type(value) is ResearchMarketDepthAnomalyObservation:
        _revalidate_observation_for_payload(value)
        return
    if type(value) is ResearchMarketDepthAnomalyDigestRow:
        _revalidate_row_for_payload(value)
        return
    if type(value) is ResearchMarketDepthAnomalyDigestReasonCodeCount:
        _revalidate_reason_code_count_for_payload(value)
        return
    if type(value) is ResearchMarketDepthAnomalyDigestReport:
        _revalidate_report_for_payload(value)
        return
    raise ValueError(f"{label} contains unsupported dataclass")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed payload revalidation") from exc


def _revalidate_config_for_payload(config: ResearchMarketDepthAnomalyDigestConfig) -> None:
    _require_exact_type(config, ResearchMarketDepthAnomalyDigestConfig, "config")
    _require_canonical_string("config_version", config.config_version)
    for field_name in (
        "depth_shortfall_watch",
        "depth_shortfall_block",
        "imbalance_watch",
        "imbalance_block",
        "spread_width_watch",
        "spread_width_block",
        "stale_snapshot_age_seconds",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(config, field_name))
    _require_at_most("depth_shortfall_watch", config.depth_shortfall_watch, config.depth_shortfall_block)
    _require_at_most("imbalance_watch", config.imbalance_watch, config.imbalance_block)
    _require_at_most("spread_width_watch", config.spread_width_watch, config.spread_width_block)
    _require_hard_flags("config", config)


def _revalidate_observation_for_payload(row: ResearchMarketDepthAnomalyObservation) -> None:
    _require_exact_type(row, ResearchMarketDepthAnomalyObservation, "observation")
    _require_canonical_string("segment", row.segment)
    for field_name in (
        "best_bid_depth",
        "best_ask_depth",
        "top_bid_depth",
        "top_ask_depth",
        "spread_width",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(row, field_name))
    _require_positive_six_decimal_decimal("baseline_depth", row.baseline_depth)
    _require_utc_datetime("snapshot_at", row.snapshot_at)
    _require_reason_codes_tuple(row.reason_codes)
    if row.reason_codes != _normalize_reason_codes(row.reason_codes):
        raise ValueError("reason_codes must use canonical sequence")
    _require_hard_flags("observation", row)


def _revalidate_row_for_payload(row: ResearchMarketDepthAnomalyDigestRow) -> None:
    _require_exact_type(row, ResearchMarketDepthAnomalyDigestRow, "row")
    _require_canonical_string("review_label", row.review_label)
    _require_canonical_string("segment", row.segment)
    _require_status("status", row.status)
    for field_name in (
        "best_bid_depth",
        "best_ask_depth",
        "top_bid_depth",
        "top_ask_depth",
        "total_depth",
        "depth_ratio",
        "depth_shortfall_ratio",
        "absolute_imbalance_ratio",
        "spread_width",
        "snapshot_age_seconds",
        "anomaly_score",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(row, field_name))
    _require_positive_six_decimal_decimal("baseline_depth", row.baseline_depth)
    _require_utc_datetime("snapshot_at", row.snapshot_at)
    _require_reason_codes_tuple(row.reason_codes)
    if row.reason_codes != _normalize_reason_codes(row.reason_codes):
        raise ValueError("reason_codes must use canonical sequence")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    _require_hard_flags("row", row)


def _revalidate_reason_code_count_for_payload(
    row: ResearchMarketDepthAnomalyDigestReasonCodeCount,
) -> None:
    _require_exact_type(row, ResearchMarketDepthAnomalyDigestReasonCodeCount, "reason_code_count")
    _require_canonical_string("reason_code", row.reason_code)
    _require_positive_six_decimal_decimal("count", row.count)
    _require_hard_flags("reason_code_count", row)


def _revalidate_report_for_payload(report: ResearchMarketDepthAnomalyDigestReport) -> None:
    _require_exact_type(report, ResearchMarketDepthAnomalyDigestReport, "report")
    _require_utc_datetime("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    for field_name in (
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "depth_shortfall_count",
        "depth_imbalance_count",
        "spread_width_count",
        "stale_snapshot_count",
        "mean_anomaly_score",
        "max_anomaly_score",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(report, field_name))
    _require_status("status", report.status)
    _require_reason_codes_tuple(report.reason_codes)
    _normalize_report_reason_codes(report.reason_codes)
    _normalize_reason_code_counts(report.reason_code_counts)
    _normalize_rows(report.market_depth_anomaly_rows)
    _validate_report(report)
    _require_hard_flags("report", report)


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_safe_value("JSON value", value)
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if isinstance(value, (list, dict, set)):
        raise ValueError("JSON value must come from public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} contains unsupported dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(path or label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower().replace("imbalance", "")
    return any(fragment in normalized for fragment in _unsafe_fragments())


def _unsafe_fragments() -> frozenset[str]:
    return frozenset(UNSAFE_SURFACE_FIELD_FRAGMENTS) | frozenset(
        (
            "raw_" "candidate",
            "candidate_" "id",
            "market_" "id",
            "market_" "slug",
            "market_" "question",
            "source_" "ref",
            "source_" "url",
            "source_" "text",
            "d" "s" "n",
            "ta" "ble",
            "to" "ken",
            "po" "sition",
            "tr" "ade",
            "bu" "y",
            "se" "ll",
            "reco" "mmend",
        ),
    )


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: datetime) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")


def _require_nonnegative_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    _require_six_decimal_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    _require_nonnegative_six_decimal_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_reason_codes_tuple(reason_codes: object) -> None:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_canonical_string("reason_codes", reason_code)
    normalized = tuple(sorted(values))
    if values != normalized:
        raise ValueError("reason_codes must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _normalize_report_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_canonical_string("reason_codes", reason_code)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    return values


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_at_most(field_name: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{field_name} must be less than or equal to paired threshold")


def _require_ratio_at_most_one(field_name: str, value: Decimal) -> None:
    if value > ONE:
        raise ValueError(f"{field_name} must be less than or equal to one")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
