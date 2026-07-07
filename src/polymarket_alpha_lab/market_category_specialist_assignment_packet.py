"""Pure Phase 1 market category specialist assignment packet."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.strategy_team_taxonomy import (
    STRATEGY_TEAM_IDS,
    require_strategy_team_id,
)


DEFAULT_MARKET_CATEGORY_SPECIALIST_ASSIGNMENT_PACKET_CONFIG_VERSION = (
    "market-category-specialist-assignment-packet-v1"
)
ASSIGNMENT_STATUSES = ("pass", "watch", "block")
PACKET_STATUSES = ("pass", "watch", "block")

_COUNT_QUANTUM = Decimal("1")
_SIX_PLACE_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_RATIO = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")
_DEFAULT_ASSIGNMENT_THRESHOLD = Decimal("0.500000")
_MAX_SECONDARY_TEAM_COUNT = Decimal("3")
_CATEGORY_WEIGHT = Decimal("0.600000")
_KEYWORD_WEIGHT = Decimal("0.250000")
_FRESHNESS_WEIGHT = Decimal("0.150000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_DIGEST_FIELD = "derived_validation_digest"
_DEFAULT_AVAILABLE_TEAM_IDS = STRATEGY_TEAM_IDS
_ASSIGNMENT_STATUS_WEIGHT = {
    "block": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}
_TEAM_SORT_INDEX = {team_id: Decimal(index) for index, team_id in enumerate(STRATEGY_TEAM_IDS)}
_CATEGORY_TO_TEAM_REASON = {
    "politics": ("politics", "category_hint_politics"),
    "finance.crypto.btc": ("crypto_btc", "category_hint_crypto_btc"),
    "crypto.btc": ("crypto_btc", "category_hint_crypto_btc"),
    "finance.equity.indices": ("equity_index", "category_hint_equity_index"),
    "finance.equities": ("equity_index", "category_hint_equity_index"),
    "equities.indexes": ("equity_index", "category_hint_equity_index"),
    "equities.indices": ("equity_index", "category_hint_equity_index"),
    "finance.commodities.gold": (
        "commodities_gold",
        "category_hint_commodities_gold",
    ),
    "commodities.gold": ("commodities_gold", "category_hint_commodities_gold"),
    "sports.soccer": ("soccer", "category_hint_soccer"),
    "sports.football": ("soccer", "category_hint_soccer"),
    "sports.basketball": ("basketball", "category_hint_basketball"),
    "sports.tennis": ("other_sports", "category_hint_other_sports"),
    "sports.other": ("other_sports", "category_hint_other_sports"),
    "general": ("general", "category_hint_general"),
    "technology": ("general", "category_hint_general"),
    "entertainment": ("general", "category_hint_general"),
    "weather": ("general", "category_hint_general"),
    "culture": ("general", "category_hint_general"),
}
_CANONICAL_CATEGORY_LABELS = frozenset(_CATEGORY_TO_TEAM_REASON)
_ROW_REASON_SEQUENCE = (
    "category_hint_politics",
    "category_hint_crypto_btc",
    "category_hint_equity_index",
    "category_hint_commodities_gold",
    "category_hint_soccer",
    "category_hint_basketball",
    "category_hint_other_sports",
    "category_hint_general",
    "category_signal_strong",
    "category_signal_watch",
    "keyword_signal_strong",
    "keyword_signal_watch",
    "fresh_signal",
    "stale_signal",
    "primary_assignment",
    "secondary_assignment",
    "assignment_confidence_watch",
    "no_general_team_available",
    "assignment_block",
)
_PACKET_REASON_SEQUENCE = (
    "no_category_signals",
    "primary_assignment_selected",
    "secondary_assignments_selected",
    "assignment_confidence_watch",
    "no_general_team_available",
    "assignment_block",
)
_UNSAFE_PUBLIC_TERMS = (
    "http://",
    "https://",
    "www.",
    ".com/",
    ".org/",
    ".net/",
    ".io/",
    "polymarket.com",
    "condition_id",
    "market_id",
    "market-id",
    "slug",
    "question",
    "candidate",
    "source_id",
    "source_ref",
    "source_url",
    "source_text",
    "url",
    "token_id",
    "dsn",
    "table",
    "au" "th",
    "token",
    "wal" "let",
    "acc" "ount",
    "or" "der",
    "tra" "de",
    "position_size",
    "b" "uy",
    "se" "ll",
    "recom" "mendation",
    "private",
    "secret",
)


@dataclass(frozen=True)
class MarketCategorySpecialistAssignmentConfig:
    config_version: str = DEFAULT_MARKET_CATEGORY_SPECIALIST_ASSIGNMENT_PACKET_CONFIG_VERSION
    assignment_threshold: Decimal = _DEFAULT_ASSIGNMENT_THRESHOLD
    max_secondary_team_count: Decimal = _MAX_SECONDARY_TEAM_COUNT
    available_team_ids: tuple[str, ...] = _DEFAULT_AVAILABLE_TEAM_IDS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "assignment_threshold",
            _normalize_ratio("assignment_threshold", self.assignment_threshold),
        )
        object.__setattr__(
            self,
            "max_secondary_team_count",
            _normalize_nonnegative_count(
                "max_secondary_team_count",
                self.max_secondary_team_count,
            ),
        )
        object.__setattr__(
            self,
            "available_team_ids",
            _normalize_available_team_ids(self.available_team_ids),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class MarketCategorySpecialistAssignmentSignal:
    category_label: str
    category_confidence: Decimal
    keyword_confidence: Decimal
    freshness_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "category_label",
            _require_canonical_category_label("category_label", self.category_label),
        )
        for field_name in (
            "category_confidence",
            "keyword_confidence",
            "freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("signal", self)
        _reject_unsafe_public_payload("signal", _payload_value(self))


@dataclass(frozen=True)
class MarketCategorySpecialistAssignmentRow:
    rank: Decimal
    category_label: str
    team_id: str
    category_confidence: Decimal
    keyword_confidence: Decimal
    freshness_score: Decimal
    assignment_score: Decimal
    assignment_status: str
    observed_at: datetime
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        object.__setattr__(
            self,
            "category_label",
            _require_canonical_category_label("category_label", self.category_label),
        )
        object.__setattr__(
            self,
            "team_id",
            require_strategy_team_id("team_id", self.team_id),
        )
        for field_name in (
            "category_confidence",
            "keyword_confidence",
            "freshness_score",
            "assignment_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("assignment_status", self.assignment_status, ASSIGNMENT_STATUSES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _ROW_REASON_SEQUENCE,
            ),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class MarketCategorySpecialistAssignmentPacket:
    generated_at: datetime
    config_version: str
    assignment_status: str
    primary_team_id: str | None
    secondary_team_ids: tuple[str, ...]
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    top_assignment_score: Decimal
    reason_codes: tuple[str, ...]
    assignments: tuple[MarketCategorySpecialistAssignmentRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_public_string("config_version", self.config_version),
        )
        _require_member("assignment_status", self.assignment_status, PACKET_STATUSES)
        if self.primary_team_id is not None:
            object.__setattr__(
                self,
                "primary_team_id",
                require_strategy_team_id("primary_team_id", self.primary_team_id),
            )
        object.__setattr__(
            self,
            "secondary_team_ids",
            _normalize_secondary_team_ids(self.secondary_team_ids, self.primary_team_id),
        )
        for field_name in (
            "team_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "top_assignment_score",
            _normalize_ratio("top_assignment_score", self.top_assignment_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _PACKET_REASON_SEQUENCE,
            ),
        )
        object.__setattr__(self, "assignments", _normalize_assignments(self.assignments))
        _require_hard_flags("packet", self)
        _reject_unsafe_public_payload("packet", _payload_value(self))
        _apply_or_verify_digest(self)
        _validate_packet_consistency(self)


def build_market_category_specialist_assignment_packet(
    inputs: object,
    *,
    generated_at: datetime,
    config: MarketCategorySpecialistAssignmentConfig | None = None,
) -> MarketCategorySpecialistAssignmentPacket:
    if config is None:
        config = MarketCategorySpecialistAssignmentConfig()
    if type(config) is not MarketCategorySpecialistAssignmentConfig:
        raise ValueError("config must be a MarketCategorySpecialistAssignmentConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    row_candidates = tuple(_row_from_signal(item, config) for item in normalized_inputs)
    rows = _rank_rows(row_candidates, config)
    return MarketCategorySpecialistAssignmentPacket(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        assignment_status=_packet_status(rows),
        primary_team_id=_primary_team_id(rows),
        secondary_team_ids=_secondary_team_ids(rows, config),
        team_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        top_assignment_score=_top_assignment_score(rows),
        reason_codes=_packet_reason_codes(rows),
        assignments=rows,
    )


def market_category_specialist_assignment_packet_payload(
    packet: object,
) -> dict[str, Any]:
    if type(packet) is MarketCategorySpecialistAssignmentPacket:
        _validate_packet_digest(packet)
        _validate_packet_consistency(packet)
        payload = _payload_value(packet)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(packet) is dict:
        _reject_non_string_numeric(packet)
        _reject_unsafe_public_payload("payload", packet)
        _require_payload_hard_flags(packet)
        if _DIGEST_FIELD in packet:
            _validate_payload_digest(packet)
        return packet
    raise ValueError("payload must be an assignment packet or payload dict")


def _row_from_signal(
    item: MarketCategorySpecialistAssignmentSignal,
    config: MarketCategorySpecialistAssignmentConfig,
) -> MarketCategorySpecialistAssignmentRow:
    team_id, category_reason = _team_reason_from_category_label(item.category_label)
    score = _assignment_score(item, config, team_id)
    status = _assignment_status(score, team_id, config)
    return MarketCategorySpecialistAssignmentRow(
        rank=_COUNT_QUANTUM,
        category_label=item.category_label,
        team_id=team_id,
        category_confidence=item.category_confidence,
        keyword_confidence=item.keyword_confidence,
        freshness_score=item.freshness_score,
        assignment_score=score,
        assignment_status=status,
        observed_at=item.observed_at,
        reason_codes=_row_reason_codes(
            category_reason=category_reason,
            category_confidence=item.category_confidence,
            keyword_confidence=item.keyword_confidence,
            freshness_score=item.freshness_score,
            assignment_status=status,
            team_id=team_id,
            config=config,
            primary=False,
        ),
    )


def _rank_rows(
    rows: tuple[MarketCategorySpecialistAssignmentRow, ...],
    config: MarketCategorySpecialistAssignmentConfig,
) -> tuple[MarketCategorySpecialistAssignmentRow, ...]:
    ranked_rows: list[MarketCategorySpecialistAssignmentRow] = []
    sorted_rows = sorted(rows, key=_row_sort_key)
    primary_team_id = _primary_team_id(tuple(sorted_rows))
    for index, row in enumerate(sorted_rows, start=1):
        is_primary = row.team_id == primary_team_id and row.assignment_status == "pass"
        ranked_rows.append(
            MarketCategorySpecialistAssignmentRow(
                rank=_count(index),
                category_label=row.category_label,
                team_id=row.team_id,
                category_confidence=row.category_confidence,
                keyword_confidence=row.keyword_confidence,
                freshness_score=row.freshness_score,
                assignment_score=row.assignment_score,
                assignment_status=row.assignment_status,
                observed_at=row.observed_at,
                reason_codes=_row_reason_codes(
                    category_reason=_category_reason_for_team(row.team_id),
                    category_confidence=row.category_confidence,
                    keyword_confidence=row.keyword_confidence,
                    freshness_score=row.freshness_score,
                    assignment_status=row.assignment_status,
                    team_id=row.team_id,
                    config=config,
                    primary=is_primary,
                ),
            ),
        )
    return tuple(ranked_rows)


def _team_reason_from_category_label(category_label: str) -> tuple[str, str]:
    normalized = category_label.casefold()
    if normalized in _CATEGORY_TO_TEAM_REASON:
        return _CATEGORY_TO_TEAM_REASON[normalized]
    raise ValueError("category_label must be a canonical category taxonomy label")


def _category_reason_for_team(team_id: str) -> str:
    for candidate_team_id, reason_code in _CATEGORY_TO_TEAM_REASON.values():
        if candidate_team_id == team_id:
            return reason_code
    if team_id == "other_sports":
        return "category_hint_other_sports"
    return "category_hint_general"


def _assignment_score(
    item: MarketCategorySpecialistAssignmentSignal,
    config: MarketCategorySpecialistAssignmentConfig,
    team_id: str,
) -> Decimal:
    if team_id == "general" and "general" not in config.available_team_ids:
        return _ZERO_RATIO
    with localcontext(_DECIMAL_CONTEXT):
        return _six(
            item.category_confidence * _CATEGORY_WEIGHT
            + item.keyword_confidence * _KEYWORD_WEIGHT
            + item.freshness_score * _FRESHNESS_WEIGHT,
        )


def _assignment_status(
    score: Decimal,
    team_id: str,
    config: MarketCategorySpecialistAssignmentConfig,
) -> str:
    if team_id == "general" and "general" not in config.available_team_ids:
        return "block"
    if score < config.assignment_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    category_reason: str,
    category_confidence: Decimal,
    keyword_confidence: Decimal,
    freshness_score: Decimal,
    assignment_status: str,
    team_id: str,
    config: MarketCategorySpecialistAssignmentConfig,
    primary: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = [category_reason]
    if assignment_status == "pass":
        if category_confidence >= Decimal("0.800000"):
            reason_codes.append("category_signal_strong")
        elif category_confidence >= Decimal("0.500000"):
            reason_codes.append("category_signal_watch")
        if keyword_confidence >= Decimal("0.800000"):
            reason_codes.append("keyword_signal_strong")
        elif keyword_confidence >= Decimal("0.500000"):
            reason_codes.append("keyword_signal_watch")
        if freshness_score >= Decimal("0.700000"):
            reason_codes.append("fresh_signal")
    if primary:
        reason_codes.append("primary_assignment")
    elif assignment_status == "pass":
        reason_codes.append("secondary_assignment")
    if assignment_status == "watch":
        reason_codes.append("assignment_confidence_watch")
    if team_id == "general" and "general" not in config.available_team_ids:
        reason_codes.append("no_general_team_available")
        reason_codes.append("assignment_block")
    elif assignment_status == "block":
        reason_codes.append("assignment_block")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), _ROW_REASON_SEQUENCE)


def _row_sort_key(
    row: MarketCategorySpecialistAssignmentRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        _ASSIGNMENT_STATUS_WEIGHT[row.assignment_status],
        -row.assignment_score,
        -row.category_confidence,
        _TEAM_SORT_INDEX[row.team_id],
        row.category_label,
    )


def _packet_status(rows: tuple[MarketCategorySpecialistAssignmentRow, ...]) -> str:
    if not rows:
        return "watch"
    if all(row.assignment_status == "block" for row in rows):
        return "block"
    if any(row.assignment_status == "pass" for row in rows):
        return "pass"
    if any(row.assignment_status == "block" for row in rows):
        return "block"
    return "watch"


def _primary_team_id(rows: tuple[MarketCategorySpecialistAssignmentRow, ...]) -> str | None:
    for row in rows:
        if row.assignment_status == "pass":
            return row.team_id
    return None


def _secondary_team_ids(
    rows: tuple[MarketCategorySpecialistAssignmentRow, ...],
    config: MarketCategorySpecialistAssignmentConfig,
) -> tuple[str, ...]:
    primary_team_id = _primary_team_id(rows)
    if primary_team_id is None:
        return ()
    secondary: list[str] = []
    selected_count = _ZERO_COUNT
    for row in rows:
        if selected_count >= config.max_secondary_team_count:
            break
        if row.assignment_status != "pass" or row.team_id == primary_team_id:
            continue
        if row.team_id in secondary:
            continue
        secondary.append(row.team_id)
        selected_count += _COUNT_QUANTUM
    return tuple(secondary)


def _packet_reason_codes(
    rows: tuple[MarketCategorySpecialistAssignmentRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_category_signals",)
    reason_codes: list[str] = []
    if any(row.assignment_status == "pass" for row in rows):
        reason_codes.append("primary_assignment_selected")
        if len(tuple(row for row in rows if row.assignment_status == "pass")) > 1:
            reason_codes.append("secondary_assignments_selected")
    if any(row.assignment_status == "watch" for row in rows):
        reason_codes.append("assignment_confidence_watch")
    if any("no_general_team_available" in row.reason_codes for row in rows):
        reason_codes.append("no_general_team_available")
    if any(row.assignment_status == "block" for row in rows):
        reason_codes.append("assignment_block")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        _PACKET_REASON_SEQUENCE,
    )


def _normalize_inputs(
    value: object,
) -> tuple[MarketCategorySpecialistAssignmentSignal, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for item in rows:
        if type(item) is not MarketCategorySpecialistAssignmentSignal:
            raise ValueError("inputs must contain exact assignment signals")
        _require_hard_flags("signal", item)
        team_id, _reason_code = _team_reason_from_category_label(item.category_label)
        if team_id in seen:
            raise ValueError("inputs must not contain duplicate teams")
        seen.add(team_id)
    return rows


def _normalize_assignments(
    value: object,
) -> tuple[MarketCategorySpecialistAssignmentRow, ...]:
    if type(value) is not tuple:
        raise ValueError("assignments must be a tuple")
    rows = tuple(value)
    expected_rank = _COUNT_QUANTUM
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketCategorySpecialistAssignmentRow:
            raise ValueError("assignments must contain exact assignment rows")
        _require_hard_flags("row", row)
        _validate_row_digest(row)
        if row.team_id in seen:
            raise ValueError("assignments must not contain duplicate teams")
        seen.add(row.team_id)
        if row.rank != expected_rank:
            raise ValueError("assignments must use consecutive ranks")
        expected_rank += _COUNT_QUANTUM
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("assignments must be sorted")
    return rows


def _normalize_available_team_ids(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or type(value) not in (list, tuple):
        raise ValueError("available_team_ids must be a list or tuple")
    team_ids = tuple(require_strategy_team_id("available_team_ids", item) for item in value)
    if len(set(team_ids)) != len(team_ids):
        raise ValueError("available_team_ids must be unique")
    if not team_ids:
        raise ValueError("available_team_ids must not be empty")
    for required_team_id in (
        "politics",
        "crypto_btc",
        "equity_index",
        "commodities_gold",
        "soccer",
        "basketball",
        "other_sports",
    ):
        if required_team_id not in team_ids:
            raise ValueError("available_team_ids must include the medium-scale specialists")
    return tuple(team_id for team_id in STRATEGY_TEAM_IDS if team_id in team_ids)


def _normalize_secondary_team_ids(value: object, primary_team_id: str | None) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("secondary_team_ids must be a tuple")
    team_ids = tuple(require_strategy_team_id("secondary_team_ids", item) for item in value)
    if primary_team_id is not None and primary_team_id in team_ids:
        raise ValueError("secondary_team_ids must not contain primary_team_id")
    if len(set(team_ids)) != len(team_ids):
        raise ValueError("secondary_team_ids must be unique")
    return team_ids


def _validate_row_consistency(row: MarketCategorySpecialistAssignmentRow) -> None:
    team_id, _reason_code = _team_reason_from_category_label(row.category_label)
    if row.team_id != team_id:
        raise ValueError("team_id must match category_label")
    expected_score = _six(
        row.category_confidence * _CATEGORY_WEIGHT
        + row.keyword_confidence * _KEYWORD_WEIGHT
        + row.freshness_score * _FRESHNESS_WEIGHT,
    )
    if row.assignment_status != "block" and row.assignment_score != expected_score:
        raise ValueError("assignment_score must match row inputs")
    if row.assignment_status == "block" and row.assignment_score != _ZERO_RATIO:
        raise ValueError("block assignment_score must be zero")


def _validate_packet_consistency(packet: MarketCategorySpecialistAssignmentPacket) -> None:
    rows = packet.assignments
    if packet.team_count != _count(len(rows)):
        raise ValueError("team_count must match assignments")
    if packet.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match assignments")
    if packet.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match assignments")
    if packet.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match assignments")
    if packet.top_assignment_score != _top_assignment_score(rows):
        raise ValueError("top_assignment_score must match assignments")
    if packet.assignment_status != _packet_status(rows):
        raise ValueError("assignment_status must match assignments")
    if packet.primary_team_id != _primary_team_id(rows):
        raise ValueError("primary_team_id must match assignments")
    assigned_secondary_team_ids = tuple(
        row.team_id
        for row in rows
        if row.assignment_status == "pass" and row.team_id != packet.primary_team_id
    )
    if packet.secondary_team_ids != assigned_secondary_team_ids[: len(packet.secondary_team_ids)]:
        raise ValueError("secondary_team_ids must match assignments")
    if packet.reason_codes != _packet_reason_codes(rows):
        raise ValueError("reason_codes must match assignments")


def _status_count(
    rows: tuple[MarketCategorySpecialistAssignmentRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.assignment_status == status))


def _top_assignment_score(rows: tuple[MarketCategorySpecialistAssignmentRow, ...]) -> Decimal:
    if not rows:
        return _ZERO_RATIO
    return max(row.assignment_score for row in rows)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _six(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_SIX_PLACE_QUANTUM)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _six(value)
    if quantized < _ZERO_RATIO or quantized > _ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return quantized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= _ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_canonical_public_string(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known values")
    seen = set(reason_codes)
    return tuple(reason_code for reason_code in allowed if reason_code in seen)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_canonical_category_label(field_name: str, value: object) -> str:
    category_label = _require_canonical_public_string(field_name, value)
    if category_label not in _CANONICAL_CATEGORY_LABELS:
        raise ValueError(f"{field_name} must be a canonical category taxonomy label")
    return category_label


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, object]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("payload paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError("payload report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError("payload readonly must be True")


def _apply_or_verify_digest(value: object) -> None:
    expected_digest = _digest_value(value)
    actual_digest = getattr(value, _DIGEST_FIELD)
    if actual_digest == "":
        object.__setattr__(value, _DIGEST_FIELD, expected_digest)
        return
    if actual_digest != expected_digest:
        raise ValueError("derived_validation_digest must match fields")


def _validate_row_digest(row: MarketCategorySpecialistAssignmentRow) -> None:
    if row.derived_validation_digest != _digest_value(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_packet_digest(packet: MarketCategorySpecialistAssignmentPacket) -> None:
    for row in packet.assignments:
        _validate_row_digest(row)
    if packet.derived_validation_digest != _digest_value(packet):
        raise ValueError("derived_validation_digest must match packet fields")


def _validate_payload_digest(payload: dict[str, object]) -> None:
    provided_digest = payload.get(_DIGEST_FIELD)
    if type(provided_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if provided_digest != _digest_value(payload):
        raise ValueError("derived_validation_digest must match payload fields")


def _digest_value(value: object) -> str:
    ready = _payload_value(value, omit_digest=True)
    _reject_unsafe_public_payload("derived validation payload", ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object, *, omit_digest: bool = False) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            if omit_digest and field.name == _DIGEST_FIELD:
                continue
            ready[field.name] = _payload_value(getattr(value, field.name), omit_digest=omit_digest)
        return ready
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is tuple:
        return [_payload_value(item, omit_digest=omit_digest) for item in value]
    if type(value) is list:
        return [_payload_value(item, omit_digest=omit_digest) for item in value]
    if type(value) is dict:
        ready = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if omit_digest and key == _DIGEST_FIELD:
                continue
            ready[key] = _payload_value(item, omit_digest=omit_digest)
        return ready
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload contains value with unsupported type")


def _reject_non_string_numeric(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is float:
        raise ValueError("float values are not supported in public payloads")
    if type(value) is int:
        raise ValueError("public numeric values must be Decimal strings")
    if type(value) is Decimal:
        raise ValueError("public Decimal values must be strings")
    if type(value) is dict:
        for item in value.values():
            _reject_non_string_numeric(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_non_string_numeric(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        if _contains_unsafe_public_text(value):
            raise ValueError(f"unsafe public payload in {label}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            if _contains_unsafe_public_text(key):
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _UNSAFE_PUBLIC_TERMS)


__all__ = (
    "DEFAULT_MARKET_CATEGORY_SPECIALIST_ASSIGNMENT_PACKET_CONFIG_VERSION",
    "ASSIGNMENT_STATUSES",
    "PACKET_STATUSES",
    "MarketCategorySpecialistAssignmentConfig",
    "MarketCategorySpecialistAssignmentSignal",
    "MarketCategorySpecialistAssignmentRow",
    "MarketCategorySpecialistAssignmentPacket",
    "build_market_category_specialist_assignment_packet",
    "market_category_specialist_assignment_packet_payload",
)
