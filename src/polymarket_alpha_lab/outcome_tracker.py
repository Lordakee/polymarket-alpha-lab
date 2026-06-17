"""Outcome tracker v0 (Stage 9 live-layer).

Closes the self-judge verification loop: reads paper-traded markets from the
journal, re-fetches them from Gamma, checks which have resolved, and builds
``PaperForecastEvidenceObservation`` records (one per resolved trade LEG)
feeding the ``forecast_evidence`` calibration report. This tells the user
whether the LLM forecast's probability estimates are actually accurate over
time.

Phase 1 boundary: read-only Gamma ``/markets`` re-fetch + pure computation. No
orders, auth, wallets, private keys, credentials, relayers, account reads, or
exchange writes. The OUTPUT ``OutcomeTrackingReport`` is paper-only/report-only
(``paper_only is True`` / ``report_only is True`` hard-enforced with ``is``).

Protocol-only (Q5): this module does NOT import ``api``. It depends on a local
``OutcomeTrackerClient`` Protocol (a subset of
``strategy_cycle.MarketDataClient`` -- only ``list_markets`` is needed); the
concrete ``PolymarketPublicClient`` is constructed in ``cli.py`` and injected
into ``check_outcomes``.

CRITICAL (Stage 9 review #1): Gamma encodes the winning outcome in
``outcomePrices`` (array paired with ``outcomes``), NOT in ``resolutionStatus``
(which is usually None/empty). Example: ``outcomes=["Yes","No"]`` paired with
``outcomePrices=["1","0"]`` means YES won. This module reads ``outcomePrices``
directly from the raw Gamma payload (never ``resolutionStatus``) and never goes
through ``normalize_gamma_market`` (which does not surface ``outcomePrices``).

IMPORTANT (Stage 9 review #2): the trade's ``outcome_name`` is uppercase
(``"YES"``/``"NO"``) while Gamma's outcome labels are title-case
(``"Yes"``/``"No"``). The tracker maps both to a side kind via the SAME
``YES_NAMES``/``NO_NAMES`` alias sets used by ``cost_aware_snapshot_builder``
(case-insensitive membership, never direct string equality).

IMPORTANT (Stage 9 review #3): YES and NO legs are independent calibration
points (different ``predicted_probability``, different
``actual_outcome_value``). The tracker NEVER deduplicates observations by
``condition_id``; one resolved trade record produces exactly one observation.
The invariant is ``len(observations) == resolved trade leg count``.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceBucket,
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceGateResult,
    PaperForecastEvidenceObservation,
    PaperForecastEvidenceReport,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.json_recovery import from_jsonable


__all__ = (
    "OutcomeTrackingConfig",
    "OutcomeTrackingLog",
    "OutcomeTrackingReport",
    "check_outcomes",
)


ZERO = Decimal("0")
ONE = Decimal("1")

# Gamma's /markets endpoint caps a single page at 500 rows. Outcome tracking
# lists the CLOSED slice once per check; 500 is the largest single-page pull
# Gamma serves, so this is both the page ceiling and the scan budget.
CLOSED_MARKET_PAGE_LIMIT = 500

# Mirrors cost_aware_snapshot_builder.YES_NAMES / NO_NAMES verbatim. The tracker
# must classify YES/NO legs the SAME way the snapshot builder does, otherwise a
# "Yes"/"YES"/"Long" trade leg would mismatch its Gamma "Yes" winner label.
# Both the trade's outcome_name and Gamma's winning outcome label are
# normalized to lowercase and resolved through these alias sets (never direct
# string equality).
YES_NAMES = {"yes", "true", "long"}
NO_NAMES = {"no", "false", "short"}


@runtime_checkable
class OutcomeTrackerClient(Protocol):
    """Read-only public market-data surface for outcome tracking (Protocol-only).

    A deliberate subset of ``strategy_cycle.MarketDataClient``: outcome
    tracking only re-fetches the CLOSED Gamma ``/markets`` slice (no order
    books, no active markets). The concrete ``PolymarketPublicClient`` is
    constructed in ``cli.py`` and injected into ``check_outcomes``. This module
    never imports ``api``.
    """

    def list_markets(self, *, active: bool, closed: bool, limit: int) -> Any:
        """Return the raw public Gamma market list payload (closed slice)."""


@dataclass(frozen=True)
class OutcomeTrackingConfig:
    """Frozen paper-only/report-only configuration for ``check_outcomes``.

    ``config_version`` defaults to the canonical Stage 9 version string.
    ``forecast_evidence_config`` drives the downstream calibration report; its
    own ``config_version`` is kept in sync with the tracker's by default.
    """

    config_version: str = "outcome-tracker-v1"
    forecast_evidence_config: PaperForecastEvidenceConfig = field(
        default_factory=lambda: PaperForecastEvidenceConfig(
            config_version="outcome-tracker-v1",
        )
    )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if not isinstance(self.forecast_evidence_config, PaperForecastEvidenceConfig):
            raise ValueError(
                "forecast_evidence_config must be a PaperForecastEvidenceConfig"
            )


@dataclass(frozen=True)
class OutcomeTrackingReport:
    """Frozen paper-only/report-only outcome-tracking summary.

    Invariants (hard-enforced in ``__post_init__``):
      - ``resolved_count == len(observations)`` (one observation per resolved
        trade LEG; never deduplicated by ``condition_id``).
      - ``resolved_count + pending_count == total_markets_checked`` (every
        journaled trade leg is either resolved or pending).
      - ``forecast_evidence_report is None`` iff ``len(observations) == 0``.
      - ``paper_only is True`` and ``report_only is True`` (compared with ``is``).
    """

    generated_at: datetime
    config_version: str
    total_markets_checked: int
    resolved_count: int
    pending_count: int
    observations: tuple[PaperForecastEvidenceObservation, ...]
    forecast_evidence_report: PaperForecastEvidenceReport | None
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("total_markets_checked", self.total_markets_checked)
        _require_nonnegative_int("resolved_count", self.resolved_count)
        _require_nonnegative_int("pending_count", self.pending_count)
        object.__setattr__(
            self,
            "observations",
            _normalize_observation_tuple(self.observations),
        )
        if self.forecast_evidence_report is not None and not isinstance(
            self.forecast_evidence_report, PaperForecastEvidenceReport
        ):
            raise ValueError(
                "forecast_evidence_report must be a PaperForecastEvidenceReport or None"
            )
        if self.resolved_count + self.pending_count != self.total_markets_checked:
            raise ValueError(
                "resolved_count + pending_count must equal total_markets_checked"
            )
        if self.resolved_count != len(self.observations):
            raise ValueError(
                "resolved_count must equal the number of observations"
            )
        if len(self.observations) == 0 and self.forecast_evidence_report is not None:
            raise ValueError(
                "forecast_evidence_report must be None when there are no observations"
            )
        if len(self.observations) > 0 and self.forecast_evidence_report is None:
            raise ValueError(
                "forecast_evidence_report must not be None when there are observations"
            )
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")


@dataclass(frozen=True)
class OutcomeTrackingLog:
    """Append/read full outcome-tracking JSONL reports for local audit replay."""

    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: OutcomeTrackingReport) -> None:
        if not isinstance(report, OutcomeTrackingReport):
            raise ValueError("report must be an OutcomeTrackingReport")
        validated = _validate_report_tree(report)
        line = (
            json.dumps(
                _json_ready(asdict(validated)),
                allow_nan=False,
                sort_keys=True,
            )
            + "\n"
        )
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    @staticmethod
    def read(path: Path | str) -> tuple[OutcomeTrackingReport, ...]:
        """Read full outcome-tracking JSONL reports back into typed reports."""

        target = Path(path)
        records: list[OutcomeTrackingReport] = []
        with target.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"outcome tracking log line {line_number} "
                        f"is not valid JSON: {exc}",
                    ) from exc
                records.append(from_jsonable(OutcomeTrackingReport, row))
        return tuple(records)


def check_outcomes(
    *,
    client: OutcomeTrackerClient,
    journal_path: Path | str,
    config: OutcomeTrackingConfig,
    generated_at: datetime,
) -> OutcomeTrackingReport:
    """Read paper trades, re-fetch their markets, and build calibration evidence.

    Phase 1 (read-only): the only network surface is ``client.list_markets``
    on the CLOSED Gamma slice. The journal is read via
    ``PaperTradeJournal.read``. All downstream math is pure Decimal computation
    building ``PaperForecastEvidenceObservation`` values and (when at least one
    observation exists) a ``PaperForecastEvidenceReport``.

    Per trade leg:
      1. Look up the raw Gamma payload by ``condition_id``. Missing payload ->
         PENDING (no observation).
      2. Check the payload's ``closed``/``active`` flags. Not closed -> PENDING.
      3. Read ``outcomes`` + ``outcomePrices`` from the RAW payload (never
         ``resolutionStatus``) and resolve the winning outcome label. Ambiguous
         or unparseable -> PENDING.
      4. Classify both the trade's ``outcome_name`` and the winning label to a
         side kind via ``YES_NAMES``/``NO_NAMES`` (case-insensitive aliases).
         Unrecognized label -> PENDING.
      5. ``actual_outcome_value = Decimal("1")`` if the traded side WON, else
         ``Decimal("0")``. ``predicted_probability = research_fair_value_estimate``
         (P(traded side wins), aligning 1:1 with ``actual_outcome_value``).
      6. Build one ``PaperForecastEvidenceObservation`` per resolved leg (never
         deduplicated by ``condition_id``).
    """
    if not isinstance(client, OutcomeTrackerClient):
        raise ValueError("client must be an OutcomeTrackerClient")
    if not isinstance(config, OutcomeTrackingConfig):
        raise ValueError("config must be an OutcomeTrackingConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    records = _read_journal_records(journal_path)
    raw_payloads = _collect_closed_market_payloads(client)
    market_lookup = _build_market_lookup(raw_payloads)

    observations: list[PaperForecastEvidenceObservation] = []
    resolved_count = 0
    pending_count = 0

    for record in records:
        payload = market_lookup.get(record.condition_id)
        if payload is None:
            pending_count += 1
            continue
        if not _is_market_closed(payload):
            pending_count += 1
            continue
        winner_label = _resolve_winner_label(payload)
        if winner_label is None:
            pending_count += 1
            continue
        side_kind = _classify_outcome_label(record.outcome_name)
        winner_kind = _classify_outcome_label(winner_label)
        if side_kind is None or winner_kind is None:
            pending_count += 1
            continue
        actual_outcome_value = ONE if side_kind == winner_kind else ZERO
        resolved_count += 1
        observations.append(
            _build_observation(
                record=record,
                actual_outcome_value=actual_outcome_value,
                generated_at=generated_at,
            )
        )

    evidence_report = (
        build_paper_forecast_evidence_report(
            observations,
            config=config.forecast_evidence_config,
            generated_at=generated_at,
        )
        if observations
        else None
    )

    return OutcomeTrackingReport(
        generated_at=generated_at,
        config_version=config.config_version,
        total_markets_checked=len(records),
        resolved_count=resolved_count,
        pending_count=pending_count,
        observations=tuple(observations),
        forecast_evidence_report=evidence_report,
    )


def _read_journal_records(journal_path: Path | str) -> tuple[PaperTradeRecord, ...]:
    """Read the paper-trade journal, tolerating a missing file as benign.

    The continuous run loop journals paper trades only when paper execution is
    enabled and a screening-ready candidate appears; on a fresh setup (or with
    paper execution default-off) the journal may not exist yet. Mirroring
    ``runner.run_strategy_loop``'s first-run skip, a missing journal is treated
    as zero records rather than a hard error, so ``check_outcomes`` produces an
    empty report instead of crashing the CLI. A present-but-corrupt journal
    still raises (JSON/type errors propagate from ``PaperTradeJournal.read``).
    """
    try:
        return PaperTradeJournal.read(journal_path)
    except FileNotFoundError:
        return ()


def _collect_closed_market_payloads(client: OutcomeTrackerClient) -> list[dict[str, Any]]:
    """List the raw closed-market slice from Gamma and normalize its envelope.

    Gamma's ``/markets`` endpoint returns a bare JSON array of market objects.
    Some wrappers return ``{"markets": [...]}`` or ``{"data": [...]}``; both are
    tolerated. Non-dict entries are dropped (defensive). This is the ONLY
    network touchpoint in the tracker.
    """
    raw = client.list_markets(
        active=False,
        closed=True,
        limit=CLOSED_MARKET_PAGE_LIMIT,
    )
    if isinstance(raw, dict):
        candidate = raw.get("markets")
        if not isinstance(candidate, list):
            candidate = raw.get("data")
        if not isinstance(candidate, list):
            candidate = []
    elif isinstance(raw, list):
        candidate = raw
    else:
        candidate = []
    return [item for item in candidate if isinstance(item, dict)]


def _build_market_lookup(
    payloads: Iterable[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Index raw Gamma payloads by ``conditionId`` (first occurrence wins).

    Gamma occasionally returns duplicate rows across paginated slices; keeping
    the first makes the lookup deterministic.
    """
    lookup: dict[str, dict[str, Any]] = {}
    for payload in payloads:
        condition_id = str(payload.get("conditionId") or "").strip()
        if not condition_id:
            continue
        lookup.setdefault(condition_id, payload)
    return lookup


