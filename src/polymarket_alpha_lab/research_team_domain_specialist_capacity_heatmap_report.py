"""Report-only heatmap for team-domain specialist capacity pressure."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_CAPACITY_HEATMAP_CONFIG_VERSION = (
    "research-team-domain-specialist-capacity-heatmap-report-v0"
)
CAPACITY_HEATMAP_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")

PASS_REASON = "capacity_heatmap_domain_clear"
EMPTY_REASON = "capacity_heatmap_no_domains"
REPORT_REASON_BY_STATUS = {
    "pass": "capacity_heatmap_report_pass",
    "watch": "capacity_heatmap_report_watch",
    "block": "capacity_heatmap_report_block",
}
MODE_BY_STATUS = {
    "pass": "paper_capacity_heatmap_monitor",
    "watch": "paper_capacity_heatmap_watch",
    "block": "paper_capacity_heatmap_block",
}
ROW_REASON_SEQUENCE = (
    "capacity_heatmap_active_review_load_block",
    "capacity_heatmap_backlog_urgency_block",
    "capacity_heatmap_calibration_freshness_block",
    "capacity_heatmap_evidence_gap_pressure_block",
    "capacity_heatmap_cross_domain_conflict_volume_block",
    "capacity_heatmap_score_block",
    "capacity_heatmap_active_review_load_watch",
    "capacity_heatmap_backlog_urgency_watch",
    "capacity_heatmap_calibration_freshness_watch",
    "capacity_heatmap_evidence_gap_pressure_watch",
    "capacity_heatmap_cross_domain_conflict_volume_watch",
    "capacity_heatmap_score_watch",
    PASS_REASON,
)
REPORT_REASON_SEQUENCE = (
    "capacity_heatmap_report_block",
    "capacity_heatmap_report_watch",
    "capacity_heatmap_report_pass",
    EMPTY_REASON,
) + ROW_REASON_SEQUENCE[:-1]
REASON_COUNT_SEQUENCE = (EMPTY_REASON,) + ROW_REASON_SEQUENCE


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("r", "aw"),
        _join_parts("candi", "date"),
        _join_parts("mar", "ket"),
        _join_parts("sl", "ug"),
        _join_parts("ques", "tion"),
        _join_parts("u", "rl"),
        _join_parts("ht", "tp://"),
        _join_parts("ht", "tps://"),
        _join_parts("so", "urce"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("creden", "tial"),
        _join_parts("pass", "word"),
        _join_parts("private", "_", "key"),
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("or", "der"),
        _join_parts("tr", "ade"),
        _join_parts("trad", "ing"),
        _join_parts("li", "ve"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("recom", "mendation"),
        _join_parts("siz", "ing"),
        "position",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_CAPACITY_HEATMAP_CONFIG_VERSION",
    "CAPACITY_HEATMAP_STATUSES",
    "ResearchTeamDomainSpecialistCapacityHeatmapConfig",
    "ResearchTeamDomainSpecialistCapacityHeatmapReasonCodeCount",
    "ResearchTeamDomainSpecialistCapacityHeatmapReport",
    "ResearchTeamDomainSpecialistCapacityHeatmapRow",
    "ResearchTeamDomainSpecialistCapacityHeatmapSignal",
    "build_research_team_domain_specialist_capacity_heatmap_report",
    "research_team_domain_specialist_capacity_heatmap_report_digest",
    "research_team_domain_specialist_capacity_heatmap_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistCapacityHeatmapConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_CAPACITY_HEATMAP_CONFIG_VERSION
    )
    watch_active_review_load_ratio: Decimal = Decimal("0.750000")
    block_active_review_load_ratio: Decimal = Decimal("1.000000")
    watch_backlog_urgency_ratio: Decimal = Decimal("0.500000")
    block_backlog_urgency_ratio: Decimal = Decimal("0.800000")
    watch_calibration_age_seconds: Decimal = Decimal("604800.000000")
    block_calibration_age_seconds: Decimal = Decimal("1209600.000000")
    watch_evidence_gap_pressure: Decimal = Decimal("0.250000")
    block_evidence_gap_pressure: Decimal = Decimal("0.500000")
    watch_cross_domain_conflict_count: Decimal = Decimal("2.000000")
    block_cross_domain_conflict_count: Decimal = Decimal("4.000000")
    active_review_load_weight: Decimal = Decimal("0.250000")
    backlog_urgency_weight: Decimal = Decimal("0.200000")
    calibration_freshness_weight: Decimal = Decimal("0.200000")
    evidence_gap_pressure_weight: Decimal = Decimal("0.200000")
    cross_domain_conflict_weight: Decimal = Decimal("0.150000")
    watch_heatmap_score: Decimal = Decimal("0.500000")
    block_heatmap_score: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSpecialistCapacityHeatmapConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_CAPACITY_HEATMAP_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_active_review_load_ratio",
            "block_active_review_load_ratio",
            "watch_backlog_urgency_ratio",
            "block_backlog_urgency_ratio",
            "watch_evidence_gap_pressure",
            "block_evidence_gap_pressure",
            "active_review_load_weight",
            "backlog_urgency_weight",
            "calibration_freshness_weight",
            "evidence_gap_pressure_weight",
            "cross_domain_conflict_weight",
            "watch_heatmap_score",
            "block_heatmap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_calibration_age_seconds",
            "block_calibration_age_seconds",
            "watch_cross_domain_conflict_count",
            "block_cross_domain_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistCapacityHeatmapSignal(_FinalPublicDataclass):
    team_label: str
    domain_label: str
    specialist_label: str
    active_review_count: Decimal
    review_capacity_count: Decimal
    urgent_backlog_count: Decimal
    backlog_item_count: Decimal
    latest_calibration_at: datetime
    required_evidence_count: Decimal
    observed_evidence_count: Decimal
    cross_domain_conflict_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSpecialistCapacityHeatmapSignal,
            "input",
        )
        for field_name in ("team_label", "domain_label", "specialist_label"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "active_review_count",
            "urgent_backlog_count",
            "cross_domain_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "review_capacity_count",
            "backlog_item_count",
            "required_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "observed_evidence_count",
            _require_count_decimal(
                "observed_evidence_count",
                self.observed_evidence_count,
            ),
        )
        if self.urgent_backlog_count > self.backlog_item_count:
            raise ValueError("urgent_backlog_count must not exceed backlog_item_count")
        if self.observed_evidence_count > self.required_evidence_count:
            raise ValueError(
                "observed_evidence_count must not exceed required_evidence_count",
            )
        object.__setattr__(
            self,
            "latest_calibration_at",
            _as_utc("latest_calibration_at", self.latest_calibration_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistCapacityHeatmapRow(_FinalPublicDataclass):
    domain_label: str
    status: str
    team_count: Decimal
    specialist_count: Decimal
    active_review_count: Decimal
    review_capacity_count: Decimal
    active_review_load_ratio: Decimal
    urgent_backlog_count: Decimal
    backlog_item_count: Decimal
    backlog_urgency_ratio: Decimal
    calibration_age_seconds: Decimal
    required_evidence_count: Decimal
    observed_evidence_count: Decimal
    evidence_gap_count: Decimal
    evidence_gap_pressure: Decimal
    cross_domain_conflict_count: Decimal
    capacity_score: Decimal
    observed_at: datetime
    observation_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSpecialistCapacityHeatmapRow,
            "row",
        )
        _require_public_label("domain_label", self.domain_label)
        _require_status("status", self.status)
        for field_name in (
            "team_count",
            "specialist_count",
            "active_review_count",
            "review_capacity_count",
            "urgent_backlog_count",
            "backlog_item_count",
            "required_evidence_count",
            "observed_evidence_count",
            "evidence_gap_count",
            "cross_domain_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.review_capacity_count <= ZERO:
            raise ValueError("review_capacity_count must be positive")
        if self.backlog_item_count <= ZERO:
            raise ValueError("backlog_item_count must be positive")
        if self.required_evidence_count <= ZERO:
            raise ValueError("required_evidence_count must be positive")
        if self.urgent_backlog_count > self.backlog_item_count:
            raise ValueError("urgent_backlog_count must not exceed backlog_item_count")
        if self.observed_evidence_count > self.required_evidence_count:
            raise ValueError(
                "observed_evidence_count must not exceed required_evidence_count",
            )
        for field_name in (
            "active_review_load_ratio",
            "backlog_urgency_ratio",
            "calibration_age_seconds",
            "observation_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_gap_pressure", "capacity_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistCapacityHeatmapReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSpecialistCapacityHeatmapReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        if self.reason_code not in REASON_COUNT_SEQUENCE:
            raise ValueError("reason_code must be supported")
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "domain_ratio",
            _require_ratio_decimal("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistCapacityHeatmapReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    heatmap_mode: str
    domain_count: Decimal
    team_count: Decimal
    specialist_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_capacity_score: Decimal
    max_capacity_score: Decimal
    average_active_review_load_ratio: Decimal
    max_active_review_load_ratio: Decimal
    average_backlog_urgency_ratio: Decimal
    max_backlog_urgency_ratio: Decimal
    average_calibration_age_seconds: Decimal
    max_calibration_age_seconds: Decimal
    average_evidence_gap_pressure: Decimal
    max_evidence_gap_pressure: Decimal
    total_cross_domain_conflict_count: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamDomainSpecialistCapacityHeatmapReasonCodeCount, ...]
    rows: tuple[ResearchTeamDomainSpecialistCapacityHeatmapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSpecialistCapacityHeatmapReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_CAPACITY_HEATMAP_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        _require_public_string("heatmap_mode", self.heatmap_mode)
        for field_name in (
            "domain_count",
            "team_count",
            "specialist_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_cross_domain_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_active_review_load_ratio",
            "max_active_review_load_ratio",
            "average_backlog_urgency_ratio",
            "max_backlog_urgency_ratio",
            "average_calibration_age_seconds",
            "max_calibration_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_capacity_score",
            "max_capacity_score",
            "average_evidence_gap_pressure",
            "max_evidence_gap_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError(
                    "derived_validation_digest does not match report payload",
                )

    @property
    def public_payload(self) -> dict[str, object]:
        return research_team_domain_specialist_capacity_heatmap_report_payload(self)


def build_research_team_domain_specialist_capacity_heatmap_report(
    signals: Iterable[ResearchTeamDomainSpecialistCapacityHeatmapSignal],
    *,
    config: ResearchTeamDomainSpecialistCapacityHeatmapConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSpecialistCapacityHeatmapReport:
    _require_exact_type(
        config,
        ResearchTeamDomainSpecialistCapacityHeatmapConfig,
        "config",
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    for signal in normalized_signals:
        if signal.latest_calibration_at > generated_at_utc:
            raise ValueError("latest_calibration_at must not be in the future")
        if signal.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be in the future")
    rows = tuple(
        sorted(
            (
                _row_from_domain_signals(
                    domain_label=domain_label,
                    signals=tuple(
                        signal
                        for signal in normalized_signals
                        if signal.domain_label == domain_label
                    ),
                    config=config,
                    generated_at=generated_at_utc,
                )
                for domain_label in _domain_labels(normalized_signals)
            ),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return ResearchTeamDomainSpecialistCapacityHeatmapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        heatmap_mode=MODE_BY_STATUS[status],
        domain_count=_count(len(rows)),
        team_count=_count(len({signal.team_label for signal in normalized_signals})),
        specialist_count=_count(
            len(
                {
                    (signal.domain_label, signal.specialist_label)
                    for signal in normalized_signals
                },
            ),
        ),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_capacity_score=_average_decimal(row.capacity_score for row in rows),
        max_capacity_score=_max_decimal(tuple(row.capacity_score for row in rows)),
        average_active_review_load_ratio=_average_decimal(
            row.active_review_load_ratio for row in rows
        ),
        max_active_review_load_ratio=_max_decimal(
            tuple(row.active_review_load_ratio for row in rows)
        ),
        average_backlog_urgency_ratio=_average_decimal(
            row.backlog_urgency_ratio for row in rows
        ),
        max_backlog_urgency_ratio=_max_decimal(
            tuple(row.backlog_urgency_ratio for row in rows)
        ),
        average_calibration_age_seconds=_average_decimal(
            row.calibration_age_seconds for row in rows
        ),
        max_calibration_age_seconds=_max_decimal(
            tuple(row.calibration_age_seconds for row in rows)
        ),
        average_evidence_gap_pressure=_average_decimal(
            row.evidence_gap_pressure for row in rows
        ),
        max_evidence_gap_pressure=_max_decimal(
            tuple(row.evidence_gap_pressure for row in rows)
        ),
        total_cross_domain_conflict_count=sum(
            (row.cross_domain_conflict_count for row in rows),
            ZERO,
        ).quantize(QUANTUM),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_domain_specialist_capacity_heatmap_report_payload(
    report: ResearchTeamDomainSpecialistCapacityHeatmapReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamDomainSpecialistCapacityHeatmapReport:
        _require_hard_flags("report", report)
        if report.derived_validation_digest != _digest_from_values(
            _report_values_without_digest(report),
        ):
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report(report)
        payload = _json_ready(report)
    elif isinstance(report, Mapping):
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainSpecialistCapacityHeatmapReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_payload_flags(payload)
    _reject_public_numeric_values(payload)
    _reject_unsafe_public_payload(
        "report payload",
        payload,
        allow_json_containers=True,
    )
    expected_digest = _digest_from_payload(payload)
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def research_team_domain_specialist_capacity_heatmap_report_digest(
    report: ResearchTeamDomainSpecialistCapacityHeatmapReport | Mapping[str, object],
) -> str:
    payload = research_team_domain_specialist_capacity_heatmap_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _row_from_domain_signals(
    *,
    domain_label: str,
    signals: tuple[ResearchTeamDomainSpecialistCapacityHeatmapSignal, ...],
    config: ResearchTeamDomainSpecialistCapacityHeatmapConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSpecialistCapacityHeatmapRow:
    active_review_count = _sum_decimal(signal.active_review_count for signal in signals)
    review_capacity_count = _sum_decimal(
        signal.review_capacity_count for signal in signals
    )
    urgent_backlog_count = _sum_decimal(signal.urgent_backlog_count for signal in signals)
    backlog_item_count = _sum_decimal(signal.backlog_item_count for signal in signals)
    required_evidence_count = _sum_decimal(
        signal.required_evidence_count for signal in signals
    )
    observed_evidence_count = _sum_decimal(
        signal.observed_evidence_count for signal in signals
    )
    evidence_gap_count = _quantize(required_evidence_count - observed_evidence_count)
    cross_domain_conflict_count = _sum_decimal(
        signal.cross_domain_conflict_count for signal in signals
    )
    latest_calibration_at = min(signal.latest_calibration_at for signal in signals)
    observed_at = max(signal.observed_at for signal in signals)
    active_review_load_ratio = _ratio_uncapped(
        active_review_count,
        review_capacity_count,
    )
    backlog_urgency_ratio = _ratio_uncapped(urgent_backlog_count, backlog_item_count)
    calibration_age_seconds = _datetime_delta_seconds(
        generated_at,
        latest_calibration_at,
    )
    evidence_gap_pressure = _ratio_capped(
        evidence_gap_count,
        required_evidence_count,
    )
    capacity_score = _capacity_score(
        active_review_load_ratio=active_review_load_ratio,
        backlog_urgency_ratio=backlog_urgency_ratio,
        calibration_age_seconds=calibration_age_seconds,
        evidence_gap_pressure=evidence_gap_pressure,
        cross_domain_conflict_count=cross_domain_conflict_count,
        config=config,
    )
    reason_codes = _row_reason_codes(
        active_review_load_ratio=active_review_load_ratio,
        backlog_urgency_ratio=backlog_urgency_ratio,
        calibration_age_seconds=calibration_age_seconds,
        evidence_gap_pressure=evidence_gap_pressure,
        cross_domain_conflict_count=cross_domain_conflict_count,
        capacity_score=capacity_score,
        config=config,
    )
    return ResearchTeamDomainSpecialistCapacityHeatmapRow(
        domain_label=domain_label,
        status=_row_status(reason_codes),
        team_count=_count(len({signal.team_label for signal in signals})),
        specialist_count=_count(len({signal.specialist_label for signal in signals})),
        active_review_count=active_review_count,
        review_capacity_count=review_capacity_count,
        active_review_load_ratio=active_review_load_ratio,
        urgent_backlog_count=urgent_backlog_count,
        backlog_item_count=backlog_item_count,
        backlog_urgency_ratio=backlog_urgency_ratio,
        calibration_age_seconds=calibration_age_seconds,
        required_evidence_count=required_evidence_count,
        observed_evidence_count=observed_evidence_count,
        evidence_gap_count=evidence_gap_count,
        evidence_gap_pressure=evidence_gap_pressure,
        cross_domain_conflict_count=cross_domain_conflict_count,
        capacity_score=capacity_score,
        observed_at=observed_at,
        observation_age_seconds=_datetime_delta_seconds(generated_at, observed_at),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    active_review_load_ratio: Decimal,
    backlog_urgency_ratio: Decimal,
    calibration_age_seconds: Decimal,
    evidence_gap_pressure: Decimal,
    cross_domain_conflict_count: Decimal,
    capacity_score: Decimal,
    config: ResearchTeamDomainSpecialistCapacityHeatmapConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_high_threshold_reason(
        reasons,
        metric=active_review_load_ratio,
        watch=config.watch_active_review_load_ratio,
        block=config.block_active_review_load_ratio,
        watch_code="capacity_heatmap_active_review_load_watch",
        block_code="capacity_heatmap_active_review_load_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=backlog_urgency_ratio,
        watch=config.watch_backlog_urgency_ratio,
        block=config.block_backlog_urgency_ratio,
        watch_code="capacity_heatmap_backlog_urgency_watch",
        block_code="capacity_heatmap_backlog_urgency_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=calibration_age_seconds,
        watch=config.watch_calibration_age_seconds,
        block=config.block_calibration_age_seconds,
        watch_code="capacity_heatmap_calibration_freshness_watch",
        block_code="capacity_heatmap_calibration_freshness_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=evidence_gap_pressure,
        watch=config.watch_evidence_gap_pressure,
        block=config.block_evidence_gap_pressure,
        watch_code="capacity_heatmap_evidence_gap_pressure_watch",
        block_code="capacity_heatmap_evidence_gap_pressure_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=cross_domain_conflict_count,
        watch=config.watch_cross_domain_conflict_count,
        block=config.block_cross_domain_conflict_count,
        watch_code="capacity_heatmap_cross_domain_conflict_volume_watch",
        block_code="capacity_heatmap_cross_domain_conflict_volume_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=capacity_score,
        watch=config.watch_heatmap_score,
        block=config.block_heatmap_score,
        watch_code="capacity_heatmap_score_watch",
        block_code="capacity_heatmap_score_block",
    )
    if not reasons:
        return (PASS_REASON,)
    ordered_reasons = tuple(reason for reason in ROW_REASON_SEQUENCE if reason in reasons)
    return _require_row_reason_codes(ordered_reasons)


def _append_high_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric >= block:
        reasons.append(block_code)
        return
    if metric >= watch:
        reasons.append(watch_code)


def _capacity_score(
    *,
    active_review_load_ratio: Decimal,
    backlog_urgency_ratio: Decimal,
    calibration_age_seconds: Decimal,
    evidence_gap_pressure: Decimal,
    cross_domain_conflict_count: Decimal,
    config: ResearchTeamDomainSpecialistCapacityHeatmapConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _ratio_capped(
            _ratio_to_cap(
                active_review_load_ratio,
                config.block_active_review_load_ratio,
            )
            * config.active_review_load_weight
            + _ratio_to_cap(backlog_urgency_ratio, config.block_backlog_urgency_ratio)
            * config.backlog_urgency_weight
            + _ratio_to_cap(
                calibration_age_seconds,
                config.block_calibration_age_seconds,
            )
            * config.calibration_freshness_weight
            + _ratio_to_cap(evidence_gap_pressure, config.block_evidence_gap_pressure)
            * config.evidence_gap_pressure_weight
            + _ratio_to_cap(
                cross_domain_conflict_count,
                config.block_cross_domain_conflict_count,
            )
            * config.cross_domain_conflict_weight,
            ONE,
        )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchTeamDomainSpecialistCapacityHeatmapRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainSpecialistCapacityHeatmapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    status = _report_status(rows)
    present = {reason for row in rows for reason in row.reason_codes}
    reasons = [REPORT_REASON_BY_STATUS[status]]
    reasons.extend(reason for reason in ROW_REASON_SEQUENCE[:-1] if reason in present)
    return tuple(reasons)


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainSpecialistCapacityHeatmapRow, ...],
) -> tuple[ResearchTeamDomainSpecialistCapacityHeatmapReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamDomainSpecialistCapacityHeatmapReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=COUNT_ONE,
                domain_ratio=ONE,
            ),
        )
    domain_count = _count(len(rows))
    return tuple(
        ResearchTeamDomainSpecialistCapacityHeatmapReasonCodeCount(
            reason_code=reason,
            count=_count(
                sum(1 for row in rows if reason in row.reason_codes),
            ),
            domain_ratio=_ratio_capped(
                _count(sum(1 for row in rows if reason in row.reason_codes)),
                domain_count,
            ),
        )
        for reason in REASON_COUNT_SEQUENCE
        if any(reason in row.reason_codes for row in rows)
    )


def _row_sort_key(
    row: ResearchTeamDomainSpecialistCapacityHeatmapRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        -_status_rank(row.status),
        -row.capacity_score,
        -row.active_review_load_ratio,
        -row.backlog_urgency_ratio,
        row.domain_label,
    )


def _status_rank(status: str) -> int:
    if status == "block":
        return 2
    if status == "watch":
        return 1
    return 0


def _status_count(
    rows: tuple[ResearchTeamDomainSpecialistCapacityHeatmapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _domain_labels(
    signals: tuple[ResearchTeamDomainSpecialistCapacityHeatmapSignal, ...],
) -> tuple[str, ...]:
    return tuple(sorted({signal.domain_label for signal in signals}))


def _normalize_signals(
    signals: Iterable[ResearchTeamDomainSpecialistCapacityHeatmapSignal],
) -> tuple[ResearchTeamDomainSpecialistCapacityHeatmapSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        rows = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen_signal_keys: set[tuple[str, str, str]] = set()
    for signal in rows:
        _require_exact_type(
            signal,
            ResearchTeamDomainSpecialistCapacityHeatmapSignal,
            "input",
        )
        _require_hard_flags("input", signal)
        signal_key = (signal.team_label, signal.domain_label, signal.specialist_label)
        if signal_key in seen_signal_keys:
            raise ValueError("signals must have unique team domain specialist keys")
        seen_signal_keys.add(signal_key)
    return tuple(sorted(rows, key=lambda row: (row.domain_label, row.team_label, row.specialist_label)))


def _require_rows(
    rows: object,
) -> tuple[ResearchTeamDomainSpecialistCapacityHeatmapRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_domains: set[str] = set()
    for row in normalized:
        _require_exact_type(
            row,
            ResearchTeamDomainSpecialistCapacityHeatmapRow,
            "row",
        )
        _require_hard_flags("row", row)
        if row.domain_label in seen_domains:
            raise ValueError("rows must have unique domain labels")
        seen_domains.add(row.domain_label)
    return tuple(sorted(normalized, key=_row_sort_key))


def _require_reason_code_counts(
    reason_code_counts: object,
) -> tuple[ResearchTeamDomainSpecialistCapacityHeatmapReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(reason_code_counts)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_reasons: set[str] = set()
    for item in normalized:
        _require_exact_type(
            item,
            ResearchTeamDomainSpecialistCapacityHeatmapReasonCodeCount,
            "reason_code_count",
        )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen_reasons:
            raise ValueError("reason_code_counts must have unique reason codes")
        seen_reasons.add(item.reason_code)
    return tuple(
        sorted(
            normalized,
            key=lambda item: REASON_COUNT_SEQUENCE.index(item.reason_code),
        ),
    )


def _validate_config(
    config: ResearchTeamDomainSpecialistCapacityHeatmapConfig,
) -> None:
    _require_watch_not_above_block(
        "active_review_load_ratio",
        config.watch_active_review_load_ratio,
        config.block_active_review_load_ratio,
    )
    _require_watch_not_above_block(
        "backlog_urgency_ratio",
        config.watch_backlog_urgency_ratio,
        config.block_backlog_urgency_ratio,
    )
    _require_watch_not_above_block(
        "calibration_age_seconds",
        config.watch_calibration_age_seconds,
        config.block_calibration_age_seconds,
    )
    _require_watch_not_above_block(
        "evidence_gap_pressure",
        config.watch_evidence_gap_pressure,
        config.block_evidence_gap_pressure,
    )
    _require_watch_not_above_block(
        "cross_domain_conflict_count",
        config.watch_cross_domain_conflict_count,
        config.block_cross_domain_conflict_count,
    )
    if config.watch_heatmap_score > config.block_heatmap_score:
        raise ValueError("watch_heatmap_score must not exceed block_heatmap_score")
    weight_total = sum(
        (
            config.active_review_load_weight,
            config.backlog_urgency_weight,
            config.calibration_freshness_weight,
            config.evidence_gap_pressure_weight,
            config.cross_domain_conflict_weight,
        ),
        ZERO,
    ).quantize(QUANTUM)
    if weight_total != ONE:
        raise ValueError("capacity heatmap weights must sum to 1.000000")


def _require_watch_not_above_block(
    label: str,
    watch: Decimal,
    block: Decimal,
) -> None:
    if watch > block:
        raise ValueError(f"watch_{label} must not exceed block_{label}")


def _validate_row(row: ResearchTeamDomainSpecialistCapacityHeatmapRow) -> None:
    if row.evidence_gap_count != _quantize(
        row.required_evidence_count - row.observed_evidence_count,
    ):
        raise ValueError("evidence_gap_count must match required minus observed")
    if row.active_review_load_ratio != _ratio_uncapped(
        row.active_review_count,
        row.review_capacity_count,
    ):
        raise ValueError("active_review_load_ratio must match active over capacity")
    if row.backlog_urgency_ratio != _ratio_uncapped(
        row.urgent_backlog_count,
        row.backlog_item_count,
    ):
        raise ValueError("backlog_urgency_ratio must match urgent over backlog")
    if row.evidence_gap_pressure != _ratio_capped(
        row.evidence_gap_count,
        row.required_evidence_count,
    ):
        raise ValueError("evidence_gap_pressure must match evidence gap ratio")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(
    report: ResearchTeamDomainSpecialistCapacityHeatmapReport,
) -> None:
    rows = report.rows
    if report.domain_count != _count(len(rows)):
        raise ValueError("domain_count must match rows")
    if report.team_count < report.domain_count and rows:
        raise ValueError("team_count must cover rows")
    if report.specialist_count < report.domain_count and rows:
        raise ValueError("specialist_count must cover rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_capacity_score != _average_decimal(
        row.capacity_score for row in rows
    ):
        raise ValueError("average_capacity_score must match rows")
    if report.max_capacity_score != _max_decimal(tuple(row.capacity_score for row in rows)):
        raise ValueError("max_capacity_score must match rows")
    if report.average_active_review_load_ratio != _average_decimal(
        row.active_review_load_ratio for row in rows
    ):
        raise ValueError("average_active_review_load_ratio must match rows")
    if report.max_active_review_load_ratio != _max_decimal(
        tuple(row.active_review_load_ratio for row in rows)
    ):
        raise ValueError("max_active_review_load_ratio must match rows")
    if report.average_backlog_urgency_ratio != _average_decimal(
        row.backlog_urgency_ratio for row in rows
    ):
        raise ValueError("average_backlog_urgency_ratio must match rows")
    if report.max_backlog_urgency_ratio != _max_decimal(
        tuple(row.backlog_urgency_ratio for row in rows)
    ):
        raise ValueError("max_backlog_urgency_ratio must match rows")
    if report.average_calibration_age_seconds != _average_decimal(
        row.calibration_age_seconds for row in rows
    ):
        raise ValueError("average_calibration_age_seconds must match rows")
    if report.max_calibration_age_seconds != _max_decimal(
        tuple(row.calibration_age_seconds for row in rows)
    ):
        raise ValueError("max_calibration_age_seconds must match rows")
    if report.average_evidence_gap_pressure != _average_decimal(
        row.evidence_gap_pressure for row in rows
    ):
        raise ValueError("average_evidence_gap_pressure must match rows")
    if report.max_evidence_gap_pressure != _max_decimal(
        tuple(row.evidence_gap_pressure for row in rows)
    ):
        raise ValueError("max_evidence_gap_pressure must match rows")
    if report.total_cross_domain_conflict_count != sum(
        (row.cross_domain_conflict_count for row in rows),
        ZERO,
    ).quantize(QUANTUM):
        raise ValueError("total_cross_domain_conflict_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.heatmap_mode != MODE_BY_STATUS[report.status]:
        raise ValueError("heatmap_mode must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_row_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason in normalized:
        _require_public_string("reason_code", reason)
        if reason not in ROW_REASON_SEQUENCE:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if tuple(reason for reason in ROW_REASON_SEQUENCE if reason in normalized) != normalized:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _require_report_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason in normalized:
        _require_public_string("reason_code", reason)
        if reason not in REPORT_REASON_SEQUENCE:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if tuple(reason for reason in REPORT_REASON_SEQUENCE if reason in normalized) != normalized:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _status_from_string(value: object) -> str:
    if type(value) is not str or value not in CAPACITY_HEATMAP_STATUSES:
        raise ValueError("status must be pass, watch, or block")
    return value


def _require_status(field_name: str, value: object) -> str:
    try:
        return _status_from_string(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be pass, watch, or block") from exc


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public aggregate label")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public aggregate label")
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public aggregate label")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical public string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized.quantize(Decimal("1")) != normalized:
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_flags(payload: dict[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if field_name not in payload or payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload contains unsafe numeric value")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("unsafe public payload Decimal")
        return
    if type(value) is datetime:
        _as_utc(label, value)
        return
    if value is None or type(value) is bool:
        return
    if allow_json_containers and type(value) in (int, float):
        raise ValueError("public payload contains unsafe numeric value")
    raise ValueError("unsafe public payload")


def _reject_unsafe_public_key(label: str, key: str) -> None:
    del label
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload key")


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("JSON value must not be numeric")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _report_values_without_digest(
    report: ResearchTeamDomainSpecialistCapacityHeatmapReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return _digest_from_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned_payload = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        unsigned_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    later_utc = _as_utc("later", later)
    earlier_utc = _as_utc("earlier", earlier)
    if earlier_utc >= later_utc:
        return ZERO
    delta = later_utc - earlier_utc
    seconds = (
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / Decimal("1000000")
    )
    return _quantize(seconds)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return sum(values, ZERO).quantize(QUANTUM)


def _ratio_uncapped(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _ratio_capped(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        ratio = _quantize(numerator / denominator)
    if ratio < ZERO:
        return ZERO
    if ratio > ONE:
        return ONE
    return ratio


def _ratio_to_cap(metric: Decimal, cap: Decimal) -> Decimal:
    return _ratio_capped(metric, cap)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)
