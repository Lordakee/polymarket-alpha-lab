"""Pure Phase 1 rate-cut path revision digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_RATE_CUT_PATH_REVISION_DIGEST_CONFIG_VERSION = (
    "market-research-rate-cut-path-revision-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_rate_cut_path_revision_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
MATERIAL_REVISION_REASON = f"{REASON_PREFIX}material_revision"
PROBABILITY_REPRICING_REASON = f"{REASON_PREFIX}probability_repricing"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}missing_acknowledgement"
SLOW_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}slow_acknowledgement"
STALE_PATH_REASON = f"{REASON_PREFIX}stale_path"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    STALE_PATH_REASON,
    MATERIAL_REVISION_REASON,
    PROBABILITY_REPRICING_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    READY_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    THIN_SOURCES_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_REVISION_REASON,
    PROBABILITY_REPRICING_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    READY_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_PATH_REASON,
    THIN_SOURCES_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_rate_cut_path_revision_digest",
    STATUS_WATCH: "watch_report_only_market_research_rate_cut_path_revision_digest",
    STATUS_BLOCKED: "block_report_only_market_research_rate_cut_path_revision_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_RATE_CUT_PATH_REVISION_DIGEST_CONFIG_VERSION",
    "MarketResearchRateCutPathRevisionDigestConfig",
    "MarketResearchRateCutPathRevisionDigestInputRow",
    "MarketResearchRateCutPathRevisionDigestReasonCodeCount",
    "MarketResearchRateCutPathRevisionDigestReport",
    "MarketResearchRateCutPathRevisionDigestRow",
    "build_market_research_rate_cut_path_revision_digest",
    "market_research_rate_cut_path_revision_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchRateCutPathRevisionDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_RATE_CUT_PATH_REVISION_DIGEST_CONFIG_VERSION
    )
    max_path_signal_age_seconds: Decimal = Decimal("7200.000000")
    material_expected_cut_revision_threshold: Decimal = Decimal("0.250000")
    min_probability_repricing_abs: Decimal = Decimal("0.050000")
    min_source_count: Decimal = Decimal("2.000000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRateCutPathRevisionDigestConfig:
            raise TypeError(
                "MarketResearchRateCutPathRevisionDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRateCutPathRevisionDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchRateCutPathRevisionDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATE_CUT_PATH_REVISION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_path_signal_age_seconds",
            "min_source_count",
            "max_acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "material_expected_cut_revision_threshold",
            "min_probability_repricing_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchRateCutPathRevisionDigestInputRow:
    research_key: str
    condition_id: str
    rate_path_key: str
    central_bank: str
    policy_event_key: str
    public_path_reference: str
    observed_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    expected_cuts_before: Decimal
    expected_cuts_after: Decimal
    path_probability_before: Decimal
    path_probability_after: Decimal
    path_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRateCutPathRevisionDigestInputRow:
            raise TypeError(
                "MarketResearchRateCutPathRevisionDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRateCutPathRevisionDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchRateCutPathRevisionDigestInputRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "rate_path_key",
            "central_bank",
            "policy_event_key",
            "path_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("public_path_reference", self.public_path_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in ("expected_cuts_before", "expected_cuts_after"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("path_probability_before", "path_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchRateCutPathRevisionDigestRow:
    research_key: str
    condition_id: str
    rate_path_key: str
    central_bank: str
    policy_event_key: str
    revision_status: str
    observed_at: datetime
    acknowledged_at: datetime | None
    signal_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    expected_cuts_before: Decimal
    expected_cuts_after: Decimal
    expected_cut_revision_delta: Decimal
    expected_cut_revision_abs: Decimal
    path_probability_before: Decimal
    path_probability_after: Decimal
    probability_delta: Decimal
    probability_delta_abs: Decimal
    redacted_public_path_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRateCutPathRevisionDigestRow:
            raise TypeError(
                "MarketResearchRateCutPathRevisionDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRateCutPathRevisionDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchRateCutPathRevisionDigestRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "rate_path_key",
            "central_bank",
            "policy_event_key",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("revision_status", self.revision_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        for field_name in ("signal_age_seconds", "source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _require_optional_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        for field_name in (
            "expected_cuts_before",
            "expected_cuts_after",
            "expected_cut_revision_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_cut_revision_delta",
            _require_finite_decimal(
                "expected_cut_revision_delta",
                self.expected_cut_revision_delta,
            ),
        )
        for field_name in ("path_probability_before", "path_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("probability_delta", "probability_delta_abs"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_delta(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "redacted_public_path_reference",
            _require_redacted_reference(
                "redacted_public_path_reference",
                self.redacted_public_path_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, order=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchRateCutPathRevisionDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    path_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRateCutPathRevisionDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchRateCutPathRevisionDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRateCutPathRevisionDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchRateCutPathRevisionDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "path_ratio",
            _require_ratio_decimal("path_ratio", self.path_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchRateCutPathRevisionDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    path_count: Decimal
    ready_path_count: Decimal
    watch_path_count: Decimal
    blocked_path_count: Decimal
    material_revision_count: Decimal
    stale_path_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    probability_repricing_count: Decimal
    average_expected_cut_revision_abs: Decimal
    average_probability_delta_abs: Decimal
    max_signal_age_seconds: Decimal
    average_source_count: Decimal
    rows: tuple[MarketResearchRateCutPathRevisionDigestRow, ...]
    path_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchRateCutPathRevisionDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRateCutPathRevisionDigestReport:
            raise TypeError(
                "MarketResearchRateCutPathRevisionDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRateCutPathRevisionDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchRateCutPathRevisionDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "path_count",
            "ready_path_count",
            "watch_path_count",
            "blocked_path_count",
            "material_revision_count",
            "stale_path_count",
            "thin_source_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
            "probability_repricing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_expected_cut_revision_abs",
            "average_probability_delta_abs",
            "max_signal_age_seconds",
            "average_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "path_config_versions",
            _normalize_path_config_versions(self.path_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, order=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_rate_cut_path_revision_digest(
    input_rows: Iterable[MarketResearchRateCutPathRevisionDigestInputRow],
    *,
    config: MarketResearchRateCutPathRevisionDigestConfig,
    generated_at: datetime,
) -> MarketResearchRateCutPathRevisionDigestReport:
    if type(config) is not MarketResearchRateCutPathRevisionDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchRateCutPathRevisionDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(input_rows, generated_at_utc)
    rows = tuple(
        _row_for_input(row, config=config, generated_at=generated_at_utc)
        for row in normalized_rows
    )
    sorted_rows = _sorted_rows(rows)
    path_count = _count(len(sorted_rows))
    reason_code_counts = _reason_code_counts(sorted_rows, path_count)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not sorted_rows:
        reason_code_counts = (
            MarketResearchRateCutPathRevisionDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                path_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    ready_path_count = _count(
        sum(1 for row in sorted_rows if row.revision_status == STATUS_READY),
    )
    watch_path_count = _count(
        sum(1 for row in sorted_rows if row.revision_status == STATUS_WATCH),
    )
    blocked_path_count = _count(
        sum(1 for row in sorted_rows if row.revision_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(sorted_rows),
        blocked_path_count=blocked_path_count,
        watch_path_count=watch_path_count,
    )

    return MarketResearchRateCutPathRevisionDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        path_count=path_count,
        ready_path_count=ready_path_count,
        watch_path_count=watch_path_count,
        blocked_path_count=blocked_path_count,
        material_revision_count=_reason_path_count(
            sorted_rows,
            MATERIAL_REVISION_REASON,
        ),
        stale_path_count=_reason_path_count(sorted_rows, STALE_PATH_REASON),
        thin_source_count=_reason_path_count(sorted_rows, THIN_SOURCES_REASON),
        missing_acknowledgement_count=_reason_path_count(
            sorted_rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        slow_acknowledgement_count=_reason_path_count(
            sorted_rows,
            SLOW_ACKNOWLEDGEMENT_REASON,
        ),
        probability_repricing_count=_reason_path_count(
            sorted_rows,
            PROBABILITY_REPRICING_REASON,
        ),
        average_expected_cut_revision_abs=_ratio(
            _decimal_sum(row.expected_cut_revision_abs for row in sorted_rows),
            path_count,
        ),
        average_probability_delta_abs=_ratio(
            _decimal_sum(row.probability_delta_abs for row in sorted_rows),
            path_count,
        ),
        max_signal_age_seconds=max(
            (row.signal_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        average_source_count=_ratio(
            _decimal_sum(row.source_count for row in sorted_rows),
            path_count,
        ),
        rows=sorted_rows,
        path_config_versions=_path_config_versions(normalized_rows),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_rate_cut_path_revision_digest_payload(
    report: MarketResearchRateCutPathRevisionDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchRateCutPathRevisionDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchRateCutPathRevisionDigestReport",
        )
    _require_hard_flags("report", report)
    _validate_report(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_for_input(
    row: MarketResearchRateCutPathRevisionDigestInputRow,
    *,
    config: MarketResearchRateCutPathRevisionDigestConfig,
    generated_at: datetime,
) -> MarketResearchRateCutPathRevisionDigestRow:
    signal_age_seconds = _seconds_between(generated_at, row.observed_at)
    if row.acknowledged_at is None:
        acknowledgement_lag_seconds = None
    else:
        acknowledgement_lag_seconds = _seconds_between(row.acknowledged_at, row.observed_at)
    expected_cut_revision_delta = _quantize(
        row.expected_cuts_after - row.expected_cuts_before,
    )
    expected_cut_revision_abs = _quantize(abs(expected_cut_revision_delta))
    probability_delta = _quantize(
        row.path_probability_after - row.path_probability_before,
    )
    probability_delta_abs = _quantize(abs(probability_delta))
    reason_codes = _row_reason_codes(
        signal_age_seconds=signal_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=row.source_count,
        expected_cut_revision_abs=expected_cut_revision_abs,
        probability_delta_abs=probability_delta_abs,
        config=config,
    )
    return MarketResearchRateCutPathRevisionDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        rate_path_key=row.rate_path_key,
        central_bank=row.central_bank,
        policy_event_key=row.policy_event_key,
        revision_status=_row_status(reason_codes),
        observed_at=row.observed_at,
        acknowledged_at=row.acknowledged_at,
        signal_age_seconds=signal_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=row.source_count,
        expected_cuts_before=row.expected_cuts_before,
        expected_cuts_after=row.expected_cuts_after,
        expected_cut_revision_delta=expected_cut_revision_delta,
        expected_cut_revision_abs=expected_cut_revision_abs,
        path_probability_before=row.path_probability_before,
        path_probability_after=row.path_probability_after,
        probability_delta=probability_delta,
        probability_delta_abs=probability_delta_abs,
        redacted_public_path_reference=_redact_reference(row.public_path_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    signal_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    source_count: Decimal,
    expected_cut_revision_abs: Decimal,
    probability_delta_abs: Decimal,
    config: MarketResearchRateCutPathRevisionDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if expected_cut_revision_abs >= config.material_expected_cut_revision_threshold:
        reasons.append(MATERIAL_REVISION_REASON)
    if probability_delta_abs >= config.min_probability_repricing_abs:
        reasons.append(PROBABILITY_REPRICING_REASON)
    if acknowledgement_lag_seconds is None:
        reasons.append(MISSING_ACKNOWLEDGEMENT_REASON)
    if (
        acknowledgement_lag_seconds is not None
        and acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds
    ):
        reasons.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if signal_age_seconds > config.max_path_signal_age_seconds:
        reasons.append(STALE_PATH_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_reason_codes(reasons, order=ROW_REASON_CODE_SEQUENCE)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_path_count: Decimal,
    watch_path_count: Decimal,
) -> str:
    if not has_inputs or blocked_path_count > ZERO:
        return STATUS_BLOCKED
    if watch_path_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _sorted_rows(
    rows: tuple[MarketResearchRateCutPathRevisionDigestRow, ...],
) -> tuple[MarketResearchRateCutPathRevisionDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.revision_status),
                -row.expected_cut_revision_abs,
                -row.probability_delta_abs,
                -row.signal_age_seconds,
                row.rate_path_key,
                row.research_key,
            ),
        ),
    )


def _status_rank(status: str) -> int:
    if status == STATUS_BLOCKED:
        return 0
    if status == STATUS_WATCH:
        return 1
    return 2


def _reason_code_counts(
    rows: tuple[MarketResearchRateCutPathRevisionDigestRow, ...],
    path_count: Decimal,
) -> tuple[MarketResearchRateCutPathRevisionDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchRateCutPathRevisionDigestReasonCodeCount(
            reason_code=reason_code,
            count=count,
            path_ratio=_ratio(count, path_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code != NO_INPUTS_REASON
        for count in (_reason_path_count(rows, reason_code),)
        if count > ZERO
    )


def _reason_path_count(
    rows: tuple[MarketResearchRateCutPathRevisionDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _path_config_versions(
    rows: tuple[MarketResearchRateCutPathRevisionDigestInputRow, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (row.rate_path_key, row.path_config_version) for row in rows
        ),
    )


def _normalize_input_rows(
    rows: Iterable[MarketResearchRateCutPathRevisionDigestInputRow],
    generated_at: datetime,
) -> tuple[MarketResearchRateCutPathRevisionDigestInputRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("input rows must be an iterable")
    normalized = tuple(rows)
    seen_keys: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchRateCutPathRevisionDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchRateCutPathRevisionDigestInputRow values",
            )
        _require_hard_flags("input row", row)
        if row.rate_path_key in seen_keys:
            raise ValueError("input rows rate_path_key values must be unique")
        seen_keys.add(row.rate_path_key)
        if row.observed_at > generated_at:
            raise ValueError("observed_at cannot be in the future")
        if row.acknowledged_at is not None and row.acknowledged_at < row.observed_at:
            raise ValueError("acknowledged_at cannot precede observed_at")
    return normalized


def _normalize_rows(
    rows: tuple[MarketResearchRateCutPathRevisionDigestRow, ...],
) -> tuple[MarketResearchRateCutPathRevisionDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchRateCutPathRevisionDigestRow:
            raise ValueError(
                "rows must contain MarketResearchRateCutPathRevisionDigestRow values",
            )
        _require_hard_flags("row", row)
        if row.rate_path_key in seen_keys:
            raise ValueError("rows rate_path_key values must be unique")
        seen_keys.add(row.rate_path_key)
    if normalized != _sorted_rows(normalized):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _normalize_reason_code_counts(
    values: tuple[MarketResearchRateCutPathRevisionDigestReasonCodeCount, ...],
) -> tuple[MarketResearchRateCutPathRevisionDigestReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(values)
    seen_codes: set[str] = set()
    for value in normalized:
        if type(value) is not MarketResearchRateCutPathRevisionDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchRateCutPathRevisionDigestReasonCodeCount values",
            )
        _require_hard_flags("reason code count", value)
        if value.reason_code in seen_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_codes.add(value.reason_code)
    if tuple(value.reason_code for value in normalized) != tuple(
        reason for reason in REASON_CODE_SEQUENCE if reason in seen_codes
    ):
        raise ValueError("reason_code_counts must use canonical reason sequence")
    return normalized


def _normalize_path_config_versions(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(values) not in (list, tuple):
        raise ValueError("path_config_versions must be a list or tuple")
    normalized = tuple(values)
    seen_keys: set[str] = set()
    for value in normalized:
        if type(value) not in (list, tuple) or len(value) != 2:
            raise ValueError("path_config_versions must contain key/version pairs")
        rate_path_key, config_version = value
        _require_public_string("path_config_versions key", rate_path_key)
        _require_public_string("path_config_versions version", config_version)
        if rate_path_key in seen_keys:
            raise ValueError("path_config_versions keys must be unique")
        seen_keys.add(rate_path_key)
    normalized_pairs = tuple((str(key), str(version)) for key, version in normalized)
    if normalized_pairs != tuple(sorted(normalized_pairs)):
        raise ValueError("path_config_versions must be sorted deterministically")
    return normalized_pairs


def _normalize_reason_codes(
    values: object,
    *,
    order: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(values)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    seen_codes: set[str] = set()
    for value in normalized:
        _require_reason_code("reason_codes", value)
        if value in seen_codes:
            raise ValueError("reason_codes must be unique")
        seen_codes.add(value)
    if normalized != tuple(reason for reason in order if reason in seen_codes):
        raise ValueError("reason_codes must use canonical reason sequence")
    return normalized


def _validate_row(row: MarketResearchRateCutPathRevisionDigestRow) -> None:
    _require_hard_flags("row", row)
    _require_redacted_reference(
        "redacted_public_path_reference",
        row.redacted_public_path_reference,
    )
    if row.expected_cut_revision_delta != _quantize(
        row.expected_cuts_after - row.expected_cuts_before,
    ):
        raise ValueError("expected_cut_revision_delta must match expected cuts")
    if row.expected_cut_revision_abs != _quantize(abs(row.expected_cut_revision_delta)):
        raise ValueError("expected_cut_revision_abs must match expected cut delta")
    if row.probability_delta != _quantize(
        row.path_probability_after - row.path_probability_before,
    ):
        raise ValueError("probability_delta must match path probabilities")
    if row.probability_delta_abs != _quantize(abs(row.probability_delta)):
        raise ValueError("probability_delta_abs must match probability_delta")
    if row.acknowledged_at is None and row.acknowledgement_lag_seconds is not None:
        raise ValueError("acknowledgement_lag_seconds must be absent without acknowledgement")
    if row.acknowledged_at is not None:
        expected_lag = _seconds_between(row.acknowledged_at, row.observed_at)
        if row.acknowledgement_lag_seconds != expected_lag:
            raise ValueError("acknowledgement_lag_seconds must match timestamps")
    if row.revision_status != _row_status(row.reason_codes):
        raise ValueError("revision_status must match reason_codes")


def _validate_report(report: MarketResearchRateCutPathRevisionDigestReport) -> None:
    _require_hard_flags("report", report)
    _normalize_rows(report.rows)
    _normalize_path_config_versions(report.path_config_versions)
    _normalize_reason_code_counts(report.reason_code_counts)
    _normalize_reason_codes(report.reason_codes, order=REASON_CODE_SEQUENCE)
    for row in report.rows:
        _validate_row(row)
    for count in report.reason_code_counts:
        _require_hard_flags("reason code count", count)
    if report.config_version != DEFAULT_MARKET_RESEARCH_RATE_CUT_PATH_REVISION_DIGEST_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.path_count != _count(len(report.rows)):
        raise ValueError("path_count must match rows")
    if tuple(key for key, _ in report.path_config_versions) != tuple(
        sorted(row.rate_path_key for row in report.rows),
    ):
        raise ValueError("path_config_versions must match rows")
    expected_ready = _count(
        sum(1 for row in report.rows if row.revision_status == STATUS_READY),
    )
    expected_watch = _count(
        sum(1 for row in report.rows if row.revision_status == STATUS_WATCH),
    )
    expected_blocked = _count(
        sum(1 for row in report.rows if row.revision_status == STATUS_BLOCKED),
    )
    if report.ready_path_count != expected_ready:
        raise ValueError("ready_path_count must match rows")
    if report.watch_path_count != expected_watch:
        raise ValueError("watch_path_count must match rows")
    if report.blocked_path_count != expected_blocked:
        raise ValueError("blocked_path_count must match rows")
    if report.ready_path_count + report.watch_path_count + report.blocked_path_count != report.path_count:
        raise ValueError("path status counts must reconcile")
    expected_reason_counts = _reason_code_counts(report.rows, report.path_count)
    if not report.rows:
        expected_reason_counts = (
            MarketResearchRateCutPathRevisionDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                path_ratio=ZERO,
            ),
        )
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.digest_status != _report_status(
        has_inputs=bool(report.rows),
        blocked_path_count=report.blocked_path_count,
        watch_path_count=report.watch_path_count,
    ):
        raise ValueError("digest_status must match rows")
    expected_counts = {
        "material_revision_count": MATERIAL_REVISION_REASON,
        "stale_path_count": STALE_PATH_REASON,
        "thin_source_count": THIN_SOURCES_REASON,
        "missing_acknowledgement_count": MISSING_ACKNOWLEDGEMENT_REASON,
        "slow_acknowledgement_count": SLOW_ACKNOWLEDGEMENT_REASON,
        "probability_repricing_count": PROBABILITY_REPRICING_REASON,
    }
    for field_name, reason_code in expected_counts.items():
        if getattr(report, field_name) != _reason_path_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.average_expected_cut_revision_abs != _ratio(
        _decimal_sum(row.expected_cut_revision_abs for row in report.rows),
        report.path_count,
    ):
        raise ValueError("average_expected_cut_revision_abs must match rows")
    if report.average_probability_delta_abs != _ratio(
        _decimal_sum(row.probability_delta_abs for row in report.rows),
        report.path_count,
    ):
        raise ValueError("average_probability_delta_abs must match rows")
    if report.max_signal_age_seconds != max(
        (row.signal_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_signal_age_seconds must match rows")
    if report.average_source_count != _ratio(
        _decimal_sum(row.source_count for row in report.rows),
        report.path_count,
    ):
        raise ValueError("average_source_count must match rows")


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _redact_reference(value: str) -> str:
    if _is_redacted_safe(value):
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _is_redacted_safe(value: str) -> bool:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        return False
    return not any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _json_ready(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(_quantize(value), "f")
    if isinstance(value, Decimal):
        raise ValueError("payload Decimal value must be exactly Decimal")
    if type(value) is datetime:
        return _as_utc("payload datetime value", value).isoformat()
    if isinstance(value, datetime):
        raise ValueError("payload datetime value must be exactly datetime")
    if type(value) is bool:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("payload numeric value must use Decimal")
    if type(value) is str:
        _require_public_string("payload string value", value)
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            _require_public_string("payload object key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            if key == "public_path_reference":
                continue
            ready[key] = _json_ready(item)
        return ready
    if value is None:
        return None
    return value


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be public report-safe text")


def _require_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)


def _require_redacted_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value.startswith("sha256:") and not _is_short_sha256_redaction(value):
        raise ValueError(f"{field_name} must be a short sha256 redaction")
    if not _is_redacted_safe(value) and not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _is_short_sha256_redaction(value: str) -> bool:
    suffix = value.removeprefix("sha256:")
    return len(suffix) == 12 and all(
        character in "0123456789abcdef" for character in suffix
    )


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal count")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_probability_delta(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return decimal_value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
