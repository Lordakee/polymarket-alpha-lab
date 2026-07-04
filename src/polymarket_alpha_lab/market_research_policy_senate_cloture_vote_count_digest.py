"""Pure Phase 1 policy Senate cloture vote-count digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_SENATE_CLOTURE_VOTE_COUNT_DIGEST_CONFIG_VERSION = (
    "market-research-policy-senate-cloture-vote-count-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"

REASON_PREFIX = "market_research_policy_senate_cloture_vote_count_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
BELOW_THRESHOLD_BLOCK_REASON = f"{REASON_PREFIX}below_threshold_block"
BELOW_THRESHOLD_WATCH_REASON = f"{REASON_PREFIX}below_threshold_watch"
PROBABILITY_SHIFT_REASON = f"{REASON_PREFIX}probability_shift"
LOW_AGREEMENT_REASON = f"{REASON_PREFIX}low_agreement"
STALE_SNAPSHOT_REASON = f"{REASON_PREFIX}stale_snapshot"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    BELOW_THRESHOLD_BLOCK_REASON,
    PROBABILITY_SHIFT_REASON,
    BELOW_THRESHOLD_WATCH_REASON,
    LOW_AGREEMENT_REASON,
    STALE_SNAPSHOT_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    BELOW_THRESHOLD_BLOCK_REASON,
    PROBABILITY_SHIFT_REASON,
    BELOW_THRESHOLD_WATCH_REASON,
    LOW_AGREEMENT_REASON,
    STALE_SNAPSHOT_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_policy_senate_cloture_vote_count_digest",
    STATUS_WATCH: "watch_report_only_market_research_policy_senate_cloture_vote_count_digest",
    STATUS_BLOCKED: "block_report_only_market_research_policy_senate_cloture_vote_count_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PROBABILITY_SHIFT_THRESHOLD = Decimal("0.100000")

UNSAFE_TEXT_FRAGMENTS = (
    "auth",
    "broker",
    "signing",
    "submit",
    "cancel",
    "wal" + "let",
    "account",
    "priv" + "ate",
    "sec" + "ret",
    "tok" + "en",
    "credential",
    "ord" + "er",
    "exchange",
)
PUBLIC_REFERENCE_FRAGMENTS = (
    "public",
    "senate",
    "cloture",
    "vote",
    "bill",
    "congress",
    "calendar",
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_SENATE_CLOTURE_VOTE_COUNT_DIGEST_CONFIG_VERSION",
    "MarketResearchPolicySenateClotureVoteCountDigestConfig",
    "MarketResearchPolicySenateClotureVoteCountDigestInputRow",
    "MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount",
    "MarketResearchPolicySenateClotureVoteCountDigestReport",
    "MarketResearchPolicySenateClotureVoteCountDigestRow",
    "build_market_research_policy_senate_cloture_vote_count_digest",
    "market_research_policy_senate_cloture_vote_count_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPolicySenateClotureVoteCountDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_SENATE_CLOTURE_VOTE_COUNT_DIGEST_CONFIG_VERSION
    )
    cloture_vote_threshold: Decimal = Decimal("60")
    watch_vote_margin: Decimal = Decimal("3")
    blocked_vote_margin: Decimal = Decimal("1")
    max_snapshot_age_seconds: Decimal = Decimal("7200.000000")
    min_public_source_count: Decimal = Decimal("2")
    min_cross_source_agreement: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicySenateClotureVoteCountDigestConfig:
            raise TypeError(
                "MarketResearchPolicySenateClotureVoteCountDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicySenateClotureVoteCountDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchPolicySenateClotureVoteCountDigestConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_SENATE_CLOTURE_VOTE_COUNT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "cloture_vote_threshold",
            "watch_vote_margin",
            "blocked_vote_margin",
            "min_public_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_snapshot_age_seconds",
            _require_nonnegative_decimal(
                "max_snapshot_age_seconds",
                self.max_snapshot_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_cross_source_agreement",
            _require_ratio_decimal(
                "min_cross_source_agreement",
                self.min_cross_source_agreement,
            ),
        )
        if self.blocked_vote_margin > self.watch_vote_margin:
            raise ValueError("blocked_vote_margin must be no greater than watch level")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPolicySenateClotureVoteCountDigestInputRow:
    research_key: str
    condition_id: str
    motion_key: str
    chamber: str
    public_vote_reference: str
    observed_at: datetime
    committed_yes_count: Decimal
    lean_yes_count: Decimal
    undecided_count: Decimal
    committed_no_count: Decimal
    public_source_count: Decimal
    cross_source_agreement: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicySenateClotureVoteCountDigestInputRow:
            raise TypeError(
                "MarketResearchPolicySenateClotureVoteCountDigestInputRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicySenateClotureVoteCountDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchPolicySenateClotureVoteCountDigestInputRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "motion_key",
            "chamber",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("public_vote_reference", self.public_vote_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "committed_yes_count",
            "lean_yes_count",
            "undecided_count",
            "committed_no_count",
            "public_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "cross_source_agreement",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchPolicySenateClotureVoteCountDigestRow:
    research_key: str
    condition_id: str
    motion_key: str
    chamber: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    committed_yes_count: Decimal
    lean_yes_count: Decimal
    undecided_count: Decimal
    committed_no_count: Decimal
    total_yes_count: Decimal
    cloture_vote_threshold: Decimal
    vote_margin: Decimal
    vote_shortfall: Decimal
    public_source_count: Decimal
    cross_source_agreement: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_change: Decimal
    vote_status: str
    redacted_vote_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicySenateClotureVoteCountDigestRow:
            raise TypeError(
                "MarketResearchPolicySenateClotureVoteCountDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicySenateClotureVoteCountDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchPolicySenateClotureVoteCountDigestRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "motion_key",
            "chamber",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "snapshot_age_seconds",
            "committed_yes_count",
            "lean_yes_count",
            "undecided_count",
            "committed_no_count",
            "total_yes_count",
            "cloture_vote_threshold",
            "vote_shortfall",
            "public_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "vote_margin",
            _require_decimal("vote_margin", self.vote_margin),
        )
        for field_name in (
            "cross_source_agreement",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_change",
            _require_probability_change("probability_change", self.probability_change),
        )
        _require_status("vote_status", self.vote_status)
        object.__setattr__(
            self,
            "redacted_vote_reference",
            _require_redacted_reference(
                "redacted_vote_reference",
                self.redacted_vote_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    vote_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "vote_ratio",
            _require_ratio_decimal("vote_ratio", self.vote_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchPolicySenateClotureVoteCountDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_step: str
    vote_count: Decimal
    ready_vote_count: Decimal
    watch_vote_count: Decimal
    blocked_vote_count: Decimal
    below_threshold_count: Decimal
    stale_snapshot_count: Decimal
    thin_source_count: Decimal
    low_agreement_count: Decimal
    probability_shift_count: Decimal
    max_vote_shortfall: Decimal
    average_vote_margin: Decimal
    average_public_source_count: Decimal
    rows: tuple[MarketResearchPolicySenateClotureVoteCountDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicySenateClotureVoteCountDigestReport:
            raise TypeError(
                "MarketResearchPolicySenateClotureVoteCountDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicySenateClotureVoteCountDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchPolicySenateClotureVoteCountDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "vote_count",
            "ready_vote_count",
            "watch_vote_count",
            "blocked_vote_count",
            "below_threshold_count",
            "stale_snapshot_count",
            "thin_source_count",
            "low_agreement_count",
            "probability_shift_count",
            "max_vote_shortfall",
            "average_public_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_vote_margin",
            _require_decimal("average_vote_margin", self.average_vote_margin),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_policy_senate_cloture_vote_count_digest(
    input_rows: list[MarketResearchPolicySenateClotureVoteCountDigestInputRow]
    | tuple[MarketResearchPolicySenateClotureVoteCountDigestInputRow, ...],
    *,
    config: MarketResearchPolicySenateClotureVoteCountDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchPolicySenateClotureVoteCountDigestReport:
    cfg = config or MarketResearchPolicySenateClotureVoteCountDigestConfig()
    if type(cfg) is not MarketResearchPolicySenateClotureVoteCountDigestConfig:
        raise ValueError(
            "config must be a MarketResearchPolicySenateClotureVoteCountDigestConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(
        _build_row(row, config=cfg, generated_at=report_time)
        for row in normalized_rows
    )
    ranked_rows = _ranked_rows(built_rows)
    vote_count = _count(len(ranked_rows))
    ready_vote_count = _count(
        sum(1 for row in ranked_rows if row.vote_status == STATUS_READY),
    )
    watch_vote_count = _count(
        sum(1 for row in ranked_rows if row.vote_status == STATUS_WATCH),
    )
    blocked_vote_count = _count(
        sum(1 for row in ranked_rows if row.vote_status == STATUS_BLOCKED),
    )
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                vote_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_vote_count=blocked_vote_count,
        watch_vote_count=watch_vote_count,
    )
    return MarketResearchPolicySenateClotureVoteCountDigestReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        digest_status=digest_status,
        next_step=NEXT_STEPS[digest_status],
        vote_count=vote_count,
        ready_vote_count=ready_vote_count,
        watch_vote_count=watch_vote_count,
        blocked_vote_count=blocked_vote_count,
        below_threshold_count=_count(
            sum(
                1
                for row in ranked_rows
                if BELOW_THRESHOLD_BLOCK_REASON in row.reason_codes
                or BELOW_THRESHOLD_WATCH_REASON in row.reason_codes
            ),
        ),
        stale_snapshot_count=_count(
            sum(1 for row in ranked_rows if STALE_SNAPSHOT_REASON in row.reason_codes),
        ),
        thin_source_count=_count(
            sum(1 for row in ranked_rows if THIN_SOURCES_REASON in row.reason_codes),
        ),
        low_agreement_count=_count(
            sum(1 for row in ranked_rows if LOW_AGREEMENT_REASON in row.reason_codes),
        ),
        probability_shift_count=_count(
            sum(1 for row in ranked_rows if PROBABILITY_SHIFT_REASON in row.reason_codes),
        ),
        max_vote_shortfall=max(
            (row.vote_shortfall for row in ranked_rows),
            default=ZERO,
        ),
        average_vote_margin=_ratio(
            _sum_decimal(row.vote_margin for row in ranked_rows),
            vote_count,
        ),
        average_public_source_count=_ratio(
            _sum_decimal(row.public_source_count for row in ranked_rows),
            vote_count,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_policy_senate_cloture_vote_count_digest_payload(
    report: MarketResearchPolicySenateClotureVoteCountDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPolicySenateClotureVoteCountDigestReport:
        raise ValueError(
            "report must be a MarketResearchPolicySenateClotureVoteCountDigestReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload("payload", payload)
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


def _build_row(
    row: MarketResearchPolicySenateClotureVoteCountDigestInputRow,
    *,
    config: MarketResearchPolicySenateClotureVoteCountDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicySenateClotureVoteCountDigestRow:
    snapshot_age_seconds = _datetime_delta_seconds(generated_at, row.observed_at)
    total_yes_count = _quantize(row.committed_yes_count + row.lean_yes_count)
    vote_margin = _quantize(total_yes_count - config.cloture_vote_threshold)
    vote_shortfall = ZERO if vote_margin >= ZERO else _quantize(-vote_margin)
    probability_change = _quantize(
        row.market_probability_after - row.market_probability_before,
    )
    reason_codes = _row_reason_codes(
        vote_margin=vote_margin,
        snapshot_age_seconds=snapshot_age_seconds,
        public_source_count=row.public_source_count,
        cross_source_agreement=row.cross_source_agreement,
        probability_change=probability_change,
        config=config,
    )
    return MarketResearchPolicySenateClotureVoteCountDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        motion_key=row.motion_key,
        chamber=row.chamber,
        observed_at=row.observed_at,
        snapshot_age_seconds=snapshot_age_seconds,
        committed_yes_count=row.committed_yes_count,
        lean_yes_count=row.lean_yes_count,
        undecided_count=row.undecided_count,
        committed_no_count=row.committed_no_count,
        total_yes_count=total_yes_count,
        cloture_vote_threshold=config.cloture_vote_threshold,
        vote_margin=vote_margin,
        vote_shortfall=vote_shortfall,
        public_source_count=row.public_source_count,
        cross_source_agreement=row.cross_source_agreement,
        market_probability_before=row.market_probability_before,
        market_probability_after=row.market_probability_after,
        probability_change=probability_change,
        vote_status=_row_status(reason_codes),
        redacted_vote_reference=_redacted_reference(row.public_vote_reference),
        reason_codes=reason_codes,
    )


def _normalize_input_rows(
    rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchPolicySenateClotureVoteCountDigestInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchPolicySenateClotureVoteCountDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchPolicySenateClotureVoteCountDigestInputRow",
            )
        _require_hard_flags("input row", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must be on or before generated_at")
        key = (row.research_key, row.condition_id)
        if key in seen:
            raise ValueError("input rows must not contain duplicate research keys")
        seen.add(key)
    return normalized


def _row_reason_codes(
    *,
    vote_margin: Decimal,
    snapshot_age_seconds: Decimal,
    public_source_count: Decimal,
    cross_source_agreement: Decimal,
    probability_change: Decimal,
    config: MarketResearchPolicySenateClotureVoteCountDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if vote_margin < config.blocked_vote_margin:
        reason_codes.append(BELOW_THRESHOLD_BLOCK_REASON)
    elif vote_margin < config.watch_vote_margin:
        reason_codes.append(BELOW_THRESHOLD_WATCH_REASON)
    if _abs_decimal(probability_change) >= PROBABILITY_SHIFT_THRESHOLD:
        reason_codes.append(PROBABILITY_SHIFT_REASON)
    if cross_source_agreement < config.min_cross_source_agreement:
        reason_codes.append(LOW_AGREEMENT_REASON)
    if snapshot_age_seconds > config.max_snapshot_age_seconds:
        reason_codes.append(STALE_SNAPSHOT_REASON)
    if public_source_count < config.min_public_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if BELOW_THRESHOLD_BLOCK_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_vote_count: Decimal,
    watch_vote_count: Decimal,
) -> str:
    if not has_inputs or blocked_vote_count > ZERO:
        return STATUS_BLOCKED
    if watch_vote_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _ranked_rows(
    rows: tuple[MarketResearchPolicySenateClotureVoteCountDigestRow, ...],
) -> tuple[MarketResearchPolicySenateClotureVoteCountDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.vote_status),
                -row.vote_shortfall,
                row.motion_key,
                row.research_key,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[value]


def _reason_code_counts(
    rows: tuple[MarketResearchPolicySenateClotureVoteCountDigestRow, ...],
) -> tuple[MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            vote_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchPolicySenateClotureVoteCountDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchPolicySenateClotureVoteCountDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchPolicySenateClotureVoteCountDigestRow",
            )
        _require_hard_flags("row", row)
    if rows != _ranked_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    prior_rank = -1
    for row in rows:
        if type(row) is not MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
        rank = REASON_CODE_SEQUENCE.index(row.reason_code)
        if rank <= prior_rank:
            raise ValueError("reason_code_counts must be unique and sorted")
        prior_rank = rank
    return rows


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    if READY_REASON in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix ready with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    return normalized


def _validate_row(row: MarketResearchPolicySenateClotureVoteCountDigestRow) -> None:
    expected_total_yes_count = _quantize(row.committed_yes_count + row.lean_yes_count)
    if row.total_yes_count != expected_total_yes_count:
        raise ValueError("total_yes_count must match committed and lean yes counts")
    expected_vote_margin = _quantize(row.total_yes_count - row.cloture_vote_threshold)
    if row.vote_margin != expected_vote_margin:
        raise ValueError("vote_margin must match total_yes_count and threshold")
    expected_shortfall = ZERO if expected_vote_margin >= ZERO else _quantize(-expected_vote_margin)
    if row.vote_shortfall != expected_shortfall:
        raise ValueError("vote_shortfall must match vote_margin")
    expected_probability_change = _quantize(
        row.market_probability_after - row.market_probability_before,
    )
    if row.probability_change != expected_probability_change:
        raise ValueError("probability_change must match probability inputs")
    if row.vote_status != _row_status(row.reason_codes):
        raise ValueError("vote_status must match reason_codes")
    if not _is_redacted_reference(row.redacted_vote_reference):
        raise ValueError("redacted_vote_reference must be redacted or public")


def _validate_report(report: MarketResearchPolicySenateClotureVoteCountDigestReport) -> None:
    if report.next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("next_step must match digest_status")
    if report.vote_count != _count(len(report.rows)):
        raise ValueError("vote_count must match rows")
    expected_ready = _count(
        sum(1 for row in report.rows if row.vote_status == STATUS_READY),
    )
    if report.ready_vote_count != expected_ready:
        raise ValueError("ready_vote_count must match rows")
    expected_watch = _count(
        sum(1 for row in report.rows if row.vote_status == STATUS_WATCH),
    )
    if report.watch_vote_count != expected_watch:
        raise ValueError("watch_vote_count must match rows")
    expected_blocked = _count(
        sum(1 for row in report.rows if row.vote_status == STATUS_BLOCKED),
    )
    if report.blocked_vote_count != expected_blocked:
        raise ValueError("blocked_vote_count must match rows")
    if report.below_threshold_count != _count(
        sum(
            1
            for row in report.rows
            if BELOW_THRESHOLD_BLOCK_REASON in row.reason_codes
            or BELOW_THRESHOLD_WATCH_REASON in row.reason_codes
        ),
    ):
        raise ValueError("below_threshold_count must match rows")
    if report.stale_snapshot_count != _count(
        sum(1 for row in report.rows if STALE_SNAPSHOT_REASON in row.reason_codes),
    ):
        raise ValueError("stale_snapshot_count must match rows")
    if report.thin_source_count != _count(
        sum(1 for row in report.rows if THIN_SOURCES_REASON in row.reason_codes),
    ):
        raise ValueError("thin_source_count must match rows")
    if report.low_agreement_count != _count(
        sum(1 for row in report.rows if LOW_AGREEMENT_REASON in row.reason_codes),
    ):
        raise ValueError("low_agreement_count must match rows")
    if report.probability_shift_count != _count(
        sum(1 for row in report.rows if PROBABILITY_SHIFT_REASON in row.reason_codes),
    ):
        raise ValueError("probability_shift_count must match rows")
    expected_max_shortfall = max(
        (row.vote_shortfall for row in report.rows),
        default=ZERO,
    )
    if report.max_vote_shortfall != expected_max_shortfall:
        raise ValueError("max_vote_shortfall must match rows")
    if report.average_vote_margin != _ratio(
        _sum_decimal(row.vote_margin for row in report.rows),
        report.vote_count,
    ):
        raise ValueError("average_vote_margin must match rows")
    if report.average_public_source_count != _ratio(
        _sum_decimal(row.public_source_count for row in report.rows),
        report.vote_count,
    ):
        raise ValueError("average_public_source_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                vote_ratio=ONE,
            ),
        )
        expected_codes = (NO_INPUTS_REASON,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_vote_count=report.blocked_vote_count,
        watch_vote_count=report.watch_vote_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED):
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_text(field_name, value)
    return value


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_redacted_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if not _is_redacted_reference(value):
        raise ValueError(f"{field_name} must be redacted or public")
    return value


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not include sensitive or live-action text")


def _is_redacted_reference(value: str) -> bool:
    if value.startswith("sha256:") and len(value) == 19:
        return True
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        return False
    if "://" in lowered:
        return False
    return any(fragment in lowered for fragment in PUBLIC_REFERENCE_FRAGMENTS)


def _redacted_reference(value: str) -> str:
    if _is_redacted_reference(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _reject_unsafe_payload(label: str, value: object) -> None:
    text = repr(value).lower()
    for fragment in UNSAFE_TEXT_FRAGMENTS:
        if fragment in text:
            raise ValueError(f"{label} must not include unsafe text")
    if "://" in text:
        raise ValueError(f"{label} must not include unredacted references")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_probability_change(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _datetime_delta_seconds(end: datetime, start: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize(total_microseconds / MICROSECONDS_PER_SECOND)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[assignment]
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _abs_decimal(value: Decimal) -> Decimal:
    return -value if value < ZERO else value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            output[key] = _json_ready(item)
        return output
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