def _is_market_closed(payload: dict[str, Any]) -> bool:
    """Return True iff the raw payload marks the market as closed.

    Reads ``closed`` first (bool or "true"/"false" string); falls back to
    ``active is False``. A payload with neither flag is treated as NOT closed
    (PENDING) -- never silently treated as resolved.
    """
    closed_flag = payload.get("closed")
    if isinstance(closed_flag, bool):
        return closed_flag
    if isinstance(closed_flag, str):
        return closed_flag.strip().lower() == "true"
    active_flag = payload.get("active")
    if isinstance(active_flag, bool):
        return not active_flag
    if isinstance(active_flag, str):
        return active_flag.strip().lower() == "false"
    return False


def _resolve_winner_label(payload: dict[str, Any]) -> str | None:
    """Return the winning outcome label from the RAW Gamma payload.

    CRITICAL (Stage 9 review #1): reads ``outcomePrices`` (array paired with
    ``outcomes``), NEVER ``resolutionStatus``. For a resolved binary market
    Gamma sets the winning share's payout to ``"1"`` and the loser's to
    ``"0"`` (e.g. ``outcomes=["Yes","No"]`` paired with
    ``outcomePrices=["1","0"]`` means YES won).

    Resolution rule:
      1. If exactly one price equals ``Decimal("1")`` -> that index wins.
      2. Otherwise fall back to the index whose price is closest to 1 (handles
         near-resolution rounding like ``["0.9999","0.0001"]``); a strict tie
         (two indices share the max) is treated as ambiguous -> None.
      3. Missing/unequal-length ``outcomes``/``outcomePrices``, unparseable
         prices, or an out-of-range winner index -> None (PENDING).

    Both ``outcomes`` and ``outcomePrices`` may arrive as JSON-encoded strings
    (``'["Yes","No"]'``) or as native lists; both shapes are decoded.
    """
    outcomes = _as_string_list(payload.get("outcomes"))
    prices = _as_string_list(payload.get("outcomePrices"))
    if not outcomes or not prices or len(outcomes) != len(prices):
        return None

    parsed: list[tuple[int, Decimal]] = []
    for index, raw_price in enumerate(prices):
        try:
            value = Decimal(str(raw_price))
        except (InvalidOperation, ValueError, TypeError):
            return None
        if not value.is_finite():
            return None
        parsed.append((index, value))
    if not parsed or len(parsed) != len(outcomes):
        return None

    exact_winners = [item for item in parsed if item[1] == ONE]
    if len(exact_winners) == 1:
        return outcomes[exact_winners[0][0]]
    if len(exact_winners) > 1:
        return None

    max_value = max(item[1] for item in parsed)
    top = [item for item in parsed if item[1] == max_value]
    if len(top) != 1:
        return None
    return outcomes[top[0][0]]


