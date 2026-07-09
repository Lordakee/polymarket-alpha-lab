"""Team specialist consensus staleness report."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_CONSENSUS_STALENESS_CONFIG_VERSION = (
    "research-team-specialist-consensus-staleness-report"
)

STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DAY_SECONDS = Decimal("86400.000000")
_PUBLIC_TEXT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = tuple(
    "".join(parts)
    for parts in (
        ("raw",),
        ("candi", "date"),
        ("market",),
        ("source",),
        ("te", "xt"),
        ("identifier",),
        ("question",),
        ("slug",),
        ("url",),
        ("dsn",),
        ("table",),
        ("d", "b_"),
        ("_d", "b"),
        ("database",),
        ("net", "work"),
        ("au", "th"),
        ("secret",),
        ("token",),
        ("private",),
        ("key",),
        ("wal", "let"),
        ("or", "der"),
        ("li", "ve"),
        ("tra", "de"),
        ("trad", "ing"),
        ("execu", "tion"),
        ("mutation",),
        ("position",),
        ("b", "uy"),
        ("s", "ell"),
        ("reco", "mmendation"),
        ("siz", "ing"),
    )
)


@dataclass(frozen=True)
class ResearchTeamSpecialistConsensusStalenessConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_CONSENSUS_STALENESS_CONFIG_VERSION
    )
    consensus_age_watch_seconds: Decimal = _DAY_SECONDS
    consensus_age_block_seconds: Decimal = Decimal("172800.000000")
    evidence_refresh_watch_seconds: Decimal = _DAY_SECONDS
    evidence_refresh_block_seconds: Decimal = Decimal("172800.000000")
    dissent_watch_count: Decimal = _ONE
    dissent_block_count: Decimal = Decimal("3.000000")
    escalation_watch_count: Decimal = _ONE
    escalation_block_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistConsensusStalenessConfig:
            raise TypeError(
                "ResearchTeamSpecialistConsensusStalenessConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistConsensusStalenessConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchTeamSpecialistConsensusStalenessConfig",
            )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_CONSENSUS_STALENESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "consensus_age_watch_seconds",
            "consensus_age_block_seconds",
            "evidence_refresh_watch_seconds",
            "evidence_refresh_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "dissent_watch_count",
            "dissent_block_count",
            "escalation_watch_count",
            "escalation_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistConsensusStalenessInput:
    team_id: str
    consensus_observed_at: datetime
    evidence_refreshed_at: datetime
    dissenting_specialist_count: Decimal
    unresolved_escalation_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistConsensusStalenessInput:
            raise TypeError(
                "ResearchTeamSpecialistConsensusStalenessInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistConsensusStalenessInput:
            raise ValueError(
                "snapshot must be exactly "
                "ResearchTeamSpecialistConsensusStalenessInput",
            )
        _require_public_text("team_id", self.team_id)
        object.__setattr__(
            self,
            "consensus_observed_at",
            _as_utc("consensus_observed_at", self.consensus_observed_at),
        )
        object.__setattr__(
            self,
            "evidence_refreshed_at",
            _as_utc("evidence_refreshed_at", self.evidence_refreshed_at),
        )
        object.__setattr__(
            self,
            "dissenting_specialist_count",
            _normalize_count(
                "dissenting_specialist_count",
                self.dissenting_specialist_count,
            ),
        )
        object.__setattr__(
            self,
            "unresolved_escalation_count",
            _normalize_count(
                "unresolved_escalation_count",
                self.unresolved_escalation_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("snapshot", self)
        _reject_unsafe_public_payload("snapshot", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistConsensusStalenessRow:
    team_id: str
    manual_review_urgency: str
    last_consensus_age_seconds: Decimal
    dissent_count: Decimal
    evidence_refresh_age_seconds: Decimal
    unresolved_escalation_count: Decimal
    snapshot_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistConsensusStalenessRow:
            raise TypeError(
                "ResearchTeamSpecialistConsensusStalenessRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistConsensusStalenessRow:
            raise ValueError(
                "row must be exactly ResearchTeamSpecialistConsensusStalenessRow",
            )
        _require_public_text("team_id", self.team_id)
        _require_status("manual_review_urgency", self.manual_review_urgency)
        for field_name in (
            "last_consensus_age_seconds",
            "evidence_refresh_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "dissent_count",
            "unresolved_escalation_count",
            "snapshot_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistConsensusStalenessReport:
    generated_at: datetime
    config_version: str
    status: str
    team_count: Decimal
    block_team_count: Decimal
    watch_team_count: Decimal
    pass_team_count: Decimal
    max_last_consensus_age_seconds: Decimal
    max_evidence_refresh_age_seconds: Decimal
    total_dissent_count: Decimal
    total_unresolved_escalation_count: Decimal
    rows: tuple[ResearchTeamSpecialistConsensusStalenessRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistConsensusStalenessReport:
            raise TypeError(
                "ResearchTeamSpecialistConsensusStalenessReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistConsensusStalenessReport:
            raise ValueError(
                "report must be exactly ResearchTeamSpecialistConsensusStalenessReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_generated_at_utc("generated_at", self.generated_at),
        )
        _require_public_text("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "team_count",
            "block_team_count",
            "watch_team_count",
            "pass_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_last_consensus_age_seconds",
            "max_evidence_refresh_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_dissent_count",
            "total_unresolved_escalation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_team_specialist_consensus_staleness_report(
    snapshots: Iterable[ResearchTeamSpecialistConsensusStalenessInput],
    *,
    config: ResearchTeamSpecialistConsensusStalenessConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistConsensusStalenessReport:
    if type(config) is not ResearchTeamSpecialistConsensusStalenessConfig:
        raise ValueError(
            "config must be a ResearchTeamSpecialistConsensusStalenessConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_generated_at_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_inputs(snapshots)
    _validate_input_times(normalized_snapshots, generated_at_utc)
    rows = _rows_from_snapshots(
        normalized_snapshots,
        config=config,
        generated_at=generated_at_utc,
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "team_count": _count(len(rows)),
        "block_team_count": _urgency_count(rows, "block"),
        "watch_team_count": _urgency_count(rows, "watch"),
        "pass_team_count": _urgency_count(rows, "pass"),
        "max_last_consensus_age_seconds": _max_decimal(
            tuple(row.last_consensus_age_seconds for row in rows),
        ),
        "max_evidence_refresh_age_seconds": _max_decimal(
            tuple(row.evidence_refresh_age_seconds for row in rows),
        ),
        "total_dissent_count": _sum_decimals(
            tuple(row.dissent_count for row in rows),
        ),
        "total_unresolved_escalation_count": _sum_decimals(
            tuple(row.unresolved_escalation_count for row in rows),
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamSpecialistConsensusStalenessReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_specialist_consensus_staleness_report_payload(
    report: ResearchTeamSpecialistConsensusStalenessReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamSpecialistConsensusStalenessReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
        _reject_unsafe_public_payload(
            "report payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        expected_digest = _digest_from_payload(payload)
        if payload["derived_validation_digest"] != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    if isinstance(report, Mapping):
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload(
            "report payload",
            payload,
            allow_json_containers=True,
        )
        _require_hard_flags("report payload", _MappingFlags(payload))
        expected_digest = _digest_from_payload(payload)
        if payload.get("derived_validation_digest") != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _report_from_payload(payload)
        return payload
    raise ValueError(
        "report must be a ResearchTeamSpecialistConsensusStalenessReport",
    )


def research_team_specialist_consensus_staleness_report_digest(
    report: ResearchTeamSpecialistConsensusStalenessReport | Mapping[str, object],
) -> str:
    payload = research_team_specialist_consensus_staleness_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


@dataclass(frozen=True)
class _MappingFlags:
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


def _rows_from_snapshots(
    snapshots: tuple[ResearchTeamSpecialistConsensusStalenessInput, ...],
    *,
    config: ResearchTeamSpecialistConsensusStalenessConfig,
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistConsensusStalenessRow, ...]:
    grouped: dict[str, list[ResearchTeamSpecialistConsensusStalenessInput]] = {}
    for snapshot in snapshots:
        grouped.setdefault(snapshot.team_id, []).append(snapshot)
    rows = tuple(
        _row_from_team_snapshots(team_id, tuple(items), config, generated_at)
        for team_id, items in grouped.items()
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _row_from_team_snapshots(
    team_id: str,
    snapshots: tuple[ResearchTeamSpecialistConsensusStalenessInput, ...],
    config: ResearchTeamSpecialistConsensusStalenessConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistConsensusStalenessRow:
    latest_consensus_at = max(snapshot.consensus_observed_at for snapshot in snapshots)
    latest_refresh_at = max(snapshot.evidence_refreshed_at for snapshot in snapshots)
    last_consensus_age_seconds = _age_seconds(generated_at, latest_consensus_at)
    evidence_refresh_age_seconds = _age_seconds(generated_at, latest_refresh_at)
    dissent_count = _sum_decimals(
        tuple(snapshot.dissenting_specialist_count for snapshot in snapshots),
    )
    unresolved_escalation_count = _sum_decimals(
        tuple(snapshot.unresolved_escalation_count for snapshot in snapshots),
    )
    manual_review_urgency = _manual_review_urgency(
        last_consensus_age_seconds=last_consensus_age_seconds,
        evidence_refresh_age_seconds=evidence_refresh_age_seconds,
        dissent_count=dissent_count,
        unresolved_escalation_count=unresolved_escalation_count,
        config=config,
    )
    return ResearchTeamSpecialistConsensusStalenessRow(
        team_id=team_id,
        manual_review_urgency=manual_review_urgency,
        last_consensus_age_seconds=last_consensus_age_seconds,
        dissent_count=dissent_count,
        evidence_refresh_age_seconds=evidence_refresh_age_seconds,
        unresolved_escalation_count=unresolved_escalation_count,
        snapshot_count=_count(len(snapshots)),
        reason_codes=_row_reason_codes(
            snapshots,
            manual_review_urgency=manual_review_urgency,
            last_consensus_age_seconds=last_consensus_age_seconds,
            evidence_refresh_age_seconds=evidence_refresh_age_seconds,
            dissent_count=dissent_count,
            unresolved_escalation_count=unresolved_escalation_count,
            config=config,
        ),
    )


def _manual_review_urgency(
    *,
    last_consensus_age_seconds: Decimal,
    evidence_refresh_age_seconds: Decimal,
    dissent_count: Decimal,
    unresolved_escalation_count: Decimal,
    config: ResearchTeamSpecialistConsensusStalenessConfig,
) -> str:
    if (
        last_consensus_age_seconds >= config.consensus_age_block_seconds
        or evidence_refresh_age_seconds >= config.evidence_refresh_block_seconds
        or dissent_count >= config.dissent_block_count
        or unresolved_escalation_count >= config.escalation_block_count
    ):
        return "block"
    if (
        last_consensus_age_seconds >= config.consensus_age_watch_seconds
        or evidence_refresh_age_seconds >= config.evidence_refresh_watch_seconds
        or dissent_count >= config.dissent_watch_count
        or unresolved_escalation_count >= config.escalation_watch_count
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    snapshots: tuple[ResearchTeamSpecialistConsensusStalenessInput, ...],
    *,
    manual_review_urgency: str,
    last_consensus_age_seconds: Decimal,
    evidence_refresh_age_seconds: Decimal,
    dissent_count: Decimal,
    unresolved_escalation_count: Decimal,
    config: ResearchTeamSpecialistConsensusStalenessConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    codes.extend(
        sorted(
            {
                code
                for snapshot in snapshots
                for code in snapshot.reason_codes
            },
        ),
    )
    if manual_review_urgency == "pass":
        codes.append("consensus_staleness_clear")
        return tuple(codes)
    for field_code, value, watch_threshold, block_threshold in (
        (
            "consensus_age",
            last_consensus_age_seconds,
            config.consensus_age_watch_seconds,
            config.consensus_age_block_seconds,
        ),
        (
            "evidence_refresh",
            evidence_refresh_age_seconds,
            config.evidence_refresh_watch_seconds,
            config.evidence_refresh_block_seconds,
        ),
        (
            "dissent",
            dissent_count,
            config.dissent_watch_count,
            config.dissent_block_count,
        ),
        (
            "escalation",
            unresolved_escalation_count,
            config.escalation_watch_count,
            config.escalation_block_count,
        ),
    ):
        if value >= block_threshold:
            codes.append(f"consensus_staleness_{field_code}_block")
        elif value >= watch_threshold:
            codes.append(f"consensus_staleness_{field_code}_watch")
    return tuple(codes)


def _row_sort_key(row: ResearchTeamSpecialistConsensusStalenessRow) -> tuple[Decimal, str]:
    return (_urgency_sort_value(row.manual_review_urgency), row.team_id)


def _urgency_sort_value(status: str) -> Decimal:
    if status == "block":
        return Decimal("0.000000")
    if status == "watch":
        return Decimal("1.000000")
    return Decimal("2.000000")


def _report_status(
    rows: tuple[ResearchTeamSpecialistConsensusStalenessRow, ...],
) -> str:
    if any(row.manual_review_urgency == "block" for row in rows):
        return "block"
    if any(row.manual_review_urgency == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistConsensusStalenessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("consensus_staleness_empty",)
    codes: list[str] = []
    if any(row.manual_review_urgency == "block" for row in rows):
        codes.append("consensus_staleness_block_team_present")
    if any(row.manual_review_urgency == "watch" for row in rows):
        codes.append("consensus_staleness_watch_team_present")
    if all(row.manual_review_urgency == "pass" for row in rows):
        codes.append("consensus_staleness_all_clear")
    return tuple(codes)


def _validate_config(
    config: ResearchTeamSpecialistConsensusStalenessConfig,
) -> None:
    for watch_field, block_field in (
        ("consensus_age_watch_seconds", "consensus_age_block_seconds"),
        ("evidence_refresh_watch_seconds", "evidence_refresh_block_seconds"),
        ("dissent_watch_count", "dissent_block_count"),
        ("escalation_watch_count", "escalation_block_count"),
    ):
        if getattr(config, block_field) <= getattr(config, watch_field):
            raise ValueError(f"{block_field} must be greater than {watch_field}")


def _validate_input_times(
    snapshots: tuple[ResearchTeamSpecialistConsensusStalenessInput, ...],
    generated_at: datetime,
) -> None:
    for snapshot in snapshots:
        if snapshot.consensus_observed_at > generated_at:
            raise ValueError("consensus_observed_at must not exceed generated_at")
        if snapshot.evidence_refreshed_at > generated_at:
            raise ValueError("evidence_refreshed_at must not exceed generated_at")


def _validate_report(report: ResearchTeamSpecialistConsensusStalenessReport) -> None:
    rows = report.rows
    if report.team_count != _count(len(rows)):
        raise ValueError("team_count must match rows")
    if report.block_team_count != _urgency_count(rows, "block"):
        raise ValueError("block_team_count must match rows")
    if report.watch_team_count != _urgency_count(rows, "watch"):
        raise ValueError("watch_team_count must match rows")
    if report.pass_team_count != _urgency_count(rows, "pass"):
        raise ValueError("pass_team_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.max_last_consensus_age_seconds != _max_decimal(
        tuple(row.last_consensus_age_seconds for row in rows),
    ):
        raise ValueError("max_last_consensus_age_seconds must match rows")
    if report.max_evidence_refresh_age_seconds != _max_decimal(
        tuple(row.evidence_refresh_age_seconds for row in rows),
    ):
        raise ValueError("max_evidence_refresh_age_seconds must match rows")
    if report.total_dissent_count != _sum_decimals(
        tuple(row.dissent_count for row in rows),
    ):
        raise ValueError("total_dissent_count must match rows")
    if report.total_unresolved_escalation_count != _sum_decimals(
        tuple(row.unresolved_escalation_count for row in rows),
    ):
        raise ValueError("total_unresolved_escalation_count must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _normalize_inputs(
    snapshots: Iterable[ResearchTeamSpecialistConsensusStalenessInput],
) -> tuple[ResearchTeamSpecialistConsensusStalenessInput, ...]:
    if isinstance(snapshots, str | bytes):
        raise ValueError("snapshots must be an iterable")
    try:
        items = tuple(snapshots)
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable") from exc
    for snapshot in items:
        if type(snapshot) is not ResearchTeamSpecialistConsensusStalenessInput:
            raise ValueError(
                "snapshots must contain ResearchTeamSpecialistConsensusStalenessInput",
            )
        _require_hard_flags("snapshot", snapshot)
        _reject_unsafe_public_payload("snapshot", snapshot)
    return items


def _normalize_rows(
    rows: Iterable[ResearchTeamSpecialistConsensusStalenessRow],
) -> tuple[ResearchTeamSpecialistConsensusStalenessRow, ...]:
    if isinstance(rows, str | bytes):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in items:
        if type(row) is not ResearchTeamSpecialistConsensusStalenessRow:
            raise ValueError(
                "rows must contain ResearchTeamSpecialistConsensusStalenessRow",
            )
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
    return tuple(sorted(items, key=_row_sort_key))


def _urgency_count(
    rows: tuple[ResearchTeamSpecialistConsensusStalenessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.manual_review_urgency == status))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    total = _ZERO
    for value in values:
        total = _normalize_nonnegative_decimal("sum", total + value)
    return total


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _normalize_nonnegative_decimal("max", max(values))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    microseconds = (
        ((delta.days * 86400) + delta.seconds) * 1000000
    ) + delta.microseconds
    return _normalize_nonnegative_decimal(
        "age_seconds",
        Decimal(microseconds) / Decimal("1000000"),
    )


def _count(value: int) -> Decimal:
    return Decimal(str(value)).quantize(_QUANT)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    normalized = _normalize_nonnegative_decimal(field_name, value)
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be UTC")
    return value.astimezone(UTC)


def _as_generated_at_utc(field_name: str, value: datetime) -> datetime:
    return _as_utc(field_name, value)


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for item in value:
        _require_public_text(field_name, item)
    return value


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_TEXT_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be public canonical text")


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _HARD_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return str(value.quantize(_QUANT))
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_ready(nested) for key, nested in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    raise ValueError("report payload contains unsupported value")


def _iter_public_entries(value: object) -> Iterable[tuple[str, str]]:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            yield from _iter_public_entries({field.name: getattr(value, field.name)})
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            yield ("key", str(key))
            yield from _iter_public_entries(nested)
        return
    if isinstance(value, tuple | list):
        for item in value:
            yield from _iter_public_entries(item)
        return
    if type(value) is str:
        yield ("value", value)


def _reject_unsafe_public_payload(
    label: str,
    payload: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if allow_json_containers and type(payload) not in (dict, list, tuple):
        raise ValueError(f"unsafe public payload in {label}")
    for _kind, item in _iter_public_entries(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _report_from_payload(
    payload: dict[str, object],
) -> ResearchTeamSpecialistConsensusStalenessReport:
    _require_exact_payload_fields(
        "report payload",
        payload,
        _public_field_names(ResearchTeamSpecialistConsensusStalenessReport),
    )
    report = ResearchTeamSpecialistConsensusStalenessReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        status=_payload_string("status", payload["status"]),
        team_count=_payload_count("team_count", payload["team_count"]),
        block_team_count=_payload_count(
            "block_team_count",
            payload["block_team_count"],
        ),
        watch_team_count=_payload_count(
            "watch_team_count",
            payload["watch_team_count"],
        ),
        pass_team_count=_payload_count("pass_team_count", payload["pass_team_count"]),
        max_last_consensus_age_seconds=_payload_decimal(
            "max_last_consensus_age_seconds",
            payload["max_last_consensus_age_seconds"],
        ),
        max_evidence_refresh_age_seconds=_payload_decimal(
            "max_evidence_refresh_age_seconds",
            payload["max_evidence_refresh_age_seconds"],
        ),
        total_dissent_count=_payload_count(
            "total_dissent_count",
            payload["total_dissent_count"],
        ),
        total_unresolved_escalation_count=_payload_count(
            "total_unresolved_escalation_count",
            payload["total_unresolved_escalation_count"],
        ),
        rows=tuple(
            _row_from_payload(row_payload)
            for row_payload in _payload_object_list("rows", payload["rows"])
        ),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )
    canonical_payload = _json_ready(asdict(report))
    if canonical_payload != payload:
        raise ValueError("report payload fields must use canonical values")
    return report


def _row_from_payload(
    payload: dict[str, object],
) -> ResearchTeamSpecialistConsensusStalenessRow:
    _require_exact_payload_fields(
        "row payload",
        payload,
        _public_field_names(ResearchTeamSpecialistConsensusStalenessRow),
    )
    return ResearchTeamSpecialistConsensusStalenessRow(
        team_id=_payload_string("team_id", payload["team_id"]),
        manual_review_urgency=_payload_string(
            "manual_review_urgency",
            payload["manual_review_urgency"],
        ),
        last_consensus_age_seconds=_payload_decimal(
            "last_consensus_age_seconds",
            payload["last_consensus_age_seconds"],
        ),
        dissent_count=_payload_count("dissent_count", payload["dissent_count"]),
        evidence_refresh_age_seconds=_payload_decimal(
            "evidence_refresh_age_seconds",
            payload["evidence_refresh_age_seconds"],
        ),
        unresolved_escalation_count=_payload_count(
            "unresolved_escalation_count",
            payload["unresolved_escalation_count"],
        ),
        snapshot_count=_payload_count("snapshot_count", payload["snapshot_count"]),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )


def _public_field_names(dataclass_type: type[object]) -> frozenset[str]:
    return frozenset(field.name for field in fields(dataclass_type))


def _require_exact_payload_fields(
    label: str,
    payload: dict[str, object],
    expected_fields: frozenset[str],
) -> None:
    actual_fields = frozenset(payload)
    extra_fields = actual_fields - expected_fields
    missing_fields = expected_fields - actual_fields
    if extra_fields:
        raise ValueError(f"unexpected {label} fields")
    if missing_fields:
        raise ValueError(f"missing {label} fields")


def _payload_object_list(field_name: str, value: object) -> tuple[dict[str, object], ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    rows: list[dict[str, object]] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError(f"{field_name} must contain objects")
        rows.append(item)
    return tuple(rows)


def _payload_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_payload_string(field_name, item) for item in value)


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        normalized = _as_utc(field_name, datetime.fromisoformat(value))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _payload_count(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    normalized = _normalize_count(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    normalized = _normalize_nonnegative_decimal(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _report_values_without_digest(
    report: ResearchTeamSpecialistConsensusStalenessReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(dict(values))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _digest_from_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_CONSENSUS_STALENESS_CONFIG_VERSION",
    "STATUSES",
    "ResearchTeamSpecialistConsensusStalenessConfig",
    "ResearchTeamSpecialistConsensusStalenessInput",
    "ResearchTeamSpecialistConsensusStalenessReport",
    "ResearchTeamSpecialistConsensusStalenessRow",
    "build_research_team_specialist_consensus_staleness_report",
    "research_team_specialist_consensus_staleness_report_digest",
    "research_team_specialist_consensus_staleness_report_payload",
)
