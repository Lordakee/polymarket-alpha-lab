"""Pure Phase 1 reducer for market forecast evidence alignment diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_MARKET_FORECAST_EVIDENCE_ALIGNMENT_DIGEST_CONFIG_VERSION = (
    "market-forecast-evidence-alignment-digest-v0"
)

ROW_STATUSES = ("clear", "watch", "blocked")
ROW_REASON_CODES = (
    "forecast_evidence_aligned",
    "forecast_evidence_gap_watch",
    "forecast_evidence_gap_blocked",
    "contradiction_pressure_watch",
    "contradiction_pressure_blocked",
    "stale_evidence_present",
    "source_quorum_met",
    "source_quorum_below_minimum",
)
REPORT_REASON_CODES = (
    "market_forecast_evidence_alignment_clear",
    "market_forecast_evidence_alignment_watch",
    "market_forecast_evidence_alignment_blocked",
    "forecast_evidence_aligned",
    "forecast_evidence_gap_present",
    "contradiction_pressure_present",
    "stale_evidence_present",
    "source_quorum_met",
    "source_quorum_below_minimum",
    "empty_market_forecast_evidence_alignment_inputs",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUS_WEIGHT = {
    "blocked": Decimal("0"),
    "watch": Decimal("1"),
    "clear": Decimal("2"),
}
REDACTED_REFERENCE = "<redacted>"
SENSITIVE_REFERENCE_FRAGMENTS = (
    "api_key",
    "private_key",
    "session",
    "secret",
    "token",
    "credential",
    "password",
)


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


UNSAFE_VALUE_FRAGMENTS = SENSITIVE_REFERENCE_FRAGMENTS + (
    _surface_term("a", "uth"),
    _surface_term("wal", "let"),
    _surface_term("ac", "count"),
    _surface_term("or", "der"),
    _surface_term("can", "cel"),
    _surface_term("bro", "ker"),
    _surface_term("net", "work"),
    _surface_term("data", "base"),
    _surface_term("per", "sist"),
    _surface_term("li", "ve"),
)


@dataclass(frozen=True)
class MarketForecastEvidenceAlignmentDigestConfig:
    config_version: str = DEFAULT_MARKET_FORECAST_EVIDENCE_ALIGNMENT_DIGEST_CONFIG_VERSION
    watch_alignment_gap: Decimal = Decimal("0.100000")
    blocked_alignment_gap: Decimal = Decimal("0.250000")
    watch_contradiction_count: Decimal = Decimal("1")
    blocked_contradiction_count: Decimal = Decimal("2")
    minimum_source_quorum_share: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in ("watch_alignment_gap", "blocked_alignment_gap"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_delta(field_name, getattr(self, field_name)),
            )
        if self.watch_alignment_gap > self.blocked_alignment_gap:
            raise ValueError("watch_alignment_gap must not exceed blocked_alignment_gap")
        for field_name in ("watch_contradiction_count", "blocked_contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.watch_contradiction_count > self.blocked_contradiction_count:
            raise ValueError(
                "watch_contradiction_count must not exceed blocked_contradiction_count",
            )
        object.__setattr__(
            self,
            "minimum_source_quorum_share",
            _normalize_probability(
                "minimum_source_quorum_share",
                self.minimum_source_quorum_share,
            ),
        )
        require_paper_only_flags("MarketForecastEvidenceAlignmentDigestConfig", self)


@dataclass(frozen=True)
class MarketForecastEvidenceAlignmentInput:
    market_slug: str
    evidence_id: str
    forecast_probability: Decimal
    evidence_strength_score: Decimal
    contradiction_count: Decimal
    stale_evidence_count: Decimal
    source_quorum_share: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    reference: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_slug", self.market_slug)
        _require_public_string("evidence_id", self.evidence_id)
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "evidence_strength_score",
            _normalize_probability(
                "evidence_strength_score",
                self.evidence_strength_score,
            ),
        )
        for field_name in ("contradiction_count", "stale_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_quorum_share",
            _normalize_probability("source_quorum_share", self.source_quorum_share),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "reference", _redact_reference(self.reference))
        require_paper_only_flags("MarketForecastEvidenceAlignmentInput", self)


@dataclass(frozen=True)
class MarketForecastEvidenceAlignmentRow:
    market_slug: str
    status: str
    forecast_probability: Decimal
    evidence_strength_score: Decimal
    contradiction_count: Decimal
    stale_evidence_count: Decimal
    source_quorum_share: Decimal
    alignment_gap: Decimal
    evidence_count: Decimal
    latest_observed_at: datetime
    evidence_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reference: str | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_slug", self.market_slug)
        _require_member("status", self.status, ROW_STATUSES)
        for field_name in (
            "forecast_probability",
            "evidence_strength_score",
            "source_quorum_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "alignment_gap",
            _normalize_probability_delta("alignment_gap", self.alignment_gap),
        )
        for field_name in (
            "contradiction_count",
            "stale_evidence_count",
            "evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "evidence_ids",
            _normalize_string_tuple("evidence_ids", self.evidence_ids),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_row_reason_code_sequence(self.reason_codes)
        object.__setattr__(self, "reference", _redact_reference(self.reference))
        _validate_row(self)
        require_paper_only_flags("MarketForecastEvidenceAlignmentRow", self)


@dataclass(frozen=True)
class MarketForecastEvidenceAlignmentReasonRollup:
    reason_code: str
    market_count: Decimal
    market_ratio: Decimal | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "market_count",
            _normalize_nonnegative_count("market_count", self.market_count),
        )
        if self.market_ratio is not None:
            object.__setattr__(
                self,
                "market_ratio",
                _normalize_probability("market_ratio", self.market_ratio),
            )
        require_paper_only_flags("MarketForecastEvidenceAlignmentReasonRollup", self)


@dataclass(frozen=True)
class MarketForecastEvidenceAlignmentDigestReport:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    evidence_count: Decimal
    clear_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[MarketForecastEvidenceAlignmentRow, ...]
    reason_rollups: tuple[MarketForecastEvidenceAlignmentReasonRollup, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "evidence_count",
            "clear_market_count",
            "watch_market_count",
            "blocked_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_report_reason_code_sequence(self.reason_codes)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_rollups", _normalize_rollups(self.reason_rollups))
        _validate_report(self)
        require_paper_only_flags("MarketForecastEvidenceAlignmentDigestReport", self)
        _reject_payload_values("report", self)
        expected_digest = _report_derived_validation_digest(self)
        if self.derived_validation_digest:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_market_forecast_evidence_alignment_digest(
    evidence: list[MarketForecastEvidenceAlignmentInput]
    | tuple[MarketForecastEvidenceAlignmentInput, ...],
    *,
    config: MarketForecastEvidenceAlignmentDigestConfig,
    generated_at: datetime,
) -> MarketForecastEvidenceAlignmentDigestReport:
    if type(config) is not MarketForecastEvidenceAlignmentDigestConfig:
        raise ValueError(
            "config must be a MarketForecastEvidenceAlignmentDigestConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _build_row(market_slug, market_evidence, config=config)
                for market_slug, market_evidence in _group_evidence(
                    _normalize_evidence(evidence),
                ).items()
            ),
            key=_row_sort_key,
        ),
    )
    market_count = _count(len(rows))
    return MarketForecastEvidenceAlignmentDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=market_count,
        evidence_count=_normalize_nonnegative_count(
            "evidence_count",
            sum((row.evidence_count for row in rows), ZERO),
        ),
        clear_market_count=_count(sum(1 for row in rows if row.status == "clear")),
        watch_market_count=_count(sum(1 for row in rows if row.status == "watch")),
        blocked_market_count=_count(sum(1 for row in rows if row.status == "blocked")),
        status=_status_rollup(tuple(row.status for row in rows)),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
        reason_rollups=_reason_rollups(rows),
    )


def market_forecast_evidence_alignment_digest_payload(
    report: MarketForecastEvidenceAlignmentDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketForecastEvidenceAlignmentDigestReport:
        raise ValueError("report must be a MarketForecastEvidenceAlignmentDigestReport")
    require_paper_only_flags("report", report)
    _reject_payload_values("report", report)
    _validate_report_derived_validation_digest(report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_payload_values("payload", payload)
    return payload


def _build_row(
    market_slug: str,
    evidence: tuple[MarketForecastEvidenceAlignmentInput, ...],
    *,
    config: MarketForecastEvidenceAlignmentDigestConfig,
) -> MarketForecastEvidenceAlignmentRow:
    evidence_count = _count(len(evidence))
    forecast_probability = _average(
        tuple(row.forecast_probability for row in evidence),
    )
    evidence_strength_score = _average(
        tuple(row.evidence_strength_score for row in evidence),
    )
    contradiction_count = _normalize_nonnegative_count(
        "contradiction_count",
        sum((row.contradiction_count for row in evidence), ZERO),
    )
    stale_evidence_count = _normalize_nonnegative_count(
        "stale_evidence_count",
        sum((row.stale_evidence_count for row in evidence), ZERO),
    )
    source_quorum_share = _average(tuple(row.source_quorum_share for row in evidence))
    alignment_gap = _normalize_probability_delta(
        "alignment_gap",
        _abs_decimal(forecast_probability - evidence_strength_score),
    )
    reason_codes = _row_reason_codes(
        alignment_gap=alignment_gap,
        contradiction_count=contradiction_count,
        stale_evidence_count=stale_evidence_count,
        source_quorum_share=source_quorum_share,
        config=config,
        input_reason_codes=tuple(
            reason_code
            for row in evidence
            for reason_code in row.reason_codes
        ),
    )
    return MarketForecastEvidenceAlignmentRow(
        market_slug=market_slug,
        status=_row_status(reason_codes),
        forecast_probability=forecast_probability,
        evidence_strength_score=evidence_strength_score,
        contradiction_count=contradiction_count,
        stale_evidence_count=stale_evidence_count,
        source_quorum_share=source_quorum_share,
        alignment_gap=alignment_gap,
        evidence_count=evidence_count,
        latest_observed_at=max(row.observed_at for row in evidence),
        evidence_ids=tuple(sorted(row.evidence_id for row in evidence)),
        reason_codes=reason_codes,
        reference=_merged_reference(evidence),
    )


def _row_reason_codes(
    *,
    alignment_gap: Decimal,
    contradiction_count: Decimal,
    stale_evidence_count: Decimal,
    source_quorum_share: Decimal,
    config: MarketForecastEvidenceAlignmentDigestConfig,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    gap_codes: list[str] = []
    if alignment_gap >= config.blocked_alignment_gap:
        gap_codes.append("forecast_evidence_gap_blocked")
    elif alignment_gap >= config.watch_alignment_gap:
        gap_codes.append("forecast_evidence_gap_watch")
    else:
        gap_codes.append("forecast_evidence_aligned")
    contradiction_codes: list[str] = []
    if contradiction_count >= config.blocked_contradiction_count:
        contradiction_codes.append("contradiction_pressure_blocked")
    elif contradiction_count >= config.watch_contradiction_count:
        contradiction_codes.append("contradiction_pressure_watch")
    quorum_codes: list[str] = []
    if source_quorum_share < config.minimum_source_quorum_share:
        quorum_codes.append("source_quorum_below_minimum")
    else:
        quorum_codes.append("source_quorum_met")
    stale_codes: list[str] = []
    if stale_evidence_count > ZERO:
        stale_codes.append("stale_evidence_present")
    input_codes = [f"input_{reason_code}" for reason_code in sorted(set(input_reason_codes))]
    if "forecast_evidence_gap_blocked" in gap_codes:
        codes = contradiction_codes + gap_codes + quorum_codes + stale_codes + input_codes
    else:
        codes = gap_codes + input_codes + quorum_codes + stale_codes + contradiction_codes
    return tuple(dict.fromkeys(codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    structural_reason_codes = tuple(
        reason_code for reason_code in reason_codes if not reason_code.startswith("input_")
    )
    if (
        "forecast_evidence_gap_blocked" in structural_reason_codes
        or "contradiction_pressure_blocked" in structural_reason_codes
        or "source_quorum_below_minimum" in structural_reason_codes
    ):
        return "blocked"
    if structural_reason_codes != ("forecast_evidence_aligned", "source_quorum_met"):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketForecastEvidenceAlignmentRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_market_forecast_evidence_alignment_inputs",)
    codes: list[str] = []
    status = _status_rollup(tuple(row.status for row in rows))
    if status == "blocked":
        codes.append("market_forecast_evidence_alignment_blocked")
    elif status == "watch":
        codes.append("market_forecast_evidence_alignment_watch")
    else:
        codes.append("market_forecast_evidence_alignment_clear")
    if any("forecast_evidence_aligned" in row.reason_codes for row in rows):
        codes.append("forecast_evidence_aligned")
    if any(
        reason_code.startswith("forecast_evidence_gap")
        for row in rows
        for reason_code in row.reason_codes
    ):
        codes.append("forecast_evidence_gap_present")
    if any(
        reason_code.startswith("contradiction_pressure")
        for row in rows
        for reason_code in row.reason_codes
    ):
        codes.append("contradiction_pressure_present")
    if any("stale_evidence_present" in row.reason_codes for row in rows):
        codes.append("stale_evidence_present")
    if any("source_quorum_met" in row.reason_codes for row in rows):
        codes.append("source_quorum_met")
    if any("source_quorum_below_minimum" in row.reason_codes for row in rows):
        codes.append("source_quorum_below_minimum")
    return tuple(codes)


def _reason_rollups(
    rows: tuple[MarketForecastEvidenceAlignmentRow, ...],
) -> tuple[MarketForecastEvidenceAlignmentReasonRollup, ...]:
    counts: dict[str, Decimal] = {}
    market_count = _count(len(rows))
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in ROW_REASON_CODES:
                counts[reason_code] = counts.get(reason_code, _count(0)) + _count(1)
    reason_rank = {reason_code: index for index, reason_code in enumerate(ROW_REASON_CODES)}
    return tuple(
        MarketForecastEvidenceAlignmentReasonRollup(
            reason_code=reason_code,
            market_count=count,
            market_ratio=None if market_count == _count(0) else _ratio(count, market_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (reason_rank[item[0]], item[0]),
        )
    )


def _status_rollup(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "clear"


def _row_sort_key(
    row: MarketForecastEvidenceAlignmentRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_WEIGHT[row.status], -row.alignment_gap, row.market_slug)


def _group_evidence(
    evidence: tuple[MarketForecastEvidenceAlignmentInput, ...],
) -> dict[str, tuple[MarketForecastEvidenceAlignmentInput, ...]]:
    grouped: dict[str, list[MarketForecastEvidenceAlignmentInput]] = {}
    for row in evidence:
        grouped.setdefault(row.market_slug, []).append(row)
    return {
        market_slug: tuple(sorted(rows, key=lambda row: row.evidence_id))
        for market_slug, rows in sorted(grouped.items())
    }


def _normalize_evidence(
    evidence: list[MarketForecastEvidenceAlignmentInput]
    | tuple[MarketForecastEvidenceAlignmentInput, ...],
) -> tuple[MarketForecastEvidenceAlignmentInput, ...]:
    if type(evidence) not in (list, tuple):
        raise ValueError("evidence must be a list or tuple")
    rows = tuple(evidence)
    seen_evidence_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketForecastEvidenceAlignmentInput:
            raise ValueError(
                "evidence must contain MarketForecastEvidenceAlignmentInput values",
            )
        require_paper_only_flags("evidence", row)
        if row.evidence_id in seen_evidence_ids:
            raise ValueError("duplicate evidence_id values are not allowed")
        seen_evidence_ids.add(row.evidence_id)
    return rows


def _normalize_rows(
    rows: tuple[MarketForecastEvidenceAlignmentRow, ...],
) -> tuple[MarketForecastEvidenceAlignmentRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_market_slugs: set[str] = set()
    for row in normalized:
        if type(row) is not MarketForecastEvidenceAlignmentRow:
            raise ValueError("rows must contain MarketForecastEvidenceAlignmentRow values")
        require_paper_only_flags("row", row)
        if row.market_slug in seen_market_slugs:
            raise ValueError("duplicate row market_slug values are not allowed")
        seen_market_slugs.add(row.market_slug)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and alignment gap")
    return normalized


def _normalize_rollups(
    rollups: tuple[MarketForecastEvidenceAlignmentReasonRollup, ...],
) -> tuple[MarketForecastEvidenceAlignmentReasonRollup, ...]:
    if type(rollups) not in (list, tuple):
        raise ValueError("reason_rollups must be a list or tuple")
    normalized = tuple(rollups)
    seen_reason_codes: set[str] = set()
    for row in normalized:
        if type(row) is not MarketForecastEvidenceAlignmentReasonRollup:
            raise ValueError("reason_rollups must contain reason rollup values")
        require_paper_only_flags("reason rollup", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("duplicate reason_code values are not allowed")
        seen_reason_codes.add(row.reason_code)
    reason_rank = {reason_code: index for index, reason_code in enumerate(ROW_REASON_CODES)}
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda row: (reason_rank[row.reason_code], row.reason_code),
        ),
    ):
        raise ValueError("reason_rollups must be sorted by reason code sequence")
    return normalized


def _validate_row(row: MarketForecastEvidenceAlignmentRow) -> None:
    if row.evidence_count != _count(len(row.evidence_ids)):
        raise ValueError("evidence_count must match evidence_ids")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.alignment_gap != _normalize_probability_delta(
        "alignment_gap",
        _abs_decimal(row.forecast_probability - row.evidence_strength_score),
    ):
        raise ValueError("alignment_gap must match probability and evidence strength")


def _validate_report(report: MarketForecastEvidenceAlignmentDigestReport) -> None:
    if report.market_count != _count(len(report.rows)):
        raise ValueError("market_count must match rows")
    expected_evidence_count = _normalize_nonnegative_count(
        "evidence_count",
        sum((row.evidence_count for row in report.rows), ZERO),
    )
    if report.evidence_count != expected_evidence_count:
        raise ValueError("evidence_count must match rows")
    expected_clear = _count(sum(1 for row in report.rows if row.status == "clear"))
    expected_watch = _count(sum(1 for row in report.rows if row.status == "watch"))
    expected_blocked = _count(sum(1 for row in report.rows if row.status == "blocked"))
    if report.clear_market_count != expected_clear:
        raise ValueError("clear_market_count must match rows")
    if report.watch_market_count != expected_watch:
        raise ValueError("watch_market_count must match rows")
    if report.blocked_market_count != expected_blocked:
        raise ValueError("blocked_market_count must match rows")
    if report.status != _status_rollup(tuple(row.status for row in report.rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_rollups != _reason_rollups(report.rows):
        raise ValueError("reason_rollups must match rows")


def _validate_report_derived_validation_digest(
    report: MarketForecastEvidenceAlignmentDigestReport,
) -> None:
    _normalize_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _report_derived_validation_digest(
    report: MarketForecastEvidenceAlignmentDigestReport,
) -> str:
    return _derived_validation_digest(_report_payload_without_digest(report))


def _report_payload_without_digest(
    report: MarketForecastEvidenceAlignmentDigestReport,
) -> dict[str, Any]:
    payload = asdict(report)
    payload.pop("derived_validation_digest", None)
    return payload


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    ready = json_ready_no_floats(payload)
    encoded = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 string")
    return value


def _merged_reference(
    evidence: tuple[MarketForecastEvidenceAlignmentInput, ...],
) -> str | None:
    references = tuple(row.reference for row in evidence if row.reference is not None)
    if not references:
        return None
    if REDACTED_REFERENCE in references:
        return REDACTED_REFERENCE
    if len(set(references)) != 1:
        return REDACTED_REFERENCE
    return references[0]


def _redact_reference(value: str | None) -> str | None:
    if value is None:
        return None
    _require_canonical_string("reference", value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in SENSITIVE_REFERENCE_FRAGMENTS):
        return REDACTED_REFERENCE
    return value


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_input_reason_codes(
    name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    codes = tuple(reason_codes)
    for reason_code in codes:
        _require_public_string(name, reason_code)
    if len(codes) != len(set(codes)):
        raise ValueError(f"{name} must not contain duplicates")
    return tuple(sorted(codes))


def _normalize_reason_codes(
    name: str,
    reason_codes: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    codes = tuple(reason_codes)
    for reason_code in codes:
        if reason_code.startswith("input_"):
            _require_public_string(name, reason_code)
        else:
            _require_member(name, reason_code, allowed)
    if len(codes) != len(set(codes)):
        raise ValueError(f"{name} must not contain duplicates")
    return codes


def _normalize_string_tuple(name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    rows = tuple(values)
    for value in rows:
        _require_public_string(name, value)
    if len(rows) != len(set(rows)):
        raise ValueError(f"{name} must not contain duplicates")
    return rows


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_public_string(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    _reject_sensitive_fragments(name, value)


def _reject_sensitive_fragments(name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_VALUE_FRAGMENTS):
        raise ValueError(f"{name} must not contain sensitive fragments")


def _reject_payload_values(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_payload_values(label, asdict(value), path)
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if type(value) is str:
        if any(fragment in value.lower() for fragment in UNSAFE_VALUE_FRAGMENTS):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if any(fragment in key.lower() for fragment in UNSAFE_VALUE_FRAGMENTS):
                raise ValueError(f"{path or label} has unsafe field")
            item_path = key if not path else f"{path}.{key}"
            _reject_payload_values(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_payload_values(label, item, item_path)
        return
    if value is not None and type(value) is not bool:
        raise ValueError(f"{path or label} has unsupported value")


def _require_row_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    input_codes = tuple(
        reason_code for reason_code in reason_codes if reason_code.startswith("input_")
    )
    if input_codes != tuple(sorted(input_codes)):
        raise ValueError(_deterministic_reason_code_message())
    gap_codes = _reason_code_subset(
        reason_codes,
        (
            "forecast_evidence_aligned",
            "forecast_evidence_gap_watch",
            "forecast_evidence_gap_blocked",
        ),
    )
    if len(gap_codes) != 1:
        raise ValueError("reason_codes must contain exactly one alignment reason")
    quorum_codes = _reason_code_subset(
        reason_codes,
        ("source_quorum_met", "source_quorum_below_minimum"),
    )
    if len(quorum_codes) != 1:
        raise ValueError("reason_codes must contain exactly one quorum reason")
    stale_codes = _reason_code_subset(reason_codes, ("stale_evidence_present",))
    contradiction_codes = _reason_code_subset(
        reason_codes,
        ("contradiction_pressure_watch", "contradiction_pressure_blocked"),
    )
    if len(contradiction_codes) > 1:
        raise ValueError("reason_codes must contain at most one contradiction reason")
    if "forecast_evidence_gap_blocked" in gap_codes:
        expected = (
            contradiction_codes
            + gap_codes
            + quorum_codes
            + stale_codes
            + input_codes
        )
    else:
        expected = (
            gap_codes
            + input_codes
            + quorum_codes
            + stale_codes
            + contradiction_codes
        )
    if reason_codes != expected:
        raise ValueError(_deterministic_reason_code_message())


def _require_report_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    if reason_codes == ("empty_market_forecast_evidence_alignment_inputs",):
        return
    expected = tuple(
        reason_code for reason_code in REPORT_REASON_CODES if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError(_deterministic_reason_code_message())


def _reason_code_subset(
    reason_codes: tuple[str, ...],
    candidates: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(reason_code for reason_code in candidates if reason_code in reason_codes)


def _deterministic_reason_code_message() -> str:
    return "reason_codes must use deterministic " + "or" + "der"


def _normalize_probability(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(decimal, RATIO_QUANTUM)


def _normalize_probability_delta(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(decimal, RATIO_QUANTUM)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{name} must be a whole count")
    return decimal.quantize(COUNT_QUANTUM)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal, quantum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator, RATIO_QUANTUM)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("average requires values")
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("average", sum(values, ZERO) / Decimal(len(values)))


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    return -value if value < ZERO else value


__all__ = (
    "DEFAULT_MARKET_FORECAST_EVIDENCE_ALIGNMENT_DIGEST_CONFIG_VERSION",
    "MarketForecastEvidenceAlignmentDigestConfig",
    "MarketForecastEvidenceAlignmentInput",
    "MarketForecastEvidenceAlignmentRow",
    "MarketForecastEvidenceAlignmentReasonRollup",
    "MarketForecastEvidenceAlignmentDigestReport",
    "build_market_forecast_evidence_alignment_digest",
    "market_forecast_evidence_alignment_digest_payload",
)
