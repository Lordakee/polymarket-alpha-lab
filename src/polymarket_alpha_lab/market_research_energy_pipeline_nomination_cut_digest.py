"""Pure report-only reducer for energy pipeline nomination cut digests."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_CONFIG_VERSION = "energy_pipeline_nomination_cut_digest.v1"
PHASE_NAME = "phase_1_market_research"

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_HUNDRED = Decimal("100.000000")
_QUANT = Decimal("0.000001")

_ROW_STATUSES = ("pass", "watch", "blocked")
_REPORT_STATUSES = ("pass", "watch", "blocked")
_COMMODITIES = ("gas", "oil")
_PHASE_FLAG_FIELDS = frozenset({"paper_only", "report_only", "readonly"})

_NOMINATION_WEIGHT = Decimal("0.350000")
_CAPACITY_WEIGHT = Decimal("0.200000")
_STORAGE_WEIGHT = Decimal("0.150000")
_TEMPERATURE_WEIGHT = Decimal("0.100000")
_OUTAGE_WEIGHT = Decimal("0.100000")
_SOURCE_QUORUM_WEIGHT = Decimal("0.050000")
_SOURCE_FRESHNESS_WEIGHT = Decimal("0.050000")

_REASON_CODE_SEQUENCE = (
    "nomination_cut_blocked",
    "capacity_cut_blocked",
    "storage_buffer_blocked",
    "demand_temperature_blocked",
    "outage_duration_blocked",
    "source_quorum_low",
    "source_freshness_stale",
    "risk_score_blocked",
    "nomination_cut_watch",
    "capacity_cut_watch",
    "storage_buffer_watch",
    "demand_temperature_watch",
    "outage_duration_watch",
    "risk_score_watch",
    "energy_pipeline_nomination_cut_passed",
    "energy_pipeline_nomination_cut_no_observations",
)
_BLOCKED_REASON_CODES = frozenset(
    {
        "nomination_cut_blocked",
        "capacity_cut_blocked",
        "storage_buffer_blocked",
        "demand_temperature_blocked",
        "outage_duration_blocked",
        "risk_score_blocked",
    },
)
_WATCH_REASON_CODES = frozenset(
    {
        "nomination_cut_watch",
        "capacity_cut_watch",
        "storage_buffer_watch",
        "demand_temperature_watch",
        "outage_duration_watch",
        "source_quorum_low",
        "source_freshness_stale",
        "risk_score_watch",
    },
)
_PASS_REASON_CODE = "energy_pipeline_nomination_cut_passed"
_EMPTY_REASON_CODE = "energy_pipeline_nomination_cut_no_observations"

_UNSAFE_NAME_FRAGMENTS = (
    "wall" + "et",
    "or" + "der",
    "can" + "cel",
    "re" + "place",
    "ex" + "change",
    "mu" + "tation",
    "au" + "th",
    "ke" + "y",
    "h" + "ttp",
    "sock" + "et",
    "url" + "open",
    "psy" + "copg",
    "supa" + "base",
)
_SENSITIVE_TEXT_FRAGMENTS = (
    "api_" + "ke" + "y",
    "pri" + "vate_" + "ke" + "y",
    "sec" + "ret",
    "bear" + "er ",
    "pass" + "word",
    "to" + "ken=",
    "seed phrase",
)


@dataclass(frozen=True)
class EnergyPipelineNominationCutThresholds:
    watch_nomination_cut_percent: Decimal = Decimal("10.000000")
    blocked_nomination_cut_percent: Decimal = Decimal("25.000000")
    watch_affected_capacity: Decimal = Decimal("250.000000")
    blocked_affected_capacity: Decimal = Decimal("750.000000")
    watch_storage_buffer_days: Decimal = Decimal("3.000000")
    blocked_storage_buffer_days: Decimal = Decimal("1.500000")
    watch_demand_temperature_anomaly_f: Decimal = Decimal("8.000000")
    blocked_demand_temperature_anomaly_f: Decimal = Decimal("15.000000")
    watch_outage_duration_hours: Decimal = Decimal("12.000000")
    blocked_outage_duration_hours: Decimal = Decimal("48.000000")
    min_source_count: Decimal = Decimal("2.000000")
    stale_after_minutes: Decimal = Decimal("180.000000")
    watch_risk_score: Decimal = Decimal("0.350000")
    blocked_risk_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "watch_nomination_cut_percent",
            "blocked_nomination_cut_percent",
            "watch_demand_temperature_anomaly_f",
            "blocked_demand_temperature_anomaly_f",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_percent_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_affected_capacity",
            "blocked_affected_capacity",
            "watch_storage_buffer_days",
            "blocked_storage_buffer_days",
            "watch_outage_duration_hours",
            "blocked_outage_duration_hours",
            "stale_after_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _normalize_nonnegative_integer_decimal(
                "min_source_count",
                self.min_source_count,
            ),
        )
        for field_name in ("watch_risk_score", "blocked_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_nomination_cut_percent > self.blocked_nomination_cut_percent:
            raise ValueError(
                "watch_nomination_cut_percent must not exceed "
                "blocked_nomination_cut_percent",
            )
        if self.watch_affected_capacity > self.blocked_affected_capacity:
            raise ValueError(
                "watch_affected_capacity must not exceed blocked_affected_capacity",
            )
        if self.blocked_storage_buffer_days > self.watch_storage_buffer_days:
            raise ValueError(
                "blocked_storage_buffer_days must not exceed watch_storage_buffer_days",
            )
        if (
            self.watch_demand_temperature_anomaly_f
            > self.blocked_demand_temperature_anomaly_f
        ):
            raise ValueError(
                "watch_demand_temperature_anomaly_f must not exceed "
                "blocked_demand_temperature_anomaly_f",
            )
        if self.watch_outage_duration_hours > self.blocked_outage_duration_hours:
            raise ValueError(
                "watch_outage_duration_hours must not exceed "
                "blocked_outage_duration_hours",
            )
        if self.watch_risk_score > self.blocked_risk_score:
            raise ValueError("watch_risk_score must not exceed blocked_risk_score")
        _require_hard_flags("thresholds", self)


@dataclass(frozen=True)
class EnergyPipelineNominationCutObservation:
    pipeline: str
    region: str
    commodity: str
    market_slug: str
    observed_at: datetime
    nomination_cut_percent: Decimal
    affected_capacity: Decimal
    storage_buffer_days: Decimal
    demand_temperature_anomaly_f: Decimal
    outage_duration_hours: Decimal
    source_count: Decimal
    source_freshness_minutes: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("pipeline", "region", "market_slug"):
            _require_clean_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "commodity",
            _normalize_commodity("commodity", self.commodity),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc_datetime("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "nomination_cut_percent",
            _normalize_percent_decimal(
                "nomination_cut_percent",
                self.nomination_cut_percent,
            ),
        )
        for field_name in (
            "affected_capacity",
            "storage_buffer_days",
            "outage_duration_hours",
            "source_freshness_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "demand_temperature_anomaly_f",
            _normalize_decimal(
                "demand_temperature_anomaly_f",
                self.demand_temperature_anomaly_f,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_integer_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class EnergyPipelineNominationCutDigestRow:
    pipeline: str
    region: str
    commodity: str
    market_slug: str
    observed_at: datetime
    nomination_cut_percent: Decimal
    affected_capacity: Decimal
    storage_buffer_days: Decimal
    demand_temperature_anomaly_f: Decimal
    outage_duration_hours: Decimal
    source_count: Decimal
    source_freshness_minutes: Decimal
    upstream_reason_codes: tuple[str, ...]
    risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    phase: str = PHASE_NAME
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("pipeline", "region", "market_slug", "phase"):
            _require_clean_text(field_name, getattr(self, field_name))
        if self.phase != PHASE_NAME:
            raise ValueError(f"phase must be {PHASE_NAME}")
        object.__setattr__(
            self,
            "commodity",
            _normalize_commodity("commodity", self.commodity),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc_datetime("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "nomination_cut_percent",
            _normalize_percent_decimal(
                "nomination_cut_percent",
                self.nomination_cut_percent,
            ),
        )
        for field_name in (
            "affected_capacity",
            "storage_buffer_days",
            "outage_duration_hours",
            "source_freshness_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "demand_temperature_anomaly_f",
            _normalize_decimal(
                "demand_temperature_anomaly_f",
                self.demand_temperature_anomaly_f,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_integer_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        object.__setattr__(
            self,
            "risk_score",
            _normalize_ratio_decimal("risk_score", self.risk_score),
        )
        object.__setattr__(self, "status", _normalize_row_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("digest row", self)


@dataclass(frozen=True)
class EnergyPipelineNominationCutDigestReport:
    generated_at: datetime
    config_version: str
    thresholds: EnergyPipelineNominationCutThresholds
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    total_affected_capacity: Decimal
    max_nomination_cut_percent: Decimal
    min_storage_buffer_days: Decimal
    max_demand_temperature_anomaly_f: Decimal
    max_outage_duration_hours: Decimal
    risk_score: Decimal
    average_risk_score: Decimal
    status: str
    top_market_slug: str | None
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    upstream_reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[EnergyPipelineNominationCutDigestRow, ...]
    phase: str = PHASE_NAME
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc_datetime("generated_at", self.generated_at),
        )
        _require_clean_text("config_version", self.config_version)
        if type(self.thresholds) is not EnergyPipelineNominationCutThresholds:
            raise ValueError("thresholds must be EnergyPipelineNominationCutThresholds")
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integer_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "total_affected_capacity",
            "max_nomination_cut_percent",
            "min_storage_buffer_days",
            "max_demand_temperature_anomaly_f",
            "max_outage_duration_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("risk_score", "average_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "status",
            _normalize_report_status("status", self.status),
        )
        if self.top_market_slug is not None:
            _require_clean_text("top_market_slug", self.top_market_slug)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "upstream_reason_code_counts",
            _normalize_upstream_reason_code_counts(self.upstream_reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_clean_text("phase", self.phase)
        if self.phase != PHASE_NAME:
            raise ValueError(f"phase must be {PHASE_NAME}")
        _validate_report_consistency(self)
        _require_hard_flags("digest report", self)


def build_market_research_energy_pipeline_nomination_cut_digest_report(
    observations: Iterable[EnergyPipelineNominationCutObservation],
    *,
    generated_at: datetime,
    thresholds: EnergyPipelineNominationCutThresholds | None = None,
    config_version: str = DEFAULT_CONFIG_VERSION,
) -> EnergyPipelineNominationCutDigestReport:
    generated_at = _as_utc_datetime("generated_at", generated_at)
    _require_clean_text("config_version", config_version)
    if thresholds is None:
        thresholds = EnergyPipelineNominationCutThresholds()
    elif type(thresholds) is not EnergyPipelineNominationCutThresholds:
        raise ValueError("thresholds must be EnergyPipelineNominationCutThresholds")

    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        _row_from_observation(observation, thresholds)
        for observation in normalized_observations
    )
    sorted_rows = _sort_rows(rows)

    if not sorted_rows:
        return EnergyPipelineNominationCutDigestReport(
            generated_at=generated_at,
            config_version=config_version,
            thresholds=thresholds,
            observation_count=_ZERO,
            pass_count=_ZERO,
            watch_count=_ZERO,
            blocked_count=_ZERO,
            total_affected_capacity=_ZERO,
            max_nomination_cut_percent=_ZERO,
            min_storage_buffer_days=_ZERO,
            max_demand_temperature_anomaly_f=_ZERO,
            max_outage_duration_hours=_ZERO,
            risk_score=_ZERO,
            average_risk_score=_ZERO,
            status="pass",
            top_market_slug=None,
            reason_codes=(_EMPTY_REASON_CODE,),
            reason_code_counts=((_EMPTY_REASON_CODE, _ONE),),
            upstream_reason_code_counts=(),
            rows=(),
        )

    pass_count = _count_rows_with_status(sorted_rows, "pass")
    watch_count = _count_rows_with_status(sorted_rows, "watch")
    blocked_count = _count_rows_with_status(sorted_rows, "blocked")
    report_reason_codes = _report_reason_codes(sorted_rows)
    return EnergyPipelineNominationCutDigestReport(
        generated_at=generated_at,
        config_version=config_version,
        thresholds=thresholds,
        observation_count=_decimal_count(len(sorted_rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        total_affected_capacity=sum(
            (row.affected_capacity for row in sorted_rows),
            _ZERO,
        ),
        max_nomination_cut_percent=max(
            row.nomination_cut_percent for row in sorted_rows
        ),
        min_storage_buffer_days=min(row.storage_buffer_days for row in sorted_rows),
        max_demand_temperature_anomaly_f=max(
            _abs_decimal(row.demand_temperature_anomaly_f) for row in sorted_rows
        ),
        max_outage_duration_hours=max(row.outage_duration_hours for row in sorted_rows),
        risk_score=max(row.risk_score for row in sorted_rows),
        average_risk_score=_quantize_decimal(
            sum((row.risk_score for row in sorted_rows), _ZERO)
            / _decimal_count(len(sorted_rows)),
        ),
        status=_report_status(watch_count, blocked_count),
        top_market_slug=sorted_rows[0].market_slug,
        reason_codes=report_reason_codes,
        reason_code_counts=_reason_counts(report_reason_codes, sorted_rows),
        upstream_reason_code_counts=_upstream_reason_counts(sorted_rows),
        rows=sorted_rows,
    )


def market_research_energy_pipeline_nomination_cut_digest_payload(
    report: EnergyPipelineNominationCutDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is EnergyPipelineNominationCutDigestReport:
        _require_hard_flags("report", report)
        _reject_unsafe_payload_names("energy pipeline nomination cut digest", report)
        _reject_sensitive_public_text("energy pipeline nomination cut digest", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_payload_names("energy pipeline nomination cut digest payload", report)
        _reject_flag_downgrades("energy pipeline nomination cut digest payload", report)
        _reject_sensitive_public_text(
            "energy pipeline nomination cut digest payload",
            report,
        )
        payload = _json_ready(report)
    else:
        raise ValueError("report must be EnergyPipelineNominationCutDigestReport")

    if type(payload) is not dict:
        raise ValueError("report payload must be a mapping")
    _reject_unsafe_payload_names("energy pipeline nomination cut digest payload", payload)
    _reject_flag_downgrades("energy pipeline nomination cut digest payload", payload)
    _reject_sensitive_public_text("energy pipeline nomination cut digest payload", payload)
    _require_hard_flags("payload", _MappingFlags(payload))
    return payload


@dataclass(frozen=True)
class _MappingFlags:
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


def _row_from_observation(
    observation: EnergyPipelineNominationCutObservation,
    thresholds: EnergyPipelineNominationCutThresholds,
) -> EnergyPipelineNominationCutDigestRow:
    reason_codes = _row_reason_codes(observation, thresholds)
    risk_score = _row_risk_score(observation, thresholds)
    status = _row_status(reason_codes, risk_score, thresholds)
    if status == "pass":
        reason_codes = (_PASS_REASON_CODE,)
    elif status == "blocked" and not any(
        code in _BLOCKED_REASON_CODES for code in reason_codes
    ):
        reason_codes = _ranked_reason_codes((*reason_codes, "risk_score_blocked"))
    elif status == "watch" and not any(
        code in _WATCH_REASON_CODES for code in reason_codes
    ):
        reason_codes = _ranked_reason_codes((*reason_codes, "risk_score_watch"))
    return EnergyPipelineNominationCutDigestRow(
        pipeline=observation.pipeline,
        region=observation.region,
        commodity=observation.commodity,
        market_slug=observation.market_slug,
        observed_at=observation.observed_at,
        nomination_cut_percent=observation.nomination_cut_percent,
        affected_capacity=observation.affected_capacity,
        storage_buffer_days=observation.storage_buffer_days,
        demand_temperature_anomaly_f=observation.demand_temperature_anomaly_f,
        outage_duration_hours=observation.outage_duration_hours,
        source_count=observation.source_count,
        source_freshness_minutes=observation.source_freshness_minutes,
        upstream_reason_codes=observation.upstream_reason_codes,
        risk_score=risk_score,
        status=status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: EnergyPipelineNominationCutObservation,
    thresholds: EnergyPipelineNominationCutThresholds,
) -> tuple[str, ...]:
    codes: list[str] = []
    if observation.nomination_cut_percent >= thresholds.blocked_nomination_cut_percent:
        codes.append("nomination_cut_blocked")
    elif observation.nomination_cut_percent >= thresholds.watch_nomination_cut_percent:
        codes.append("nomination_cut_watch")
    if observation.affected_capacity >= thresholds.blocked_affected_capacity:
        codes.append("capacity_cut_blocked")
    elif observation.affected_capacity >= thresholds.watch_affected_capacity:
        codes.append("capacity_cut_watch")
    if observation.storage_buffer_days <= thresholds.blocked_storage_buffer_days:
        codes.append("storage_buffer_blocked")
    elif observation.storage_buffer_days <= thresholds.watch_storage_buffer_days:
        codes.append("storage_buffer_watch")
    demand_temperature = _abs_decimal(observation.demand_temperature_anomaly_f)
    if demand_temperature >= thresholds.blocked_demand_temperature_anomaly_f:
        codes.append("demand_temperature_blocked")
    elif demand_temperature >= thresholds.watch_demand_temperature_anomaly_f:
        codes.append("demand_temperature_watch")
    if observation.outage_duration_hours >= thresholds.blocked_outage_duration_hours:
        codes.append("outage_duration_blocked")
    elif observation.outage_duration_hours >= thresholds.watch_outage_duration_hours:
        codes.append("outage_duration_watch")
    if observation.source_count < thresholds.min_source_count:
        codes.append("source_quorum_low")
    if observation.source_freshness_minutes > thresholds.stale_after_minutes:
        codes.append("source_freshness_stale")
    return _ranked_reason_codes(codes)


def _row_risk_score(
    observation: EnergyPipelineNominationCutObservation,
    thresholds: EnergyPipelineNominationCutThresholds,
) -> Decimal:
    score = (
        _positive_component(
            observation.nomination_cut_percent,
            thresholds.blocked_nomination_cut_percent,
            _NOMINATION_WEIGHT,
        )
        + _positive_component(
            observation.affected_capacity,
            thresholds.blocked_affected_capacity,
            _CAPACITY_WEIGHT,
        )
        + _storage_component(
            observation.storage_buffer_days,
            thresholds.watch_storage_buffer_days,
            thresholds.blocked_storage_buffer_days,
            _STORAGE_WEIGHT,
        )
        + _positive_component(
            _abs_decimal(observation.demand_temperature_anomaly_f),
            thresholds.blocked_demand_temperature_anomaly_f,
            _TEMPERATURE_WEIGHT,
        )
        + _positive_component(
            observation.outage_duration_hours,
            thresholds.blocked_outage_duration_hours,
            _OUTAGE_WEIGHT,
        )
        + (
            _SOURCE_QUORUM_WEIGHT
            if observation.source_count < thresholds.min_source_count
            else _ZERO
        )
        + (
            _SOURCE_FRESHNESS_WEIGHT
            if observation.source_freshness_minutes > thresholds.stale_after_minutes
            else _ZERO
        )
    )
    return _quantize_decimal(min(score, _ONE))


def _positive_component(value: Decimal, blocked_value: Decimal, weight: Decimal) -> Decimal:
    if value <= _ZERO:
        return _ZERO
    if blocked_value <= _ZERO:
        return weight
    return min(value / blocked_value, _ONE) * weight


def _storage_component(
    value: Decimal,
    watch_value: Decimal,
    blocked_value: Decimal,
    weight: Decimal,
) -> Decimal:
    if value > watch_value:
        return _ZERO
    if value <= blocked_value:
        return weight
    span = watch_value - blocked_value
    if span <= _ZERO:
        return weight
    return ((watch_value - value) / span) * weight


def _row_status(
    reason_codes: tuple[str, ...],
    risk_score: Decimal,
    thresholds: EnergyPipelineNominationCutThresholds,
) -> str:
    if any(code in _BLOCKED_REASON_CODES for code in reason_codes):
        return "blocked"
    if risk_score >= thresholds.blocked_risk_score:
        return "blocked"
    if any(code in _WATCH_REASON_CODES for code in reason_codes):
        return "watch"
    if risk_score >= thresholds.watch_risk_score:
        return "watch"
    return "pass"


def _report_status(watch_count: Decimal, blocked_count: Decimal) -> str:
    if blocked_count > _ZERO:
        return "blocked"
    if watch_count > _ZERO:
        return "watch"
    return "pass"


def _count_rows_with_status(
    rows: tuple[EnergyPipelineNominationCutDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _report_reason_codes(
    rows: tuple[EnergyPipelineNominationCutDigestRow, ...],
) -> tuple[str, ...]:
    codes = [
        code
        for row in rows
        for code in row.reason_codes
        if code != _PASS_REASON_CODE
    ]
    if codes:
        return _ranked_reason_codes(codes)
    return (_PASS_REASON_CODE,)


def _reason_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[EnergyPipelineNominationCutDigestRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts = {code: _ZERO for code in reason_codes}
    for row in rows:
        for code in row.reason_codes:
            if code in counts:
                counts[code] = counts[code] + _ONE
    return tuple((code, counts[code]) for code in reason_codes)


def _upstream_reason_counts(
    rows: tuple[EnergyPipelineNominationCutDigestRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for code in row.upstream_reason_codes:
            counts[code] = counts.get(code, _ZERO) + _ONE
    pairs = list(counts.items())
    pairs.sort()
    return tuple(pairs)


def _sort_rows(
    rows: tuple[EnergyPipelineNominationCutDigestRow, ...],
) -> tuple[EnergyPipelineNominationCutDigestRow, ...]:
    pairs = [(_row_sort_token(row), row) for row in rows]
    pairs.sort()
    return tuple(row for _, row in pairs)


def _row_sort_token(row: EnergyPipelineNominationCutDigestRow) -> tuple[object, ...]:
    status_position = {"blocked": 0, "watch": 1, "pass": 2}[row.status]
    return (
        status_position,
        -row.risk_score,
        -row.nomination_cut_percent,
        -row.affected_capacity,
        row.market_slug,
        row.pipeline,
    )


def _normalize_observations(
    observations: Iterable[EnergyPipelineNominationCutObservation],
) -> tuple[EnergyPipelineNominationCutObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized: list[EnergyPipelineNominationCutObservation] = []
    for observation in observations:
        if type(observation) is not EnergyPipelineNominationCutObservation:
            raise ValueError(
                "observations must contain EnergyPipelineNominationCutObservation",
            )
        normalized.append(observation)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[EnergyPipelineNominationCutDigestRow, ...],
) -> tuple[EnergyPipelineNominationCutDigestRow, ...]:
    if not isinstance(rows, (tuple, list)):
        raise ValueError("rows must be a tuple")
    normalized: list[EnergyPipelineNominationCutDigestRow] = []
    for row in rows:
        if type(row) is not EnergyPipelineNominationCutDigestRow:
            raise ValueError("rows must contain EnergyPipelineNominationCutDigestRow")
        normalized.append(row)
    return _sort_rows(tuple(normalized))


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(reason_codes, (tuple, list)):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for code in reason_codes:
        _require_reason_code("reason_codes", code)
        normalized.append(code)
    return _ranked_reason_codes(normalized)


def _ranked_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    seen = set(reason_codes)
    positions = {
        code: position for position, code in enumerate(_REASON_CODE_SEQUENCE)
    }
    ranked = [(positions.get(code, len(positions)), code) for code in seen]
    ranked.sort()
    return tuple(code for _, code in ranked)


def _normalize_reason_code_counts(
    value: tuple[tuple[str, Decimal], ...],
) -> tuple[tuple[str, Decimal], ...]:
    if not isinstance(value, (tuple, list)):
        raise ValueError("reason_code_counts must be a tuple")
    counts: dict[str, Decimal] = {}
    for item in value:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise ValueError("reason_code_counts must contain pairs")
        code = item[0]
        count = item[1]
        _require_reason_code("reason_code_counts", code)
        counts[code] = _normalize_nonnegative_integer_decimal(
            "reason_code_counts",
            count,
        )
    return tuple((code, counts[code]) for code in _ranked_reason_codes(counts))


def _normalize_upstream_reason_code_counts(
    value: tuple[tuple[str, Decimal], ...],
) -> tuple[tuple[str, Decimal], ...]:
    if not isinstance(value, (tuple, list)):
        raise ValueError("upstream_reason_code_counts must be a tuple")
    pairs: list[tuple[str, Decimal]] = []
    for item in value:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise ValueError("upstream_reason_code_counts must contain pairs")
        code = _normalize_upstream_reason_code(item[0])
        count = _normalize_nonnegative_integer_decimal(
            "upstream_reason_code_counts",
            item[1],
        )
        pairs.append((code, count))
    pairs.sort()
    return tuple(pairs)


def _normalize_upstream_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        raise ValueError("upstream_reason_codes must be a tuple")
    codes = {_normalize_upstream_reason_code(code) for code in value}
    normalized = list(codes)
    normalized.sort()
    return tuple(normalized)


def _normalize_upstream_reason_code(value: object) -> str:
    _require_reason_code("upstream_reason_code", value)
    code = str(value)
    if not all(character.islower() or character.isdigit() or character in "_-" for character in code):
        raise ValueError("upstream_reason_code must use lowercase code text")
    return code


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if not value:
        raise ValueError(f"{field_name} must contain non-empty strings")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have surrounding whitespace")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    _reject_sensitive_text(field_name, value)


def _normalize_commodity(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in _COMMODITIES:
        raise ValueError("commodity must be gas or oil")
    return value


def _normalize_row_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _ROW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")
    return value


def _normalize_report_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")
    return value


def _normalize_percent_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _HUNDRED:
        raise ValueError(f"{field_name} must be between 0 and 100")
    return normalized


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_integer_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_checked(field_name, value)


def _quantize_checked(field_name: str, value: Decimal) -> Decimal:
    normalized = value.quantize(_QUANT)
    if value != normalized:
        raise ValueError(f"{field_name} must use no more than six decimal places")
    return normalized


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _abs_decimal(value: Decimal) -> Decimal:
    if value < _ZERO:
        return -value
    return value


def _as_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_clean_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have surrounding whitespace")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    _reject_sensitive_text(field_name, value)


def _validate_report_consistency(
    report: EnergyPipelineNominationCutDigestReport,
) -> None:
    row_count = _decimal_count(len(report.rows))
    pass_count = _count_rows_with_status(report.rows, "pass")
    watch_count = _count_rows_with_status(report.rows, "watch")
    blocked_count = _count_rows_with_status(report.rows, "blocked")
    if report.observation_count != row_count:
        raise ValueError("observation_count must match rows")
    if report.pass_count != pass_count:
        raise ValueError("pass_count must match rows")
    if report.watch_count != watch_count:
        raise ValueError("watch_count must match rows")
    if report.blocked_count != blocked_count:
        raise ValueError("blocked_count must match rows")
    if row_count != report.pass_count + report.watch_count + report.blocked_count:
        raise ValueError("status counts must match observation_count")

    if not report.rows:
        if report.status != "pass":
            raise ValueError("empty report status must be pass")
        if report.top_market_slug is not None:
            raise ValueError("empty report top_market_slug must be None")
        if report.reason_codes != (_EMPTY_REASON_CODE,):
            raise ValueError("empty report reason_codes must mark no observations")
        if report.reason_code_counts != ((_EMPTY_REASON_CODE, _ONE),):
            raise ValueError("empty report reason_code_counts must mark no observations")
        return

    if report.status != _report_status(watch_count, blocked_count):
        raise ValueError("status must match row statuses")
    if report.top_market_slug != report.rows[0].market_slug:
        raise ValueError("top_market_slug must match highest risk row")
    if report.total_affected_capacity != sum(
        (row.affected_capacity for row in report.rows),
        _ZERO,
    ):
        raise ValueError("total_affected_capacity must match rows")
    if report.max_nomination_cut_percent != max(
        row.nomination_cut_percent for row in report.rows
    ):
        raise ValueError("max_nomination_cut_percent must match rows")
    if report.min_storage_buffer_days != min(
        row.storage_buffer_days for row in report.rows
    ):
        raise ValueError("min_storage_buffer_days must match rows")
    if report.max_demand_temperature_anomaly_f != max(
        _abs_decimal(row.demand_temperature_anomaly_f) for row in report.rows
    ):
        raise ValueError("max_demand_temperature_anomaly_f must match rows")
    if report.max_outage_duration_hours != max(
        row.outage_duration_hours for row in report.rows
    ):
        raise ValueError("max_outage_duration_hours must match rows")
    if report.risk_score != max(row.risk_score for row in report.rows):
        raise ValueError("risk_score must match rows")
    expected_average = _quantize_decimal(
        sum((row.risk_score for row in report.rows), _ZERO)
        / _decimal_count(len(report.rows)),
    )
    if report.average_risk_score != expected_average:
        raise ValueError("average_risk_score must match rows")
    expected_reasons = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_counts(expected_reasons, report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.upstream_reason_code_counts != _upstream_reason_counts(report.rows):
        raise ValueError("upstream_reason_code_counts must match rows")


def _validate_row_consistency(row: EnergyPipelineNominationCutDigestRow) -> None:
    has_pass = _PASS_REASON_CODE in row.reason_codes
    has_blocked = any(code in _BLOCKED_REASON_CODES for code in row.reason_codes)
    has_watch = any(code in _WATCH_REASON_CODES for code in row.reason_codes)
    if has_pass and row.reason_codes != (_PASS_REASON_CODE,):
        raise ValueError("reason_codes must not mix pass with active reasons")
    if row.status == "pass":
        if row.reason_codes != (_PASS_REASON_CODE,):
            raise ValueError("status must match reason_codes")
        return
    if has_pass:
        raise ValueError("reason_codes must match status")
    if row.status == "watch":
        if has_blocked or not has_watch:
            raise ValueError("status must match reason_codes")
        return
    if not has_blocked:
        raise ValueError("status must match reason_codes")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return _decimal_string(value)
    if type(value) is datetime:
        return _as_utc_datetime("datetime value", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for name, item in value.items():
            if type(name) is not str:
                raise ValueError("mapping names must be strings")
            ready[name] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not serializable")


def _decimal_string(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("Decimal value must be finite")
    return format(_quantize_checked("Decimal value", value), "f")


def _reject_unsafe_payload_names(label: str, value: object) -> None:
    for name in _iter_payload_names(value):
        lowered = name.lower()
        if any(fragment in lowered for fragment in _UNSAFE_NAME_FRAGMENTS):
            raise ValueError(f"unsafe live surface field in {label}: {name}")


def _iter_payload_names(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_payload_names(asdict(value))
    if isinstance(value, dict):
        names: list[str] = []
        for name, item in value.items():
            if type(name) is not str:
                raise ValueError("mapping names must be strings")
            names.append(name)
            names.extend(_iter_payload_names(item))
        return tuple(names)
    if isinstance(value, (list, tuple)):
        names: list[str] = []
        for item in value:
            names.extend(_iter_payload_names(item))
        return tuple(names)
    return ()


def _reject_flag_downgrades(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_flag_downgrades(label, asdict(value))
        return
    if isinstance(value, dict):
        for name, item in value.items():
            if name in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{name} must be True in {label}")
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _reject_sensitive_public_text(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_sensitive_public_text(label, asdict(value))
        return
    if type(value) is str:
        _reject_sensitive_text(label, value)
        return
    if isinstance(value, dict):
        for name, item in value.items():
            if type(name) is not str:
                raise ValueError("mapping names must be strings")
            _reject_sensitive_text(label, name)
            _reject_sensitive_public_text(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_sensitive_public_text(label, item)


def _reject_sensitive_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _SENSITIVE_TEXT_FRAGMENTS):
        raise ValueError(f"sensitive value in {field_name}")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "PHASE_NAME",
    "EnergyPipelineNominationCutDigestReport",
    "EnergyPipelineNominationCutDigestRow",
    "EnergyPipelineNominationCutObservation",
    "EnergyPipelineNominationCutThresholds",
    "build_market_research_energy_pipeline_nomination_cut_digest_report",
    "market_research_energy_pipeline_nomination_cut_digest_payload",
)
