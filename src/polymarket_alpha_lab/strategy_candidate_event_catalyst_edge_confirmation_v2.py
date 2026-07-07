"""Pure Phase 1 scorer for event-catalyst edge confirmation."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import UNSAFE_SURFACE_FIELD_FRAGMENTS


DEFAULT_STRATEGY_CANDIDATE_EVENT_CATALYST_EDGE_CONFIRMATION_V2_CONFIG_VERSION = (
    "strategy-candidate-event-catalyst-edge-confirmation-v2-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "blocked")
STATUS_SORT_KEY = {
    "blocked": "0",
    "watch": "1",
    "pass": "2",
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
SENSITIVE_TEXT_FRAGMENTS = ("secret", "private", "token")
REPORT_STATUS_REASON_CODE = {
    "pass": "candidate_event_catalyst_edge_confirmation_clear",
    "watch": "candidate_event_catalyst_edge_confirmation_watch",
    "blocked": "candidate_event_catalyst_edge_confirmation_blocked",
}


@dataclass(frozen=True)
class StrategyCandidateEventCatalystEdgeConfirmationV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_EVENT_CATALYST_EDGE_CONFIRMATION_V2_CONFIG_VERSION
    )
    minimum_catalyst_evidence_score: Decimal = Decimal("0.700000")
    minimum_probability_movement_attribution_score: Decimal = Decimal("0.700000")
    minimum_absolute_probability_move: Decimal = Decimal("0.020000")
    stale_source_age_seconds: Decimal = Decimal("3600.000000")
    maximum_contradiction_score: Decimal = Decimal("0.000000")
    minimum_cost_adjusted_margin: Decimal = Decimal("0.030000")
    watch_cost_adjusted_margin: Decimal = Decimal("0.010000")
    minimum_evidence_source_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_catalyst_evidence_score",
            "minimum_probability_movement_attribution_score",
            "minimum_absolute_probability_move",
            "maximum_contradiction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_source_age_seconds",
            "minimum_cost_adjusted_margin",
            "watch_cost_adjusted_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_evidence_source_count",
            _normalize_nonnegative_count(
                "minimum_evidence_source_count",
                self.minimum_evidence_source_count,
            ),
        )
        _require_at_most(
            "watch_cost_adjusted_margin",
            self.watch_cost_adjusted_margin,
            self.minimum_cost_adjusted_margin,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateEventCatalystEdgeConfirmationV2Input:
    candidate_id: str
    market_slug: str
    forecast_probability: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    estimated_fee: Decimal
    estimated_slippage: Decimal
    catalyst_evidence_score: Decimal
    probability_movement_attribution_score: Decimal
    source_observed_at: datetime
    contradiction_score: Decimal
    evidence_source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "forecast_probability",
            "market_probability_before",
            "market_probability_after",
            "estimated_fee",
            "estimated_slippage",
            "catalyst_evidence_score",
            "probability_movement_attribution_score",
            "contradiction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "evidence_source_count",
            _normalize_nonnegative_count(
                "evidence_source_count",
                self.evidence_source_count,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyCandidateEventCatalystEdgeConfirmationV2Row:
    candidate_id: str
    market_slug: str
    forecast_probability: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    raw_probability_move: Decimal
    absolute_probability_move: Decimal
    candidate_edge: Decimal
    estimated_fee: Decimal
    estimated_slippage: Decimal
    total_estimated_cost: Decimal
    cost_adjusted_margin: Decimal
    catalyst_evidence_score: Decimal
    probability_movement_attribution_score: Decimal
    source_observed_at: datetime
    source_age_seconds: Decimal
    contradiction_score: Decimal
    evidence_source_count: Decimal
    confirmation_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "forecast_probability",
            "market_probability_before",
            "market_probability_after",
            "estimated_fee",
            "estimated_slippage",
            "catalyst_evidence_score",
            "probability_movement_attribution_score",
            "contradiction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "raw_probability_move",
            "candidate_edge",
            "total_estimated_cost",
            "cost_adjusted_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "absolute_probability_move",
            _normalize_nonnegative_decimal(
                "absolute_probability_move",
                self.absolute_probability_move,
            ),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "evidence_source_count",
            _normalize_nonnegative_count(
                "evidence_source_count",
                self.evidence_source_count,
            ),
        )
        _require_member("confirmation_status", self.confirmation_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyCandidateEventCatalystEdgeConfirmationV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class StrategyCandidateEventCatalystEdgeConfirmationV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    confirmed_count: Decimal
    stale_source_count: Decimal
    contradiction_blocked_count: Decimal
    mean_cost_adjusted_margin: Decimal
    max_cost_adjusted_margin: Decimal
    min_cost_adjusted_margin: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    digest: str
    rows: tuple[StrategyCandidateEventCatalystEdgeConfirmationV2Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "confirmed_count",
            "stale_source_count",
            "contradiction_blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_cost_adjusted_margin",
            "max_cost_adjusted_margin",
            "min_cost_adjusted_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
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
        _require_digest("digest", self.digest)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_strategy_candidate_event_catalyst_edge_confirmation_v2_report(
    candidates: tuple[StrategyCandidateEventCatalystEdgeConfirmationV2Input, ...],
    *,
    config: StrategyCandidateEventCatalystEdgeConfirmationV2Config | None = None,
    generated_at: datetime,
) -> StrategyCandidateEventCatalystEdgeConfirmationV2Report:
    cfg = config or StrategyCandidateEventCatalystEdgeConfirmationV2Config()
    if type(cfg) is not StrategyCandidateEventCatalystEdgeConfirmationV2Config:
        raise ValueError(
            "config must be a StrategyCandidateEventCatalystEdgeConfirmationV2Config",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_inputs(candidates)
    _reject_duplicate_inputs(source_rows)
    rows = tuple(
        sorted(
            (
                _row_for_input(row, config=cfg, generated_at=generated_at_utc)
                for row in source_rows
            ),
            key=_row_sort_key,
        ),
    )
    counts = _report_counts(rows)
    margins = tuple(row.cost_adjusted_margin for row in rows)
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows)
    digest = _report_digest_from_parts(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        candidate_count=counts["candidate_count"],
        pass_count=counts["pass_count"],
        watch_count=counts["watch_count"],
        blocked_count=counts["blocked_count"],
        confirmed_count=counts["confirmed_count"],
        stale_source_count=counts["stale_source_count"],
        contradiction_blocked_count=counts["contradiction_blocked_count"],
        mean_cost_adjusted_margin=_mean(margins),
        max_cost_adjusted_margin=_maximum(margins),
        min_cost_adjusted_margin=_minimum(margins),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        rows=rows,
    )
    return StrategyCandidateEventCatalystEdgeConfirmationV2Report(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        candidate_count=counts["candidate_count"],
        pass_count=counts["pass_count"],
        watch_count=counts["watch_count"],
        blocked_count=counts["blocked_count"],
        confirmed_count=counts["confirmed_count"],
        stale_source_count=counts["stale_source_count"],
        contradiction_blocked_count=counts["contradiction_blocked_count"],
        mean_cost_adjusted_margin=_mean(margins),
        max_cost_adjusted_margin=_maximum(margins),
        min_cost_adjusted_margin=_minimum(margins),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        digest=digest,
        rows=rows,
    )


def strategy_candidate_event_catalyst_edge_confirmation_v2_payload(
    report: StrategyCandidateEventCatalystEdgeConfirmationV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCandidateEventCatalystEdgeConfirmationV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyCandidateEventCatalystEdgeConfirmationV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
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


def _row_for_input(
    candidate: StrategyCandidateEventCatalystEdgeConfirmationV2Input,
    *,
    config: StrategyCandidateEventCatalystEdgeConfirmationV2Config,
    generated_at: datetime,
) -> StrategyCandidateEventCatalystEdgeConfirmationV2Row:
    source_age_seconds = _source_age_seconds(
        "source_observed_at",
        candidate.source_observed_at,
        generated_at,
    )
    raw_probability_move = _subtract(
        candidate.market_probability_after,
        candidate.market_probability_before,
    )
    absolute_probability_move = _absolute(raw_probability_move)
    candidate_edge = _subtract(
        candidate.forecast_probability,
        candidate.market_probability_after,
    )
    total_estimated_cost = _add(candidate.estimated_fee, candidate.estimated_slippage)
    cost_adjusted_margin = _subtract(candidate_edge, total_estimated_cost)
    reason_codes = _row_reason_codes(
        candidate=candidate,
        config=config,
        source_age_seconds=source_age_seconds,
        raw_probability_move=raw_probability_move,
        absolute_probability_move=absolute_probability_move,
        candidate_edge=candidate_edge,
        cost_adjusted_margin=cost_adjusted_margin,
    )
    return StrategyCandidateEventCatalystEdgeConfirmationV2Row(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        forecast_probability=candidate.forecast_probability,
        market_probability_before=candidate.market_probability_before,
        market_probability_after=candidate.market_probability_after,
        raw_probability_move=raw_probability_move,
        absolute_probability_move=absolute_probability_move,
        candidate_edge=candidate_edge,
        estimated_fee=candidate.estimated_fee,
        estimated_slippage=candidate.estimated_slippage,
        total_estimated_cost=total_estimated_cost,
        cost_adjusted_margin=cost_adjusted_margin,
        catalyst_evidence_score=candidate.catalyst_evidence_score,
        probability_movement_attribution_score=(
            candidate.probability_movement_attribution_score
        ),
        source_observed_at=candidate.source_observed_at,
        source_age_seconds=source_age_seconds,
        contradiction_score=candidate.contradiction_score,
        evidence_source_count=candidate.evidence_source_count,
        confirmation_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    candidate: StrategyCandidateEventCatalystEdgeConfirmationV2Input,
    config: StrategyCandidateEventCatalystEdgeConfirmationV2Config,
    source_age_seconds: Decimal,
    raw_probability_move: Decimal,
    absolute_probability_move: Decimal,
    candidate_edge: Decimal,
    cost_adjusted_margin: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if candidate_edge > ZERO:
        codes.append("candidate_edge_positive")
    else:
        codes.append("candidate_edge_nonpositive_blocked")

    if candidate.catalyst_evidence_score >= config.minimum_catalyst_evidence_score:
        codes.append("catalyst_evidence_confirmed")
    else:
        codes.append("catalyst_evidence_score_blocked")

    if (
        candidate.probability_movement_attribution_score
        >= config.minimum_probability_movement_attribution_score
    ):
        codes.append("probability_movement_attributed")
    else:
        codes.append("probability_movement_attribution_blocked")

    if absolute_probability_move < config.minimum_absolute_probability_move:
        codes.append("probability_movement_below_minimum_watch")
    if _movement_runs_against_edge(raw_probability_move, candidate_edge):
        codes.append("probability_movement_against_edge_blocked")

    if source_age_seconds > config.stale_source_age_seconds:
        codes.append("source_stale_watch")
    else:
        codes.append("source_fresh")

    if candidate.contradiction_score > config.maximum_contradiction_score:
        codes.append("contradiction_detected_blocked")
    else:
        codes.append("no_contradiction_detected")

    if candidate.evidence_source_count < config.minimum_evidence_source_count:
        codes.append("catalyst_source_count_low_watch")

    if cost_adjusted_margin < config.watch_cost_adjusted_margin:
        codes.append("cost_adjusted_margin_blocked")
    elif cost_adjusted_margin < config.minimum_cost_adjusted_margin:
        codes.append("cost_adjusted_margin_watch")
    else:
        codes.append("cost_adjusted_margin_clear")
    return tuple(codes)


def _movement_runs_against_edge(
    raw_probability_move: Decimal,
    candidate_edge: Decimal,
) -> bool:
    return (
        candidate_edge > ZERO
        and raw_probability_move < ZERO
        or candidate_edge < ZERO
        and raw_probability_move > ZERO
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_blocked") for code in reason_codes):
        return "blocked"
    if any(code.endswith("_watch") for code in reason_codes):
        return "watch"
    return "pass"


def _report_counts(
    rows: tuple[StrategyCandidateEventCatalystEdgeConfirmationV2Row, ...],
) -> dict[str, Decimal]:
    return {
        "candidate_count": _decimal_len(rows),
        "pass_count": _count_rows(rows, "pass"),
        "watch_count": _count_rows(rows, "watch"),
        "blocked_count": _count_rows(rows, "blocked"),
        "confirmed_count": _count_rows(rows, "pass"),
        "stale_source_count": _count_reason(rows, "source_stale_watch"),
        "contradiction_blocked_count": _count_reason(
            rows,
            "contradiction_detected_blocked",
        ),
    }


def _report_status(
    rows: tuple[StrategyCandidateEventCatalystEdgeConfirmationV2Row, ...],
) -> str:
    if any(row.confirmation_status == "blocked" for row in rows):
        return "blocked"
    if any(row.confirmation_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyCandidateEventCatalystEdgeConfirmationV2Row, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    if status == "pass":
        return (REPORT_STATUS_REASON_CODE["pass"],)
    row_codes = {
        code
        for row in rows
        for code in row.reason_codes
        if code.endswith("_blocked") or code.endswith("_watch")
    }
    return (REPORT_STATUS_REASON_CODE[status], *tuple(sorted(row_codes)))


def _reason_code_counts(
    rows: tuple[StrategyCandidateEventCatalystEdgeConfirmationV2Row, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        (code, _normalize_positive_count("count", Decimal(count)))
        for code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _row_sort_key(
    row: StrategyCandidateEventCatalystEdgeConfirmationV2Row,
) -> tuple[str, str, str]:
    return (STATUS_SORT_KEY[row.confirmation_status], row.candidate_id, row.market_slug)


def _validate_row(
    row: StrategyCandidateEventCatalystEdgeConfirmationV2Row,
) -> None:
    if row.raw_probability_move != _subtract(
        row.market_probability_after,
        row.market_probability_before,
    ):
        raise ValueError("raw_probability_move must match market probabilities")
    if row.absolute_probability_move != _absolute(row.raw_probability_move):
        raise ValueError("absolute_probability_move must match raw_probability_move")
    if row.candidate_edge != _subtract(
        row.forecast_probability,
        row.market_probability_after,
    ):
        raise ValueError("candidate_edge must match forecast and market probability")
    if row.total_estimated_cost != _add(row.estimated_fee, row.estimated_slippage):
        raise ValueError("total_estimated_cost must match estimated costs")
    if row.cost_adjusted_margin != _subtract(
        row.candidate_edge,
        row.total_estimated_cost,
    ):
        raise ValueError("cost_adjusted_margin must match edge and costs")
    if row.confirmation_status != _row_status(row.reason_codes):
        raise ValueError("confirmation_status must match reason_codes")


def _validate_report(
    report: StrategyCandidateEventCatalystEdgeConfirmationV2Report,
) -> None:
    counts = _report_counts(report.rows)
    for field_name, expected_value in counts.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    margins = tuple(row.cost_adjusted_margin for row in report.rows)
    if report.mean_cost_adjusted_margin != _mean(margins):
        raise ValueError("mean_cost_adjusted_margin must match rows")
    if report.max_cost_adjusted_margin != _maximum(margins):
        raise ValueError("max_cost_adjusted_margin must match rows")
    if report.min_cost_adjusted_margin != _minimum(margins):
        raise ValueError("min_cost_adjusted_margin must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    expected_digest = _report_digest_from_parts(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        confirmed_count=report.confirmed_count,
        stale_source_count=report.stale_source_count,
        contradiction_blocked_count=report.contradiction_blocked_count,
        mean_cost_adjusted_margin=report.mean_cost_adjusted_margin,
        max_cost_adjusted_margin=report.max_cost_adjusted_margin,
        min_cost_adjusted_margin=report.min_cost_adjusted_margin,
        status=report.status,
        reason_codes=report.reason_codes,
        reason_code_counts=report.reason_code_counts,
        rows=report.rows,
    )
    if report.digest != expected_digest:
        raise ValueError("digest must match report content")


def _report_digest_from_parts(
    *,
    generated_at: datetime,
    config_version: str,
    candidate_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    confirmed_count: Decimal,
    stale_source_count: Decimal,
    contradiction_blocked_count: Decimal,
    mean_cost_adjusted_margin: Decimal,
    max_cost_adjusted_margin: Decimal,
    min_cost_adjusted_margin: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
    reason_code_counts: tuple[tuple[str, Decimal], ...],
    rows: tuple[StrategyCandidateEventCatalystEdgeConfirmationV2Row, ...],
) -> str:
    material = {
        "generated_at": generated_at,
        "config_version": config_version,
        "candidate_count": candidate_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "blocked_count": blocked_count,
        "confirmed_count": confirmed_count,
        "stale_source_count": stale_source_count,
        "contradiction_blocked_count": contradiction_blocked_count,
        "mean_cost_adjusted_margin": mean_cost_adjusted_margin,
        "max_cost_adjusted_margin": max_cost_adjusted_margin,
        "min_cost_adjusted_margin": min_cost_adjusted_margin,
        "status": status,
        "reason_codes": reason_codes,
        "reason_code_counts": reason_code_counts,
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    json_material = _json_ready(material)
    return sha256(
        json.dumps(
            json_material,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()


def _normalize_inputs(
    candidates: tuple[StrategyCandidateEventCatalystEdgeConfirmationV2Input, ...],
) -> tuple[StrategyCandidateEventCatalystEdgeConfirmationV2Input, ...]:
    if not isinstance(candidates, (tuple, list)):
        raise ValueError("candidates must be a tuple or list")
    normalized = []
    for candidate in candidates:
        if type(candidate) is not StrategyCandidateEventCatalystEdgeConfirmationV2Input:
            raise ValueError(
                "candidates must contain StrategyCandidateEventCatalystEdgeConfirmationV2Input",
            )
        _require_hard_flags("input", candidate)
        normalized.append(candidate)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[StrategyCandidateEventCatalystEdgeConfirmationV2Row, ...],
) -> tuple[StrategyCandidateEventCatalystEdgeConfirmationV2Row, ...]:
    if not isinstance(rows, (tuple, list)):
        raise ValueError("rows must be a tuple or list")
    normalized = []
    for row in rows:
        if type(row) is not StrategyCandidateEventCatalystEdgeConfirmationV2Row:
            raise ValueError(
                "rows must contain StrategyCandidateEventCatalystEdgeConfirmationV2Row",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(normalized)


def _reject_duplicate_inputs(
    candidates: tuple[StrategyCandidateEventCatalystEdgeConfirmationV2Input, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (candidate.candidate_id, candidate.market_slug)
        if key in seen:
            raise ValueError("inputs must not contain duplicate candidate market pairs")
        seen.add(key)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        raise ValueError("reason_codes must be a tuple or list")
    normalized = []
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _normalize_reason_code_counts(
    value: object,
) -> tuple[tuple[str, Decimal], ...]:
    if not isinstance(value, (tuple, list)):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise ValueError("reason_code_counts items must be pairs")
        reason_code, count = item
        _require_canonical_string("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(reason_code)
        normalized.append(
            (
                reason_code,
                _normalize_positive_count("count", count),
            ),
        )
    return tuple(normalized)


def _source_age_seconds(
    field_name: str,
    source_observed_at: datetime,
    generated_at: datetime,
) -> Decimal:
    if source_observed_at > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")
    delta = generated_at - source_observed_at
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    )
    return _normalize_nonnegative_decimal(f"{field_name}_age_seconds", seconds)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_decimal("mean", _sum(values) / _decimal_len(values))


def _maximum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _minimum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _sum(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add(total, value)
    return total


def _decimal_len(values: tuple[object, ...]) -> Decimal:
    count = Decimal("0")
    for _value in values:
        count += COUNT_QUANTUM
    return _normalize_nonnegative_count("count", count)


def _count_rows(
    rows: tuple[StrategyCandidateEventCatalystEdgeConfirmationV2Row, ...],
    status: str,
) -> Decimal:
    count = Decimal("0")
    for row in rows:
        if row.confirmation_status == status:
            count += COUNT_QUANTUM
    return _normalize_nonnegative_count("count", count)


def _count_reason(
    rows: tuple[StrategyCandidateEventCatalystEdgeConfirmationV2Row, ...],
    reason_code: str,
) -> Decimal:
    count = Decimal("0")
    for row in rows:
        if reason_code in row.reason_codes:
            count += COUNT_QUANTUM
    return _normalize_nonnegative_count("count", count)


def _add(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("sum", left + right)


def _subtract(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("difference", left - right)


def _absolute(value: Decimal) -> Decimal:
    return _normalize_nonnegative_decimal("absolute", abs(value))


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be exactly Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= Decimal("0"):
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be exactly Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _require_at_most(field_name: str, value: Decimal, upper_bound: Decimal) -> None:
    if value > upper_bound:
        raise ValueError(f"{field_name} must not exceed upper bound")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be non-empty canonical text")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single-line text")


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} is not supported")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in PHASE_FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be 64 hex characters")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be 64 hex characters")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        if _contains_sensitive_text(value):
            raise ValueError(f"{path or label} has sensitive value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe surface field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS)


def _contains_sensitive_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in SENSITIVE_TEXT_FRAGMENTS)


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_EVENT_CATALYST_EDGE_CONFIRMATION_V2_CONFIG_VERSION",
    "StrategyCandidateEventCatalystEdgeConfirmationV2Config",
    "StrategyCandidateEventCatalystEdgeConfirmationV2Input",
    "StrategyCandidateEventCatalystEdgeConfirmationV2ReasonCodeCount",
    "StrategyCandidateEventCatalystEdgeConfirmationV2Report",
    "StrategyCandidateEventCatalystEdgeConfirmationV2Row",
    "build_strategy_candidate_event_catalyst_edge_confirmation_v2_report",
    "strategy_candidate_event_catalyst_edge_confirmation_v2_payload",
)
