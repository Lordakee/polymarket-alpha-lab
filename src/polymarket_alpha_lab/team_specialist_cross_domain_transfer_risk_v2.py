"""Readonly Decimal digest for specialist cross-domain playbook transfer risk."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_CROSS_DOMAIN_TRANSFER_RISK_V2_CONFIG_VERSION = (
    "team-specialist-cross-domain-transfer-risk-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

RISK_BANDS = ("low", "watch", "high")
ROW_REASON_CODES = (
    "cross_domain_transfer_risk_low",
    "cross_domain_transfer_risk_watch",
    "cross_domain_transfer_risk_high",
    "source_mismatch_low",
    "source_mismatch_watch",
    "source_mismatch_high",
    "resolution_rule_mismatch_low",
    "resolution_rule_mismatch_watch",
    "resolution_rule_mismatch_high",
    "volatility_regime_mismatch_low",
    "volatility_regime_mismatch_watch",
    "volatility_regime_mismatch_high",
    "calibration_sample_full",
    "calibration_sample_partial",
    "calibration_sample_sparse",
    "recency_current",
    "recency_watch",
    "recency_stale",
)
REPORT_REASON_CODES = (
    "cross_domain_transfer_risk_report_low",
    "cross_domain_transfer_risk_report_watch_rows",
    "cross_domain_transfer_risk_report_high_rows",
    "cross_domain_transfer_risk_report_empty",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_CROSS_DOMAIN_TRANSFER_RISK_V2_CONFIG_VERSION",
    "TeamSpecialistCrossDomainTransferRiskV2Config",
    "TeamSpecialistCrossDomainTransferRiskV2Input",
    "TeamSpecialistCrossDomainTransferRiskV2Row",
    "TeamSpecialistCrossDomainTransferRiskV2Report",
    "build_team_specialist_cross_domain_transfer_risk_v2",
)


@dataclass(frozen=True)
class TeamSpecialistCrossDomainTransferRiskV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_CROSS_DOMAIN_TRANSFER_RISK_V2_CONFIG_VERSION
    )
    source_mismatch_weight: Decimal = Decimal("0.250000")
    resolution_rule_mismatch_weight: Decimal = Decimal("0.250000")
    volatility_regime_mismatch_weight: Decimal = Decimal("0.200000")
    sample_size_risk_weight: Decimal = Decimal("0.150000")
    recency_risk_weight: Decimal = Decimal("0.150000")
    full_calibration_sample_count: Decimal = Decimal("20")
    stale_recency_days: Decimal = Decimal("45")
    high_risk_floor: Decimal = Decimal("0.700000")
    watch_risk_floor: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCrossDomainTransferRiskV2Config:
            raise TypeError(
                "TeamSpecialistCrossDomainTransferRiskV2Config does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCrossDomainTransferRiskV2Config:
            raise ValueError(
                "config must be exactly TeamSpecialistCrossDomainTransferRiskV2Config",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_CROSS_DOMAIN_TRANSFER_RISK_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_mismatch_weight",
            "resolution_rule_mismatch_weight",
            "volatility_regime_mismatch_weight",
            "sample_size_risk_weight",
            "recency_risk_weight",
            "high_risk_floor",
            "watch_risk_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "full_calibration_sample_count",
            "stale_recency_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistCrossDomainTransferRiskV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCrossDomainTransferRiskV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCrossDomainTransferRiskV2Input:
    team_id: str
    specialist_id: str
    playbook_id: str
    source_domain_id: str
    target_domain_id: str
    source_mismatch_score: Decimal
    resolution_rule_mismatch_score: Decimal
    volatility_regime_mismatch_score: Decimal
    calibration_sample_count: Decimal
    last_calibrated_days_ago: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCrossDomainTransferRiskV2Input:
            raise TypeError(
                "TeamSpecialistCrossDomainTransferRiskV2Input does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCrossDomainTransferRiskV2Input:
            raise ValueError(
                "input must be exactly TeamSpecialistCrossDomainTransferRiskV2Input",
            )
        for field_name in (
            "team_id",
            "specialist_id",
            "playbook_id",
            "source_domain_id",
            "target_domain_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_mismatch_score",
            "resolution_rule_mismatch_score",
            "volatility_regime_mismatch_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_sample_count",
            "last_calibrated_days_ago",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_hard_flags("TeamSpecialistCrossDomainTransferRiskV2Input", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCrossDomainTransferRiskV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCrossDomainTransferRiskV2Row:
    rank: Decimal
    team_id: str
    specialist_id: str
    playbook_id: str
    source_domain_id: str
    target_domain_id: str
    source_mismatch_score: Decimal
    resolution_rule_mismatch_score: Decimal
    volatility_regime_mismatch_score: Decimal
    calibration_sample_count: Decimal
    calibration_sample_size_risk: Decimal
    last_calibrated_days_ago: Decimal
    recency_risk_score: Decimal
    transfer_risk_score: Decimal
    risk_band: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCrossDomainTransferRiskV2Row:
            raise TypeError(
                "TeamSpecialistCrossDomainTransferRiskV2Row does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCrossDomainTransferRiskV2Row:
            raise ValueError(
                "row must be exactly TeamSpecialistCrossDomainTransferRiskV2Row",
            )
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        for field_name in (
            "team_id",
            "specialist_id",
            "playbook_id",
            "source_domain_id",
            "target_domain_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_mismatch_score",
            "resolution_rule_mismatch_score",
            "volatility_regime_mismatch_score",
            "calibration_sample_size_risk",
            "recency_risk_score",
            "transfer_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_sample_count",
            "last_calibrated_days_ago",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_risk_band("risk_band", self.risk_band)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
            ),
        )
        _require_hard_flags("TeamSpecialistCrossDomainTransferRiskV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCrossDomainTransferRiskV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class TeamSpecialistCrossDomainTransferRiskV2Report:
    generated_at: datetime
    config_version: str
    transfer_risk_status: str
    candidate_count: Decimal
    low_risk_candidate_count: Decimal
    watch_risk_candidate_count: Decimal
    high_risk_candidate_count: Decimal
    average_transfer_risk_score: Decimal
    top_transfer_risk_score: Decimal
    bottom_transfer_risk_score: Decimal
    rows: tuple[TeamSpecialistCrossDomainTransferRiskV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCrossDomainTransferRiskV2Report:
            raise TypeError(
                "TeamSpecialistCrossDomainTransferRiskV2Report does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCrossDomainTransferRiskV2Report:
            raise ValueError(
                "report must be exactly TeamSpecialistCrossDomainTransferRiskV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_CROSS_DOMAIN_TRANSFER_RISK_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_risk_band("transfer_risk_status", self.transfer_risk_status)
        for field_name in (
            "candidate_count",
            "low_risk_candidate_count",
            "watch_risk_candidate_count",
            "high_risk_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_transfer_risk_score",
            "top_transfer_risk_score",
            "bottom_transfer_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("TeamSpecialistCrossDomainTransferRiskV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCrossDomainTransferRiskV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistCrossDomainTransferRiskV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_cross_domain_transfer_risk_v2(
    transfer_risk_inputs: object,
    *,
    config: TeamSpecialistCrossDomainTransferRiskV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistCrossDomainTransferRiskV2Report:
    if config is None:
        config = TeamSpecialistCrossDomainTransferRiskV2Config()
    if type(config) is not TeamSpecialistCrossDomainTransferRiskV2Config:
        raise ValueError(
            "config must be a TeamSpecialistCrossDomainTransferRiskV2Config",
        )
    _require_hard_flags("TeamSpecialistCrossDomainTransferRiskV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_transfer_risk_inputs(transfer_risk_inputs)

    rows = tuple(
        _row_for_transfer_risk_input(rank=index, item=item, config=config)
        for index, item in enumerate(_sorted_transfer_risk_inputs(items, config), start=1)
    )
    status = _risk_digest_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "transfer_risk_status": status,
        "candidate_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "low_risk_candidate_count": _risk_band_count(rows, "low"),
        "watch_risk_candidate_count": _risk_band_count(rows, "watch"),
        "high_risk_candidate_count": _risk_band_count(rows, "high"),
        "average_transfer_risk_score": _average_risk_score(rows),
        "top_transfer_risk_score": _top_risk_score(rows),
        "bottom_transfer_risk_score": _bottom_risk_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistCrossDomainTransferRiskV2Report(**values)


def _sorted_transfer_risk_inputs(
    items: tuple[TeamSpecialistCrossDomainTransferRiskV2Input, ...],
    config: TeamSpecialistCrossDomainTransferRiskV2Config,
) -> tuple[TeamSpecialistCrossDomainTransferRiskV2Input, ...]:
    return tuple(
        sorted(
            items,
            key=lambda item: (
                -_risk_score_for_transfer_input(item, config),
                item.team_id,
                item.specialist_id,
                item.playbook_id,
                item.source_domain_id,
                item.target_domain_id,
            ),
        ),
    )


def _row_for_transfer_risk_input(
    *,
    rank: int,
    item: TeamSpecialistCrossDomainTransferRiskV2Input,
    config: TeamSpecialistCrossDomainTransferRiskV2Config,
) -> TeamSpecialistCrossDomainTransferRiskV2Row:
    sample_size_risk = _sample_size_risk(item.calibration_sample_count, config)
    recency_risk = _recency_risk(item.last_calibrated_days_ago, config)
    score = _risk_score_for_transfer_input(item, config)
    band = _risk_band(score, config)
    return TeamSpecialistCrossDomainTransferRiskV2Row(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        team_id=item.team_id,
        specialist_id=item.specialist_id,
        playbook_id=item.playbook_id,
        source_domain_id=item.source_domain_id,
        target_domain_id=item.target_domain_id,
        source_mismatch_score=item.source_mismatch_score,
        resolution_rule_mismatch_score=item.resolution_rule_mismatch_score,
        volatility_regime_mismatch_score=item.volatility_regime_mismatch_score,
        calibration_sample_count=item.calibration_sample_count,
        calibration_sample_size_risk=sample_size_risk,
        last_calibrated_days_ago=item.last_calibrated_days_ago,
        recency_risk_score=recency_risk,
        transfer_risk_score=score,
        risk_band=band,
        reason_codes=_row_reason_codes(
            item,
            band,
            sample_size_risk,
            recency_risk,
        ),
    )


def _risk_score_for_transfer_input(
    item: TeamSpecialistCrossDomainTransferRiskV2Input,
    config: TeamSpecialistCrossDomainTransferRiskV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            item.source_mismatch_score * config.source_mismatch_weight
            + item.resolution_rule_mismatch_score
            * config.resolution_rule_mismatch_weight
            + item.volatility_regime_mismatch_score
            * config.volatility_regime_mismatch_weight
            + _sample_size_risk(item.calibration_sample_count, config)
            * config.sample_size_risk_weight
            + _recency_risk(item.last_calibrated_days_ago, config)
            * config.recency_risk_weight
        )
        return _clamp_ratio(score)


def _sample_size_risk(
    calibration_sample_count: Decimal,
    config: TeamSpecialistCrossDomainTransferRiskV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        sample_depth = _clamp_ratio(
            calibration_sample_count / config.full_calibration_sample_count,
        )
        return _clamp_ratio(ONE - sample_depth)


def _recency_risk(
    last_calibrated_days_ago: Decimal,
    config: TeamSpecialistCrossDomainTransferRiskV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(last_calibrated_days_ago / config.stale_recency_days)


def _risk_band(
    score: Decimal,
    config: TeamSpecialistCrossDomainTransferRiskV2Config,
) -> str:
    if score >= config.high_risk_floor:
        return "high"
    if score >= config.watch_risk_floor:
        return "watch"
    return "low"


def _risk_digest_status(
    rows: tuple[TeamSpecialistCrossDomainTransferRiskV2Row, ...],
) -> str:
    if not rows:
        return "high"
    if any(row.risk_band == "high" for row in rows):
        return "high"
    if any(row.risk_band == "watch" for row in rows):
        return "watch"
    return "low"


def _row_reason_codes(
    item: TeamSpecialistCrossDomainTransferRiskV2Input,
    band: str,
    sample_size_risk: Decimal,
    recency_risk: Decimal,
) -> tuple[str, ...]:
    return (
        f"cross_domain_transfer_risk_{band}",
        _tier_risk_reason(
            item.source_mismatch_score,
            high=Decimal("0.750000"),
            watch=Decimal("0.400000"),
            low_reason="source_mismatch_low",
            watch_reason="source_mismatch_watch",
            high_reason="source_mismatch_high",
        ),
        _tier_risk_reason(
            item.resolution_rule_mismatch_score,
            high=Decimal("0.750000"),
            watch=Decimal("0.400000"),
            low_reason="resolution_rule_mismatch_low",
            watch_reason="resolution_rule_mismatch_watch",
            high_reason="resolution_rule_mismatch_high",
        ),
        _tier_risk_reason(
            item.volatility_regime_mismatch_score,
            high=Decimal("0.750000"),
            watch=Decimal("0.400000"),
            low_reason="volatility_regime_mismatch_low",
            watch_reason="volatility_regime_mismatch_watch",
            high_reason="volatility_regime_mismatch_high",
        ),
        _sample_size_reason(sample_size_risk),
        _recency_reason(recency_risk),
    )


def _report_reason_codes(
    rows: tuple[TeamSpecialistCrossDomainTransferRiskV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("cross_domain_transfer_risk_report_empty",)
    reasons: list[str] = []
    if any(row.risk_band == "high" for row in rows):
        reasons.append("cross_domain_transfer_risk_report_high_rows")
    if any(row.risk_band == "watch" for row in rows):
        reasons.append("cross_domain_transfer_risk_report_watch_rows")
    if not reasons and status == "low":
        reasons.append("cross_domain_transfer_risk_report_low")
    return tuple(reasons)


def _tier_risk_reason(
    value: Decimal,
    *,
    high: Decimal,
    watch: Decimal,
    low_reason: str,
    watch_reason: str,
    high_reason: str,
) -> str:
    if value >= high:
        return high_reason
    if value >= watch:
        return watch_reason
    return low_reason


def _sample_size_reason(value: Decimal) -> str:
    if value <= Decimal("0.200000"):
        return "calibration_sample_full"
    if value <= Decimal("0.600000"):
        return "calibration_sample_partial"
    return "calibration_sample_sparse"


def _recency_reason(value: Decimal) -> str:
    if value <= Decimal("0.250000"):
        return "recency_current"
    if value <= Decimal("0.750000"):
        return "recency_watch"
    return "recency_stale"


def _risk_band_count(
    rows: tuple[TeamSpecialistCrossDomainTransferRiskV2Row, ...],
    band: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.risk_band == band)).quantize(
        COUNT_QUANT,
    )


def _average_risk_score(
    rows: tuple[TeamSpecialistCrossDomainTransferRiskV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum(row.transfer_risk_score for row in rows) / Decimal(len(rows)),
        )


def _top_risk_score(
    rows: tuple[TeamSpecialistCrossDomainTransferRiskV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.transfer_risk_score for row in rows)


def _bottom_risk_score(
    rows: tuple[TeamSpecialistCrossDomainTransferRiskV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.transfer_risk_score for row in rows)


def _normalize_transfer_risk_inputs(
    value: object,
) -> tuple[TeamSpecialistCrossDomainTransferRiskV2Input, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("transfer_risk_inputs must be an iterable")
    items = tuple(value)
    for item in items:
        if type(item) is not TeamSpecialistCrossDomainTransferRiskV2Input:
            raise ValueError(
                "transfer risk items must be TeamSpecialistCrossDomainTransferRiskV2Input",
            )
        _require_hard_flags("TeamSpecialistCrossDomainTransferRiskV2Input", item)
    keys = tuple(
        (
            item.team_id,
            item.specialist_id,
            item.playbook_id,
            item.source_domain_id,
            item.target_domain_id,
        )
        for item in items
    )
    if len(set(keys)) != len(keys):
        raise ValueError("transfer risk items must not contain duplicate transfer risk keys")
    return items


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistCrossDomainTransferRiskV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistCrossDomainTransferRiskV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistCrossDomainTransferRiskV2Row",
            )
    return value


def _validate_config(
    config: TeamSpecialistCrossDomainTransferRiskV2Config,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.source_mismatch_weight
            + config.resolution_rule_mismatch_weight
            + config.volatility_regime_mismatch_weight
            + config.sample_size_risk_weight
            + config.recency_risk_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("risk weights must sum to 1.000000")
    if config.watch_risk_floor > config.high_risk_floor:
        raise ValueError("watch_risk_floor must not exceed high_risk_floor")


def _validate_row_consistency(row: TeamSpecialistCrossDomainTransferRiskV2Row) -> None:
    if row.reason_codes[0] != f"cross_domain_transfer_risk_{row.risk_band}":
        raise ValueError("risk_band must match transfer_risk_score")


def _validate_report_consistency(
    report: TeamSpecialistCrossDomainTransferRiskV2Report,
) -> None:
    rows = report.rows
    if report.candidate_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("candidate_count must match rows")
    if (
        report.low_risk_candidate_count != _risk_band_count(rows, "low")
        or report.watch_risk_candidate_count != _risk_band_count(rows, "watch")
        or report.high_risk_candidate_count != _risk_band_count(rows, "high")
    ):
        raise ValueError("risk counts must match rows")
    if (
        report.low_risk_candidate_count
        + report.watch_risk_candidate_count
        + report.high_risk_candidate_count
        != report.candidate_count
    ):
        raise ValueError("risk counts must sum to candidate_count")
    _validate_rows_sorted(rows)
    expected_status = _risk_digest_status(rows)
    if report.transfer_risk_status != expected_status:
        raise ValueError("transfer_risk_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.transfer_risk_status):
        raise ValueError("reason_codes must match transfer_risk_status")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_transfer_risk_score != _average_risk_score(rows):
        raise ValueError("average_transfer_risk_score must match rows")
    if report.top_transfer_risk_score != _top_risk_score(rows):
        raise ValueError("top_transfer_risk_score must match rows")
    if report.bottom_transfer_risk_score != _bottom_risk_score(rows):
        raise ValueError("bottom_transfer_risk_score must match rows")


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistCrossDomainTransferRiskV2Row, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.transfer_risk_score,
                row.team_id,
                row.specialist_id,
                row.playbook_id,
                row.source_domain_id,
                row.target_domain_id,
            ),
        ),
    )
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by risk score and rank")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_risk_band(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in RISK_BANDS:
        raise ValueError(f"{field_name} must be low, watch, or high")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    value = _require_non_empty_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("payload contains unsafe numeric value")
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if value.strip() != value:
        raise ValueError(f"unsafe public payload in {label}")
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
