"""Report-only research event team confidence rollup dashboard."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_EVENT_TEAM_CONFIDENCE_ROLLUP_DASHBOARD_CONFIG_VERSION = (
    "research-event-team-confidence-rollup-dashboard-v0"
)

PUBLIC_STATUSES = ("pass", "watch", "block")
COORDINATION_STATUSES = (
    "aligned_for_human_review",
    "coordinate_human_review",
    "halt_for_human_recheck",
)
REVIEW_STATUSES = ("complete", "pending", "blocked")
HARD_FLAGS = ("evidence_conflict", "policy_block", "review_escalation")

PASS_REASON = "research_event_team_confidence_rollup_pass"
NO_INPUTS_REASON = "research_event_team_confidence_rollup_no_inputs"
INSUFFICIENT_TEAMS_REASON = "research_event_team_confidence_rollup_insufficient_teams"
CONFIDENCE_DIVERGENCE_REASON = (
    "research_event_team_confidence_rollup_confidence_divergence"
)
EVIDENCE_GAP_REASON = "research_event_team_confidence_rollup_evidence_gap"
REVIEW_PENDING_REASON = "research_event_team_confidence_rollup_review_pending"
REVIEW_BLOCKED_REASON = "research_event_team_confidence_rollup_review_blocked"
HARD_FLAG_REASON = "research_event_team_confidence_rollup_hard_flag"
REASON_CODE_SEQUENCE = (
    HARD_FLAG_REASON,
    REVIEW_BLOCKED_REASON,
    NO_INPUTS_REASON,
    INSUFFICIENT_TEAMS_REASON,
    CONFIDENCE_DIVERGENCE_REASON,
    EVIDENCE_GAP_REASON,
    REVIEW_PENDING_REASON,
    PASS_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
VALIDATION_DIGEST_ALGORITHM = "sha256"
HEX_DIGITS = frozenset("0123456789abcdef")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "trading",
        "position",
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        "recommend",
        "auth",
        "private",
        "secret",
        "account",
        "balance",
        "cancel",
        "replace",
        "sign",
        "broker",
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_TEAM_CONFIDENCE_ROLLUP_DASHBOARD_CONFIG_VERSION",
    "ResearchEventTeamConfidenceObservation",
    "ResearchEventTeamConfidenceRollupConfig",
    "ResearchEventTeamConfidenceRollupReport",
    "ResearchEventTeamConfidenceRollupRow",
    "build_research_event_team_confidence_rollup_dashboard",
    "research_event_team_confidence_rollup_dashboard_digest",
    "research_event_team_confidence_rollup_dashboard_payload",
)


@dataclass(frozen=True)
class ResearchEventTeamConfidenceRollupConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_TEAM_CONFIDENCE_ROLLUP_DASHBOARD_CONFIG_VERSION
    )
    min_team_count: Decimal = Decimal("2.000000")
    max_pass_confidence_spread: Decimal = Decimal("0.200000")
    min_pass_evidence_coverage_ratio: Decimal = Decimal("0.800000")
    min_pass_review_complete_ratio: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventTeamConfidenceRollupConfig:
            raise TypeError(
                "ResearchEventTeamConfidenceRollupConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTeamConfidenceRollupConfig:
            raise ValueError(
                "config must be exactly ResearchEventTeamConfidenceRollupConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_TEAM_CONFIDENCE_ROLLUP_DASHBOARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config_version")
        object.__setattr__(
            self,
            "min_team_count",
            _require_positive_count_decimal("min_team_count", self.min_team_count),
        )
        for field_name in (
            "max_pass_confidence_spread",
            "min_pass_evidence_coverage_ratio",
            "min_pass_review_complete_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchEventTeamConfidenceObservation:
    coordination_key: str
    team_key: str
    discipline: str
    confidence_score: Decimal
    evidence_covered_count: Decimal
    evidence_required_count: Decimal
    review_status: str
    hard_flags: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventTeamConfidenceObservation:
            raise TypeError(
                "ResearchEventTeamConfidenceObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTeamConfidenceObservation:
            raise ValueError(
                "observation must be exactly ResearchEventTeamConfidenceObservation",
            )
        _require_public_string("coordination_key", self.coordination_key)
        _require_public_string("team_key", self.team_key)
        _require_public_string("discipline", self.discipline)
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        object.__setattr__(
            self,
            "evidence_covered_count",
            _require_nonnegative_count_decimal(
                "evidence_covered_count",
                self.evidence_covered_count,
            ),
        )
        object.__setattr__(
            self,
            "evidence_required_count",
            _require_positive_count_decimal(
                "evidence_required_count",
                self.evidence_required_count,
            ),
        )
        if self.evidence_covered_count > self.evidence_required_count:
            raise ValueError(
                "evidence_covered_count must not exceed evidence_required_count",
            )
        _require_member("review_status", self.review_status, REVIEW_STATUSES)
        object.__setattr__(self, "hard_flags", _normalize_hard_flags(self.hard_flags))
        require_paper_only_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventTeamConfidenceRollupRow:
    coordination_key: str
    team_key: str
    discipline: str
    public_status: str
    confidence_score: Decimal
    evidence_coverage_ratio: Decimal
    review_status: str
    hard_flag_count: Decimal
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventTeamConfidenceRollupRow:
            raise TypeError(
                "ResearchEventTeamConfidenceRollupRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTeamConfidenceRollupRow:
            raise ValueError("row must be exactly ResearchEventTeamConfidenceRollupRow")
        _require_public_string("coordination_key", self.coordination_key)
        _require_public_string("team_key", self.team_key)
        _require_public_string("discipline", self.discipline)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        object.__setattr__(
            self,
            "evidence_coverage_ratio",
            _require_ratio_decimal(
                "evidence_coverage_ratio",
                self.evidence_coverage_ratio,
            ),
        )
        _require_member("review_status", self.review_status, REVIEW_STATUSES)
        object.__setattr__(
            self,
            "hard_flag_count",
            _require_nonnegative_count_decimal(
                "hard_flag_count",
                self.hard_flag_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("row", self)
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
                _row_validation_digest(
                    coordination_key=self.coordination_key,
                    team_key=self.team_key,
                    discipline=self.discipline,
                    public_status=self.public_status,
                    confidence_score=self.confidence_score,
                    evidence_coverage_ratio=self.evidence_coverage_ratio,
                    review_status=self.review_status,
                    hard_flag_count=self.hard_flag_count,
                    reason_codes=self.reason_codes,
                ),
            ),
        )


@dataclass(frozen=True)
class ResearchEventTeamConfidenceRollupReport:
    generated_at: datetime
    config_version: str
    coordination_key: str
    public_status: str
    coordination_status: str
    team_count: Decimal
    pass_team_count: Decimal
    watch_team_count: Decimal
    block_team_count: Decimal
    average_confidence_score: Decimal
    min_confidence_score: Decimal
    max_confidence_score: Decimal
    confidence_spread: Decimal
    evidence_covered_count: Decimal
    evidence_required_count: Decimal
    evidence_coverage_ratio: Decimal
    review_complete_count: Decimal
    review_complete_ratio: Decimal
    hard_flag_count: Decimal
    rows: tuple[ResearchEventTeamConfidenceRollupRow, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventTeamConfidenceRollupReport:
            raise TypeError(
                "ResearchEventTeamConfidenceRollupReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTeamConfidenceRollupReport:
            raise ValueError(
                "report must be exactly ResearchEventTeamConfidenceRollupReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_public_string("coordination_key", self.coordination_key)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        _require_member(
            "coordination_status",
            self.coordination_status,
            COORDINATION_STATUSES,
        )
        for field_name in (
            "team_count",
            "pass_team_count",
            "watch_team_count",
            "block_team_count",
            "evidence_covered_count",
            "evidence_required_count",
            "review_complete_count",
            "hard_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_confidence_score",
            "min_confidence_score",
            "max_confidence_score",
            "confidence_spread",
            "evidence_coverage_ratio",
            "review_complete_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        require_paper_only_flags("report", self)
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
                _report_validation_digest(
                    generated_at=self.generated_at,
                    config_version=self.config_version,
                    coordination_key=self.coordination_key,
                    public_status=self.public_status,
                    coordination_status=self.coordination_status,
                    team_count=self.team_count,
                    pass_team_count=self.pass_team_count,
                    watch_team_count=self.watch_team_count,
                    block_team_count=self.block_team_count,
                    average_confidence_score=self.average_confidence_score,
                    min_confidence_score=self.min_confidence_score,
                    max_confidence_score=self.max_confidence_score,
                    confidence_spread=self.confidence_spread,
                    evidence_covered_count=self.evidence_covered_count,
                    evidence_required_count=self.evidence_required_count,
                    evidence_coverage_ratio=self.evidence_coverage_ratio,
                    review_complete_count=self.review_complete_count,
                    review_complete_ratio=self.review_complete_ratio,
                    hard_flag_count=self.hard_flag_count,
                    rows=self.rows,
                    reason_codes=self.reason_codes,
                ),
            ),
        )


def build_research_event_team_confidence_rollup_dashboard(
    observations: list[ResearchEventTeamConfidenceObservation]
    | tuple[ResearchEventTeamConfidenceObservation, ...],
    *,
    config: ResearchEventTeamConfidenceRollupConfig,
    generated_at: datetime,
) -> ResearchEventTeamConfidenceRollupReport:
    if type(config) is not ResearchEventTeamConfidenceRollupConfig:
        raise ValueError("config must be a ResearchEventTeamConfidenceRollupConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)

    if not normalized_observations:
        rows: tuple[ResearchEventTeamConfidenceRollupRow, ...] = ()
        reason_codes = (NO_INPUTS_REASON,)
        return ResearchEventTeamConfidenceRollupReport(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            coordination_key="event-rollup-empty",
            public_status="block",
            coordination_status="halt_for_human_recheck",
            team_count=ZERO,
            pass_team_count=ZERO,
            watch_team_count=ZERO,
            block_team_count=ZERO,
            average_confidence_score=ZERO,
            min_confidence_score=ZERO,
            max_confidence_score=ZERO,
            confidence_spread=ZERO,
            evidence_covered_count=ZERO,
            evidence_required_count=ZERO,
            evidence_coverage_ratio=ZERO,
            review_complete_count=ZERO,
            review_complete_ratio=ZERO,
            hard_flag_count=ZERO,
            rows=rows,
            reason_codes=reason_codes,
        )

    coordination_key = normalized_observations[0].coordination_key
    _require_single_coordination_key(normalized_observations)
    report_reason_codes = _report_reason_codes(normalized_observations, config)
    rows = tuple(
        sorted(
            (
                _rollup_row(
                    observation,
                    config=config,
                    report_reason_codes=report_reason_codes,
                )
                for observation in normalized_observations
            ),
            key=lambda row: (row.team_key, row.discipline),
        ),
    )
    public_status = _report_public_status(rows, report_reason_codes)
    team_count = _decimal_count_from_int(len(rows))

    return ResearchEventTeamConfidenceRollupReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        coordination_key=coordination_key,
        public_status=public_status,
        coordination_status=_coordination_status(public_status),
        team_count=team_count,
        pass_team_count=_status_count(rows, "pass"),
        watch_team_count=_status_count(rows, "watch"),
        block_team_count=_status_count(rows, "block"),
        average_confidence_score=_average_confidence(rows),
        min_confidence_score=min(row.confidence_score for row in rows),
        max_confidence_score=max(row.confidence_score for row in rows),
        confidence_spread=_confidence_spread(rows),
        evidence_covered_count=_sum_decimal(
            observation.evidence_covered_count for observation in normalized_observations
        ),
        evidence_required_count=_sum_decimal(
            observation.evidence_required_count for observation in normalized_observations
        ),
        evidence_coverage_ratio=_coverage_ratio(normalized_observations),
        review_complete_count=_decimal_count_from_int(
            sum(
                1
                for observation in normalized_observations
                if observation.review_status == "complete"
            ),
        ),
        review_complete_ratio=_ratio(
            _decimal_count_from_int(
                sum(
                    1
                    for observation in normalized_observations
                    if observation.review_status == "complete"
                ),
            ),
            team_count,
        ),
        hard_flag_count=_decimal_count_from_int(
            sum(len(observation.hard_flags) for observation in normalized_observations),
        ),
        rows=rows,
        reason_codes=report_reason_codes,
    )


def research_event_team_confidence_rollup_dashboard_payload(
    report: ResearchEventTeamConfidenceRollupReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventTeamConfidenceRollupReport:
        _validate_report_runtime(report)
        payload = _json_ready_public_payload(asdict(report), allow_decimal=True)
    elif type(report) is dict:
        payload = _json_ready_public_payload(report, allow_decimal=False)
    else:
        raise ValueError("report must be a ResearchEventTeamConfidenceRollupReport")
    if type(payload) is not dict:
        raise ValueError("rollup payload must be a JSON object")
    _require_payload_flags(payload)
    _validate_payload_digest(payload)
    _reject_unsafe_public_payload("confidence rollup payload", payload)
    return payload


def research_event_team_confidence_rollup_dashboard_digest(
    report: ResearchEventTeamConfidenceRollupReport | dict[str, Any],
) -> dict[str, Any]:
    payload = research_event_team_confidence_rollup_dashboard_payload(report)
    digest_keys = (
        "generated_at",
        "config_version",
        "coordination_key",
        "public_status",
        "coordination_status",
        "team_count",
        "pass_team_count",
        "watch_team_count",
        "block_team_count",
        "average_confidence_score",
        "confidence_spread",
        "evidence_coverage_ratio",
        "review_complete_ratio",
        "hard_flag_count",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    return {key: payload[key] for key in digest_keys}


def _rollup_row(
    observation: ResearchEventTeamConfidenceObservation,
    *,
    config: ResearchEventTeamConfidenceRollupConfig,
    report_reason_codes: tuple[str, ...],
) -> ResearchEventTeamConfidenceRollupRow:
    reason_codes = _row_reason_codes(
        observation,
        config=config,
        report_reason_codes=report_reason_codes,
    )
    return ResearchEventTeamConfidenceRollupRow(
        coordination_key=observation.coordination_key,
        team_key=observation.team_key,
        discipline=observation.discipline,
        public_status=_row_public_status(reason_codes),
        confidence_score=observation.confidence_score,
        evidence_coverage_ratio=_ratio(
            observation.evidence_covered_count,
            observation.evidence_required_count,
        ),
        review_status=observation.review_status,
        hard_flag_count=_decimal_count_from_int(len(observation.hard_flags)),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: ResearchEventTeamConfidenceObservation,
    *,
    config: ResearchEventTeamConfidenceRollupConfig,
    report_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.hard_flags:
        reason_codes.append(HARD_FLAG_REASON)
    if observation.review_status == "blocked":
        reason_codes.append(REVIEW_BLOCKED_REASON)
    if reason_codes:
        return _ordered_reason_codes(reason_codes)
    if observation.review_status == "pending":
        reason_codes.append(REVIEW_PENDING_REASON)
    if EVIDENCE_GAP_REASON in report_reason_codes and (
        _ratio(observation.evidence_covered_count, observation.evidence_required_count)
        < config.min_pass_evidence_coverage_ratio
    ):
        reason_codes.append(EVIDENCE_GAP_REASON)
    for reason_code in (INSUFFICIENT_TEAMS_REASON, CONFIDENCE_DIVERGENCE_REASON):
        if reason_code in report_reason_codes:
            reason_codes.append(reason_code)
    return _ordered_reason_codes(reason_codes) or (PASS_REASON,)


def _report_reason_codes(
    observations: tuple[ResearchEventTeamConfidenceObservation, ...],
    config: ResearchEventTeamConfidenceRollupConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if any(observation.hard_flags for observation in observations):
        reason_codes.append(HARD_FLAG_REASON)
    if any(observation.review_status == "blocked" for observation in observations):
        reason_codes.append(REVIEW_BLOCKED_REASON)
    if _decimal_count_from_int(len(observations)) < config.min_team_count:
        reason_codes.append(INSUFFICIENT_TEAMS_REASON)
    if _observation_confidence_spread(observations) > config.max_pass_confidence_spread:
        reason_codes.append(CONFIDENCE_DIVERGENCE_REASON)
    if _coverage_ratio(observations) < config.min_pass_evidence_coverage_ratio:
        reason_codes.append(EVIDENCE_GAP_REASON)
    if any(observation.review_status == "pending" for observation in observations):
        reason_codes.append(REVIEW_PENDING_REASON)
    return _ordered_reason_codes(reason_codes) or (PASS_REASON,)


def _ordered_reason_codes(reason_codes: list[str]) -> tuple[str, ...]:
    known = set(reason_codes)
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in known)


def _row_public_status(reason_codes: tuple[str, ...]) -> str:
    if HARD_FLAG_REASON in reason_codes or REVIEW_BLOCKED_REASON in reason_codes:
        return "block"
    if reason_codes != (PASS_REASON,):
        return "watch"
    return "pass"


def _report_public_status(
    rows: tuple[ResearchEventTeamConfidenceRollupRow, ...],
    reason_codes: tuple[str, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.public_status == "block" for row in rows):
        return "block"
    if reason_codes != (PASS_REASON,) or any(row.public_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _coordination_status(public_status: str) -> str:
    if public_status == "pass":
        return "aligned_for_human_review"
    if public_status == "watch":
        return "coordinate_human_review"
    if public_status == "block":
        return "halt_for_human_recheck"
    raise ValueError("public_status must be pass, watch, or block")


def _normalize_observations(
    value: object,
) -> tuple[ResearchEventTeamConfidenceObservation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    observations = tuple(value)
    for observation in observations:
        if type(observation) is not ResearchEventTeamConfidenceObservation:
            raise ValueError(
                "observations must contain ResearchEventTeamConfidenceObservation values",
            )
        require_paper_only_flags("observation", observation)
    sorted_observations = tuple(
        sorted(observations, key=lambda item: (item.coordination_key, item.team_key))
    )
    previous_team_key: str | None = None
    for observation in sorted_observations:
        if observation.team_key == previous_team_key:
            raise ValueError("team_key must be unique within a coordination_key")
        previous_team_key = observation.team_key
    return sorted_observations


def _require_single_coordination_key(
    observations: tuple[ResearchEventTeamConfidenceObservation, ...],
) -> None:
    coordination_keys = {observation.coordination_key for observation in observations}
    if len(coordination_keys) != 1:
        raise ValueError("coordination_key must identify one public event rollup")


def _normalize_rows(value: object) -> tuple[ResearchEventTeamConfidenceRollupRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    previous_key: tuple[str, str] | None = None
    for row in rows:
        if type(row) is not ResearchEventTeamConfidenceRollupRow:
            raise ValueError("rows must contain ResearchEventTeamConfidenceRollupRow values")
        require_paper_only_flags("row", row)
        key = (row.team_key, row.discipline)
        if previous_key is not None and key <= previous_key:
            raise ValueError("rows must be deterministic by team_key and discipline")
        previous_key = key
    return rows


def _normalize_hard_flags(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("hard_flags must be a list or tuple")
    flags = tuple(value)
    for flag in flags:
        _require_public_string("hard_flags", flag)
        if flag not in HARD_FLAGS:
            raise ValueError("hard_flags must use known safe values")
    return tuple(flag for flag in HARD_FLAGS if flag in flags)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_public_string("reason_codes", reason_code)
        if reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must use supported reason codes")
    ordered = _ordered_reason_codes(list(reason_codes))
    if ordered != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _status_count(
    rows: tuple[ResearchEventTeamConfidenceRollupRow, ...],
    public_status: str,
) -> Decimal:
    return _decimal_count_from_int(sum(1 for row in rows if row.public_status == public_status))


def _average_confidence(rows: tuple[ResearchEventTeamConfidenceRollupRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _ratio(_sum_decimal(row.confidence_score for row in rows), _decimal_count_from_int(len(rows)))


def _confidence_spread(rows: tuple[ResearchEventTeamConfidenceRollupRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _quantize_decimal(
        max(row.confidence_score for row in rows) - min(row.confidence_score for row in rows),
    )


def _observation_confidence_spread(
    observations: tuple[ResearchEventTeamConfidenceObservation, ...],
) -> Decimal:
    if not observations:
        return ZERO
    return _quantize_decimal(
        max(observation.confidence_score for observation in observations)
        - min(observation.confidence_score for observation in observations),
    )


def _coverage_ratio(
    observations: tuple[ResearchEventTeamConfidenceObservation, ...],
) -> Decimal:
    required = _sum_decimal(
        observation.evidence_required_count for observation in observations
    )
    if required == ZERO:
        return ZERO
    covered = _sum_decimal(
        observation.evidence_covered_count for observation in observations
    )
    return _ratio(covered, required)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _decimal_count_from_int(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize_decimal(Decimal(value))


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal count")
    return _quantize_decimal(normalized)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be a Decimal ratio between 0 and 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a concrete UTC offset")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    _require_public_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value != value.strip():
        raise ValueError(f"{field_name} must be a canonical public string")
    if not value.isascii() or any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must be printable ASCII")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS)


def _validate_report_consistency(
    report: ResearchEventTeamConfidenceRollupReport,
) -> None:
    if report.team_count != _decimal_count_from_int(len(report.rows)):
        raise ValueError("team_count must match rows")
    if report.pass_team_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_team_count must match rows")
    if report.watch_team_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_team_count must match rows")
    if report.block_team_count != _status_count(report.rows, "block"):
        raise ValueError("block_team_count must match rows")
    if report.average_confidence_score != _average_confidence(report.rows):
        raise ValueError("average_confidence_score must match rows")
    if report.confidence_spread != _confidence_spread(report.rows):
        raise ValueError("confidence_spread must match rows")
    if report.review_complete_count != _decimal_count_from_int(
        sum(1 for row in report.rows if row.review_status == "complete"),
    ):
        raise ValueError("review_complete_count must match rows")
    if report.review_complete_ratio != _ratio(
        report.review_complete_count,
        report.team_count,
    ):
        raise ValueError("review_complete_ratio must match rows")
    if report.hard_flag_count != _sum_decimal(row.hard_flag_count for row in report.rows):
        raise ValueError("hard_flag_count must match rows")
    if report.public_status != _report_public_status(report.rows, report.reason_codes):
        raise ValueError("public_status must match rows")
    if report.coordination_status != _coordination_status(report.public_status):
        raise ValueError("coordination_status must match public_status")


def _validate_report_runtime(report: ResearchEventTeamConfidenceRollupReport) -> None:
    require_paper_only_flags("report", report)
    _as_utc("generated_at", report.generated_at)
    _require_public_string("config_version", report.config_version)
    _require_public_string("coordination_key", report.coordination_key)
    _require_member("public_status", report.public_status, PUBLIC_STATUSES)
    _require_member(
        "coordination_status",
        report.coordination_status,
        COORDINATION_STATUSES,
    )
    _normalize_rows(report.rows)
    _normalize_reason_codes(report.reason_codes)
    for row in report.rows:
        _validate_row_runtime(row)
    _validate_report_consistency(report)
    expected = _report_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        coordination_key=report.coordination_key,
        public_status=report.public_status,
        coordination_status=report.coordination_status,
        team_count=report.team_count,
        pass_team_count=report.pass_team_count,
        watch_team_count=report.watch_team_count,
        block_team_count=report.block_team_count,
        average_confidence_score=report.average_confidence_score,
        min_confidence_score=report.min_confidence_score,
        max_confidence_score=report.max_confidence_score,
        confidence_spread=report.confidence_spread,
        evidence_covered_count=report.evidence_covered_count,
        evidence_required_count=report.evidence_required_count,
        evidence_coverage_ratio=report.evidence_coverage_ratio,
        review_complete_count=report.review_complete_count,
        review_complete_ratio=report.review_complete_ratio,
        hard_flag_count=report.hard_flag_count,
        rows=report.rows,
        reason_codes=report.reason_codes,
    )
    if report.validation_digest != expected:
        raise ValueError("validation_digest must match report")


def _validate_row_runtime(row: ResearchEventTeamConfidenceRollupRow) -> None:
    require_paper_only_flags("row", row)
    _require_public_string("coordination_key", row.coordination_key)
    _require_public_string("team_key", row.team_key)
    _require_public_string("discipline", row.discipline)
    _require_member("public_status", row.public_status, PUBLIC_STATUSES)
    _require_ratio_decimal("confidence_score", row.confidence_score)
    _require_ratio_decimal("evidence_coverage_ratio", row.evidence_coverage_ratio)
    _require_member("review_status", row.review_status, REVIEW_STATUSES)
    _require_nonnegative_count_decimal("hard_flag_count", row.hard_flag_count)
    _normalize_reason_codes(row.reason_codes)
    expected = _row_validation_digest(
        coordination_key=row.coordination_key,
        team_key=row.team_key,
        discipline=row.discipline,
        public_status=row.public_status,
        confidence_score=row.confidence_score,
        evidence_coverage_ratio=row.evidence_coverage_ratio,
        review_status=row.review_status,
        hard_flag_count=row.hard_flag_count,
        reason_codes=row.reason_codes,
    )
    if row.validation_digest != expected:
        raise ValueError("validation_digest must match row")


def _json_ready_public_payload(value: Any, *, allow_decimal: bool) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_public_payload(asdict(value), allow_decimal=allow_decimal)
    if type(value) is Decimal:
        if not allow_decimal:
            raise ValueError("JSON numeric value must use Decimal-derived strings")
        return _decimal_payload(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if isinstance(value, datetime):
        return _datetime_payload(value)
    if type(value) is bool:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready_public_payload(item, allow_decimal=allow_decimal)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready_public_payload(item, allow_decimal=allow_decimal) for item in value]
    raise ValueError("value is not JSON serializable")


def _decimal_payload(value: Decimal) -> str:
    return str(_require_decimal("value", value))


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _optional_string_sequence_payload(values: tuple[str, ...]) -> str:
    return "\x1f".join(values)


def _normalize_validation_digest(
    field_name: str,
    value: object,
    expected_digest: str,
) -> str:
    if value == "":
        return expected_digest
    digest = _require_validation_digest(field_name, value)
    if digest != expected_digest:
        raise ValueError(f"{field_name} must match derived values")
    return digest


def _require_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a validation digest")
    if len(value) != 64 or any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _row_validation_digest(
    *,
    coordination_key: str,
    team_key: str,
    discipline: str,
    public_status: str,
    confidence_score: Decimal,
    evidence_coverage_ratio: Decimal,
    review_status: str,
    hard_flag_count: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "research_event_team_confidence_rollup_row",
            coordination_key,
            team_key,
            discipline,
            public_status,
            _decimal_payload(confidence_score),
            _decimal_payload(evidence_coverage_ratio),
            review_status,
            _decimal_payload(hard_flag_count),
            _optional_string_sequence_payload(reason_codes),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _report_validation_digest(
    *,
    generated_at: datetime,
    config_version: str,
    coordination_key: str,
    public_status: str,
    coordination_status: str,
    team_count: Decimal,
    pass_team_count: Decimal,
    watch_team_count: Decimal,
    block_team_count: Decimal,
    average_confidence_score: Decimal,
    min_confidence_score: Decimal,
    max_confidence_score: Decimal,
    confidence_spread: Decimal,
    evidence_covered_count: Decimal,
    evidence_required_count: Decimal,
    evidence_coverage_ratio: Decimal,
    review_complete_count: Decimal,
    review_complete_ratio: Decimal,
    hard_flag_count: Decimal,
    rows: tuple[ResearchEventTeamConfidenceRollupRow, ...],
    reason_codes: tuple[str, ...],
) -> str:
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "research_event_team_confidence_rollup_report",
            _datetime_payload(generated_at),
            config_version,
            coordination_key,
            public_status,
            coordination_status,
            _decimal_payload(team_count),
            _decimal_payload(pass_team_count),
            _decimal_payload(watch_team_count),
            _decimal_payload(block_team_count),
            _decimal_payload(average_confidence_score),
            _decimal_payload(min_confidence_score),
            _decimal_payload(max_confidence_score),
            _decimal_payload(confidence_spread),
            _decimal_payload(evidence_covered_count),
            _decimal_payload(evidence_required_count),
            _decimal_payload(evidence_coverage_ratio),
            _decimal_payload(review_complete_count),
            _decimal_payload(review_complete_ratio),
            _decimal_payload(hard_flag_count),
            _optional_string_sequence_payload(
                tuple(row.validation_digest for row in rows),
            ),
            _optional_string_sequence_payload(reason_codes),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _payload_row_digest(row: dict[str, Any]) -> str:
    _require_payload_flags(row)
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "research_event_team_confidence_rollup_row",
            _payload_required_string(row, "coordination_key"),
            _payload_required_string(row, "team_key"),
            _payload_required_string(row, "discipline"),
            _payload_required_member(row, "public_status", PUBLIC_STATUSES),
            _payload_required_decimal_string(row, "confidence_score"),
            _payload_required_decimal_string(row, "evidence_coverage_ratio"),
            _payload_required_member(row, "review_status", REVIEW_STATUSES),
            _payload_required_decimal_string(row, "hard_flag_count"),
            _optional_string_sequence_payload(
                _payload_required_reason_code_sequence(row, "reason_codes"),
            ),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _payload_report_digest(
    payload: dict[str, Any],
    row_digests: tuple[str, ...],
) -> str:
    _require_payload_flags(payload)
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "research_event_team_confidence_rollup_report",
            _payload_required_datetime_string(payload, "generated_at"),
            _payload_required_string(payload, "config_version"),
            _payload_required_string(payload, "coordination_key"),
            _payload_required_member(payload, "public_status", PUBLIC_STATUSES),
            _payload_required_member(
                payload,
                "coordination_status",
                COORDINATION_STATUSES,
            ),
            _payload_required_decimal_string(payload, "team_count"),
            _payload_required_decimal_string(payload, "pass_team_count"),
            _payload_required_decimal_string(payload, "watch_team_count"),
            _payload_required_decimal_string(payload, "block_team_count"),
            _payload_required_decimal_string(payload, "average_confidence_score"),
            _payload_required_decimal_string(payload, "min_confidence_score"),
            _payload_required_decimal_string(payload, "max_confidence_score"),
            _payload_required_decimal_string(payload, "confidence_spread"),
            _payload_required_decimal_string(payload, "evidence_covered_count"),
            _payload_required_decimal_string(payload, "evidence_required_count"),
            _payload_required_decimal_string(payload, "evidence_coverage_ratio"),
            _payload_required_decimal_string(payload, "review_complete_count"),
            _payload_required_decimal_string(payload, "review_complete_ratio"),
            _payload_required_decimal_string(payload, "hard_flag_count"),
            _optional_string_sequence_payload(row_digests),
            _optional_string_sequence_payload(
                _payload_required_reason_code_sequence(payload, "reason_codes"),
            ),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _hash_parts(parts: tuple[str, ...]) -> str:
    rendered = json.dumps(parts, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    rows = _payload_rows(payload)
    row_digests = tuple(_payload_row_digest(row) for row in rows)
    for row, expected_digest in zip(rows, row_digests, strict=True):
        if _payload_required_digest(row, "validation_digest") != expected_digest:
            raise ValueError("validation_digest must match payload row")
    if _payload_required_digest(payload, "validation_digest") != _payload_report_digest(
        payload,
        row_digests,
    ):
        raise ValueError("validation_digest must match payload")
    _validate_payload_report_consistency(payload, rows)


def _validate_payload_report_consistency(
    payload: dict[str, Any],
    rows: tuple[dict[str, Any], ...],
) -> None:
    team_count = _decimal_count_from_int(len(rows))
    if _payload_required_decimal(payload, "team_count") != team_count:
        raise ValueError("team_count must match payload rows")
    for field_name, public_status in (
        ("pass_team_count", "pass"),
        ("watch_team_count", "watch"),
        ("block_team_count", "block"),
    ):
        expected = _decimal_count_from_int(
            sum(
                1
                for row in rows
                if _payload_required_member(row, "public_status", PUBLIC_STATUSES)
                == public_status
            ),
        )
        if _payload_required_decimal(payload, field_name) != expected:
            raise ValueError(f"{field_name} must match payload rows")
    reason_codes = _payload_required_reason_code_sequence(payload, "reason_codes")
    expected_public_status = _payload_report_status(rows, reason_codes)
    if _payload_required_member(payload, "public_status", PUBLIC_STATUSES) != expected_public_status:
        raise ValueError("public_status must match payload rows")
    if _payload_required_member(
        payload,
        "coordination_status",
        COORDINATION_STATUSES,
    ) != _coordination_status(expected_public_status):
        raise ValueError("coordination_status must match payload public_status")


def _payload_report_status(
    rows: tuple[dict[str, Any], ...],
    reason_codes: tuple[str, ...],
) -> str:
    if not rows:
        return "block"
    statuses = tuple(
        _payload_required_member(row, "public_status", PUBLIC_STATUSES) for row in rows
    )
    if "block" in statuses:
        return "block"
    if reason_codes != (PASS_REASON,) or "watch" in statuses:
        return "watch"
    return "pass"


def _payload_rows(payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    normalized: list[dict[str, Any]] = []
    previous_key: tuple[str, str] | None = None
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        key = (
            _payload_required_string(row, "team_key"),
            _payload_required_string(row, "discipline"),
        )
        if previous_key is not None and key <= previous_key:
            raise ValueError("rows must be deterministic by team_key and discipline")
        previous_key = key
        normalized.append(row)
    return tuple(normalized)


def _payload_required_digest(payload: dict[str, Any], field_name: str) -> str:
    return _require_validation_digest(field_name, payload.get(field_name))


def _payload_required_member(
    payload: dict[str, Any],
    field_name: str,
    allowed_values: tuple[str, ...],
) -> str:
    value = _payload_required_string(payload, field_name)
    _require_member(field_name, value, allowed_values)
    return value


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    return _require_public_string(field_name, value)


def _payload_required_decimal(payload: dict[str, Any], field_name: str) -> Decimal:
    return _require_decimal(field_name, Decimal(_payload_required_decimal_string(payload, field_name)))


def _payload_required_decimal_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    canonical = _decimal_payload(decimal_value)
    if value != canonical:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return canonical


def _payload_required_datetime_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    canonical = _datetime_payload(parsed)
    if value != canonical:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return canonical


def _payload_required_reason_code_sequence(
    payload: dict[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    value = payload.get(field_name)
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(tuple(value))


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    _reject_unsafe_public_values(label, value)


def _reject_unsafe_public_values(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_values(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public key in {label}")
            _reject_unsafe_public_values(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_values(label, item)
