"""Pure Phase 1 playbook for research-packet source disagreement resolution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_PACKET_SOURCE_DISAGREEMENT_RESOLUTION_PLAYBOOK_V2_CONFIG_VERSION = (
    "research-packet-source-disagreement-resolution-playbook-v2"
)

DISAGREEMENT_STATUSES = ("open", "resolved")
REPORT_STATUSES = ("clear", "watch", "blocked")
PLAYBOOK_STATUSES = ("blocked", "watch")
FOLLOWUP_SOURCE_FAMILIES = (
    "official_resolution_source",
    "primary_source_trace",
    "independent_source_family",
    "rule_text_trace",
    "settlement_evidence",
)
ESCALATION_REASONS = (
    "missing_resolution_owner",
    "stale_source_disagreement",
)
MINIMUM_EVIDENCE_GAPS = (
    "missing_official_resolution_source",
    "missing_primary_source_trace",
    "independent_source_family_count_below_minimum",
    "missing_rule_text_trace",
    "missing_settlement_evidence",
)
REASON_CODES = (
    "open_source_disagreement",
    "official_resolution_source_followup_required",
    "primary_source_trace_followup_required",
    "independent_source_family_gap",
    "rule_text_trace_gap",
    "settlement_evidence_gap",
    "missing_resolution_owner",
    "stale_source_disagreement",
)
STATUS_WEIGHT = {
    "blocked": 0,
    "watch": 1,
}
COUNT_QUANT = Decimal("1")
SECONDS_QUANT = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_SECONDS = Decimal("0.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=28)


@dataclass(frozen=True)
class ResearchPacketSourceDisagreementResolutionPlaybookConfig:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_SOURCE_DISAGREEMENT_RESOLUTION_PLAYBOOK_V2_CONFIG_VERSION
    )
    min_independent_source_family_count: Decimal = Decimal("3")
    stale_disagreement_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceDisagreementResolutionPlaybookConfig:
            raise ValueError(
                "config must be a "
                "ResearchPacketSourceDisagreementResolutionPlaybookConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_independent_source_family_count",
            _normalize_positive_count_decimal(
                "min_independent_source_family_count",
                self.min_independent_source_family_count,
            ),
        )
        object.__setattr__(
            self,
            "stale_disagreement_age_seconds",
            _normalize_positive_seconds_decimal(
                "stale_disagreement_age_seconds",
                self.stale_disagreement_age_seconds,
            ),
        )
        require_paper_only_flags("config", self)
        reject_unsafe_surface_fields("config", self)


@dataclass(frozen=True)
class ResearchPacketSourceDisagreementInput:
    packet_ref: str
    market_slug: str
    disagreement_id: str
    disagreement_status: str
    source_families: tuple[str, ...]
    disputed_outcome_keys: tuple[str, ...]
    observed_at: datetime
    has_official_resolution_source: bool
    has_primary_source_trace: bool
    has_rule_text_trace: bool
    has_settlement_evidence: bool
    resolution_owner: str | None
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceDisagreementInput:
            raise ValueError("source row must be a ResearchPacketSourceDisagreementInput")
        for field_name in (
            "packet_ref",
            "market_slug",
            "disagreement_id",
            "source_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_disagreement_status("disagreement_status", self.disagreement_status)
        object.__setattr__(
            self,
            "source_families",
            _normalize_public_string_tuple(
                "source_families",
                self.source_families,
                minimum_count=1,
            ),
        )
        object.__setattr__(
            self,
            "disputed_outcome_keys",
            _normalize_public_string_tuple(
                "disputed_outcome_keys",
                self.disputed_outcome_keys,
                minimum_count=2,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "has_official_resolution_source",
            "has_primary_source_trace",
            "has_rule_text_trace",
            "has_settlement_evidence",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "resolution_owner",
            _normalize_optional_string("resolution_owner", self.resolution_owner),
        )
        require_paper_only_flags("source row", self)
        reject_unsafe_surface_fields("source row", self)


@dataclass(frozen=True)
class ResearchPacketSourceDisagreementResolutionPlaybookRow:
    packet_ref: str
    market_slug: str
    disagreement_id: str
    playbook_status: str
    source_families: tuple[str, ...]
    disputed_outcome_keys: tuple[str, ...]
    source_family_count: Decimal
    disputed_outcome_count: Decimal
    disagreement_age_seconds: Decimal
    required_followup_source_families: tuple[str, ...]
    escalation_reasons: tuple[str, ...]
    minimum_evidence_gaps: tuple[str, ...]
    reason_codes: tuple[str, ...]
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceDisagreementResolutionPlaybookRow:
            raise ValueError(
                "playbook row must be a "
                "ResearchPacketSourceDisagreementResolutionPlaybookRow",
            )
        for field_name in (
            "packet_ref",
            "market_slug",
            "disagreement_id",
            "source_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_playbook_status("playbook_status", self.playbook_status)
        object.__setattr__(
            self,
            "source_families",
            _normalize_public_string_tuple(
                "source_families",
                self.source_families,
                minimum_count=1,
            ),
        )
        object.__setattr__(
            self,
            "disputed_outcome_keys",
            _normalize_public_string_tuple(
                "disputed_outcome_keys",
                self.disputed_outcome_keys,
                minimum_count=2,
            ),
        )
        object.__setattr__(
            self,
            "source_family_count",
            _normalize_count_decimal("source_family_count", self.source_family_count),
        )
        object.__setattr__(
            self,
            "disputed_outcome_count",
            _normalize_count_decimal("disputed_outcome_count", self.disputed_outcome_count),
        )
        object.__setattr__(
            self,
            "disagreement_age_seconds",
            _normalize_seconds_decimal(
                "disagreement_age_seconds",
                self.disagreement_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "required_followup_source_families",
            _normalize_ordered_members(
                "required_followup_source_families",
                self.required_followup_source_families,
                FOLLOWUP_SOURCE_FAMILIES,
            ),
        )
        object.__setattr__(
            self,
            "escalation_reasons",
            _normalize_ordered_members(
                "escalation_reasons",
                self.escalation_reasons,
                ESCALATION_REASONS,
            ),
        )
        object.__setattr__(
            self,
            "minimum_evidence_gaps",
            _normalize_ordered_members(
                "minimum_evidence_gaps",
                self.minimum_evidence_gaps,
                MINIMUM_EVIDENCE_GAPS,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_ordered_members("reason_codes", self.reason_codes, REASON_CODES),
        )
        require_paper_only_flags("playbook row", self)
        reject_unsafe_surface_fields("playbook row", self)
        _validate_playbook_row(self)


@dataclass(frozen=True)
class ResearchPacketSourceDisagreementResolutionPlaybookReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    source_row_count: Decimal
    open_disagreement_count: Decimal
    blocked_playbook_count: Decimal
    watch_playbook_count: Decimal
    official_followup_required_count: Decimal
    primary_followup_required_count: Decimal
    independent_family_gap_count: Decimal
    rule_text_gap_count: Decimal
    settlement_evidence_gap_count: Decimal
    owner_escalation_count: Decimal
    stale_disagreement_count: Decimal
    max_disagreement_age_seconds: Decimal
    rows: tuple[ResearchPacketSourceDisagreementResolutionPlaybookRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceDisagreementResolutionPlaybookReport:
            raise ValueError(
                "report must be a "
                "ResearchPacketSourceDisagreementResolutionPlaybookReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_ordered_members("reason_codes", self.reason_codes, REASON_CODES),
        )
        for field_name in (
            "source_row_count",
            "open_disagreement_count",
            "blocked_playbook_count",
            "watch_playbook_count",
            "official_followup_required_count",
            "primary_followup_required_count",
            "independent_family_gap_count",
            "rule_text_gap_count",
            "settlement_evidence_gap_count",
            "owner_escalation_count",
            "stale_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_disagreement_age_seconds",
            _normalize_seconds_decimal(
                "max_disagreement_age_seconds",
                self.max_disagreement_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_playbook_rows(self.rows))
        require_paper_only_flags("report", self)
        reject_unsafe_surface_fields("report", self)
        _validate_report(self)


def build_research_packet_source_disagreement_resolution_playbook_v2(
    disagreement_rows: object,
    *,
    config: ResearchPacketSourceDisagreementResolutionPlaybookConfig,
    generated_at: datetime,
) -> ResearchPacketSourceDisagreementResolutionPlaybookReport:
    if type(config) is not ResearchPacketSourceDisagreementResolutionPlaybookConfig:
        raise ValueError(
            "config must be a ResearchPacketSourceDisagreementResolutionPlaybookConfig",
        )
    require_paper_only_flags("config", config)
    reject_unsafe_surface_fields("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_source_rows(
        disagreement_rows,
        generated_at=generated_at_utc,
    )
    open_rows = tuple(row for row in source_rows if row.disagreement_status == "open")
    playbook_rows = _normalize_playbook_rows(
        tuple(
            _playbook_row(row, config=config, generated_at=generated_at_utc)
            for row in open_rows
        ),
    )

    reason_codes = _report_reason_codes(playbook_rows)
    return ResearchPacketSourceDisagreementResolutionPlaybookReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(playbook_rows),
        reason_codes=reason_codes,
        source_row_count=_decimal_count(len(source_rows)),
        open_disagreement_count=_decimal_count(len(open_rows)),
        blocked_playbook_count=_status_count(playbook_rows, "blocked"),
        watch_playbook_count=_status_count(playbook_rows, "watch"),
        official_followup_required_count=_followup_count(
            playbook_rows,
            "official_resolution_source",
        ),
        primary_followup_required_count=_followup_count(
            playbook_rows,
            "primary_source_trace",
        ),
        independent_family_gap_count=_reason_count(
            playbook_rows,
            "independent_source_family_gap",
        ),
        rule_text_gap_count=_reason_count(playbook_rows, "rule_text_trace_gap"),
        settlement_evidence_gap_count=_reason_count(
            playbook_rows,
            "settlement_evidence_gap",
        ),
        owner_escalation_count=_escalation_count(
            playbook_rows,
            "missing_resolution_owner",
        ),
        stale_disagreement_count=_escalation_count(
            playbook_rows,
            "stale_source_disagreement",
        ),
        max_disagreement_age_seconds=max(
            (row.disagreement_age_seconds for row in playbook_rows),
            default=ZERO_SECONDS,
        ),
        rows=playbook_rows,
    )


def research_packet_source_disagreement_resolution_playbook_v2_payload(
    report: ResearchPacketSourceDisagreementResolutionPlaybookReport,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketSourceDisagreementResolutionPlaybookReport:
        raise ValueError(
            "report must be a ResearchPacketSourceDisagreementResolutionPlaybookReport",
        )
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report must convert to a JSON object")
    reject_unsafe_surface_fields("report payload", payload)
    return payload


def _playbook_row(
    row: ResearchPacketSourceDisagreementInput,
    *,
    config: ResearchPacketSourceDisagreementResolutionPlaybookConfig,
    generated_at: datetime,
) -> ResearchPacketSourceDisagreementResolutionPlaybookRow:
    age_seconds = _age_seconds(generated_at, row.observed_at)
    source_family_count = _decimal_count(len(row.source_families))
    required_followups: list[str] = []
    evidence_gaps: list[str] = []
    escalation_reasons: list[str] = []
    reason_codes = ["open_source_disagreement"]

    if not row.has_official_resolution_source:
        required_followups.append("official_resolution_source")
        evidence_gaps.append("missing_official_resolution_source")
        reason_codes.append("official_resolution_source_followup_required")
    if not row.has_primary_source_trace:
        required_followups.append("primary_source_trace")
        evidence_gaps.append("missing_primary_source_trace")
        reason_codes.append("primary_source_trace_followup_required")
    if source_family_count < config.min_independent_source_family_count:
        required_followups.append("independent_source_family")
        evidence_gaps.append("independent_source_family_count_below_minimum")
        reason_codes.append("independent_source_family_gap")
    if not row.has_rule_text_trace:
        required_followups.append("rule_text_trace")
        evidence_gaps.append("missing_rule_text_trace")
        reason_codes.append("rule_text_trace_gap")
    if not row.has_settlement_evidence:
        required_followups.append("settlement_evidence")
        evidence_gaps.append("missing_settlement_evidence")
        reason_codes.append("settlement_evidence_gap")
    if row.resolution_owner is None:
        escalation_reasons.append("missing_resolution_owner")
        reason_codes.append("missing_resolution_owner")
    if age_seconds >= config.stale_disagreement_age_seconds:
        escalation_reasons.append("stale_source_disagreement")
        reason_codes.append("stale_source_disagreement")

    return ResearchPacketSourceDisagreementResolutionPlaybookRow(
        packet_ref=row.packet_ref,
        market_slug=row.market_slug,
        disagreement_id=row.disagreement_id,
        playbook_status=_playbook_status(
            required_followups=tuple(required_followups),
            escalation_reasons=tuple(escalation_reasons),
        ),
        source_families=row.source_families,
        disputed_outcome_keys=row.disputed_outcome_keys,
        source_family_count=source_family_count,
        disputed_outcome_count=_decimal_count(len(row.disputed_outcome_keys)),
        disagreement_age_seconds=age_seconds,
        required_followup_source_families=tuple(required_followups),
        escalation_reasons=tuple(escalation_reasons),
        minimum_evidence_gaps=tuple(evidence_gaps),
        reason_codes=tuple(reason_codes),
        source_config_version=row.source_config_version,
    )


def _playbook_status(
    *,
    required_followups: tuple[str, ...],
    escalation_reasons: tuple[str, ...],
) -> str:
    if required_followups or "missing_resolution_owner" in escalation_reasons:
        return "blocked"
    return "watch"


def _report_status(
    rows: tuple[ResearchPacketSourceDisagreementResolutionPlaybookRow, ...],
) -> str:
    if not rows:
        return "clear"
    if any(row.playbook_status == "blocked" for row in rows):
        return "blocked"
    return "watch"


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceDisagreementResolutionPlaybookRow, ...],
) -> tuple[str, ...]:
    observed = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in observed)


def _normalize_source_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchPacketSourceDisagreementInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("disagreement_rows must be a list or tuple")
    rows = tuple(value)
    seen_refs: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketSourceDisagreementInput:
            raise ValueError(
                "disagreement_rows must contain "
                "ResearchPacketSourceDisagreementInput values",
            )
        require_paper_only_flags("source row", row)
        reject_unsafe_surface_fields("source row", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        ref = (row.packet_ref, row.disagreement_id)
        if ref in seen_refs:
            raise ValueError("disagreement_id values must be unique per packet_ref")
        seen_refs.add(ref)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.packet_ref,
                row.market_slug,
                row.disagreement_id,
            ),
        ),
    )


def _normalize_playbook_rows(
    value: object,
) -> tuple[ResearchPacketSourceDisagreementResolutionPlaybookRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_refs: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketSourceDisagreementResolutionPlaybookRow:
            raise ValueError("rows must contain exact playbook rows")
        require_paper_only_flags("playbook row", row)
        reject_unsafe_surface_fields("playbook row", row)
        ref = (row.packet_ref, row.disagreement_id)
        if ref in seen_refs:
            raise ValueError("rows must be unique per packet_ref")
        seen_refs.add(ref)
    return tuple(sorted(rows, key=_playbook_row_key))


def _playbook_row_key(
    row: ResearchPacketSourceDisagreementResolutionPlaybookRow,
) -> tuple[int, Decimal, str, str, str]:
    return (
        STATUS_WEIGHT[row.playbook_status],
        -row.disagreement_age_seconds,
        row.packet_ref,
        row.market_slug,
        row.disagreement_id,
    )


def _validate_playbook_row(
    row: ResearchPacketSourceDisagreementResolutionPlaybookRow,
) -> None:
    if row.source_family_count != _decimal_count(len(row.source_families)):
        raise ValueError("source_family_count must match source_families")
    if row.disputed_outcome_count != _decimal_count(len(row.disputed_outcome_keys)):
        raise ValueError("disputed_outcome_count must match disputed_outcome_keys")
    _require_gap_bundle(
        row,
        followup="official_resolution_source",
        gap="missing_official_resolution_source",
        reason="official_resolution_source_followup_required",
    )
    _require_gap_bundle(
        row,
        followup="primary_source_trace",
        gap="missing_primary_source_trace",
        reason="primary_source_trace_followup_required",
    )
    _require_gap_bundle(
        row,
        followup="independent_source_family",
        gap="independent_source_family_count_below_minimum",
        reason="independent_source_family_gap",
    )
    _require_gap_bundle(
        row,
        followup="rule_text_trace",
        gap="missing_rule_text_trace",
        reason="rule_text_trace_gap",
    )
    _require_gap_bundle(
        row,
        followup="settlement_evidence",
        gap="missing_settlement_evidence",
        reason="settlement_evidence_gap",
    )
    for escalation_reason in ESCALATION_REASONS:
        if (escalation_reason in row.escalation_reasons) != (
            escalation_reason in row.reason_codes
        ):
            raise ValueError("escalation_reasons must match reason_codes")
    if "open_source_disagreement" not in row.reason_codes:
        raise ValueError("reason_codes must include open_source_disagreement")
    if row.playbook_status != _playbook_status(
        required_followups=row.required_followup_source_families,
        escalation_reasons=row.escalation_reasons,
    ):
        raise ValueError("playbook_status must match followups and escalations")


def _require_gap_bundle(
    row: ResearchPacketSourceDisagreementResolutionPlaybookRow,
    *,
    followup: str,
    gap: str,
    reason: str,
) -> None:
    has_followup = followup in row.required_followup_source_families
    if (gap in row.minimum_evidence_gaps) != has_followup:
        raise ValueError("minimum_evidence_gaps must match followups")
    if (reason in row.reason_codes) != has_followup:
        raise ValueError("reason_codes must match followups")


def _validate_report(
    report: ResearchPacketSourceDisagreementResolutionPlaybookReport,
) -> None:
    if report.open_disagreement_count > report.source_row_count:
        raise ValueError("open_disagreement_count must not exceed source_row_count")
    if report.open_disagreement_count != _decimal_count(len(report.rows)):
        raise ValueError("open_disagreement_count must match rows")
    if report.blocked_playbook_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_playbook_count must match rows")
    if report.watch_playbook_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_playbook_count must match rows")
    if report.official_followup_required_count != _followup_count(
        report.rows,
        "official_resolution_source",
    ):
        raise ValueError("official_followup_required_count must match rows")
    if report.primary_followup_required_count != _followup_count(
        report.rows,
        "primary_source_trace",
    ):
        raise ValueError("primary_followup_required_count must match rows")
    if report.independent_family_gap_count != _reason_count(
        report.rows,
        "independent_source_family_gap",
    ):
        raise ValueError("independent_family_gap_count must match rows")
    if report.rule_text_gap_count != _reason_count(report.rows, "rule_text_trace_gap"):
        raise ValueError("rule_text_gap_count must match rows")
    if report.settlement_evidence_gap_count != _reason_count(
        report.rows,
        "settlement_evidence_gap",
    ):
        raise ValueError("settlement_evidence_gap_count must match rows")
    if report.owner_escalation_count != _escalation_count(
        report.rows,
        "missing_resolution_owner",
    ):
        raise ValueError("owner_escalation_count must match rows")
    if report.stale_disagreement_count != _escalation_count(
        report.rows,
        "stale_source_disagreement",
    ):
        raise ValueError("stale_disagreement_count must match rows")
    expected_max_age = max(
        (row.disagreement_age_seconds for row in report.rows),
        default=ZERO_SECONDS,
    )
    if report.max_disagreement_age_seconds != expected_max_age:
        raise ValueError("max_disagreement_age_seconds must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status == "clear":
        if report.rows:
            raise ValueError("clear reports must not have rows")
        if report.reason_codes:
            raise ValueError("clear reports must not have reason_codes")


def _status_count(
    rows: tuple[ResearchPacketSourceDisagreementResolutionPlaybookRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.playbook_status == status))


def _followup_count(
    rows: tuple[ResearchPacketSourceDisagreementResolutionPlaybookRow, ...],
    source_family: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if source_family in row.required_followup_source_families),
    )


def _reason_count(
    rows: tuple[ResearchPacketSourceDisagreementResolutionPlaybookRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _escalation_count(
    rows: tuple[ResearchPacketSourceDisagreementResolutionPlaybookRow, ...],
    escalation_reason: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if escalation_reason in row.escalation_reasons),
    )


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = _as_utc("generated_at", generated_at) - _as_utc("observed_at", observed_at)
    with localcontext(DECIMAL_CONTEXT):
        age_seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    if age_seconds < ZERO_SECONDS:
        raise ValueError("observed_at must not be in the future")
    return _normalize_seconds_decimal("disagreement_age_seconds", age_seconds)


def _decimal_count(value: int) -> Decimal:
    return _normalize_count_decimal("count", Decimal(value))


def _normalize_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count_decimal(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    try:
        return value.quantize(COUNT_QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _normalize_positive_seconds_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_seconds_decimal(field_name, value)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_seconds_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(SECONDS_QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _normalize_public_string_tuple(
    field_name: str,
    value: object,
    *,
    minimum_count: int,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(value)
    if len(normalized) < minimum_count:
        raise ValueError(f"{field_name} must contain at least {minimum_count} values")
    for item in normalized:
        _require_canonical_string(field_name, item)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} values must be unique")
    return tuple(sorted(normalized))


def _normalize_ordered_members(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    values = tuple(value)
    for item in values:
        _require_canonical_string(field_name, item)
        if item not in allowed:
            raise ValueError(f"{field_name} must contain known values")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} values must be unique")
    if tuple(item for item in allowed if item in values) != values:
        raise ValueError(f"{field_name} must be deterministic")
    return values


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_optional_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_disagreement_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in DISAGREEMENT_STATUSES:
        raise ValueError(f"{field_name} must be open or resolved")


def _require_playbook_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in PLAYBOOK_STATUSES:
        raise ValueError(f"{field_name} must be blocked or watch")


def _require_report_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or blocked")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_DISAGREEMENT_RESOLUTION_PLAYBOOK_V2_CONFIG_VERSION",
    "ResearchPacketSourceDisagreementInput",
    "ResearchPacketSourceDisagreementResolutionPlaybookConfig",
    "ResearchPacketSourceDisagreementResolutionPlaybookReport",
    "ResearchPacketSourceDisagreementResolutionPlaybookRow",
    "build_research_packet_source_disagreement_resolution_playbook_v2",
    "research_packet_source_disagreement_resolution_playbook_v2_payload",
)
