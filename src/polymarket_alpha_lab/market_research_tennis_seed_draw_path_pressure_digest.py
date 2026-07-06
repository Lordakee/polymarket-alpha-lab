"""Pure Phase 1 tennis seed draw path pressure digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_TENNIS_SEED_DRAW_PATH_PRESSURE_DIGEST_CONFIG_VERSION = (
    "market-research-tennis-seed-draw-path-pressure-digest-v0"
)

INPUT_REASONS = (
    "tennis_seed_draw_path_pressure_input_observed",
    "tennis_seed_draw_path_pressure_seeded_opponent_cluster",
    "tennis_seed_draw_path_pressure_short_rest_path",
    "tennis_seed_draw_path_pressure_small_sample",
)
ROW_REASONS = (
    "tennis_seed_draw_path_pressure_seeded_cluster",
    "tennis_seed_draw_path_pressure_top_seed_cluster",
    "tennis_seed_draw_path_pressure_rest_cluster",
    "tennis_seed_draw_path_pressure_small_sample",
    "tennis_seed_draw_path_pressure_blocked",
    "tennis_seed_draw_path_pressure_watch",
    "tennis_seed_draw_path_pressure_clear",
)
REPORT_REASONS = (
    "tennis_seed_draw_path_pressure_digest_empty",
    "tennis_seed_draw_path_pressure_digest_clear",
    "tennis_seed_draw_path_pressure_blocked_present",
    "tennis_seed_draw_path_pressure_watch_present",
    "tennis_seed_draw_path_pressure_seeded_cluster_present",
    "tennis_seed_draw_path_pressure_rest_cluster_present",
    "tennis_seed_draw_path_pressure_small_sample_present",
)
ROW_STATUSES = ("clear", "watch", "blocked")
DIGEST_STATUSES = ("clear", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
THREE = Decimal("3.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class TennisSeedDrawPathPressureDigestConfig:
    config_version: str = DEFAULT_TENNIS_SEED_DRAW_PATH_PRESSURE_DIGEST_CONFIG_VERSION
    watch_path_pressure_score: Decimal = Decimal("0.300000")
    blocked_path_pressure_score: Decimal = Decimal("0.500000")
    min_projected_match_count: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "TennisSeedDrawPathPressureDigestConfig does not support subclassing"
        )

    def __post_init__(self) -> None:
        _require_exact_dataclass_type(self, TennisSeedDrawPathPressureDigestConfig)
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_TENNIS_SEED_DRAW_PATH_PRESSURE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "watch_path_pressure_score",
            _require_positive_ratio(
                "watch_path_pressure_score",
                self.watch_path_pressure_score,
            ),
        )
        object.__setattr__(
            self,
            "blocked_path_pressure_score",
            _require_positive_ratio(
                "blocked_path_pressure_score",
                self.blocked_path_pressure_score,
            ),
        )
        if self.blocked_path_pressure_score < self.watch_path_pressure_score:
            raise ValueError(
                "blocked_path_pressure_score must be at least watch_path_pressure_score"
            )
        object.__setattr__(
            self,
            "min_projected_match_count",
            _require_positive_decimal(
                "min_projected_match_count",
                self.min_projected_match_count,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TennisSeedDrawPathPressureInput:
    source_id: str
    tournament_id: str
    draw_id: str
    player_id: str
    seed_rank: Decimal
    projected_match_count: Decimal
    seeded_opponent_count: Decimal
    top_eight_opponent_count: Decimal
    short_rest_match_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("TennisSeedDrawPathPressureInput does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_dataclass_type(self, TennisSeedDrawPathPressureInput)
        for field_name in ("source_id", "tournament_id", "draw_id", "player_id"):
            object.__setattr__(
                self,
                field_name,
                _require_text(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "seed_rank",
            _require_positive_decimal("seed_rank", self.seed_rank),
        )
        for field_name in (
            "projected_match_count",
            "seeded_opponent_count",
            "top_eight_opponent_count",
            "short_rest_match_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_input_counts(self)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons("reason_codes", self.reason_codes, INPUT_REASONS),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class TennisSeedDrawPathPressureReasonCodeCount:
    reason_code: str
    row_count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "TennisSeedDrawPathPressureReasonCodeCount does not support subclassing"
        )

    def __post_init__(self) -> None:
        _require_exact_dataclass_type(self, TennisSeedDrawPathPressureReasonCodeCount)
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, REPORT_REASONS),
        )
        object.__setattr__(
            self,
            "row_count",
            _require_positive_whole_decimal("row_count", self.row_count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class TennisSeedDrawPathPressureRow:
    source_id: str
    tournament_id: str
    draw_id: str
    player_id: str
    seed_rank: Decimal
    projected_match_count: Decimal
    seeded_opponent_count: Decimal
    top_eight_opponent_count: Decimal
    short_rest_match_count: Decimal
    seeded_opponent_ratio: Decimal
    top_eight_opponent_ratio: Decimal
    rest_pressure_ratio: Decimal
    path_pressure_score: Decimal
    observed_at: datetime
    pressure_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("TennisSeedDrawPathPressureRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_dataclass_type(self, TennisSeedDrawPathPressureRow)
        for field_name in ("source_id", "tournament_id", "draw_id", "player_id"):
            object.__setattr__(
                self,
                field_name,
                _require_text(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "seed_rank",
            _require_positive_decimal("seed_rank", self.seed_rank),
        )
        for field_name in (
            "projected_match_count",
            "seeded_opponent_count",
            "top_eight_opponent_count",
            "short_rest_match_count",
            "seeded_opponent_ratio",
            "top_eight_opponent_ratio",
            "rest_pressure_ratio",
            "path_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "seeded_opponent_ratio",
            "top_eight_opponent_ratio",
            "rest_pressure_ratio",
            "path_pressure_score",
        ):
            _require_ratio(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "pressure_status",
            _require_member("pressure_status", self.pressure_status, ROW_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons("reason_codes", self.reason_codes, ROW_REASONS),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class TennisSeedDrawPathPressureDigest:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    input_count: Decimal
    row_count: Decimal
    source_count: Decimal
    watch_row_count: Decimal
    blocked_row_count: Decimal
    total_projected_match_count: Decimal
    total_seeded_opponent_count: Decimal
    total_top_eight_opponent_count: Decimal
    total_short_rest_match_count: Decimal
    max_path_pressure_score: Decimal
    weighted_path_pressure_score: Decimal
    rows: tuple[TennisSeedDrawPathPressureRow, ...]
    reason_code_counts: tuple[TennisSeedDrawPathPressureReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("TennisSeedDrawPathPressureDigest does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_dataclass_type(self, TennisSeedDrawPathPressureDigest)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_TENNIS_SEED_DRAW_PATH_PRESSURE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "digest_status",
            _require_member("digest_status", self.digest_status, DIGEST_STATUSES),
        )
        object.__setattr__(
            self,
            "recommended_next_step",
            _require_text("recommended_next_step", self.recommended_next_step),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons("reason_codes", self.reason_codes, REPORT_REASONS),
        )
        for field_name in (
            "input_count",
            "row_count",
            "source_count",
            "watch_row_count",
            "blocked_row_count",
            "total_projected_match_count",
            "total_seeded_opponent_count",
            "total_top_eight_opponent_count",
            "total_short_rest_match_count",
            "max_path_pressure_score",
            "weighted_path_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio("max_path_pressure_score", self.max_path_pressure_score)
        _require_ratio("weighted_path_pressure_score", self.weighted_path_pressure_score)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_counts(self.reason_code_counts),
        )
        _validate_digest(self)
        _require_hard_flags("digest", self)


_PUBLIC_DATACLASS_TYPES = (
    TennisSeedDrawPathPressureDigestConfig,
    TennisSeedDrawPathPressureInput,
    TennisSeedDrawPathPressureReasonCodeCount,
    TennisSeedDrawPathPressureRow,
    TennisSeedDrawPathPressureDigest,
)


def build_market_research_tennis_seed_draw_path_pressure_digest(
    inputs: tuple[TennisSeedDrawPathPressureInput, ...],
    *,
    config: TennisSeedDrawPathPressureDigestConfig,
    generated_at: datetime,
) -> TennisSeedDrawPathPressureDigest:
    if type(config) is not TennisSeedDrawPathPressureDigestConfig:
        raise ValueError("config must be a TennisSeedDrawPathPressureDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for row in normalized_inputs:
        if row.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    if not normalized_inputs:
        return TennisSeedDrawPathPressureDigest(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            digest_status="blocked",
            recommended_next_step=(
                "block_report_only_market_research_tennis_seed_draw_path_pressure_digest"
            ),
            reason_codes=("tennis_seed_draw_path_pressure_digest_empty",),
            input_count=ZERO,
            row_count=ZERO,
            source_count=ZERO,
            watch_row_count=ZERO,
            blocked_row_count=ZERO,
            total_projected_match_count=ZERO,
            total_seeded_opponent_count=ZERO,
            total_top_eight_opponent_count=ZERO,
            total_short_rest_match_count=ZERO,
            max_path_pressure_score=ZERO,
            weighted_path_pressure_score=ZERO,
            rows=(),
            reason_code_counts=_reason_counts(
                (),
                ("tennis_seed_draw_path_pressure_digest_empty",),
                ZERO,
            ),
        )

    reduced_rows = tuple(
        sorted(
            (_pressure_row(row, config=config) for row in normalized_inputs),
            key=_row_sort_key,
        )
    )
    row_count = _count(len(reduced_rows))
    report_reasons = _report_reasons(reduced_rows)
    digest_status = _digest_status(reduced_rows)
    return TennisSeedDrawPathPressureDigest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=_next_step(digest_status),
        reason_codes=report_reasons,
        input_count=_count(len(normalized_inputs)),
        row_count=row_count,
        source_count=_count(len({row.source_id for row in reduced_rows})),
        watch_row_count=_count(
            sum(1 for row in reduced_rows if row.pressure_status == "watch")
        ),
        blocked_row_count=_count(
            sum(1 for row in reduced_rows if row.pressure_status == "blocked")
        ),
        total_projected_match_count=_sum_decimal(
            row.projected_match_count for row in reduced_rows
        ),
        total_seeded_opponent_count=_sum_decimal(
            row.seeded_opponent_count for row in reduced_rows
        ),
        total_top_eight_opponent_count=_sum_decimal(
            row.top_eight_opponent_count for row in reduced_rows
        ),
        total_short_rest_match_count=_sum_decimal(
            row.short_rest_match_count for row in reduced_rows
        ),
        max_path_pressure_score=max(
            (row.path_pressure_score for row in reduced_rows),
            default=ZERO,
        ),
        weighted_path_pressure_score=_weighted_path_pressure_score(reduced_rows),
        rows=reduced_rows,
        reason_code_counts=_reason_counts(reduced_rows, report_reasons, row_count),
    )


def market_research_tennis_seed_draw_path_pressure_digest_payload(
    digest: TennisSeedDrawPathPressureDigest,
) -> dict[str, Any]:
    if type(digest) is not TennisSeedDrawPathPressureDigest:
        raise ValueError("digest must be a TennisSeedDrawPathPressureDigest")
    _revalidate_public_dataclass_graph(digest)
    return _json_ready(digest)


def _pressure_row(
    row: TennisSeedDrawPathPressureInput,
    *,
    config: TennisSeedDrawPathPressureDigestConfig,
) -> TennisSeedDrawPathPressureRow:
    seeded_ratio = _ratio(row.seeded_opponent_count, row.projected_match_count)
    top_eight_ratio = _ratio(row.top_eight_opponent_count, row.projected_match_count)
    rest_ratio = _ratio(row.short_rest_match_count, row.projected_match_count)
    score = _path_pressure_score(
        row.projected_match_count,
        row.seeded_opponent_count,
        row.top_eight_opponent_count,
        row.short_rest_match_count,
    )
    status = _row_status(
        score,
        row.projected_match_count,
        row.reason_codes,
        config=config,
    )
    return TennisSeedDrawPathPressureRow(
        source_id=row.source_id,
        tournament_id=row.tournament_id,
        draw_id=row.draw_id,
        player_id=row.player_id,
        seed_rank=row.seed_rank,
        projected_match_count=row.projected_match_count,
        seeded_opponent_count=row.seeded_opponent_count,
        top_eight_opponent_count=row.top_eight_opponent_count,
        short_rest_match_count=row.short_rest_match_count,
        seeded_opponent_ratio=seeded_ratio,
        top_eight_opponent_ratio=top_eight_ratio,
        rest_pressure_ratio=rest_ratio,
        path_pressure_score=score,
        observed_at=row.observed_at,
        pressure_status=status,
        reason_codes=_row_reasons(
            row,
            seeded_ratio=seeded_ratio,
            top_eight_ratio=top_eight_ratio,
            rest_ratio=rest_ratio,
            status=status,
            config=config,
        ),
    )


def _path_pressure_score(
    projected_match_count: Decimal,
    seeded_opponent_count: Decimal,
    top_eight_opponent_count: Decimal,
    short_rest_match_count: Decimal,
) -> Decimal:
    denominator = projected_match_count * THREE
    numerator = seeded_opponent_count + top_eight_opponent_count + short_rest_match_count
    return _ratio(numerator, denominator)


def _weighted_path_pressure_score(
    rows: tuple[TennisSeedDrawPathPressureRow, ...],
) -> Decimal:
    total_projected = _sum_decimal(row.projected_match_count for row in rows)
    weighted_total = _sum_decimal(
        row.seeded_opponent_count
        + row.top_eight_opponent_count
        + row.short_rest_match_count
        for row in rows
    )
    return _ratio(weighted_total, total_projected * THREE)


def _row_status(
    score: Decimal,
    match_count: Decimal,
    reason_codes: tuple[str, ...],
    *,
    config: TennisSeedDrawPathPressureDigestConfig,
) -> str:
    if score >= config.blocked_path_pressure_score:
        return "blocked"
    if (
        score >= config.watch_path_pressure_score
        or match_count < config.min_projected_match_count
        or "tennis_seed_draw_path_pressure_small_sample" in reason_codes
    ):
        return "watch"
    return "clear"


def _row_reasons(
    row: TennisSeedDrawPathPressureInput,
    *,
    seeded_ratio: Decimal,
    top_eight_ratio: Decimal,
    rest_ratio: Decimal,
    status: str,
    config: TennisSeedDrawPathPressureDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if (
        seeded_ratio >= config.watch_path_pressure_score
        or "tennis_seed_draw_path_pressure_seeded_opponent_cluster" in row.reason_codes
    ):
        reasons.append("tennis_seed_draw_path_pressure_seeded_cluster")
    if top_eight_ratio > ZERO:
        reasons.append("tennis_seed_draw_path_pressure_top_seed_cluster")
    if (
        rest_ratio >= config.watch_path_pressure_score
        or "tennis_seed_draw_path_pressure_short_rest_path" in row.reason_codes
    ):
        reasons.append("tennis_seed_draw_path_pressure_rest_cluster")
    if (
        row.projected_match_count < config.min_projected_match_count
        or "tennis_seed_draw_path_pressure_small_sample" in row.reason_codes
    ):
        reasons.append("tennis_seed_draw_path_pressure_small_sample")
    if status == "blocked":
        reasons.append("tennis_seed_draw_path_pressure_blocked")
    elif status == "watch":
        reasons.append("tennis_seed_draw_path_pressure_watch")
    else:
        reasons.append("tennis_seed_draw_path_pressure_clear")
    return _normalize_reasons("reason_codes", tuple(reasons), ROW_REASONS)


def _digest_status(rows: tuple[TennisSeedDrawPathPressureRow, ...]) -> str:
    if any(row.pressure_status == "blocked" for row in rows):
        return "blocked"
    if any(row.pressure_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reasons(rows: tuple[TennisSeedDrawPathPressureRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("tennis_seed_draw_path_pressure_digest_empty",)
    reasons: list[str] = []
    if any(row.pressure_status == "blocked" for row in rows):
        reasons.append("tennis_seed_draw_path_pressure_blocked_present")
    if any(row.pressure_status == "watch" for row in rows):
        reasons.append("tennis_seed_draw_path_pressure_watch_present")
    if any(
        "tennis_seed_draw_path_pressure_seeded_cluster" in row.reason_codes
        or "tennis_seed_draw_path_pressure_top_seed_cluster" in row.reason_codes
        for row in rows
    ):
        reasons.append("tennis_seed_draw_path_pressure_seeded_cluster_present")
    if any("tennis_seed_draw_path_pressure_rest_cluster" in row.reason_codes for row in rows):
        reasons.append("tennis_seed_draw_path_pressure_rest_cluster_present")
    if any("tennis_seed_draw_path_pressure_small_sample" in row.reason_codes for row in rows):
        reasons.append("tennis_seed_draw_path_pressure_small_sample_present")
    if not reasons:
        reasons.append("tennis_seed_draw_path_pressure_digest_clear")
    return _normalize_reasons("reason_codes", tuple(reasons), REPORT_REASONS)


def _reason_counts(
    rows: tuple[TennisSeedDrawPathPressureRow, ...],
    report_reasons: tuple[str, ...],
    row_count: Decimal,
) -> tuple[TennisSeedDrawPathPressureReasonCodeCount, ...]:
    if report_reasons == ("tennis_seed_draw_path_pressure_digest_empty",):
        return (
            TennisSeedDrawPathPressureReasonCodeCount(
                reason_code="tennis_seed_draw_path_pressure_digest_empty",
                row_count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts: list[TennisSeedDrawPathPressureReasonCodeCount] = []
    for reason in report_reasons:
        matching_count = _count(
            sum(1 for row in rows if _row_matches_report_reason(row, reason))
        )
        if matching_count <= ZERO:
            raise ValueError("reason_code_counts must not include zero row_count")
        counts.append(
            TennisSeedDrawPathPressureReasonCodeCount(
                reason_code=reason,
                row_count=matching_count,
                row_ratio=_ratio(matching_count, row_count),
            )
        )
    return tuple(counts)


def _row_matches_report_reason(
    row: TennisSeedDrawPathPressureRow,
    reason: str,
) -> bool:
    if reason == "tennis_seed_draw_path_pressure_digest_clear":
        return row.pressure_status == "clear"
    if reason == "tennis_seed_draw_path_pressure_blocked_present":
        return row.pressure_status == "blocked"
    if reason == "tennis_seed_draw_path_pressure_watch_present":
        return row.pressure_status == "watch"
    if reason == "tennis_seed_draw_path_pressure_seeded_cluster_present":
        return (
            "tennis_seed_draw_path_pressure_seeded_cluster" in row.reason_codes
            or "tennis_seed_draw_path_pressure_top_seed_cluster" in row.reason_codes
        )
    if reason == "tennis_seed_draw_path_pressure_rest_cluster_present":
        return "tennis_seed_draw_path_pressure_rest_cluster" in row.reason_codes
    if reason == "tennis_seed_draw_path_pressure_small_sample_present":
        return "tennis_seed_draw_path_pressure_small_sample" in row.reason_codes
    return False


def _next_step(status: str) -> str:
    if status == "blocked":
        return "block_report_only_market_research_tennis_seed_draw_path_pressure_digest"
    if status == "watch":
        return "monitor_report_only_market_research_tennis_seed_draw_path_pressure_digest"
    return "allow_report_only_market_research_tennis_seed_draw_path_pressure_digest"


def _normalize_inputs(
    inputs: tuple[TennisSeedDrawPathPressureInput, ...],
) -> tuple[TennisSeedDrawPathPressureInput, ...]:
    if type(inputs) is not tuple:
        raise ValueError("inputs must be a tuple")
    seen_source_ids: set[str] = set()
    for row in inputs:
        if type(row) is not TennisSeedDrawPathPressureInput:
            raise ValueError("inputs must contain TennisSeedDrawPathPressureInput")
        _require_hard_flags("input", row)
        if row.source_id in seen_source_ids:
            raise ValueError("inputs must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return inputs


def _normalize_rows(value: object) -> tuple[TennisSeedDrawPathPressureRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TennisSeedDrawPathPressureRow:
            raise ValueError("rows must contain TennisSeedDrawPathPressureRow")
        _require_hard_flags("row", row)
    if value != tuple(sorted(value, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if len({row.source_id for row in value}) != len(value):
        raise ValueError("rows must not contain duplicate source_id values")
    return value


def _normalize_reason_counts(
    value: object,
) -> tuple[TennisSeedDrawPathPressureReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in value:
        if type(row) is not TennisSeedDrawPathPressureReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain TennisSeedDrawPathPressureReasonCodeCount"
            )
    if value != tuple(sorted(value, key=lambda row: REPORT_REASONS.index(row.reason_code))):
        raise ValueError("reason_code_counts must be sorted deterministically")
    if len({row.reason_code for row in value}) != len(value):
        raise ValueError("reason_code_counts must not contain duplicates")
    return value


def _row_sort_key(
    row: TennisSeedDrawPathPressureRow,
) -> tuple[int, Decimal, datetime, str, str, str, str]:
    return (
        STATUS_RANK[row.pressure_status],
        -row.path_pressure_score,
        row.observed_at,
        row.tournament_id,
        row.draw_id,
        row.player_id,
        row.source_id,
    )


def _validate_input_counts(row: TennisSeedDrawPathPressureInput) -> None:
    if row.seeded_opponent_count > row.projected_match_count:
        raise ValueError("seeded_opponent_count must not exceed projected_match_count")
    if row.top_eight_opponent_count > row.seeded_opponent_count:
        raise ValueError("top_eight_opponent_count must not exceed seeded_opponent_count")
    if row.short_rest_match_count > row.projected_match_count:
        raise ValueError("short_rest_match_count must not exceed projected_match_count")


def _validate_row(row: TennisSeedDrawPathPressureRow) -> None:
    if row.seeded_opponent_count > row.projected_match_count:
        raise ValueError("seeded_opponent_count must not exceed projected_match_count")
    if row.top_eight_opponent_count > row.seeded_opponent_count:
        raise ValueError("top_eight_opponent_count must not exceed seeded_opponent_count")
    if row.short_rest_match_count > row.projected_match_count:
        raise ValueError("short_rest_match_count must not exceed projected_match_count")
    if row.seeded_opponent_ratio != _ratio(
        row.seeded_opponent_count,
        row.projected_match_count,
    ):
        raise ValueError("seeded_opponent_ratio must match row counts")
    if row.top_eight_opponent_ratio != _ratio(
        row.top_eight_opponent_count,
        row.projected_match_count,
    ):
        raise ValueError("top_eight_opponent_ratio must match row counts")
    if row.rest_pressure_ratio != _ratio(
        row.short_rest_match_count,
        row.projected_match_count,
    ):
        raise ValueError("rest_pressure_ratio must match row counts")
    if row.path_pressure_score != _path_pressure_score(
        row.projected_match_count,
        row.seeded_opponent_count,
        row.top_eight_opponent_count,
        row.short_rest_match_count,
    ):
        raise ValueError("path_pressure_score must match row counts")


def _validate_digest(digest: TennisSeedDrawPathPressureDigest) -> None:
    if digest.input_count != _count(len(digest.rows)):
        raise ValueError("input_count must match rows")
    if digest.row_count != _count(len(digest.rows)):
        raise ValueError("row_count must match rows")
    if digest.source_count != _count(len({row.source_id for row in digest.rows})):
        raise ValueError("source_count must match rows")
    if digest.watch_row_count != _count(
        sum(1 for row in digest.rows if row.pressure_status == "watch")
    ):
        raise ValueError("watch_row_count must match rows")
    if digest.blocked_row_count != _count(
        sum(1 for row in digest.rows if row.pressure_status == "blocked")
    ):
        raise ValueError("blocked_row_count must match rows")
    if digest.total_projected_match_count != _sum_decimal(
        row.projected_match_count for row in digest.rows
    ):
        raise ValueError("total_projected_match_count must match rows")
    if digest.total_seeded_opponent_count != _sum_decimal(
        row.seeded_opponent_count for row in digest.rows
    ):
        raise ValueError("total_seeded_opponent_count must match rows")
    if digest.total_top_eight_opponent_count != _sum_decimal(
        row.top_eight_opponent_count for row in digest.rows
    ):
        raise ValueError("total_top_eight_opponent_count must match rows")
    if digest.total_short_rest_match_count != _sum_decimal(
        row.short_rest_match_count for row in digest.rows
    ):
        raise ValueError("total_short_rest_match_count must match rows")
    if digest.max_path_pressure_score != max(
        (row.path_pressure_score for row in digest.rows),
        default=ZERO,
    ):
        raise ValueError("max_path_pressure_score must match rows")
    if digest.weighted_path_pressure_score != _weighted_path_pressure_score(digest.rows):
        raise ValueError("weighted_path_pressure_score must match rows")
    if any(row.observed_at > digest.generated_at for row in digest.rows):
        raise ValueError("observed_at must not be after generated_at")
    expected_status = "blocked" if not digest.rows else _digest_status(digest.rows)
    if digest.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    if digest.recommended_next_step != _next_step(digest.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    expected_reasons = (
        ("tennis_seed_draw_path_pressure_digest_empty",)
        if not digest.rows
        else _report_reasons(digest.rows)
    )
    if digest.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    if digest.reason_code_counts != _reason_counts(
        digest.rows,
        digest.reason_codes,
        digest.row_count,
    ):
        raise ValueError("reason_code_counts must match rows")


def _normalize_reasons(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reasons = tuple(_require_member("reason_code", item, allowed) for item in value)
    if not reasons:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reasons)) != len(reasons):
        raise ValueError(f"{field_name} must not contain duplicates")
    canonical = tuple(item for item in allowed if item in reasons)
    if reasons != canonical:
        raise ValueError(f"{field_name} must be in canonical order")
    return reasons


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    text = _require_text(field_name, value)
    if text not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return text


def _require_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    if normalized != value:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _require_six_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_six_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value % ONE != ZERO:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _require_positive_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_ratio(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a UTC offset")
    return value.astimezone(UTC)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return total.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _revalidate_public_dataclass_graph(value: object) -> None:
    if type(value) not in _PUBLIC_DATACLASS_TYPES:
        raise ValueError("payload contains unsupported dataclass")
    _require_hard_flags(type(value).__name__, value)
    for field in fields(value):
        field_value = getattr(value, field.name)
        if _is_public_numeric_field(field.name):
            _require_six_decimal(field.name, field_value)
        elif field.name.endswith("_at"):
            _require_stored_utc_datetime(field.name, field_value)
    if type(value) is TennisSeedDrawPathPressureDigest:
        for row in value.rows:
            _revalidate_public_dataclass_graph(row)
        for count in value.reason_code_counts:
            _revalidate_public_dataclass_graph(count)
    _rebuild_public_dataclass(value)


def _rebuild_public_dataclass(value: object) -> object:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("payload contains unsupported dataclass")
    values = {field.name: getattr(value, field.name) for field in fields(value)}
    return type(value)(**values)


def _is_public_numeric_field(field_name: str) -> bool:
    return field_name.endswith(("_count", "_ratio", "_rank", "_score"))


def _require_stored_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.tzinfo is not UTC or value.astimezone(UTC) != value:
        raise ValueError(f"{field_name} must be UTC")
    return value


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return str(_require_six_decimal("JSON Decimal value", value))
    if type(value) is datetime:
        return _require_stored_utc_datetime("JSON datetime value", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _revalidate_public_dataclass_graph(value)
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is bool or value is None:
        return value
    if type(value) is str:
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        raise ValueError("list values are not valid public records")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (Decimal, float, int)):
        raise ValueError("JSON numeric value must use exact Decimal fields")
    raise ValueError("value is not JSON serializable")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_dataclass_type(value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{expected_type.__name__} requires exact type")


__all__ = (
    "DEFAULT_TENNIS_SEED_DRAW_PATH_PRESSURE_DIGEST_CONFIG_VERSION",
    "DIGEST_STATUSES",
    "INPUT_REASONS",
    "REPORT_REASONS",
    "ROW_REASONS",
    "ROW_STATUSES",
    "TennisSeedDrawPathPressureDigest",
    "TennisSeedDrawPathPressureDigestConfig",
    "TennisSeedDrawPathPressureInput",
    "TennisSeedDrawPathPressureReasonCodeCount",
    "TennisSeedDrawPathPressureRow",
    "build_market_research_tennis_seed_draw_path_pressure_digest",
    "market_research_tennis_seed_draw_path_pressure_digest_payload",
)
