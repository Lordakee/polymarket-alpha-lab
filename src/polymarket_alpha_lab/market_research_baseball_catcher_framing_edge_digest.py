"""Pure Phase 1 baseball catcher framing edge digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_BASEBALL_CATCHER_FRAMING_EDGE_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-catcher-framing-edge-digest-v0"
)

INPUT_REASONS = (
    "baseball_catcher_framing_edge_input_reported",
    "baseball_catcher_framing_edge_manual_chart",
    "baseball_catcher_framing_edge_pitcher_profile",
    "baseball_catcher_framing_edge_lineup_confirmed",
)
ROW_REASONS = (
    "baseball_catcher_framing_edge_blocked_threshold",
    "baseball_catcher_framing_edge_catcher_available",
    "baseball_catcher_framing_edge_catcher_unavailable",
    "baseball_catcher_framing_edge_input_reported",
    "baseball_catcher_framing_edge_lineup_confirmed",
    "baseball_catcher_framing_edge_pass_threshold",
    "baseball_catcher_framing_edge_pitcher_profile",
    "baseball_catcher_framing_edge_lineup_fresh",
    "baseball_catcher_framing_edge_lineup_stale",
    "baseball_catcher_framing_edge_manual_chart",
    "baseball_catcher_framing_edge_source_disagreement_high",
    "baseball_catcher_framing_edge_source_fresh",
    "baseball_catcher_framing_edge_source_stale",
    "baseball_catcher_framing_edge_watch_threshold",
)
REPORT_REASONS = (
    "baseball_catcher_framing_edge_digest_empty",
    "baseball_catcher_framing_edge_blocked_present",
    "baseball_catcher_framing_edge_watch_present",
    "baseball_catcher_framing_edge_pass_present",
    "baseball_catcher_framing_edge_source_stale_present",
    "baseball_catcher_framing_edge_lineup_stale_present",
    "baseball_catcher_framing_edge_source_disagreement_present",
    "baseball_catcher_framing_edge_availability_risk_present",
)
EDGE_STATUSES = ("blocked", "watch", "pass")
DIGEST_STATUSES = ("blocked", "watch", "pass")
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class BaseballCatcherFramingEdgeDigestConfig:
    config_version: str = DEFAULT_BASEBALL_CATCHER_FRAMING_EDGE_DIGEST_CONFIG_VERSION
    max_update_age_seconds: Decimal = Decimal("900.000000")
    max_lineup_confirmation_age_seconds: Decimal = Decimal("1200.000000")
    elite_framing_runs: Decimal = Decimal("12.000000")
    watch_edge_score_threshold: Decimal = Decimal("0.400000")
    blocked_edge_score_threshold: Decimal = Decimal("0.750000")
    min_catcher_availability_score: Decimal = Decimal("0.600000")
    max_source_disagreement: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_BASEBALL_CATCHER_FRAMING_EDGE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for name in (
            "max_update_age_seconds",
            "max_lineup_confirmation_age_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "elite_framing_runs",
            _require_positive_decimal("elite_framing_runs", self.elite_framing_runs),
        )
        for name in (
            "watch_edge_score_threshold",
            "blocked_edge_score_threshold",
            "min_catcher_availability_score",
            "max_source_disagreement",
        ):
            object.__setattr__(self, name, _require_ratio(name, getattr(self, name)))
        if self.blocked_edge_score_threshold < self.watch_edge_score_threshold:
            raise ValueError(
                "blocked_edge_score_threshold must be at least watch_edge_score_threshold",
            )
        _require_hard_flags("baseball catcher framing edge config", self)


@dataclass(frozen=True)
class BaseballCatcherFramingEdgeObservation:
    source_id: str
    team: str
    opponent: str
    market_slug: str
    observed_at: datetime
    catcher_framing_runs: Decimal
    umpire_called_strike_sensitivity: Decimal
    pitcher_zone_edge_rate: Decimal
    catcher_availability_score: Decimal
    lineup_confirmation_age_seconds: Decimal
    source_disagreement: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for name in ("source_id", "team", "opponent", "market_slug"):
            object.__setattr__(self, name, _require_text(name, getattr(self, name)))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "catcher_framing_runs",
            _require_decimal("catcher_framing_runs", self.catcher_framing_runs),
        )
        for name in (
            "umpire_called_strike_sensitivity",
            "pitcher_zone_edge_rate",
            "catcher_availability_score",
            "source_disagreement",
        ):
            object.__setattr__(self, name, _require_ratio(name, getattr(self, name)))
        object.__setattr__(
            self,
            "lineup_confirmation_age_seconds",
            _require_nonnegative_decimal(
                "lineup_confirmation_age_seconds",
                self.lineup_confirmation_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons("reason_codes", self.reason_codes, INPUT_REASONS),
        )
        _require_hard_flags("baseball catcher framing edge observation", self)


@dataclass(frozen=True)
class BaseballCatcherFramingEdgeReasonCodeCount:
    reason_code: str
    market_count: Decimal
    market_ratio: Decimal
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
            "market_count",
            _require_nonnegative_decimal("market_count", self.market_count),
        )
        object.__setattr__(
            self,
            "market_ratio",
            _require_ratio("market_ratio", self.market_ratio),
        )
        _require_hard_flags("baseball catcher framing edge reason count", self)


@dataclass(frozen=True)
class BaseballCatcherFramingEdgeMarketRow:
    team: str
    opponent: str
    market_slug: str
    catcher_framing_runs: Decimal
    umpire_called_strike_sensitivity: Decimal
    pitcher_zone_edge_rate: Decimal
    catcher_availability_score: Decimal
    lineup_confirmation_age_seconds: Decimal
    source_disagreement: Decimal
    edge_score: Decimal
    risk_score: Decimal
    source_age_seconds: Decimal
    source_count: Decimal
    latest_observed_at: datetime
    edge_status: str
    source_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for name in ("team", "opponent", "market_slug"):
            object.__setattr__(self, name, _require_text(name, getattr(self, name)))
        object.__setattr__(
            self,
            "catcher_framing_runs",
            _require_decimal("catcher_framing_runs", self.catcher_framing_runs),
        )
        for name in (
            "umpire_called_strike_sensitivity",
            "pitcher_zone_edge_rate",
            "catcher_availability_score",
            "source_disagreement",
            "edge_score",
            "risk_score",
        ):
            object.__setattr__(self, name, _require_ratio(name, getattr(self, name)))
        for name in (
            "lineup_confirmation_age_seconds",
            "source_age_seconds",
            "source_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "edge_status",
            _require_member("edge_status", self.edge_status, EDGE_STATUSES),
        )
        object.__setattr__(
            self,
            "source_ids",
            _normalize_text_tuple("source_ids", self.source_ids),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons("reason_codes", self.reason_codes, ROW_REASONS),
        )
        _validate_market_row(self)
        _require_hard_flags("baseball catcher framing edge market row", self)


@dataclass(frozen=True)
class BaseballCatcherFramingEdgeDigest:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_step: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    source_count: Decimal
    pass_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    stale_source_count: Decimal
    lineup_stale_count: Decimal
    disagreement_risk_count: Decimal
    availability_risk_count: Decimal
    max_edge_score: Decimal
    risk_score: Decimal
    rows: tuple[BaseballCatcherFramingEdgeMarketRow, ...]
    reason_code_counts: tuple[BaseballCatcherFramingEdgeReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_BASEBALL_CATCHER_FRAMING_EDGE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "digest_status",
            _require_member("digest_status", self.digest_status, DIGEST_STATUSES),
        )
        object.__setattr__(self, "next_step", _require_text("next_step", self.next_step))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons("reason_codes", self.reason_codes, REPORT_REASONS),
        )
        for name in (
            "market_count",
            "source_count",
            "pass_market_count",
            "watch_market_count",
            "blocked_market_count",
            "stale_source_count",
            "lineup_stale_count",
            "disagreement_risk_count",
            "availability_risk_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in ("max_edge_score", "risk_score"):
            object.__setattr__(self, name, _require_ratio(name, getattr(self, name)))
        object.__setattr__(self, "rows", _normalize_market_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_counts(self.reason_code_counts),
        )
        _validate_digest(self)
        _require_hard_flags("baseball catcher framing edge digest", self)


def build_market_research_baseball_catcher_framing_edge_digest(
    rows: Iterable[BaseballCatcherFramingEdgeObservation],
    *,
    config: BaseballCatcherFramingEdgeDigestConfig,
    generated_at: datetime,
) -> BaseballCatcherFramingEdgeDigest:
    if type(config) is not BaseballCatcherFramingEdgeDigestConfig:
        raise ValueError("config must be a BaseballCatcherFramingEdgeDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("baseball catcher framing edge config", config)
    input_rows = _normalize_inputs(rows)
    if not input_rows:
        return BaseballCatcherFramingEdgeDigest(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            digest_status="pass",
            next_step="pass_report_only_market_research_baseball_catcher_framing_edge_digest",
            reason_codes=("baseball_catcher_framing_edge_digest_empty",),
            market_count=ZERO,
            source_count=ZERO,
            pass_market_count=ZERO,
            watch_market_count=ZERO,
            blocked_market_count=ZERO,
            stale_source_count=ZERO,
            lineup_stale_count=ZERO,
            disagreement_risk_count=ZERO,
            availability_risk_count=ZERO,
            max_edge_score=ZERO,
            risk_score=ZERO,
            rows=(),
            reason_code_counts=(),
        )

    grouped: dict[tuple[str, str, str], list[BaseballCatcherFramingEdgeObservation]] = {}
    for row in input_rows:
        group_id = (row.team, row.opponent, row.market_slug)
        grouped.setdefault(group_id, []).append(row)
    market_rows = tuple(
        _market_row(tuple(group_rows), config=config, generated_at=generated_at_utc)
        for group_id, group_rows in sorted(grouped.items())
        if group_id
    )
    sorted_rows = _sorted_market_rows(market_rows)
    market_count = _count(len(sorted_rows))
    reason_codes = _digest_reasons(sorted_rows)
    digest_status = _digest_status(sorted_rows)

    return BaseballCatcherFramingEdgeDigest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        next_step=_next_step(digest_status),
        reason_codes=reason_codes,
        market_count=market_count,
        source_count=_sum_decimal(row.source_count for row in sorted_rows),
        pass_market_count=_status_count(sorted_rows, "pass"),
        watch_market_count=_status_count(sorted_rows, "watch"),
        blocked_market_count=_status_count(sorted_rows, "blocked"),
        stale_source_count=_reason_count(
            sorted_rows,
            "baseball_catcher_framing_edge_source_stale",
        ),
        lineup_stale_count=_reason_count(
            sorted_rows,
            "baseball_catcher_framing_edge_lineup_stale",
        ),
        disagreement_risk_count=_reason_count(
            sorted_rows,
            "baseball_catcher_framing_edge_source_disagreement_high",
        ),
        availability_risk_count=_reason_count(
            sorted_rows,
            "baseball_catcher_framing_edge_catcher_unavailable",
        ),
        max_edge_score=max((row.edge_score for row in sorted_rows), default=ZERO),
        risk_score=max((row.risk_score for row in sorted_rows), default=ZERO),
        rows=sorted_rows,
        reason_code_counts=_reason_counts(sorted_rows, reason_codes, market_count),
    )


def market_research_baseball_catcher_framing_edge_digest_payload(
    digest: BaseballCatcherFramingEdgeDigest,
) -> dict[str, Any]:
    if type(digest) is not BaseballCatcherFramingEdgeDigest:
        raise ValueError("digest must be a BaseballCatcherFramingEdgeDigest")
    value = _json_ready(digest)
    if type(value) is not dict:
        raise ValueError("digest must serialize to a JSON object")
    return value


def _market_row(
    rows: tuple[BaseballCatcherFramingEdgeObservation, ...],
    *,
    config: BaseballCatcherFramingEdgeDigestConfig,
    generated_at: datetime,
) -> BaseballCatcherFramingEdgeMarketRow:
    latest_observed_at = max(row.observed_at for row in rows)
    source_age_seconds = _seconds_between(generated_at, latest_observed_at, "observed_at")
    catcher_framing_runs = _strongest_framing_runs(rows)
    umpire_called_strike_sensitivity = max(
        row.umpire_called_strike_sensitivity for row in rows
    )
    pitcher_zone_edge_rate = max(row.pitcher_zone_edge_rate for row in rows)
    catcher_availability_score = min(row.catcher_availability_score for row in rows)
    lineup_confirmation_age_seconds = max(
        row.lineup_confirmation_age_seconds for row in rows
    )
    source_disagreement = max(row.source_disagreement for row in rows)
    edge_score = _edge_score(
        catcher_framing_runs=catcher_framing_runs,
        umpire_called_strike_sensitivity=umpire_called_strike_sensitivity,
        pitcher_zone_edge_rate=pitcher_zone_edge_rate,
        catcher_availability_score=catcher_availability_score,
        config=config,
    )
    source_fresh = source_age_seconds <= config.max_update_age_seconds
    lineup_fresh = (
        lineup_confirmation_age_seconds <= config.max_lineup_confirmation_age_seconds
    )
    catcher_available = (
        catcher_availability_score >= config.min_catcher_availability_score
    )
    disagreement_ok = source_disagreement <= config.max_source_disagreement
    risk_score = _row_risk_score(
        edge_score,
        config=config,
        source_fresh=source_fresh,
        lineup_fresh=lineup_fresh,
        catcher_available=catcher_available,
        disagreement_ok=disagreement_ok,
    )
    status = _edge_status(
        edge_score=edge_score,
        risk_score=risk_score,
        config=config,
        source_fresh=source_fresh,
        lineup_fresh=lineup_fresh,
        catcher_available=catcher_available,
        disagreement_ok=disagreement_ok,
    )
    first_row = rows[0]
    return BaseballCatcherFramingEdgeMarketRow(
        team=first_row.team,
        opponent=first_row.opponent,
        market_slug=first_row.market_slug,
        catcher_framing_runs=catcher_framing_runs,
        umpire_called_strike_sensitivity=umpire_called_strike_sensitivity,
        pitcher_zone_edge_rate=pitcher_zone_edge_rate,
        catcher_availability_score=catcher_availability_score,
        lineup_confirmation_age_seconds=lineup_confirmation_age_seconds,
        source_disagreement=source_disagreement,
        edge_score=edge_score,
        risk_score=risk_score,
        source_age_seconds=source_age_seconds,
        source_count=_count(len(rows)),
        latest_observed_at=latest_observed_at,
        edge_status=status,
        source_ids=tuple(row.source_id for row in rows),
        reason_codes=_row_reasons(
            rows,
            status=status,
            source_fresh=source_fresh,
            lineup_fresh=lineup_fresh,
            catcher_available=catcher_available,
            disagreement_ok=disagreement_ok,
        ),
    )


def _row_reasons(
    rows: tuple[BaseballCatcherFramingEdgeObservation, ...],
    *,
    status: str,
    source_fresh: bool,
    lineup_fresh: bool,
    catcher_available: bool,
    disagreement_ok: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    for row in rows:
        reasons.extend(row.reason_codes)
    if status == "blocked":
        reasons.append("baseball_catcher_framing_edge_blocked_threshold")
    elif status == "watch":
        reasons.append("baseball_catcher_framing_edge_watch_threshold")
    else:
        reasons.append("baseball_catcher_framing_edge_pass_threshold")
    if source_fresh:
        reasons.append("baseball_catcher_framing_edge_source_fresh")
    else:
        reasons.append("baseball_catcher_framing_edge_source_stale")
    if lineup_fresh:
        reasons.append("baseball_catcher_framing_edge_lineup_fresh")
    else:
        reasons.append("baseball_catcher_framing_edge_lineup_stale")
    if catcher_available:
        reasons.append("baseball_catcher_framing_edge_catcher_available")
    else:
        reasons.append("baseball_catcher_framing_edge_catcher_unavailable")
    if not disagreement_ok:
        reasons.append("baseball_catcher_framing_edge_source_disagreement_high")
    return _normalize_reasons("reason_codes", tuple(reasons), ROW_REASONS)


def _edge_score(
    *,
    catcher_framing_runs: Decimal,
    umpire_called_strike_sensitivity: Decimal,
    pitcher_zone_edge_rate: Decimal,
    catcher_availability_score: Decimal,
    config: BaseballCatcherFramingEdgeDigestConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        framing_component = abs(catcher_framing_runs) / config.elite_framing_runs
        if framing_component > ONE:
            framing_component = ONE
        score = (
            framing_component
            * umpire_called_strike_sensitivity
            * pitcher_zone_edge_rate
            * catcher_availability_score
        )
        return score.quantize(QUANT)


def _row_risk_score(
    edge_score: Decimal,
    *,
    config: BaseballCatcherFramingEdgeDigestConfig,
    source_fresh: bool,
    lineup_fresh: bool,
    catcher_available: bool,
    disagreement_ok: bool,
) -> Decimal:
    if source_fresh and lineup_fresh and catcher_available and disagreement_ok:
        return edge_score
    return max(edge_score, config.blocked_edge_score_threshold)


def _edge_status(
    *,
    edge_score: Decimal,
    risk_score: Decimal,
    config: BaseballCatcherFramingEdgeDigestConfig,
    source_fresh: bool,
    lineup_fresh: bool,
    catcher_available: bool,
    disagreement_ok: bool,
) -> str:
    if (
        risk_score >= config.blocked_edge_score_threshold
        or not source_fresh
        or not lineup_fresh
        or not catcher_available
        or not disagreement_ok
    ):
        return "blocked"
    if edge_score >= config.watch_edge_score_threshold:
        return "watch"
    return "pass"


def _strongest_framing_runs(
    rows: tuple[BaseballCatcherFramingEdgeObservation, ...],
) -> Decimal:
    strongest = rows[0].catcher_framing_runs
    for row in rows[1:]:
        candidate = row.catcher_framing_runs
        if abs(candidate) > abs(strongest):
            strongest = candidate
        elif abs(candidate) == abs(strongest) and candidate > strongest:
            strongest = candidate
    return strongest


def _digest_status(rows: tuple[BaseballCatcherFramingEdgeMarketRow, ...]) -> str:
    if any(row.edge_status == "blocked" for row in rows):
        return "blocked"
    if any(row.edge_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _digest_reasons(
    rows: tuple[BaseballCatcherFramingEdgeMarketRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("baseball_catcher_framing_edge_digest_empty",)
    reasons: list[str] = []
    if any(row.edge_status == "blocked" for row in rows):
        reasons.append("baseball_catcher_framing_edge_blocked_present")
    if any(row.edge_status == "watch" for row in rows):
        reasons.append("baseball_catcher_framing_edge_watch_present")
    if any(row.edge_status == "pass" for row in rows):
        reasons.append("baseball_catcher_framing_edge_pass_present")
    if any(_row_has_reason(row, "baseball_catcher_framing_edge_source_stale") for row in rows):
        reasons.append("baseball_catcher_framing_edge_source_stale_present")
    if any(_row_has_reason(row, "baseball_catcher_framing_edge_lineup_stale") for row in rows):
        reasons.append("baseball_catcher_framing_edge_lineup_stale_present")
    if any(
        _row_has_reason(
            row,
            "baseball_catcher_framing_edge_source_disagreement_high",
        )
        for row in rows
    ):
        reasons.append("baseball_catcher_framing_edge_source_disagreement_present")
    if any(
        _row_has_reason(row, "baseball_catcher_framing_edge_catcher_unavailable")
        for row in rows
    ):
        reasons.append("baseball_catcher_framing_edge_availability_risk_present")
    return _normalize_reasons("reason_codes", tuple(reasons), REPORT_REASONS)


def _reason_counts(
    rows: tuple[BaseballCatcherFramingEdgeMarketRow, ...],
    report_reasons: tuple[str, ...],
    market_count: Decimal,
) -> tuple[BaseballCatcherFramingEdgeReasonCodeCount, ...]:
    if report_reasons == ("baseball_catcher_framing_edge_digest_empty",):
        return ()
    counts: list[BaseballCatcherFramingEdgeReasonCodeCount] = []
    for reason in report_reasons:
        reason_market_count = _count(
            sum(1 for row in rows if _row_matches_report_reason(row, reason)),
        )
        counts.append(
            BaseballCatcherFramingEdgeReasonCodeCount(
                reason_code=reason,
                market_count=reason_market_count,
                market_ratio=_ratio(reason_market_count, market_count),
            ),
        )
    return tuple(counts)


def _row_matches_report_reason(
    row: BaseballCatcherFramingEdgeMarketRow,
    reason: str,
) -> bool:
    if reason == "baseball_catcher_framing_edge_blocked_present":
        return row.edge_status == "blocked"
    if reason == "baseball_catcher_framing_edge_watch_present":
        return row.edge_status == "watch"
    if reason == "baseball_catcher_framing_edge_pass_present":
        return row.edge_status == "pass"
    if reason == "baseball_catcher_framing_edge_source_stale_present":
        return _row_has_reason(row, "baseball_catcher_framing_edge_source_stale")
    if reason == "baseball_catcher_framing_edge_lineup_stale_present":
        return _row_has_reason(row, "baseball_catcher_framing_edge_lineup_stale")
    if reason == "baseball_catcher_framing_edge_source_disagreement_present":
        return _row_has_reason(
            row,
            "baseball_catcher_framing_edge_source_disagreement_high",
        )
    if reason == "baseball_catcher_framing_edge_availability_risk_present":
        return _row_has_reason(row, "baseball_catcher_framing_edge_catcher_unavailable")
    return False


def _row_has_reason(row: BaseballCatcherFramingEdgeMarketRow, reason: str) -> bool:
    return reason in row.reason_codes


def _next_step(status: str) -> str:
    if status == "blocked":
        return "block_report_only_market_research_baseball_catcher_framing_edge_digest"
    if status == "watch":
        return "watch_report_only_market_research_baseball_catcher_framing_edge_digest"
    return "pass_report_only_market_research_baseball_catcher_framing_edge_digest"


def _normalize_inputs(
    rows: Iterable[BaseballCatcherFramingEdgeObservation],
) -> tuple[BaseballCatcherFramingEdgeObservation, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain baseball catcher framing edge observations")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError(
            "rows must contain baseball catcher framing edge observations",
        ) from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not BaseballCatcherFramingEdgeObservation:
            raise ValueError("rows must contain BaseballCatcherFramingEdgeObservation")
        _require_hard_flags("baseball catcher framing edge observation", row)
        if row.source_id in seen:
            raise ValueError("rows must not contain duplicate source_id values")
        seen.add(row.source_id)
    return normalized


def _normalize_market_rows(
    value: object,
) -> tuple[BaseballCatcherFramingEdgeMarketRow, ...]:
    if not isinstance(value, tuple):
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not BaseballCatcherFramingEdgeMarketRow:
            raise ValueError("rows must contain BaseballCatcherFramingEdgeMarketRow")
        _require_hard_flags("baseball catcher framing edge market row", row)
    if value != _sorted_market_rows(value):
        raise ValueError("rows must be sorted deterministically")
    if len({row.market_slug for row in value}) != len(value):
        raise ValueError("rows must not contain duplicate market_slug values")
    return value


def _normalize_reason_counts(
    value: object,
) -> tuple[BaseballCatcherFramingEdgeReasonCodeCount, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for row in value:
        if type(row) is not BaseballCatcherFramingEdgeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain BaseballCatcherFramingEdgeReasonCodeCount",
            )
        _require_hard_flags("baseball catcher framing edge reason count", row)
    if len({row.reason_code for row in value}) != len(value):
        raise ValueError("reason_code_counts must not contain duplicate reason_code values")
    expected = tuple(
        row
        for reason in REPORT_REASONS
        for row in value
        if row.reason_code == reason
    )
    if value != expected:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return value


def _sorted_market_rows(
    rows: tuple[BaseballCatcherFramingEdgeMarketRow, ...],
) -> tuple[BaseballCatcherFramingEdgeMarketRow, ...]:
    return tuple(
        row
        for _, _, row in sorted(
            (_row_rank(row), slot, row) for slot, row in enumerate(rows)
        )
    )


def _row_rank(row: BaseballCatcherFramingEdgeMarketRow) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.edge_status],
        -row.risk_score,
        row.team,
        row.opponent,
        row.market_slug,
    )


def _validate_market_row(row: BaseballCatcherFramingEdgeMarketRow) -> None:
    if row.source_count != _count(len(row.source_ids)):
        raise ValueError("source_count must match source_ids")
    if row.edge_status == "blocked":
        expected_reason = "baseball_catcher_framing_edge_blocked_threshold"
    elif row.edge_status == "watch":
        expected_reason = "baseball_catcher_framing_edge_watch_threshold"
    else:
        expected_reason = "baseball_catcher_framing_edge_pass_threshold"
    if expected_reason not in row.reason_codes:
        raise ValueError("edge_status must match reason_codes")
    if (
        "baseball_catcher_framing_edge_source_fresh" in row.reason_codes
        and "baseball_catcher_framing_edge_source_stale" in row.reason_codes
    ):
        raise ValueError("reason_codes must contain one source freshness reason")
    if (
        "baseball_catcher_framing_edge_catcher_available" in row.reason_codes
        and "baseball_catcher_framing_edge_catcher_unavailable" in row.reason_codes
    ):
        raise ValueError("reason_codes must contain one catcher availability reason")


def _validate_digest(digest: BaseballCatcherFramingEdgeDigest) -> None:
    if digest.market_count != _count(len(digest.rows)):
        raise ValueError("market_count must match rows")
    if digest.source_count != _sum_decimal(row.source_count for row in digest.rows):
        raise ValueError("source_count must match rows")
    if digest.pass_market_count != _status_count(digest.rows, "pass"):
        raise ValueError("pass_market_count must match rows")
    if digest.watch_market_count != _status_count(digest.rows, "watch"):
        raise ValueError("watch_market_count must match rows")
    if digest.blocked_market_count != _status_count(digest.rows, "blocked"):
        raise ValueError("blocked_market_count must match rows")
    if digest.stale_source_count != _reason_count(
        digest.rows,
        "baseball_catcher_framing_edge_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if digest.lineup_stale_count != _reason_count(
        digest.rows,
        "baseball_catcher_framing_edge_lineup_stale",
    ):
        raise ValueError("lineup_stale_count must match rows")
    if digest.disagreement_risk_count != _reason_count(
        digest.rows,
        "baseball_catcher_framing_edge_source_disagreement_high",
    ):
        raise ValueError("disagreement_risk_count must match rows")
    if digest.availability_risk_count != _reason_count(
        digest.rows,
        "baseball_catcher_framing_edge_catcher_unavailable",
    ):
        raise ValueError("availability_risk_count must match rows")
    if digest.max_edge_score != max((row.edge_score for row in digest.rows), default=ZERO):
        raise ValueError("max_edge_score must match rows")
    if digest.risk_score != max((row.risk_score for row in digest.rows), default=ZERO):
        raise ValueError("risk_score must match rows")
    expected_status = "pass" if not digest.rows else _digest_status(digest.rows)
    if digest.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    if digest.next_step != _next_step(digest.digest_status):
        raise ValueError("next_step must match digest_status")
    expected_reasons = _digest_reasons(digest.rows)
    if digest.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[BaseballCatcherFramingEdgeMarketRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.edge_status == status))


def _reason_count(
    rows: tuple[BaseballCatcherFramingEdgeMarketRow, ...],
    reason: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason in row.reason_codes))


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
    checked = tuple({_require_member("reason_code", item, allowed) for item in value})
    return tuple(reason for reason in allowed if reason in checked)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    text = _require_text(field_name, value)
    if text not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return text


def _require_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonempty string")
    return value


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
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _seconds_between(later: datetime, earlier: datetime, earlier_name: str) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError(f"{earlier_name} must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _require_nonnegative_decimal(
        f"{earlier_name}_age_seconds",
        whole_seconds + fractional_seconds,
    )


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


def _count(value: object) -> Decimal:
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
        return {str(name): _json_ready(item) for name, item in value.items()}
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} requires {field_name}=True")


__all__ = (
    "DEFAULT_BASEBALL_CATCHER_FRAMING_EDGE_DIGEST_CONFIG_VERSION",
    "BaseballCatcherFramingEdgeDigestConfig",
    "BaseballCatcherFramingEdgeObservation",
    "BaseballCatcherFramingEdgeReasonCodeCount",
    "BaseballCatcherFramingEdgeMarketRow",
    "BaseballCatcherFramingEdgeDigest",
    "build_market_research_baseball_catcher_framing_edge_digest",
    "market_research_baseball_catcher_framing_edge_digest_payload",
)
