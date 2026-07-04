"""Pure Phase 1 refinery unplanned flare / outage risk digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_ENERGY_REFINERY_UNPLANNED_FLARE_DIGEST_CONFIG_VERSION = (
    "market-research-energy-refinery-unplanned-flare-digest-v0"
)

INPUT_REASONS = (
    "refinery_unplanned_flare_input_observed",
    "refinery_unplanned_flare_source_gap",
    "refinery_unplanned_flare_revision",
)
ROW_REASONS = (
    "refinery_unplanned_flare_source_gap",
    "refinery_unplanned_flare_refinery_clear",
    "refinery_unplanned_flare_refinery_watch",
    "refinery_unplanned_flare_refinery_blocked",
    "refinery_unplanned_flare_outage_watch",
    "refinery_unplanned_flare_outage_blocked",
    "refinery_unplanned_flare_revision_present",
)
REPORT_REASONS = (
    "refinery_unplanned_flare_digest_empty",
    "refinery_unplanned_flare_clear",
    "refinery_unplanned_flare_source_gap_present",
    "refinery_unplanned_flare_watch_present",
    "refinery_unplanned_flare_blocked_present",
    "refinery_unplanned_flare_outage_watch_present",
    "refinery_unplanned_flare_outage_blocked_present",
    "refinery_unplanned_flare_revision_present",
)
ROW_STATUSES = ("clear", "watch", "blocked")
DIGEST_STATUSES = ("empty", "clear", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class EnergyRefineryUnplannedFlareDigestConfig:
    config_version: str = (
        DEFAULT_ENERGY_REFINERY_UNPLANNED_FLARE_DIGEST_CONFIG_VERSION
    )
    watch_flare_event_ratio: Decimal = Decimal("0.200000")
    blocked_flare_event_ratio: Decimal = Decimal("0.400000")
    watch_outage_capacity_ratio: Decimal = Decimal("0.050000")
    blocked_outage_capacity_ratio: Decimal = Decimal("0.100000")
    min_sample_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_ENERGY_REFINERY_UNPLANNED_FLARE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "watch_flare_event_ratio",
            "blocked_flare_event_ratio",
            "watch_outage_capacity_ratio",
            "blocked_outage_capacity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_ratio(field_name, getattr(self, field_name)),
            )
        if self.blocked_flare_event_ratio < self.watch_flare_event_ratio:
            raise ValueError(
                "blocked_flare_event_ratio must be at least watch_flare_event_ratio"
            )
        if self.blocked_outage_capacity_ratio < self.watch_outage_capacity_ratio:
            raise ValueError(
                "blocked_outage_capacity_ratio must be at least "
                "watch_outage_capacity_ratio"
            )
        object.__setattr__(
            self,
            "min_sample_count",
            _require_positive_decimal("min_sample_count", self.min_sample_count),
        )
        _require_hard_flags("refinery unplanned flare config", self)


@dataclass(frozen=True)
class EnergyRefineryUnplannedFlareInput:
    source_id: str
    refinery_id: str
    market_id: str
    region_id: str
    unplanned_flare_event_count: Decimal
    sample_count: Decimal
    offline_capacity_bpd: Decimal
    nameplate_capacity_bpd: Decimal
    expected_offline_capacity_bpd: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("source_id", "refinery_id", "market_id", "region_id"):
            object.__setattr__(
                self,
                field_name,
                _require_text(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unplanned_flare_event_count",
            "sample_count",
            "offline_capacity_bpd",
            "nameplate_capacity_bpd",
            "expected_offline_capacity_bpd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.unplanned_flare_event_count > self.sample_count:
            raise ValueError(
                "unplanned_flare_event_count must not exceed sample_count"
            )
        if self.offline_capacity_bpd > self.nameplate_capacity_bpd:
            raise ValueError(
                "offline_capacity_bpd must not exceed nameplate_capacity_bpd"
            )
        if self.expected_offline_capacity_bpd > self.nameplate_capacity_bpd:
            raise ValueError(
                "expected_offline_capacity_bpd must not exceed "
                "nameplate_capacity_bpd"
            )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons("reason_codes", self.reason_codes, INPUT_REASONS),
        )
        _require_hard_flags("refinery unplanned flare input", self)


@dataclass(frozen=True)
class EnergyRefineryUnplannedFlareReasonCodeCount:
    reason_code: str
    refinery_count: Decimal
    refinery_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, REPORT_REASONS),
        )
        object.__setattr__(
            self,
            "refinery_count",
            _require_nonnegative_decimal("refinery_count", self.refinery_count),
        )
        object.__setattr__(
            self,
            "refinery_ratio",
            _require_ratio("refinery_ratio", self.refinery_ratio),
        )
        _require_hard_flags("refinery unplanned flare reason count", self)


@dataclass(frozen=True)
class EnergyRefineryUnplannedFlareRefineryRow:
    refinery_id: str
    region_ids: tuple[str, ...]
    market_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    unplanned_flare_event_count: Decimal
    sample_count: Decimal
    flare_event_ratio: Decimal
    offline_capacity_bpd: Decimal
    nameplate_capacity_bpd: Decimal
    expected_offline_capacity_bpd: Decimal
    outage_capacity_ratio: Decimal
    expected_outage_capacity_ratio: Decimal
    outage_surprise_ratio: Decimal
    source_count: Decimal
    latest_observed_at: datetime
    risk_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "refinery_id",
            _require_text("refinery_id", self.refinery_id),
        )
        for field_name in ("region_ids", "market_ids", "source_ids"):
            object.__setattr__(
                self,
                field_name,
                _normalize_text_tuple(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unplanned_flare_event_count",
            "sample_count",
            "flare_event_ratio",
            "offline_capacity_bpd",
            "nameplate_capacity_bpd",
            "expected_offline_capacity_bpd",
            "outage_capacity_ratio",
            "expected_outage_capacity_ratio",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "outage_surprise_ratio",
            _require_signed_ratio(
                "outage_surprise_ratio",
                self.outage_surprise_ratio,
            ),
        )
        _require_ratio("flare_event_ratio", self.flare_event_ratio)
        _require_ratio("outage_capacity_ratio", self.outage_capacity_ratio)
        _require_ratio(
            "expected_outage_capacity_ratio",
            self.expected_outage_capacity_ratio,
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "risk_status",
            _require_member("risk_status", self.risk_status, ROW_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons("reason_codes", self.reason_codes, ROW_REASONS),
        )
        _validate_refinery_row(self)
        _require_hard_flags("refinery unplanned flare row", self)


@dataclass(frozen=True)
class EnergyRefineryUnplannedFlareDigest:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    refinery_count: Decimal
    source_count: Decimal
    total_unplanned_flare_event_count: Decimal
    total_sample_count: Decimal
    total_offline_capacity_bpd: Decimal
    total_nameplate_capacity_bpd: Decimal
    total_expected_offline_capacity_bpd: Decimal
    max_flare_event_ratio: Decimal
    max_outage_capacity_ratio: Decimal
    weighted_flare_event_ratio: Decimal
    weighted_outage_capacity_ratio: Decimal
    watch_refinery_count: Decimal
    blocked_refinery_count: Decimal
    rows: tuple[EnergyRefineryUnplannedFlareRefineryRow, ...]
    reason_code_counts: tuple[EnergyRefineryUnplannedFlareReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_ENERGY_REFINERY_UNPLANNED_FLARE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "digest_status",
            _require_member("digest_status", self.digest_status, DIGEST_STATUSES),
        )
        object.__setattr__(
            self,
            "recommended_next_step",
            _require_text("recommended_next_step", self.recommended_next_step),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons("reason_codes", self.reason_codes, REPORT_REASONS),
        )
        for field_name in (
            "refinery_count",
            "source_count",
            "total_unplanned_flare_event_count",
            "total_sample_count",
            "total_offline_capacity_bpd",
            "total_nameplate_capacity_bpd",
            "total_expected_offline_capacity_bpd",
            "max_flare_event_ratio",
            "max_outage_capacity_ratio",
            "weighted_flare_event_ratio",
            "weighted_outage_capacity_ratio",
            "watch_refinery_count",
            "blocked_refinery_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio("max_flare_event_ratio", self.max_flare_event_ratio)
        _require_ratio("max_outage_capacity_ratio", self.max_outage_capacity_ratio)
        _require_ratio("weighted_flare_event_ratio", self.weighted_flare_event_ratio)
        _require_ratio(
            "weighted_outage_capacity_ratio",
            self.weighted_outage_capacity_ratio,
        )
        object.__setattr__(self, "rows", _normalize_refinery_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_counts(self.reason_code_counts),
        )
        _validate_digest(self)
        _require_hard_flags("refinery unplanned flare digest", self)


def build_market_research_energy_refinery_unplanned_flare_digest(
    rows: Iterable[EnergyRefineryUnplannedFlareInput],
    *,
    config: EnergyRefineryUnplannedFlareDigestConfig,
    generated_at: datetime,
) -> EnergyRefineryUnplannedFlareDigest:
    if type(config) is not EnergyRefineryUnplannedFlareDigestConfig:
        raise ValueError(
            "config must be an EnergyRefineryUnplannedFlareDigestConfig"
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(rows)
    if not input_rows:
        return EnergyRefineryUnplannedFlareDigest(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            digest_status="empty",
            recommended_next_step=(
                "monitor_report_only_market_research_energy_refinery_"
                "unplanned_flare_digest"
            ),
            reason_codes=("refinery_unplanned_flare_digest_empty",),
            refinery_count=ZERO,
            source_count=ZERO,
            total_unplanned_flare_event_count=ZERO,
            total_sample_count=ZERO,
            total_offline_capacity_bpd=ZERO,
            total_nameplate_capacity_bpd=ZERO,
            total_expected_offline_capacity_bpd=ZERO,
            max_flare_event_ratio=ZERO,
            max_outage_capacity_ratio=ZERO,
            weighted_flare_event_ratio=ZERO,
            weighted_outage_capacity_ratio=ZERO,
            watch_refinery_count=ZERO,
            blocked_refinery_count=ZERO,
            rows=(),
            reason_code_counts=(),
        )

    grouped: dict[str, list[EnergyRefineryUnplannedFlareInput]] = {}
    for input_row in input_rows:
        grouped.setdefault(input_row.refinery_id, []).append(input_row)
    refinery_rows = tuple(
        _refinery_row(refinery_id, tuple(refinery_inputs), config=config)
        for refinery_id, refinery_inputs in sorted(
            grouped.items(),
            key=lambda item: item[0],
        )
    )
    sorted_rows = tuple(sorted(refinery_rows, key=_row_sort_key))
    refinery_count = _count(len(sorted_rows))
    reason_codes = _digest_reasons(sorted_rows)
    digest_status = _digest_status(sorted_rows)

    return EnergyRefineryUnplannedFlareDigest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=_next_step(digest_status),
        reason_codes=reason_codes,
        refinery_count=refinery_count,
        source_count=_sum_decimal(row.source_count for row in sorted_rows),
        total_unplanned_flare_event_count=_sum_decimal(
            row.unplanned_flare_event_count for row in sorted_rows
        ),
        total_sample_count=_sum_decimal(row.sample_count for row in sorted_rows),
        total_offline_capacity_bpd=_sum_decimal(
            row.offline_capacity_bpd for row in sorted_rows
        ),
        total_nameplate_capacity_bpd=_sum_decimal(
            row.nameplate_capacity_bpd for row in sorted_rows
        ),
        total_expected_offline_capacity_bpd=_sum_decimal(
            row.expected_offline_capacity_bpd for row in sorted_rows
        ),
        max_flare_event_ratio=max(
            (row.flare_event_ratio for row in sorted_rows),
            default=ZERO,
        ),
        max_outage_capacity_ratio=max(
            (row.outage_capacity_ratio for row in sorted_rows),
            default=ZERO,
        ),
        weighted_flare_event_ratio=_ratio(
            _sum_decimal(row.unplanned_flare_event_count for row in sorted_rows),
            _sum_decimal(row.sample_count for row in sorted_rows),
        ),
        weighted_outage_capacity_ratio=_ratio(
            _sum_decimal(row.offline_capacity_bpd for row in sorted_rows),
            _sum_decimal(row.nameplate_capacity_bpd for row in sorted_rows),
        ),
        watch_refinery_count=_count(
            sum(1 for row in sorted_rows if row.risk_status == "watch")
        ),
        blocked_refinery_count=_count(
            sum(1 for row in sorted_rows if row.risk_status == "blocked")
        ),
        rows=sorted_rows,
        reason_code_counts=_reason_counts(sorted_rows, reason_codes, refinery_count),
    )


def market_research_energy_refinery_unplanned_flare_digest_payload(
    digest: EnergyRefineryUnplannedFlareDigest,
) -> dict[str, Any]:
    if type(digest) is not EnergyRefineryUnplannedFlareDigest:
        raise ValueError("digest must be an EnergyRefineryUnplannedFlareDigest")
    return _json_ready(digest)


def _refinery_row(
    refinery_id: str,
    rows: tuple[EnergyRefineryUnplannedFlareInput, ...],
    *,
    config: EnergyRefineryUnplannedFlareDigestConfig,
) -> EnergyRefineryUnplannedFlareRefineryRow:
    event_count = _sum_decimal(row.unplanned_flare_event_count for row in rows)
    sample_count = _sum_decimal(row.sample_count for row in rows)
    offline_capacity = _sum_decimal(row.offline_capacity_bpd for row in rows)
    nameplate_capacity = _sum_decimal(row.nameplate_capacity_bpd for row in rows)
    expected_capacity = _sum_decimal(
        row.expected_offline_capacity_bpd for row in rows
    )
    flare_ratio = _ratio(event_count, sample_count)
    outage_ratio = _ratio(offline_capacity, nameplate_capacity)
    expected_ratio = _ratio(expected_capacity, nameplate_capacity)
    status = _row_status(flare_ratio, outage_ratio, config=config)
    return EnergyRefineryUnplannedFlareRefineryRow(
        refinery_id=refinery_id,
        region_ids=tuple(row.region_id for row in rows),
        market_ids=tuple(row.market_id for row in rows),
        source_ids=tuple(row.source_id for row in rows),
        unplanned_flare_event_count=event_count,
        sample_count=sample_count,
        flare_event_ratio=flare_ratio,
        offline_capacity_bpd=offline_capacity,
        nameplate_capacity_bpd=nameplate_capacity,
        expected_offline_capacity_bpd=expected_capacity,
        outage_capacity_ratio=outage_ratio,
        expected_outage_capacity_ratio=expected_ratio,
        outage_surprise_ratio=outage_ratio - expected_ratio,
        source_count=_count(len(rows)),
        latest_observed_at=max(row.observed_at for row in rows),
        risk_status=status,
        reason_codes=_row_reasons(
            rows,
            status=status,
            sample_count=sample_count,
            outage_capacity_ratio=outage_ratio,
            config=config,
        ),
    )


def _row_status(
    flare_event_ratio: Decimal,
    outage_capacity_ratio: Decimal,
    *,
    config: EnergyRefineryUnplannedFlareDigestConfig,
) -> str:
    if (
        flare_event_ratio >= config.blocked_flare_event_ratio
        or outage_capacity_ratio >= config.blocked_outage_capacity_ratio
    ):
        return "blocked"
    if (
        flare_event_ratio >= config.watch_flare_event_ratio
        or outage_capacity_ratio >= config.watch_outage_capacity_ratio
    ):
        return "watch"
    return "clear"


def _row_reasons(
    rows: tuple[EnergyRefineryUnplannedFlareInput, ...],
    *,
    status: str,
    sample_count: Decimal,
    outage_capacity_ratio: Decimal,
    config: EnergyRefineryUnplannedFlareDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if sample_count < config.min_sample_count or any(
        "refinery_unplanned_flare_source_gap" in row.reason_codes for row in rows
    ):
        reasons.append("refinery_unplanned_flare_source_gap")
    if status == "blocked":
        reasons.append("refinery_unplanned_flare_refinery_blocked")
    elif status == "watch":
        reasons.append("refinery_unplanned_flare_refinery_watch")
    else:
        reasons.append("refinery_unplanned_flare_refinery_clear")
    if outage_capacity_ratio >= config.blocked_outage_capacity_ratio:
        reasons.append("refinery_unplanned_flare_outage_blocked")
    elif outage_capacity_ratio >= config.watch_outage_capacity_ratio:
        reasons.append("refinery_unplanned_flare_outage_watch")
    if any("refinery_unplanned_flare_revision" in row.reason_codes for row in rows):
        reasons.append("refinery_unplanned_flare_revision_present")
    return _normalize_reasons("reason_codes", tuple(reasons), ROW_REASONS)


def _digest_status(
    rows: tuple[EnergyRefineryUnplannedFlareRefineryRow, ...],
) -> str:
    if any(row.risk_status == "blocked" for row in rows):
        return "blocked"
    if any(row.risk_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _digest_reasons(
    rows: tuple[EnergyRefineryUnplannedFlareRefineryRow, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if any("refinery_unplanned_flare_source_gap" in row.reason_codes for row in rows):
        reasons.append("refinery_unplanned_flare_source_gap_present")
    if any(row.risk_status == "watch" for row in rows):
        reasons.append("refinery_unplanned_flare_watch_present")
    if any(row.risk_status == "blocked" for row in rows):
        reasons.append("refinery_unplanned_flare_blocked_present")
    if any(
        "refinery_unplanned_flare_outage_watch" in row.reason_codes for row in rows
    ):
        reasons.append("refinery_unplanned_flare_outage_watch_present")
    if any(
        "refinery_unplanned_flare_outage_blocked" in row.reason_codes
        for row in rows
    ):
        reasons.append("refinery_unplanned_flare_outage_blocked_present")
    if any(
        "refinery_unplanned_flare_revision_present" in row.reason_codes
        for row in rows
    ):
        reasons.append("refinery_unplanned_flare_revision_present")
    if not reasons:
        reasons.append("refinery_unplanned_flare_clear")
    return _normalize_reasons("reason_codes", tuple(reasons), REPORT_REASONS)


def _reason_counts(
    rows: tuple[EnergyRefineryUnplannedFlareRefineryRow, ...],
    report_reasons: tuple[str, ...],
    refinery_count: Decimal,
) -> tuple[EnergyRefineryUnplannedFlareReasonCodeCount, ...]:
    if report_reasons == ("refinery_unplanned_flare_digest_empty",):
        return ()
    return tuple(
        EnergyRefineryUnplannedFlareReasonCodeCount(
            reason_code=reason,
            refinery_count=_count(
                sum(1 for row in rows if _row_matches_report_reason(row, reason))
            ),
            refinery_ratio=_ratio(
                _count(
                    sum(1 for row in rows if _row_matches_report_reason(row, reason))
                ),
                refinery_count,
            ),
        )
        for reason in report_reasons
    )


def _row_matches_report_reason(
    row: EnergyRefineryUnplannedFlareRefineryRow,
    reason: str,
) -> bool:
    if reason == "refinery_unplanned_flare_clear":
        return row.risk_status == "clear"
    if reason == "refinery_unplanned_flare_source_gap_present":
        return "refinery_unplanned_flare_source_gap" in row.reason_codes
    if reason == "refinery_unplanned_flare_watch_present":
        return row.risk_status == "watch"
    if reason == "refinery_unplanned_flare_blocked_present":
        return row.risk_status == "blocked"
    if reason == "refinery_unplanned_flare_outage_watch_present":
        return "refinery_unplanned_flare_outage_watch" in row.reason_codes
    if reason == "refinery_unplanned_flare_outage_blocked_present":
        return "refinery_unplanned_flare_outage_blocked" in row.reason_codes
    if reason == "refinery_unplanned_flare_revision_present":
        return "refinery_unplanned_flare_revision_present" in row.reason_codes
    return False


def _next_step(status: str) -> str:
    if status == "blocked":
        return (
            "block_report_only_market_research_energy_refinery_"
            "unplanned_flare_digest"
        )
    if status in {"empty", "watch"}:
        return (
            "monitor_report_only_market_research_energy_refinery_"
            "unplanned_flare_digest"
        )
    return (
        "allow_report_only_market_research_energy_refinery_"
        "unplanned_flare_digest"
    )


def _normalize_inputs(
    rows: Iterable[EnergyRefineryUnplannedFlareInput],
) -> tuple[EnergyRefineryUnplannedFlareInput, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain refinery unplanned flare inputs")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must contain refinery unplanned flare inputs") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not EnergyRefineryUnplannedFlareInput:
            raise ValueError("rows must contain EnergyRefineryUnplannedFlareInput")
        if row.source_id in seen:
            raise ValueError("rows must not contain duplicate source_id values")
        seen.add(row.source_id)
    return normalized


def _normalize_refinery_rows(
    value: object,
) -> tuple[EnergyRefineryUnplannedFlareRefineryRow, ...]:
    if not isinstance(value, tuple):
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not EnergyRefineryUnplannedFlareRefineryRow:
            raise ValueError(
                "rows must contain EnergyRefineryUnplannedFlareRefineryRow"
            )
    if value != tuple(sorted(value, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if len({row.refinery_id for row in value}) != len(value):
        raise ValueError("rows must not contain duplicate refinery_id values")
    return value


def _normalize_reason_counts(
    value: object,
) -> tuple[EnergyRefineryUnplannedFlareReasonCodeCount, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for row in value:
        if type(row) is not EnergyRefineryUnplannedFlareReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "EnergyRefineryUnplannedFlareReasonCodeCount"
            )
    if value != tuple(sorted(value, key=lambda row: REPORT_REASONS.index(row.reason_code))):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return value


def _row_sort_key(
    row: EnergyRefineryUnplannedFlareRefineryRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.risk_status],
        -row.outage_capacity_ratio,
        -row.flare_event_ratio,
        row.refinery_id,
    )


def _validate_refinery_row(row: EnergyRefineryUnplannedFlareRefineryRow) -> None:
    if row.unplanned_flare_event_count > row.sample_count:
        raise ValueError("unplanned_flare_event_count must not exceed sample_count")
    if row.offline_capacity_bpd > row.nameplate_capacity_bpd:
        raise ValueError("offline_capacity_bpd must not exceed nameplate_capacity_bpd")
    if row.expected_offline_capacity_bpd > row.nameplate_capacity_bpd:
        raise ValueError(
            "expected_offline_capacity_bpd must not exceed nameplate_capacity_bpd"
        )
    if row.flare_event_ratio != _ratio(
        row.unplanned_flare_event_count,
        row.sample_count,
    ):
        raise ValueError("flare_event_ratio must match flare events and samples")
    if row.outage_capacity_ratio != _ratio(
        row.offline_capacity_bpd,
        row.nameplate_capacity_bpd,
    ):
        raise ValueError("outage_capacity_ratio must match offline and nameplate")
    if row.expected_outage_capacity_ratio != _ratio(
        row.expected_offline_capacity_bpd,
        row.nameplate_capacity_bpd,
    ):
        raise ValueError(
            "expected_outage_capacity_ratio must match expected and nameplate"
        )
    if (
        row.outage_surprise_ratio
        != row.outage_capacity_ratio - row.expected_outage_capacity_ratio
    ):
        raise ValueError("outage_surprise_ratio must match outage ratios")
    if row.source_count != _count(len(row.source_ids)):
        raise ValueError("source_count must match source_ids")


def _validate_digest(digest: EnergyRefineryUnplannedFlareDigest) -> None:
    if digest.refinery_count != _count(len(digest.rows)):
        raise ValueError("refinery_count must match rows")
    if digest.source_count != _sum_decimal(row.source_count for row in digest.rows):
        raise ValueError("source_count must match rows")
    if digest.total_unplanned_flare_event_count != _sum_decimal(
        row.unplanned_flare_event_count for row in digest.rows
    ):
        raise ValueError("total_unplanned_flare_event_count must match rows")
    if digest.total_sample_count != _sum_decimal(row.sample_count for row in digest.rows):
        raise ValueError("total_sample_count must match rows")
    if digest.total_offline_capacity_bpd != _sum_decimal(
        row.offline_capacity_bpd for row in digest.rows
    ):
        raise ValueError("total_offline_capacity_bpd must match rows")
    if digest.total_nameplate_capacity_bpd != _sum_decimal(
        row.nameplate_capacity_bpd for row in digest.rows
    ):
        raise ValueError("total_nameplate_capacity_bpd must match rows")
    if digest.total_expected_offline_capacity_bpd != _sum_decimal(
        row.expected_offline_capacity_bpd for row in digest.rows
    ):
        raise ValueError("total_expected_offline_capacity_bpd must match rows")
    if digest.max_flare_event_ratio != max(
        (row.flare_event_ratio for row in digest.rows),
        default=ZERO,
    ):
        raise ValueError("max_flare_event_ratio must match rows")
    if digest.max_outage_capacity_ratio != max(
        (row.outage_capacity_ratio for row in digest.rows),
        default=ZERO,
    ):
        raise ValueError("max_outage_capacity_ratio must match rows")
    if digest.weighted_flare_event_ratio != _ratio(
        digest.total_unplanned_flare_event_count,
        digest.total_sample_count,
    ):
        raise ValueError("weighted_flare_event_ratio must match totals")
    if digest.weighted_outage_capacity_ratio != _ratio(
        digest.total_offline_capacity_bpd,
        digest.total_nameplate_capacity_bpd,
    ):
        raise ValueError("weighted_outage_capacity_ratio must match totals")
    if digest.watch_refinery_count != _count(
        sum(1 for row in digest.rows if row.risk_status == "watch")
    ):
        raise ValueError("watch_refinery_count must match rows")
    if digest.blocked_refinery_count != _count(
        sum(1 for row in digest.rows if row.risk_status == "blocked")
    ):
        raise ValueError("blocked_refinery_count must match rows")
    expected_status = "empty" if not digest.rows else _digest_status(digest.rows)
    if digest.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    if digest.recommended_next_step != _next_step(digest.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    expected_reasons = (
        ("refinery_unplanned_flare_digest_empty",)
        if not digest.rows
        else _digest_reasons(digest.rows)
    )
    if digest.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    expected_count_reasons = () if not digest.rows else digest.reason_codes
    if tuple(row.reason_code for row in digest.reason_code_counts) != expected_count_reasons:
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_text_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    return tuple(sorted({_require_text(field_name, item) for item in value}))


def _normalize_reasons(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    reasons = tuple({_require_member("reason_code", item, allowed) for item in value})
    return tuple(sorted(reasons, key=lambda item: allowed.index(item)))


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    text = _require_text(field_name, value)
    if text not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return text


def _require_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _require_positive_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_ratio(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_signed_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return total.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} requires {field_name}=True")


__all__ = (
    "DEFAULT_ENERGY_REFINERY_UNPLANNED_FLARE_DIGEST_CONFIG_VERSION",
    "EnergyRefineryUnplannedFlareDigestConfig",
    "EnergyRefineryUnplannedFlareInput",
    "EnergyRefineryUnplannedFlareReasonCodeCount",
    "EnergyRefineryUnplannedFlareRefineryRow",
    "EnergyRefineryUnplannedFlareDigest",
    "build_market_research_energy_refinery_unplanned_flare_digest",
    "market_research_energy_refinery_unplanned_flare_digest_payload",
)
