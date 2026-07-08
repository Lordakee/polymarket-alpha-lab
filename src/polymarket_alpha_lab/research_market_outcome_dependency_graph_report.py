"""Pure dependency-overlap report reducer for outcome research queues."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_OUTCOME_DEPENDENCY_GRAPH_REPORT_VERSION",
    "ResearchMarketOutcomeDependencyGraphConfig",
    "ResearchMarketOutcomeDependencyGraphObservation",
    "ResearchMarketOutcomeDependencyGraphPairRow",
    "ResearchMarketOutcomeDependencyGraphReasonCodeCount",
    "ResearchMarketOutcomeDependencyGraphReport",
    "build_research_market_outcome_dependency_graph_report",
    "research_market_outcome_dependency_graph_report_digest",
    "research_market_outcome_dependency_graph_report_payload",
)


DEFAULT_RESEARCH_MARKET_OUTCOME_DEPENDENCY_GRAPH_REPORT_VERSION = (
    "research-market-outcome-dependency-graph-report-v0"
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
NO_INPUTS_REASON = "outcome_dependency_graph_no_inputs"
SAFE_REASON_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_-")
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "raw",
    "candidate",
    "market_" + "id",
    "market-" + "id",
    "market_" + "slug",
    "market-" + "slug",
    "question",
    "source_" + "ref",
    "source-" + "ref",
    "source_" + "url",
    "source-" + "url",
    "source_" + "text",
    "source-" + "text",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "pos" + "ition",
    "tr" + "ade",
    "b" + "uy",
    "se" + "ll",
    "recom" + "mend",
    "://",
    "www.",
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
class ResearchMarketOutcomeDependencyGraphConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_MARKET_OUTCOME_DEPENDENCY_GRAPH_REPORT_VERSION
    event_overlap_watch: Decimal = Decimal("0.500000")
    event_overlap_block: Decimal = Decimal("0.800000")
    resolution_overlap_watch: Decimal = Decimal("0.500000")
    resolution_overlap_block: Decimal = Decimal("0.800000")
    evidence_overlap_watch: Decimal = Decimal("0.400000")
    evidence_overlap_block: Decimal = Decimal("0.700000")
    semantic_overlap_watch: Decimal = Decimal("0.450000")
    semantic_overlap_block: Decimal = Decimal("0.750000")
    timing_overlap_watch: Decimal = Decimal("0.500000")
    timing_overlap_block: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketOutcomeDependencyGraphConfig, "config")
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "event_overlap_watch",
            "event_overlap_block",
            "resolution_overlap_watch",
            "resolution_overlap_block",
            "evidence_overlap_watch",
            "evidence_overlap_block",
            "semantic_overlap_watch",
            "semantic_overlap_block",
            "timing_overlap_watch",
            "timing_overlap_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for watch_field, block_field in (
            ("event_overlap_watch", "event_overlap_block"),
            ("resolution_overlap_watch", "resolution_overlap_block"),
            ("evidence_overlap_watch", "evidence_overlap_block"),
            ("semantic_overlap_watch", "semantic_overlap_block"),
            ("timing_overlap_watch", "timing_overlap_block"),
        ):
            _require_at_most(watch_field, getattr(self, watch_field), getattr(self, block_field))
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketOutcomeDependencyGraphObservation(_FinalPublicDataclass):
    left_key: str
    right_key: str
    event_overlap_ratio: Decimal
    resolution_overlap_ratio: Decimal
    evidence_overlap_ratio: Decimal
    semantic_overlap_ratio: Decimal
    timing_overlap_ratio: Decimal
    hard_dependency_flag: bool = False
    duplicate_research_flag: bool = False
    correlation_crowding_flag: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketOutcomeDependencyGraphObservation,
            "observation",
        )
        _require_internal_key("left_key", self.left_key)
        _require_internal_key("right_key", self.right_key)
        if self.left_key == self.right_key:
            raise ValueError("left_key and right_key must be distinct")
        for field_name in (
            "event_overlap_ratio",
            "resolution_overlap_ratio",
            "evidence_overlap_ratio",
            "semantic_overlap_ratio",
            "timing_overlap_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "hard_dependency_flag",
            "duplicate_research_flag",
            "correlation_crowding_flag",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketOutcomeDependencyGraphPairRow(_FinalPublicDataclass):
    pair_label: str
    left_node_label: str
    right_node_label: str
    dependency_status: str
    event_overlap_ratio: Decimal
    resolution_overlap_ratio: Decimal
    evidence_overlap_ratio: Decimal
    semantic_overlap_ratio: Decimal
    timing_overlap_ratio: Decimal
    dependency_score: Decimal
    hard_dependency_flag: bool
    duplicate_research_flag: bool
    correlation_crowding_flag: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketOutcomeDependencyGraphPairRow, "row")
        for field_name in ("pair_label", "left_node_label", "right_node_label"):
            _require_public_label(field_name, getattr(self, field_name))
        if self.left_node_label == self.right_node_label:
            raise ValueError("node labels must be distinct")
        _require_status("dependency_status", self.dependency_status)
        for field_name in (
            "event_overlap_ratio",
            "resolution_overlap_ratio",
            "evidence_overlap_ratio",
            "semantic_overlap_ratio",
            "timing_overlap_ratio",
            "dependency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "hard_dependency_flag",
            "duplicate_research_flag",
            "correlation_crowding_flag",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        if self.dependency_status != _row_status(self.reason_codes):
            raise ValueError("dependency_status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketOutcomeDependencyGraphReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketOutcomeDependencyGraphReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketOutcomeDependencyGraphReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    pair_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    hard_dependency_count: Decimal
    duplicate_research_count: Decimal
    correlation_crowding_count: Decimal
    mean_dependency_score: Decimal
    max_dependency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketOutcomeDependencyGraphReasonCodeCount, ...]
    pair_rows: tuple[ResearchMarketOutcomeDependencyGraphPairRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketOutcomeDependencyGraphReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "pair_count",
            "pass_count",
            "watch_count",
            "block_count",
            "hard_dependency_count",
            "duplicate_research_count",
            "correlation_crowding_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_dependency_score", "max_dependency_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "pair_rows", _normalize_rows(self.pair_rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchMarketOutcomeDependencyGraphConfig,
    ResearchMarketOutcomeDependencyGraphObservation,
    ResearchMarketOutcomeDependencyGraphPairRow,
    ResearchMarketOutcomeDependencyGraphReasonCodeCount,
    ResearchMarketOutcomeDependencyGraphReport,
)


def build_research_market_outcome_dependency_graph_report(
    observations: Iterable[ResearchMarketOutcomeDependencyGraphObservation],
    *,
    config: ResearchMarketOutcomeDependencyGraphConfig,
    generated_at: datetime,
) -> ResearchMarketOutcomeDependencyGraphReport:
    if type(config) is not ResearchMarketOutcomeDependencyGraphConfig:
        raise ValueError("config must be a ResearchMarketOutcomeDependencyGraphConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_observations(observations)
    node_labels = _node_labels(inputs)
    pair_rows: list[ResearchMarketOutcomeDependencyGraphPairRow] = []
    for index, item in enumerate(sorted(inputs, key=_observation_pair_sort_key), start=1):
        left_key, right_key = _canonical_pair_keys(item)
        pair_rows.append(
            _pair_row(
                item,
                config=config,
                pair_label=f"pair-{index:06d}",
                left_node_label=node_labels[left_key],
                right_node_label=node_labels[right_key],
            ),
        )
    rows = tuple(sorted(pair_rows, key=_row_sort_key))
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketOutcomeDependencyGraphReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        pair_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        hard_dependency_count=_bool_count(rows, "hard_dependency_flag"),
        duplicate_research_count=_bool_count(rows, "duplicate_research_flag"),
        correlation_crowding_count=_bool_count(rows, "correlation_crowding_flag"),
        mean_dependency_score=_mean(tuple(row.dependency_score for row in rows)),
        max_dependency_score=_max_decimal(tuple(row.dependency_score for row in rows)),
        status=_report_status(tuple(row.dependency_status for row in rows)),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        pair_rows=rows,
    )


def research_market_outcome_dependency_graph_report_payload(
    report: ResearchMarketOutcomeDependencyGraphReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketOutcomeDependencyGraphReport:
        raise ValueError("report must be a ResearchMarketOutcomeDependencyGraphReport")
    _require_payload_safe_value("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_market_outcome_dependency_graph_report_digest(
    report: ResearchMarketOutcomeDependencyGraphReport,
) -> dict[str, Any]:
    payload = research_market_outcome_dependency_graph_report_payload(report)
    digest = {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "pair_count": payload["pair_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "hard_dependency_count": payload["hard_dependency_count"],
        "duplicate_research_count": payload["duplicate_research_count"],
        "correlation_crowding_count": payload["correlation_crowding_count"],
        "mean_dependency_score": payload["mean_dependency_score"],
        "max_dependency_score": payload["max_dependency_score"],
        "status": payload["status"],
        "reason_codes": payload["reason_codes"],
        "reason_code_counts": payload["reason_code_counts"],
        "pair_rows": tuple(
            {
                "pair_label": row["pair_label"],
                "left_node_label": row["left_node_label"],
                "right_node_label": row["right_node_label"],
                "dependency_status": row["dependency_status"],
                "dependency_score": row["dependency_score"],
                "hard_dependency_flag": row["hard_dependency_flag"],
                "duplicate_research_flag": row["duplicate_research_flag"],
                "correlation_crowding_flag": row["correlation_crowding_flag"],
                "reason_codes": row["reason_codes"],
            }
            for row in payload["pair_rows"]
        ),
        "paper_only": payload["paper_only"],
        "report_only": payload["report_only"],
        "readonly": payload["readonly"],
    }
    _reject_unsafe_public_payload("digest", digest)
    return digest


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


def _pair_row(
    item: ResearchMarketOutcomeDependencyGraphObservation,
    *,
    config: ResearchMarketOutcomeDependencyGraphConfig,
    pair_label: str,
    left_node_label: str,
    right_node_label: str,
) -> ResearchMarketOutcomeDependencyGraphPairRow:
    reason_codes = _pair_reason_codes(item, config=config)
    return ResearchMarketOutcomeDependencyGraphPairRow(
        pair_label=pair_label,
        left_node_label=left_node_label,
        right_node_label=right_node_label,
        dependency_status=_row_status(reason_codes),
        event_overlap_ratio=item.event_overlap_ratio,
        resolution_overlap_ratio=item.resolution_overlap_ratio,
        evidence_overlap_ratio=item.evidence_overlap_ratio,
        semantic_overlap_ratio=item.semantic_overlap_ratio,
        timing_overlap_ratio=item.timing_overlap_ratio,
        dependency_score=_dependency_score(item, reason_codes),
        hard_dependency_flag=item.hard_dependency_flag,
        duplicate_research_flag=item.duplicate_research_flag,
        correlation_crowding_flag=item.correlation_crowding_flag,
        reason_codes=reason_codes,
    )


def _pair_reason_codes(
    item: ResearchMarketOutcomeDependencyGraphObservation,
    *,
    config: ResearchMarketOutcomeDependencyGraphConfig,
) -> tuple[str, ...]:
    generated: list[str] = []
    if item.hard_dependency_flag:
        generated.append("hard_dependency_block")
    if item.duplicate_research_flag:
        generated.append("duplicate_research_block")
    if item.correlation_crowding_flag:
        generated.append("correlation_crowding_watch")
    for metric_name, value, watch, block in (
        (
            "event_overlap",
            item.event_overlap_ratio,
            config.event_overlap_watch,
            config.event_overlap_block,
        ),
        (
            "resolution_overlap",
            item.resolution_overlap_ratio,
            config.resolution_overlap_watch,
            config.resolution_overlap_block,
        ),
        (
            "evidence_overlap",
            item.evidence_overlap_ratio,
            config.evidence_overlap_watch,
            config.evidence_overlap_block,
        ),
        (
            "semantic_overlap",
            item.semantic_overlap_ratio,
            config.semantic_overlap_watch,
            config.semantic_overlap_block,
        ),
        (
            "timing_overlap",
            item.timing_overlap_ratio,
            config.timing_overlap_watch,
            config.timing_overlap_block,
        ),
    ):
        if value >= block:
            generated.append(f"{metric_name}_block")
        elif value >= watch:
            generated.append(f"{metric_name}_watch")
    if not generated:
        generated.append("dependency_overlap_clear")
    generated.extend(f"input_{reason_code}" for reason_code in item.reason_codes)
    return tuple(sorted(set(generated)))


def _dependency_score(
    item: ResearchMarketOutcomeDependencyGraphObservation,
    reason_codes: tuple[str, ...],
) -> Decimal:
    if _row_status(reason_codes) == "block" and (
        item.hard_dependency_flag or item.duplicate_research_flag
    ):
        return ONE
    score = _max_decimal(
        (
            item.event_overlap_ratio,
            item.resolution_overlap_ratio,
            item.evidence_overlap_ratio,
            item.semantic_overlap_ratio,
            item.timing_overlap_ratio,
        ),
    )
    if item.correlation_crowding_flag and score < Decimal("0.500000"):
        return Decimal("0.500000")
    return score


def _normalize_observations(
    observations: Iterable[ResearchMarketOutcomeDependencyGraphObservation],
) -> tuple[ResearchMarketOutcomeDependencyGraphObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        rows = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_pairs: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchMarketOutcomeDependencyGraphObservation:
            raise ValueError(
                "observations must contain ResearchMarketOutcomeDependencyGraphObservation values",
            )
        _require_hard_flags("observation", row)
        pair_keys = _canonical_pair_keys(row)
        if pair_keys in seen_pairs:
            raise ValueError("observations must not contain duplicate pairs")
        seen_pairs.add(pair_keys)
    return rows


def _normalize_rows(
    rows: Iterable[ResearchMarketOutcomeDependencyGraphPairRow],
) -> tuple[ResearchMarketOutcomeDependencyGraphPairRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("pair_rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("pair_rows must be an iterable") from exc
    seen_pair_labels: set[str] = set()
    seen_node_pairs: set[tuple[str, str]] = set()
    for row in values:
        if type(row) is not ResearchMarketOutcomeDependencyGraphPairRow:
            raise ValueError(
                "pair_rows must contain ResearchMarketOutcomeDependencyGraphPairRow values",
            )
        _require_hard_flags("row", row)
        if row.pair_label in seen_pair_labels:
            raise ValueError("pair_rows must not contain duplicate pair labels")
        seen_pair_labels.add(row.pair_label)
        node_pair = (row.left_node_label, row.right_node_label)
        if node_pair in seen_node_pairs:
            raise ValueError("pair_rows must not contain duplicate node pairs")
        seen_node_pairs.add(node_pair)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("pair_rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchMarketOutcomeDependencyGraphReasonCodeCount],
) -> tuple[ResearchMarketOutcomeDependencyGraphReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchMarketOutcomeDependencyGraphReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchMarketOutcomeDependencyGraphReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason codes")
        seen_codes.add(row.reason_code)
    expected = tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must use canonical sequence")
    return values


def _node_labels(
    observations: tuple[ResearchMarketOutcomeDependencyGraphObservation, ...],
) -> dict[str, str]:
    keys = sorted(
        {
            key
            for observation in observations
            for key in _canonical_pair_keys(observation)
        },
    )
    return {key: f"node-{index:06d}" for index, key in enumerate(keys, start=1)}


def _canonical_pair_keys(
    item: ResearchMarketOutcomeDependencyGraphObservation,
) -> tuple[str, str]:
    left_key, right_key = sorted((item.left_key, item.right_key))
    return (left_key, right_key)


def _observation_pair_sort_key(
    item: ResearchMarketOutcomeDependencyGraphObservation,
) -> tuple[str, str]:
    return _canonical_pair_keys(item)


def _row_sort_key(
    row: ResearchMarketOutcomeDependencyGraphPairRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        -STATUS_WEIGHT[row.dependency_status],
        -row.dependency_score,
        row.pair_label,
        row.left_node_label,
        row.right_node_label,
    )


def _report_reason_codes(
    rows: tuple[ResearchMarketOutcomeDependencyGraphPairRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _report_status(tuple(row.dependency_status for row in rows))
    codes = [f"outcome_dependency_graph_report_{status}"]
    row_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    for reason_code in (
        "hard_dependency_block",
        "duplicate_research_block",
        "event_overlap_block",
        "resolution_overlap_block",
        "evidence_overlap_block",
        "semantic_overlap_block",
        "timing_overlap_block",
        "correlation_crowding_watch",
        "event_overlap_watch",
        "resolution_overlap_watch",
        "evidence_overlap_watch",
        "semantic_overlap_watch",
        "timing_overlap_watch",
        "dependency_overlap_clear",
    ):
        if reason_code in row_codes:
            codes.append(reason_code)
    return tuple(codes)


def _reason_code_counts(
    rows: tuple[ResearchMarketOutcomeDependencyGraphPairRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketOutcomeDependencyGraphReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketOutcomeDependencyGraphReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter(report_reason_codes[:1])
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchMarketOutcomeDependencyGraphReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _status_count(
    rows: tuple[ResearchMarketOutcomeDependencyGraphPairRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.dependency_status == status))


def _bool_count(
    rows: tuple[ResearchMarketOutcomeDependencyGraphPairRow, ...],
    field_name: str,
) -> Decimal:
    return _count(sum(1 for row in rows if getattr(row, field_name) is True))


def _report_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    active_codes = tuple(
        reason_code for reason_code in reason_codes if not reason_code.startswith("input_")
    )
    if any(reason_code.endswith("_block") for reason_code in active_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in active_codes):
        return "watch"
    return "pass"


def _validate_report(report: ResearchMarketOutcomeDependencyGraphReport) -> None:
    rows = report.pair_rows
    if report.pair_count != _count(len(rows)):
        raise ValueError("pair_count must match pair_rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match pair_rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match pair_rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match pair_rows")
    if report.hard_dependency_count != _bool_count(rows, "hard_dependency_flag"):
        raise ValueError("hard_dependency_count must match pair_rows")
    if report.duplicate_research_count != _bool_count(rows, "duplicate_research_flag"):
        raise ValueError("duplicate_research_count must match pair_rows")
    if report.correlation_crowding_count != _bool_count(
        rows,
        "correlation_crowding_flag",
    ):
        raise ValueError("correlation_crowding_count must match pair_rows")
    if report.mean_dependency_score != _mean(tuple(row.dependency_score for row in rows)):
        raise ValueError("mean_dependency_score must match pair_rows")
    if report.max_dependency_score != _max_decimal(tuple(row.dependency_score for row in rows)):
        raise ValueError("max_dependency_score must match pair_rows")
    if report.status != _report_status(tuple(row.dependency_status for row in rows)):
        raise ValueError("status must match pair_rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match pair_rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match pair_rows")


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
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
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        _require_canonical_public_string(label, value)
        return
    if type(value) in (int, float) or isinstance(value, (list, dict, set)):
        raise ValueError(f"{label} must come from public dataclass fields")
    raise ValueError(f"{label} contains unsupported value")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed payload revalidation") from exc


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} contains unsupported dataclass")
        for field in fields(value):
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_text(label, field.name, field_path)
            _reject_unsafe_public_payload(label, getattr(value, field.name), field_path)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_text(label, key, item_path)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value, path or label)
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(path or label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal numeric strings")
    raise ValueError(f"{path or label} is not JSON serializable")


def _reject_unsafe_public_text(label: str, value: str, path: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{path or label} has unsafe public value")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("payload contains unsupported dataclass")
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return str(value)
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if value is None or type(value) in (bool, str):
        return value
    if type(value) is dict:
        return _json_ready_dict(value)
    if type(value) in (int, float) or isinstance(value, (list, set)):
        raise ValueError("JSON value must use public dataclass values")
    raise ValueError("value is not JSON serializable")


def _json_ready_dict(value: dict[Any, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        ready[key] = _json_ready(item)
    return ready


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count seed must be an int")
    if value < 0:
        raise ValueError("count seed must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(QUANTUM)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: datetime) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be UTC")


def _require_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")


def _require_internal_key(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_public_label(field_name: str, value: object) -> None:
    _require_canonical_public_string(field_name, value)
    if type(value) is str and not value.startswith(("pair-", "node-")):
        raise ValueError(f"{field_name} must use a public label")


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    _reject_unsafe_public_text(field_name, value, field_name)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain nonempty reason codes")
    if value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must use canonical reason codes")
    if any(char not in SAFE_REASON_CHARS for char in value):
        raise ValueError(f"{field_name} must use safe reason code characters")
    _reject_unsafe_public_text(field_name, value, field_name)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(normalized))


def _normalize_report_reason_codes(
    field_name: str,
    values: object,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(normalized)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_at_most(field_name: str, value: Decimal, upper_value: Decimal) -> None:
    if value > upper_value:
        raise ValueError(f"{field_name} must be less than or equal to block threshold")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
