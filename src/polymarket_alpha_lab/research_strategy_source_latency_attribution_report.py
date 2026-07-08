"""Pure report-only source latency attribution report."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_SOURCE_LATENCY_ATTRIBUTION_REPORT_CONFIG_VERSION = (
    "research-strategy-source-latency-attribution-report-v0"
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SOURCE_LATENCY_ATTRIBUTION_REPORT_CONFIG_VERSION",
    "ResearchStrategySourceLatencyAttributionConfig",
    "ResearchStrategySourceLatencyAttributionInput",
    "ResearchStrategySourceLatencyAttributionReasonCodeCount",
    "ResearchStrategySourceLatencyAttributionReport",
    "ResearchStrategySourceLatencyAttributionRow",
    "build_research_strategy_source_latency_attribution_report",
    "research_strategy_source_latency_attribution_digest",
    "research_strategy_source_latency_attribution_digest_payload",
    "research_strategy_source_latency_attribution_report_payload",
)


PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
PUBLIC_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)
STATUS_SEVERITY = {
    BLOCK_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}
DRIVER_NAMES = (
    "retrieval",
    "parsing",
    "corroboration",
    "domain_handoff",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FOUR = Decimal("4.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

MISSING_INPUTS_REASON = "source_latency_attribution_missing_inputs"
REASON_CODE_SEQUENCE = (
    MISSING_INPUTS_REASON,
    "source_latency_attribution_block",
    "source_latency_attribution_watch",
    "source_latency_attribution_pass",
    "retrieval_delay_block",
    "retrieval_delay_watch",
    "parsing_delay_block",
    "parsing_delay_watch",
    "corroboration_delay_block",
    "corroboration_delay_watch",
    "domain_handoff_delay_block",
    "domain_handoff_delay_watch",
    "latency_pressure_block",
    "latency_pressure_watch",
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "can" "didate",
    "mar" "ket",
    "sl" "ug",
    "ques" "tion",
    "so" "urce" "_" "text",
    "d" "sn",
    "ta" "ble",
    "to" "ken",
    "wal" "let",
    "or" "der",
    "tra" "de",
    "b" "uy",
    "s" "ell",
    "reco" "mmend",
    "siz" "ing",
    "data" "base",
    "net" "work",
    "au" "th",
    "li" "ve",
)

PUBLIC_ROW_FIELDS_WITHOUT_DIGEST = (
    "rank",
    "lane_label",
    "sample_count",
    "average_retrieval_delay_seconds",
    "average_parsing_delay_seconds",
    "average_corroboration_delay_seconds",
    "average_domain_handoff_delay_seconds",
    "total_average_latency_seconds",
    "retrieval_latency_share",
    "parsing_latency_share",
    "corroboration_latency_share",
    "domain_handoff_latency_share",
    "dominant_latency_driver",
    "dominant_driver_share",
    "latency_pressure_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_ROW_FIELDS = (*PUBLIC_ROW_FIELDS_WITHOUT_DIGEST, "public_payload_digest")
PUBLIC_REASON_COUNT_FIELDS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "status",
    "attribution_count",
    "lane_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_retrieval_delay_seconds",
    "average_parsing_delay_seconds",
    "average_corroboration_delay_seconds",
    "average_domain_handoff_delay_seconds",
    "average_total_latency_seconds",
    "dominant_latency_driver",
    "dominant_driver_average_delay_seconds",
    "max_latency_pressure_score",
    "rows",
    "reason_code_counts",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_FIELDS = (*PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST, "public_payload_digest")


@dataclass(frozen=True)
class ResearchStrategySourceLatencyAttributionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_SOURCE_LATENCY_ATTRIBUTION_REPORT_CONFIG_VERSION
    )
    retrieval_delay_watch_seconds: Decimal = Decimal("600.000000")
    retrieval_delay_block_seconds: Decimal = Decimal("1800.000000")
    parsing_delay_watch_seconds: Decimal = Decimal("300.000000")
    parsing_delay_block_seconds: Decimal = Decimal("900.000000")
    corroboration_delay_watch_seconds: Decimal = Decimal("1200.000000")
    corroboration_delay_block_seconds: Decimal = Decimal("3600.000000")
    domain_handoff_delay_watch_seconds: Decimal = Decimal("600.000000")
    domain_handoff_delay_block_seconds: Decimal = Decimal("2400.000000")
    latency_pressure_watch_threshold: Decimal = Decimal("0.250000")
    latency_pressure_block_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceLatencyAttributionConfig:
            raise TypeError(
                "ResearchStrategySourceLatencyAttributionConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySourceLatencyAttributionConfig,
            "config",
        )
        _require_supported_config_version(self.config_version)
        for field_name in (
            "retrieval_delay_watch_seconds",
            "retrieval_delay_block_seconds",
            "parsing_delay_watch_seconds",
            "parsing_delay_block_seconds",
            "corroboration_delay_watch_seconds",
            "corroboration_delay_block_seconds",
            "domain_handoff_delay_watch_seconds",
            "domain_handoff_delay_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latency_pressure_watch_threshold",
            "latency_pressure_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_less_than(
            "retrieval_delay_watch_seconds",
            self.retrieval_delay_watch_seconds,
            "retrieval_delay_block_seconds",
            self.retrieval_delay_block_seconds,
        )
        _require_less_than(
            "parsing_delay_watch_seconds",
            self.parsing_delay_watch_seconds,
            "parsing_delay_block_seconds",
            self.parsing_delay_block_seconds,
        )
        _require_less_than(
            "corroboration_delay_watch_seconds",
            self.corroboration_delay_watch_seconds,
            "corroboration_delay_block_seconds",
            self.corroboration_delay_block_seconds,
        )
        _require_less_than(
            "domain_handoff_delay_watch_seconds",
            self.domain_handoff_delay_watch_seconds,
            "domain_handoff_delay_block_seconds",
            self.domain_handoff_delay_block_seconds,
        )
        _require_less_than(
            "latency_pressure_watch_threshold",
            self.latency_pressure_watch_threshold,
            "latency_pressure_block_threshold",
            self.latency_pressure_block_threshold,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategySourceLatencyAttributionInput:
    evidence_ref: str
    lane_label: str
    retrieval_delay_seconds: Decimal
    parsing_delay_seconds: Decimal
    corroboration_delay_seconds: Decimal
    domain_handoff_delay_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceLatencyAttributionInput:
            raise TypeError(
                "ResearchStrategySourceLatencyAttributionInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySourceLatencyAttributionInput,
            "input",
        )
        _require_private_ref("evidence_ref", self.evidence_ref)
        object.__setattr__(
            self,
            "lane_label",
            _require_public_label("lane_label", self.lane_label),
        )
        for field_name in (
            "retrieval_delay_seconds",
            "parsing_delay_seconds",
            "corroboration_delay_seconds",
            "domain_handoff_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategySourceLatencyAttributionRow:
    rank: Decimal
    lane_label: str
    sample_count: Decimal
    average_retrieval_delay_seconds: Decimal
    average_parsing_delay_seconds: Decimal
    average_corroboration_delay_seconds: Decimal
    average_domain_handoff_delay_seconds: Decimal
    total_average_latency_seconds: Decimal
    retrieval_latency_share: Decimal
    parsing_latency_share: Decimal
    corroboration_latency_share: Decimal
    domain_handoff_latency_share: Decimal
    dominant_latency_driver: str
    dominant_driver_share: Decimal
    latency_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceLatencyAttributionRow:
            raise TypeError(
                "ResearchStrategySourceLatencyAttributionRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceLatencyAttributionRow, "row")
        object.__setattr__(self, "rank", _require_positive_whole_decimal("rank", self.rank))
        object.__setattr__(
            self,
            "lane_label",
            _require_public_label("lane_label", self.lane_label),
        )
        object.__setattr__(
            self,
            "sample_count",
            _require_positive_whole_decimal("sample_count", self.sample_count),
        )
        for field_name in (
            "average_retrieval_delay_seconds",
            "average_parsing_delay_seconds",
            "average_corroboration_delay_seconds",
            "average_domain_handoff_delay_seconds",
            "total_average_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "retrieval_latency_share",
            "parsing_latency_share",
            "corroboration_latency_share",
            "domain_handoff_latency_share",
            "dominant_driver_share",
            "latency_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "dominant_latency_driver",
            _require_driver_name(self.dominant_latency_driver),
        )
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        expected_digest = _public_digest_from_values(_row_values_without_digest(self))
        if self.public_payload_digest:
            _require_digest(self.public_payload_digest)
            if self.public_payload_digest != expected_digest:
                raise ValueError("public_payload_digest must match row payload")
        else:
            object.__setattr__(self, "public_payload_digest", expected_digest)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategySourceLatencyAttributionReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceLatencyAttributionReasonCodeCount:
            raise TypeError(
                "ResearchStrategySourceLatencyAttributionReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySourceLatencyAttributionReasonCodeCount,
            "reason_count",
        )
        object.__setattr__(self, "reason_code", _require_reason_code(self.reason_code))
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_count", self)


@dataclass(frozen=True)
class ResearchStrategySourceLatencyAttributionReport:
    generated_at: datetime
    config_version: str
    status: str
    attribution_count: Decimal
    lane_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_retrieval_delay_seconds: Decimal
    average_parsing_delay_seconds: Decimal
    average_corroboration_delay_seconds: Decimal
    average_domain_handoff_delay_seconds: Decimal
    average_total_latency_seconds: Decimal
    dominant_latency_driver: str
    dominant_driver_average_delay_seconds: Decimal
    max_latency_pressure_score: Decimal
    rows: tuple[ResearchStrategySourceLatencyAttributionRow, ...]
    reason_code_counts: tuple[
        ResearchStrategySourceLatencyAttributionReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceLatencyAttributionReport:
            raise TypeError(
                "ResearchStrategySourceLatencyAttributionReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceLatencyAttributionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_supported_config_version(self.config_version)
        _require_status(self.status)
        for field_name in (
            "attribution_count",
            "lane_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_retrieval_delay_seconds",
            "average_parsing_delay_seconds",
            "average_corroboration_delay_seconds",
            "average_domain_handoff_delay_seconds",
            "average_total_latency_seconds",
            "dominant_driver_average_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_latency_pressure_score",
            _require_probability_decimal(
                "max_latency_pressure_score",
                self.max_latency_pressure_score,
            ),
        )
        object.__setattr__(
            self,
            "dominant_latency_driver",
            _require_driver_name(self.dominant_latency_driver),
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        expected_digest = _public_digest_from_values(_report_values_without_digest(self))
        if self.public_payload_digest:
            _require_digest(self.public_payload_digest)
            if self.public_payload_digest != expected_digest:
                raise ValueError("public_payload_digest must match report payload")
        else:
            object.__setattr__(self, "public_payload_digest", expected_digest)
        _validate_report_consistency(self)


def build_research_strategy_source_latency_attribution_report(
    inputs: Iterable[ResearchStrategySourceLatencyAttributionInput],
    *,
    generated_at: datetime,
    config: ResearchStrategySourceLatencyAttributionConfig | None = None,
) -> ResearchStrategySourceLatencyAttributionReport:
    if config is None:
        config = ResearchStrategySourceLatencyAttributionConfig()
    _require_exact_type(config, ResearchStrategySourceLatencyAttributionConfig, "config")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_inputs(inputs)
    rows = _rank_rows(
        tuple(
            _row_from_group(lane_label, group_items, config=config)
            for lane_label, group_items in _group_inputs(items)
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "attribution_count": _count(len(items)),
        "lane_count": _count(len(rows)),
        "pass_count": _status_count(rows, PASS_STATUS),
        "watch_count": _status_count(rows, WATCH_STATUS),
        "block_count": _status_count(rows, BLOCK_STATUS),
        "average_retrieval_delay_seconds": _weighted_row_average(
            rows,
            "average_retrieval_delay_seconds",
        ),
        "average_parsing_delay_seconds": _weighted_row_average(
            rows,
            "average_parsing_delay_seconds",
        ),
        "average_corroboration_delay_seconds": _weighted_row_average(
            rows,
            "average_corroboration_delay_seconds",
        ),
        "average_domain_handoff_delay_seconds": _weighted_row_average(
            rows,
            "average_domain_handoff_delay_seconds",
        ),
        "average_total_latency_seconds": _weighted_row_average(
            rows,
            "total_average_latency_seconds",
        ),
        "dominant_latency_driver": _report_dominant_driver(rows)[0],
        "dominant_driver_average_delay_seconds": _report_dominant_driver(rows)[1],
        "max_latency_pressure_score": max(
            (row.latency_pressure_score for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategySourceLatencyAttributionReport(**values)


def research_strategy_source_latency_attribution_report_payload(
    report: ResearchStrategySourceLatencyAttributionReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchStrategySourceLatencyAttributionReport:
        _require_hard_flags("report", report)
        if report.public_payload_digest != research_strategy_source_latency_attribution_digest(
            report,
        ):
            raise ValueError("public_payload_digest must match report payload")
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _validate_public_report_payload(report)
        return dict(report)
    raise ValueError("report must be ResearchStrategySourceLatencyAttributionReport")


def research_strategy_source_latency_attribution_digest_payload(
    report: ResearchStrategySourceLatencyAttributionReport,
) -> dict[str, object]:
    if type(report) is not ResearchStrategySourceLatencyAttributionReport:
        raise ValueError("report must be ResearchStrategySourceLatencyAttributionReport")
    payload = _json_ready(_report_values_without_digest(report))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    payload["public_payload_digest"] = None
    return payload


def research_strategy_source_latency_attribution_digest(
    report: ResearchStrategySourceLatencyAttributionReport,
) -> str:
    if type(report) is not ResearchStrategySourceLatencyAttributionReport:
        raise ValueError("report must be ResearchStrategySourceLatencyAttributionReport")
    return _public_digest_from_values(_report_values_without_digest(report))


def _row_from_group(
    lane_label: str,
    items: tuple[ResearchStrategySourceLatencyAttributionInput, ...],
    *,
    config: ResearchStrategySourceLatencyAttributionConfig,
) -> ResearchStrategySourceLatencyAttributionRow:
    sample_count = _count(len(items))
    retrieval = _average(tuple(item.retrieval_delay_seconds for item in items))
    parsing = _average(tuple(item.parsing_delay_seconds for item in items))
    corroboration = _average(tuple(item.corroboration_delay_seconds for item in items))
    handoff = _average(tuple(item.domain_handoff_delay_seconds for item in items))
    total = _sum_decimals((retrieval, parsing, corroboration, handoff))
    shares = (
        _share(retrieval, total),
        _share(parsing, total),
        _share(corroboration, total),
        _share(handoff, total),
    )
    dominant_driver, dominant_share = _dominant_from_named_values(
        tuple(zip(DRIVER_NAMES, shares, strict=True)),
    )
    pressure_score = _average(
        (
            _pressure(retrieval, config.retrieval_delay_block_seconds),
            _pressure(parsing, config.parsing_delay_block_seconds),
            _pressure(corroboration, config.corroboration_delay_block_seconds),
            _pressure(handoff, config.domain_handoff_delay_block_seconds),
        ),
    )
    reason_codes = _row_reason_codes(
        retrieval=retrieval,
        parsing=parsing,
        corroboration=corroboration,
        handoff=handoff,
        pressure_score=pressure_score,
        config=config,
    )
    return ResearchStrategySourceLatencyAttributionRow(
        rank=ONE,
        lane_label=lane_label,
        sample_count=sample_count,
        average_retrieval_delay_seconds=retrieval,
        average_parsing_delay_seconds=parsing,
        average_corroboration_delay_seconds=corroboration,
        average_domain_handoff_delay_seconds=handoff,
        total_average_latency_seconds=total,
        retrieval_latency_share=shares[0],
        parsing_latency_share=shares[1],
        corroboration_latency_share=shares[2],
        domain_handoff_latency_share=shares[3],
        dominant_latency_driver=dominant_driver,
        dominant_driver_share=dominant_share,
        latency_pressure_score=pressure_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    retrieval: Decimal,
    parsing: Decimal,
    corroboration: Decimal,
    handoff: Decimal,
    pressure_score: Decimal,
    config: ResearchStrategySourceLatencyAttributionConfig,
) -> tuple[str, ...]:
    detail_codes: list[str] = []
    _append_delay_reason(
        detail_codes,
        value=retrieval,
        watch_value=config.retrieval_delay_watch_seconds,
        block_value=config.retrieval_delay_block_seconds,
        block_reason="retrieval_delay_block",
        watch_reason="retrieval_delay_watch",
    )
    _append_delay_reason(
        detail_codes,
        value=parsing,
        watch_value=config.parsing_delay_watch_seconds,
        block_value=config.parsing_delay_block_seconds,
        block_reason="parsing_delay_block",
        watch_reason="parsing_delay_watch",
    )
    _append_delay_reason(
        detail_codes,
        value=corroboration,
        watch_value=config.corroboration_delay_watch_seconds,
        block_value=config.corroboration_delay_block_seconds,
        block_reason="corroboration_delay_block",
        watch_reason="corroboration_delay_watch",
    )
    _append_delay_reason(
        detail_codes,
        value=handoff,
        watch_value=config.domain_handoff_delay_watch_seconds,
        block_value=config.domain_handoff_delay_block_seconds,
        block_reason="domain_handoff_delay_block",
        watch_reason="domain_handoff_delay_watch",
    )
    if pressure_score >= config.latency_pressure_block_threshold:
        detail_codes.append("latency_pressure_block")
    elif pressure_score >= config.latency_pressure_watch_threshold:
        detail_codes.append("latency_pressure_watch")
    status = _status_from_reason_codes(tuple(detail_codes))
    return _normalize_reason_codes(
        "reason_codes",
        (f"source_latency_attribution_{status}", *detail_codes),
    )


def _append_delay_reason(
    reason_codes: list[str],
    *,
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    block_reason: str,
    watch_reason: str,
) -> None:
    if value >= block_value:
        reason_codes.append(block_reason)
    elif value >= watch_value:
        reason_codes.append(watch_reason)


def _rank_rows(
    rows: tuple[ResearchStrategySourceLatencyAttributionRow, ...],
) -> tuple[ResearchStrategySourceLatencyAttributionRow, ...]:
    ranked_rows: list[ResearchStrategySourceLatencyAttributionRow] = []
    for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1):
        ranked_rows.append(
            ResearchStrategySourceLatencyAttributionRow(
                rank=_count(index),
                lane_label=row.lane_label,
                sample_count=row.sample_count,
                average_retrieval_delay_seconds=row.average_retrieval_delay_seconds,
                average_parsing_delay_seconds=row.average_parsing_delay_seconds,
                average_corroboration_delay_seconds=(
                    row.average_corroboration_delay_seconds
                ),
                average_domain_handoff_delay_seconds=(
                    row.average_domain_handoff_delay_seconds
                ),
                total_average_latency_seconds=row.total_average_latency_seconds,
                retrieval_latency_share=row.retrieval_latency_share,
                parsing_latency_share=row.parsing_latency_share,
                corroboration_latency_share=row.corroboration_latency_share,
                domain_handoff_latency_share=row.domain_handoff_latency_share,
                dominant_latency_driver=row.dominant_latency_driver,
                dominant_driver_share=row.dominant_driver_share,
                latency_pressure_score=row.latency_pressure_score,
                status=row.status,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked_rows)


def _row_sort_key(
    row: ResearchStrategySourceLatencyAttributionRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_SEVERITY[row.status],
        -row.latency_pressure_score,
        -row.total_average_latency_seconds,
        row.lane_label,
    )


def _normalize_inputs(
    value: Iterable[ResearchStrategySourceLatencyAttributionInput],
) -> tuple[ResearchStrategySourceLatencyAttributionInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategySourceLatencyAttributionInput:
            raise ValueError("inputs must contain attribution input values")
        _require_hard_flags("input", row)
        if row.evidence_ref in seen:
            raise ValueError("evidence_ref values must be unique")
        seen.add(row.evidence_ref)
    return tuple(sorted(rows, key=lambda row: (row.lane_label, row.evidence_ref)))


def _group_inputs(
    rows: tuple[ResearchStrategySourceLatencyAttributionInput, ...],
) -> tuple[tuple[str, tuple[ResearchStrategySourceLatencyAttributionInput, ...]], ...]:
    grouped: dict[str, list[ResearchStrategySourceLatencyAttributionInput]] = {}
    for row in rows:
        if row.lane_label not in grouped:
            grouped[row.lane_label] = []
        grouped[row.lane_label].append(row)
    return tuple((label, tuple(grouped[label])) for label in sorted(grouped))


def _normalize_rows(
    value: Sequence[ResearchStrategySourceLatencyAttributionRow],
) -> tuple[ResearchStrategySourceLatencyAttributionRow, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("rows must be a sequence")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategySourceLatencyAttributionRow:
            raise ValueError("rows must contain attribution row values")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    if tuple(row.rank for row in rows) != tuple(
        _count(index) for index in range(1, len(rows) + 1)
    ):
        raise ValueError("rows must use sequential ranks")
    return rows


def _normalize_reason_code_counts(
    value: Sequence[ResearchStrategySourceLatencyAttributionReasonCodeCount],
) -> tuple[ResearchStrategySourceLatencyAttributionReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    rows = tuple(value)
    if rows != tuple(sorted(rows, key=lambda row: _reason_rank(row.reason_code))):
        raise ValueError("reason_code_counts must use deterministic sequence")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategySourceLatencyAttributionReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not repeat")
        seen.add(row.reason_code)
    return rows


def _reason_code_counts(
    rows: tuple[ResearchStrategySourceLatencyAttributionRow, ...],
) -> tuple[ResearchStrategySourceLatencyAttributionReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    if not rows:
        counts[MISSING_INPUTS_REASON] = 1
    else:
        for row in rows:
            for reason_code in row.reason_codes:
                counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchStrategySourceLatencyAttributionReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_reason_codes(
    field_name: str,
    value: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        reason_code = _require_reason_code(reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not repeat")
        seen.add(reason_code)
        normalized.append(reason_code)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    expected = tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen)
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return tuple(normalized)


def _report_reason_codes(
    rows: tuple[ResearchStrategySourceLatencyAttributionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (MISSING_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        for reason_code in row.reason_codes:
            seen.add(reason_code)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen),
    )


def _report_status(rows: tuple[ResearchStrategySourceLatencyAttributionRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[ResearchStrategySourceLatencyAttributionRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _weighted_row_average(
    rows: tuple[ResearchStrategySourceLatencyAttributionRow, ...],
    field_name: str,
) -> Decimal:
    total_count = _sum_decimals(tuple(row.sample_count for row in rows))
    if total_count == ZERO:
        return ZERO
    total = ZERO
    for row in rows:
        total = _quantize(total + (getattr(row, field_name) * row.sample_count))
    return _ratio_uncapped(total, total_count)


def _report_dominant_driver(
    rows: tuple[ResearchStrategySourceLatencyAttributionRow, ...],
) -> tuple[str, Decimal]:
    averages = (
        ("retrieval", _weighted_row_average(rows, "average_retrieval_delay_seconds")),
        ("parsing", _weighted_row_average(rows, "average_parsing_delay_seconds")),
        (
            "corroboration",
            _weighted_row_average(rows, "average_corroboration_delay_seconds"),
        ),
        (
            "domain_handoff",
            _weighted_row_average(rows, "average_domain_handoff_delay_seconds"),
        ),
    )
    name = averages[0][0]
    score = averages[0][1]
    for next_name, next_score in averages[1:]:
        if next_score > score:
            name = next_name
            score = next_score
    return name, score


def _validate_row_consistency(
    row: ResearchStrategySourceLatencyAttributionRow,
) -> None:
    expected_total = _sum_decimals(
        (
            row.average_retrieval_delay_seconds,
            row.average_parsing_delay_seconds,
            row.average_corroboration_delay_seconds,
            row.average_domain_handoff_delay_seconds,
        ),
    )
    if row.total_average_latency_seconds != expected_total:
        raise ValueError("total_average_latency_seconds must match row delays")
    expected_shares = (
        _share(row.average_retrieval_delay_seconds, row.total_average_latency_seconds),
        _share(row.average_parsing_delay_seconds, row.total_average_latency_seconds),
        _share(row.average_corroboration_delay_seconds, row.total_average_latency_seconds),
        _share(row.average_domain_handoff_delay_seconds, row.total_average_latency_seconds),
    )
    actual_shares = (
        row.retrieval_latency_share,
        row.parsing_latency_share,
        row.corroboration_latency_share,
        row.domain_handoff_latency_share,
    )
    if actual_shares != expected_shares:
        raise ValueError("latency shares must match row delays")
    expected_driver, expected_share = _dominant_from_named_values(
        tuple(zip(DRIVER_NAMES, expected_shares, strict=True)),
    )
    if row.dominant_latency_driver != expected_driver:
        raise ValueError("dominant_latency_driver must match latency shares")
    if row.dominant_driver_share != expected_share:
        raise ValueError("dominant_driver_share must match latency shares")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == PASS_STATUS and row.reason_codes != (
        "source_latency_attribution_pass",
    ):
        raise ValueError("pass rows must expose only pass reason code")


def _validate_report_consistency(
    report: ResearchStrategySourceLatencyAttributionReport,
) -> None:
    rows = report.rows
    if report.attribution_count != _sum_decimals(tuple(row.sample_count for row in rows)):
        raise ValueError("attribution_count must match rows")
    if report.lane_count != _count(len(rows)):
        raise ValueError("lane_count must match rows")
    if report.pass_count != _status_count(rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    for field_name in (
        "average_retrieval_delay_seconds",
        "average_parsing_delay_seconds",
        "average_corroboration_delay_seconds",
        "average_domain_handoff_delay_seconds",
    ):
        if getattr(report, field_name) != _weighted_row_average(rows, field_name):
            raise ValueError(f"{field_name} must match rows")
    if report.average_total_latency_seconds != _weighted_row_average(
        rows,
        "total_average_latency_seconds",
    ):
        raise ValueError("average_total_latency_seconds must match rows")
    expected_driver, expected_score = _report_dominant_driver(rows)
    if report.dominant_latency_driver != expected_driver:
        raise ValueError("dominant_latency_driver must match row averages")
    if report.dominant_driver_average_delay_seconds != expected_score:
        raise ValueError("dominant_driver_average_delay_seconds must match row averages")
    if report.max_latency_pressure_score != max(
        (row.latency_pressure_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_latency_pressure_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return BLOCK_STATUS
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _dominant_from_named_values(
    values: tuple[tuple[str, Decimal], ...],
) -> tuple[str, Decimal]:
    name = values[0][0]
    score = values[0][1]
    for next_name, next_score in values[1:]:
        if next_score > score:
            name = next_name
            score = next_score
    return name, score


def _pressure(value: Decimal, block_value: Decimal) -> Decimal:
    return _cap_probability(_ratio_uncapped(value, block_value))


def _share(value: Decimal, total: Decimal) -> Decimal:
    if total == ZERO:
        return ZERO
    return _cap_probability(_ratio_uncapped(value, total))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio_uncapped(_sum_decimals(values), Decimal(len(values)))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + _require_decimal("sum value", value))
    return total


def _ratio_uncapped(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _cap_probability(value: Decimal) -> Decimal:
    value = _quantize(value)
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _require_supported_config_version(value: object) -> str:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_STRATEGY_SOURCE_LATENCY_ATTRIBUTION_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported value")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    return value


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public aggregate label")
    return value


def _require_driver_name(value: object) -> str:
    if type(value) is not str or value not in DRIVER_NAMES:
        raise ValueError("dominant_latency_driver must be a supported latency driver")
    return value


def _require_reason_code(value: object) -> str:
    if type(value) is not str:
        raise ValueError("reason_code must be a string")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError("reason_code is not supported")
    return value


def _reason_rank(reason_code: str) -> int:
    return REASON_CODE_SEQUENCE.index(reason_code)


def _require_status(value: object) -> str:
    if type(value) is not str:
        raise ValueError("status must be a string")
    if value not in PUBLIC_STATUSES:
        raise ValueError("status must be pass, watch, or block")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_whole_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_less_than(
    left_name: str,
    left: Decimal,
    right_name: str,
    right: Decimal,
) -> None:
    if left >= right:
        raise ValueError(f"{left_name} must be less than {right_name}")


def _require_digest(value: object) -> str:
    if type(value) is not str:
        raise ValueError("public_payload_digest must be a string")
    if not DIGEST_RE.fullmatch(value):
        raise ValueError("public_payload_digest must be a SHA-256 hex digest")
    return value


def _row_values_without_digest(
    row: ResearchStrategySourceLatencyAttributionRow,
) -> dict[str, object]:
    values = asdict(row)
    values.pop("public_payload_digest", None)
    return values


def _report_values_without_digest(
    report: ResearchStrategySourceLatencyAttributionReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("public_payload_digest", None)
    for row in values["rows"]:
        if isinstance(row, dict):
            row.pop("public_payload_digest", None)
    return values


def _public_digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric values must be Decimal strings")
    raise ValueError(f"unsupported public payload value type: {type(value).__name__}")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            next_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), next_path)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            next_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_payload(label, item, next_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{current_path} numeric values must be Decimal strings")
    return


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


def _validate_public_report_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_REPORT_FIELDS, "report")
    _require_datetime_payload_string("generated_at", payload["generated_at"])
    _require_supported_config_version(payload["config_version"])
    _require_status(payload["status"])
    for field_name in (
        "attribution_count",
        "lane_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    for field_name in (
        "average_retrieval_delay_seconds",
        "average_parsing_delay_seconds",
        "average_corroboration_delay_seconds",
        "average_domain_handoff_delay_seconds",
        "average_total_latency_seconds",
        "dominant_driver_average_delay_seconds",
    ):
        _require_decimal_payload_string(field_name, payload[field_name])
    _require_driver_name(payload["dominant_latency_driver"])
    _require_decimal_payload_string(
        "max_latency_pressure_score",
        payload["max_latency_pressure_score"],
        probability=True,
    )
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain row payload dictionaries")
        _validate_public_row_payload(row)
    reason_counts = payload["reason_code_counts"]
    if type(reason_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for reason_count in reason_counts:
        if type(reason_count) is not dict:
            raise ValueError("reason_code_counts must contain payload dictionaries")
        _validate_public_reason_count_payload(reason_count)
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    _require_hard_flags("payload", _DictFlags(payload))
    _require_digest(payload["public_payload_digest"])
    values = dict(payload)
    values.pop("public_payload_digest", None)
    values["rows"] = [
        _public_row_values_without_digest(row)
        for row in payload["rows"]
        if type(row) is dict
    ]
    if payload["public_payload_digest"] != _public_digest_from_values(values):
        raise ValueError("public_payload_digest must match payload")


def _validate_public_row_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_ROW_FIELDS, "row")
    _require_decimal_payload_string("rank", payload["rank"], whole=True)
    _require_public_label("lane_label", payload["lane_label"])
    _require_decimal_payload_string("sample_count", payload["sample_count"], whole=True)
    for field_name in (
        "average_retrieval_delay_seconds",
        "average_parsing_delay_seconds",
        "average_corroboration_delay_seconds",
        "average_domain_handoff_delay_seconds",
        "total_average_latency_seconds",
    ):
        _require_decimal_payload_string(field_name, payload[field_name])
    for field_name in (
        "retrieval_latency_share",
        "parsing_latency_share",
        "corroboration_latency_share",
        "domain_handoff_latency_share",
        "dominant_driver_share",
        "latency_pressure_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], probability=True)
    _require_driver_name(payload["dominant_latency_driver"])
    _require_status(payload["status"])
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    _require_hard_flags("row payload", _DictFlags(payload))
    _require_digest(payload["public_payload_digest"])
    values = dict(payload)
    values.pop("public_payload_digest", None)
    if payload["public_payload_digest"] != _public_digest_from_values(values):
        raise ValueError("public_payload_digest must match row payload")


def _public_row_values_without_digest(payload: dict[str, object]) -> dict[str, object]:
    values = dict(payload)
    values.pop("public_payload_digest", None)
    return values


def _validate_public_reason_count_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_REASON_COUNT_FIELDS, "reason_count")
    _require_reason_code(payload["reason_code"])
    _require_decimal_payload_string("count", payload["count"], whole=True)
    _require_hard_flags("reason_count payload", _DictFlags(payload))


def _require_exact_payload_fields(
    payload: dict[str, object],
    field_names: tuple[str, ...],
    label: str,
) -> None:
    missing = [field_name for field_name in field_names if field_name not in payload]
    if missing:
        raise ValueError(f"{missing[0]} is required")
    extra = sorted(set(payload) - set(field_names))
    if extra:
        raise ValueError(f"unexpected {label} payload field: {extra[0]}")


def _normalize_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    reason_codes: list[str] = []
    seen: set[str] = set()
    for reason_code in value:
        reason_code = _require_reason_code(reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not repeat")
        seen.add(reason_code)
        reason_codes.append(reason_code)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    expected = tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen)
    if tuple(reason_codes) != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return tuple(reason_codes)


def _require_datetime_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    probability: bool = False,
    whole: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(parsed)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if probability and normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    if whole and normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal string")
    return normalized


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")
