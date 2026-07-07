"""Pure read-only scorecard for domain team memory readiness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any, Mapping

from polymarket_alpha_lab.team_memory_readiness_digest import (
    TeamMemoryReadinessDigestReport,
)
from polymarket_alpha_lab.team_memory_readiness_digest_history import (
    TeamMemoryReadinessDigestHistoryReport,
)
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_DOMAIN_TEAM_MEMORY_SCORECARD_CONFIG_VERSION = (
    "domain-team-memory-scorecard-v0"
)
DEFAULT_SCORECARD_DOMAIN_TEAM_IDS = (
    ("politics", ("politics",)),
    ("crypto_btc", ("crypto_btc",)),
    ("macro_rates", ("macro_rates",)),
    ("sports", ("sports_soccer", "sports_basketball", "sports_other")),
)
DOMAIN_MEMORY_SCORECARD_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "domain_team_memory_ready",
    "domain_team_memory_watch",
    "domain_team_memory_blocked",
    "domain_team_memory_missing",
    "domain_team_memory_history_blocked",
)
REPORT_REASON_CODES = (
    "domain_team_memory_scorecard_ready",
    "domain_team_memory_scorecard_blocked_rows",
    "domain_team_memory_scorecard_history_blocked",
    "domain_team_memory_scorecard_watch_rows",
    "domain_team_memory_scorecard_empty",
)
DECIMAL_ZERO = Decimal("0")
COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
SCORE_QUANT = Decimal("0.000001")
DIGEST_HEX_LENGTH = 64
UNSAFE_PUBLIC_FRAGMENTS = (
    "acc" "ount",
    "au" "th",
    "b" "uy",
    "can" "cel",
    "cre" "dential",
    "data" "base",
    "dot" "env",
    "env" "iron",
    "fi" "le",
    "inv" "est",
    "li" "ve",
    "net" "work",
    "or" "der",
    "pri" "vate_key",
    "req" "uest",
    "se" "ll",
    "soc" "ket",
    "s" "tore",
    "sub" "mit",
    "supa" "base",
    "tr" "ade",
    "url" "lib",
    "wa" "llet",
)


@dataclass(frozen=True)
class DomainTeamMemoryScorecardConfig:
    config_version: str = DEFAULT_DOMAIN_TEAM_MEMORY_SCORECARD_CONFIG_VERSION
    domain_team_ids: tuple[tuple[str, tuple[str, ...]], ...] = (
        DEFAULT_SCORECARD_DOMAIN_TEAM_IDS
    )
    pass_score: Decimal = Decimal("1.000000")
    watch_score: Decimal = Decimal("0.500000")
    blocked_score: Decimal = Decimal("0.000000")
    missing_score: Decimal = Decimal("0.000000")
    history_blocked_penalty: Decimal = Decimal("0.250000")
    watch_threshold: Decimal = Decimal("0.750000")
    pass_threshold: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "domain_team_ids",
            _normalize_domain_team_ids(self.domain_team_ids),
        )
        for field_name in (
            "pass_score",
            "watch_score",
            "blocked_score",
            "missing_score",
            "history_blocked_penalty",
            "watch_threshold",
            "pass_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_threshold > self.pass_threshold:
            raise ValueError("watch_threshold must not exceed pass_threshold")
        require_paper_only_flags("DomainTeamMemoryScorecardConfig", self)
        _reject_unsafe_public_payload("DomainTeamMemoryScorecardConfig", self)


@dataclass(frozen=True)
class DomainTeamMemoryScorecardRow:
    domain_id: str
    team_ids: tuple[str, ...]
    configured_team_count: Decimal
    latest_team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    missing_team_count: Decimal
    raw_memory_score: Decimal
    history_penalty: Decimal
    memory_score: Decimal
    memory_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("domain_id", self.domain_id)
        object.__setattr__(self, "team_ids", _normalize_team_ids(self.team_ids))
        for field_name in (
            "configured_team_count",
            "latest_team_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "missing_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("raw_memory_score", "history_penalty", "memory_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_scorecard_status("memory_status", self.memory_status)
        object.__setattr__(self, "reason_codes", _normalize_row_reason_codes(self.reason_codes))
        require_paper_only_flags("DomainTeamMemoryScorecardRow", self)
        _reject_unsafe_public_payload("DomainTeamMemoryScorecardRow", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class DomainTeamMemoryScorecardReport:
    generated_at: datetime
    config_version: str
    source_digest_config_version: str
    source_history_config_version: str
    scorecard_status: str
    domain_count: Decimal
    pass_domain_count: Decimal
    watch_domain_count: Decimal
    blocked_domain_count: Decimal
    configured_team_count: Decimal
    latest_team_count: Decimal
    missing_team_count: Decimal
    average_memory_score: Decimal
    lowest_memory_score: Decimal
    history_status: str
    history_report_count: Decimal
    history_required_report_count: Decimal
    rows: tuple[DomainTeamMemoryScorecardRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_digest_config_version", self.source_digest_config_version)
        _require_canonical_string("source_history_config_version", self.source_history_config_version)
        _require_scorecard_status("scorecard_status", self.scorecard_status)
        for field_name in (
            "domain_count",
            "pass_domain_count",
            "watch_domain_count",
            "blocked_domain_count",
            "configured_team_count",
            "latest_team_count",
            "missing_team_count",
            "history_report_count",
            "history_required_report_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("average_memory_score", "lowest_memory_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_history_status("history_status", self.history_status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        require_paper_only_flags("DomainTeamMemoryScorecardReport", self)
        _reject_unsafe_public_payload("DomainTeamMemoryScorecardReport", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "DomainTeamMemoryScorecardReport.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_domain_team_memory_scorecard_report(
    *,
    latest_digest: TeamMemoryReadinessDigestReport,
    history: TeamMemoryReadinessDigestHistoryReport,
    config: DomainTeamMemoryScorecardConfig,
    generated_at: datetime,
) -> DomainTeamMemoryScorecardReport:
    if type(config) is not DomainTeamMemoryScorecardConfig:
        raise ValueError("config must be a DomainTeamMemoryScorecardConfig")
    if type(latest_digest) is not TeamMemoryReadinessDigestReport:
        raise ValueError("latest_digest must be a TeamMemoryReadinessDigestReport")
    if type(history) is not TeamMemoryReadinessDigestHistoryReport:
        raise ValueError("history must be a TeamMemoryReadinessDigestHistoryReport")
    require_paper_only_flags("DomainTeamMemoryScorecardConfig", config)
    require_paper_only_flags("TeamMemoryReadinessDigestReport", latest_digest)
    require_paper_only_flags("TeamMemoryReadinessDigestHistoryReport", history)

    rows = _scorecard_rows(latest_digest, history, config)
    reason_codes = _report_reason_codes(rows, history.history_status)
    values: dict[str, object] = {
        "generated_at": _as_utc("generated_at", generated_at),
        "config_version": config.config_version,
        "source_digest_config_version": latest_digest.config_version,
        "source_history_config_version": history.config_version,
        "scorecard_status": _scorecard_status(reason_codes),
        "domain_count": _decimal_count(len(rows)),
        "pass_domain_count": _decimal_count(
            sum(1 for row in rows if row.memory_status == "pass"),
        ),
        "watch_domain_count": _decimal_count(
            sum(1 for row in rows if row.memory_status == "watch"),
        ),
        "blocked_domain_count": _decimal_count(
            sum(1 for row in rows if row.memory_status == "blocked"),
        ),
        "configured_team_count": sum(
            (row.configured_team_count for row in rows),
            DECIMAL_ZERO,
        ).quantize(COUNT_QUANT),
        "latest_team_count": sum(
            (row.latest_team_count for row in rows),
            DECIMAL_ZERO,
        ).quantize(COUNT_QUANT),
        "missing_team_count": sum(
            (row.missing_team_count for row in rows),
            DECIMAL_ZERO,
        ).quantize(COUNT_QUANT),
        "average_memory_score": _average_score(rows),
        "lowest_memory_score": _lowest_score(rows),
        "history_status": history.history_status,
        "history_report_count": _decimal_count(history.report_count),
        "history_required_report_count": _decimal_count(history.required_report_count),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return DomainTeamMemoryScorecardReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def domain_team_memory_scorecard_payload(
    report: DomainTeamMemoryScorecardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is DomainTeamMemoryScorecardReport:
        require_paper_only_flags("DomainTeamMemoryScorecardReport", report)
        _reject_unsafe_public_payload("DomainTeamMemoryScorecardReport", report)
        payload = report.payload
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a DomainTeamMemoryScorecardReport or payload")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _scorecard_rows(
    latest_digest: TeamMemoryReadinessDigestReport,
    history: TeamMemoryReadinessDigestHistoryReport,
    config: DomainTeamMemoryScorecardConfig,
) -> tuple[DomainTeamMemoryScorecardRow, ...]:
    statuses_by_team_id = {
        source_status.team_id: source_status.gate_status
        for source_status in latest_digest.source_statuses
    }
    return tuple(
        _scorecard_row(
            domain_id=domain_id,
            team_ids=team_ids,
            statuses_by_team_id=statuses_by_team_id,
            history_blocked=history.history_status == "blocked",
            config=config,
        )
        for domain_id, team_ids in config.domain_team_ids
    )


def _scorecard_row(
    *,
    domain_id: str,
    team_ids: tuple[str, ...],
    statuses_by_team_id: dict[str, str],
    history_blocked: bool,
    config: DomainTeamMemoryScorecardConfig,
) -> DomainTeamMemoryScorecardRow:
    latest_statuses = tuple(
        statuses_by_team_id[team_id]
        for team_id in team_ids
        if team_id in statuses_by_team_id
    )
    pass_count = _decimal_count(sum(1 for status in latest_statuses if status == "pass"))
    watch_count = _decimal_count(sum(1 for status in latest_statuses if status == "watch"))
    blocked_count = _decimal_count(
        sum(1 for status in latest_statuses if status == "blocked"),
    )
    configured_team_count = _decimal_count(len(team_ids))
    latest_team_count = _decimal_count(len(latest_statuses))
    missing_team_count = configured_team_count - latest_team_count
    raw_score = _raw_memory_score(
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        missing_team_count=missing_team_count,
        configured_team_count=configured_team_count,
        config=config,
    )
    history_penalty = (
        config.history_blocked_penalty if history_blocked else Decimal("0.000000")
    )
    score = max(DECIMAL_ZERO, raw_score - history_penalty).quantize(SCORE_QUANT)
    reason_codes = _row_reason_codes(
        missing_team_count=missing_team_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        history_blocked=history_blocked,
    )
    return DomainTeamMemoryScorecardRow(
        domain_id=domain_id,
        team_ids=team_ids,
        configured_team_count=configured_team_count,
        latest_team_count=latest_team_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        missing_team_count=missing_team_count,
        raw_memory_score=raw_score,
        history_penalty=history_penalty,
        memory_score=score,
        memory_status=_memory_status(score, config),
        reason_codes=reason_codes,
    )


def _raw_memory_score(
    *,
    pass_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    missing_team_count: Decimal,
    configured_team_count: Decimal,
    config: DomainTeamMemoryScorecardConfig,
) -> Decimal:
    if configured_team_count == DECIMAL_ZERO:
        return Decimal("0.000000")
    weighted_score = (
        pass_count * config.pass_score
        + watch_count * config.watch_score
        + blocked_count * config.blocked_score
        + missing_team_count * config.missing_score
    )
    return (weighted_score / configured_team_count).quantize(SCORE_QUANT)


def _row_reason_codes(
    *,
    missing_team_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    history_blocked: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if blocked_count > DECIMAL_ZERO:
        reason_codes.append("domain_team_memory_blocked")
    if missing_team_count > DECIMAL_ZERO:
        reason_codes.append("domain_team_memory_missing")
    if history_blocked:
        reason_codes.append("domain_team_memory_history_blocked")
    if watch_count > DECIMAL_ZERO and not reason_codes:
        reason_codes.append("domain_team_memory_watch")
    if not reason_codes:
        reason_codes.append("domain_team_memory_ready")
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[DomainTeamMemoryScorecardRow, ...],
    history_status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("domain_team_memory_scorecard_empty",)
    reason_codes: list[str] = []
    if any(row.memory_status == "blocked" for row in rows):
        reason_codes.append("domain_team_memory_scorecard_blocked_rows")
    if history_status == "blocked":
        reason_codes.append("domain_team_memory_scorecard_history_blocked")
    if any(row.memory_status == "watch" for row in rows):
        reason_codes.append("domain_team_memory_scorecard_watch_rows")
    if not reason_codes:
        reason_codes.append("domain_team_memory_scorecard_ready")
    return tuple(reason_codes)


def _scorecard_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "domain_team_memory_scorecard_blocked_rows" in reason_codes
        or "domain_team_memory_scorecard_history_blocked" in reason_codes
        or "domain_team_memory_scorecard_empty" in reason_codes
    ):
        return "blocked"
    if "domain_team_memory_scorecard_watch_rows" in reason_codes:
        return "watch"
    return "pass"


def _memory_status(score: Decimal, config: DomainTeamMemoryScorecardConfig) -> str:
    if score >= config.pass_threshold:
        return "pass"
    if score >= config.watch_threshold:
        return "watch"
    return "blocked"


def _average_score(rows: tuple[DomainTeamMemoryScorecardRow, ...]) -> Decimal:
    if not rows:
        return Decimal("0.000000")
    return (
        sum((row.memory_score for row in rows), DECIMAL_ZERO) / Decimal(len(rows))
    ).quantize(SCORE_QUANT)


def _lowest_score(rows: tuple[DomainTeamMemoryScorecardRow, ...]) -> Decimal:
    if not rows:
        return Decimal("0.000000")
    return min(row.memory_score for row in rows).quantize(SCORE_QUANT)


def _validate_row_consistency(row: DomainTeamMemoryScorecardRow) -> None:
    if row.configured_team_count != _decimal_count(len(row.team_ids)):
        raise ValueError("configured_team_count must match team_ids")
    if (
        row.pass_count + row.watch_count + row.blocked_count
        != row.latest_team_count
    ):
        raise ValueError("latest counts must sum to latest_team_count")
    if row.latest_team_count + row.missing_team_count != row.configured_team_count:
        raise ValueError("latest_team_count plus missing_team_count must match configured_team_count")
    if row.memory_score > row.raw_memory_score:
        raise ValueError("memory_score must not exceed raw_memory_score")
    if row.raw_memory_score - row.history_penalty > DECIMAL_ZERO:
        expected_score = (row.raw_memory_score - row.history_penalty).quantize(
            SCORE_QUANT,
        )
    else:
        expected_score = Decimal("0.000000")
    if row.memory_score != expected_score:
        raise ValueError("memory_score must match raw score less history penalty")
    expected_reasons = _row_reason_codes(
        missing_team_count=row.missing_team_count,
        watch_count=row.watch_count,
        blocked_count=row.blocked_count,
        history_blocked=row.history_penalty > DECIMAL_ZERO,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row inputs")


def _validate_report_consistency(report: DomainTeamMemoryScorecardReport) -> None:
    if report.domain_count != _decimal_count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if (
        report.pass_domain_count
        + report.watch_domain_count
        + report.blocked_domain_count
        != report.domain_count
    ):
        raise ValueError("status counts must sum to domain_count")
    if report.pass_domain_count != _decimal_count(
        sum(1 for row in report.rows if row.memory_status == "pass"),
    ):
        raise ValueError("pass_domain_count must match rows")
    if report.watch_domain_count != _decimal_count(
        sum(1 for row in report.rows if row.memory_status == "watch"),
    ):
        raise ValueError("watch_domain_count must match rows")
    if report.blocked_domain_count != _decimal_count(
        sum(1 for row in report.rows if row.memory_status == "blocked"),
    ):
        raise ValueError("blocked_domain_count must match rows")
    if report.configured_team_count != sum(
        (row.configured_team_count for row in report.rows),
        DECIMAL_ZERO,
    ).quantize(COUNT_QUANT):
        raise ValueError("configured_team_count must match rows")
    if report.latest_team_count != sum(
        (row.latest_team_count for row in report.rows),
        DECIMAL_ZERO,
    ).quantize(COUNT_QUANT):
        raise ValueError("latest_team_count must match rows")
    if report.missing_team_count != sum(
        (row.missing_team_count for row in report.rows),
        DECIMAL_ZERO,
    ).quantize(COUNT_QUANT):
        raise ValueError("missing_team_count must match rows")
    if report.average_memory_score != _average_score(report.rows):
        raise ValueError("average_memory_score must match rows")
    if report.lowest_memory_score != _lowest_score(report.rows):
        raise ValueError("lowest_memory_score must match rows")
    if report.scorecard_status != _scorecard_status(report.reason_codes):
        raise ValueError("scorecard_status must match reason_codes")


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


def _normalize_domain_team_ids(
    value: object,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("domain_team_ids must contain domain/team pairs")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("domain_team_ids must contain domain/team pairs") from exc
    if not items:
        raise ValueError("domain_team_ids must contain at least one domain")
    domain_ids: set[str] = set()
    team_ids_seen: set[str] = set()
    normalized: list[tuple[str, tuple[str, ...]]] = []
    for item in items:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("domain_team_ids entries must be domain/team pairs")
        domain_id, team_ids = item
        _require_canonical_string("domain_team_ids domain_id", domain_id)
        if domain_id in domain_ids:
            raise ValueError("domain_team_ids domain_id values must be unique")
        domain_ids.add(domain_id)
        normalized_team_ids = _normalize_team_ids(team_ids)
        for team_id in normalized_team_ids:
            if team_id in team_ids_seen:
                raise ValueError("domain_team_ids team_id values must be unique")
            team_ids_seen.add(team_id)
        normalized.append((domain_id, normalized_team_ids))
    return tuple(normalized)


def _normalize_team_ids(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("team_ids must contain known teams")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("team_ids must contain known teams") from exc
    if not items:
        raise ValueError("team_ids must contain at least one team")
    normalized = tuple(require_team_id("team_id", item) for item in items)
    if len(set(normalized)) != len(normalized):
        raise ValueError("team_ids must be unique")
    return normalized


def _normalize_rows(
    value: object,
) -> tuple[DomainTeamMemoryScorecardRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    domain_ids: set[str] = set()
    team_ids_seen: set[str] = set()
    for row in rows:
        if type(row) is not DomainTeamMemoryScorecardRow:
            raise ValueError("rows must contain DomainTeamMemoryScorecardRow values")
        require_paper_only_flags("DomainTeamMemoryScorecardRow", row)
        if row.domain_id in domain_ids:
            raise ValueError("rows domain_id values must be unique")
        domain_ids.add(row.domain_id)
        for team_id in row.team_ids:
            if team_id in team_ids_seen:
                raise ValueError("rows team_id values must be unique")
            team_ids_seen.add(team_id)
    return rows


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes(value, ROW_REASON_CODES)


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes(value, REPORT_REASON_CODES)


def _normalize_reason_codes(
    value: object,
    known_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in known_reason_codes:
            raise ValueError("reason_codes must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in known_reason_codes if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_scorecard_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DOMAIN_MEMORY_SCORECARD_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_history_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("observed", "blocked"):
        raise ValueError(f"{field_name} must be observed or blocked")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if len(value) != DIGEST_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(RATIO_QUANT)
    if quantized < DECIMAL_ZERO or quantized > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _normalize_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _normalize_nonnegative_integral_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    quantized = _normalize_integral_decimal(field_name, value)
    if quantized < DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _report_values_without_digest(
    report: DomainTeamMemoryScorecardReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("derived_validation_digest payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
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
        if value.tzinfo is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_text(path or label, value)
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
        if value.tzinfo is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_text(item_path, key)
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_text(path: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"unsafe public payload at {path}")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload at {path}")


__all__ = (
    "DEFAULT_DOMAIN_TEAM_MEMORY_SCORECARD_CONFIG_VERSION",
    "DEFAULT_SCORECARD_DOMAIN_TEAM_IDS",
    "DomainTeamMemoryScorecardConfig",
    "DomainTeamMemoryScorecardReport",
    "DomainTeamMemoryScorecardRow",
    "build_domain_team_memory_scorecard_report",
    "domain_team_memory_scorecard_payload",
)