def _classify_outcome_label(label: Any) -> str | None:
    """Map an outcome label to ``"yes"``/``"no"`` via the alias sets.

    IMPORTANT (Stage 9 review #2): case-insensitive alias membership, NEVER
    direct string equality. The trade's ``outcome_name`` is uppercase
    (``"YES"``/``"NO"``) while Gamma's outcome labels are title-case
    (``"Yes"``/``"No"``); both normalize to lowercase and resolve through the
    SAME ``YES_NAMES``/``NO_NAMES`` sets as ``cost_aware_snapshot_builder``.
    Unrecognized labels (e.g. multi-outcome ``"Option A"``) -> None (PENDING).
    """
    if not isinstance(label, str):
        return None
    normalized = label.strip().lower()
    if not normalized:
        return None
    if normalized in YES_NAMES:
        return "yes"
    if normalized in NO_NAMES:
        return "no"
    return None


def _build_observation(
    *,
    record: PaperTradeRecord,
    actual_outcome_value: Decimal,
    generated_at: datetime,
) -> PaperForecastEvidenceObservation:
    """Build one calibration observation for a resolved trade LEG.

    ``predicted_probability`` = ``research_fair_value_estimate`` (the LLM
    forecast's P(traded side wins), journaled at decision time), which aligns
    1:1 with ``actual_outcome_value`` (1 if the traded side won, 0 if it lost).
    ``source_packet_id`` = ``record.packet_id`` (unique per trade leg) so the
    downstream forecast-evidence dedup key (observed_at, token_id,
    source_packet_id) never collapses YES and NO legs of the same market.
    """
    return PaperForecastEvidenceObservation(
        observed_at=generated_at,
        source_packet_id=record.packet_id,
        condition_id=record.condition_id,
        token_id=record.token_id,
        market_slug=record.market_slug,
        strategy_type=record.strategy_type,
        risk_tags=record.risk_tags,
        predicted_probability=record.research_fair_value_estimate,
        actual_outcome_value=actual_outcome_value,
    )


