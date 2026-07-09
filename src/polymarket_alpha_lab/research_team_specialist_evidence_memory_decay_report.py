"""Public-safe specialist evidence memory decay report reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_MEMORY_DECAY_REPORT_CONFIG_VERSION = (
    "research-team-specialist-evidence-memory-decay-report-v0"
)
EVIDENCE_MEMORY_DECAY_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SECONDS_PER_HOUR = Decimal("3600.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
OPAQUE_HEX_IDENTIFIER_RE = re.compile(r"^(?:0x)?[0-9a-f]{32,}$")
OPAQUE_NUMERIC_IDENTIFIER_RE = re.compile(r"^[0-9]{16,}$")
UUID_IDENTIFIER_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
)
HEX_CHARS = frozenset("0123456789abcdef")

PAPER_ACTION_BY_STATUS = {
    "pass": "paper_specialist_evidence_memory_decay_monitor",
    "watch": "paper_specialist_evidence_memory_decay_watch",
    "block": "paper_specialist_evidence_memory_decay_block",
}

REPORT_REASON_BY_STATUS = {
    "pass": "specialist_evidence_memory_decay_report_pass",
    "watch": "specialist_evidence_memory_decay_report_watch",
    "block": "specialist_evidence_memory_decay_report_block",
}

EVIDENCE_STALE_BLOCK_REASON = "specialist_evidence_memory_evidence_stale_block"
MEMORY_STALE_BLOCK_REASON = "specialist_evidence_memory_memory_stale_block"
CONFIDENCE_BLOCK_REASON = "specialist_evidence_memory_confidence_block"
CONTRADICTION_BLOCK_REASON = "specialist_evidence_memory_contradiction_block"
CORROBORATION_BLOCK_REASON = "specialist_evidence_memory_corroboration_block"
REUSE_BLOCK_REASON = "specialist_evidence_memory_reuse_block"
EVIDENCE_STALE_WATCH_REASON = "specialist_evidence_memory_evidence_stale_watch"
MEMORY_STALE_WATCH_REASON = "specialist_evidence_memory_memory_stale_watch"
CONFIDENCE_WATCH_REASON = "specialist_evidence_memory_confidence_watch"
CONTRADICTION_WATCH_REASON = "specialist_evidence_memory_contradiction_watch"
CORROBORATION_WATCH_REASON = "specialist_evidence_memory_corroboration_watch"
REUSE_WATCH_REASON = "specialist_evidence_memory_reuse_watch"
PASS_REASON = "specialist_evidence_memory_decay_clear"

BLOCK_REASON_CODES = (
    EVIDENCE_STALE_BLOCK_REASON,
    MEMORY_STALE_BLOCK_REASON,
    CONFIDENCE_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    CORROBORATION_BLOCK_REASON,
    REUSE_BLOCK_REASON,
)
WATCH_REASON_CODES = (
    EVIDENCE_STALE_WATCH_REASON,
    MEMORY_STALE_WATCH_REASON,
    CONFIDENCE_WATCH_REASON,
    CONTRADICTION_WATCH_REASON,
    CORROBORATION_WATCH_REASON,
    REUSE_WATCH_REASON,
)
ROW_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (PASS_REASON,)
REPORT_REASON_CODES = (
    REPORT_REASON_BY_STATUS["pass"],
    REPORT_REASON_BY_STATUS["watch"],
    REPORT_REASON_BY_STATUS["block"],
    *ROW_REASON_CODES,
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_LABEL_FRAGMENTS = frozenset(
    (
        "candidate",
        "condition_id",
        _join_parts("mar", "ket"),
        "slug",
        "question",
        "raw",
        "http",
        "url",
        "dsn",
        _join_parts("tab", "le"),
        "token",
        "secret",
        "credential",
        "api_key",
        "private_key",
        "auth",
        "account",
        "execution",
        "sizing",
        "recommendation",
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("li", "ve"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
    ),
)
UNSAFE_PAYLOAD_KEYS = frozenset(
    (
        "candidate_id",
        "candidate_key",
        "condition_id",
        "event_id",
        "asset_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "raw_source",
        "dsn",
        "table",
        "token",
        "token_id",
        "clob_token_id",
        "outcome_token_id",
        "auth",
        "account",
        "private_key",
        "wallet",
        "order",
        "order_ticket",
        "trade",
        "execution",
        "sizing",
        "recommendation",
        "live",
    ),
)
UNSAFE_PAYLOAD_VALUE_FRAGMENTS = frozenset(
    (
        "candidate",
        "condition_id",
        _join_parts("mar", "ket"),
        "slug",
        "question",
        "https://",
        "http://",
        "source_url",
        "source_text",
        "postgres://",
        "dsn",
        _join_parts("tab", "le"),
        "token",
        "auth",
        "account",
        "private_key",
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        "execution",
        "sizing",
        "recommendation",
        _join_parts(" li", "ve "),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_MEMORY_DECAY_REPORT_CONFIG_VERSION",
    "EVIDENCE_MEMORY_DECAY_STATUSES",
    "ResearchTeamSpecialistEvidenceMemoryDecayConfig",
    "ResearchTeamSpecialistEvidenceMemoryDecayInput",
    "ResearchTeamSpecialistEvidenceMemoryDecayReasonCodeCount",
    "ResearchTeamSpecialistEvidenceMemoryDecayReport",
    "ResearchTeamSpecialistEvidenceMemoryDecayRow",
    "build_research_team_specialist_evidence_memory_decay_report",
    "research_team_specialist_evidence_memory_decay_report_digest",
    "research_team_specialist_evidence_memory_decay_report_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamSpecialistEvidenceMemoryDecayConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_MEMORY_DECAY_REPORT_CONFIG_VERSION
    )
    max_pass_evidence_age_hours: Decimal = Decimal("12.000000")
    max_watch_evidence_age_hours: Decimal = Decimal("48.000000")
    max_pass_memory_age_hours: Decimal = Decimal("24.000000")
    max_watch_memory_age_hours: Decimal = Decimal("72.000000")
    min_pass_evidence_confidence_score: Decimal = Decimal("0.800000")
    min_watch_evidence_confidence_score: Decimal = Decimal("0.500000")
    max_pass_contradiction_score: Decimal = Decimal("0.100000")
    max_watch_contradiction_score: Decimal = Decimal("0.250000")
    min_pass_corroboration_score: Decimal = Decimal("0.700000")
    min_watch_corroboration_score: Decimal = Decimal("0.400000")
    max_pass_memory_reuse_count: Decimal = Decimal("3.000000")
    max_watch_memory_reuse_count: Decimal = Decimal("8.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistEvidenceMemoryDecayConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_MEMORY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_evidence_age_hours",
            "max_watch_evidence_age_hours",
            "max_pass_memory_age_hours",
            "max_watch_memory_age_hours",
            "max_pass_memory_reuse_count",
            "max_watch_memory_reuse_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_evidence_confidence_score",
            "min_watch_evidence_confidence_score",
            "max_pass_contradiction_score",
            "max_watch_contradiction_score",
            "min_pass_corroboration_score",
            "min_watch_corroboration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistEvidenceMemoryDecayInput(_FinalDataclass):
    domain_label: str
    specialist_label: str
    memory_bucket_label: str
    observed_at: datetime
    evidence_observed_at: datetime
    memory_refreshed_at: datetime
    evidence_confidence_score: Decimal
    contradiction_score: Decimal
    corroboration_score: Decimal
    memory_reuse_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistEvidenceMemoryDecayInput,
            "input",
        )
        _require_public_label("domain_label", self.domain_label)
        _require_public_label("specialist_label", self.specialist_label)
        _require_public_label("memory_bucket_label", self.memory_bucket_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "memory_refreshed_at",
            _as_utc("memory_refreshed_at", self.memory_refreshed_at),
        )
        for field_name in (
            "evidence_confidence_score",
            "contradiction_score",
            "corroboration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_reuse_count",
            _require_nonnegative_decimal("memory_reuse_count", self.memory_reuse_count),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistEvidenceMemoryDecayRow(_FinalDataclass):
    domain_label: str
    specialist_label: str
    memory_bucket_label: str
    decay_status: str
    generated_at: datetime
    observed_at: datetime
    observation_age_seconds: Decimal
    evidence_observed_at: datetime
    evidence_age_hours: Decimal
    memory_refreshed_at: datetime
    memory_age_hours: Decimal
    evidence_confidence_score: Decimal
    contradiction_score: Decimal
    corroboration_score: Decimal
    memory_reuse_count: Decimal
    decay_pressure_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistEvidenceMemoryDecayRow, "row")
        _require_public_label("domain_label", self.domain_label)
        _require_public_label("specialist_label", self.specialist_label)
        _require_public_label("memory_bucket_label", self.memory_bucket_label)
        _require_status("decay_status", self.decay_status)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "memory_refreshed_at",
            _as_utc("memory_refreshed_at", self.memory_refreshed_at),
        )
        for field_name in (
            "observation_age_seconds",
            "evidence_age_hours",
            "memory_age_hours",
            "memory_reuse_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_confidence_score",
            "contradiction_score",
            "corroboration_score",
            "decay_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _require_reason_codes(self.reason_codes))
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistEvidenceMemoryDecayReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistEvidenceMemoryDecayReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        if self.reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistEvidenceMemoryDecayReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    max_pass_evidence_age_hours: Decimal
    max_watch_evidence_age_hours: Decimal
    max_pass_memory_age_hours: Decimal
    max_watch_memory_age_hours: Decimal
    min_pass_evidence_confidence_score: Decimal
    min_watch_evidence_confidence_score: Decimal
    max_pass_contradiction_score: Decimal
    max_watch_contradiction_score: Decimal
    min_pass_corroboration_score: Decimal
    min_watch_corroboration_score: Decimal
    max_pass_memory_reuse_count: Decimal
    max_watch_memory_reuse_count: Decimal
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_evidence_count: Decimal
    stale_memory_count: Decimal
    low_confidence_count: Decimal
    contradiction_count: Decimal
    weak_corroboration_count: Decimal
    overused_memory_count: Decimal
    max_evidence_age_hours: Decimal
    max_memory_age_hours: Decimal
    max_decay_pressure_score: Decimal
    status: str
    paper_queue_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistEvidenceMemoryDecayReasonCodeCount, ...]
    rows: tuple[ResearchTeamSpecialistEvidenceMemoryDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistEvidenceMemoryDecayReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_MEMORY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_evidence_age_hours",
            "max_watch_evidence_age_hours",
            "max_pass_memory_age_hours",
            "max_watch_memory_age_hours",
            "max_pass_memory_reuse_count",
            "max_watch_memory_reuse_count",
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_evidence_count",
            "stale_memory_count",
            "low_confidence_count",
            "contradiction_count",
            "weak_corroboration_count",
            "overused_memory_count",
            "max_evidence_age_hours",
            "max_memory_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_evidence_confidence_score",
            "min_watch_evidence_confidence_score",
            "max_pass_contradiction_score",
            "max_watch_contradiction_score",
            "min_pass_corroboration_score",
            "min_watch_corroboration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_decay_pressure_score",
            _require_ratio_decimal(
                "max_decay_pressure_score",
                self.max_decay_pressure_score,
            ),
        )
        _require_status("status", self.status)
        _require_public_string("paper_queue_action", self.paper_queue_action)
        if self.paper_queue_action != PAPER_ACTION_BY_STATUS[self.status]:
            raise ValueError("paper_queue_action must match status")
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
        _reject_unsafe_public_payload("report", self)
        _validate_config(_config_from_report(self))
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report(self)


def build_research_team_specialist_evidence_memory_decay_report(
    inputs: Iterable[ResearchTeamSpecialistEvidenceMemoryDecayInput],
    *,
    config: ResearchTeamSpecialistEvidenceMemoryDecayConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistEvidenceMemoryDecayReport:
    _require_exact_type(config, ResearchTeamSpecialistEvidenceMemoryDecayConfig, "config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return ResearchTeamSpecialistEvidenceMemoryDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        max_pass_evidence_age_hours=config.max_pass_evidence_age_hours,
        max_watch_evidence_age_hours=config.max_watch_evidence_age_hours,
        max_pass_memory_age_hours=config.max_pass_memory_age_hours,
        max_watch_memory_age_hours=config.max_watch_memory_age_hours,
        min_pass_evidence_confidence_score=config.min_pass_evidence_confidence_score,
        min_watch_evidence_confidence_score=config.min_watch_evidence_confidence_score,
        max_pass_contradiction_score=config.max_pass_contradiction_score,
        max_watch_contradiction_score=config.max_watch_contradiction_score,
        min_pass_corroboration_score=config.min_pass_corroboration_score,
        min_watch_corroboration_score=config.min_watch_corroboration_score,
        max_pass_memory_reuse_count=config.max_pass_memory_reuse_count,
        max_watch_memory_reuse_count=config.max_watch_memory_reuse_count,
        input_count=_count(len(input_rows)),
        row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        stale_evidence_count=_reason_row_count(
            rows,
            EVIDENCE_STALE_BLOCK_REASON,
            EVIDENCE_STALE_WATCH_REASON,
        ),
        stale_memory_count=_reason_row_count(
            rows,
            MEMORY_STALE_BLOCK_REASON,
            MEMORY_STALE_WATCH_REASON,
        ),
        low_confidence_count=_reason_row_count(
            rows,
            CONFIDENCE_BLOCK_REASON,
            CONFIDENCE_WATCH_REASON,
        ),
        contradiction_count=_reason_row_count(
            rows,
            CONTRADICTION_BLOCK_REASON,
            CONTRADICTION_WATCH_REASON,
        ),
        weak_corroboration_count=_reason_row_count(
            rows,
            CORROBORATION_BLOCK_REASON,
            CORROBORATION_WATCH_REASON,
        ),
        overused_memory_count=_reason_row_count(
            rows,
            REUSE_BLOCK_REASON,
            REUSE_WATCH_REASON,
        ),
        max_evidence_age_hours=_max_decimal(tuple(row.evidence_age_hours for row in rows)),
        max_memory_age_hours=_max_decimal(tuple(row.memory_age_hours for row in rows)),
        max_decay_pressure_score=_max_decimal(
            tuple(row.decay_pressure_score for row in rows),
        ),
        status=status,
        paper_queue_action=PAPER_ACTION_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_specialist_evidence_memory_decay_report_payload(
    report: ResearchTeamSpecialistEvidenceMemoryDecayReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamSpecialistEvidenceMemoryDecayReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _copy_public_json_value(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamSpecialistEvidenceMemoryDecayReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    supplied_digest = payload.get("derived_validation_digest")
    if type(supplied_digest) is not str:
        raise ValueError("derived_validation_digest is required")
    _require_sha256("derived_validation_digest", supplied_digest)
    if supplied_digest != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")
    _reject_public_numeric_values(payload)
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    validated_report = _report_from_payload(payload)
    canonical_payload = _json_ready(asdict(validated_report))
    if type(canonical_payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return canonical_payload


def research_team_specialist_evidence_memory_decay_report_digest(
    report: ResearchTeamSpecialistEvidenceMemoryDecayReport | Mapping[str, object],
) -> str:
    payload = research_team_specialist_evidence_memory_decay_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _report_from_payload(
    payload: Mapping[str, object],
) -> ResearchTeamSpecialistEvidenceMemoryDecayReport:
    _require_exact_payload_schema(
        "report",
        payload,
        ResearchTeamSpecialistEvidenceMemoryDecayReport,
    )
    rows = tuple(
        _row_from_payload(item, index=index)
        for index, item in enumerate(_payload_list("rows", payload["rows"]))
    )
    reason_code_counts = tuple(
        _reason_code_count_from_payload(item, index=index)
        for index, item in enumerate(
            _payload_list("reason_code_counts", payload["reason_code_counts"]),
        )
    )
    return ResearchTeamSpecialistEvidenceMemoryDecayReport(
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        config_version=_string_from_payload("config_version", payload["config_version"]),
        max_pass_evidence_age_hours=_decimal_from_payload(
            "max_pass_evidence_age_hours",
            payload["max_pass_evidence_age_hours"],
        ),
        max_watch_evidence_age_hours=_decimal_from_payload(
            "max_watch_evidence_age_hours",
            payload["max_watch_evidence_age_hours"],
        ),
        max_pass_memory_age_hours=_decimal_from_payload(
            "max_pass_memory_age_hours",
            payload["max_pass_memory_age_hours"],
        ),
        max_watch_memory_age_hours=_decimal_from_payload(
            "max_watch_memory_age_hours",
            payload["max_watch_memory_age_hours"],
        ),
        min_pass_evidence_confidence_score=_decimal_from_payload(
            "min_pass_evidence_confidence_score",
            payload["min_pass_evidence_confidence_score"],
        ),
        min_watch_evidence_confidence_score=_decimal_from_payload(
            "min_watch_evidence_confidence_score",
            payload["min_watch_evidence_confidence_score"],
        ),
        max_pass_contradiction_score=_decimal_from_payload(
            "max_pass_contradiction_score",
            payload["max_pass_contradiction_score"],
        ),
        max_watch_contradiction_score=_decimal_from_payload(
            "max_watch_contradiction_score",
            payload["max_watch_contradiction_score"],
        ),
        min_pass_corroboration_score=_decimal_from_payload(
            "min_pass_corroboration_score",
            payload["min_pass_corroboration_score"],
        ),
        min_watch_corroboration_score=_decimal_from_payload(
            "min_watch_corroboration_score",
            payload["min_watch_corroboration_score"],
        ),
        max_pass_memory_reuse_count=_decimal_from_payload(
            "max_pass_memory_reuse_count",
            payload["max_pass_memory_reuse_count"],
        ),
        max_watch_memory_reuse_count=_decimal_from_payload(
            "max_watch_memory_reuse_count",
            payload["max_watch_memory_reuse_count"],
        ),
        input_count=_decimal_from_payload("input_count", payload["input_count"]),
        row_count=_decimal_from_payload("row_count", payload["row_count"]),
        pass_count=_decimal_from_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_payload("watch_count", payload["watch_count"]),
        block_count=_decimal_from_payload("block_count", payload["block_count"]),
        stale_evidence_count=_decimal_from_payload(
            "stale_evidence_count",
            payload["stale_evidence_count"],
        ),
        stale_memory_count=_decimal_from_payload(
            "stale_memory_count",
            payload["stale_memory_count"],
        ),
        low_confidence_count=_decimal_from_payload(
            "low_confidence_count",
            payload["low_confidence_count"],
        ),
        contradiction_count=_decimal_from_payload(
            "contradiction_count",
            payload["contradiction_count"],
        ),
        weak_corroboration_count=_decimal_from_payload(
            "weak_corroboration_count",
            payload["weak_corroboration_count"],
        ),
        overused_memory_count=_decimal_from_payload(
            "overused_memory_count",
            payload["overused_memory_count"],
        ),
        max_evidence_age_hours=_decimal_from_payload(
            "max_evidence_age_hours",
            payload["max_evidence_age_hours"],
        ),
        max_memory_age_hours=_decimal_from_payload(
            "max_memory_age_hours",
            payload["max_memory_age_hours"],
        ),
        max_decay_pressure_score=_decimal_from_payload(
            "max_decay_pressure_score",
            payload["max_decay_pressure_score"],
        ),
        status=_string_from_payload("status", payload["status"]),
        paper_queue_action=_string_from_payload(
            "paper_queue_action",
            payload["paper_queue_action"],
        ),
        reason_codes=_string_tuple_from_payload("reason_codes", payload["reason_codes"]),
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_string_from_payload(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_bool_from_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_payload("report_only", payload["report_only"]),
        readonly=_bool_from_payload("readonly", payload["readonly"]),
    )


def _row_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchTeamSpecialistEvidenceMemoryDecayRow:
    label = f"rows[{index}]"
    payload = _mapping_from_payload(label, value)
    _require_exact_payload_schema(
        "row",
        payload,
        ResearchTeamSpecialistEvidenceMemoryDecayRow,
    )
    return ResearchTeamSpecialistEvidenceMemoryDecayRow(
        domain_label=_string_from_payload(
            f"{label}.domain_label",
            payload["domain_label"],
        ),
        specialist_label=_string_from_payload(
            f"{label}.specialist_label",
            payload["specialist_label"],
        ),
        memory_bucket_label=_string_from_payload(
            f"{label}.memory_bucket_label",
            payload["memory_bucket_label"],
        ),
        decay_status=_string_from_payload(
            f"{label}.decay_status",
            payload["decay_status"],
        ),
        generated_at=_datetime_from_payload(
            f"{label}.generated_at",
            payload["generated_at"],
        ),
        observed_at=_datetime_from_payload(
            f"{label}.observed_at",
            payload["observed_at"],
        ),
        observation_age_seconds=_decimal_from_payload(
            f"{label}.observation_age_seconds",
            payload["observation_age_seconds"],
        ),
        evidence_observed_at=_datetime_from_payload(
            f"{label}.evidence_observed_at",
            payload["evidence_observed_at"],
        ),
        evidence_age_hours=_decimal_from_payload(
            f"{label}.evidence_age_hours",
            payload["evidence_age_hours"],
        ),
        memory_refreshed_at=_datetime_from_payload(
            f"{label}.memory_refreshed_at",
            payload["memory_refreshed_at"],
        ),
        memory_age_hours=_decimal_from_payload(
            f"{label}.memory_age_hours",
            payload["memory_age_hours"],
        ),
        evidence_confidence_score=_decimal_from_payload(
            f"{label}.evidence_confidence_score",
            payload["evidence_confidence_score"],
        ),
        contradiction_score=_decimal_from_payload(
            f"{label}.contradiction_score",
            payload["contradiction_score"],
        ),
        corroboration_score=_decimal_from_payload(
            f"{label}.corroboration_score",
            payload["corroboration_score"],
        ),
        memory_reuse_count=_decimal_from_payload(
            f"{label}.memory_reuse_count",
            payload["memory_reuse_count"],
        ),
        decay_pressure_score=_decimal_from_payload(
            f"{label}.decay_pressure_score",
            payload["decay_pressure_score"],
        ),
        reason_codes=_string_tuple_from_payload(
            f"{label}.reason_codes",
            payload["reason_codes"],
        ),
        paper_only=_bool_from_payload(f"{label}.paper_only", payload["paper_only"]),
        report_only=_bool_from_payload(f"{label}.report_only", payload["report_only"]),
        readonly=_bool_from_payload(f"{label}.readonly", payload["readonly"]),
    )


def _reason_code_count_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchTeamSpecialistEvidenceMemoryDecayReasonCodeCount:
    label = f"reason_code_counts[{index}]"
    payload = _mapping_from_payload(label, value)
    _require_exact_payload_schema(
        "reason_code_count",
        payload,
        ResearchTeamSpecialistEvidenceMemoryDecayReasonCodeCount,
    )
    return ResearchTeamSpecialistEvidenceMemoryDecayReasonCodeCount(
        reason_code=_string_from_payload(
            f"{label}.reason_code",
            payload["reason_code"],
        ),
        count=_decimal_from_payload(f"{label}.count", payload["count"]),
        row_ratio=_decimal_from_payload(f"{label}.row_ratio", payload["row_ratio"]),
        paper_only=_bool_from_payload(f"{label}.paper_only", payload["paper_only"]),
        report_only=_bool_from_payload(f"{label}.report_only", payload["report_only"]),
        readonly=_bool_from_payload(f"{label}.readonly", payload["readonly"]),
    )


def _require_exact_payload_schema(
    label: str,
    payload: Mapping[str, object],
    dataclass_type: type[object],
) -> None:
    expected_keys = {field.name for field in fields(dataclass_type)}
    if set(payload) != expected_keys:
        raise ValueError(f"{label} must use canonical {label} payload schema")


def _mapping_from_payload(field_name: str, value: object) -> Mapping[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    return value


def _payload_list(field_name: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    return value


def _string_tuple_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    return tuple(
        _string_from_payload(f"{field_name}[{index}]", item)
        for index, item in enumerate(_payload_list(field_name, value))
    )


def _string_from_payload(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _bool_from_payload(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        normalized = _quantize(Decimal(value))
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    return _as_utc(field_name, parsed)


def _row_from_input(
    item: ResearchTeamSpecialistEvidenceMemoryDecayInput,
    *,
    config: ResearchTeamSpecialistEvidenceMemoryDecayConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistEvidenceMemoryDecayRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    if item.evidence_observed_at > generated_at:
        raise ValueError("evidence_observed_at must not be in the future")
    if item.memory_refreshed_at > generated_at:
        raise ValueError("memory_refreshed_at must not be in the future")
    evidence_age_hours = _hours_between(generated_at, item.evidence_observed_at)
    memory_age_hours = _hours_between(generated_at, item.memory_refreshed_at)
    reason_codes = _row_reason_codes(
        item=item,
        evidence_age_hours=evidence_age_hours,
        memory_age_hours=memory_age_hours,
        config=config,
    )
    return ResearchTeamSpecialistEvidenceMemoryDecayRow(
        domain_label=item.domain_label,
        specialist_label=item.specialist_label,
        memory_bucket_label=item.memory_bucket_label,
        decay_status=_row_status(reason_codes),
        generated_at=generated_at,
        observed_at=item.observed_at,
        observation_age_seconds=_seconds_between(generated_at, item.observed_at),
        evidence_observed_at=item.evidence_observed_at,
        evidence_age_hours=evidence_age_hours,
        memory_refreshed_at=item.memory_refreshed_at,
        memory_age_hours=memory_age_hours,
        evidence_confidence_score=item.evidence_confidence_score,
        contradiction_score=item.contradiction_score,
        corroboration_score=item.corroboration_score,
        memory_reuse_count=item.memory_reuse_count,
        decay_pressure_score=_decay_pressure_score(
            item=item,
            evidence_age_hours=evidence_age_hours,
            memory_age_hours=memory_age_hours,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    item: ResearchTeamSpecialistEvidenceMemoryDecayInput,
    evidence_age_hours: Decimal,
    memory_age_hours: Decimal,
    config: ResearchTeamSpecialistEvidenceMemoryDecayConfig,
) -> tuple[str, ...]:
    return _row_reason_codes_from_metrics(
        evidence_age_hours=evidence_age_hours,
        memory_age_hours=memory_age_hours,
        evidence_confidence_score=item.evidence_confidence_score,
        contradiction_score=item.contradiction_score,
        corroboration_score=item.corroboration_score,
        memory_reuse_count=item.memory_reuse_count,
        config=config,
    )


def _row_reason_codes_from_metrics(
    *,
    evidence_age_hours: Decimal,
    memory_age_hours: Decimal,
    evidence_confidence_score: Decimal,
    contradiction_score: Decimal,
    corroboration_score: Decimal,
    memory_reuse_count: Decimal,
    config: ResearchTeamSpecialistEvidenceMemoryDecayConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_high_threshold_reason(
        reasons,
        metric=evidence_age_hours,
        watch=config.max_pass_evidence_age_hours,
        block=config.max_watch_evidence_age_hours,
        watch_code=EVIDENCE_STALE_WATCH_REASON,
        block_code=EVIDENCE_STALE_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=memory_age_hours,
        watch=config.max_pass_memory_age_hours,
        block=config.max_watch_memory_age_hours,
        watch_code=MEMORY_STALE_WATCH_REASON,
        block_code=MEMORY_STALE_BLOCK_REASON,
    )
    _append_low_threshold_reason(
        reasons,
        metric=evidence_confidence_score,
        watch=config.min_pass_evidence_confidence_score,
        block=config.min_watch_evidence_confidence_score,
        watch_code=CONFIDENCE_WATCH_REASON,
        block_code=CONFIDENCE_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=contradiction_score,
        watch=config.max_pass_contradiction_score,
        block=config.max_watch_contradiction_score,
        watch_code=CONTRADICTION_WATCH_REASON,
        block_code=CONTRADICTION_BLOCK_REASON,
    )
    _append_low_threshold_reason(
        reasons,
        metric=corroboration_score,
        watch=config.min_pass_corroboration_score,
        block=config.min_watch_corroboration_score,
        watch_code=CORROBORATION_WATCH_REASON,
        block_code=CORROBORATION_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=memory_reuse_count,
        watch=config.max_pass_memory_reuse_count,
        block=config.max_watch_memory_reuse_count,
        watch_code=REUSE_WATCH_REASON,
        block_code=REUSE_BLOCK_REASON,
    )
    if not reasons:
        reasons.append(PASS_REASON)
    return _require_reason_codes(tuple(reasons))


def _append_high_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric > block:
        reasons.append(block_code)
        return
    if metric > watch:
        reasons.append(watch_code)


def _append_low_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric < block:
        reasons.append(block_code)
        return
    if metric < watch:
        reasons.append(watch_code)


def _decay_pressure_score(
    *,
    item: ResearchTeamSpecialistEvidenceMemoryDecayInput,
    evidence_age_hours: Decimal,
    memory_age_hours: Decimal,
    config: ResearchTeamSpecialistEvidenceMemoryDecayConfig,
) -> Decimal:
    return _decay_pressure_score_from_metrics(
        evidence_age_hours=evidence_age_hours,
        memory_age_hours=memory_age_hours,
        evidence_confidence_score=item.evidence_confidence_score,
        contradiction_score=item.contradiction_score,
        corroboration_score=item.corroboration_score,
        memory_reuse_count=item.memory_reuse_count,
        config=config,
    )


def _decay_pressure_score_from_metrics(
    *,
    evidence_age_hours: Decimal,
    memory_age_hours: Decimal,
    evidence_confidence_score: Decimal,
    contradiction_score: Decimal,
    corroboration_score: Decimal,
    memory_reuse_count: Decimal,
    config: ResearchTeamSpecialistEvidenceMemoryDecayConfig,
) -> Decimal:
    return _max_decimal(
        (
            _high_threshold_pressure(
                evidence_age_hours,
                pass_limit=config.max_pass_evidence_age_hours,
                block_limit=config.max_watch_evidence_age_hours,
            ),
            _high_threshold_pressure(
                memory_age_hours,
                pass_limit=config.max_pass_memory_age_hours,
                block_limit=config.max_watch_memory_age_hours,
            ),
            _low_threshold_pressure(
                evidence_confidence_score,
                pass_limit=config.min_pass_evidence_confidence_score,
                block_limit=config.min_watch_evidence_confidence_score,
            ),
            _high_threshold_pressure(
                contradiction_score,
                pass_limit=config.max_pass_contradiction_score,
                block_limit=config.max_watch_contradiction_score,
            ),
            _low_threshold_pressure(
                corroboration_score,
                pass_limit=config.min_pass_corroboration_score,
                block_limit=config.min_watch_corroboration_score,
            ),
            _high_threshold_pressure(
                memory_reuse_count,
                pass_limit=config.max_pass_memory_reuse_count,
                block_limit=config.max_watch_memory_reuse_count,
            ),
        ),
    )


def _high_threshold_pressure(
    metric: Decimal,
    *,
    pass_limit: Decimal,
    block_limit: Decimal,
) -> Decimal:
    if metric <= pass_limit:
        return ZERO
    if metric > block_limit:
        return ONE
    if block_limit == pass_limit:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _quantize((metric - pass_limit) / (block_limit - pass_limit))


def _low_threshold_pressure(
    metric: Decimal,
    *,
    pass_limit: Decimal,
    block_limit: Decimal,
) -> Decimal:
    if metric >= pass_limit:
        return ZERO
    if metric < block_limit:
        return ONE
    if pass_limit == block_limit:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _quantize((pass_limit - metric) / (pass_limit - block_limit))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchTeamSpecialistEvidenceMemoryDecayRow, ...],
) -> str:
    if any(row.decay_status == "block" for row in rows):
        return "block"
    if any(row.decay_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchTeamSpecialistEvidenceMemoryDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(row.decay_status == status for row in rows))


def _reason_row_count(
    rows: tuple[ResearchTeamSpecialistEvidenceMemoryDecayRow, ...],
    *reason_codes: str,
) -> Decimal:
    return _count(
        sum(any(reason_code in row.reason_codes for reason_code in reason_codes) for row in rows),
    )


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistEvidenceMemoryDecayRow, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    row_reasons = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    )
    reasons = [REPORT_REASON_BY_STATUS[status]]
    reasons.extend(reason_code for reason_code in ROW_REASON_CODES if reason_code in row_reasons)
    return tuple(reasons)


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistEvidenceMemoryDecayRow, ...],
) -> tuple[ResearchTeamSpecialistEvidenceMemoryDecayReasonCodeCount, ...]:
    counter = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    total = _count(len(rows))
    return tuple(
        ResearchTeamSpecialistEvidenceMemoryDecayReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
            row_ratio=_ratio(_count(counter[reason_code]), total),
        )
        for reason_code in ROW_REASON_CODES
        if counter[reason_code]
    )


def _normalize_inputs(
    inputs: Iterable[ResearchTeamSpecialistEvidenceMemoryDecayInput],
) -> tuple[ResearchTeamSpecialistEvidenceMemoryDecayInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        if type(item) is not ResearchTeamSpecialistEvidenceMemoryDecayInput:
            raise ValueError(
                "inputs must contain ResearchTeamSpecialistEvidenceMemoryDecayInput",
            )
        _require_hard_flags("input", item)
        key = (item.domain_label, item.specialist_label, item.memory_bucket_label)
        if key in seen:
            raise ValueError("input rows must be unique")
        seen.add(key)
    return items


def _require_rows(
    rows: tuple[ResearchTeamSpecialistEvidenceMemoryDecayRow, ...],
) -> tuple[ResearchTeamSpecialistEvidenceMemoryDecayRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    expected = tuple(sorted(normalized, key=_row_sort_key))
    if normalized != expected:
        raise ValueError("rows must be sorted deterministically")
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchTeamSpecialistEvidenceMemoryDecayRow:
            raise ValueError(
                "rows must contain ResearchTeamSpecialistEvidenceMemoryDecayRow",
            )
        _require_hard_flags("row", row)
        key = (row.domain_label, row.specialist_label, row.memory_bucket_label)
        if key in seen:
            raise ValueError("rows must contain unique row keys")
        seen.add(key)
    return normalized


def _require_reason_code_counts(
    counts: tuple[ResearchTeamSpecialistEvidenceMemoryDecayReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistEvidenceMemoryDecayReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(counts)
    expected = tuple(
        sorted(normalized, key=lambda item: ROW_REASON_CODES.index(item.reason_code)),
    )
    if normalized != expected:
        raise ValueError("reason_code_counts must be sorted deterministically")
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchTeamSpecialistEvidenceMemoryDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamSpecialistEvidenceMemoryDecayReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    return normalized


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if normalized[0] not in REPORT_REASON_BY_STATUS.values():
        raise ValueError("reason_codes must begin with report status reason")
    expected = tuple(
        reason_code
        for reason_code in (
            normalized[0],
            *ROW_REASON_CODES,
        )
        if reason_code in normalized
    )
    if normalized != expected:
        raise ValueError("reason_codes must be sorted deterministically")
    return normalized


def _require_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    expected = tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in normalized)
    if normalized != expected:
        raise ValueError("reason_codes must be sorted deterministically")
    if PASS_REASON in normalized and len(normalized) != 1:
        raise ValueError("pass reason_codes must not be mixed with decay reasons")
    return normalized


def _validate_config(config: ResearchTeamSpecialistEvidenceMemoryDecayConfig) -> None:
    if config.max_pass_evidence_age_hours > config.max_watch_evidence_age_hours:
        raise ValueError(
            "max_watch_evidence_age_hours must be at least max_pass_evidence_age_hours",
        )
    if config.max_pass_memory_age_hours > config.max_watch_memory_age_hours:
        raise ValueError(
            "max_watch_memory_age_hours must be at least max_pass_memory_age_hours",
        )
    if (
        config.min_watch_evidence_confidence_score
        > config.min_pass_evidence_confidence_score
    ):
        raise ValueError(
            "min_watch_evidence_confidence_score must not exceed "
            "min_pass_evidence_confidence_score",
        )
    if config.max_pass_contradiction_score > config.max_watch_contradiction_score:
        raise ValueError(
            "max_watch_contradiction_score must be at least "
            "max_pass_contradiction_score",
        )
    if config.min_watch_corroboration_score > config.min_pass_corroboration_score:
        raise ValueError(
            "min_watch_corroboration_score must not exceed "
            "min_pass_corroboration_score",
        )
    if config.max_pass_memory_reuse_count > config.max_watch_memory_reuse_count:
        raise ValueError(
            "max_watch_memory_reuse_count must be at least "
            "max_pass_memory_reuse_count",
        )


def _config_from_report(
    report: ResearchTeamSpecialistEvidenceMemoryDecayReport,
) -> ResearchTeamSpecialistEvidenceMemoryDecayConfig:
    return ResearchTeamSpecialistEvidenceMemoryDecayConfig(
        config_version=report.config_version,
        max_pass_evidence_age_hours=report.max_pass_evidence_age_hours,
        max_watch_evidence_age_hours=report.max_watch_evidence_age_hours,
        max_pass_memory_age_hours=report.max_pass_memory_age_hours,
        max_watch_memory_age_hours=report.max_watch_memory_age_hours,
        min_pass_evidence_confidence_score=report.min_pass_evidence_confidence_score,
        min_watch_evidence_confidence_score=report.min_watch_evidence_confidence_score,
        max_pass_contradiction_score=report.max_pass_contradiction_score,
        max_watch_contradiction_score=report.max_watch_contradiction_score,
        min_pass_corroboration_score=report.min_pass_corroboration_score,
        min_watch_corroboration_score=report.min_watch_corroboration_score,
        max_pass_memory_reuse_count=report.max_pass_memory_reuse_count,
        max_watch_memory_reuse_count=report.max_watch_memory_reuse_count,
    )


def _validate_row(row: ResearchTeamSpecialistEvidenceMemoryDecayRow) -> None:
    if row.observed_at > row.generated_at:
        raise ValueError("observed_at must not be in the future")
    if row.evidence_observed_at > row.generated_at:
        raise ValueError("evidence_observed_at must not be in the future")
    if row.memory_refreshed_at > row.generated_at:
        raise ValueError("memory_refreshed_at must not be in the future")
    if row.observation_age_seconds != _seconds_between(row.generated_at, row.observed_at):
        raise ValueError("observation_age_seconds must match generated_at and observed_at")
    if row.evidence_age_hours != _hours_between(row.generated_at, row.evidence_observed_at):
        raise ValueError("evidence_age_hours must match generated_at and evidence_observed_at")
    if row.memory_age_hours != _hours_between(row.generated_at, row.memory_refreshed_at):
        raise ValueError("memory_age_hours must match generated_at and memory_refreshed_at")
    if row.decay_status != _row_status(row.reason_codes):
        raise ValueError("decay_status must match reason_codes")
    if (
        row.decay_status == "pass"
        and row.decay_pressure_score != ZERO
        or row.decay_status == "block"
        and row.decay_pressure_score != ONE
    ):
        raise ValueError("decay_pressure_score must match decay_status")


def _validate_row_against_config(
    row: ResearchTeamSpecialistEvidenceMemoryDecayRow,
    config: ResearchTeamSpecialistEvidenceMemoryDecayConfig,
) -> None:
    if row.reason_codes != _row_reason_codes_from_metrics(
        evidence_age_hours=row.evidence_age_hours,
        memory_age_hours=row.memory_age_hours,
        evidence_confidence_score=row.evidence_confidence_score,
        contradiction_score=row.contradiction_score,
        corroboration_score=row.corroboration_score,
        memory_reuse_count=row.memory_reuse_count,
        config=config,
    ):
        raise ValueError("reason_codes must match row metrics")
    if row.decay_pressure_score != _decay_pressure_score_from_metrics(
        evidence_age_hours=row.evidence_age_hours,
        memory_age_hours=row.memory_age_hours,
        evidence_confidence_score=row.evidence_confidence_score,
        contradiction_score=row.contradiction_score,
        corroboration_score=row.corroboration_score,
        memory_reuse_count=row.memory_reuse_count,
        config=config,
    ):
        raise ValueError("decay_pressure_score must match row metrics")


def _validate_report(report: ResearchTeamSpecialistEvidenceMemoryDecayReport) -> None:
    rows = report.rows
    config = _config_from_report(report)
    for row in rows:
        _validate_row_against_config(row, config)
    checks = {
        "row_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "stale_evidence_count": _reason_row_count(
            rows,
            EVIDENCE_STALE_BLOCK_REASON,
            EVIDENCE_STALE_WATCH_REASON,
        ),
        "stale_memory_count": _reason_row_count(
            rows,
            MEMORY_STALE_BLOCK_REASON,
            MEMORY_STALE_WATCH_REASON,
        ),
        "low_confidence_count": _reason_row_count(
            rows,
            CONFIDENCE_BLOCK_REASON,
            CONFIDENCE_WATCH_REASON,
        ),
        "contradiction_count": _reason_row_count(
            rows,
            CONTRADICTION_BLOCK_REASON,
            CONTRADICTION_WATCH_REASON,
        ),
        "weak_corroboration_count": _reason_row_count(
            rows,
            CORROBORATION_BLOCK_REASON,
            CORROBORATION_WATCH_REASON,
        ),
        "overused_memory_count": _reason_row_count(
            rows,
            REUSE_BLOCK_REASON,
            REUSE_WATCH_REASON,
        ),
        "max_evidence_age_hours": _max_decimal(
            tuple(row.evidence_age_hours for row in rows),
        ),
        "max_memory_age_hours": _max_decimal(tuple(row.memory_age_hours for row in rows)),
        "max_decay_pressure_score": _max_decimal(
            tuple(row.decay_pressure_score for row in rows),
        ),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.paper_queue_action != PAPER_ACTION_BY_STATUS[report.status]:
        raise ValueError("paper_queue_action must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _row_sort_key(
    row: ResearchTeamSpecialistEvidenceMemoryDecayRow,
) -> tuple[str, str, str]:
    return (row.domain_label, row.specialist_label, row.memory_bucket_label)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in EVIDENCE_MEMORY_DECAY_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_public_label(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public lowercase label")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_text(field_name, value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return _quantize(normalized)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(QUANTUM)
    if quantized == ZERO:
        return ZERO
    return quantized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    if earlier > later:
        raise ValueError("datetime values must not be in the future")
    delta = later - earlier
    micros = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _quantize(micros / MICROSECONDS_PER_SECOND)


def _hours_between(later: datetime, earlier: datetime) -> Decimal:
    return _quantize(_seconds_between(later, earlier) / SECONDS_PER_HOUR)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(
    report: ResearchTeamSpecialistEvidenceMemoryDecayReport,
) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return _digest_from_values(values)


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value.quantize(QUANTUM))
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("public payload must not contain numeric values")
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


def _copy_public_json_value(value: object) -> object:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) in (Decimal, int, float):
        raise ValueError("public payload must not contain numeric values")
    if isinstance(value, Mapping):
        copied: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            copied[key] = _copy_public_json_value(item)
        return copied
    if type(value) is list:
        return [_copy_public_json_value(item) for item in value]
    raise ValueError("public payload must contain only JSON values")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload must not contain numeric values")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_text(label, field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must not contain raw mappings")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key in UNSAFE_PAYLOAD_KEYS:
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers and isinstance(value, list):
            raise ValueError(f"{label} must not contain raw lists")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if label in {"domain_label", "specialist_label", "memory_bucket_label"} or label.endswith(
        (".domain_label", ".specialist_label", ".memory_bucket_label"),
    ):
        if any(
            (
                any(fragment in lowered for fragment in UNSAFE_LABEL_FRAGMENTS),
                OPAQUE_HEX_IDENTIFIER_RE.fullmatch(lowered) is not None,
                OPAQUE_NUMERIC_IDENTIFIER_RE.fullmatch(lowered) is not None,
                UUID_IDENTIFIER_RE.fullmatch(lowered) is not None,
            ),
        ):
            raise ValueError(f"{label} contains unsafe public identifier text")
        return
    if any(fragment in lowered for fragment in UNSAFE_PAYLOAD_VALUE_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public payload text")
