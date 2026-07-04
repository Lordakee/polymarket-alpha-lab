from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


DEFAULT_BASKETBALL_ROTATION_INJURY_CLUSTER_DIGEST_CONFIG_VERSION = (
    "basketball_rotation_injury_cluster_digest.v1"
)

_ZERO = Decimal("0")
_ONE = Decimal("1")
_TWO = Decimal("2")
_QUANT = Decimal("0.000001")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")

_ROTATION_ROLES = frozenset(("starter", "key_reserve", "reserve", "two_way"))
_INJURY_STATUSES = frozenset(
    ("out", "doubtful", "questionable", "probable", "available")
)
_ROW_STATUSES = frozenset(("screen", "watch", "pass"))
_REPORT_STATUSES = frozenset(("screen", "watch", "clear"))
_ROW_REASON_CODE_ORDER = (
    "rotation_minutes_cluster",
    "high_usage_cluster",
    "multi_player_absence",
    "starter_absence_signal",
    "short_event_window",
    "priced_probability_gap",
    "insufficient_cluster_risk",
)
_REPORT_REASON_CODE_ORDER = (
    "screenable_injury_cluster",
    "watch_injury_cluster",
    "no_screenable_injury_cluster",
    "no_rotation_injury_signals",
)
_SENSITIVE_TEXT_MARKERS = (
    "sk_live",
    "sk_test",
    "api_key",
    "private" "_key",
    "bearer ",
    "password=",
    "token=",
)