def _as_string_list(value: Any) -> list[str]:
    """Decode a Gamma outcomes/outcomePrices field into a list of strings.

    Gamma returns these fields as either a native list (``["Yes","No"]``) or a
    JSON-encoded string (``'["Yes","No"]'``). Non-list JSON and non-string
    scalars coerce via ``str()`` so ``outcomePrices`` numeric values
    (``"1"``/``"0"`` or ``1``/``0``) both survive as strings.
    """
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            decoded = json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            return []
        if not isinstance(decoded, list):
            return []
        value = decoded
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _normalize_observation_tuple(
    value: Any,
) -> tuple[PaperForecastEvidenceObservation, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for item in items:
        if not isinstance(item, PaperForecastEvidenceObservation):
            raise ValueError(
                "observations must contain PaperForecastEvidenceObservation values"
            )
    return items


def _validate_report_tree(report: OutcomeTrackingReport) -> OutcomeTrackingReport:
    observations = tuple(
        PaperForecastEvidenceObservation(
            observed_at=observation.observed_at,
            source_packet_id=observation.source_packet_id,
            condition_id=observation.condition_id,
            token_id=observation.token_id,
            market_slug=observation.market_slug,
            strategy_type=observation.strategy_type,
            risk_tags=observation.risk_tags,
            predicted_probability=observation.predicted_probability,
            actual_outcome_value=observation.actual_outcome_value,
            theoretical_edge_ratio=observation.theoretical_edge_ratio,
            executable_edge_ratio=observation.executable_edge_ratio,
            fill_probability=observation.fill_probability,
            residual_exposure_ratio=observation.residual_exposure_ratio,
            paper_return_ratio=observation.paper_return_ratio,
            paper_only=observation.paper_only,
        )
        for observation in _normalize_observation_tuple(report.observations)
    )
    forecast_evidence_report = (
        None
        if report.forecast_evidence_report is None
        else _clone_forecast_evidence_report(report.forecast_evidence_report)
    )
    return OutcomeTrackingReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        total_markets_checked=report.total_markets_checked,
        resolved_count=report.resolved_count,
        pending_count=report.pending_count,
        observations=observations,
        forecast_evidence_report=forecast_evidence_report,
        paper_only=report.paper_only,
        report_only=report.report_only,
    )


