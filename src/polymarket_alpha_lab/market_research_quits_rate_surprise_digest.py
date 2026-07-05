"""Pure Phase 1 quits-rate surprise digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_QUITS_RATE_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-quits-rate-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_quits_rate_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
NO_MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}no_material_surprise"
MATERIAL_POSITIVE_SURPRISE_REASON = f"{REASON_PREFIX}material_positive_surprise"
MATERIAL_NEGATIVE_SURPRISE_REASON = f"{REASON_PREFIX}material_negative_surprise"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}stale_observation"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
MISSING_CONSENSUS_REASON = f"{REASON_PREFIX}missing_consensus"
WATCH_REASON = f"{REASON_PREFIX}watch"

REASON_CODE_SEQUENCE = (
    MATERIAL_POSITIVE_SURPRISE_REASON,
    MATERIAL_NEGATIVE_SURPRISE_REASON,
    STALE_OBSERVATION_REASON,
    THIN_SOURCES_REASON,
    MISSING_CONSENSUS_REASON,
    WATCH_REASON,
    NO_MATERIAL_SURPRISE_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_POSITIVE_SURPRISE_REASON,
    MATERIAL_NEGATIVE_SURPRISE_REASON,
    STALE_OBSERVATION_REASON,
    THIN_SOURCES_REASON,
    MISSING_CONSENSUS_REASON,
    NO_MATERIAL_SURPRISE_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_quits_rate_surprise",
    STATUS_WATCH: "watch_report_only_quits_rate_surprise",
    STATUS_BLOCKED: "block_report_only_quits_rate_surprise",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "can" + "cel",
    "re" + "place",
    "ex" + "change",
    "tra" + "de",
    "trad" + "ing",
    "pri" + "vate" + "_" + "key",
    "api" + "_" + "key",
    "sec" + "ret",
    "to" + "ken",
    "data" + "base",
    "net" + "work",
    "http" + "://",
    "https" + "://",
    "bear" + "er",
    "pass" + "word",
    "cred" + "ential",
    "sign" + "ature",
    "sign" + "ing",
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_QUITS_RATE_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchQuitsRateSurpriseDigestConfig",
    "MarketResearchQuitsRateSurpriseDigestObservation",
    "MarketResearchQuitsRateSurpriseDigestReasonCodeCount",
    "MarketResearchQuitsRateSurpriseDigestReport",
    "MarketResearchQuitsRateSurpriseDigestRow",
    "build_market_research_quits_rate_surprise_digest",
    "market_research_quits_rate_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchQuitsRateSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_QUITS_RATE_SURPRISE_DIGEST_CONFIG_VERSION
    )
    material_surprise_threshold: Decimal = Decimal("0.100000")
    max_observation_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchQuitsRateSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchQuitsRateSurpriseDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchQuitsRateSurpriseDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchQuitsRateSurpriseDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_QUITS_RATE_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "material_surprise_threshold",
            _require_ratio_decimal(
                "material_surprise_threshold",
                self.material_surprise_threshold,
            ),
        )
        object.__setattr__(
            self,
            "max_observation_age_seconds",
            _require_positive_count_decimal(
                "max_observation_age_seconds",
                self.max_observation_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchQuitsRateSurpriseDigestObservation:
    release_id: str
    market_slug: str
    observed_at: datetime
    actual_quits_rate: Decimal
    consensus_quits_rate: Decimal
    previous_quits_rate: Decimal
    source_count: Decimal
    release_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchQuitsRateSurpriseDigestObservation:
            raise TypeError(
                "MarketResearchQuitsRateSurpriseDigestObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchQuitsRateSurpriseDigestObservation:
            raise ValueError(
                "observation must be exactly "
                "MarketResearchQuitsRateSurpriseDigestObservation",
            )
        for field_name in ("release_id", "market_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference_string("release_reference", self.release_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "actual_quits_rate",
            "consensus_quits_rate",
            "previous_quits_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchQuitsRateSurpriseDigestRow:
    release_id: str
    market_slug: str
    observed_at: datetime
    digest_status: str
    observation_age_seconds: Decimal
    actual_quits_rate: Decimal
    consensus_quits_rate: Decimal
    previous_quits_rate: Decimal
    source_count: Decimal
    quits_rate_surprise: Decimal
    surprise_ratio: Decimal
    redacted_release_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchQuitsRateSurpriseDigestRow:
            raise TypeError(
                "MarketResearchQuitsRateSurpriseDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchQuitsRateSurpriseDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchQuitsRateSurpriseDigestRow",
            )
        for field_name in ("release_id", "market_slug", "redacted_release_reference"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("digest_status", self.digest_status)
        for field_name in (
            "observation_age_seconds",
            "actual_quits_rate",
            "consensus_quits_rate",
            "previous_quits_rate",
            "source_count",
            "quits_rate_surprise",
            "surprise_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        _require_nonnegative_decimal(
            "observation_age_seconds",
            self.observation_age_seconds,
        )
        _require_nonnegative_count_decimal("source_count", self.source_count)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchQuitsRateSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchQuitsRateSurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchQuitsRateSurpriseDigestReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchQuitsRateSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchQuitsRateSurpriseDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio_decimal("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchQuitsRateSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    material_surprise_count: Decimal
    positive_surprise_count: Decimal
    negative_surprise_count: Decimal
    stale_observation_count: Decimal
    thin_source_count: Decimal
    missing_consensus_count: Decimal
    largest_abs_surprise_ratio: Decimal
    average_surprise_ratio: Decimal
    average_source_count: Decimal
    observations: tuple[MarketResearchQuitsRateSurpriseDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketResearchQuitsRateSurpriseDigestReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchQuitsRateSurpriseDigestReport:
            raise TypeError(
                "MarketResearchQuitsRateSurpriseDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchQuitsRateSurpriseDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchQuitsRateSurpriseDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "observation_count",
            "material_surprise_count",
            "positive_surprise_count",
            "negative_surprise_count",
            "stale_observation_count",
            "thin_source_count",
            "missing_consensus_count",
            "largest_abs_surprise_ratio",
            "average_surprise_ratio",
            "average_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "observation_count",
            "material_surprise_count",
            "positive_surprise_count",
            "negative_surprise_count",
            "stale_observation_count",
            "thin_source_count",
            "missing_consensus_count",
        ):
            _require_nonnegative_count_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "largest_abs_surprise_ratio",
            "average_surprise_ratio",
            "average_source_count",
        ):
            if getattr(self, field_name) < ZERO:
                raise ValueError(f"{field_name} must be nonnegative")
        object.__setattr__(
            self,
            "observations",
            _normalize_rows(self.observations),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_quits_rate_surprise_digest(
    observations: tuple[object, ...],
    *,
    generated_at: datetime,
    config: MarketResearchQuitsRateSurpriseDigestConfig | None = None,
) -> MarketResearchQuitsRateSurpriseDigestReport:
    cfg = config or MarketResearchQuitsRateSurpriseDigestConfig()
    if type(cfg) is not MarketResearchQuitsRateSurpriseDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchQuitsRateSurpriseDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _build_row(observation, generated_at=generated_at_utc, config=cfg)
                for observation in _normalize_input_observations(observations)
            ),
            key=lambda row: (row.release_id, row.observed_at, row.market_slug),
        ),
    )
    reason_codes = _report_reason_codes(rows)
    digest_status = _report_status(rows, reason_codes)
    reason_code_counts = _reason_code_counts(reason_codes, rows)
    return MarketResearchQuitsRateSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        observation_count=_decimal_count(len(rows)),
        material_surprise_count=_decimal_count(
            sum(
                1
                for row in rows
                if MATERIAL_POSITIVE_SURPRISE_REASON in row.reason_codes
                or MATERIAL_NEGATIVE_SURPRISE_REASON in row.reason_codes
            ),
        ),
        positive_surprise_count=_decimal_count(
            sum(1 for row in rows if MATERIAL_POSITIVE_SURPRISE_REASON in row.reason_codes),
        ),
        negative_surprise_count=_decimal_count(
            sum(1 for row in rows if MATERIAL_NEGATIVE_SURPRISE_REASON in row.reason_codes),
        ),
        stale_observation_count=_decimal_count(
            sum(1 for row in rows if STALE_OBSERVATION_REASON in row.reason_codes),
        ),
        thin_source_count=_decimal_count(
            sum(1 for row in rows if THIN_SOURCES_REASON in row.reason_codes),
        ),
        missing_consensus_count=_decimal_count(
            sum(1 for row in rows if MISSING_CONSENSUS_REASON in row.reason_codes),
        ),
        largest_abs_surprise_ratio=_largest_abs_surprise_ratio(rows),
        average_surprise_ratio=_average_abs_surprise_ratio(rows),
        average_source_count=_average_source_count(rows),
        observations=rows,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
    )


def market_research_quits_rate_surprise_digest_payload(
    report: MarketResearchQuitsRateSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchQuitsRateSurpriseDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchQuitsRateSurpriseDigestReport",
        )
    _validate_report(report)
    payload = asdict(report)
    return _serialize_payload(payload)


def _build_row(
    observation: MarketResearchQuitsRateSurpriseDigestObservation,
    *,
    generated_at: datetime,
    config: MarketResearchQuitsRateSurpriseDigestConfig,
) -> MarketResearchQuitsRateSurpriseDigestRow:
    age_seconds = _seconds_between(generated_at, observation.observed_at)
    if age_seconds < ZERO:
        raise ValueError("observed_at cannot be after generated_at")
    if observation.consensus_quits_rate == ZERO:
        surprise = ZERO
        surprise_ratio = ZERO
    else:
        surprise = _quantize(observation.actual_quits_rate - observation.consensus_quits_rate)
        surprise_ratio = _ratio(surprise, observation.consensus_quits_rate)
    reason_codes = _row_reason_codes(
        quits_rate_surprise=surprise,
        surprise_ratio=surprise_ratio,
        consensus_quits_rate=observation.consensus_quits_rate,
        observation_age_seconds=age_seconds,
        source_count=observation.source_count,
        config=config,
    )
    return MarketResearchQuitsRateSurpriseDigestRow(
        release_id=observation.release_id,
        market_slug=observation.market_slug,
        observed_at=observation.observed_at,
        digest_status=_row_status(reason_codes),
        observation_age_seconds=age_seconds,
        actual_quits_rate=_quantize(observation.actual_quits_rate),
        consensus_quits_rate=_quantize(observation.consensus_quits_rate),
        previous_quits_rate=_quantize(observation.previous_quits_rate),
        source_count=_quantize(observation.source_count),
        quits_rate_surprise=surprise,
        surprise_ratio=surprise_ratio,
        redacted_release_reference=_redact_reference(observation.release_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    quits_rate_surprise: Decimal,
    surprise_ratio: Decimal,
    consensus_quits_rate: Decimal,
    observation_age_seconds: Decimal,
    source_count: Decimal,
    config: MarketResearchQuitsRateSurpriseDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if consensus_quits_rate == ZERO:
        reasons.append(MISSING_CONSENSUS_REASON)
    elif quits_rate_surprise >= config.material_surprise_threshold:
        reasons.append(MATERIAL_POSITIVE_SURPRISE_REASON)
    elif quits_rate_surprise <= -config.material_surprise_threshold:
        reasons.append(MATERIAL_NEGATIVE_SURPRISE_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if consensus_quits_rate == ZERO:
        reasons.append(NO_MATERIAL_SURPRISE_REASON)
    if not reasons:
        reasons.append(NO_MATERIAL_SURPRISE_REASON)
    return _normalize_reason_codes(
        tuple(reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in reasons),
        sequence=ROW_REASON_CODE_SEQUENCE,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if MISSING_CONSENSUS_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (NO_MATERIAL_SURPRISE_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_reason_codes(
    rows: tuple[MarketResearchQuitsRateSurpriseDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    present = {reason_code for row in rows for reason_code in row.reason_codes}
    reasons: list[str] = [
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in present and reason_code != NO_MATERIAL_SURPRISE_REASON
    ]
    if (
        NO_MATERIAL_SURPRISE_REASON in present
        and not any(row.digest_status == STATUS_WATCH for row in rows)
    ):
        reasons.append(NO_MATERIAL_SURPRISE_REASON)
    if any(row.digest_status == STATUS_WATCH for row in rows):
        reasons.append(WATCH_REASON)
    return _normalize_reason_codes(tuple(reasons), sequence=REASON_CODE_SEQUENCE)


def _report_status(
    rows: tuple[MarketResearchQuitsRateSurpriseDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> str:
    if not rows or MISSING_CONSENSUS_REASON in reason_codes:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchQuitsRateSurpriseDigestRow, ...],
) -> tuple[MarketResearchQuitsRateSurpriseDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchQuitsRateSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                observation_ratio=ZERO,
            ),
        )
    total = _decimal_count(len(rows))
    return tuple(
        MarketResearchQuitsRateSurpriseDigestReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(reason_code, rows),
            observation_ratio=_ratio(_reason_count(reason_code, rows), total),
        )
        for reason_code in reason_codes
    )


def _reason_count(
    reason_code: str,
    rows: tuple[MarketResearchQuitsRateSurpriseDigestRow, ...],
) -> Decimal:
    if reason_code == WATCH_REASON:
        return _decimal_count(sum(1 for row in rows if row.digest_status == STATUS_WATCH))
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _largest_abs_surprise_ratio(
    rows: tuple[MarketResearchQuitsRateSurpriseDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize(max(abs(row.surprise_ratio) for row in rows))


def _average_abs_surprise_ratio(
    rows: tuple[MarketResearchQuitsRateSurpriseDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio(sum(abs(row.surprise_ratio) for row in rows), _decimal_count(len(rows)))


def _average_source_count(
    rows: tuple[MarketResearchQuitsRateSurpriseDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio(sum(row.source_count for row in rows), _decimal_count(len(rows)))


def _normalize_input_observations(
    observations: tuple[object, ...],
) -> tuple[MarketResearchQuitsRateSurpriseDigestObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, tuple):
        raise ValueError("observations must be a tuple")
    for observation in observations:
        if type(observation) is not MarketResearchQuitsRateSurpriseDigestObservation:
            raise ValueError(
                "observations must contain exactly "
                "MarketResearchQuitsRateSurpriseDigestObservation",
            )
        _require_hard_flags("observation", observation)
    return observations


def _normalize_rows(
    rows: tuple[MarketResearchQuitsRateSurpriseDigestRow, ...],
) -> tuple[MarketResearchQuitsRateSurpriseDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, tuple):
        raise ValueError("observations must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchQuitsRateSurpriseDigestRow:
            raise ValueError(
                "observations must contain exactly "
                "MarketResearchQuitsRateSurpriseDigestRow",
            )
        _require_hard_flags("row", row)
    expected = tuple(
        sorted(rows, key=lambda row: (row.release_id, row.observed_at, row.market_slug)),
    )
    if rows != expected:
        raise ValueError("observations must use deterministic ordering")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchQuitsRateSurpriseDigestReasonCodeCount, ...],
) -> tuple[MarketResearchQuitsRateSurpriseDigestReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not MarketResearchQuitsRateSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "MarketResearchQuitsRateSurpriseDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
    expected = tuple(
        sorted(counts, key=lambda count: REASON_CODE_SEQUENCE.index(count.reason_code)),
    )
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic ordering")
    return counts


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, tuple):
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in sequence:
            raise ValueError("reason_codes must contain supported reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    normalized = tuple(reason_code for reason_code in sequence if reason_code in reason_codes)
    if normalized != reason_codes:
        raise ValueError("reason_codes must use deterministic ordering")
    return reason_codes


def _validate_row(row: MarketResearchQuitsRateSurpriseDigestRow) -> None:
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if row.digest_status == STATUS_READY and row.reason_codes != (
        NO_MATERIAL_SURPRISE_REASON,
    ):
        raise ValueError("ready rows must only use no material surprise")
    if (
        row.digest_status == STATUS_BLOCKED
        and MISSING_CONSENSUS_REASON not in row.reason_codes
    ):
        raise ValueError("blocked rows must include missing consensus")
    if row.digest_status == STATUS_WATCH and not any(
        reason in row.reason_codes
        for reason in (
            MATERIAL_POSITIVE_SURPRISE_REASON,
            MATERIAL_NEGATIVE_SURPRISE_REASON,
            STALE_OBSERVATION_REASON,
            THIN_SOURCES_REASON,
        )
    ):
        raise ValueError("watch rows must include a watch reason")


def _validate_report(report: MarketResearchQuitsRateSurpriseDigestReport) -> None:
    rows = report.observations
    if report.observation_count != _decimal_count(len(rows)):
        raise ValueError("observation_count must match observations")
    count_checks = (
        (
            "material_surprise_count",
            report.material_surprise_count,
            _decimal_count(
                sum(
                    1
                    for row in rows
                    if MATERIAL_POSITIVE_SURPRISE_REASON in row.reason_codes
                    or MATERIAL_NEGATIVE_SURPRISE_REASON in row.reason_codes
                ),
            ),
        ),
        (
            "positive_surprise_count",
            report.positive_surprise_count,
            _decimal_count(
                sum(
                    1
                    for row in rows
                    if MATERIAL_POSITIVE_SURPRISE_REASON in row.reason_codes
                ),
            ),
        ),
        (
            "negative_surprise_count",
            report.negative_surprise_count,
            _decimal_count(
                sum(
                    1
                    for row in rows
                    if MATERIAL_NEGATIVE_SURPRISE_REASON in row.reason_codes
                ),
            ),
        ),
        (
            "stale_observation_count",
            report.stale_observation_count,
            _decimal_count(
                sum(1 for row in rows if STALE_OBSERVATION_REASON in row.reason_codes),
            ),
        ),
        (
            "thin_source_count",
            report.thin_source_count,
            _decimal_count(
                sum(1 for row in rows if THIN_SOURCES_REASON in row.reason_codes),
            ),
        ),
        (
            "missing_consensus_count",
            report.missing_consensus_count,
            _decimal_count(
                sum(1 for row in rows if MISSING_CONSENSUS_REASON in row.reason_codes),
            ),
        ),
    )
    for field_name, actual, expected in count_checks:
        if actual != expected:
            raise ValueError(f"{field_name} must match observations")
    if report.largest_abs_surprise_ratio != _largest_abs_surprise_ratio(rows):
        raise ValueError("largest_abs_surprise_ratio must match observations")
    if report.average_surprise_ratio != _average_abs_surprise_ratio(rows):
        raise ValueError("average_surprise_ratio must match observations")
    if report.average_source_count != _average_source_count(rows):
        raise ValueError("average_source_count must match observations")
    expected_codes = _report_reason_codes(rows)
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match observations")
    expected_status = _report_status(rows, report.reason_codes)
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match observations")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    expected_counts = _reason_code_counts(report.reason_codes, rows)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match observations")
    for row in rows:
        if row.observed_at > report.generated_at:
            raise ValueError("row observed_at cannot be after generated_at")
        if row.observation_age_seconds != _seconds_between(
            report.generated_at,
            row.observed_at,
        ):
            raise ValueError("row observation_age_seconds must match generated_at")


def _serialize_payload(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload numeric values must be Decimal")
        if not value.is_finite():
            raise ValueError("payload numeric values must be finite")
        return f"{value.quantize(QUANT):f}"
    if isinstance(value, datetime):
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is str:
        _require_public_string("payload", value)
        return value
    if type(value) is bool or value is None:
        return value
    if isinstance(value, float) or type(value) is int:
        raise ValueError("payload numeric values must use Decimal")
    if isinstance(value, tuple):
        return [_serialize_payload(item) for item in value]
    if isinstance(value, list):
        return [_serialize_payload(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be plain str")
            _require_public_string("payload key", key)
            ready[key] = _serialize_payload(item)
        return ready
    raise ValueError("payload value is not serializable")


def _redact_reference(reference: str) -> str:
    if reference == "public-bls-jolts-release":
        return reference
    digest = sha256(reference.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _ratio(value: Decimal, total: Decimal) -> Decimal:
    if total == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(value / total)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_public_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if _has_unsafe_public_text(value):
        raise ValueError(f"{field_name} has unsafe public text")


def _require_reference_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_canonical_string(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    if value != value.strip() or value.lower() != value:
        raise ValueError(f"{field_name} must be canonical lowercase text")


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be a Decimal")
    return value


def _require_finite_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_count_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_finite_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _has_unsafe_public_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS)
