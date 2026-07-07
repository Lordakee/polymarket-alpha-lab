"""Report-only quality gate for caller-supplied source collection results."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchSourceCollectionItem",
    "ResearchSourceCollectionQualityGateConfig",
    "ResearchSourceCollectionQualityGateReasonCodeCount",
    "ResearchSourceCollectionQualityGateReport",
    "ResearchSourceCollectionQualityGateRow",
    "ResearchSourceCollectionQualityPublicPayloadItem",
    "build_research_source_collection_quality_gate_report",
    "research_source_collection_quality_gate_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-source-collection-quality-gate-v0"
STATUSES = ("pass", "watch", "blocked")
SOURCE_KINDS = ("official", "primary", "secondary", "analysis")
STANCE_VALUES = ("supports", "contradicts", "context")
VERIFICATION_SCORES = {
    "verified": Decimal("1.000000"),
    "partially_verified": Decimal("0.500000"),
    "unverified": Decimal("0.000000"),
}
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_PASS_QUALITY_SCORE = Decimal("0.750000")
DEFAULT_WATCH_QUALITY_SCORE = Decimal("0.450000")


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchSourceCollectionQualityGateConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("3600")
    stale_age_seconds: Decimal = Decimal("86400")
    min_source_count: Decimal = Decimal("2")
    min_source_family_count: Decimal = Decimal("2")
    min_counterevidence_check_count: Decimal = Decimal("1")
    pass_quality_score: Decimal = DEFAULT_PASS_QUALITY_SCORE
    watch_quality_score: Decimal = DEFAULT_WATCH_QUALITY_SCORE
    independence_weight: Decimal = Decimal("0.300000")
    timeliness_weight: Decimal = Decimal("0.250000")
    verifiability_weight: Decimal = Decimal("0.250000")
    counterevidence_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchSourceCollectionQualityGateConfig,
        )
        _require_public_string("config_version", self.config_version)
        for field_name in ("fresh_age_seconds", "stale_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must be greater than fresh_age_seconds")
        for field_name in (
            "min_source_count",
            "min_source_family_count",
            "min_counterevidence_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_quality_score",
            "watch_quality_score",
            "independence_weight",
            "timeliness_weight",
            "verifiability_weight",
            "counterevidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_quality_score <= self.watch_quality_score:
            raise ValueError("pass_quality_score must be greater than watch_quality_score")
        weight_sum = _quantize(
            self.independence_weight
            + self.timeliness_weight
            + self.verifiability_weight
            + self.counterevidence_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "independence_weight, timeliness_weight, verifiability_weight, "
                "and counterevidence_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceCollectionItem:
    collection_id: str
    claim_id: str
    source_id: str
    source_family: str
    source_kind: str
    stance: str
    collected_at: datetime
    verification_status: str
    counterevidence_checked: bool
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("source item", self, ResearchSourceCollectionItem)
        for field_name in (
            "collection_id",
            "claim_id",
            "source_id",
            "source_family",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_enum("source_kind", self.source_kind, SOURCE_KINDS)
        _require_enum("stance", self.stance, STANCE_VALUES)
        object.__setattr__(
            self,
            "collected_at",
            _as_utc("collected_at", self.collected_at),
        )
        _require_enum(
            "verification_status",
            self.verification_status,
            tuple(VERIFICATION_SCORES),
        )
        if type(self.counterevidence_checked) is not bool:
            raise ValueError("counterevidence_checked must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=True,
            ),
        )
        _require_hard_flags("source item", self)
        _reject_unsafe_public_payload("source item", self)


@dataclass(frozen=True)
class ResearchSourceCollectionQualityPublicPayloadItem:
    payload_id: str
    collection_id: str
    claim_id: str
    public_summary: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "public payload item",
            self,
            ResearchSourceCollectionQualityPublicPayloadItem,
        )
        for field_name in ("payload_id", "collection_id", "claim_id", "public_summary"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=True,
            ),
        )
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSourceCollectionQualityGateRow:
    collection_id: str
    claim_id: str
    source_count: Decimal
    source_family_count: Decimal
    verifiable_source_count: Decimal
    counterevidence_checked_count: Decimal
    stale_source_count: Decimal
    unverified_source_count: Decimal
    latest_collected_at: datetime
    latest_source_age_seconds: Decimal
    independence_score: Decimal
    timeliness_score: Decimal
    verifiability_score: Decimal
    counterevidence_score: Decimal
    quality_score: Decimal
    gate_status: str
    source_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceCollectionQualityGateRow)
        _require_public_string("collection_id", self.collection_id)
        _require_public_string("claim_id", self.claim_id)
        for field_name in (
            "source_count",
            "source_family_count",
            "verifiable_source_count",
            "counterevidence_checked_count",
            "stale_source_count",
            "unverified_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_collected_at",
            _as_utc("latest_collected_at", self.latest_collected_at),
        )
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _require_nonnegative_decimal(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        for field_name in (
            "independence_score",
            "timeliness_score",
            "verifiability_score",
            "counterevidence_score",
            "quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("gate_status", self.gate_status)
        for field_name in ("source_ids", "source_families"):
            object.__setattr__(
                self,
                field_name,
                _normalize_public_string_tuple(
                    field_name,
                    getattr(self, field_name),
                    allow_empty=True,
                ),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", self)

    @property
    def status(self) -> str:
        return self.gate_status


@dataclass(frozen=True)
class ResearchSourceCollectionQualityGateReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason code count",
            self,
            ResearchSourceCollectionQualityGateReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchSourceCollectionQualityGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    collection_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_quality_score: Decimal | None
    rows: tuple[ResearchSourceCollectionQualityGateRow, ...]
    reason_code_counts: tuple[ResearchSourceCollectionQualityGateReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchSourceCollectionQualityPublicPayloadItem, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourceCollectionQualityGateReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("gate_status", self.gate_status)
        for field_name in (
            "collection_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_quality_score",
            _require_optional_ratio_decimal(
                "average_quality_score",
                self.average_quality_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)

    @property
    def status(self) -> str:
        return self.gate_status

    @property
    def payload(self) -> dict[str, object]:
        return research_source_collection_quality_gate_report_payload(self)


def build_research_source_collection_quality_gate_report(
    source_items: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchSourceCollectionQualityGateConfig | None = None,
    public_payload: Iterable[object] = (),
) -> ResearchSourceCollectionQualityGateReport:
    if config is None:
        config = ResearchSourceCollectionQualityGateConfig()
    if type(config) is not ResearchSourceCollectionQualityGateConfig:
        raise ValueError("config must be a ResearchSourceCollectionQualityGateConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_source_items(source_items)
    payload_items = _normalize_public_payload(public_payload)
    for item in normalized_items:
        if item.collected_at > generated_at_utc:
            raise ValueError("collected_at must not be after generated_at")

    grouped: dict[tuple[str, str], list[ResearchSourceCollectionItem]] = {}
    for item in normalized_items:
        grouped.setdefault((item.collection_id, item.claim_id), []).append(item)

    rows = tuple(
        _row_for_collection(
            collection_id=collection_id,
            claim_id=claim_id,
            items=tuple(grouped[(collection_id, claim_id)]),
            generated_at=generated_at_utc,
            config=config,
        )
        for collection_id, claim_id in sorted(grouped)
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchSourceCollectionQualityGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        gate_status=_summary_status(reason_codes),
        collection_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "blocked")),
        average_quality_score=_average_quality_score(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
        public_payload=payload_items,
    )


def research_source_collection_quality_gate_report_payload(
    report: ResearchSourceCollectionQualityGateReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceCollectionQualityGateReport:
        raise ValueError("report must be a ResearchSourceCollectionQualityGateReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    _reject_unsafe_public_payload(
        "ResearchSourceCollectionQualityGateReport.payload",
        payload,
        allow_json_containers=True,
    )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_for_collection(
    *,
    collection_id: str,
    claim_id: str,
    items: tuple[ResearchSourceCollectionItem, ...],
    generated_at: datetime,
    config: ResearchSourceCollectionQualityGateConfig,
) -> ResearchSourceCollectionQualityGateRow:
    sorted_items = tuple(
        sorted(
            items,
            key=lambda item: (
                item.source_id,
                item.source_family,
                item.verification_status,
            ),
        ),
    )
    latest = max(sorted_items, key=lambda item: item.collected_at)
    source_ids = tuple(sorted({item.source_id for item in sorted_items}))
    source_families = tuple(sorted({item.source_family for item in sorted_items}))
    source_count = len(source_ids)
    source_family_count = len(source_families)
    counterevidence_checked_count = sum(
        1 for item in sorted_items if item.counterevidence_checked
    )
    stale_source_count = sum(
        1
        for item in sorted_items
        if _age_seconds(generated_at, item.collected_at) >= config.stale_age_seconds
    )
    unverified_source_count = sum(
        1 for item in sorted_items if item.verification_status == "unverified"
    )
    verifiable_source_count = sum(
        1 for item in sorted_items if item.verification_status != "unverified"
    )
    independence_score = _independence_score(
        source_count=source_count,
        source_family_count=source_family_count,
        config=config,
    )
    timeliness_score = _average_decimal(
        tuple(
            _timeliness_score(
                _age_seconds(generated_at, item.collected_at),
                fresh_age_seconds=config.fresh_age_seconds,
                stale_age_seconds=config.stale_age_seconds,
            )
            for item in sorted_items
        ),
    )
    verifiability_score = _average_decimal(
        tuple(VERIFICATION_SCORES[item.verification_status] for item in sorted_items),
    )
    counterevidence_score = _counterevidence_score(
        counterevidence_checked_count=counterevidence_checked_count,
        config=config,
    )
    quality_score = _quality_score(
        independence_score=independence_score,
        timeliness_score=timeliness_score,
        verifiability_score=verifiability_score,
        counterevidence_score=counterevidence_score,
        config=config,
    )
    gate_status = _row_status(
        quality_score=quality_score,
        source_count=source_count,
        source_family_count=source_family_count,
        verifiable_source_count=verifiable_source_count,
        counterevidence_checked_count=counterevidence_checked_count,
        config=config,
    )

    return ResearchSourceCollectionQualityGateRow(
        collection_id=collection_id,
        claim_id=claim_id,
        source_count=_decimal_count(source_count),
        source_family_count=_decimal_count(source_family_count),
        verifiable_source_count=_decimal_count(verifiable_source_count),
        counterevidence_checked_count=_decimal_count(counterevidence_checked_count),
        stale_source_count=_decimal_count(stale_source_count),
        unverified_source_count=_decimal_count(unverified_source_count),
        latest_collected_at=latest.collected_at,
        latest_source_age_seconds=_age_seconds(generated_at, latest.collected_at),
        independence_score=independence_score,
        timeliness_score=timeliness_score,
        verifiability_score=verifiability_score,
        counterevidence_score=counterevidence_score,
        quality_score=quality_score,
        gate_status=gate_status,
        source_ids=source_ids,
        source_families=source_families,
        reason_codes=_row_reason_codes(
            gate_status=gate_status,
            source_count=source_count,
            source_family_count=source_family_count,
            verifiable_source_count=verifiable_source_count,
            counterevidence_checked_count=counterevidence_checked_count,
            stale_source_count=stale_source_count,
            unverified_source_count=unverified_source_count,
            source_reason_codes=tuple(
                reason_code for item in sorted_items for reason_code in item.reason_codes
            ),
            config=config,
        ),
    )


def _normalize_source_items(
    source_items: Iterable[object],
) -> tuple[ResearchSourceCollectionItem, ...]:
    if isinstance(source_items, (str, bytes)):
        raise ValueError("source_items must be an iterable")
    try:
        values = tuple(source_items)
    except TypeError as exc:
        raise ValueError("source_items must be an iterable") from exc
    return tuple(_coerce_source_item(value) for value in values)


def _coerce_source_item(value: object) -> ResearchSourceCollectionItem:
    if type(value) is ResearchSourceCollectionItem:
        _require_hard_flags("source item", value)
        return value
    _require_hard_flags("source item", value)
    return ResearchSourceCollectionItem(
        collection_id=_field_value(value, "collection_id"),
        claim_id=_field_value(value, "claim_id"),
        source_id=_field_value(value, "source_id"),
        source_family=_field_value(value, "source_family"),
        source_kind=_field_value(value, "source_kind"),
        stance=_field_value(value, "stance"),
        collected_at=_field_value(value, "collected_at"),
        verification_status=_field_value(value, "verification_status"),
        counterevidence_checked=_field_value(value, "counterevidence_checked"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _normalize_public_payload(
    public_payload: Iterable[object],
) -> tuple[ResearchSourceCollectionQualityPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)):
        raise ValueError("public_payload must be an iterable")
    try:
        values = tuple(public_payload)
    except TypeError as exc:
        raise ValueError("public_payload must be an iterable") from exc
    items = tuple(_coerce_public_payload_item(value) for value in values)
    return tuple(sorted(items, key=lambda item: item.payload_id))


def _coerce_public_payload_item(
    value: object,
) -> ResearchSourceCollectionQualityPublicPayloadItem:
    if type(value) is ResearchSourceCollectionQualityPublicPayloadItem:
        _require_hard_flags("public payload item", value)
        return value
    _require_hard_flags("public payload item", value)
    return ResearchSourceCollectionQualityPublicPayloadItem(
        payload_id=_field_value(value, "payload_id"),
        collection_id=_field_value(value, "collection_id"),
        claim_id=_field_value(value, "claim_id"),
        public_summary=_field_value(value, "public_summary"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _independence_score(
    *,
    source_count: int,
    source_family_count: int,
    config: ResearchSourceCollectionQualityGateConfig,
) -> Decimal:
    source_ratio = min(ONE, Decimal(source_count) / config.min_source_count)
    family_ratio = min(ONE, Decimal(source_family_count) / config.min_source_family_count)
    return _quantize((source_ratio + family_ratio) / Decimal("2"))


def _timeliness_score(
    age_seconds: Decimal,
    *,
    fresh_age_seconds: Decimal,
    stale_age_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_age_seconds:
        return ONE
    if age_seconds >= stale_age_seconds:
        return ZERO
    return _quantize(ONE - (age_seconds / stale_age_seconds))


def _counterevidence_score(
    *,
    counterevidence_checked_count: int,
    config: ResearchSourceCollectionQualityGateConfig,
) -> Decimal:
    return _quantize(
        min(
            ONE,
            Decimal(counterevidence_checked_count)
            / config.min_counterevidence_check_count,
        ),
    )


def _quality_score(
    *,
    independence_score: Decimal,
    timeliness_score: Decimal,
    verifiability_score: Decimal,
    counterevidence_score: Decimal,
    config: ResearchSourceCollectionQualityGateConfig,
) -> Decimal:
    return _quantize(
        (independence_score * config.independence_weight)
        + (timeliness_score * config.timeliness_weight)
        + (verifiability_score * config.verifiability_weight)
        + (counterevidence_score * config.counterevidence_weight),
    )


def _row_status(
    *,
    quality_score: Decimal,
    source_count: int,
    source_family_count: int,
    verifiable_source_count: int,
    counterevidence_checked_count: int,
    config: ResearchSourceCollectionQualityGateConfig,
) -> str:
    independence_blocked = (
        Decimal(source_count) < config.min_source_count
        or Decimal(source_family_count) < config.min_source_family_count
    )
    coverage_blocked = (
        verifiable_source_count == 0 or counterevidence_checked_count == 0
    )
    if (
        independence_blocked
        or coverage_blocked
        or quality_score < config.watch_quality_score
    ):
        return "blocked"
    if (
        quality_score < config.pass_quality_score
        or Decimal(counterevidence_checked_count)
        < config.min_counterevidence_check_count
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    gate_status: str,
    source_count: int,
    source_family_count: int,
    verifiable_source_count: int,
    counterevidence_checked_count: int,
    stale_source_count: int,
    unverified_source_count: int,
    source_reason_codes: tuple[str, ...],
    config: ResearchSourceCollectionQualityGateConfig,
) -> tuple[str, ...]:
    reason_codes = {f"research_source_collection_quality_{gate_status}"}
    source_threshold_met = Decimal(source_count) >= config.min_source_count
    family_threshold_met = Decimal(source_family_count) >= config.min_source_family_count
    counter_threshold_met = (
        Decimal(counterevidence_checked_count)
        >= config.min_counterevidence_check_count
    )
    reason_codes.add(
        "independent_sources_met"
        if source_threshold_met and family_threshold_met
        else "insufficient_source_independence",
    )
    reason_codes.add("fresh_collection" if not stale_source_count else "stale_collection")
    reason_codes.add(
        "verifiable_sources_present"
        if verifiable_source_count
        else "missing_verifiable_sources",
    )
    reason_codes.add(
        "unverified_sources_present"
        if unverified_source_count
        else "all_sources_verifiable",
    )
    reason_codes.add(
        "counterevidence_coverage_met"
        if counter_threshold_met
        else "missing_counterevidence_coverage",
    )
    for reason_code in source_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchSourceCollectionQualityGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_source_collection_results",)
    if any(row.gate_status == "blocked" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if any(row.gate_status == "watch" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    return ("research_source_collection_quality_pass",)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_source_collection_results",):
        return "blocked"
    if "research_source_collection_quality_blocked" in reason_codes:
        return "blocked"
    if "research_source_collection_quality_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchSourceCollectionQualityGateRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceCollectionQualityGateReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceCollectionQualityGateReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceCollectionQualityGateReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_quality_score(
    rows: tuple[ResearchSourceCollectionQualityGateRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _average_decimal(tuple(row.quality_score for row in rows))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _age_seconds(generated_at: datetime, collected_at: datetime) -> Decimal:
    delta = generated_at - collected_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _status_count(
    rows: tuple[ResearchSourceCollectionQualityGateRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.gate_status == status)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourceCollectionQualityGateRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceCollectionQualityGateRow:
            raise ValueError(
                "rows must contain ResearchSourceCollectionQualityGateRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.collection_id, row.claim_id)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by collection_id and claim_id")
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchSourceCollectionQualityGateReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchSourceCollectionQualityGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceCollectionQualityGateReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchSourceCollectionQualityGateRow) -> None:
    if row.source_count <= ZERO:
        raise ValueError("source_count must be positive")
    if row.source_family_count > row.source_count:
        raise ValueError("source_family_count must not exceed source_count")
    if row.verifiable_source_count > row.source_count:
        raise ValueError("verifiable_source_count must not exceed source_count")
    if row.counterevidence_checked_count > row.source_count:
        raise ValueError("counterevidence_checked_count must not exceed source_count")
    if row.stale_source_count > row.source_count:
        raise ValueError("stale_source_count must not exceed source_count")
    if row.unverified_source_count > row.source_count:
        raise ValueError("unverified_source_count must not exceed source_count")
    if row.source_count != _decimal_count(len(row.source_ids)):
        raise ValueError("source_ids must match source_count")
    if row.source_family_count != _decimal_count(len(row.source_families)):
        raise ValueError("source_families must match source_family_count")


def _validate_report_consistency(
    report: ResearchSourceCollectionQualityGateReport,
) -> None:
    if report.collection_count != _decimal_count(len(report.rows)):
        raise ValueError("collection_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_quality_score != _average_quality_score(report.rows):
        raise ValueError("average_quality_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.gate_status != _summary_status(report.reason_codes):
        raise ValueError("gate_status must match reason_codes")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload Decimal values must be exact Decimal")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("payload datetime values must be exact datetime")
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")
    if "://" in value or "?" in value:
        raise ValueError(f"{field_name} must be safe for public payloads")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} must be safe for public payloads")


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _normalize_public_string_tuple(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_string(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


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
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            ResearchSourceCollectionQualityGateConfig,
            ResearchSourceCollectionItem,
            ResearchSourceCollectionQualityPublicPayloadItem,
            ResearchSourceCollectionQualityGateRow,
            ResearchSourceCollectionQualityGateReasonCodeCount,
            ResearchSourceCollectionQualityGateReport,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{current_path} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{key} has unsafe public field")
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        _require_public_string(current_path, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    unsafe_fragments = (
        "credential",
        "password",
        "secret",
        "token",
        "private",
        "wallet",
        "session",
        "cookie",
        "endpoint",
        "url",
        "uri",
        "raw",
        "prompt",
    )
    return any(fragment in lowered for fragment in unsafe_fragments)