def _clone_forecast_evidence_report(
    report: PaperForecastEvidenceReport,
) -> PaperForecastEvidenceReport:
    if not isinstance(report, PaperForecastEvidenceReport):
        raise ValueError("forecast_evidence_report must be a PaperForecastEvidenceReport")
    gate_results = tuple(
        PaperForecastEvidenceGateResult(
            gate_name=gate.gate_name,
            status=gate.status,
            message=gate.message,
            observed_value=gate.observed_value,
            threshold=gate.threshold,
        )
        for gate in report.gate_results
    )
    buckets = tuple(
        PaperForecastEvidenceBucket(
            bucket_label=bucket.bucket_label,
            lower_probability=bucket.lower_probability,
            upper_probability=bucket.upper_probability,
            observation_count=bucket.observation_count,
            mean_predicted_probability=bucket.mean_predicted_probability,
            observed_frequency=bucket.observed_frequency,
            bucket_error=bucket.bucket_error,
            mean_probability_loss=bucket.mean_probability_loss,
        )
        for bucket in report.buckets
    )
    return PaperForecastEvidenceReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        first_observed_at=report.first_observed_at,
        last_observed_at=report.last_observed_at,
        observation_count=report.observation_count,
        probability_observation_count=report.probability_observation_count,
        edge_observation_count=report.edge_observation_count,
        unique_market_count=report.unique_market_count,
        unique_strategy_count=report.unique_strategy_count,
        unique_risk_tag_count=report.unique_risk_tag_count,
        mean_probability_loss=report.mean_probability_loss,
        worst_bucket_error=report.worst_bucket_error,
        mean_edge_gap_ratio=report.mean_edge_gap_ratio,
        positive_edge_hit_rate=report.positive_edge_hit_rate,
        worst_residual_exposure_ratio=report.worst_residual_exposure_ratio,
        status=report.status,
        gate_results=gate_results,
        buckets=buckets,
        paper_only=report.paper_only,
    )


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative integer")


def _require_finite_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_positive_int(field_name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        _require_finite_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("outcome tracking log values must be JSON serializable")


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str) and not value.strip():
        raise ValueError("path is required")
    try:
        path = Path(value)
    except TypeError as exc:
        raise ValueError("path must be path-like") from exc
    if path.exists() and path.is_dir():
        raise ValueError("path must be a file path")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    for parent in (path.parent, *path.parent.parents):
        if parent.exists():
            if not parent.is_dir():
                raise ValueError("path parent must be a directory")
            return