@dataclass(frozen=True)
class BasketballRotationInjuryClusterDigestConfig:
    config_version: str = DEFAULT_BASKETBALL_ROTATION_INJURY_CLUSTER_DIGEST_CONFIG_VERSION
    high_risk_score_threshold: Decimal = Decimal("0.700000")
    watch_risk_score_threshold: Decimal = Decimal("0.400000")
    affected_minutes_share_threshold: Decimal = Decimal("0.350000")
    affected_usage_share_threshold: Decimal = Decimal("0.300000")
    expected_absence_count_threshold: Decimal = Decimal("1.250000")
    starter_absence_probability_threshold: Decimal = Decimal("0.600000")
    market_probability_gap_threshold: Decimal = Decimal("0.150000")
    short_event_window_seconds: Decimal = Decimal("86400")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_text("config_version", self.config_version),
        )
        for field_name in (
            "high_risk_score_threshold",
            "watch_risk_score_threshold",
            "affected_minutes_share_threshold",
            "affected_usage_share_threshold",
            "starter_absence_probability_threshold",
            "market_probability_gap_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_absence_count_threshold",
            "short_event_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.high_risk_score_threshold < self.watch_risk_score_threshold:
            raise ValueError(
                "high_risk_score_threshold must be greater than or equal to "
                "watch_risk_score_threshold"
            )
        _require_hard_flags("BasketballRotationInjuryClusterDigestConfig", self)


@dataclass(frozen=True)
class BasketballRotationInjurySignal:
    market_slug: str
    event_id: str
    team_name: str
    player_name: str
    rotation_role: str
    injury_status: str
    event_start: datetime
    observed_at: datetime
    minutes_share: Decimal
    usage_share: Decimal
    absence_probability: Decimal
    market_reference_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "market_slug",
            "event_id",
            "team_name",
            "player_name",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_canonical_text(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "rotation_role",
            _require_member("rotation_role", self.rotation_role, _ROTATION_ROLES),
        )
        object.__setattr__(
            self,
            "injury_status",
            _require_member("injury_status", self.injury_status, _INJURY_STATUSES),
        )
        object.__setattr__(self, "event_start", _as_utc("event_start", self.event_start))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "minutes_share",
            "usage_share",
            "absence_probability",
            "market_reference_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("BasketballRotationInjurySignal", self)


@dataclass(frozen=True)
class BasketballRotationInjuryClusterRow:
    market_slug: str
    event_id: str
    team_name: str
    event_start: datetime
    affected_player_count: Decimal
    affected_minutes_share: Decimal
    affected_usage_share: Decimal
    expected_absence_count: Decimal
    max_absence_probability: Decimal
    market_reference_probability: Decimal
    injury_probability_gap: Decimal
    injury_cluster_score: Decimal
    screening_status: str
    reason_codes: tuple[str, ...]
    affected_players: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_slug", "event_id", "team_name"):
            object.__setattr__(
                self,
                field_name,
                _require_canonical_text(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "event_start", _as_utc("event_start", self.event_start))
        object.__setattr__(
            self,
            "affected_player_count",
            _normalize_nonnegative_decimal(
                "affected_player_count",
                self.affected_player_count,
            ),
        )
        object.__setattr__(
            self,
            "expected_absence_count",
            _normalize_nonnegative_decimal(
                "expected_absence_count",
                self.expected_absence_count,
            ),
        )
        for field_name in (
            "affected_minutes_share",
            "affected_usage_share",
            "max_absence_probability",
            "market_reference_probability",
            "injury_probability_gap",
            "injury_cluster_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "screening_status",
            _require_member("screening_status", self.screening_status, _ROW_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _ROW_REASON_CODE_ORDER,
            ),
        )
        object.__setattr__(
            self,
            "affected_players",
            _normalize_text_tuple("affected_players", self.affected_players),
        )
        _validate_row_consistency(self)
        _require_hard_flags("BasketballRotationInjuryClusterRow", self)


@dataclass(frozen=True)
class BasketballRotationInjuryClusterDigestReport:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    screen_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    total_affected_player_count: Decimal
    max_injury_cluster_score: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[BasketballRotationInjuryClusterRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_text("config_version", self.config_version),
        )
        for field_name in (
            "market_count",
            "screen_count",
            "watch_count",
            "pass_count",
            "total_affected_player_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_injury_cluster_score",
            _normalize_ratio(
                "max_injury_cluster_score",
                self.max_injury_cluster_score,
            ),
        )
        object.__setattr__(
            self,
            "digest_status",
            _require_member("digest_status", self.digest_status, _REPORT_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _REPORT_REASON_CODE_ORDER,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("BasketballRotationInjuryClusterDigestReport", self)


def build_basketball_rotation_injury_cluster_digest(
    signals: Iterable[BasketballRotationInjurySignal],
    *,
    generated_at: datetime,
    config: BasketballRotationInjuryClusterDigestConfig | None = None,
) -> BasketballRotationInjuryClusterDigestReport:
    checked_generated_at = _as_utc("generated_at", generated_at)
    checked_config = config or BasketballRotationInjuryClusterDigestConfig()
    if type(checked_config) is not BasketballRotationInjuryClusterDigestConfig:
        raise ValueError("config must be a BasketballRotationInjuryClusterDigestConfig")

    checked_signals = _normalize_signals(signals)
    grouped: dict[tuple[str, str, str, datetime], list[BasketballRotationInjurySignal]] = {}
    for signal in checked_signals:
        key = (signal.market_slug, signal.event_id, signal.team_name, signal.event_start)
        grouped.setdefault(key, []).append(signal)

    rows = tuple(
        sorted(
            (
                _build_cluster_row(
                    group_signals,
                    generated_at=checked_generated_at,
                    config=checked_config,
                )
                for group_signals in grouped.values()
            ),
            key=_row_sort_key,
        )
    )
    digest_status = _digest_status(rows)
    return BasketballRotationInjuryClusterDigestReport(
        generated_at=checked_generated_at,
        config_version=checked_config.config_version,
        market_count=_decimal_count(len(rows)),
        screen_count=_decimal_count(
            sum(1 for row in rows if row.screening_status == "screen")
        ),
        watch_count=_decimal_count(
            sum(1 for row in rows if row.screening_status == "watch")
        ),
        pass_count=_decimal_count(
            sum(1 for row in rows if row.screening_status == "pass")
        ),
        total_affected_player_count=sum(
            (row.affected_player_count for row in rows),
            _ZERO,
        ),
        max_injury_cluster_score=max(
            (row.injury_cluster_score for row in rows),
            default=_ZERO,
        ),
        digest_status=digest_status,
        reason_codes=_report_reason_codes(rows, digest_status),
        rows=rows,
    )


def _build_cluster_row(
    signals: list[BasketballRotationInjurySignal],
    *,
    generated_at: datetime,
    config: BasketballRotationInjuryClusterDigestConfig,
) -> BasketballRotationInjuryClusterRow:
    ordered_signals = tuple(sorted(signals, key=_signal_sort_key))
    first = ordered_signals[0]
    affected_minutes_share = _cap_ratio(
        sum((signal.minutes_share for signal in ordered_signals), _ZERO)
    )
    affected_usage_share = _cap_ratio(
        sum((signal.usage_share for signal in ordered_signals), _ZERO)
    )
    expected_absence_count = _q(
        sum((signal.absence_probability for signal in ordered_signals), _ZERO)
    )
    max_absence_probability = max(
        (signal.absence_probability for signal in ordered_signals),
        default=_ZERO,
    )
    market_reference_probability = max(
        (signal.market_reference_probability for signal in ordered_signals),
        default=_ZERO,
    )
    injury_cluster_score = _cluster_score(
        affected_minutes_share=affected_minutes_share,
        affected_usage_share=affected_usage_share,
        expected_absence_count=expected_absence_count,
        max_absence_probability=max_absence_probability,
    )
    injury_probability_gap = _cap_ratio(
        max(injury_cluster_score - market_reference_probability, _ZERO)
    )
    reason_codes = _row_reason_codes(
        ordered_signals,
        generated_at=generated_at,
        config=config,
        affected_minutes_share=affected_minutes_share,
        affected_usage_share=affected_usage_share,
        expected_absence_count=expected_absence_count,
        injury_probability_gap=injury_probability_gap,
    )
    screening_status = _screening_status(
        injury_cluster_score=injury_cluster_score,
        reason_codes=reason_codes,
        config=config,
    )
    if screening_status == "pass":
        reason_codes = ("insufficient_cluster_risk",)

    return BasketballRotationInjuryClusterRow(
        market_slug=first.market_slug,
        event_id=first.event_id,
        team_name=first.team_name,
        event_start=first.event_start,
        affected_player_count=_decimal_count(len(ordered_signals)),
        affected_minutes_share=affected_minutes_share,
        affected_usage_share=affected_usage_share,
        expected_absence_count=expected_absence_count,
        max_absence_probability=max_absence_probability,
        market_reference_probability=market_reference_probability,
        injury_probability_gap=injury_probability_gap,
        injury_cluster_score=injury_cluster_score,
        screening_status=screening_status,
        reason_codes=reason_codes,
        affected_players=tuple(signal.player_name for signal in ordered_signals),
    )


def _row_reason_codes(
    signals: tuple[BasketballRotationInjurySignal, ...],
    *,
    generated_at: datetime,
    config: BasketballRotationInjuryClusterDigestConfig,
    affected_minutes_share: Decimal,
    affected_usage_share: Decimal,
    expected_absence_count: Decimal,
    injury_probability_gap: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if affected_minutes_share >= config.affected_minutes_share_threshold:
        reason_codes.append("rotation_minutes_cluster")
    if affected_usage_share >= config.affected_usage_share_threshold:
        reason_codes.append("high_usage_cluster")
    if expected_absence_count >= config.expected_absence_count_threshold:
        reason_codes.append("multi_player_absence")
    if any(
        signal.rotation_role == "starter"
        and signal.absence_probability >= config.starter_absence_probability_threshold
        for signal in signals
    ):
        reason_codes.append("starter_absence_signal")
    if injury_probability_gap >= config.market_probability_gap_threshold:
        reason_codes.append("priced_probability_gap")
    if reason_codes and _within_short_event_window(
        signals[0].event_start,
        generated_at=generated_at,
        config=config,
    ):
        reason_codes.append("short_event_window")
    if not reason_codes:
        reason_codes.append("insufficient_cluster_risk")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        _ROW_REASON_CODE_ORDER,
    )


def _screening_status(
    *,
    injury_cluster_score: Decimal,
    reason_codes: tuple[str, ...],
    config: BasketballRotationInjuryClusterDigestConfig,
) -> str:
    if injury_cluster_score >= config.high_risk_score_threshold:
        return "screen"
    if (
        reason_codes != ("insufficient_cluster_risk",)
        and injury_cluster_score >= config.watch_risk_score_threshold
    ):
        return "watch"
    return "pass"


def _cluster_score(
    *,
    affected_minutes_share: Decimal,
    affected_usage_share: Decimal,
    expected_absence_count: Decimal,
    max_absence_probability: Decimal,
) -> Decimal:
    expected_absence_component = min(expected_absence_count / _TWO, _ONE)
    return _cap_ratio(
        max(
            affected_minutes_share,
            affected_usage_share,
            expected_absence_component,
            max_absence_probability,
        )
    )


def _report_reason_codes(
    rows: tuple[BasketballRotationInjuryClusterRow, ...],
    digest_status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("no_rotation_injury_signals",)
    if digest_status == "screen":
        return ("screenable_injury_cluster",)
    if digest_status == "watch":
        return ("watch_injury_cluster",)
    return ("no_screenable_injury_cluster",)


def _digest_status(rows: tuple[BasketballRotationInjuryClusterRow, ...]) -> str:
    if any(row.screening_status == "screen" for row in rows):
        return "screen"
    if any(row.screening_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _within_short_event_window(
    event_start: datetime,
    *,
    generated_at: datetime,
    config: BasketballRotationInjuryClusterDigestConfig,
) -> bool:
    delta = event_start - generated_at
    seconds = (
        Decimal(delta.days) * _SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND)
    )
    return _ZERO <= seconds <= config.short_event_window_seconds


def _normalize_signals(
    signals: Iterable[BasketballRotationInjurySignal],
) -> tuple[BasketballRotationInjurySignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of BasketballRotationInjurySignal")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError(
            "signals must be an iterable of BasketballRotationInjurySignal"
        ) from exc
    for signal in normalized:
        if type(signal) is not BasketballRotationInjurySignal:
            raise ValueError("signals must contain BasketballRotationInjurySignal items")
    return normalized


def _normalize_rows(
    rows: tuple[BasketballRotationInjuryClusterRow, ...],
) -> tuple[BasketballRotationInjuryClusterRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not BasketballRotationInjuryClusterRow:
            raise ValueError("rows must contain BasketballRotationInjuryClusterRow items")
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(row: BasketballRotationInjuryClusterRow) -> tuple[object, ...]:
    status_rank = {"screen": 0, "watch": 1, "pass": 2}[row.screening_status]
    return (
        status_rank,
        -row.injury_cluster_score,
        row.event_start,
        row.market_slug,
        row.team_name,
        row.event_id,
    )


def _signal_sort_key(signal: BasketballRotationInjurySignal) -> tuple[object, ...]:
    role_rank = {"starter": 0, "key_reserve": 1, "reserve": 2, "two_way": 3}[
        signal.rotation_role
    ]
    return (
        signal.player_name,
        role_rank,
        signal.injury_status,
        signal.observed_at,
        signal.market_slug,
    )


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed_order: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple) or not reason_codes:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    allowed = set(allowed_order)
    unique = []
    for reason_code in reason_codes:
        checked = _require_canonical_text(field_name, reason_code)
        if checked not in allowed:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if checked not in unique:
            unique.append(checked)
    return tuple(reason_code for reason_code in allowed_order if reason_code in unique)


def _normalize_text_tuple(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    return tuple(sorted(_require_canonical_text(field_name, value) for value in values))


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    checked = _require_decimal(field_name, value)
    if checked < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _q(checked)


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    checked = _normalize_nonnegative_decimal(field_name, value)
    if checked > _ONE:
        raise ValueError(f"{field_name} must be less than or equal to 1")
    return checked


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_canonical_text(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character in value for character in ("\n", "\r", "\t")):
        raise ValueError(f"{field_name} must be a single-line string")
    lowered = value.lower()
    if any(marker in lowered for marker in _SENSITIVE_TEXT_MARKERS):
        raise ValueError(f"{field_name} must not contain sensitive material")
    return value


def _require_member(field_name: str, value: str, allowed: frozenset[str]) -> str:
    checked = _require_canonical_text(field_name, value)
    if checked not in allowed:
        raise ValueError(f"{field_name} must be one of {tuple(sorted(allowed))}")
    return checked


def _require_hard_flags(context: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{context}.{flag_name} must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value)


def _cap_ratio(value: Decimal) -> Decimal:
    return _q(min(max(value, _ZERO), _ONE))


def _q(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _validate_row_consistency(row: BasketballRotationInjuryClusterRow) -> None:
    if row.affected_player_count != _decimal_count(len(row.affected_players)):
        raise ValueError("affected_player_count must match affected_players")
    if row.screening_status == "pass" and row.reason_codes != (
        "insufficient_cluster_risk",
    ):
        raise ValueError("pass rows must use insufficient_cluster_risk")
    if row.screening_status != "pass" and row.reason_codes == (
        "insufficient_cluster_risk",
    ):
        raise ValueError("screenable rows must include a risk reason")


def _validate_report_consistency(
    report: BasketballRotationInjuryClusterDigestReport,
) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.screen_count != _decimal_count(
        sum(1 for row in report.rows if row.screening_status == "screen")
    ):
        raise ValueError("screen_count must match rows")
    if report.watch_count != _decimal_count(
        sum(1 for row in report.rows if row.screening_status == "watch")
    ):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _decimal_count(
        sum(1 for row in report.rows if row.screening_status == "pass")
    ):
        raise ValueError("pass_count must match rows")
    if report.total_affected_player_count != sum(
        (row.affected_player_count for row in report.rows),
        _ZERO,
    ):
        raise ValueError("total_affected_player_count must match rows")
    if report.max_injury_cluster_score != max(
        (row.injury_cluster_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_injury_cluster_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, report.digest_status):
        raise ValueError("reason_codes must match digest_status")
