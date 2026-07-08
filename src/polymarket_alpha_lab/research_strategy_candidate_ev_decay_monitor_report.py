"""Report-only monitor for candidate EV decay as research inputs age."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
from typing import Any, Mapping


DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EV_DECAY_MONITOR_REPORT_VERSION = (
    "research-strategy-candidate-ev-decay-monitor-report-v1"
)
MONITOR_STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_COUNT_QUANT = Decimal("1")
_UNSAFE_PUBLIC_TERMS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "question",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "source_text",
    "raw_text",
)
_REASON_CODE_ORDER = (
    "decayed_ev_pass",
    "decayed_ev_watch",
    "decayed_ev_block",
    "evidence_age_penalty",
    "cost_move_penalty",
    "liquidity_weakness_penalty",
    "confidence_haircut_penalty",
    "resolution_ambiguity_penalty",
)


@dataclass(frozen=True)
class ResearchStrategyCandidateEvDecayMonitorConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EV_DECAY_MONITOR_REPORT_VERSION
    evidence_half_life_seconds: Decimal = Decimal("3600.000000")
    minimum_decayed_ev_bps: Decimal = Decimal("20.000000")
    watch_decay_ratio: Decimal = Decimal("0.500000")
    liquidity_weakness_penalty_bps: Decimal = Decimal("100.000000")
    confidence_haircut_penalty_bps: Decimal = Decimal("100.000000")
    resolution_ambiguity_penalty_bps: Decimal = Decimal("100.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCandidateEvDecayMonitorConfig:
            raise TypeError(
                "ResearchStrategyCandidateEvDecayMonitorConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateEvDecayMonitorConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyCandidateEvDecayMonitorConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EV_DECAY_MONITOR_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "evidence_half_life_seconds",
            _require_positive_decimal(
                "evidence_half_life_seconds",
                self.evidence_half_life_seconds,
            ),
        )
        object.__setattr__(
            self,
            "minimum_decayed_ev_bps",
            _require_nonnegative_decimal(
                "minimum_decayed_ev_bps",
                self.minimum_decayed_ev_bps,
            ),
        )
        object.__setattr__(
            self,
            "watch_decay_ratio",
            _require_nonnegative_decimal("watch_decay_ratio", self.watch_decay_ratio),
        )
        for name in (
            "liquidity_weakness_penalty_bps",
            "confidence_haircut_penalty_bps",
            "resolution_ambiguity_penalty_bps",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateEvDecayMonitorObservation:
    candidate_key: str
    scope_key: str
    observed_at: datetime
    expected_value_bps: Decimal
    cost_bps: Decimal
    liquidity_score: Decimal
    confidence_haircut: Decimal
    resolution_ambiguity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCandidateEvDecayMonitorObservation:
            raise TypeError(
                "ResearchStrategyCandidateEvDecayMonitorObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateEvDecayMonitorObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchStrategyCandidateEvDecayMonitorObservation",
            )
        _require_canonical_string("candidate_key", self.candidate_key)
        _require_canonical_string("scope_key", self.scope_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "expected_value_bps",
            _require_decimal("expected_value_bps", self.expected_value_bps),
        )
        object.__setattr__(
            self,
            "cost_bps",
            _require_nonnegative_decimal("cost_bps", self.cost_bps),
        )
        for name in ("liquidity_score", "confidence_haircut", "resolution_ambiguity"):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateEvDecayMonitorRow:
    candidate_ref: str
    scope_ref: str
    observation_count: Decimal
    latest_observed_at: datetime
    evidence_age_seconds: Decimal
    starting_expected_value_bps: Decimal
    latest_expected_value_bps: Decimal
    observed_ev_decay_bps: Decimal
    evidence_age_penalty_bps: Decimal
    cost_move_bps: Decimal
    liquidity_weakening_bps: Decimal
    confidence_haircut_rise_bps: Decimal
    resolution_ambiguity_change_bps: Decimal
    total_decay_bps: Decimal
    decay_ratio: Decimal
    decayed_ev_bps: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCandidateEvDecayMonitorRow:
            raise TypeError(
                "ResearchStrategyCandidateEvDecayMonitorRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateEvDecayMonitorRow:
            raise ValueError("row must be exactly ResearchStrategyCandidateEvDecayMonitorRow")
        _require_canonical_string("candidate_ref", self.candidate_ref)
        _require_canonical_string("scope_ref", self.scope_ref)
        object.__setattr__(
            self,
            "observation_count",
            _require_positive_count_decimal("observation_count", self.observation_count),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for name in (
            "evidence_age_seconds",
            "observed_ev_decay_bps",
            "evidence_age_penalty_bps",
            "cost_move_bps",
            "liquidity_weakening_bps",
            "confidence_haircut_rise_bps",
            "resolution_ambiguity_change_bps",
            "total_decay_bps",
            "decay_ratio",
        ):
            object.__setattr__(self, name, _require_nonnegative_decimal(name, getattr(self, name)))
        for name in (
            "starting_expected_value_bps",
            "latest_expected_value_bps",
            "decayed_ev_bps",
        ):
            object.__setattr__(self, name, _require_decimal(name, getattr(self, name)))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        digest = _row_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != digest:
                raise ValueError("derived_validation_digest does not match row payload")
        else:
            object.__setattr__(self, "derived_validation_digest", digest)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(_row_public_map(self, include_digest=True))
        if type(payload) is not dict:
            raise ValueError("row payload must be a dict")
        return payload


@dataclass(frozen=True)
class ResearchStrategyCandidateEvDecayMonitorReport:
    generated_at: datetime
    config_version: str
    report_status: str
    observation_count: Decimal
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_decayed_ev_bps: Decimal
    max_total_decay_bps: Decimal
    rows: tuple[ResearchStrategyCandidateEvDecayMonitorRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCandidateEvDecayMonitorReport:
            raise TypeError(
                "ResearchStrategyCandidateEvDecayMonitorReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateEvDecayMonitorReport:
            raise ValueError(
                "report must be exactly ResearchStrategyCandidateEvDecayMonitorReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EV_DECAY_MONITOR_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("report_status", self.report_status)
        for name in (
            "observation_count",
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_count_decimal(name, getattr(self, name)),
            )
        for name in ("average_decayed_ev_bps", "max_total_decay_bps"):
            object.__setattr__(self, name, _require_decimal(name, getattr(self, name)))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != digest:
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_candidate_ev_decay_monitor_report_payload(self)


def build_research_strategy_candidate_ev_decay_monitor_report(
    observations: object,
    *,
    config: ResearchStrategyCandidateEvDecayMonitorConfig,
    generated_at: datetime,
) -> ResearchStrategyCandidateEvDecayMonitorReport:
    """Build a local report-only EV decay monitor without action recommendations."""

    if type(config) is not ResearchStrategyCandidateEvDecayMonitorConfig:
        raise ValueError("config must be a ResearchStrategyCandidateEvDecayMonitorConfig")
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    if not isinstance(observations, (list, tuple)):
        raise ValueError("observations must be a list or tuple")
    generated_at = _as_utc("generated_at", generated_at)

    normalized: list[ResearchStrategyCandidateEvDecayMonitorObservation] = []
    seen: set[tuple[str, str, datetime]] = set()
    for item in observations:
        if type(item) is not ResearchStrategyCandidateEvDecayMonitorObservation:
            raise ValueError(
                "observations must contain "
                "ResearchStrategyCandidateEvDecayMonitorObservation values",
            )
        _require_hard_flags("observation", item)
        _reject_unsafe_public_payload("observation", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (item.candidate_key, item.scope_key, item.observed_at)
        if key in seen:
            raise ValueError("duplicate observation")
        seen.add(key)
        normalized.append(item)

    rows = tuple(
        _row_from_observations(items, config=config, generated_at=generated_at)
        for items in _observation_groups(normalized)
    )
    return ResearchStrategyCandidateEvDecayMonitorReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_status=_report_status(rows),
        observation_count=_decimal_count(len(normalized)),
        candidate_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_decayed_ev_bps=_average(tuple(row.decayed_ev_bps for row in rows)),
        max_total_decay_bps=_max_or_zero(tuple(row.total_decay_bps for row in rows)),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_strategy_candidate_ev_decay_monitor_report_payload(
    value: ResearchStrategyCandidateEvDecayMonitorReport | Mapping[str, object],
) -> dict[str, object]:
    """Return a deterministic JSON-ready payload and validate SHA-256 digests."""

    if type(value) is ResearchStrategyCandidateEvDecayMonitorReport:
        _require_hard_flags("report", value)
        _reject_unsafe_public_payload("report", value)
        payload = _json_ready(_report_public_map(value, include_digest=True))
    elif isinstance(value, Mapping):
        payload = _json_ready(dict(value))
    else:
        raise ValueError(
            "value must be a ResearchStrategyCandidateEvDecayMonitorReport or payload dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_digest(payload)
    return payload


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


def _row_from_observations(
    items: tuple[ResearchStrategyCandidateEvDecayMonitorObservation, ...],
    *,
    config: ResearchStrategyCandidateEvDecayMonitorConfig,
    generated_at: datetime,
) -> ResearchStrategyCandidateEvDecayMonitorRow:
    ordered = tuple(sorted(items, key=lambda item: (item.observed_at, item.scope_key)))
    first = ordered[0]
    latest = ordered[-1]
    evidence_age_seconds = _age_seconds(latest.observed_at, generated_at)
    observed_ev_decay_bps = _clamp_nonnegative(
        first.expected_value_bps - latest.expected_value_bps,
    )
    evidence_age_penalty_bps = _clamp_nonnegative(
        latest.expected_value_bps
        * evidence_age_seconds
        / (config.evidence_half_life_seconds + evidence_age_seconds),
    )
    cost_move_bps = _clamp_nonnegative(latest.cost_bps - first.cost_bps)
    liquidity_weakening_bps = _clamp_nonnegative(
        (first.liquidity_score - latest.liquidity_score)
        * config.liquidity_weakness_penalty_bps,
    )
    confidence_haircut_rise_bps = _clamp_nonnegative(
        (latest.confidence_haircut - first.confidence_haircut)
        * config.confidence_haircut_penalty_bps,
    )
    resolution_ambiguity_change_bps = _clamp_nonnegative(
        (latest.resolution_ambiguity - first.resolution_ambiguity)
        * config.resolution_ambiguity_penalty_bps,
    )
    total_decay_bps = _clamp_nonnegative(
        observed_ev_decay_bps
        + evidence_age_penalty_bps
        + cost_move_bps
        + liquidity_weakening_bps
        + confidence_haircut_rise_bps
        + resolution_ambiguity_change_bps,
    )
    decay_ratio = _decay_ratio(total_decay_bps, first.expected_value_bps)
    decayed_ev_bps = _quantize(first.expected_value_bps - total_decay_bps)
    status = _row_status(
        decayed_ev_bps=decayed_ev_bps,
        decay_ratio=decay_ratio,
        config=config,
    )
    return ResearchStrategyCandidateEvDecayMonitorRow(
        candidate_ref=_public_ref("candidate", first.candidate_key),
        scope_ref=_public_ref("scope", first.scope_key),
        observation_count=_decimal_count(len(ordered)),
        latest_observed_at=latest.observed_at,
        evidence_age_seconds=evidence_age_seconds,
        starting_expected_value_bps=first.expected_value_bps,
        latest_expected_value_bps=latest.expected_value_bps,
        observed_ev_decay_bps=observed_ev_decay_bps,
        evidence_age_penalty_bps=evidence_age_penalty_bps,
        cost_move_bps=cost_move_bps,
        liquidity_weakening_bps=liquidity_weakening_bps,
        confidence_haircut_rise_bps=confidence_haircut_rise_bps,
        resolution_ambiguity_change_bps=resolution_ambiguity_change_bps,
        total_decay_bps=total_decay_bps,
        decay_ratio=decay_ratio,
        decayed_ev_bps=decayed_ev_bps,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            evidence_age_penalty_bps=evidence_age_penalty_bps,
            cost_move_bps=cost_move_bps,
            liquidity_weakening_bps=liquidity_weakening_bps,
            confidence_haircut_rise_bps=confidence_haircut_rise_bps,
            resolution_ambiguity_change_bps=resolution_ambiguity_change_bps,
        ),
    )


def _observation_groups(
    observations: list[ResearchStrategyCandidateEvDecayMonitorObservation],
) -> tuple[tuple[ResearchStrategyCandidateEvDecayMonitorObservation, ...], ...]:
    buckets: dict[tuple[str, str], list[ResearchStrategyCandidateEvDecayMonitorObservation]] = {}
    for item in observations:
        buckets.setdefault((item.candidate_key, item.scope_key), []).append(item)
    return tuple(
        tuple(
            sorted(
                buckets[key],
                key=lambda item: (item.observed_at, item.candidate_key, item.scope_key),
            ),
        )
        for key in sorted(buckets)
    )


def _row_status(
    *,
    decayed_ev_bps: Decimal,
    decay_ratio: Decimal,
    config: ResearchStrategyCandidateEvDecayMonitorConfig,
) -> str:
    if decayed_ev_bps <= _ZERO:
        return "block"
    if decayed_ev_bps < config.minimum_decayed_ev_bps:
        return "watch"
    if decay_ratio >= config.watch_decay_ratio:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchStrategyCandidateEvDecayMonitorRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    evidence_age_penalty_bps: Decimal,
    cost_move_bps: Decimal,
    liquidity_weakening_bps: Decimal,
    confidence_haircut_rise_bps: Decimal,
    resolution_ambiguity_change_bps: Decimal,
) -> tuple[str, ...]:
    codes = [f"decayed_ev_{status}"]
    if evidence_age_penalty_bps > _ZERO:
        codes.append("evidence_age_penalty")
    if cost_move_bps > _ZERO:
        codes.append("cost_move_penalty")
    if liquidity_weakening_bps > _ZERO:
        codes.append("liquidity_weakness_penalty")
    if confidence_haircut_rise_bps > _ZERO:
        codes.append("confidence_haircut_penalty")
    if resolution_ambiguity_change_bps > _ZERO:
        codes.append("resolution_ambiguity_penalty")
    return _normalize_reason_codes(tuple(codes))


def _report_reason_codes(
    rows: tuple[ResearchStrategyCandidateEvDecayMonitorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("decayed_ev_pass",)
    return _normalize_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _validate_row_consistency(row: ResearchStrategyCandidateEvDecayMonitorRow) -> None:
    expected_total = _clamp_nonnegative(
        row.observed_ev_decay_bps
        + row.evidence_age_penalty_bps
        + row.cost_move_bps
        + row.liquidity_weakening_bps
        + row.confidence_haircut_rise_bps
        + row.resolution_ambiguity_change_bps,
    )
    if row.total_decay_bps != expected_total:
        raise ValueError("total_decay_bps must match row components")
    if row.decay_ratio != _decay_ratio(row.total_decay_bps, row.starting_expected_value_bps):
        raise ValueError("decay_ratio must match total decay and starting EV")
    if row.decayed_ev_bps != _quantize(row.starting_expected_value_bps - row.total_decay_bps):
        raise ValueError("decayed_ev_bps must match starting EV and total decay")


def _validate_report_consistency(report: ResearchStrategyCandidateEvDecayMonitorReport) -> None:
    if report.observation_count != _require_nonnegative_count_decimal(
        "observation_count",
        sum((row.observation_count for row in report.rows), _ZERO),
    ):
        raise ValueError("observation_count must match rows")
    if report.candidate_count != _decimal_count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.average_decayed_ev_bps != _average(
        tuple(row.decayed_ev_bps for row in report.rows),
    ):
        raise ValueError("average_decayed_ev_bps must match rows")
    if report.max_total_decay_bps != _max_or_zero(
        tuple(row.total_decay_bps for row in report.rows),
    ):
        raise ValueError("max_total_decay_bps must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _row_public_map(
    row: ResearchStrategyCandidateEvDecayMonitorRow,
    *,
    include_digest: bool,
) -> dict[str, object]:
    result: dict[str, object] = {
        "candidate_ref": row.candidate_ref,
        "scope_ref": row.scope_ref,
        "observation_count": row.observation_count,
        "latest_observed_at": row.latest_observed_at,
        "evidence_age_seconds": row.evidence_age_seconds,
        "starting_expected_value_bps": row.starting_expected_value_bps,
        "latest_expected_value_bps": row.latest_expected_value_bps,
        "observed_ev_decay_bps": row.observed_ev_decay_bps,
        "evidence_age_penalty_bps": row.evidence_age_penalty_bps,
        "cost_move_bps": row.cost_move_bps,
        "liquidity_weakening_bps": row.liquidity_weakening_bps,
        "confidence_haircut_rise_bps": row.confidence_haircut_rise_bps,
        "resolution_ambiguity_change_bps": row.resolution_ambiguity_change_bps,
        "total_decay_bps": row.total_decay_bps,
        "decay_ratio": row.decay_ratio,
        "decayed_ev_bps": row.decayed_ev_bps,
        "status": row.status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    if include_digest:
        result["derived_validation_digest"] = row.derived_validation_digest
    return result


def _report_public_map(
    report: ResearchStrategyCandidateEvDecayMonitorReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    result: dict[str, object] = {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "report_status": report.report_status,
        "observation_count": report.observation_count,
        "candidate_count": report.candidate_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "average_decayed_ev_bps": report.average_decayed_ev_bps,
        "max_total_decay_bps": report.max_total_decay_bps,
        "rows": tuple(_row_public_map(row, include_digest=True) for row in report.rows),
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        result["derived_validation_digest"] = report.derived_validation_digest
    return result


def _row_digest(row: ResearchStrategyCandidateEvDecayMonitorRow) -> str:
    return _digest("row", _json_ready(_row_public_map(row, include_digest=False)))


def _report_digest(report: ResearchStrategyCandidateEvDecayMonitorReport) -> str:
    return _digest("report", _json_ready(_report_public_map(report, include_digest=False)))


def _require_payload_digest(payload: Mapping[str, object]) -> None:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain dict values")
        digest = row.get("derived_validation_digest")
        _require_sha256_digest("derived_validation_digest", digest)
        row_base = {key: item for key, item in row.items() if key != "derived_validation_digest"}
        if digest != _digest("row", row_base):
            raise ValueError("derived_validation_digest does not match row payload")

    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    report_base = {
        key: item for key, item in payload.items() if key != "derived_validation_digest"
    }
    if digest != _digest("report", report_base):
        raise ValueError("derived_validation_digest does not match report payload")


def _digest(label: str, value: object) -> str:
    payload = _json_ready(value)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(label.encode("utf-8") + b"\n" + encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("JSON numeric values must use Decimal-derived strings")
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_rows(value: object) -> tuple[ResearchStrategyCandidateEvDecayMonitorRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchStrategyCandidateEvDecayMonitorRow:
            raise ValueError("rows must contain ResearchStrategyCandidateEvDecayMonitorRow")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("reason_codes must be a sequence")
    seen: set[str] = set()
    normalized: list[str] = []
    allowed = set(_REASON_CODE_ORDER)
    for item in value:
        _require_canonical_string("reason_codes", item)
        if item not in allowed:
            raise ValueError("reason_codes contain unsupported value")
        if item not in seen:
            seen.add(item)
            normalized.append(item)
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    normalized.sort(key=_REASON_CODE_ORDER.index)
    return tuple(normalized)


def _status_count(
    rows: tuple[ResearchStrategyCandidateEvDecayMonitorRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _max_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(max(values))


def _age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - observed_at).total_seconds()))
    return _require_nonnegative_decimal("evidence_age_seconds", seconds)


def _decay_ratio(total_decay_bps: Decimal, starting_expected_value_bps: Decimal) -> Decimal:
    if starting_expected_value_bps <= _ZERO:
        return _ZERO
    return _require_nonnegative_decimal("decay_ratio", total_decay_bps / starting_expected_value_bps)


def _public_ref(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _require_hard_flags(label: str, value: object) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        if getattr(value, name, None) is not True:
            raise ValueError(f"{label} {name} must be True")


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in MONITOR_STATUSES:
        raise ValueError(f"{name} must be one of pass, watch, block")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    if _has_unsafe_public_term(value):
        raise ValueError(f"{name} contains unsafe public text")


def _require_sha256_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a SHA-256 digest")


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < _ZERO or decimal > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal


def _require_positive_count_decimal(name: str, value: object) -> Decimal:
    decimal = _require_nonnegative_count_decimal(name, value)
    if decimal <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal


def _require_nonnegative_count_decimal(name: str, value: object) -> Decimal:
    decimal = _require_nonnegative_decimal(name, value)
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{name} must be a whole-number Decimal")
    return decimal.quantize(_COUNT_QUANT)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_COUNT_QUANT)


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.rounding = ROUND_HALF_UP
        return value.quantize(_QUANT)


def _clamp_nonnegative(value: Decimal) -> Decimal:
    return _quantize(max(value, _ZERO))


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, Decimal):
        _require_decimal(path or label, value)
        return
    if type(value) is datetime:
        _as_utc(path or label, value)
        return
    if type(value) is int or type(value) is float:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is str:
        if _has_unsafe_public_term(value):
            raise ValueError(f"{path or label} contains unsafe public text")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_term(key):
                raise ValueError(f"{key} is an unsafe public field")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not a safe public payload value")


def _has_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _UNSAFE_PUBLIC_TERMS)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EV_DECAY_MONITOR_REPORT_VERSION",
    "MONITOR_STATUSES",
    "ResearchStrategyCandidateEvDecayMonitorConfig",
    "ResearchStrategyCandidateEvDecayMonitorObservation",
    "ResearchStrategyCandidateEvDecayMonitorRow",
    "ResearchStrategyCandidateEvDecayMonitorReport",
    "build_research_strategy_candidate_ev_decay_monitor_report",
    "research_strategy_candidate_ev_decay_monitor_report_payload",
)
